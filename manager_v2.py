"""
Game Manager - Player-based game manager for Advance Wars RPC
"""
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
import math
import configparser

from map_system import Army, MapType, MOVEMENT_COST, INF, TERRAIN_DEFENSE
from gameboard import GameTile, GameBoard
from unit import UnitType, Unit, UnitClass, UnitConfig, UnitStatus
from game_board_v2 import GameBoardV2
from player_system import PlayerManager
from transport_system import CompleteTransportSystem
from production_system import ProductionSystem
from enhanced_movement_validation import EnhancedMovementValidator
from enhanced_combat_system import EnhancedCombatSystem
from dijkstra import dijkstra
from config import Config

class GameManager:
    """Game manager that uses the new player system"""
    
    def __init__(self, config, board: GameBoardV2, player_manager: PlayerManager):
        """Initialize with player-aware board"""
        # Store board and player manager
        self.board = board
        self.board_v2 = board  # Keep for compatibility during migration
        self.player_manager = player_manager
        self.config = config
        
        # Initialize board with player manager
        board.initialize_from_player_manager(player_manager)
        
        # Initialize transport system
        self.transport_system = CompleteTransportSystem(self)
        self.app_logger = None  # Will be set by the calling code
        
        # Modifier system for COs, COM_TOWERs, etc.
        self.modifiers = {}  # army -> list of modifiers
        self._update_com_tower_modifiers()  # Initialize COM_TOWER modifiers
        
    def setup_initial_economy(self) -> None:
        """Setup initial funds for all players based on starting properties"""
        # Load config
        config = configparser.ConfigParser()
        config.read('config.ini')
        income = int(config['FUNDS']['income'])
        production_system = ProductionSystem(self)
        
        # Count production buildings for each player
        for player_id in range(self.player_manager.get_player_count()):
            initial_income = 0
            
            # Count properties owned by this player
            for y in range(self.board.height):
                for x in range(self.board.width):
                    tile = self.board.grid[y * self.board.width + x]
                    if tile.mapTile and tile.mapTile.type in {MapType.CITY, MapType.FACTORY, MapType.AIRPORT, MapType.PORT}:
                        # Check ownership by player ID
                        tile_player = self._get_tile_player(tile)
                        if tile_player == player_id:
                            initial_income += income
                            
            # Set starting funds
            starting_funds = max(10000, initial_income * 3)
            self.board_v2.player_funds[player_id] = starting_funds
            
            # Update army funds for backward compatibility
            army = self.board_v2.get_army_for_player(player_id)
            if army:
                self.board_v2.army_funds[army] = starting_funds
                
    def _update_property_ownership(self, tile: GameTile, new_army: Army) -> None:
        """Update property ownership and adjust player statistics."""
        old_army = tile.mapTile.army
        income = 1000  # Standard income per property
        
        # Update the tile ownership
        tile.mapTile.army = new_army
        
        # Update COM_TOWER modifiers if needed
        if tile.mapTile.type == MapType.COM_TOWER:
            self._update_com_tower_modifiers()
        
        # Convert armies to player IDs for v2-specific updates
        old_player = self.board_v2.get_player_for_army(old_army) if old_army else None
        new_player = self.board_v2.get_player_for_army(new_army) if new_army else None
        
        # Update player property counts
        if old_player is not None:
            self.board_v2.update_player_properties(old_player, -1)
            
        if new_player is not None:
            self.board_v2.update_player_properties(new_player, 1)
            
    def _update_army_funds(self, army: Army, amount: int) -> None:
        """Update funds for an army/player."""
        player_id = self.board_v2.get_player_for_army(army)
        if player_id is not None:
            self.board_v2.update_player_funds(player_id, amount)
        else:
            # Fallback for armies not mapped to players
            if hasattr(self.board, 'army_funds') and army in self.board.army_funds:
                self.board.army_funds[army] += amount
                
    def _get_army_funds(self, army: Army) -> int:
        """Get current funds for an army/player."""
        player_id = self.board_v2.get_player_for_army(army)
        if player_id is not None:
            return self.board_v2.player_funds.get(player_id, 0)
        else:
            # Fallback for armies not mapped to players
            if hasattr(self.board, 'army_funds') and army in self.board.army_funds:
                return self.board.army_funds.get(army, 0)
            return 0
            
    def unit_create(self, army: str, unit_type: str, x: int, y: int) -> Unit:
        """Create a new unit at the specified coordinates."""
        from production_system import ProductionSystem
        
        # Validation
        self._validate_coordinates(x, y)
        self._validate_game_active()
        
        # Check tile is empty
        if self.unit_at(x, y):
            raise ValueError(f'Tile at ({x}, {y}) already occupied')
        
        # Get army object
        army_obj = Army[army] if isinstance(army, str) else army
        
        # Check funds
        unit_type_enum = UnitType[unit_type] if isinstance(unit_type, str) else unit_type
        cost = ProductionSystem.UNIT_COSTS.get(unit_type_enum, 99999)
        funds = self._get_army_funds(army_obj)
        if funds < cost:
            raise ValueError(f'Insufficient funds: {funds} < {cost}')
        
        # Create the unit
        # Read unit config from config.ini
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        unit_section = config[unit_type_enum.name]
        unit_config = UnitConfig(
            cls=UnitClass[unit_section['class']],
            cost=int(unit_section['cost']),
            move=int(unit_section['move']),
            rangemin=int(unit_section['rangemin']),
            rangemax=int(unit_section['rangemax']),
            max_fuel=int(unit_section['fuel']),
            vision=int(unit_section['vision']),
            max_hp=int(unit_section['hp']),
            max_ammo=int(unit_section['ammo'])
        )
        
        unit = Unit.create(army_obj, unit_type_enum, unit_config)
        self.tile_at(x, y).unit = unit
        
        # Mark unit as unable to act on creation turn
        self._set_unit_inactive(unit)
        
        # Deduct funds
        self._update_army_funds(army_obj, -cost)
        
        # Update statistics
        self._update_army_statistics()
        
        return unit
        
    def _update_army_statistics(self) -> None:
        """Update all player statistics in a single pass."""
        # Reset all player counters
        for player_id in range(self.player_manager.get_player_count()):
            self.board_v2.player_troops[player_id] = 0
            self.board_v2.player_properties[player_id] = 0
            
        # Also reset army counters for backward compatibility
        for army in self.board.turn_order:
            self.board.army_troops[army] = 0
            self.board.army_properties[army] = 0
            
        # Count units and properties in single pass
        for y in range(self.board.height):
            for x in range(self.board.width):
                tile = self.board.grid[y * self.board.width + x]
                
                # Count units
                if tile.unit:
                    player_id = self._get_unit_player(tile.unit)
                    if player_id is not None:
                        self.board_v2.player_troops[player_id] += 1
                        
                    # Also update army troops for compatibility
                    if tile.unit.army in self.board.army_troops:
                        self.board.army_troops[tile.unit.army] += 1
                        
                # Count properties
                if tile.mapTile and tile.mapTile.type in {MapType.CITY, MapType.FACTORY, MapType.AIRPORT, MapType.PORT}:
                    player_id = self._get_tile_player(tile)
                    if player_id is not None:
                        self.board_v2.player_properties[player_id] += 1
                        
                    # Also update army properties for compatibility
                    if tile.mapTile.army and tile.mapTile.army in self.board.army_properties:
                        self.board.army_properties[tile.mapTile.army] += 1
                        
    def _get_unit_player(self, unit: Unit) -> Optional[int]:
        """Get player ID for a unit"""
        return self.board_v2.get_player_for_army(unit.army)
        
    def _get_tile_player(self, tile: GameTile) -> Optional[int]:
        """Get player ID for a tile"""
        if tile.mapTile and tile.mapTile.army:
            return self.board_v2.get_player_for_army(tile.mapTile.army)
        return None
        
    def _advance_to_next_army(self) -> None:
        """Advance to the next player's turn."""
        # Use player-based turn order
        self.board_v2.current_player = self.board_v2.get_next_player()
        
        # Update current_turn for backward compatibility
        new_army = self.board_v2.get_army_for_player(self.board_v2.current_player)
        if new_army:
            self.board.current_turn = new_army
            
        # Check if we've completed a round
        if self.board_v2.current_player == 0:
            self.board.days += 1
            
    def get_current_player_info(self) -> Dict:
        """Get information about the current player"""
        player_id = self.board_v2.current_player
        player = self.player_manager.get_player(player_id)
        
        if player:
            return {
                'id': player.id,
                'name': player.name,
                'color': player.color,
                'sprite_color': player.sprite_color.value,
                'funds': self.board_v2.player_funds.get(player_id, 0),
                'properties': self.board_v2.player_properties.get(player_id, 0),
                'troops': self.board_v2.player_troops.get(player_id, 0)
            }
        return {}
        
    def to_dict(self) -> Dict:
        """Convert game state to dictionary with player information"""
        # Get board state
        state = self.board.to_dict()
        
        # Add player information
        player_data = self.player_manager.to_dict()
        state['players'] = player_data['players']
        state['sprite_mapping'] = player_data['sprite_mapping']
        state['player_funds'] = self.board_v2.player_funds
        state['player_properties'] = self.board_v2.player_properties
        state['player_troops'] = self.board_v2.player_troops
        state['current_player'] = self.board_v2.current_player
        
        return state
    
    # =============================================================================
    # CORE UTILITY METHODS
    # =============================================================================
    
    def tile_at(self, x: int, y: int) -> GameTile:
        """Returns the game tile at the coordinates given."""
        index = x + y * self.board.width
        return self.board.grid[index]
    
    def tile_get(self, x: int, y: int) -> GameTile:
        """Get tile at given coordinates (alias for tile_at)."""
        return self.tile_at(x, y)
    
    def unit_at(self, x: int, y: int) -> Optional[Unit]:
        """Returns the unit at the given coordinates."""
        return self.tile_at(x, y).unit
    
    def check_turn(self) -> Army:
        """Returns the current army's turn."""
        return self.board.current_turn
    
    def coord_valid(self, x: int, y: int) -> bool:
        """Returns true if the coordinate is within the board bounds."""
        return 0 <= x < self.board.width and 0 <= y < self.board.height
    
    def tile_from_unit(self, unit: Unit) -> Optional[GameTile]:
        """Returns the tile the unit is on."""
        for tile in self.board.grid:
            if tile.unit and tile.unit.id == unit.id:
                return tile
        return None
    
    # =============================================================================
    # VALIDATION HELPERS
    # =============================================================================
    
    def _validate_coordinates(self, x: int, y: int, x2: Optional[int] = None, y2: Optional[int] = None) -> None:
        """Validate that coordinates are within board bounds."""
        if not (0 <= x < self.board.width and 0 <= y < self.board.height):
            raise ValueError(f'Coordinate ({x}, {y}) out of range')
        if x2 is not None and y2 is not None:
            if not (0 <= x2 < self.board.width and 0 <= y2 < self.board.height):
                raise ValueError(f'Target coordinate ({x2}, {y2}) out of range')
    
    def _validate_game_active(self) -> None:
        """Ensure game is still active."""
        if not self.board.game_active:
            raise ValueError("Game is over")
    
    def _validate_unit_exists(self, x: int, y: int) -> Unit:
        """Validate unit exists at coordinates and return it."""
        unit = self.tile_at(x, y).unit
        if not unit:
            raise ValueError(f'No unit at ({x}, {y})')
        return unit
    
    def _validate_unit_turn(self, unit: Unit) -> None:
        """Validate it's the unit's army's turn."""
        if unit.army != self.board.current_turn:
            raise ValueError(f"Not this unit's turn (unit army: {unit.army.name}, current turn: {self.board.current_turn.name})")
    
    def _validate_unit_can_act(self, unit: Unit, action: str) -> None:
        """Validate unit can perform the specified action."""
        if action == 'move' and not unit.can_move:
            raise ValueError('Unit cannot move this turn')
        elif action == 'attack' and not unit.can_attack:
            raise ValueError('Unit cannot attack this turn')
        elif action == 'capture' and not unit.can_capture:
            raise ValueError('Unit cannot capture this turn')
    
    # =============================================================================
    # UNIT STATE MANAGEMENT
    # =============================================================================
    
    def _set_unit_inactive(self, unit: Unit) -> None:
        """Set unit to inactive state after performing an action."""
        unit.can_move = False
        unit.can_attack = False
        unit.can_capture = False
    
    def _set_all_army_units_inactive(self, army: Army) -> None:
        """Set all units of an army to inactive."""
        for tile in self.board.grid:
            if tile.unit and tile.unit.army == army:
                self._set_unit_inactive(tile.unit)
    
    def _set_all_army_units_active(self, army: Army) -> None:
        """Activate all units for an army's turn."""
        for tile in self.board.grid:
            if tile.unit and tile.unit.army == army:
                unit = tile.unit
                unit.can_move = True
                unit.can_attack = True
                unit.can_capture = unit.type_can_capture()  # Only infantry/mech can capture
    
    def _remove_destroyed_units(self) -> List[GameTile]:
        """Remove all units with HP <= 0 and return their tiles."""
        destroyed_tiles = []
        for tile in self.board.grid:
            if tile.unit and tile.unit.status.hp <= 0:
                tile.unit = None
                tile.capture_hp = 20
                destroyed_tiles.append(tile)
        return destroyed_tiles
    
    # =============================================================================
    # MOVEMENT SYSTEM (Delegates to EnhancedMovementValidator)
    # =============================================================================
    
    def unit_move(self, x: int, y: int, x2: int, y2: int) -> Unit:
        """Move a unit from one position to another."""
        # Validation
        self._validate_coordinates(x, y, x2, y2)
        self._validate_game_active()
        unit = self._validate_unit_exists(x, y)
        self._validate_unit_turn(unit)
        self._validate_unit_can_act(unit, 'move')
        
        # Use enhanced movement validator
        validator = EnhancedMovementValidator(self.board, self)
        result = validator.validate_movement(unit, x, y, x2, y2)
        
        if not result.valid:
            raise ValueError(result.reason)
        
        # Execute the move
        source_tile = self.tile_at(x, y)
        dest_tile = self.tile_at(x2, y2)
        
        # Move the unit
        dest_tile.unit = source_tile.unit
        source_tile.unit = None
        
        # Update unit state
        unit.status.fuel -= result.fuel_required
        self._set_unit_inactive(unit)
        
        return unit
    
    def get_unit_valid_moves(self, unit: Unit) -> List[Tuple[int, int]]:
        """Get all valid moves for a unit."""
        tile = self.tile_from_unit(unit)
        if not tile:
            return []
        
        validator = EnhancedMovementValidator(self.board, self)
        return validator.get_valid_moves(unit, tile.x, tile.y)
    
    def validate_movement_detailed(self, x: int, y: int, x2: int, y2: int):
        """Validate movement and get detailed information."""
        unit = self._validate_unit_exists(x, y)
        validator = EnhancedMovementValidator(self.board, self)
        return validator.validate_movement(unit, x, y, x2, y2)
    
    def get_modified_movement(self, unit: Unit) -> int:
        """Get movement range with modifiers applied."""
        base_movement = unit.status.move
        # TODO: Apply CO and other modifiers here
        return base_movement
    
    # =============================================================================
    # COMBAT SYSTEM (Delegates to EnhancedCombatSystem)
    # =============================================================================
    
    def unit_attack(self, x: int, y: int, x2: int, y2: int) -> Optional[Unit]:
        """Basic unit attack - uses enhanced combat system."""
        return self.unit_attack_enhanced(x, y, x2, y2)
    
    def unit_attack_enhanced(self, attacker_x: int, attacker_y: int, 
                            defender_x: int, defender_y: int):
        """Enhanced unit attack with full combat system."""
        # Validation
        self._validate_coordinates(attacker_x, attacker_y, defender_x, defender_y)
        attacker = self._validate_unit_exists(attacker_x, attacker_y)
        defender = self._validate_unit_exists(defender_x, defender_y)
        
        self._validate_unit_turn(attacker)
        self._validate_unit_can_act(attacker, 'attack')
        
        # Use enhanced combat system
        combat_system = EnhancedCombatSystem(self)
        result = combat_system.execute_enhanced_combat(
            attacker_x, attacker_y, defender_x, defender_y
        )
        
        # Mark attacker as having acted
        self._set_unit_inactive(attacker)
        
        # Remove destroyed units
        self._remove_destroyed_units()
        
        return result
    
    def damage_estimate(self, x: int, y: int, x2: int, y2: int) -> Tuple[int, int]:
        """Get damage preview for combat."""
        combat_system = EnhancedCombatSystem(self)
        preview = combat_system.get_combat_preview(x, y, x2, y2)
        return (preview.attacker_damage, preview.counter_damage)
    
    def get_damage_preview(self, attacker_x: int, attacker_y: int, 
                          defender_x: int, defender_y: int, 
                          hypothetical_distance: int = None) -> Dict:
        """Get comprehensive damage preview for combat."""
        try:
            combat_system = EnhancedCombatSystem(self)
            preview = combat_system.get_combat_preview(attacker_x, attacker_y, 
                                                     defender_x, defender_y)
            
            # Return comprehensive preview data
            return {
                "attacker_damage": preview.attacker_damage,
                "defender_damage": preview.counter_damage,
                "can_counter": preview.can_counter,
                "attacker_hp_after": preview.attacker_hp_after,
                "defender_hp_after": preview.defender_hp_after,
                "attacker_destroyed": preview.attacker_destroyed,
                "defender_destroyed": preview.defender_destroyed,
                "terrain_bonus": preview.terrain_bonus,
                "damage_range": preview.luck_range,
                "ammo_warning": preview.ammo_warning
            }
        except Exception as e:
            return {"error": str(e)}
    
    def unit_can_attack(self, attacker: Unit, target_x: int, target_y: int) -> bool:
        """Check if unit can attack target position."""
        # Get attacker position
        attacker_tile = self.tile_from_unit(attacker)
        if not attacker_tile:
            return False
        
        # Calculate distance
        distance = abs(attacker_tile.x - target_x) + abs(attacker_tile.y - target_y)
        
        # Check if within range
        return attacker.status.rangemin <= distance <= attacker.status.rangemax
    
    def unit_remove(self, x: int, y: int) -> None:
        """Remove unit at given position."""
        tile = self.tile_at(x, y)
        if tile.unit:
            tile.unit = None
            # Update statistics
            self._update_army_statistics()
    
    def unit_load(self, cargo_x: int, cargo_y: int, transport_x: int, transport_y: int) -> Dict:
        """Load a unit into a transport (legacy interface)."""
        try:
            cargo = self.unit_at(cargo_x, cargo_y)
            transport = self.unit_at(transport_x, transport_y)
            
            if not cargo:
                return {'success': False, 'error': 'No cargo unit at position'}
            if not transport:
                return {'success': False, 'error': 'No transport at position'}
            
            result = self.transport_system.load_unit_enhanced(
                transport, cargo, transport_x, transport_y, cargo_x, cargo_y
            )
            
            if result.success:
                # Remove cargo from board
                self.tile_at(cargo_x, cargo_y).unit = None
                
            return {'success': result.success, 'error': result.message if not result.success else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def unit_wait(self, x: int, y: int) -> None:
        """Mark unit as having finished its turn."""
        unit = self.unit_at(x, y)
        if unit:
            self._set_unit_inactive(unit)
    
    # =============================================================================
    # GAME STATE MANAGEMENT
    # =============================================================================
    
    def army_end_turn(self) -> None:
        """End the current army's turn and advance to the next."""
        current_army = self.board.current_turn
        
        # Set all current army units to inactive
        self._set_all_army_units_inactive(current_army)
        
        # Apply turn-end effects (repairs, fuel consumption, etc.)
        self._apply_turn_end_effects(current_army)
        
        # Advance to next turn
        self._advance_to_next_army()
        
        # Activate all units for the new turn
        new_army = self.board.current_turn
        self._set_all_army_units_active(new_army)
        
        # Apply turn-start effects (income, auto-resupply)
        self._apply_turn_start_effects(new_army)
    
    def _apply_turn_end_effects(self, army: Army) -> None:
        """Apply effects at the end of an army's turn."""
        # Note: Fuel consumption moved to turn start AFTER refueling
        pass
    
    def _apply_turn_start_effects(self, army: Army) -> None:
        """Apply effects at the start of an army's turn."""
        # FIRST: Auto-resupply from APCs and bases (before fuel consumption)
        self._apply_auto_resupply(army)
        
        # SECOND: Consume fuel for air and naval units
        for tile in self.board.grid:
            if tile.unit and tile.unit.army == army:
                unit = tile.unit
                if unit.status.cls in {UnitClass.AIR, UnitClass.SEA, UnitClass.LANDER}:
                    # Air units consume 2 fuel, naval units consume 1
                    fuel_consumption = 2 if unit.status.cls == UnitClass.AIR else 1
                    unit.status.fuel = max(0, unit.status.fuel - fuel_consumption)
                    
                    # Crash/sink if out of fuel
                    if unit.status.fuel == 0:
                        unit.status.hp = 0
        
        # THIRD: Add income from properties
        player_id = self.board_v2.get_player_for_army(army)
        if player_id is not None:
            income = self.board_v2.player_properties.get(player_id, 0) * 1000
            self._update_army_funds(army, income)
    
    def _update_com_tower_modifiers(self) -> None:
        """Update COM_TOWER damage modifiers for all armies."""
        # Reset all modifiers
        self.modifiers = {}
        
        # Count COM_TOWERs for each army
        for tile in self.board.grid:
            if tile.mapTile and tile.mapTile.type == MapType.COM_TOWER and tile.mapTile.army:
                army = tile.mapTile.army
                if army not in self.modifiers:
                    self.modifiers[army] = []
                # Each COM_TOWER provides +10% attack damage
                self.modifiers[army].append(('COM_TOWER', 'attack', 0.1))
    
    def _apply_auto_resupply(self, army: Army) -> None:
        """Auto-resupply units at the start of their turn."""
        # Resupply from appropriate buildings based on unit type
        for tile in self.board.grid:
            if tile.unit and tile.unit.army == army:
                unit = tile.unit
                # Check if unit is on a friendly resupply building
                if tile.mapTile and tile.mapTile.army == army:
                    can_resupply = False
                    
                    # Check unit type and building compatibility
                    if unit.status.cls == UnitClass.AIR:
                        # Air units only resupply at airports
                        can_resupply = tile.mapTile.type == MapType.AIRPORT
                    elif unit.status.cls in {UnitClass.SEA, UnitClass.LANDER}:
                        # Sea units only resupply at ports
                        can_resupply = tile.mapTile.type == MapType.PORT
                    else:
                        # Land units resupply at cities, factories, and HQs
                        can_resupply = tile.mapTile.type in {MapType.CITY, MapType.FACTORY,
                                                            MapType.BASE_TOWER_1, MapType.BASE_TOWER_2,
                                                            MapType.BASE_TOWER_3, MapType.BASE_TOWER_4}
                    
                    if can_resupply:
                        # Full resupply
                        unit.status.fuel = unit.config.max_fuel
                        unit.status.ammo = unit.config.max_ammo
        
        # Resupply from APCs (adjacent units)
        for tile in self.board.grid:
            if tile.unit and tile.unit.army == army and tile.unit.type == UnitType.APC:
                apc = tile.unit
                # Check all adjacent tiles
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    adj_x, adj_y = tile.x + dx, tile.y + dy
                    if self.coord_valid(adj_x, adj_y):
                        adj_unit = self.unit_at(adj_x, adj_y)
                        if adj_unit and adj_unit.army == army:
                            # Resupply adjacent friendly units
                            adj_unit.status.fuel = adj_unit.config.max_fuel
                            adj_unit.status.ammo = adj_unit.config.max_ammo
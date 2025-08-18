"""
Game Manager - Player-based game manager for Advance Wars RPC
"""
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
import math
import configparser

from core.map_system import Army, MapType, get_movement_cost, INF, TERRAIN_DEFENSE_STARS
from gameboard import GameBoard, GameTile
from core.unit import UnitType, Unit, UnitClass, UnitConfig, UnitStatus
from core.player_system import PlayerManager
from core.transport_system import CompleteTransportSystem
from core.production_system import ProductionSystem
from core.enhanced_movement_validation import EnhancedMovementValidator
from core.enhanced_combat_system import EnhancedCombatSystem
from core.dijkstra import dijkstra
from config import Config

class GameManager:
    """Game manager that uses the new player system"""
    
    def __init__(self, config, board: GameBoard, player_manager: PlayerManager):
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
    
    def log(self, message: str, level: str = 'info') -> None:
        """Safe logging that handles missing or incorrect app_logger"""
        if self.app_logger and hasattr(self.app_logger, level):
            getattr(self.app_logger, level)(message)
        
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
                            
            # Set starting funds to 0 - players only get income at turn start
            self.board_v2.player_funds[player_id] = 0
            
            # Update army funds for backward compatibility
            army = self.board_v2.get_army_for_player(player_id)
            if army:
                self.board_v2.army_funds[army] = 0
                
    def _update_property_ownership(self, tile: GameTile, new_army: Army) -> None:
        """Update property ownership and adjust player statistics."""
        old_army = tile.mapTile.army
        income = 1000  # Standard income per property
        
        # Convert army to player_id and update using helper method
        new_player_id = self.board_v2.get_player_for_army(new_army) if new_army else None
        self.board_v2.set_tile_owner(tile, new_player_id)
        
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
            
    def _update_player_funds(self, player_id: int, amount: int) -> None:
        """Update funds for a player."""
        self.board_v2.update_player_funds(player_id, amount)
                
    def _get_player_funds(self, player_id: int) -> int:
        """Get current funds for a player."""
        return self.board_v2.player_funds.get(player_id, 0)
    
    def _update_player_statistics(self):
        """Update game statistics for all players."""
        # Reset all player counters
        for player_id in range(self.player_manager.get_player_count()):
            self.board_v2.player_troops[player_id] = 0
            self.board_v2.player_properties[player_id] = 0
            
        # Count units and properties in single pass
        for tile in self.board_v2.grid:
            # Count units
            if tile.unit and tile.unit.player_id is not None:
                self.board_v2.player_troops[tile.unit.player_id] += 1
                        
            # Count properties
            if tile.mapTile and tile.mapTile.type in {MapType.CITY, MapType.FACTORY, MapType.AIRPORT, MapType.PORT, 
                                                     MapType.BASE_TOWER_0, MapType.BASE_TOWER_1, MapType.BASE_TOWER_2, 
                                                     MapType.BASE_TOWER_3, MapType.BASE_TOWER_4}:
                player_id = self._get_tile_player(tile)
                if player_id is not None:
                    self.board_v2.player_properties[player_id] += 1
    
    def _set_all_player_units_active(self, player_id: int):
        """Set all units for a player as active (can move/attack)."""
        for tile in self.board_v2.grid:
            if tile.unit and tile.unit.player_id == player_id:
                tile.unit.can_move = True
                tile.unit.can_attack = True
                tile.unit.has_attacked = False
                tile.unit.status.action_taken = False  # Reset the done flag
                if tile.unit.type in [UnitType.INFANTRY, UnitType.MECH]:
                    tile.unit.can_capture = True
    
    def _set_all_player_units_inactive(self, player_id: int):
        """Set all units for a player as inactive (cannot move/attack)."""
        for tile in self.board_v2.grid:
            if tile.unit and tile.unit.player_id == player_id:
                self._set_unit_inactive(tile.unit)
    
    def get_player_income(self, player_id: int) -> int:
        """Calculate income for a player based on owned properties."""
        income = 0
        for tile in self.board_v2.grid:
            if self.board_v2.is_tile_owned_by_player(tile, player_id):
                # Each property gives 1000 funds
                if tile.mapTile and tile.mapTile.is_property():
                    income += 1000
        return income
            
    def unit_create_v2(self, player_id: int, unit_type: str, x: int, y: int) -> Unit:
        """Create a new unit at the specified coordinates (player-based version)."""
        from core.production_system import ProductionSystem
        
        # Validation
        self._validate_coordinates(x, y)
        self._validate_game_active()
        
        # Check tile is empty
        if self.unit_at(x, y):
            raise ValueError(f'Tile at ({x}, {y}) already occupied')
        
        # Check funds
        unit_type_enum = UnitType[unit_type] if isinstance(unit_type, str) else unit_type
        cost = ProductionSystem.UNIT_COSTS.get(unit_type_enum, 99999)
        funds = self._get_player_funds(player_id)
        if funds < cost:
            raise ValueError(f'Insufficient funds: {funds} < {cost}')
        
        # Create the unit with player ID
        # Read unit config from config.ini
        import configparser
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
        
        # Get sprite color for this player
        sprite_color = self.board_v2.get_player_sprite_color(player_id)
        
        unit = Unit.create_with_player(player_id, unit_type_enum, unit_config, sprite_color)
        self.tile_at(x, y).unit = unit
        
        # Mark unit as unable to act on creation turn
        self._set_unit_inactive(unit)
        # Double-check the flags are set correctly
        unit.can_move = False
        unit.can_attack = False
        unit.can_capture = False
        
        # Deduct funds
        self._update_player_funds(player_id, -cost)
        
        # Update statistics
        self._update_player_statistics()
        
        return unit
                        
    def _get_unit_player(self, unit: Unit) -> Optional[int]:
        """Get player ID for a unit"""
        return self.board_v2.get_player_for_army(unit.army)
        
    def _get_tile_player(self, tile: GameTile) -> Optional[int]:
        """Get player ID for a tile"""
        if tile.mapTile and tile.mapTile.army:
            return self.board_v2.get_player_for_army(tile.mapTile.army)
        return None
    
    def _get_player_for_army(self, army: Army) -> Optional[int]:
        """Get player ID for an army"""
        return self.board_v2.get_player_for_army(army)
        
    def _advance_to_next_army(self) -> None:
        """Advance to the next player's turn."""
        # Use player-based turn order
        self.board_v2.current_player = self.board_v2.get_next_player()
        
            
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
    
    def produce_unit_at_facility(self, x: int, y: int, unit_type: str) -> Unit:
        """Create unit at production facility."""
        # Validate coordinates
        self._validate_coordinates(x, y)
        self._validate_game_active()
        
        # Get tile
        tile = self.tile_at(x, y)
        
        # Validate it's a production facility
        if not tile.mapTile or tile.mapTile.type not in [MapType.FACTORY, MapType.AIRPORT, MapType.PORT]:
            raise ValueError(f"No production facility at ({x}, {y})")
        
        # Validate ownership
        if tile.mapTile.army != self.board.current_turn:
            raise ValueError("Facility not owned by current player")
        
        # Validate not occupied
        if tile.unit:
            raise ValueError("Facility is occupied")
        
        # Get current player ID
        current_player_id = self.board_v2.current_player
        
        # Use unit_create_v2 method which handles everything
        return self.unit_create_v2(current_player_id, unit_type, x, y)
    
        
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
        """Validate it's the unit's turn."""
        if unit.player_id != self.board.current_player:
            raise ValueError(f"Not this unit's turn (unit player: {unit.player_id}, current player: {self.board.current_player})")
    
    def _validate_unit_can_act(self, unit: Unit, action: str) -> None:
        """Validate unit can perform the specified action."""
        if action == 'move' and not unit.can_move:
            raise ValueError('Unit cannot move this turn')
        elif action == 'attack':
            if not unit.can_attack:
                raise ValueError('Unit cannot attack this turn')
            if hasattr(unit, 'is_hidden') and unit.is_hidden:
                raise ValueError('Hidden units cannot attack')
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
        unit.status.action_taken = True
    
    
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
        
        # Check for ambush along the path
        ambush_location = self.check_for_ambush(unit, x, y, x2, y2)
        if ambush_location:
            # Unit gets ambushed - move to position before the hidden enemy
            ambush_x, ambush_y = ambush_location
            if ambush_x == x and ambush_y == y:
                # Can't move at all
                unit.can_move = False
                unit.can_attack = False  # Ambushed units lose all actions
                return unit
            else:
                # Move to the ambush location instead of intended destination
                x2, y2 = ambush_x, ambush_y
        
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
        unit.can_move = False
        
        # If ambushed, unit loses all actions
        if ambush_location:
            unit.can_attack = False
        else:
            # Only indirect units lose attack ability after moving
            if unit.is_indirect():
                unit.can_attack = False
        
        return unit
    
    def get_unit_valid_moves(self, unit: Unit) -> List[Tuple[int, int]]:
        """Get all valid moves for a unit."""
        tile = self.tile_from_unit(unit)
        if not tile:
            return []
        
        validator = EnhancedMovementValidator(self.board, self)
        return validator.get_valid_moves(unit, tile.x, tile.y)
    
    def get_valid_moves(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get valid moves for a unit at specified coordinates."""
        unit = self._validate_unit_exists(x, y)
        return self.get_unit_valid_moves(unit)
    
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
    
    def get_movement_preview(self, x: int, y: int, x2: int, y2: int) -> Dict:
        """Preview movement path and fuel cost."""
        try:
            unit = self._validate_unit_exists(x, y)
            validator = EnhancedMovementValidator(self.board, self)
            result = validator.validate_movement(unit, x, y, x2, y2)
            
            return {
                'valid': result.valid,
                'fuel_cost': result.fuel_required,
                'path_found': result.path_found,
                'reason': result.reason if not result.valid else None,
                'distance': abs(x2 - x) + abs(y2 - y)
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def unit_can_move_to(self, unit: Unit, x: int, y: int) -> bool:
        """Check if unit can reach destination."""
        tile = self.tile_from_unit(unit)
        if not tile:
            return False
        
        validator = EnhancedMovementValidator(self.board, self)
        result = validator.validate_movement(unit, tile.x, tile.y, x, y)
        return result.valid
    
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
        
        # Validate no friendly fire
        if attacker.player_id == defender.player_id:
            raise ValueError("Cannot attack friendly units")
        
        # Validate attack range
        distance = abs(attacker_x - defender_x) + abs(attacker_y - defender_y)
        if distance < attacker.status.rangemin or distance > attacker.status.rangemax:
            raise ValueError(f"Target out of range. Unit range: {attacker.status.rangemin}-{attacker.status.rangemax}, distance: {distance}")
        
        # Validate unit can damage target
        if not attacker.is_attackable(defender):
            raise ValueError(f"{attacker.type.name} cannot attack {defender.type.name}")
        
        # Use enhanced combat system
        combat_system = EnhancedCombatSystem(self)
        result = combat_system.execute_enhanced_combat(
            attacker_x, attacker_y, defender_x, defender_y
        )
        
        # Mark attacker as having attacked and acted
        attacker.has_attacked = True
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
            self._update_player_statistics()
    
    # =============================================================================
    # TRANSPORT SYSTEM WRAPPERS
    # =============================================================================
    
    def is_transport_unit(self, unit: Unit) -> bool:
        """Check if unit is a transport."""
        return self.transport_system.is_transport_unit(unit)
    
    def get_transport_capability(self, unit: Unit) -> Optional[Dict]:
        """Get transport capacity info."""
        return self.transport_system.get_transport_capability(unit)
    
    def get_transport_cargo_info(self, unit: Unit) -> List[Dict]:
        """Get information about units loaded in transport."""
        return self.transport_system.get_cargo_info(unit)
    
    def load_transport_unit(self, transport_x: int, transport_y: int, 
                           cargo_x: int, cargo_y: int) -> Dict:
        """Load unit into transport."""
        transport = self.unit_at(transport_x, transport_y)
        cargo = self.unit_at(cargo_x, cargo_y)
        
        if not transport or not cargo:
            return {'success': False, 'error': 'Unit not found'}
        
        result = self.transport_system.load_unit_enhanced(
            transport, cargo, transport_x, transport_y, cargo_x, cargo_y
        )
        
        if result.success:
            # Remove cargo from board
            self.tile_at(cargo_x, cargo_y).unit = None
            # Update statistics
            self._update_player_statistics()
            
        return {'success': result.success, 'message': result.message}
    
    def unload_transport_unit(self, transport_x: int, transport_y: int,
                             unload_x: int, unload_y: int, cargo_index: int = 0) -> Dict:
        """Unload unit from transport."""
        transport = self.unit_at(transport_x, transport_y)
        
        if not transport:
            return {'success': False, 'error': 'Transport not found'}
        
        result = self.transport_system.unload_unit_enhanced(
            transport, cargo_index, transport_x, transport_y, unload_x, unload_y
        )
        
        if result.success and result.unloaded_unit:
            # Place unloaded unit on board
            self.tile_at(unload_x, unload_y).unit = result.unloaded_unit
            # Mark unit as unable to act
            self._set_unit_inactive(result.unloaded_unit)
            # Update statistics
            self._update_player_statistics()
            
        return {'success': result.success, 'message': result.message}
    
    def can_transport_move(self, unit: Unit) -> bool:
        """Check if transport can still move."""
        return unit.can_move and not getattr(unit.status, 'has_moved_this_turn', False)
    
    def can_transport_load_unload(self, unit: Unit) -> bool:
        """Check if transport can load/unload units."""
        # Transports can always unload during their turn
        # They can unload after moving or after unloading other units
        return unit.player_id == self.board.current_player
    
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
    
    def unit_join(self, moving_x: int, moving_y: int, target_x: int, target_y: int) -> Dict:
        """Join two units of the same type together.
        
        Rules:
        - Units must be the same type
        - Target unit must have 9 HP or less
        - Combined HP/fuel/ammo respects max values
        - Excess HP over 10 is converted to funds (10% of unit cost per HP)
        - The joined unit ends its turn (moving unit is absorbed)
        
        Args:
            moving_x, moving_y: Position of unit that is moving to join
            target_x, target_y: Position of stationary unit to join into
            
        Returns:
            Dict with success status and any refunded amount
        """
        try:
            # Validate coordinates
            self._validate_coordinates(moving_x, moving_y, target_x, target_y)
            self._validate_game_active()
            
            # Get units
            moving_unit = self._validate_unit_exists(moving_x, moving_y)
            target_unit = self._validate_unit_exists(target_x, target_y)
            
            # Validate ownership
            self._validate_unit_turn(moving_unit)
            if moving_unit.player_id != target_unit.player_id:
                raise ValueError("Cannot join with enemy units")
            
            # Validate unit can move
            self._validate_unit_can_act(moving_unit, 'move')
            
            # Validate same unit type
            if moving_unit.type != target_unit.type:
                raise ValueError("Can only join units of the same type")
            
            # Validate target HP requirement
            if target_unit.status.hp > 90:  # 9 HP in display = 90 HP internally
                raise ValueError("Target unit must have 9 HP or less to join")
            
            # Validate movement to target - special handling for join
            # Check if we can reach the target position
            validator = EnhancedMovementValidator(self.board, self)
            # Temporarily remove target unit to check if we can reach that position
            target_tile = self.tile_at(target_x, target_y)
            temp_unit = target_tile.unit
            target_tile.unit = None
            
            move_result = validator.validate_movement(moving_unit, moving_x, moving_y, target_x, target_y)
            
            # Restore target unit
            target_tile.unit = temp_unit
            
            if not move_result.valid:
                raise ValueError(f"Cannot reach target: {move_result.reason}")
            
            # Calculate combined stats
            combined_hp = moving_unit.status.hp + target_unit.status.hp
            combined_fuel = min(moving_unit.status.fuel + target_unit.status.fuel - move_result.fuel_required, 
                              moving_unit.config.max_fuel)
            combined_ammo = min(moving_unit.status.ammo + target_unit.status.ammo, 
                              moving_unit.config.max_ammo)
            
            # Calculate fund refund for excess HP
            refund = 0
            if combined_hp > 100:
                excess_hp = combined_hp - 100
                # Convert to display HP (divide by 10) for refund calculation
                excess_display_hp = excess_hp // 10
                refund = (moving_unit.config.cost * excess_display_hp) // 10
                combined_hp = 100
            
            # Apply the join
            # Remove moving unit
            moving_tile = self.tile_at(moving_x, moving_y)
            moving_tile.unit = None
            
            # Update target unit with combined stats
            target_unit.status.hp = combined_hp
            target_unit.status.fuel = combined_fuel
            target_unit.status.ammo = combined_ammo
            
            # The joined unit ends its turn (moving unit was absorbed)
            self._set_unit_inactive(target_unit)
            
            # Add refund to player funds
            if refund > 0:
                player_id = target_unit.player_id
                self.board_v2.player_funds[player_id] += refund
            
            return {
                'success': True,
                'refund': refund,
                'combined_hp': combined_hp,
                'combined_fuel': combined_fuel,
                'combined_ammo': combined_ammo
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def unit_hide(self, x: int, y: int) -> Dict:
        """Hide a stealth fighter or submarine.
        
        Hidden units:
        - Are invisible to enemies unless adjacent
        - Cannot be attacked by most units
        - Consume extra fuel per turn (5 for Stealth when unhidden, 8 when hidden)
        - Cannot attack while hidden
        
        Args:
            x, y: Position of unit to hide
            
        Returns:
            Dict with success status
        """
        try:
            # Validate
            self._validate_coordinates(x, y)
            self._validate_game_active()
            
            # Get unit
            unit = self._validate_unit_exists(x, y)
            self._validate_unit_turn(unit)
            
            # Check if unit can hide
            if unit.type not in [UnitType.STEALTH, UnitType.SUB]:
                raise ValueError("Only Stealth fighters and Submarines can hide")
            
            # Check if already hidden
            if unit.is_hidden:
                raise ValueError("Unit is already hidden")
            
            # Check if unit has moved (can only hide if hasn't moved)
            if not unit.can_move:
                raise ValueError("Unit must not have moved to hide")
            
            # Hide the unit
            unit.is_hidden = True
            
            # End unit's turn (hiding ends turn)
            self._set_unit_inactive(unit)
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def unit_unhide(self, x: int, y: int) -> Dict:
        """Unhide a stealth fighter or submarine.
        
        Unhiding:
        - Makes unit visible again
        - Allows unit to attack
        - Does NOT end the unit's turn
        
        Args:
            x, y: Position of unit to unhide
            
        Returns:
            Dict with success status
        """
        try:
            # Validate
            self._validate_coordinates(x, y)
            self._validate_game_active()
            
            # Get unit
            unit = self._validate_unit_exists(x, y)
            self._validate_unit_turn(unit)
            
            # Check if unit can unhide
            if unit.type not in [UnitType.STEALTH, UnitType.SUB]:
                raise ValueError("Only Stealth fighters and Submarines can unhide")
            
            # Check if hidden
            if not unit.is_hidden:
                raise ValueError("Unit is not hidden")
            
            # Unhide the unit
            unit.is_hidden = False
            
            # Unhiding does NOT end turn - unit can still act
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def is_unit_visible_to_player(self, unit: Unit, viewing_player_id: int) -> bool:
        """Check if a unit is visible to a specific player.
        
        Visibility rules:
        - Own units are always visible
        - Non-hidden enemy units are always visible
        - Hidden enemy units are visible only if adjacent to an enemy unit
        
        Args:
            unit: The unit to check visibility for (must have x, y attributes)
            viewing_player_id: The player viewing the board
            
        Returns:
            True if unit should be visible to the viewing player
        """
        # Own units always visible
        if unit.player_id == viewing_player_id:
            return True
        
        # Non-hidden units always visible
        if not unit.is_hidden:
            return True
        
        # Hidden enemy units only visible if adjacent to a unit of the viewing player
        # Note: requires unit to have x, y attributes set
        if hasattr(unit, 'x') and hasattr(unit, 'y'):
            return self.is_adjacent_to_player_unit(unit.x, unit.y, viewing_player_id)
        
        return False
    
    def is_adjacent_to_player_unit(self, x: int, y: int, player_id: int) -> bool:
        """Check if a position is adjacent to any unit owned by the specified player.
        
        Args:
            x, y: Position to check
            player_id: Player to check for adjacent units
            
        Returns:
            True if any unit owned by player_id is adjacent to the position
        """
        # Check all 4 adjacent tiles
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            adj_x, adj_y = x + dx, y + dy
            
            # Check bounds
            if not (0 <= adj_x < self.board.width and 0 <= adj_y < self.board.height):
                continue
            
            # Check for friendly unit
            tile = self.tile_at(adj_x, adj_y)
            if tile and tile.unit and tile.unit.player_id == player_id:
                return True
        
        return False
    
    def get_visible_units_for_player(self, viewing_player_id: int) -> List[Dict]:
        """Get all units visible to a specific player.
        
        Args:
            viewing_player_id: The player viewing the board
            
        Returns:
            List of unit data dictionaries for units visible to the player
        """
        visible_units = []
        
        for i, tile in enumerate(self.board.grid):
            if tile.unit:
                # Store unit position for visibility check
                unit_x = i % self.board.width
                unit_y = i // self.board.width
                
                # Temporarily store position on unit for visibility check
                # (units don't normally store their position)
                unit = tile.unit
                unit.x = unit_x
                unit.y = unit_y
                
                if self.is_unit_visible_to_player(unit, viewing_player_id):
                    from core.api_response import APIResponse
                    unit_info = APIResponse.unit_info(unit)
                    unit_info['x'] = unit_x
                    unit_info['y'] = unit_y
                    visible_units.append(unit_info)
                
                # Clean up temporary position
                delattr(unit, 'x')
                delattr(unit, 'y')
        
        return visible_units
    
    def check_for_ambush(self, moving_unit: Unit, from_x: int, from_y: int, to_x: int, to_y: int) -> Optional[Tuple[int, int]]:
        """Check if a unit would be ambushed by hidden enemies along its movement path.
        
        When a unit moves into a tile with a hidden enemy, it gets ambushed:
        - Movement stops immediately at the tile before the hidden enemy
        - Turn ends (can't attack or act)
        - Hidden unit becomes visible (discovered)
        
        Args:
            moving_unit: Unit that is moving
            from_x, from_y: Starting position
            to_x, to_y: Intended destination
            
        Returns:
            (x, y) of where the unit should stop (before the ambush), or None if no ambush
        """
        # For simplicity, we'll check a straight line path
        # In a real implementation, this would follow the actual pathfinding route
        
        # Calculate direction
        dx = 0 if to_x == from_x else (1 if to_x > from_x else -1)
        dy = 0 if to_y == from_y else (1 if to_y > from_y else -1)
        
        # Check each tile along the path
        current_x, current_y = from_x, from_y
        
        while current_x != to_x or current_y != to_y:
            # Move one step
            next_x = current_x + dx if current_x != to_x else current_x
            next_y = current_y + dy if current_y != to_y else current_y
            
            # Check for hidden enemy at next position
            tile = self.tile_at(next_x, next_y)
            if tile and tile.unit:
                enemy_unit = tile.unit
                # Check if it's a hidden enemy unit
                if (enemy_unit.player_id != moving_unit.player_id and 
                    enemy_unit.is_hidden):
                    # Ambush! Return current position (before the hidden enemy)
                    if current_x == from_x and current_y == from_y:
                        # Can't move at all if ambushed on first step
                        return (from_x, from_y)
                    else:
                        return (current_x, current_y)
            
            # Continue to next tile
            current_x, current_y = next_x, next_y
        
        return None
    
    def unit_select(self, x: int, y: int) -> None:
        """Select a unit or tile at the given coordinates."""
        # Validate coordinates
        self._validate_coordinates(x, y)
        
        # Clear previous highlights
        for tile in self.board.grid:
            tile.can_be_moved_to = False
            tile.can_be_attacked = False
        
        # Get the tile
        tile = self.tile_at(x, y)
        
        # If clicking on the currently selected tile, deselect
        if self.board.selected and self.board.selected.x == x and self.board.selected.y == y:
            self.board.selected = None
        else:
            # Select the new tile
            self.board.selected = tile
            
            # If selecting a unit that belongs to current player
            if tile and tile.unit and tile.unit.player_id == self.board.current_player:
                unit = tile.unit
                
                # Mark movement tiles if unit can move
                if unit.can_move and not getattr(unit, 'done', False):
                    valid_moves = self.get_valid_moves(x, y)
                    for move_x, move_y in valid_moves:
                        move_tile = self.tile_at(move_x, move_y)
                        if move_tile:
                            move_tile.can_be_moved_to = True
                
                # Mark attack targets if unit can attack
                if unit.can_attack and not getattr(unit, 'done', False):
                    # Get unit's attack range from config
                    min_range = unit.config.rangemin if hasattr(unit, 'config') else 1
                    max_range = unit.config.rangemax if hasattr(unit, 'config') else 1
                    
                    # Check all tiles within attack range
                    for dy in range(-max_range, max_range + 1):
                        for dx in range(-max_range, max_range + 1):
                            target_x = x + dx
                            target_y = y + dy
                            
                            # Skip if out of bounds
                            if target_x < 0 or target_x >= self.board.width or target_y < 0 or target_y >= self.board.height:
                                continue
                            
                            # Calculate Manhattan distance
                            distance = abs(dx) + abs(dy)
                            
                            # Skip if out of range
                            if distance < min_range or distance > max_range:
                                continue
                            
                            # Skip self
                            if distance == 0:
                                continue
                            
                            # Check if there's an enemy unit
                            target_tile = self.tile_at(target_x, target_y)
                            if target_tile and target_tile.unit and target_tile.unit.player_id != unit.player_id:
                                target_tile.can_be_attacked = True
    
    def capture_tile(self, x: int, y: int) -> None:
        """Capture a property with an infantry or mech unit."""
        # Validate coordinates and game state
        self._validate_coordinates(x, y)
        self._validate_game_active()
        
        # Get tile and unit
        tile = self.tile_at(x, y)
        unit = tile.unit
        
        # Validate unit exists and can capture
        if not unit:
            raise ValueError(f"No unit at ({x}, {y})")
        
        if unit.player_id != self.board.current_player:
            raise ValueError("Not this unit's turn")
        
        # Only infantry and mech can capture
        if unit.type not in [UnitType.INFANTRY, UnitType.MECH]:
            raise ValueError(f"{unit.type.name} units cannot capture")
        
        # Check if unit can capture this turn
        if not unit.can_capture:
            raise ValueError("Unit has already acted this turn")
        
        # Check if there's a capturable property
        if not tile.mapTile or tile.mapTile.type not in [
            MapType.CITY, MapType.FACTORY, MapType.AIRPORT, MapType.PORT,
            MapType.BASE_TOWER_1, MapType.BASE_TOWER_2, MapType.BASE_TOWER_3, MapType.BASE_TOWER_4
        ]:
            raise ValueError("No capturable property at this location")
        
        # Can't capture own properties
        if tile.mapTile.army == unit.army:
            raise ValueError("Cannot capture own property")
        
        # Calculate capture power (HP / 10, rounded up)
        capture_power = math.ceil(unit.status.hp / 10)
        
        # Apply capture damage
        tile.capture_hp = max(0, tile.capture_hp - capture_power)
        
        # If captured, change ownership
        if tile.capture_hp <= 0:
            old_army = tile.mapTile.army
            self._update_property_ownership(tile, unit.army)
            
            # Reset capture HP to full after ownership change
            tile.capture_hp = 20
            
            # Check for HQ capture victory
            if tile.mapTile.type in [MapType.BASE_TOWER_1, MapType.BASE_TOWER_2, 
                                      MapType.BASE_TOWER_3, MapType.BASE_TOWER_4]:
                self._check_hq_capture_victory(old_army)
        
        # Mark unit as having acted
        self._set_unit_inactive(unit)
    
    def capture_tile_enhanced(self, x: int, y: int) -> Dict:
        """Enhanced capture with detailed feedback."""
        try:
            # Get initial state
            tile = self.tile_at(x, y)
            initial_hp = tile.capture_hp
            initial_owner = tile.mapTile.army if tile.mapTile else None
            
            # Execute capture
            self.capture_tile(x, y)
            
            # Get final state
            final_hp = tile.capture_hp
            final_owner = tile.mapTile.army if tile.mapTile else None
            captured = final_hp <= 0
            
            return {
                'success': True,
                'capture_progress': {
                    'initial_hp': initial_hp,
                    'final_hp': final_hp,
                    'damage_dealt': initial_hp - final_hp,
                    'captured': captured
                },
                'ownership': {
                    'previous': initial_owner.name if initial_owner else 'Neutral',
                    'current': final_owner.name if final_owner else 'Neutral'
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_capture_preview(self, x: int, y: int) -> Dict:
        """Preview capture without executing it."""
        try:
            tile = self.tile_at(x, y)
            unit = tile.unit
            
            if not unit or unit.type not in [UnitType.INFANTRY, UnitType.MECH]:
                return {'can_capture': False, 'reason': 'Invalid unit type'}
            
            if not tile.mapTile or tile.mapTile.type not in [
                MapType.CITY, MapType.FACTORY, MapType.AIRPORT, MapType.PORT,
                MapType.BASE_TOWER_1, MapType.BASE_TOWER_2, MapType.BASE_TOWER_3, MapType.BASE_TOWER_4
            ]:
                return {'can_capture': False, 'reason': 'No capturable property'}
            
            if tile.mapTile.army == unit.army:
                return {'can_capture': False, 'reason': 'Already owned'}
            
            capture_power = math.ceil(unit.status.hp / 10)
            turns_to_capture = math.ceil(tile.capture_hp / capture_power)
            
            return {
                'can_capture': True,
                'current_hp': tile.capture_hp,
                'capture_power': capture_power,
                'turns_to_capture': turns_to_capture,
                'property_type': tile.mapTile.type.name,
                'current_owner': tile.mapTile.army.name if tile.mapTile.army else 'Neutral'
            }
        except Exception as e:
            return {'can_capture': False, 'reason': str(e)}
    
    # =============================================================================
    # GAME STATE MANAGEMENT
    # =============================================================================
    
    def army_end_turn(self) -> None:
        """End the current army's turn and advance to the next."""
        current_army = self.board.current_turn
        
        # Set all current army units to inactive
        player_id = self.board_v2.get_player_for_army(current_army)
        if player_id is not None:
            self._set_all_player_units_inactive(player_id)
        
        # Apply turn-end effects (repairs, fuel consumption, etc.)
        self._apply_turn_end_effects(current_army)
        
        # Advance to next turn
        self._advance_to_next_army()
        
        # Activate all units for the new turn
        new_army = self.board.current_turn
        player_id = self.board_v2.get_player_for_army(new_army)
        if player_id is not None:
            self._set_all_player_units_active(player_id)
        
        # Apply turn-start effects (income, auto-resupply)
        new_player_id = self.board_v2.current_player
        self._apply_turn_start_effects(new_player_id)
    
    def _apply_turn_end_effects(self, army: Army) -> None:
        """Apply effects at the end of an army's turn."""
        # Note: Fuel consumption moved to turn start AFTER refueling
        pass
    
    def _check_hq_capture_victory(self, defeated_army: Army) -> None:
        """Check if HQ capture results in victory."""
        # Mark game as ended
        self.board.game_active = False
        
        # Determine winner - current turn's army captured the HQ
        winner_army = self.board.current_turn
        winner_player_id = self._get_player_for_army(winner_army)
        
        if winner_player_id is not None:
            winner = self.player_manager.get_player(winner_player_id)
            self.board.winner = winner.name if winner else winner_army.name
        else:
            self.board.winner = winner_army.name
            
        self.board.victory_type = "HQ Capture"
        
        # Log victory
        self.log(f"Game ended: {self.board.winner} wins by HQ capture!")
    
    def check_win_condition(self) -> Optional[Dict]:
        """Check if game has ended due to victory conditions."""
        if not self.board.game_active:
            return {
                'game_ended': True,
                'winner': self.board.winner,
                'victory_type': self.board.victory_type
            }
        
        # Check unit elimination
        army_units = {}
        # Get list of armies actually in the game
        active_armies = set()
        for player_id in self.board.turn_order:
            army = self.board.get_army_for_player(player_id)
            if army:
                active_armies.add(army)
                army_units[army] = 0
        
        # If no armies found through players, use default
        if not active_armies:
            active_armies = {Army.RED, Army.BLUE}
            for army in active_armies:
                army_units[army] = 0
        
        # Count units for each army
        for tile in self.board.grid:
            if tile.unit and tile.unit.army in active_armies:
                army_units[tile.unit.army] = army_units.get(tile.unit.army, 0) + 1
        
        # Check if any active army has no units
        for army, count in army_units.items():
            if army in active_armies and count == 0:
                # Find who has units (the winner)
                for winner_army, winner_count in army_units.items():
                    if winner_count > 0:
                        self.board.game_active = False
                        winner_player_id = self._get_player_for_army(winner_army)
                        
                        if winner_player_id is not None:
                            winner = self.player_manager.get_player(winner_player_id)
                            self.board.winner = winner.name if winner else winner_army.name
                        else:
                            self.board.winner = winner_army.name
                            
                        self.board.victory_type = "Elimination"
                        
                        return {
                            'game_ended': True,
                            'winner': self.board.winner,
                            'victory_type': self.board.victory_type
                        }
        
        return None
    
    def _apply_turn_start_effects(self, player_id: int) -> None:
        """Apply effects at the start of a player's turn."""
        if player_id is None:
            return
            
        # FIRST: Reset all unit states for the active player
        self._set_all_player_units_active(player_id)
        
        # SECOND: Auto-resupply from APCs and bases (before fuel consumption)
        self._apply_auto_resupply(player_id)
        
        # SECOND: Apply facility repair (after resupply, before fuel consumption)
        self._apply_facility_repair(player_id)
        
        # THIRD: Consume fuel for air and naval units
        for tile in self.board.grid:
            if tile.unit and tile.unit.player_id == player_id:
                unit = tile.unit
                # Use the unit's fuel_use() method which handles special cases
                fuel_consumption = unit.fuel_use()
                if fuel_consumption > 0:
                    unit.status.fuel = max(0, unit.status.fuel - fuel_consumption)
                    
                    # Crash/sink if out of fuel
                    if unit.status.fuel == 0:
                        unit.status.hp = 0
        
        # FOURTH: Add income from properties
        income = self.board_v2.player_properties.get(player_id, 0) * 1000
        self._update_player_funds(player_id, income)
    
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
    
    def _apply_auto_resupply(self, player_id: int) -> None:
        """Auto-resupply units at the start of their turn."""
        if player_id is None:
            return
            
        # Resupply from appropriate buildings based on unit type
        for tile in self.board.grid:
            if tile.unit and tile.unit.player_id == player_id:
                unit = tile.unit
                # Check if unit is on a friendly resupply building
                if self.board_v2.is_tile_owned_by_player(tile, player_id):
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
            if tile.unit and tile.unit.player_id == player_id and tile.unit.type == UnitType.APC:
                apc = tile.unit
                # Check all adjacent tiles
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    adj_x, adj_y = tile.x + dx, tile.y + dy
                    if self.coord_valid(adj_x, adj_y):
                        adj_unit = self.unit_at(adj_x, adj_y)
                        if adj_unit and adj_unit.player_id == player_id:
                            # Resupply adjacent friendly units
                            adj_unit.status.fuel = adj_unit.config.max_fuel
                            adj_unit.status.ammo = adj_unit.config.max_ammo
    
    def _apply_facility_repair(self, player_id: int) -> None:
        """Auto-repair units at facilities at the start of their turn."""
        if player_id is None:
            return
            
        # Repair units at appropriate facilities based on unit type
        for tile in self.board.grid:
            if tile.unit and tile.unit.player_id == player_id:
                unit = tile.unit
                # Only repair if unit is damaged
                if unit.status.hp < 100:
                    # Check if unit is on a friendly repair facility
                    if self.board_v2.is_tile_owned_by_player(tile, player_id):
                        can_repair = False
                        
                        # Check unit type and facility compatibility
                        if unit.status.cls == UnitClass.AIR:
                            # Air units repair at airports
                            can_repair = tile.mapTile.type == MapType.AIRPORT
                        elif unit.status.cls in {UnitClass.SEA, UnitClass.LANDER}:
                            # Naval units repair at ports
                            can_repair = tile.mapTile.type == MapType.PORT
                        elif unit.status.cls in {UnitClass.BOOTS, UnitClass.TREADS, UnitClass.TYRES, UnitClass.FOOT, UnitClass.PIPE}:
                            # Land units repair at factories
                            can_repair = tile.mapTile.type == MapType.FACTORY
                        
                        if can_repair:
                            # Calculate repair cost and amount
                            unit_cost = ProductionSystem.UNIT_COSTS.get(unit.type, 1000)
                            current_hp = unit.status.hp
                            max_repair = min(20, 100 - current_hp)  # Max 2 HP (20 points) per turn
                            
                            if max_repair > 0:
                                # Calculate cost per HP (1 HP = 10 points)
                                cost_per_hp = unit_cost // 10  # 10% of unit cost per HP
                                current_funds = self._get_player_funds(player_id)
                                
                                # Calculate how much we can actually repair based on funds
                                affordable_hp_points = min(max_repair, (current_funds * 10) // cost_per_hp)
                                
                                if affordable_hp_points > 0:
                                    # Apply repair
                                    unit.status.hp = min(100, current_hp + affordable_hp_points)
                                    # Deduct cost
                                    repair_cost = (cost_per_hp * affordable_hp_points) // 10
                                    self._update_player_funds(player_id, -repair_cost)
                                    
                                    self.log(f"Repaired {unit.type.name} at ({tile.x},{tile.y}) by {affordable_hp_points//10} HP for {repair_cost} funds")
    
    def get_army_economy(self, army: Army) -> Dict:
        """Get economic information for an army (legacy compatibility)."""
        player_id = self.board_v2.get_player_for_army(army)
        if player_id is None:
            return {
                'funds': 0,
                'properties': 0,
                'troops': 0,
                'total_income': 0
            }
        
        return {
            'funds': self.board_v2.player_funds.get(player_id, 0),
            'properties': self.board_v2.player_properties.get(player_id, 0),
            'troops': self.board_v2.player_troops.get(player_id, 0),
            'total_income': self.board_v2.player_properties.get(player_id, 0) * 1000
        }
    
    def get_army_facilities(self, army: Army) -> List[Dict]:
        """Get list of facilities owned by an army (legacy compatibility)."""
        facilities = []
        
        for y in range(self.board.height):
            for x in range(self.board.width):
                tile = self.tile_at(x, y)
                if tile.mapTile and tile.mapTile.army == army:
                    if tile.mapTile.type in {MapType.FACTORY, MapType.AIRPORT, MapType.PORT}:
                        facilities.append({
                            'x': x,
                            'y': y,
                            'type': tile.mapTile.type.name,
                            'can_produce': True
                        })
        
        return facilities
    
    def get_production_options(self, x: int, y: int, army: Army) -> Dict:
        """Get available units that can be produced at a facility."""
        tile = self.tile_at(x, y)
        
        # Check if it's a valid production facility
        if not tile or not tile.mapTile:
            return {"error": "Invalid tile"}
        
        facility_type = tile.mapTile.type
        if facility_type not in {MapType.FACTORY, MapType.AIRPORT, MapType.PORT}:
            return {"error": "Not a production facility"}
        
        # Check ownership
        if tile.mapTile.army != army:
            return {"error": "Facility not owned by current player"}
        
        # Check if occupied
        if self.unit_at(x, y):
            return {"error": "Facility is occupied"}
        
        # Define production options by facility type
        production_units = {
            MapType.FACTORY: ['INFANTRY', 'MECH', 'RECON', 'TANK', 'MEDIUMTANK', 'NEOTANK', 'MEGATANK',
                            'APC', 'ARTILLERY', 'ROCKET', 'ANTIAIR', 'MISSILE', 'PIPERUNNER'],
            MapType.AIRPORT: ['FIGHTER', 'BOMBER', 'BCOPTER', 'TCOPTER', 'STEALTH', 'BLACKBOMB'],
            MapType.PORT: ['BATTLESHIP', 'CRUISER', 'SUB', 'LANDER', 'CARRIER', 'BLACKBOAT']
        }
        
        # Get unit costs from production system
        from core.production_system import ProductionSystem
        from core.unit import UnitType
        
        # Use default costs from production system
        production_system = ProductionSystem(self)
        unit_costs = production_system.UNIT_COSTS
        
        available_units = []
        units = production_units.get(facility_type, [])
        
        # Get player funds
        player_id = self._get_player_for_army(army)
        player_funds = self.board_v2.player_funds.get(player_id, 0)
        
        for unit_name in units:
            try:
                unit_type = UnitType[unit_name]
                cost = unit_costs.get(unit_type, 0)
                available_units.append({
                    'type': unit_name,
                    'cost': cost,
                    'can_afford': player_funds >= cost
                })
            except KeyError:
                # Skip invalid unit types
                continue
        
        return {
            'facility_type': facility_type.name,
            'units': available_units,
            'player_funds': player_funds
        }
import math
from typing import Tuple, Optional, List
from gameboard import GameBoard, GameTile
from unit import Army, UnitType, Unit, UnitClass
from dijkstra import dijkstra
from map_system import MapType, MOVEMENT_COST, INF, TERRAIN_DEFENSE
from config import Config
import configparser
from enhanced_movement_validation import EnhancedMovementValidator, MovementValidationResult
'''[This is a cleaned and optimized manager for the RPC game engine for Advance Wars]'''


config = configparser.ConfigParser()
config.read('config.ini')

REPAIR_CLASSES = {
    MapType.CITY: {UnitClass.BOOTS, UnitClass.TREADS, UnitClass.TYRES, UnitClass.FOOT},
    MapType.FACTORY: {UnitClass.BOOTS, UnitClass.TREADS, UnitClass.TYRES, UnitClass.FOOT},
    MapType.AIRPORT: {UnitClass.AIR},
    MapType.PORT: {UnitClass.SEA, UnitClass.LANDER},
    MapType.BASE_TOWER_1: {UnitClass.BOOTS, UnitClass.TREADS, UnitClass.TYRES, UnitClass.FOOT},
}

# Missile damage pattern: (dx, dy, damage)
MISSILE_DAMAGE_PATTERN = [
    (0, 0, 50),   # Center - direct hit
    (1, 0, 30), (2, 0, 30), (-1, 0, 30), (-2, 0, 30),  # Horizontal
    (0, 1, 30), (0, 2, 30), (0, -1, 30), (0, -2, 30),  # Vertical  
    (1, 1, 20), (1, -1, 20), (-1, 1, 20), (-1, -1, 20)  # Diagonal
]


class GameManager:
    """Manages game logic and state for Advance Wars RPC game."""
    
    def __init__(self, config: Config, board: GameBoard):
        self.config = config
        self.board = board

    def __repr__(self):
        return f"{self.__class__.__name__}"

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
            raise ValueError("Not this unit's turn")

    def _validate_unit_can_act(self, unit: Unit, action: str) -> None:
        """Validate unit can perform the specified action."""
        if action == 'move' and not unit.can_move:
            raise ValueError('Unit cannot move this turn')
        elif action == 'attack' and not unit.can_attack:
            raise ValueError('Unit cannot attack this turn')
        elif action == 'capture' and not unit.can_capture:
            raise ValueError('Unit cannot capture this turn')

    # =============================================================================
    # CORE UTILITY METHODS
    # =============================================================================
    
    def coord_valid(self, x: int, y: int) -> bool:
        """Returns true if the coordinate is within the board bounds."""
        return 0 <= x < self.board.width and 0 <= y < self.board.height

    def tile_at(self, x: int, y: int) -> GameTile:
        """Returns the game tile at the coordinates given."""
        index = x + y * self.board.width
        return self.board.grid[index]

    def tile_get(self, x: int, y: int) -> GameTile:
        """Return the tile at the given coordinates with validation."""
        self._validate_coordinates(x, y)
        return self.tile_at(x, y)

    def unit_at(self, x: int, y: int) -> Optional[Unit]:
        """Returns the unit at the given coordinates."""
        return self.tile_at(x, y).unit

    def check_turn(self) -> Army:
        """Returns the current army's turn."""
        return self.board.current_turn

    def tile_from_unit(self, unit: Unit) -> Optional[GameTile]:
        """Returns the tile the unit is on."""
        for tile in self.board.grid:
            if tile.unit and tile.unit.id == unit.id:
                return tile
        return None

    def unit_from_id(self, unit_id: str) -> Optional[Unit]:
        """Returns the unit from the ID given."""
        for tile in self.board.grid:
            if tile.unit and tile.unit.id == unit_id:
                return tile.unit
        return None

    def _calculate_manhattan_distance(self, x1: int, y1: int, x2: int, y2: int) -> int:
        """Calculate Manhattan distance between two points."""
        return abs(x1 - x2) + abs(y1 - y2)

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
                unit.can_capture = True

    def _apply_damage(self, unit: Unit, damage: int) -> None:
        """Apply damage to a unit, ensuring HP doesn't go below 1."""
        unit.status.hp = max(1, unit.status.hp - damage)

    def _consume_fuel(self, unit: Unit, distance: int) -> None:
        """Consume fuel for unit movement."""
        unit.status.fuel -= distance

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
    # PROPERTY AND ECONOMY MANAGEMENT  
    # =============================================================================
    
    def _update_property_ownership(self, tile: GameTile, new_army: Army) -> None:
        """Update property ownership and adjust army statistics."""
        old_army = tile.mapTile.army
        income = int(config['FUNDS']['income'])
        
        # Remove from old army
        if old_army == Army.RED:
            self.board.total_red_properties -= income
        elif old_army == Army.BLUE:
            self.board.total_blue_properties -= income
            
        # Add to new army
        tile.mapTile.army = new_army
        if new_army == Army.RED:
            self.board.total_red_properties += income
        elif new_army == Army.BLUE:
            self.board.total_blue_properties += income

    def _update_army_funds(self, army: Army, amount: int) -> None:
        """Update army funds."""
        if army == Army.RED:
            self.board.red_funds += amount
        elif army == Army.BLUE:
            self.board.blue_funds += amount

    def _get_army_funds(self, army: Army) -> int:
        """Get current army funds."""
        if army == Army.RED:
            return self.board.red_funds
        elif army == Army.BLUE:
            return self.board.blue_funds
        return 0

    def _update_army_statistics(self) -> None:
        """Update all army statistics in a single pass."""
        # Reset counters
        self.board.total_red_troops = 0
        self.board.total_blue_troops = 0
        self.board.total_red_properties = 0
        self.board.total_blue_properties = 0
        
        # Count in single pass
        income = int(config['FUNDS']['income'])
        for tile in self.board.grid:
            if tile.unit:
                if tile.unit.army == Army.RED:
                    self.board.total_red_troops += 1
                elif tile.unit.army == Army.BLUE:
                    self.board.total_blue_troops += 1
                    
            if tile.mapTile.army:
                if tile.mapTile.army == Army.RED:
                    self.board.total_red_properties += income
                elif tile.mapTile.army == Army.BLUE:
                    self.board.total_blue_properties += income

    # =============================================================================
    # COMBAT SYSTEM
    # =============================================================================
    
    def _apply_missile_damage_area(self, center_x: int, center_y: int) -> None:
        """Apply missile damage to all units in blast radius."""
        for dx, dy, damage in MISSILE_DAMAGE_PATTERN:
            target_x, target_y = center_x + dx, center_y + dy
            if self.coord_valid(target_x, target_y):
                target_tile = self.tile_at(target_x, target_y)
                if target_tile.unit:
                    self._apply_damage(target_tile.unit, damage)

    def _execute_combat(self, attacker: Unit, defender: Unit, attacker_tile: GameTile, defender_tile: GameTile) -> None:
        """Execute combat between two units."""
        # Attacker damages defender
        damage = attacker.attack_damage(defender, defender_tile)
        defender.status.hp -= damage
        attacker.status.ammo -= 1
        
        # Counter-attack if defender survives and can counter
        if defender.status.hp > 0 and defender.is_direct() and attacker.is_direct():
            counter_damage = defender.attack_damage(attacker, attacker_tile)
            attacker.status.hp -= counter_damage
            defender.status.ammo -= 1

    # =============================================================================
    # MOVEMENT AND VALIDATION
    # =============================================================================
    
    def unit_can_move_to(self, unit: Unit, x: int, y: int) -> bool:
        """Enhanced movement validation for UI indicators"""
        
        # Get unit's current position
        tile = self.tile_from_unit(unit)
        if not tile:
            return False
        
        # Use enhanced validator
        validator = EnhancedMovementValidator(self.board)
        result = validator.validate_movement(unit, tile.x, tile.y, x, y)
        
        return result.valid    
    
    def unit_can_attack(self, unit: Unit, x: int, y: int) -> bool:
        """Returns true if the unit can attack the target."""
        tile = self.tile_from_unit(unit)
        if not tile or (tile.x == x and tile.y == y):
            return False
            
        target = self.unit_at(x, y)
        if not target or target.army == unit.army:
            return False
            
        if not unit.is_attackable(target):
            return False
            
        distance = self._calculate_manhattan_distance(tile.x, tile.y, x, y)
        return unit.status.rangemin <= distance <= unit.status.rangemax

    # =============================================================================
    # UNIT MANAGEMENT
    # =============================================================================
    
    def unit_remove(self, x: int, y: int) -> Optional[Unit]:
        """Remove the unit at the given coordinates."""
        tile = self.tile_at(x, y)
        unit = tile.unit
        if unit:
            tile.unit = None
            tile.capture_hp = 20
        return unit

    def unit_place(self, unit: Unit, x: int, y: int) -> None:
        """Place the unit at the given coordinates."""
        self.tile_at(x, y).unit = unit

    def resupply_unit(self, unit: Unit) -> None:
        """Resupply unit with full fuel and ammo."""
        unit.status.fuel = int(config[unit.type.name]['fuel'])
        unit.status.ammo = int(config[unit.type.name]['ammo'])

    def unit_deselect(self) -> None:
        """Deselect current unit and clear movement/attack indicators."""
        self.board.selected = None
        for tile in self.board.grid:
            tile.can_be_moved_to = False
            tile.can_be_attacked = False

    # =============================================================================
    # PUBLIC GAME ACTIONS
    # =============================================================================
    
    def end_game(self) -> None:
        """End the game."""
        self.board.game_active = False

    def army_end_turn(self) -> None:
        """End current army's turn and advance to next army."""
        self._validate_game_active()
        self._end_current_army_turn()
        self._advance_to_next_army()
        self._start_next_army_turn()
        self._update_army_statistics()

    def _end_current_army_turn(self) -> None:
        """Process end-of-turn effects for current army."""
        self.unit_deselect()
        self._set_all_army_units_inactive(self.board.current_turn)

    def _advance_to_next_army(self) -> None:
        """Advance to the next army in turn order."""
        current_idx = self.board.turn_order.index(self.board.current_turn)
        next_idx = (current_idx + 1) % len(self.board.turn_order)
        self.board.current_turn = self.board.turn_order[next_idx]
        
        # Increment day counter when returning to first army
        if next_idx == 0:
            self.board.days += 1

    def _start_next_army_turn(self) -> None:
        """Process start-of-turn effects for new army."""
        current_army = self.board.current_turn
        income = int(config['FUNDS']['income'])
        
        # Add income from properties
        for tile in self.board.grid:
            if tile.mapTile.army == current_army:
                self._update_army_funds(current_army, income)
        
        # Activate units and process turn effects
        for tile in self.board.grid:
            if tile.unit and tile.unit.army == current_army:
                unit = tile.unit
                self._process_unit_turn_start(unit, tile)
            elif not tile.unit and tile.mapTile.is_capturable():
                tile.capture_hp = 20

    def _process_unit_turn_start(self, unit: Unit, tile: GameTile) -> None:
        """Process start-of-turn effects for a unit."""
        # Activate unit
        unit.can_move = True
        unit.can_attack = True
        unit.can_capture = True
        
        # Consume daily fuel
        unit.status.fuel -= unit.fuel_use()
        
        # Remove unit if out of fuel
        if unit.fuel_daily_use() and unit.status.fuel <= 0:
            self.unit_remove(tile.x, tile.y)
            return
            
        # Repair if on friendly repair facility
        if (unit.army == tile.mapTile.army and 
            tile.mapTile.type in REPAIR_CLASSES and
            unit.status.cls in REPAIR_CLASSES[tile.mapTile.type]):
            unit.status.hp = min(100, unit.status.hp + 20)
            self.resupply_unit(unit)
        
        # APC resupply adjacent units
        if unit.type == UnitType.APC:
            self._apc_resupply_adjacent(tile)

    def _apc_resupply_adjacent(self, apc_tile: GameTile) -> None:
        """Resupply all adjacent friendly units from APC."""
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for dx, dy in directions:
            adj_x, adj_y = apc_tile.x + dx, apc_tile.y + dy
            if self.coord_valid(adj_x, adj_y):
                adj_tile = self.tile_at(adj_x, adj_y)
                if (adj_tile.unit and 
                    adj_tile.unit.army == apc_tile.unit.army):
                    self.resupply_unit(adj_tile.unit)

    def unit_select(self, x: int, y: int) -> Unit:
        """Select unit and show valid moves/attacks."""
        self._validate_coordinates(x, y)
        tile = self.tile_at(x, y)
        unit = self._validate_unit_exists(x, y)
        
        if self.board.selected and tile.unit == self.board.selected.unit:
            self.unit_deselect()
        else:
            self._validate_unit_turn(unit)
            self.board.selected = tile
            self._update_move_attack_indicators(unit)
        
        return unit

    def _update_move_attack_indicators(self, unit: Unit) -> None:
        """Update visual indicators for valid moves and attacks."""
        for tile in self.board.grid:
            if unit.can_move:
                tile.can_be_moved_to = self.unit_can_move_to(unit, tile.x, tile.y)
            else:
                tile.can_be_moved_to = False
                
            if unit.can_attack:
                tile.can_be_attacked = self.unit_can_attack(unit, tile.x, tile.y)
            else:
                tile.can_be_attacked = False

    def unit_move(self, x: int, y: int, x2: int, y2: int) -> Unit:
        """Enhanced unit movement with comprehensive validation"""
        
        # Basic validations
        self._validate_coordinates(x, y, x2, y2)
        unit = self._validate_unit_exists(x, y)
        self._validate_unit_turn(unit)
        self._validate_game_active()
        
        # Enhanced movement validation
        validator = EnhancedMovementValidator(self.board)
        result = validator.validate_movement(unit, x, y, x2, y2)
        
        if not result.valid:
            raise ValueError(f"Invalid movement: {result.reason}")
        
        # Execute the movement
        unit = self.unit_remove(x, y)
        self.unit_place(unit, x2, y2)
        
        # Consume fuel based on actual pathfinding cost
        fuel_cost = min(result.MOVEMENT_COST, result.fuel_required)
        self._consume_fuel(unit, fuel_cost)
        
        # Update unit state
        unit.can_move = False
        if unit.is_indirect():
            unit.can_attack = False
        
        # Update selection
        self.unit_deselect()
        self.unit_select(x2, y2)
        
        return unit

    def unit_create(self, army: str, unit_type: str, x: int, y: int) -> Unit:
        """Create a unit at the given coordinates."""
        army_enum = Army[army.upper()]
        unit_type_enum = UnitType[unit_type.upper()]
        
        self._validate_coordinates(x, y)
        if self.unit_at(x, y):
            raise ValueError('Tile already occupied')
        
        # Check funds
        cost = int(config[unit_type_enum.name]['cost'])
        current_funds = self._get_army_funds(army_enum)
        if cost > current_funds:
            raise ValueError('Insufficient funds')
        
        # Create and place unit
        unit = Unit.create(army_enum, unit_type_enum, self.config.units[unit_type])
        self.unit_place(unit, x, y)
        
        # Deduct funds and update statistics
        self._update_army_funds(army_enum, -cost)
        if army_enum == Army.RED:
            self.board.total_red_troops += 1
        elif army_enum == Army.BLUE:
            self.board.total_blue_troops += 1
        
        return unit

    def unit_attack(self, x: int, y: int, x2: int, y2: int) -> Optional[Unit]:
        """Execute attack from (x,y) to (x2,y2)."""
        self._validate_coordinates(x, y, x2, y2)
        attacker = self._validate_unit_exists(x, y)
        defender = self._validate_unit_exists(x2, y2)
        self._validate_unit_turn(attacker)
        self._validate_unit_can_act(attacker, 'attack')
        
        if not self.unit_can_attack(attacker, x2, y2):
            raise ValueError('Cannot attack target')
        
        # Execute combat
        attacker_tile = self.tile_at(x, y)
        defender_tile = self.tile_at(x2, y2)
        self._execute_combat(attacker, defender, attacker_tile, defender_tile)
        
        # Remove destroyed units
        destroyed_tiles = self._remove_destroyed_units()
        
        # Update attacker state
        self._set_unit_inactive(attacker)
        self.unit_deselect()
        
        return self.unit_at(x, y)  # Return attacker if still alive

    def damage_estimate(self, x: int, y: int, x2: int, y2: int) -> Tuple[int, int]:
        """Estimate damage for combat between units."""
        self._validate_coordinates(x, y, x2, y2)
        attacker = self._validate_unit_exists(x, y)
        defender = self._validate_unit_exists(x2, y2)
        
        attacker_tile = self.tile_at(x, y)
        defender_tile = self.tile_at(x2, y2)
        
        # Calculate damage
        attacker_hp = attacker.status.hp
        defender_hp = defender.status.hp
        
        # Attacker damages defender
        damage_to_defender = attacker.attack_damage(defender, defender_tile)
        defender_hp_after = max(0, defender_hp - damage_to_defender)
        
        # Counter-attack if applicable
        attacker_hp_after = attacker_hp
        if (defender_hp_after > 0 and defender.is_direct() and attacker.is_direct()):
            damage_to_attacker = defender.attack_damage(attacker, attacker_tile)
            attacker_hp_after = max(0, attacker_hp - damage_to_attacker)
        
        return attacker_hp_after, defender_hp_after

    def capture_tile(self, x: int, y: int) -> GameTile:
        """Capture property at coordinates."""
        self._validate_coordinates(x, y)
        tile = self.tile_get(x, y)
        unit = self._validate_unit_exists(x, y)
        self._validate_unit_turn(unit)
        self._validate_unit_can_act(unit, 'capture')
        
        if not tile.mapTile.is_capturable():
            raise ValueError('Tile not capturable')
        
        if not unit.type_can_capture():
            raise ValueError('Unit cannot capture')
        
        if tile.mapTile.army == unit.army:
            raise ValueError('Cannot capture own property')
        
        # Apply capture damage
        capture_power = math.ceil(unit.status.hp / 10)
        tile.capture_hp -= capture_power
        
        # Complete capture if HP depleted
        if tile.capture_hp <= 0:
            self._update_property_ownership(tile, unit.army)
            tile.capture_hp = 20
            
            # Check for HQ capture (game end)
            if tile.mapTile.type == MapType.BASE_TOWER_1:
                self.board.game_active = False
        
        self._set_unit_inactive(unit)
        self.unit_deselect()
        return tile

    def unit_wait(self, x: int, y: int) -> Unit:
        """Set unit to wait (end turn for unit)."""
        self._validate_coordinates(x, y)
        unit = self._validate_unit_exists(x, y)
        self._validate_unit_turn(unit)
        
        self._set_unit_inactive(unit)
        self.unit_deselect()
        return unit

    def unit_delete(self, x: int, y: int) -> Optional[Unit]:
        """Delete unit at coordinates."""
        self._validate_coordinates(x, y)
        return self.unit_remove(x, y)

    def unit_join(self, x: int, y: int, x2: int, y2: int) -> Unit:
        """Join unit from (x,y) with unit at (x2,y2)."""
        self._validate_coordinates(x, y, x2, y2)
        unit1 = self._validate_unit_exists(x, y)
        unit2 = self._validate_unit_exists(x2, y2)
        self._validate_unit_turn(unit1)
        
        if unit1.type != unit2.type:
            raise ValueError('Cannot join different unit types')
        
        if unit2.status.hp >= 100:
            raise ValueError('Target unit already at full health')
        
        # Calculate movement to target
        if not self.unit_can_move_to(unit1, x2, y2):
            raise ValueError('Cannot reach target unit')
        
        # Join units
        combined_hp = min(100, unit1.status.hp + unit2.status.hp)
        unit2.status.hp = combined_hp
        
        self._set_unit_inactive(unit2)
        self.unit_remove(x, y)
        
        return unit2

    def unit_load(self, x: int, y: int, x2: int, y2: int) -> Unit:
        """Load unit from (x,y) into transport at (x2,y2)."""
        self._validate_coordinates(x, y, x2, y2)
        unit = self._validate_unit_exists(x, y)
        transport = self._validate_unit_exists(x2, y2)
        self._validate_unit_turn(unit)
        self._validate_unit_can_act(unit, 'move')
        
        if transport.army != unit.army:
            raise ValueError('Cannot load into enemy transport')
        
        if not transport.can_carry(unit):
            raise ValueError('Transport cannot carry this unit type')
        
        if len(transport.status.cargo) >= transport.capacity():
            raise ValueError('Transport is full')
        
        if not self.unit_can_move_to(unit, x2, y2):
            raise ValueError('Cannot reach transport')
        
        # Execute loading
        distance = self._calculate_manhattan_distance(x, y, x2, y2)
        self._consume_fuel(unit, distance)
        
        # Resupply if air/sea transport
        if transport.type in {UnitType.CARRIER, UnitType.CRUISER}:
            self.resupply_unit(unit)
        
        unit = self.unit_remove(x, y)
        transport.status.cargo.append(unit)
        self._set_unit_inactive(unit)
        
        return transport

    def unit_unload(self, x: int, y: int, x2: int, y2: int, index: int) -> Unit:
        """Unload unit from transport at (x,y) to (x2,y2)."""
        self._validate_coordinates(x, y, x2, y2)
        transport = self._validate_unit_exists(x, y)
        self._validate_unit_turn(transport)
        
        if self.unit_at(x2, y2):
            raise ValueError('Target tile occupied')
        
        distance = self._calculate_manhattan_distance(x, y, x2, y2)
        if distance > 1:
            raise ValueError('Can only unload to adjacent tile')
        
        if not transport.status.cargo or index >= len(transport.status.cargo):
            raise ValueError('No unit at cargo index')
        
        # Check if unit can be placed on target terrain
        unit = transport.status.cargo[index]
        target_tile = self.tile_get(x2, y2)
        if MOVEMENT_COST[target_tile.mapTile.type][unit.status.cls.value] == INF:
            raise ValueError('Unit cannot be placed on this terrain')
        
        # Execute unloading
        unit = transport.status.cargo.pop(index)
        self.unit_place(unit, x2, y2)
        
        # Both units become inactive
        self._set_unit_inactive(unit)
        self._set_unit_inactive(transport)
        
        return unit

    def launch_missile(self, x: int, y: int, x2: int, y2: int) -> GameTile:
        """Launch missile from silo at (x,y) targeting (x2,y2)."""
        self._validate_coordinates(x, y, x2, y2)
        tile = self.tile_get(x, y)
        
        if tile.mapTile.type != MapType.MISSILE_SILO:
            raise ValueError('Not a missile silo')
        
        unit = self._validate_unit_exists(x, y)
        self._validate_unit_turn(unit)
        
        # Convert silo and apply damage
        tile.mapTile.type = MapType.EMPTY_SILO
        self._apply_missile_damage_area(x2, y2)
        self._remove_destroyed_units()
        
        self._set_unit_inactive(unit)
        return tile

    def unit_resupply(self, x: int, y: int, x2: int, y2: int) -> Unit:
        """Resupply unit at (x2,y2) from unit at (x,y)."""
        self._validate_coordinates(x, y, x2, y2)
        supplier = self._validate_unit_exists(x, y)
        target = self._validate_unit_exists(x2, y2)
        self._validate_unit_turn(supplier)
        
        if not supplier.can_resupply():
            raise ValueError('Unit cannot resupply others')
        
        if supplier.army != target.army:
            raise ValueError('Cannot resupply enemy units')
        
        self.resupply_unit(target)
        return target

    # =============================================================================
    # ENHANCED MOVEMENT METHODS
    # =============================================================================
    
    def get_unit_valid_moves(self, unit: Unit) -> List[Tuple[int, int]]:
        """Get all valid moves for a unit"""
        
        tile = self.tile_from_unit(unit)
        if not tile:
            return []
        
        validator = EnhancedMovementValidator(self.board)
        return validator.get_valid_moves(unit, tile.x, tile.y)
    
    def get_movement_preview(self, x: int, y: int, x2: int, y2: int) -> dict:
        """Get movement preview for UI"""
        
        self._validate_coordinates(x, y, x2, y2)
        unit = self._validate_unit_exists(x, y)
        validator = EnhancedMovementValidator(self.board)
        
        return validator.get_movement_preview(unit, x, y, x2, y2)
    
    def validate_movement_detailed(self, x: int, y: int, x2: int, y2: int):
        """Get detailed movement validation result with safe error handling"""
        from enhanced_movement_validation import MovementValidationResult
        
        # Safe coordinate checking without exceptions
        if not (0 <= x < self.board.width and 0 <= y < self.board.height):
            return MovementValidationResult(
                False, 
                f"Source coordinates ({x}, {y}) are out of bounds. Board size: {self.board.width}x{self.board.height}"
            )
        
        if not (0 <= x2 < self.board.width and 0 <= y2 < self.board.height):
            return MovementValidationResult(
                False, 
                f"Destination coordinates ({x2}, {y2}) are out of bounds. Board size: {self.board.width}x{self.board.height}"
            )
        
        # Check if unit exists
        unit = self.unit_at(x, y)
        if not unit:
            return MovementValidationResult(False, f"No unit found at coordinates ({x}, {y})")
        
        # Use the enhanced validator
        try:
            from enhanced_movement_validation import EnhancedMovementValidator
            validator = EnhancedMovementValidator(self.board)
            return validator.validate_movement(unit, x, y, x2, y2)
        except Exception as e:
            return MovementValidationResult(False, f"Validation error: {str(e)}")
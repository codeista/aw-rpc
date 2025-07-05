import math
from typing import Dict, List, Optional, Tuple, Any
from gameboard import GameBoard, GameTile
from unit import Army, UnitType, Unit, UnitClass
from dijkstra import dijkstra
from map_system import MapType, MOVEMENT_COST, INF, TERRAIN_DEFENSE
from config import Config
import configparser
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from combat_system import CombatResult, CombatSystem
from enhanced_movement_validation import EnhancedMovementValidator, MovementValidationResult
import random
from dataclasses import dataclass
from enum import Enum

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

    def check_win_condition(self) -> Optional[Army]:
        """Check if any army has won the game"""
        
        # Count units for each army
        army_unit_counts = {}
        for army in self.board.turn_order:
            army_unit_counts[army] = 0
        
        # Count all units on the board
        for tile in self.board.grid:
            if tile.unit:
                army_unit_counts[tile.unit.army] += 1
        
        # Check for armies with units
        armies_with_units = []
        total_units = 0
        for army, count in army_unit_counts.items():
            total_units += count
            if count > 0:
                armies_with_units.append(army)
        
        # Only declare winner if:
        # 1. Game has been going for a while (multiple units created)
        # 2. Only one army has units remaining
        # 3. At least some combat has occurred
        if len(armies_with_units) == 1 and total_units > 0 and self.board.days > 0:
            return armies_with_units[0]
        
        return None

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
                    
    def produce_unit_at_facility(self, facility_x: int, facility_y: int, 
                           unit_type_str: str, army: Army):
        """Produce a unit at a facility with cost management"""
        
        # Import here to avoid circular imports
        from production_system import ProductionSystem
        from unit import UnitType
        
        # Convert string to UnitType enum
        try:
            unit_type = UnitType[unit_type_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid unit type: {unit_type_str}")
        
        # Use production system
        production_system = ProductionSystem(self)
        result = production_system.produce_unit(facility_x, facility_y, unit_type, army)
        
        return result

    def get_production_options(self, facility_x: int, facility_y: int, army: Army) -> Dict:
        """Get available production options for a facility"""
        
        from production_system import ProductionSystem
        
        production_system = ProductionSystem(self)
        return production_system.get_producible_units(facility_x, facility_y, army)

    def get_army_economy(self, army: Army) -> Dict:
        """Get complete economic information for an army"""
        
        from production_system import ProductionSystem
        
        production_system = ProductionSystem(self)
        return production_system.get_economic_summary(army)

    def get_army_facilities(self, army: Army) -> List[Dict]:
        """Get all production facilities owned by an army"""
        
        from production_system import ProductionSystem
        
        production_system = ProductionSystem(self)
        return production_system.get_all_production_facilities(army)

    def can_afford_unit(self, unit_type_str: str, army: Army) -> bool:
        """Check if army can afford a specific unit type"""
        
        from production_system import ProductionSystem
        from unit import UnitType
        
        try:
            unit_type = UnitType[unit_type_str.upper()]
            production_system = ProductionSystem(self)
            current_funds = self._get_army_funds(army)
            unit_cost = production_system.UNIT_COSTS.get(unit_type, 1000)
            return current_funds >= unit_cost
        except KeyError:
            return False

    def process_daily_income(self, army: Army) -> int:
        """Process daily income for an army (called during turn start)"""
        
        from production_system import ProductionSystem
        
        production_system = ProductionSystem(self)
        daily_income = production_system.calculate_daily_income(army)
        
        # Add income to army funds
        self._update_army_funds(army, daily_income)
        
        return daily_income

    # Enhanced turn start method with income processing
    def _start_next_army_turn(self) -> None:
        """Process start-of-turn effects for new army with enhanced income"""
        current_army = self.board.current_turn
        
        # Process daily income using production system
        daily_income = self.process_daily_income(current_army)
        
        # Activate units and process turn effects
        for tile in self.board.grid:
            if tile.unit and tile.unit.army == current_army:
                unit = tile.unit
                self._process_unit_turn_start(unit, tile)
            elif not tile.unit and tile.mapTile.is_capturable():
                tile.capture_hp = 20
        
        # Log income processing
        if hasattr(self, 'app_logger'):
            self.app_logger.info(f"{current_army.name} received {daily_income} income")

    # Enhanced unit creation with initial funds setup
    def setup_initial_economy(self) -> None:
        """Setup initial funds for all armies based on starting properties"""
        
        from production_system import ProductionSystem
        
        production_system = ProductionSystem(self)
        
        # Calculate initial funds for each army
        for army in self.board.turn_order:
            initial_income = production_system.calculate_daily_income(army)
            # Give armies starting funds (could be 10x daily income or a fixed amount)
            starting_funds = max(10000, initial_income * 3)  # At least 10k or 3 days income
            
            # Set initial funds
            if army == Army.RED:
                self.board.red_funds = starting_funds
            elif army == Army.BLUE:
                self.board.blue_funds = starting_funds

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

    def unit_attack_enhanced(self, attacker_x: int, attacker_y: int, 
                        defender_x: int, defender_y: int):
        """Enhanced unit attack with full combat system"""
        from combat_system import CombatSystem
        
        # Validation
        self._validate_coordinates(attacker_x, attacker_y, defender_x, defender_y)
        attacker = self._validate_unit_exists(attacker_x, attacker_y)
        defender = self._validate_unit_exists(defender_x, defender_y)
        
        self._validate_unit_turn(attacker)
        self._validate_unit_can_act(attacker, 'attack')
        
        # Check if attack is valid
        if not attacker.is_attackable(defender):
            raise ValueError(f"{attacker.type.name} cannot attack {defender.type.name}")
        
        if attacker.army == defender.army:
            raise ValueError("Cannot attack friendly units")
        
        # Check range
        distance = abs(attacker_x - defender_x) + abs(attacker_y - defender_y)
        if not (attacker.status.rangemin <= distance <= attacker.status.rangemax):
            raise ValueError(f"Target out of range ({distance}). Range: {attacker.status.rangemin}-{attacker.status.rangemax}")
        
        # Execute combat
        combat_system = CombatSystem(self)
        result = combat_system.execute_combat((attacker_x, attacker_y), (defender_x, defender_y))
        
        # Set attacker as inactive
        if not result.attacker_destroyed:
            self._set_unit_inactive(attacker)
        
        # Deselect units
        self.unit_deselect()
        
        return result

    def get_damage_preview(self, attacker_x: int, attacker_y: int, 
                        defender_x: int, defender_y: int) -> Dict:
        """Get damage preview without executing combat"""
        from combat_system import CombatSystem
        
        attacker = self.unit_at(attacker_x, attacker_y)
        defender = self.unit_at(defender_x, defender_y)
        
        if not attacker or not defender:
            return {"error": "Missing units"}
        
        attacker_tile = self.tile_at(attacker_x, attacker_y)
        defender_tile = self.tile_at(defender_x, defender_y)
        
        combat_system = CombatSystem(self)
        
        # Calculate potential damage
        attacker_damage = combat_system.calculate_damage(attacker, defender, defender_tile)
        
        # Check for potential counter
        counter_damage = 0
        can_counter = combat_system.can_counter_attack(
            attacker, defender, (attacker_x, attacker_y), (defender_x, defender_y)
        )
        
        if can_counter:
            counter_damage = combat_system.calculate_damage(defender, attacker, attacker_tile)
        
        return {
            "attacker_damage": attacker_damage,
            "counter_damage": counter_damage,
            "can_counter": can_counter,
            "defender_hp_after": max(0, defender.status.hp - attacker_damage),
            "attacker_hp_after": max(0, attacker.status.hp - counter_damage) if can_counter else attacker.status.hp,
            "defender_destroyed": (defender.status.hp - attacker_damage) <= 0,
            "attacker_destroyed": can_counter and (attacker.status.hp - counter_damage) <= 0
        }
 
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
        """Enhanced turn ending with daily fuel consumption"""
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

    def _advance_to_next_army(self):
        """Advance to next army and handle day increment with fuel consumption"""
        
        # Get current turn info
        current_army = self.board.current_turn
        current_turn_index = self.board.turn_order.index(current_army)
        next_turn_index = (current_turn_index + 1) % len(self.board.turn_order)
        
        # Advance to next army
        self.board.current_turn = self.board.turn_order[next_turn_index]
        
        # If we've cycled back to first player, increment day and consume fuel
        if next_turn_index == 0:
            self.board.days += 1
            
            # Consume daily fuel for all units
            fuel_results = self.consume_daily_fuel()
            
            # Log fuel consumption results
            if fuel_results["units_destroyed"] > 0:
                print(f"Day {self.board.days}: {fuel_results['units_destroyed']} units destroyed due to fuel depletion")
            
            if fuel_results["units_immobilized"] > 0:
                print(f"Day {self.board.days}: {fuel_results['units_immobilized']} land units immobilized due to fuel depletion")

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
        
        # # Consume daily fuel
        # unit.status.fuel -= unit.fuel_use()
        
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
        """Enhanced unit movement with proper validation and fuel consumption"""
        
        # Basic validation
        self._validate_coordinates(x, y)
        self._validate_coordinates(x2, y2)
        
        # Get and validate unit
        unit = self.unit_at(x, y)
        if not unit:
            from error_handling import MovementError
            raise MovementError(
                f"No unit at position ({x}, {y})",
                from_pos=(x, y)
            )
        
        # Validate unit ownership and turn
        if unit.army != self.board.current_turn:
            from error_handling import MovementError
            raise MovementError(
                f"Cannot move {unit.army.name} unit during {self.board.current_turn.name}'s turn",
                from_pos=(x, y)
            )
        
        # Check if unit can move (including fuel restrictions)
        if not unit.can_move or unit.status.fuel <= 0:
            from error_handling import UnitError
            if unit.status.fuel <= 0:
                raise UnitError(
                    "Unit is immobilized due to lack of fuel",
                    unit_id=str(unit.id)
                )
            else:
                raise UnitError(
                    "Unit has already moved this turn",
                    unit_id=str(unit.id)
                )
        
        # Check if trying to move to same position
        if x == x2 and y == y2:
            from error_handling import MovementError
            raise MovementError(
                "Cannot move to the same position",
                from_pos=(x, y),
                to_pos=(x2, y2)
            )
        
        # Validate destination and calculate costs
        self._validate_move_destination(x2, y2, unit)
        move_cost = self._calculate_movement_cost(unit, x, y, x2, y2)
        fuel_cost = self._calculate_fuel_cost(unit, x, y, x2, y2)
        
        # Validate movement and fuel
        if move_cost > unit.status.move:
            from error_handling import MovementError
            raise MovementError(
                f"Distance {move_cost} exceeds movement range {unit.status.move}",
                from_pos=(x, y),
                to_pos=(x2, y2)
            )
        
        if fuel_cost > unit.status.fuel:
            from error_handling import UnitError
            raise UnitError(
                f"Insufficient fuel. Need {fuel_cost}, have {unit.status.fuel}",
                unit_id=str(unit.id)
            )
        
        # Check for unit joining
        target_unit = self.unit_at(x2, y2)
        if target_unit and target_unit.army == unit.army and target_unit.type == unit.type:
            return self._handle_unit_join_fixed(x, y, x2, y2)
        
        # Execute the movement
        self.unit_remove(x, y)
        self.unit_place(unit, x2, y2)
        
        # Update unit state
        unit.status.fuel -= fuel_cost
        unit.can_move = False
        
        # Indirect units can't attack after moving
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

    def capture_tile(self, x: int, y: int) -> Dict:
        """Enhanced property capture with comprehensive validation"""
        return self.capture_tile_enhanced(x, y)

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
    # ENHANCED CAPTURE MECHANICS
    # =============================================================================
    
    def capture_tile_enhanced(self, x: int, y: int) -> Dict:
        """Enhanced property capture with comprehensive validation and features"""
        
        # Basic validation
        self._validate_coordinates(x, y)
        tile = self.tile_get(x, y)
        
        # Validate unit exists and can capture
        unit = self._validate_capture_unit(x, y)
        
        # Validate property can be captured
        self._validate_capturable_property(tile, unit)
        
        # Get capture context for logging
        capture_context = self._get_capture_context(tile, unit)
        
        # Calculate capture damage
        capture_damage = self._calculate_capture_damage(unit)
        original_hp = tile.capture_hp
        
        # Apply capture damage
        tile.capture_hp = max(0, tile.capture_hp - capture_damage)
        
        # Check if capture is complete
        capture_complete = tile.capture_hp <= 0
        
        if capture_complete:
            # Complete the capture
            capture_result = self._complete_property_capture(tile, unit)
        else:
            # Partial capture
            capture_result = {
                "captured": False,
                "progress": True,
                "hp_remaining": tile.capture_hp,
                "hp_reduced": capture_damage
            }
        
        # Set unit inactive
        self._set_unit_inactive(unit)
        self.unit_deselect()
        
        # Enhanced capture result
        result = {
            **capture_context,
            **capture_result,
            "original_hp": original_hp,
            "capture_damage": capture_damage,
            "unit_hp": math.ceil(unit.status.hp / 10),  # Display HP for capture
            "position": {"x": x, "y": y}
        }
        
        # Log capture event
        self._log_capture_event(result)
        
        return result
    
    def _validate_capture_unit(self, x: int, y: int) -> Unit:
        """Validate unit exists and can perform capture"""
        
        unit = self.unit_at(x, y)
        if not unit:
            from error_handling import NotFoundError
            raise NotFoundError(
                f"No unit at position ({x}, {y}) to capture with",
                resource_type="unit",
                details={"position": {"x": x, "y": y}}
            )
        
        # Validate it's the unit's turn
        if unit.army != self.board.current_turn:
            from error_handling import GameStateError
            raise GameStateError(
                f"It's {self.board.current_turn.name}'s turn, not {unit.army.name}'s",
                details={"current_turn": self.board.current_turn.name, "unit_army": unit.army.name}
            )
        
        # Validate unit can act
        if not unit.can_capture:
            from error_handling import UnitError
            raise UnitError(
                "Unit has already performed an action this turn",
                unit_id=str(unit.id)
            )
        
        # Validate unit type can capture
        if not unit.type_can_capture():
            from error_handling import UnitError
            raise UnitError(
                f"{unit.type.name} units cannot capture properties",
                unit_id=str(unit.id),
                details={"unit_type": unit.type.name}
            )
        
        return unit

    def _validate_capturable_property(self, tile, unit: Unit):
        """Validate the property can be captured"""
        
        # Check if tile has a capturable property
        capturable_properties = {
            MapType.CITY, MapType.FACTORY, MapType.AIRPORT, MapType.PORT,
            MapType.BASE_TOWER_1, MapType.BASE_TOWER_2, MapType.BASE_TOWER_3, MapType.BASE_TOWER_4,
            MapType.COM_TOWER, MapType.LAB, MapType.MISSILE_SILO
        }
        
        if tile.mapTile.type not in capturable_properties:
            from error_handling import GameStateError
            raise GameStateError(
                f"Cannot capture {tile.mapTile.type.name} - not a capturable property",
                details={"terrain_type": tile.mapTile.type.name}
            )
        
        # Can't capture own properties
        if tile.mapTile.army == unit.army:
            from error_handling import GameStateError
            raise GameStateError(
                f"Property already belongs to {unit.army.name}",
                details={"property_owner": unit.army.name, "unit_army": unit.army.name}
            )
        
        # Can't capture if property has defending unit
        if tile.unit and tile.unit != unit:
            from error_handling import GameStateError
            raise GameStateError(
                f"Property is defended by {tile.unit.army.name} {tile.unit.type.name}",
                details={"defender": f"{tile.unit.army.name}_{tile.unit.type.name}"}
            )

    def _get_capture_context(self, tile, unit: Unit) -> Dict:
        """Get context information about the capture attempt"""
        
        property_name = tile.mapTile.type.name
        current_owner = tile.mapTile.army.name if tile.mapTile.army else "Neutral"
        
        return {
            "property_type": property_name,
            "current_owner": current_owner,
            "capturing_army": unit.army.name,
            "capturing_unit": unit.type.name,
            "is_hq": tile.mapTile.type in {MapType.BASE_TOWER_1, MapType.BASE_TOWER_2, 
                                        MapType.BASE_TOWER_3, MapType.BASE_TOWER_4}
        }

    def _calculate_capture_damage(self, unit: Unit) -> int:
        """Calculate capture damage based on unit HP"""
        
        # Capture damage = unit's displayed HP (1-10)
        # This matches authentic Advance Wars mechanics
        capture_power = math.ceil(unit.status.hp / 10)
        
        return capture_power

    def _complete_property_capture(self, tile, unit: Unit) -> Dict:
        """Complete property capture and handle consequences"""
        
        old_owner = tile.mapTile.army
        property_type = tile.mapTile.type
        
        # Update ownership
        self._update_property_ownership(tile, unit.army)
        tile.capture_hp = 20  # Reset to full
        
        # Check for victory conditions
        victory_result = self._check_capture_victory_conditions(property_type, unit.army, old_owner)
        
        # Generate capture income bonus (immediate reward)
        capture_bonus = self._calculate_capture_bonus(property_type)
        if capture_bonus > 0:
            self._update_army_funds(unit.army, capture_bonus)
        
        return {
            "captured": True,
            "progress": False,
            "hp_remaining": 20,
            "new_owner": unit.army.name,
            "old_owner": old_owner.name if old_owner else "Neutral",
            "capture_bonus": capture_bonus,
            "victory_achieved": victory_result["victory"],
            "victory_type": victory_result["type"],
            "game_ended": victory_result["game_ended"]
        }

    def _calculate_capture_bonus(self, property_type: MapType) -> int:
        """Calculate immediate bonus for capturing specific properties"""
        
        # Different properties give different immediate bonuses
        capture_bonuses = {
            MapType.CITY: 1000,           # Standard city bonus
            MapType.FACTORY: 1500,        # Industrial bonus
            MapType.AIRPORT: 2000,        # Strategic air bonus
            MapType.PORT: 2000,           # Strategic sea bonus
            MapType.COM_TOWER: 3000,      # Major strategic bonus
            MapType.LAB: 2500,            # Research bonus
            MapType.MISSILE_SILO: 2000,   # Weapons bonus
            MapType.BASE_TOWER_1: 5000,   # HQ capture bonus
            MapType.BASE_TOWER_2: 5000,
            MapType.BASE_TOWER_3: 5000,
            MapType.BASE_TOWER_4: 5000,
        }
        
        return capture_bonuses.get(property_type, 0)

    def _check_capture_victory_conditions(self, property_type: MapType, capturing_army: Army, old_owner: Army) -> Dict:
        """Check if capture results in victory"""
        
        victory_result = {
            "victory": False,
            "type": None,
            "game_ended": False
        }
        
        # HQ Capture Victory
        if property_type in {MapType.BASE_TOWER_1, MapType.BASE_TOWER_2, 
                        MapType.BASE_TOWER_3, MapType.BASE_TOWER_4}:
            
            # Check if the captured HQ belonged to an enemy
            if old_owner and old_owner != capturing_army:
                
                # Check if this army has lost all HQs
                remaining_hqs = self._count_army_hqs(old_owner)
                
                if remaining_hqs == 0:
                    # Enemy has lost all HQs - victory!
                    self.board.game_active = False
                    self.board.winner = capturing_army
                    
                    victory_result = {
                        "victory": True,
                        "type": "HQ_CAPTURE",
                        "game_ended": True,
                        "defeated_army": old_owner.name
                    }
        
        return victory_result

    def _count_army_hqs(self, army: Army) -> int:
        """Count how many HQs an army still controls"""
        
        hq_types = {MapType.BASE_TOWER_1, MapType.BASE_TOWER_2, 
                MapType.BASE_TOWER_3, MapType.BASE_TOWER_4}
        
        hq_count = 0
        for tile in self.board.grid:
            if (tile.mapTile.type in hq_types and 
                tile.mapTile.army == army):
                hq_count += 1
        
        return hq_count
    
    def _log_capture_event(self, result: Dict):
        """Log capture event with detailed information"""
        
        if result["captured"]:
            print(f"🏴 PROPERTY CAPTURED: {result['capturing_army']} {result['capturing_unit']} "
                f"captured {result['property_type']} at ({result['position']['x']}, {result['position']['y']}) "
                f"from {result['old_owner']}")
            
            if result["victory_achieved"]:
                print(f"🎉 VICTORY: {result['capturing_army']} wins by {result['victory_type']}!")
        else:
            print(f"📈 CAPTURE PROGRESS: {result['capturing_army']} {result['capturing_unit']} "
                f"reduced {result['property_type']} HP to {result['hp_remaining']}/20 "
                f"(-{result['capture_damage']} damage)")

    def get_capture_preview(self, x: int, y: int) -> Dict:
        """Get capture preview information for UI"""
        
        try:
            tile = self.tile_get(x, y)
            unit = self.unit_at(x, y)
            
            if not unit:
                return {"can_capture": False, "reason": "No unit present"}
            
            if not unit.type_can_capture():
                return {"can_capture": False, "reason": f"{unit.type.name} cannot capture"}
            
            if not unit.can_capture:
                return {"can_capture": False, "reason": "Unit has already acted"}
            
            if unit.army != self.board.current_turn:
                return {"can_capture": False, "reason": "Not unit's turn"}
            
            # Calculate capture preview
            capture_damage = self._calculate_capture_damage(unit)
            new_hp = max(0, tile.capture_hp - capture_damage)
            will_complete = new_hp <= 0
            
            return {
                "can_capture": True,
                "current_hp": tile.capture_hp,
                "damage": capture_damage,
                "new_hp": new_hp,
                "will_complete": will_complete,
                "property_type": tile.mapTile.type.name,
                "current_owner": tile.mapTile.army.name if tile.mapTile.army else "Neutral",
                "turns_to_complete": math.ceil(new_hp / capture_damage) if not will_complete else 0
            }
            
        except Exception as e:
            return {"can_capture": False, "reason": str(e)}
        
    # =============================================================================
    # ENHANCED MOVEMENT METHODS
    # =============================================================================
    
    def _validate_move_destination(self, x: int, y: int, moving_unit):
        """Validate the destination tile for movement"""
        
        # Check if destination has a unit
        target_unit = self.unit_at(x, y)
        if target_unit:
            # Allow joining friendly units of same type
            if (target_unit.army == moving_unit.army and 
                target_unit.type == moving_unit.type and
                target_unit.status.hp < 100):
                return  # Valid for joining
            
            # Block all other unit occupations
            from error_handling import MovementError
            raise MovementError(
                f"Destination occupied by {target_unit.army.name} {target_unit.type.name}",
                to_pos=(x, y)
            )
        
        # Check if terrain is passable
        tile = self.tile_at(x, y)
        if not self._can_unit_traverse_terrain(moving_unit, tile.mapTile.type):
            from error_handling import MovementError
            raise MovementError(
                f"{moving_unit.type.name} cannot move onto {tile.mapTile.type.name}",
                to_pos=(x, y)
            )

    def _can_unit_traverse_terrain(self, unit, terrain) -> bool:
        """Check if unit can move onto specific terrain type"""
        
        unit_class = unit.status.cls
        
        # Get movement cost for this unit class on this terrain
        if terrain in MOVEMENT_COST:
            cost = MOVEMENT_COST[terrain][unit_class.value]
            return cost != 99999999  # INF means impassable
        
        # Default to passable if not in table
        return True

    def _calculate_movement_cost(self, unit, from_x: int, from_y: int, to_x: int, to_y: int) -> int:
        """Calculate movement cost considering terrain"""
        
        # For air units, movement is direct (Manhattan distance)
        if unit.is_air_unit():
            return abs(to_x - from_x) + abs(to_y - from_y)
        
        # For ground/sea units, try pathfinding
        try:
            from dijkstra import dijkstra
            source_tile = self.tile_at(from_x, from_y)
            target_tile = self.tile_at(to_x, to_y)
            
            path_cost = dijkstra(self.board, source_tile, target_tile)
            if path_cost == 99999999:  # No path found
                return abs(to_x - from_x) + abs(to_y - from_y)  # Fallback
            
            return min(path_cost, unit.status.move + 1)
        except:
            # Fallback to Manhattan distance
            return abs(to_x - from_x) + abs(to_y - from_y)

    def _calculate_fuel_cost(self, unit, from_x: int, from_y: int, to_x: int, to_y: int) -> int:
        """Calculate fuel cost based on movement points spent"""
        
        # Air units: 1 fuel per tile
        if unit.is_air_unit():
            return abs(to_x - from_x) + abs(to_y - from_y)
        
        # Ground/sea units: 1 fuel per movement point spent
        return self._calculate_movement_cost(unit, from_x, from_y, to_x, to_y)
    
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
    
    def consume_daily_fuel(self):
        """
        Consume daily fuel at start of each day
        - Air and sea units are destroyed if fuel hits 0
        - Land units become immobile but are not destroyed
        """
        
        destroyed_units = []
        immobilized_units = []
        
        for tile in self.board.grid:
            if not tile.unit:
                continue
                
            unit = tile.unit
            daily_fuel_cost = self._get_daily_fuel_cost(unit)
            
            if daily_fuel_cost > 0:
                unit.status.fuel -= daily_fuel_cost
                
                # Check if unit is affected by fuel depletion
                if unit.status.fuel <= 0:
                    unit.status.fuel = 0  # Don't go negative
                    
                    if unit.is_air_unit() or unit.is_sea_unit():
                        # Air and sea units are destroyed
                        destroyed_units.append((tile.x, tile.y, unit))
                    else:
                        # Land units become immobile but stay on board
                        unit.can_move = False
                        immobilized_units.append((tile.x, tile.y, unit))
        
        # Remove destroyed units (air and sea only)
        for x, y, unit in destroyed_units:
            unit_type = unit.type.name
            army = unit.army.name
            self.unit_remove(x, y)
            print(f"Unit destroyed due to fuel depletion: {army} {unit_type} at ({x}, {y})")
        
        return {
            "units_destroyed": len(destroyed_units),
            "units_immobilized": len(immobilized_units),
            "destroyed_details": [(x, y, unit.type.name, unit.army.name) for x, y, unit in destroyed_units],
            "immobilized_details": [(x, y, unit.type.name, unit.army.name) for x, y, unit in immobilized_units]
        }

    def _get_daily_fuel_cost(self, unit) -> int:
        """Get daily fuel consumption for different unit types"""
        
        # Copter units: 2 fuel per day (check this FIRST)
        if unit.is_copter_unit():
            return 2
        
        # Sea units: 1 fuel per day
        elif unit.is_sea_unit():
            return 1
        
        # Other air units: 5 fuel per day  
        elif unit.is_air_unit():
            return 5
        
        # Ground units: No daily fuel consumption
        return 0
'''[This is a manager for the RPC game engine for Advance war]'''


import math
from gameboard import GameBoard, GameTile
from unit import Army, UnitType, Unit, UnitClass
from dijkstra import dijkstra
from map_system import MapType, MOVEMENT_COST, INF
from config import Config
import configparser

from error_handling import logging, AWRPCError, ValidationError, GameStateError, UnitError, MovementError, TurnError, NotFoundError

config = configparser.ConfigParser()
config.read('config.ini')


REPAIR_CLASSES = {
    MapType.CITY: {UnitClass.BOOTS, UnitClass.TREADS, UnitClass.TYRES,
                   UnitClass.FOOT},
    MapType.FACTORY: {UnitClass.BOOTS, UnitClass.TREADS,
                      UnitClass.TYRES, UnitClass.FOOT},
    MapType.AIRPORT: {UnitClass.AIR},
    MapType.PORT: {UnitClass.SEA, UnitClass.LANDER},
    MapType.BASE_TOWER_1: {UnitClass.BOOTS, UnitClass.TREADS,
                           UnitClass.TYRES, UnitClass.FOOT},
}



# Turn system logger
logger = logging.getLogger(__name__)

class GameManager():

    def __init__(self, config: Config, board: GameBoard):
        self.config = config
        self.board = board

    def __repr__(self):
        return f"{self.__class__.__name__}"

    def coord_valid(self, x: int, y: int) -> bool:
        """Returns true if the coordinate is within the board width and height."""
        return 0 <= x < self.board.width and 0 <= y < self.board.height

    def check_turn_and_raise(self, unit):
        '''Raises exception if its not the units turn.'''
        if unit.army != self.board.current_turn:
            raise Exception(f'Not {unit.army.name}\'s turn (current: {self.board.current_turn.name})')

    def check_turn(self) -> str:
        '''Returns the units turn.'''
        turn = self.board.current_turn
        return turn

    def tile_at(self, x: int, y: int) -> GameTile:
        '''Returns the game tile at the coordinates given.'''
        index = x + y * self.board.width
        return self.board.grid[index]

    def tile_from_unit(self, unit: Unit) -> GameTile:
        '''Returns the tile the unit is on.'''
        for tile in self.board.grid:
            if tile.unit and tile.unit.id == unit.id:
                return tile

    def unit_at(self, x: int, y: int) -> Unit:
        '''Returns the unit at the given coordinates.'''
        return self.tile_at(x, y).unit

    def resupply_unit(self, unit: Unit):
        '''Sets the units fuel and ammo to the max for that unit.'''
        unit.status.fuel = int(config[unit.type.name]['fuel'])
        unit.status.ammo = int(config[unit.type.name]['ammo'])

    def unit_resupply(self, x: int, y: int, x2: int, y2: int):
        '''Resupplys the given unit from the unit specified.'''
        if not self.board.game_active:
            raise Exception("tried to resupply but Game Over")
        if not self.coord_valid(x, y):
            raise Exception('coordinate out of range')
        if not self.coord_valid(x2, y2):
            raise Exception('target coordinate out of range')
        tile = self.tile_get(x, y)
        unit = tile.unit
        self.check_turn_and_raise(unit)
        if not unit.can_resupply():
            raise Exception('unit cannot resupply')
        target = self.unit_at(x2, y2)
        if not target:
            raise Exception('no target unit to resupply')
        self.resupply_unit(target)

    def missile_damage(self, unit: Unit):
        '''Subtracts the missile damage for the given unit.'''
        unit.status.hp -= 30
        if unit.status.hp <= 10:
            unit.status.hp = 10

    def unit_can_move_to(self, unit: Unit, x: int, y: int) -> bool:
        '''Returns true if the unit can move to that coordinate.'''
        tile = self.tile_from_unit(unit)
        if tile.x == x and tile.y == y:
            return False
        if self.unit_at(x, y):
            return False
        dist = abs(x - tile.x) + abs(y - tile.y)
        if dist > unit.status.move:
            return False
        if dist > unit.status.fuel:
            return False
        dist = dijkstra(self.board, tile, self.tile_at(x, y))
        if dist > unit.status.move:
            return False
        return True

    def unit_can_join_to(self, unit: Unit, x: int, y: int) -> bool:
        '''Returns true if the unit can join to the unit at the
            coordinate given.'''
        tile = self.tile_from_unit(unit)
        if tile.x == x and tile.y == y:
            return False
        dist = abs(x - tile.x) + abs(y - tile.y)
        if dist > unit.status.move:
            return False
        if dist > unit.status.fuel:
            return False
        dist = dijkstra(self.board, tile, self.tile_at(x, y))
        if dist > unit.status.move:
            return False
        return True

# only call this from unit_load
    def _unit_can_load_to(self, unit: Unit, x: int, y: int) -> bool:
        '''Returns true if the unit can be loaded
           to the transport specified.'''
        tile = self.tile_from_unit(unit)
        if tile.x == x and tile.y == y:
            return False
        dist = abs(x - tile.x) + abs(y - tile.y)
        if dist > unit.status.move:
            return False
        dist = dijkstra(self.board, tile, self.tile_at(x, y))
        if dist > unit.status.move or dist > unit.status.fuel:
            return False
        return True

    def unit_can_attack(self, unit: Unit, x: int, y: int) -> bool:
        '''Returns true if the unit can attack.'''
        tile = self.tile_from_unit(unit)
        if tile.x == x and tile.y == y:
            return False
        target = self.unit_at(x, y)
        if not target:
            return False
        if target.army == unit.army:
            return False
        if not unit.is_attackable(target):
            return False
        dist = abs(x - tile.x) + abs(y - tile.y)
        return unit.status.rangemin <= dist <= unit.status.rangemax

    def unit_from_id(self, id: str) -> Unit:
        '''Returns the unit from the ID given.'''
        for tile in self.board.grid:
            if tile.unit and tile.unit.id == id:
                return tile.unit

    def unit_remove(self, x: int, y: int) -> Unit:
        '''Remove the unit at the given coordinates.'''
        tile = self.tile_at(x, y)
        unit = tile.unit
        # self.check_turn_and_raise(unit)
        tile.mapTile.is_capturable == True
        tile.capture_hp = 20
        tile.unit = None
        return unit

    def unit_remove2(self, id: str) -> Unit:
        '''Remove the unit with the given ID.'''
        for tile in self.board.grid:
            if tile.unit and tile.unit.id == id:
                unit = tile.unit
                tile.mapTile.is_capturable == True
                tile.capture_hp = 20
                tile.unit = None
                return unit

    def unit_place(self, unit: Unit, x: int, y: int):
        '''Place the unit at the given coordinates.'''
        self.tile_at(x, y).unit = unit

    def tile_get(self, x: int, y: int) -> GameTile:
        '''Return the tile at the given coordinates.'''
        if not self.coord_valid(x, y):
            raise Exception('coordinate out of range')
        return self.tile_at(x, y)

    def unit_deselect(self):
        '''Deselects the unit.'''
        self.board.selected = None
        for tile in self.board.grid:
            tile.can_be_moved_to = False
            tile.can_be_attacked = False

    def capture_tile(self, x: int, y: int):
        """Capture the tile at the given coordinate."""
        if not self.coord_valid(x, y):
            raise Exception('coordinate out of range')
        
        tile = self.tile_get(x, y)
        
        if tile.unit is None:
            raise Exception(f'No unit at {x}, {y}')
        
        if not tile.unit.can_capture:
            raise Exception('Unit cannot capture this turn')
        
        unit = tile.unit
        self.check_turn_and_raise(unit)
        
        if not tile.mapTile.is_capturable():
            raise Exception('Cannot capture this tile type')
        
        if not unit.type_can_capture():
            raise Exception('This unit type cannot capture properties')
        
        # Check if trying to capture own property
        if tile.mapTile.army == unit.army:
            raise Exception('Cannot capture your own property')
        
        # Calculate capture damage based on displayed HP (unit.status.hp / 10)
        # A full HP unit (100 HP) shows as 10 HP and deals 10 capture damage
        # A damaged unit (e.g., 55 HP) shows as 6 HP and deals 6 capture damage
        displayed_hp = math.ceil(unit.status.hp / 10)
        capture_damage = displayed_hp
        tile.capture_hp -= capture_damage
        
        logger.info(f"{unit.type.name} (HP: {displayed_hp}) deals {capture_damage} capture damage. Property HP: {tile.capture_hp} -> {tile.capture_hp - capture_damage}")
        
        # Check if property is fully captured
        if tile.capture_hp <= 0:
            old_army = tile.mapTile.army
            tile.mapTile.army = unit.army
            tile.capture_hp = 20
            
            logger.info(f"Property captured by {unit.army.name}!")
            
            # Check for HQ capture (ends game immediately)
            if tile.mapTile.is_hq():
                self.board.game_active = False
                logger.info(f"Game ended - {unit.army.name} captured {old_army.name if old_army else 'neutral'}'s HQ!")
        
        # Unit can't move or attack after capturing
        unit.can_move = False
        unit.can_attack = False
        unit.can_capture = False
        
        # Deselect unit
        self.unit_deselect()
        
        # Log capture status
        if tile.capture_hp > 0:
            logger.info(f"Capture in progress: {tile.capture_hp}/20 HP remaining")
        
        return tile
    def launch_missile(self, x: int, y: int, x2: int, y2: int) -> Unit:
        '''Launch missile from the silo at the given coordinate.  The damage
           will reach 2 tiles out for N-E-S-W directions
           and 1 for each diagonal'''
        # if self.board.game_active == False:
        #     raise Exception("tried to launch missile but Game Over")
        if not self.coord_valid(x, y):
            raise Exception('coordinate out of range')
        if not self.coord_valid(x2, y2):
            raise Exception('target coordinate out of range')
        tile = self.tile_get(x, y)
        if not tile.mapTile.type == MapType.MISSILE_SILO:
            raise Exception('cannot launch from this tile')
        if not tile.unit:
            raise Exception('unit does not exist at coordinate')
        tile.mapTile.type = MapType.EMPTY_SILO
        unit = tile.unit
        self.check_turn_and_raise(unit)
        unit.can_move = False
        unit.can_attack = False
        target = self.tile_get(x2, y2)
        if target.unit:
            unit = target.unit
            self.missile_damage(unit)
        b = x2 + 1
        if self.coord_valid(b, y2):
            target = self.tile_at(b, y2)
            if target.unit:
                unit = target.unit
                self.missile_damage(unit)
        b = x2 + 2
        if self.coord_valid(b, y2):
            target = self.tile_at(b, y2)
            if target.unit:
                unit = target.unit
                self.missile_damage(unit)
        c = y2 + 1
        if self.coord_valid(x2, c):
            target = self.tile_at(x2, c)
            if target.unit:
                unit = target.unit
                self.missile_damage(unit)
        c = y2 + 2
        if self.coord_valid(x2, c):
            target = self.tile_at(x2, c)
            if target.unit:
                unit = target.unit
                self.missile_damage(unit)
        b = x2 - 1
        if self.coord_valid(b, y2):
            target = self.tile_at(b, y2)
            if target.unit:
                unit = target.unit
                self.missile_damage(unit)
        b = x2 - 2
        if self.coord_valid(b, y2):
            target = self.tile_at(b, y2)
            if target.unit:
                unit = target.unit
                self.missile_damage(unit)
        c = y2 - 1
        if self.coord_valid(x2, c):
            target = self.tile_at(x2, c)
            if target.unit:
                unit = target.unit
                self.missile_damage(unit)
        c = y2 - 2
        if self.coord_valid(x2, c):
            target = self.tile_at(x2, c)
            if target.unit:
                unit = target.unit
                self.missile_damage(unit)
        b = x2 + 1
        c = y2 + 1
        if self.coord_valid(b, c):
            target = self.tile_at(b, c)
            if target.unit:
                unit = target.unit
                self.missile_damage(unit)
        b = x2 + 1
        c = y2 - 1
        if self.coord_valid(b, c):
            target = self.tile_at(b, c)
            if target.unit:
                self.missile_damage(unit)
        b = x2 - 1
        c = y2 + 1
        if self.coord_valid(b, c):
            target = self.tile_at(b, c)
            if target.unit:
                unit = target.unit
                self.missile_damage(unit)
        b = x2 - 1
        c = y2 - 1
        if self.coord_valid(b, c):
            target = self.tile_at(b, c)
            if target.unit:
                unit = target.unit
                self.missile_damage(unit)
        return tile

    def unit_wait(self, x: int, y: int):
        '''Sets the bool false for the unit at the given coordinates.'''
        # if self.board.game_active == False:
        #     raise Exception("tried to wait but Game Over")
        if not self.coord_valid(x, y):
            raise Exception('coordinate out of range')
        tile = self.tile_get(x, y)
        if not tile.unit:
            raise Exception('unit does not exist at coordinate')
        unit = tile.unit
        logger.debug(f'unit_wait: unit={unit.army.name}, turn={self.board.current_turn.name}')
        self.check_turn_and_raise(unit)
        unit.can_move = False
        unit.can_attack = False
        unit.can_capture = False
        self.unit_deselect()
        return self.tile_at(x, y)

    #
    # Public functions
    #

    def end_game(self):
        '''Ends the game'''
        self.board.game_active = False

    def army_end_turn(self):
        """Enhanced turn ending with proper unit management and fuel consumption."""
        if not self.board.game_active:
            raise Exception("Cannot end turn - game is over")
        
        logger.info(f"Ending turn for {self.board.current_turn.name}")
        
        # Clear selection and movement flags
        self.unit_deselect()
        
        # Process current turn's units before switching
        self._process_current_turn_units()
        
        # Update army totals and funds
        self._update_army_totals()
        
        # Switch to next army
        self._advance_turn()
        
        # Distribute income to the new current army
        self._distribute_income()
        
        # Setup next turn's units
        self._setup_next_turn_units()
        
        # Reset capture progress for unoccupied properties
        self._reset_capture_progress()
        
        # Check for victory conditions
        self._check_victory_conditions()
        
        logger.info(f"Turn advanced to {self.board.current_turn.name}, Day: {self.board.days}")
    def unit_select(self, x: int, y: int) -> Unit:
        '''Select the unit at the given coordinates if valid.'''
        if not self.coord_valid(x, y):
            raise Exception('coordinate out of range')
        tile = self.tile_at(x, y)
        if not tile.unit:
            raise Exception('unit does not exist at coordinate')
        if self.board.selected and tile.unit == self.board.selected.unit:
            self.unit_deselect()
        else:
            self.check_turn_and_raise(tile.unit)
            self.board.selected = tile
            unit = tile.unit
            for tile in self.board.grid:
                if unit.can_move:
                    tile.can_be_moved_to = self.unit_can_move_to(unit,
                                                                 tile.x,
                                                                 tile.y)
                else:
                    tile.can_be_moved_to = False
                if unit.can_attack:
                    tile.can_be_attacked = self.unit_can_attack(unit,
                                                                tile.x,
                                                                tile.y)
                else:
                    tile.can_be_attacked = False
        return tile.unit

    def unit_move(self, x: int, y: int, x2: int, y2: int) -> Unit:
        '''Enhanced unit movement with comprehensive validation'''
        
        # Validate coordinates are in bounds
        if not (0 <= x < self.board.width and 0 <= y < self.board.height):
            raise MovementError(
                f"Source coordinates out of bounds: ({x}, {y})",
                from_pos=(x, y),
                details={"board_size": {"width": self.board.width, "height": self.board.height}}
            )
        
        if not (0 <= x2 < self.board.width and 0 <= y2 < self.board.height):
            raise MovementError(
                f"Target coordinates out of bounds: ({x2}, {y2})",
                to_pos=(x2, y2),
                details={"board_size": {"width": self.board.width, "height": self.board.height}}
            )
        
        # Check if game is active
        if not self.board.game_active:
            raise GameStateError("Game has ended, movement not allowed")
        
        # Get source unit
        source_unit = self.unit_at(x, y)
        if not source_unit:
            raise UnitError(f"No unit found at position ({x}, {y})")
        
        # Validate unit ownership
        if source_unit.army != self.board.current_turn:
            raise TurnError(
                f"Unit belongs to {source_unit.army.name}, but it's {self.board.current_turn.name}'s turn",
                current_army=self.board.current_turn.name,
                details={"unit_army": source_unit.army.name}
            )
        
        # Validate unit can move
        if not source_unit.can_move:
            raise UnitError(
                "Unit has already moved this turn",
                unit_id=str(source_unit.id),
                details={"action": "move"}
            )
        
        # Check target tile
        target_unit = self.unit_at(x2, y2)
        if target_unit:
            if target_unit.army == source_unit.army:
                raise MovementError(
                    f"Target position ({x2}, {y2}) occupied by friendly unit",
                    from_pos=(x, y),
                    to_pos=(x2, y2),
                    details={"target_unit_type": target_unit.type.name}
                )
            else:
                raise MovementError(
                    f"Target position ({x2}, {y2}) occupied by enemy unit",
                    from_pos=(x, y),
                    to_pos=(x2, y2),
                    details={"target_unit_type": target_unit.type.name, "target_army": target_unit.army.name}
                )
        
        # Validate movement is possible (use your existing pathfinding)
        if not self.unit_can_move_to(source_unit, x2, y2):
            raise MovementError(
                f"Unit cannot reach position ({x2}, {y2})",
                from_pos=(x, y),
                to_pos=(x2, y2),
                details={"unit_type": source_unit.type.name, "movement_range": source_unit.status.move}
            )
        
        # Perform the move
        unit = self.unit_remove(x, y)
        self.unit_place(unit, x2, y2)
        unit.can_move = False

        # Handle post-move effects
        distance = abs(x2 - x) + abs(y2 - y)  # Manhattan distance
        unit.status.fuel = max(0, unit.status.fuel - distance)

        # Clear selection
        self.unit_deselect()

        return unit
    
    def unit_move2(self, id: str, x: int, y: int) -> Unit:
        '''Move a unit with ID to the coordinate given.'''
        unit = self.unit_from_id(id)
        if not unit:
            raise Exception('unit not found')
        self.check_turn_and_raise(unit)
        tile = self.tile_from_unit(unit)
        return self.unit_move(tile.x, tile.y, x, y)

    def unit_create(self, army: str, unit_type: str, x: int, y: int) -> Unit:
        '''Create a unit given the unit type
           and army at the coordinate given.'''
        army = army.upper()
        unit_type = unit_type.upper()
        try:
            Army[army]
        except KeyError:
            raise Exception('invalid "army" parameter')
        try:
            UnitType[unit_type]
        except KeyError:
            raise Exception('invalid "unit_type" parameter')
        if not self.coord_valid(x, y):
            raise Exception('coordinate out of range')
        if self.unit_at(x, y):
            raise Exception('unit already exists at this tile')
        unit = Unit.create(Army[army], UnitType[unit_type],
                           self.config.units[unit_type])

        if self.board.current_turn.name == 'RED':
            wallet = self.board.red_funds
            if int(config[unit.type.name]['cost']) <= wallet:
                self.board.red_funds -= int(config[unit.type.name]['cost'])
                self.board.total_red_troops += 1
            else:
                raise Exception('not enough funds for this unit')
        if self.board.current_turn.name == 'BLUE':
            wallet = self.board.blue_funds
            if int(config[unit.type.name]['cost']) <= wallet:
                self.board.blue_funds -= int(config[unit.type.name]['cost'])
                self.board.total_blue_troops += 1
            else:
                raise Exception('not enough funds for this unit')
        self.unit_place(unit, x, y)
        self.check_turn_and_raise(unit)
        return unit

    def unit_attack(self, x: int, y: int, x2: int, y2: int) -> Unit:
        '''Attacks from/to the cordinates given.'''
        if not self.coord_valid(x, y):
            raise Exception('coordinate out of range')
        if not self.coord_valid(x2, y2):
            raise Exception('coordinate out of range')
        attacker = self.unit_at(x, y)
        attacker_tile = self.tile_at(x, y)
        self.check_turn_and_raise(attacker)
        defender = self.unit_at(x2, y2)
        if not attacker.can_attack:
            raise Exception('unit can not attack')
        defender_tile = self.tile_at(x2, y2)
        if not attacker:
            raise Exception('unit does not exist at source tile')
        if not defender:
            raise Exception('unit does not exist at target tile')
        if not self.unit_can_attack(attacker, x2, y2):
            raise Exception('target tile too far')
        if attacker.is_direct() and defender.is_direct():
            defender.status.hp -= attacker.attack_damage(defender,
                                                         defender_tile)
            attacker.status.ammo -= 1
            if defender.status.hp >= 1:
                attacker.status.hp -= defender.attack_damage(attacker,
                                                             attacker_tile)
                defender.status.ammo -= 1
            else:
                self.unit_remove(x2, y2)
        if attacker.is_direct() and defender.is_indirect():
            defender.status.hp -= attacker.attack_damage(defender,
                                                         defender_tile)
            attacker.status.ammo -= 1
            if defender.status.hp <= 1:
                self.unit_remove(x2, y2)
        if attacker.is_indirect():
            defender.status.hp -= attacker.attack_damage(defender,
                                                         defender_tile)
            attacker.status.ammo -= 1
            if defender.status.hp <= 1:
                self.unit_remove(x2, y2)
        if attacker.status.hp < 1:
            self.unit_remove(x, y)
        attacker.can_capture = False
        attacker.can_move = False
        attacker.can_attack = False
        self.unit_deselect()
        unit = self.unit_at(x, y)
        return unit

    def damage_estimate(self, x: int, y: int, x2: int, y2: int) -> list:
        '''Returns the estimate damage
           for the units at the given coordinates.'''
        if not self.coord_valid(x, y):
            raise Exception('coordinate out of range')
        if not self.coord_valid(x2, y2):
            raise Exception('coordinate out of range')
        attacker = self.unit_at(x, y)
        attacker_tile = self.tile_at(x, y)
        defender = self.unit_at(x2, y2)
        defender_tile = self.tile_at(x2, y2)
        defender_hp = 100
        attacker_hp = 100
        if not attacker:
            raise Exception('unit does not exist at source tile')
        if not defender:
            raise Exception('unit does not exist at target tile')
        if attacker.is_direct() and defender.is_direct():
            defender_hp = defender.status.hp
            - attacker.attack_damage(defender, defender_tile)
            if defender.status.hp >= 1:
                attacker_hp = attacker.status.hp
                - defender.attack_damage(attacker, attacker_tile)
        if attacker.is_direct() and defender.is_indirect():
            defender_hp = defender.status.hp
            - attacker.attack_damage(defender, defender_tile)
        if attacker.is_indirect():
            defender.status.hp -= attacker.attack_damage(defender,
                                                         defender_tile)
        return attacker_hp, defender_hp

    def unit_delete(self, x: int, y: int) -> Unit:
        '''Deletes the unit at the given cordinates.'''
        unit = self.unit_remove(x, y)
        return unit

    def unit_join(self, x: int, y: int, x2: int, y2: int) -> Unit:
        '''Joins the unit from/to the cordinates given.'''
        if not self.coord_valid(x, y):
            raise Exception('coordinate out of range')
        if not self.coord_valid(x2, y2):
            raise Exception('coordinate out of range')
        unit = self.unit_at(x, y)
        self.check_turn_and_raise(unit)
        unit2 = self.unit_at(x2, y2)
        if not unit:
            raise Exception('unit does not exist at source tile')
        if not unit2:
            raise Exception('unit does not exist at target tile')
        if not unit.type == unit2.type:
            raise Exception('cannot join different units')
        if unit2.status.hp == 100:
            raise Exception('cannot join a full hp unit')
        if not self.unit_can_join_to(unit, x2, y2):
            raise Exception('target tile too far')
        unit2.status.hp = min(100, unit2.status.hp + unit.status.hp)
        unit2.can_capture = False
        unit2.can_attack = False
        unit2.can_move = False
        self.unit_remove(x, y)
        return unit2

    def unit_load(self, x: int, y: int, x2: int, y2: int) -> Unit:
        '''Loads the unit from / to the coordinates given.'''
        if not self.coord_valid(x, y):
            raise Exception('coordinate out of range')
        if not self.coord_valid(x2, y2):
            raise Exception('coordinate out of range')
        unit = self.unit_at(x, y)
        transport = self.unit_at(x2, y2)
        if not unit:
            raise Exception('unit does not exist at source tile')
        self.check_turn_and_raise(unit)
        if not transport:
            raise Exception('unit does not exist at target tile')
        if transport.army is not unit.army:
            raise Exception('army is not same type')
        if not transport.can_carry(unit):
            raise Exception('cannot carry this unit type')
        if len(transport.status.cargo) >= transport.capacity():
            raise Exception('transport is full')
        if not unit.can_move:
            raise Exception('unit can not move')
        if not self._unit_can_load_to(unit, x2, y2):
            raise Exception('target tile too far')
        tile = self.tile_from_unit(unit)
        dist = abs(x - tile.x) + abs(y - tile.y)
        unit.status.fuel -= dist
        if transport.type in {UnitType.CARRIER, UnitType.CRUISER}:
            self.resupply_unit(unit)
        unit = self.unit_remove(x, y)
        transport.status.cargo.append(unit)
        # For the moment, fuel cost is simplified, Manhatten distance.
        unit.can_move = False
        unit.can_attack = False
        self.unit_deselect()
        return transport

    def _process_current_turn_units(self):
        """Process units for the army ending their turn."""
        units_to_remove = []
        
        for tile in self.board.grid:
            if tile.unit and tile.unit.army == self.board.current_turn:
                unit = tile.unit
                
                # Disable unit actions for this turn
                unit.can_move = False
                unit.can_attack = False
                unit.can_capture = False
                
                # Consume daily fuel for air/sea units
                if unit.fuel_daily_use():
                    unit.status.fuel -= unit.fuel_use()
                    logger.debug(f"{unit.type.name} consumed {unit.fuel_use()} fuel")
                    
                    # Remove units that run out of fuel
                    if unit.status.fuel <= 0:
                        logger.info(f"{unit.type.name} at ({tile.x}, {tile.y}) ran out of fuel")
                        units_to_remove.append((tile.x, tile.y))
                        continue
                
                # Repair and resupply units on friendly properties
                self._repair_unit_on_property(unit, tile)
                
                # APC/Blackboat resupply adjacent units
                if unit.type in {UnitType.APC, UnitType.BLACKBOAT}:
                    self._resupply_adjacent_units(tile)
        
        # Remove fuel-depleted units
        for x, y in units_to_remove:
            self.unit_remove(x, y)

    def _repair_unit_on_property(self, unit, tile):
        """Repair and resupply unit if on appropriate friendly property."""
        if (unit.army == tile.mapTile.army and 
            unit.status.cls in REPAIR_CLASSES.get(tile.mapTile.type, set())):
            
            # Repair 2 HP per turn (20% of max)
            old_hp = unit.status.hp
            unit.status.hp = min(100, unit.status.hp + 20)
            
            # Full resupply
            self.resupply_unit(unit)
            
            if unit.status.hp > old_hp:
                logger.debug(f"{unit.type.name} repaired {unit.status.hp - old_hp} HP")

    def _resupply_adjacent_units(self, transport_tile):
        """Resupply units adjacent to APC/Blackboat."""
        adjacent_coords = [
            (transport_tile.x + 1, transport_tile.y),
            (transport_tile.x - 1, transport_tile.y),
            (transport_tile.x, transport_tile.y + 1),
            (transport_tile.x, transport_tile.y - 1)
        ]
        
        for x, y in adjacent_coords:
            if self.coord_valid(x, y):
                target_tile = self.tile_at(x, y)
                if (target_tile.unit and 
                    target_tile.unit.army == transport_tile.unit.army):
                    self.resupply_unit(target_tile.unit)
                    logger.debug(f"Resupplied {target_tile.unit.type.name} at ({x}, {y})")

    def _update_army_totals(self):
        """Update troop counts and property income for all armies."""
        # Reset counters
        self.board.total_red_troops = 0
        self.board.total_blue_troops = 0
        self.board.total_red_properties = 0
        self.board.total_blue_properties = 0
        
        # Count units
        for tile in self.board.grid:
            if tile.unit:
                if tile.unit.army.value == 0:  # RED
                    self.board.total_red_troops += 1
                elif tile.unit.army.value == 1:  # BLUE
                    self.board.total_blue_troops += 1
        
        # Count properties (but don't add income here - that happens at start of turn)
        for tile in self.board.grid:
            if tile.mapTile.army:
                if tile.mapTile.army.name == "RED":
                    self.board.total_red_properties += 1
                elif tile.mapTile.army.name == "BLUE":
                    self.board.total_blue_properties += 1
    def _distribute_income(self):
        """Distribute income to the army starting their turn."""
        property_income = int(config['FUNDS']['income'])
        current_army = self.board.current_turn.name
        
        # Count properties for current army and give income
        properties_owned = 0
        for tile in self.board.grid:
            if tile.mapTile.army and tile.mapTile.army.name == current_army:
                properties_owned += 1
        
        total_income = properties_owned * property_income
        
        if current_army == "RED":
            self.board.red_funds += total_income
            logger.info(f"RED received {total_income} funds from {properties_owned} properties")
        elif current_army == "BLUE":
            self.board.blue_funds += total_income
            logger.info(f"BLUE received {total_income} funds from {properties_owned} properties")

    def _advance_turn(self):
        """Advance to the next army in turn order."""
        current_idx = self.board.turn_order.index(self.board.current_turn)
        next_idx = (current_idx + 1) % len(self.board.turn_order)
        self.board.current_turn = self.board.turn_order[next_idx]
        
        # Increment day counter when returning to first player
        if next_idx == 0:
            self.board.days += 1

    def _setup_next_turn_units(self):
        """Enable actions for the new current army's units."""
        for tile in self.board.grid:
            if tile.unit and tile.unit.army == self.board.current_turn:
                unit = tile.unit
                unit.can_move = True
                unit.can_attack = True
                unit.can_capture = True

    def _reset_capture_progress(self):
        """Reset capture progress for properties without occupying units."""
        for tile in self.board.grid:
            if tile.mapTile.is_capturable() and not tile.unit:
                tile.capture_hp = 20

    def _check_victory_conditions(self):
        """Check if the game should end due to victory conditions."""
        # Only check victory conditions if the game has progressed beyond initial setup
        # (i.e., some units have been created and it's past day 1)
        if self.board.days < 1:
            return
        
        # Check if any HQ has been captured (ownership changed, not just occupied)
        # An HQ is captured when its army ownership has changed from the original
        # We don't check for unit occupation here, only actual ownership change
        for tile in self.board.grid:
            if tile.mapTile.is_hq():
                # Check if this HQ was captured by looking at ownership vs original
                # This should only trigger when capture_tile actually changes ownership
                # The capture_tile method will set game_active = False when HQ is captured
                pass  # Victory condition is handled in capture_tile method

        # Count units for each army
        army_unit_counts = {}
        total_units = 0
        
        for tile in self.board.grid:
            if tile.unit:
                army = tile.unit.army
                army_unit_counts[army] = army_unit_counts.get(army, 0) + 1
                total_units += 1
        
        # Only check elimination if:
        # 1. There are actually units on the board
        # 2. The game has progressed (day > 0)
        # 3. At least one army had units at some point
        if total_units > 0 and self.board.days > 0:
            armies_with_units = set(army_unit_counts.keys())
            
            # Game ends only if exactly one army remains AND there were multiple armies before
            if len(armies_with_units) == 1 and len(self.board.turn_order) > 1:
                # Check if this army elimination is legitimate by ensuring other armies
                # had units at some point (check if they have properties or previous activity)
                other_armies_exist = False
                winning_army = list(armies_with_units)[0]
                
                for army in self.board.turn_order:
                    if army != winning_army:
                        # Check if this army has properties (indicating they were active)
                        for tile in self.board.grid:
                            if tile.mapTile.army == army:
                                other_armies_exist = True
                                break
                        if other_armies_exist:
                            break
                
                if other_armies_exist:
                    self.board.game_active = False
                    winner = winning_army
                    logger.info(f"Game ended - {winner.name} eliminated all other armies!")
                    return
        
        # Check for stalemate conditions (optional - can be added later)
        # For now, only end on HQ capture or legitimate elimination

    def unit_unload(
            self, x: int, y: int, x2: int, y2: int, index: int) -> Unit:
        '''Unloads the unit from / to the coordinates.'''
        if not self.coord_valid(x, y):
            raise Exception('coordinate out of range')
        if not self.coord_valid(x2, y2):
            raise Exception('coordinate out of range')
        transport = self.unit_at(x, y)
        if not transport:
            raise Exception('unit does not exist at source tile')
        self.check_turn_and_raise(transport)
        if self.unit_at(x2, y2):
            raise Exception('unit already exists at target tile')
        dist = abs(x - x2) + abs(y - y2)
        if dist >= 2:
            raise Exception('can only unload to adjacent tile')
        if len(transport.status.cargo) == 0:
            raise Exception('cargo is empty')
        unit = transport.status.cargo[index]
        target_tile = self.tile_get(x2, y2)
        if MOVEMENT_COST[target_tile.mapTile.type][unit.status.cls.value] == INF:
            raise Exception('unit cannot unload to tile')
        unit = transport.status.cargo.pop(index)
        self.unit_place(unit, x2, y2)
        self.can_move = False
        self.can_attack = False
        transport.can_move = False
        transport.can_attack = False
        return unit

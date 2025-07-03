'''[This is a manager for the RPC game engine for Advance war]'''


import math
from gameboard import GameBoard, GameTile
from unit import Army, UnitType, Unit, UnitClass
from dijkstra import dijkstra
from map_system import MapType, MOVEMENT_COST, INF
from config import Config
import configparser

from error_handling import logging, AWRPCError, ValidationError, GameStateError, UnitError, MovementError, TurnError, NotFoundError
from enhanced_logging import log_movement, log_attack, log_game_event, log_error

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
    def __init__(self, config: Config, board: GameBoard, token: str = 'unknown'):
        self.config = config
        self.board = board
        self.current_token = token

    def __repr__(self):
        return f"{self.__class__.__name__}"

    def coord_valid(self, x: int, y: int) -> bool:
        '''Returns true if the coordinate is within the board width and height.'''
        return 0 <= x < self.board.width and 0 <= y < self.board.height  # FIXED!

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
        source_tile = self.tile_from_unit(unit)
        
        # Check if target coordinates are valid
        if not self.coord_valid(x, y):
            return False
        
        # Can't move to occupied tile
        target_unit = self.unit_at(x, y)
        if target_unit:
            return False
             
        # Simple check: if moving horizontally/vertically, check each tile
        if source_tile.x == x:  # Vertical movement
            start_y = min(source_tile.y, y)
            end_y = max(source_tile.y, y)
            for check_y in range(start_y + 1, end_y):
                blocking_unit = self.unit_at(x, check_y)
                if blocking_unit and blocking_unit.army != unit.army:
                    return False
        elif source_tile.y == y:  # Horizontal movement
            start_x = min(source_tile.x, x)
            end_x = max(source_tile.x, x)
            for check_x in range(start_x + 1, end_x):
                blocking_unit = self.unit_at(check_x, y)
                if blocking_unit and blocking_unit.army != unit.army:
                    return False
        
        # Check basic movement constraints
        manhattan_dist = abs(x - source_tile.x) + abs(y - source_tile.y)
        if manhattan_dist > unit.status.move or manhattan_dist > unit.status.fuel:
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

    # Fixed capture_tile method in manager.py

    def capture_tile(self, x: int, y: int):
        '''Capture the tile at the given coordinate.'''
        if not self.coord_valid(x, y):
            raise Exception('coordinate out of range')
        
        tile = self.tile_get(x, y)
        
        # Check if unit exists
        if tile.unit is None:
            raise Exception(f'No unit at {x}, {y}')
        
        unit = tile.unit
        self.check_turn_and_raise(unit)
        
        # Check if unit can capture this turn
        if not unit.can_capture:
            raise Exception('Unit cannot capture this turn')
        
        # Check if unit type can capture
        if not unit.type_can_capture():
            raise Exception('Unit type cannot capture properties')
        
        # Check if tile is capturable
        if not tile.mapTile.is_capturable():
            raise Exception('This tile cannot be captured')
        
        # Check if it's already owned by the same army
        if tile.mapTile.army and tile.mapTile.army == unit.army:
            raise Exception('Cannot capture your own property')
        
        # Calculate capture damage based on unit HP
        capture_damage = math.ceil(unit.status.hp / 10)
        tile.capture_hp -= capture_damage
        
        # If fully captured
        if tile.capture_hp <= 0:
            # Remove income from previous owner
            if tile.mapTile.army:
                if tile.mapTile.army.name == 'RED':
                    self.board.total_red_properties -= int(config['FUNDS']['income'])
                    self.board.red_funds -= int(config['FUNDS']['income'])  # Remove from current funds too
                elif tile.mapTile.army.name == 'BLUE':
                    self.board.total_blue_properties -= int(config['FUNDS']['income'])
                    self.board.blue_funds -= int(config['FUNDS']['income'])
            
            # Transfer ownership
            tile.mapTile.army = unit.army
            tile.capture_hp = 20
            
            # Add income to new owner
            if unit.army.name == 'RED':
                self.board.total_red_properties += int(config['FUNDS']['income'])
            elif unit.army.name == 'BLUE':
                self.board.total_blue_properties += int(config['FUNDS']['income'])
            
            # Check for game-ending conditions (HQ capture)
            if tile.mapTile.type == MapType.BASE_TOWER_1:
                self.board.game_active = False
        
        # Set unit flags - unit is spent after capturing
        unit.can_move = False
        unit.can_attack = False
        unit.can_capture = False
        
        # Deselect unit
        self.unit_deselect()
        
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

    # def army_end_turn(self):
    # '''Ends the army turn with proper repair timing.'''
    # if self.board.game_active == False:
    #     raise Exception("tried to end turn but Game Over")
    
    # self.unit_deselect()
    # current_army = self.board.current_turn.name
    
    # # 1. FUEL CONSUMPTION (end of current turn)
    # for tile in self.board.grid:
    #     if tile.unit and tile.unit.army == self.board.current_turn:
    #         unit = tile.unit
    #         unit.can_move = False
    #         unit.can_attack = False
            
    #         # Consume fuel for units that use fuel daily
    #         unit.status.fuel -= unit.fuel_use()
    #         if unit.fuel_daily_use() and unit.status.fuel <= 0:
    #             self.unit_remove(tile.x, tile.y)
    #             log_game_event(
    #                 token=self.current_token,
    #                 event_type="UNIT_DESTROYED",
    #                 army=unit.army.name,
    #                 details=f"{unit.type.name} ran out of fuel at ({tile.x},{tile.y})"
    #             )
    
    def army_end_turn(self):
        '''Ends the army turn with proper repair timing.'''
        if self.board.game_active == False:
            raise Exception("tried to end turn but Game Over")
        
        self.unit_deselect()
        current_army = self.board.current_turn.name
        
        # 1. FUEL CONSUMPTION (end of current turn)
        for tile in self.board.grid:
            if tile.unit and tile.unit.army == self.board.current_turn:
                unit = tile.unit
                unit.can_move = False
                unit.can_attack = False
                
                # Consume fuel for units that use fuel daily
                unit.status.fuel -= unit.fuel_use()
                if unit.fuel_daily_use() and unit.status.fuel <= 0:
                    self.unit_remove(tile.x, tile.y)
                    log_game_event(
                        token=self.current_token,
                        event_type="UNIT_DESTROYED",
                        army=unit.army.name,
                        details=f"{unit.type.name} ran out of fuel at ({tile.x},{tile.y})"
                    )
        
        # 2. CHANGE TURNS
        log_game_event(
            token=self.current_token,
            event_type="TURN_END",
            army=current_army,
            details=f"Turn ended for {current_army}"
        )
        
        # Change current_turn
        idx = None
        for i in range(len(self.board.turn_order)):
            if self.board.turn_order[i] == self.board.current_turn:
                idx = i
                break
        idx += 1
        if idx >= len(self.board.turn_order):
            idx = 0
        self.board.current_turn = self.board.turn_order[idx]
        
        # Increment day counter when RED's turn starts
        if self.board.current_turn.name == "RED":
            self.board.days += 1
        
        # 3. START OF NEW TURN - REPAIRS AND ACTIVATION
        for tile in self.board.grid:
            if tile.unit and tile.unit.army == self.board.current_turn:
                unit = tile.unit
                unit.can_move = True
                unit.can_attack = True
                unit.can_capture = True
                
                # REPAIR UNITS ON OWNED PROPERTIES (start of turn)
                if (tile.mapTile.army == unit.army and 
                    tile.mapTile.type in [MapType.CITY, MapType.FACTORY, MapType.AIRPORT, 
                                        MapType.PORT, MapType.BASE_TOWER_1, MapType.BASE_TOWER_2]):
                    old_hp = unit.status.hp
                    unit.status.hp = min(100, unit.status.hp + 20)
                    self.resupply_unit(unit)
                    
                    # Log the repair
                    if unit.status.hp > old_hp:
                        log_game_event(
                            token=self.current_token,
                            event_type="UNIT_REPAIRED",
                            army=unit.army.name,
                            details=f"{unit.type.name} repaired from {old_hp} to {unit.status.hp} HP at ({tile.x},{tile.y})"
                        )
        
        # 4. RESUPPLY FROM APC/BLACK BOAT (start of turn)
        for tile in self.board.grid:
            if tile.unit and tile.unit.army == self.board.current_turn:
                unit = tile.unit
                if unit.type in {UnitType.APC, UnitType.BLACKBOAT}:
                    # Resupply adjacent units
                    for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                        adj_x, adj_y = tile.x + dx, tile.y + dy
                        if self.coord_valid(adj_x, adj_y):
                            adj_tile = self.tile_at(adj_x, adj_y)
                            if (adj_tile.unit and 
                                adj_tile.unit.army == unit.army and
                                adj_tile.unit != unit):
                                self.resupply_unit(adj_tile.unit)
                                log_game_event(
                                    token=self.current_token,
                                    event_type="UNIT_RESUPPLIED",
                                    army=unit.army.name,
                                    details=f"{adj_tile.unit.type.name} resupplied by {unit.type.name}"
                                )
        
        log_game_event(
            token=self.current_token,
            event_type="TURN_START",
            army=self.board.current_turn.name,
            details=f"Turn started for {self.board.current_turn.name}, Day {self.board.days}"
        )
        
        # 2. CHANGE TURNS
        log_game_event(
            token=self.current_token,
            event_type="TURN_END",
            army=current_army,
            details=f"Turn ended for {current_army}"
        )
        
        # Change current_turn
        idx = None
        for i in range(len(self.board.turn_order)):
            if self.board.turn_order[i] == self.board.current_turn:
                idx = i
                break
        idx += 1
        if idx >= len(self.board.turn_order):
            idx = 0
        self.board.current_turn = self.board.turn_order[idx]
        
        # Increment day counter when RED's turn starts
        if self.board.current_turn.name == "RED":
            self.board.days += 1
        
        # 3. START OF NEW TURN - REPAIRS AND ACTIVATION
        for tile in self.board.grid:
            if tile.unit and tile.unit.army == self.board.current_turn:
                unit = tile.unit
                unit.can_move = True
                unit.can_attack = True
                unit.can_capture = True
                
                # REPAIR UNITS ON OWNED PROPERTIES (start of turn)
                if (tile.mapTile.army == unit.army and 
                    tile.mapTile.type in [MapType.CITY, MapType.FACTORY, MapType.AIRPORT, 
                                        MapType.PORT, MapType.BASE_TOWER_1, MapType.BASE_TOWER_2]):
                    old_hp = unit.status.hp
                    unit.status.hp = min(100, unit.status.hp + 20)
                    self.resupply_unit(unit)
                    
                    # Log the repair
                    if unit.status.hp > old_hp:
                        log_game_event(
                            token=self.current_token,
                            event_type="UNIT_REPAIRED",
                            army=unit.army.name,
                            details=f"{unit.type.name} repaired from {old_hp} to {unit.status.hp} HP at ({tile.x},{tile.y})"
                        )
        
        # 4. RESUPPLY FROM APC/BLACK BOAT (start of turn)
        for tile in self.board.grid:
            if tile.unit and tile.unit.army == self.board.current_turn:
                unit = tile.unit
                if unit.type in {UnitType.APC, UnitType.BLACKBOAT}:
                    # Resupply adjacent units
                    for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                        adj_x, adj_y = tile.x + dx, tile.y + dy
                        if self.coord_valid(adj_x, adj_y):
                            adj_tile = self.tile_at(adj_x, adj_y)
                            if (adj_tile.unit and 
                                adj_tile.unit.army == unit.army and
                                adj_tile.unit != unit):
                                self.resupply_unit(adj_tile.unit)
                                log_game_event(
                                    token=self.current_token,
                                    event_type="UNIT_RESUPPLIED",
                                    army=unit.army.name,
                                    details=f"{adj_tile.unit.type.name} resupplied by {unit.type.name}"
                                )
        
        log_game_event(
            token=self.current_token,
            event_type="TURN_START",
            army=self.board.current_turn.name,
            details=f"Turn started for {self.board.current_turn.name}, Day {self.board.days}"
        )
       
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
        '''Move the unit with proper fuel consumption based on actual path taken.'''
        if not self.coord_valid(x, y):
            raise Exception('Source coordinates out of range')
        if not self.coord_valid(x2, y2):
            raise Exception('Target coordinates out of range')
        
        unit = self.unit_at(x, y)
        distance = abs(x2 - x) + abs(y2 - y)
        if not unit:
            raise Exception('No unit at source coordinates')
        
        self.check_turn_and_raise(unit)
        
        if not unit.can_move:
            raise Exception('Unit cannot move this turn')
        
        # Check if target is occupied
        target_unit = self.unit_at(x2, y2)
        if target_unit:
            if (target_unit.army == unit.army and 
                target_unit.type == unit.type and 
                target_unit.status.hp < 100):
                # This is a join operation
                return self.unit_join(x, y, x2, y2)
            else:
                raise Exception('Target tile is occupied')
        
        # Calculate actual fuel cost using pathfinding
        source_tile = self.tile_at(x, y)
        target_tile = self.tile_at(x2, y2)
               
        try:
            # Use dijkstra to get actual path cost
            actual_fuel_cost = dijkstra(self.board, source_tile, target_tile)
            
            if actual_fuel_cost >= INF:
                raise Exception('No valid path to target location')
            
            if actual_fuel_cost > unit.status.move:
                raise Exception(f'Target too far: need {actual_fuel_cost} movement, have {unit.status.move}')
            
            if actual_fuel_cost > unit.status.fuel:
                raise Exception(f'Not enough fuel: need {actual_fuel_cost}, have {unit.status.fuel}')
                
        except Exception as path_error:
            # Fallback to Manhattan distance
            manhattan_cost = abs(x2 - x) + abs(y2 - y)
            if manhattan_cost > unit.status.move or manhattan_cost > unit.status.fuel:
                raise Exception(f'Movement failed: {path_error}')
            actual_fuel_cost = manhattan_cost
        
        # Store fuel before move
        fuel_before = unit.status.fuel
        
        # Perform the move
        unit = self.unit_remove(x, y)
        self.unit_place(unit, x2, y2)
        
        # Consume fuel based on actual path cost
        unit.status.fuel -= actual_fuel_cost
        
        # Set movement flags
        unit.can_move = False
        if unit.is_indirect():
            unit.can_attack = False
        
        # Update selection
        self.unit_deselect()
        self.unit_select(x2, y2)
        
        try:
            from enhanced_logging import log_movement
            log_movement(
                token=self.current_token,
                army=unit.army.name,
                unit_type=unit.type.name,
                from_x=x, from_y=y,
                to_x=x2, to_y=y2,
                fuel_used=distance,
                fuel_remaining=unit.status.fuel
            )
        except Exception as e:
            print(f"Logging error: {e}")  # Don't crash if logging fails
        
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
        """
        Enhanced attack system with proper counter-attack mechanics.
        
        Args:
            x, y: Attacker coordinates
            x2, y2: Defender coordinates
        
        Returns:
            The surviving unit (or None if both destroyed)
        """
        # Debug logging
        attacker = self.unit_at(x, y)
        print(f"DEBUG: Attack by {attacker.army.name}, token: {self.current_token}")
        
        # Validation
        if not self.coord_valid(x, y) or not self.coord_valid(x2, y2):
            raise Exception('coordinates out of range')
        
        attacker = self.unit_at(x, y)
        defender = self.unit_at(x2, y2)
        attacker_tile = self.tile_at(x, y)
        defender_tile = self.tile_at(x2, y2)
        
        if not attacker:
            raise Exception('no unit at source coordinates')
        if not defender:
            raise Exception('no unit at target coordinates')
        
        self.check_turn_and_raise(attacker)
        
        if not attacker.can_attack:
            raise Exception('unit cannot attack this turn')
        
        if not self.unit_can_attack(attacker, x2, y2):
            raise Exception('target out of range or cannot be attacked')
        
        if attacker.status.ammo <= 0:
            raise Exception('unit is out of ammunition')
        
        # Store unit info BEFORE combat (in case they get destroyed)
        attacker_army = attacker.army.name
        attacker_type = attacker.type.name
        defender_army = defender.army.name
        defender_type = defender.type.name
        
        # Store original HP for damage calculation
        defender_original_hp = defender.status.hp
        attacker_original_hp = attacker.status.hp
        
        # Calculate distances for counter-attack eligibility
        distance = abs(x2 - x) + abs(y2 - y)
        
        # Phase 1: Attacker attacks defender
        print(f"🎯 {attacker.type.name} attacks {defender.type.name}")
        
        damage_to_defender = attacker.attack_damage(defender, defender_tile)
        defender.status.hp -= damage_to_defender
        attacker.status.ammo -= 1
        
        print(f"   Defender takes {damage_to_defender} damage (HP: {defender.status.hp})")
        
        # Phase 2: Counter-attack (if conditions are met)
        damage_to_attacker = 0
        defender_destroyed = defender.status.hp <= 0
        
        if not defender_destroyed:
            can_counter_attack = (
                defender.status.ammo > 0 and         # Defender has ammo
                defender.is_attackable(attacker) and # Defender can damage attacker
                self._can_counter_attack(defender, attacker, distance) if hasattr(self, '_can_counter_attack') else True
            )
            
            if can_counter_attack:
                print(f"🔄 {defender.type.name} counter-attacks!")
                
                damage_to_attacker = defender.attack_damage(attacker, attacker_tile)
                attacker.status.hp -= damage_to_attacker
                defender.status.ammo -= 1
                
                print(f"   Attacker takes {damage_to_attacker} damage (HP: {attacker.status.hp})")
            else:
                print(f"   No counter-attack possible")
        else:
            print(f"   💀 {defender.type.name} destroyed!")
        
        # Determine final status
        attacker_destroyed = attacker.status.hp <= 0
        
        if attacker_destroyed:
            print(f"   💀 {attacker.type.name} destroyed!")
        
        # Prepare logging information
        damage_dealt = defender_original_hp - max(0, defender.status.hp)
        counter_damage = attacker_original_hp - max(0, attacker.status.hp)
        
        result_parts = []
        if defender_destroyed:
            result_parts.append("Defender DESTROYED")
        elif damage_dealt > 0:
            result_parts.append(f"Defender HP: {defender.status.hp}")
        
        if counter_damage > 0:
            result_parts.append(f"Counter: {counter_damage}")
        
        if attacker_destroyed:
            result_parts.append("Attacker DESTROYED")
        
        result_summary = ", ".join(result_parts) if result_parts else "No damage"
        
        # LOG THE COMBAT
        try:
            from enhanced_logging import log_attack, log_game_event
            log_attack(
                token=self.current_token,
                attacker_army=attacker_army,
                attacker_type=attacker_type,
                att_x=x, att_y=y,
                defender_army=defender_army,
                defender_type=defender_type,
                def_x=x2, def_y=y2,
                damage=damage_dealt,
                result=result_summary
            )
            
            # Log unit destruction as separate events
            if defender_destroyed:
                log_game_event(
                    token=self.current_token,
                    event_type="UNIT_DESTROYED",
                    army=defender_army,
                    details=f"{defender_type} destroyed at ({x2},{y2}) by {attacker_army} {attacker_type}"
                )
            
            if attacker_destroyed:
                log_game_event(
                    token=self.current_token,
                    event_type="UNIT_DESTROYED", 
                    army=attacker_army,
                    details=f"{attacker_type} destroyed at ({x},{y}) by counter-attack from {defender_army} {defender_type}"
                )
                
        except Exception as e:
            print(f"Combat logging error: {e}")
        
        # Remove destroyed units from the board
        if defender_destroyed:
            self.unit_remove(x2, y2)
        
        if attacker_destroyed:
            self.unit_remove(x, y)
        
        # Update attacker status if it survived
        if not attacker_destroyed:
            attacker.can_move = False
            attacker.can_attack = False
            attacker.can_capture = False
        
        # Deselect unit
        self.unit_deselect()
        
        # Return the surviving unit (or None if both destroyed)
        if not attacker_destroyed:
            return attacker
        elif not defender_destroyed:
            return defender
        else:
            return None  # Both destroyed
        
    def _can_counter_attack(self, defender, attacker, distance):
        """
        Determine if the defender can counter-attack based on unit types and range.
        
        Args:
            defender: The defending unit
            attacker: The attacking unit  
            distance: Distance between units
        
        Returns:
            bool: True if counter-attack is possible
        """
        # Direct units can always counter-attack other direct units at range 1
        if defender.is_direct() and attacker.is_direct() and distance == 1:
            return True
        
        # Indirect units cannot counter-attack direct units
        if defender.is_indirect() and attacker.is_direct():
            return False
        
        # Direct units cannot counter-attack indirect units
        if defender.is_direct() and attacker.is_indirect():
            return False
        
        # Indirect vs indirect - check if defender can reach attacker
        if defender.is_indirect() and attacker.is_indirect():
            return (defender.status.rangemin <= distance <= defender.status.rangemax)
        
        # Air units have special counter-attack rules
        if defender.is_air_unit():
            # Fighters can counter-attack other air units
            if attacker.is_air_unit() and defender.type in {UnitType.FIGHTER}:
                return True
            # Anti-air can counter-attack air units
            if attacker.is_air_unit() and defender.type in {UnitType.ANTIAIR}:
                return True
        
        return False

    def _get_no_counter_reason(self, defender, attacker, distance):
        """Get human-readable reason why counter-attack isn't possible"""
        if defender.status.ammo <= 0:
            return "no ammo"
        if not defender.is_attackable(attacker):
            return "cannot damage this unit type"
        if defender.is_indirect() and attacker.is_direct():
            return "indirect vs direct"
        if defender.is_direct() and attacker.is_indirect():
            return "direct vs indirect"
        if distance > defender.status.rangemax:
            return "out of range"
        if distance < defender.status.rangemin:
            return "too close"
        return "unknown"

    def damage_estimate(self, x: int, y: int, x2: int, y2: int) -> tuple:
        """
        Enhanced damage estimation for combat preview.
        
        Returns:
            tuple: (attacker_hp_after, defender_hp_after, can_counter)
        """
        attacker = self.unit_at(x, y)
        defender = self.unit_at(x2, y2)
        attacker_tile = self.tile_at(x, y)
        defender_tile = self.tile_at(x2, y2)
        
        if not attacker or not defender:
            raise Exception('units not found at coordinates')
        
        # Simulate attacker damage to defender
        damage_to_defender = attacker.attack_damage(defender, defender_tile)
        defender_hp_after = max(0, defender.status.hp - damage_to_defender)
        
        # Check if counter-attack is possible
        distance = abs(x2 - x) + abs(y2 - y)
        can_counter = (
            defender_hp_after > 0 and
            defender.status.ammo > 0 and
            defender.is_attackable(attacker) and
            self._can_counter_attack(defender, attacker, distance)
        )
        
        # Simulate counter-attack damage
        attacker_hp_after = attacker.status.hp
        if can_counter:
            damage_to_attacker = defender.attack_damage(attacker, attacker_tile)
            attacker_hp_after = max(0, attacker.status.hp - damage_to_attacker)
        
        return (attacker_hp_after, defender_hp_after, can_counter)
    
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

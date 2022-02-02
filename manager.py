'''[This is a manager for the RPC game engine for Advance war]'''


import math
from gameboard import GameBoard, GameTile
from unit import Army, UnitType, Unit, UnitClass
from dijkstra import dijkstra
from mapping import MapType, movement_cost, INF
from config import Config
import configparser
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


class GameManager():

    def __init__(self, config: Config, board: GameBoard):
        self.config = config
        self.board = board

    def coord_valid(self, x: int, y: int) -> bool:
        '''Returns true if the coordinate is
           within the board width and hight.'''
        return x in range(self.board.width) and y in range(self.board.width)

    def check_turn_and_raise(self, unit):
        '''Raises exception if its not the units turn.'''
        if unit.army != self.board.current_turn:
            raise Exception('is not the units turn')

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
        tile.unit = None
        return unit

    def unit_remove2(self, id: str) -> Unit:
        '''Remove the unit with the given ID.'''
        for tile in self.board.grid:
            if tile.unit and tile.unit.id == id:
                unit = tile.unit
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
        '''Capture the tile at the given coordinate.'''
        # if self.board.game_active == False:
        #     raise Exception("treid to capture but Game Over")
        if not self.coord_valid(x, y):
            raise Exception('coordinate out of range')
        tile = self.tile_get(x, y)
        if not tile.unit.can_attack:
            raise Exception('Unit cannot capture this turn')
        if not tile.unit:
            raise Exception('unit does not exist at coordinate')
        if not tile.mapTile.is_capturable:
            raise Exception('cannot capture tile')
        unit = tile.unit
        self.check_turn_and_raise(unit)
        if not unit.can_capture():
            raise Exception('Unit cannot capture')
        tile.capture_hp -= math.ceil(unit.status.hp / 10)
        if tile.capture_hp <= 0:
            tile.mapTile.army = unit.army
            tile.capture_hp = 20
            if tile.mapTile.type == MapType.BASE_TOWER_1:
                self.board.game_active = False
        unit.can_move = False
        unit.can_attack = False
        return self.tile_at(x, y)

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
        self.check_turn_and_raise(unit)
        unit.can_move = False
        unit.can_attack = False
        return self.tile_at(x, y)

    #
    # Public functions
    #

    def army_end_turn(self):
        '''Ends the armys turn.
           consumes fuel if nessessary and repairs/resupplys if on a
           corosponding repair tile.'''
        # if self.board.game_active == False:
        #     raise Exception("tried to end turn but Game Over")
        self.unit_deselect()
        # remove move/attack statuses from units
        self.board.total_blue_troops = 0
        self.board.total_red_troops = 0
        self.board.total_blue_properties = 0
        self.board.total_red_properties = 0
        for tile in self.board.grid:
            if tile.unit and tile.unit.army.value == 0:
                self.board.total_red_troops += 1
            if tile.unit and tile.unit.army.value == 1:
                self.board.total_blue_troops += 1
            if tile.mapTile.army and tile.mapTile.army.name == "BLUE":
                self.board.total_blue_properties += 1
                if self.board.current_turn.name == "RED":
                    self.board.blue_funds += int(config['FUNDS']['income'])
            if tile.mapTile.army and tile.mapTile.army.name == "RED":
                self.board.total_red_properties += 1
                if self.board.current_turn.name == "BLUE":
                    self.board.red_funds += int(config['FUNDS']['income'])
            if tile.unit and tile.unit.army == self.board.current_turn:
                tile.unit.can_move = False
                tile.unit.can_attack = False
        # change current_turn
        idx = None
        for i in range(len(self.board.turn_order)):
            if self.board.turn_order[i] == self.board.current_turn:
                idx = i
                break
        idx += 1
        if idx >= len(self.board.turn_order):
            idx = 0
        self.board.current_turn = self.board.turn_order[idx]
        # give move/attack statuses to units
        for tile in self.board.grid:
            if tile.unit and tile.unit.army == self.board.current_turn:
                tile.unit.can_move = True
                tile.unit.can_attack = True
                unit = tile.unit
                unit.status.fuel -= unit.fuel_use()
                if unit.fuel_daily_use() and unit.status.fuel <= 0:
                    tile = self.tile_from_unit(unit)
                    self.unit_remove(tile.x, tile.y)
                if (unit.army == tile.mapTile.army and unit.status.cls
                        in REPAIR_CLASSES[tile.mapTile.type]):
                    unit.status.hp = min(100, unit.status.hp + 20)
                    self.resupply_unit(unit)
                # Refuel units adjacent APC
                if unit.type in {UnitType.APC}:
                    b = tile.x + 1
                    if self.coord_valid(b, tile.y):
                        target = self.tile_get(b, tile.y)
                        if target.unit:
                            unit = target.unit
                            self.resupply_unit(unit)
                    b = tile.x - 1
                    if self.coord_valid(b, tile.y):
                        target = self.tile_get(b, tile.y)
                        if target.unit:
                            unit = target.unit
                            self.resupply_unit(unit)
                    c = tile.y + 1
                    if self.coord_valid(tile.x, c):
                        target = self.tile_get(tile.x, c)
                        if target.unit:
                            unit = target.unit
                            self.resupply_unit(unit)
                    c = tile.y - 1
                    if self.coord_valid(tile.x, c):
                        target = self.tile_get(tile.x, c)
                        if target.unit:
                            unit = target.unit
                            self.resupply_unit(unit)

            if not tile.unit and tile.mapTile.is_capturable:
                tile.capture_hp = 20
        if self.board.current_turn.name == "RED":
            self.board.days += 1

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
        '''Move the unit to / from the coordinates given.'''
        if not self.coord_valid(x, y):
            raise Exception('coordinate out of range')
        if not self.coord_valid(x2, y2):
            raise Exception('coordinate out of range')
        unit = self.unit_at(x, y)
        if not unit:
            raise Exception('unit does not exist at source tile')
        self.check_turn_and_raise(unit)
        if not unit.can_move:
            raise Exception('unit can not move')
        if self.unit_at(x2, y2):
            raise Exception('unit already exists at target tile')
        if not self.unit_can_move_to(unit, x2, y2):
            raise Exception('target tile too far')
        unit = self.unit_remove(x, y)
        self.unit_place(unit, x2, y2)
        unit.can_move = False
        if unit.is_indirect():
            unit.can_attack = False
        tile = self.tile_from_unit(unit)
        dist = abs(x - tile.x) + abs(y - tile.y)
        unit.status.fuel -= dist
        self.unit_deselect()
        self.unit_select(x2, y2)
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
            else:
                raise Exception('not enough funds for this unit')
        if self.board.current_turn.name == 'BLUE':
            wallet = self.board.blue_funds
            if int(config[unit.type.name]['cost']) <= wallet:
                self.board.blue_funds -= int(config[unit.type.name]['cost'])
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
        if movement_cost[target_tile.mapTile.type][unit.status.cls.value] == INF:
            raise Exception('unit cannot unload to tile')
        unit = transport.status.cargo.pop(index)
        self.unit_place(unit, x2, y2)
        self.can_move = False
        self.can_attack = False
        transport.can_move = False
        transport.can_attack = False
        return unit

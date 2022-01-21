import random
import math

from dataclasses import dataclass
from enum import Enum
import uuid
from mapping import terrain_star
from army import Army
from typing import List


class UnitType(Enum):
    ANTIAIR = 0
    APC = 1
    ARTILLERY = 2
    BCOPTER = 3
    BATTLESHIP = 4
    BLACKBOAT = 5
    BLACKBOMB = 6
    BOMBER = 7
    CARRIER = 8
    CRUISER = 9
    FIGHTER = 10
    INFANTRY = 11
    LANDER = 12
    MEDIUMTANK = 13
    MECH = 14
    MEGATANK = 15
    MISSILE = 16
    NEOTANK = 17
    PIPERUNNER = 18
    RECON = 19
    ROCKET = 20
    STEALTH = 21
    SUB = 22
    TCOPTER = 23
    TANK = 24

''' damage table for the primary weapon.'''
DAMAGE_TABLE = {
    UnitType.ANTIAIR:    ([45,  50,  50,  120,  0,  0,  120,  75,  0,  0,  65,
                           105, 0,  10,  105, 1, 55, 5, 25, 60, 55, 75, 0, 120,
                           25]),
    UnitType.APC:        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0]),
    UnitType.ARTILLERY:   ([75, 70, 75, 0, 40, 55, 0, 0, 45, 65, 0, 90, 55, 45,
                           85, 15, 80, 40, 70, 80, 80, 0, 60, 0, 70]),
    UnitType.BCOPTER:    ([25, 60, 65, 65, 25, 25, 0, 0, 25, 55, 0, 75, 25,
                           25, 75, 10, 65, 20, 55, 55, 65, 0, 25, 95, 55]),
    UnitType.BATTLESHIP: ([85, 80, 80, 0, 50, 95, 0, 0, 60, 95, 0, 95, 95,
                           55, 90, 25, 90, 50, 80, 90, 85, 0, 95, 0, 80]),
    UnitType.BLACKBOAT:  ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0]),
    UnitType.BLACKBOMB:  ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0]),
    UnitType.BOMBER:     ([95, 105, 105, 0, 75, 95, 0, 0, 75, 85, 0, 110,
                           95, 95, 110, 35, 105, 90, 105, 105, 105, 0, 95,
                           0, 105, ]),
    UnitType.CARRIER:    ([0, 0, 0, 115, 0, 0, 120, 100, 0, 0, 100,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 115, 0]),
    UnitType.CRUISER:    ([0, 0, 0, 115, 0, 25, 120, 65, 5, 0, 55, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 100, 90, 115, 0]),
    UnitType.FIGHTER:    ([0, 0, 0, 100, 0, 0, 120, 100, 0, 0, 55,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 85, 0, 100, 0]),
    UnitType.INFANTRY:   ([5, 14, 15, 7, 0, 0, 0, 0, 0, 0,
                           0, 55, 0, 1, 45, 1, 26, 1, 5, 12, 25, 0, 0, 30, 5]),
    UnitType.LANDER:     ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0]),
    UnitType.MEDIUMTANK: ([105, 105, 105, 12, 10, 35, 0, 0, 10, 45, 0, 105, 35,
                           55, 95, 25, 105, 45, 85, 105, 105, 0, 10, 45, 85]),
    UnitType.MECH:       ([65, 75, 70, 9, 0, 0, 0, 0, 0, 0, 0, 65, 0, 15, 55,
                           5, 85, 15, 55, 85, 85, 0, 0, 35, 55]),
    UnitType.MEGATANK:   ([195, 195, 195, 22, 45, 105, 0, 0, 45, 65, 0, 135,
                           75, 125, 125, 65, 195, 115, 180, 195, 195, 0, 45,
                           55, 180]),
    UnitType.MISSILE:    ([0, 0, 0, 120, 0, 0, 120, 100, 0, 0, 100, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 100, 0, 120, 0]),
    UnitType.NEOTANK:    ([115, 125, 115, 22, 15, 40, 0, 0, 15, 50, 0, 125,
                           50, 75, 115, 35, 125, 55, 105, 125, 125, 0, 15,
                           55, 105]),
    UnitType.PIPERUNNER: ([85, 80, 80, 105, 55, 60, 120, 75, 60, 85, 65, 95, 60,
                           55, 90, 25, 90, 50, 80, 90, 85, 75, 85, 105, 80]),
    UnitType.RECON:      ([4, 45, 45, 12, 0, 0, 0, 0, 0, 0, 0, 70, 0, 1, 65, 1,
                           28, 1, 6, 35, 55, 0, 0, 35, 6]),
    UnitType.ROCKET:    ([85, 80, 80, 0, 55, 60, 0, 0, 60, 85, 0, 95, 60, 55,
                           90, 25, 90, 50, 80, 90, 85, 0, 85, 0, 80]),
    UnitType.STEALTH:    ([50, 85, 75, 85, 45, 65, 120, 70, 45, 35, 45, 90, 65,
                           70, 90, 15, 85, 60, 80, 85, 85, 55, 55, 95, 75]),
    UnitType.SUB:        ([0, 0, 0, 0, 55, 95, 0, 0, 75, 25, 0, 0, 95, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 55, 0, 0]),
    UnitType.TCOPTER:    ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    UnitType.TANK:       ([65, 75, 70, 10, 1, 10, 0, 0, 1, 5, 0, 75, 10,
                           15, 70, 10, 85, 15, 55, 85, 85, 0, 1, 40, 55]),
}


class UnitClass(Enum):
    BOOTS = 0
    TREADS = 1
    TYRES = 2
    SEA = 3
    AIR = 4
    LANDER = 5
    FOOT = 6
    PIPE = 7


@dataclass
class UnitConfig:
    '''Attributes of a unit.'''
    cls: UnitClass
    cost: int
    move: int
    rangemin: int
    rangemax: int
    fuel: int
    vision: int
    hp: int
    ammo: int
    cargo: List['Unit']


@dataclass
class Unit:
    '''Type and status of a unit.'''
    army: Army
    type: UnitType
    status: UnitConfig
    id: str
    can_move: bool
    can_attack: bool

    def attack_damage(self, target, tile):
        '''Returns the attack damamge from the attacker to the defender
            taking into account the terrain.'''
        damage_const = DAMAGE_TABLE[self.type][target.type.value]
        def_const = terrain_star[tile.mapTile.type]
        atk_hp = math.ceil(self.status.hp / 10)
        # The displayed HP of the defender, from 1 through 10.
        def_hp = math.ceil(target.status.hp / 10)
        attack_term = damage_const + random.randrange(10)
        hp_term = atk_hp / 10
        defense_term = (100 - def_const * def_hp) / 100
        result = attack_term * hp_term * defense_term
        return int(result)

    def is_indirect(self):
        '''Returns true if the unit is an indirect unit.'''
        return self.type in ({UnitType.ARTILLERY, UnitType.BATTLESHIP,
                              UnitType.MISSILE, UnitType.ROCKET,
                              UnitType.CARRIER, UnitType.PIPERUNNER})

    def is_direct(self):
        '''Returns true if the unit is an direct unit.'''
        return self.type in ({UnitType.INFANTRY, UnitType.MECH, UnitType.TANK,
                              UnitType.MEGATANK, UnitType.NEOTANK,
                              UnitType.MEDIUMTANK, UnitType.BCOPTER,
                              UnitType.CRUISER, UnitType.FIGHTER,
                              UnitType.RECON, UnitType.SUB},
                              UnitType.ANTIAIR)

    def is_attackable(self, defender):
        '''Returns true if the unit is able to attack this type of unit.'''
        return bool(DAMAGE_TABLE[self.type][defender.type.value])

    def is_sea_unit(self):
        '''Returns true if the unit is a sea unit.'''
        return self.type in ({UnitType.LANDER, UnitType.BLACKBOAT,
                              UnitType.CARRIER, UnitType.BATTLESHIP,
                              UnitType.CRUISER})

    def is_stealth_sea(self):
        '''Returns true if the unit is an stealth sea unit.'''
        return self.type in {UnitType.SUB}

    def is_copter_unit(self):
        '''Returns true if the unit is a copter unit.'''
        return self.type in {UnitType.TCOPTER, UnitType.BCOPTER}

    def is_air_unit(self):
        '''Returns true if the unit is an air unit.'''
        return self.type in ({UnitType.FIGHTER, UnitType.BOMBER,
                              UnitType.BLACKBOMB})
    def is_land_unit(self):
        '''Returns true if the unit is an air unit.'''
        return self.type in ({UnitType.INFANTRY, UnitType.MECH, UnitType.TANK,
                              UnitType.MEGATANK, UnitType.NEOTANK,
                              UnitType.MEDIUMTANK, UnitType.RECON,
                              UnitType.ARTILLERY, UnitType.MISSILE,
                              UnitType.ROCKET, UnitType.PIPERUNNER})

    def can_capture(self):
        '''Returns true if the unit can capture.'''
        return self.type in {UnitType.INFANTRY, UnitType.MECH}

    def is_stealth_air(self):
        '''Returns true if the unit is an stealth air unit.'''
        return self.type in {UnitType.STEALTH}

    def fuel_daily_use(self):
        '''Returns true if the unit consumes fuel every day.'''
        return self.type in ({UnitType.STEALTH, UnitType.FIGHTER,
                              UnitType.BOMBER, UnitType.BLACKBOMB,
                              UnitType.TCOPTER, UnitType.BCOPTER, UnitType.SUB,
                              UnitType.LANDER, UnitType.BLACKBOAT,
                              UnitType.CARRIER, UnitType.BATTLESHIP,
                              UnitType.CRUISER})

    def fuel_use(self):
        '''Returns the daily fuel use for the unit type.'''
        fuel = 0
        if self.is_sea_unit():
            fuel = 1
        if self.is_copter_unit():
            fuel = 2
        if self.is_air_unit():
            fuel = 5
        if self.is_stealth_air():
            fuel = 8
        return fuel

    def capacity(self):
        '''Return the carrying capacity of the unit, (0, 1, or 2).'''
        if self.type in {UnitType.TCOPTER, UnitType.APC}:
            return 1
        if self.type in {UnitType.LANDER, UnitType.CARRIER, UnitType.CRUISER, UnitType.BLACKBOAT}:
            return 2
        return 0

    def can_carry(self, unit):
         '''Returns true if the transport unit can carry the unit.'''
         if self.type in {UnitType.TCOPTER, UnitType.APC, UnitType.BLACKBOAT}:
             if unit.type in {UnitType.INFANTRY, UnitType.MECH}:
                 return True
         if self.type in {UnitType.LANDER}:
             if unit.type in {UnitType.INFANTRY, UnitType.MECH, UnitType.APC, UnitType.TANK, UnitType.MEDIUMTANK, UnitType.NEOTANK, UnitType.ANTIAIR, UnitType.RECON, UnitType.ARTILLERY, UnitType.MISSILE, UnitType.ROCKET}:
                 return True
         if self.type in {UnitType.CRUISER}:
             if unit.type in {UnitType.BCOPTER, UnitType.TCOPTER}:
                 return True
         if self.type in {UnitType.CARRIER}:
             if unit.type in {UnitType.FIGHTER, UnitType.BOMBER, UnitType.BLACKBOMB, UnitType.BCOPTER, UnitType.TCOPTER}:
                 return True

    def can_resupply(self):
         '''Returns true if the unit can resuppy.'''
         if self.type in {UnitType.APC, UnitType.BLACKBOAT}:
             return True

    @classmethod
    def create(cls, army: Army, unit_type: UnitType, unit_config: UnitConfig):
        '''Creates the unit.'''
        return Unit(army, unit_type, unit_config,
                    uuid.uuid4(), False, False)

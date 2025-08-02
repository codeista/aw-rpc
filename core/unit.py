import random
import math

from dataclasses import dataclass, field
from enum import Enum
import uuid
from core.map_system import TERRAIN_DEFENSE_STARS
from core.map_system import Army
from typing import List, Optional


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


# Primary weapon damage table (authentic AWBW values)
DAMAGE_TABLE = {
    UnitType.ANTIAIR: ([45, 50, 50, 120, 0, 0, 120, 75, 0, 0, 65, 105, 0, 10, 105, 1, 55, 5, 25, 60, 55, 75, 0, 120, 25]),
    UnitType.APC: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    UnitType.ARTILLERY: ([75, 70, 75, 0, 40, 55, 0, 0, 45, 65, 0, 90, 55, 45, 85, 15, 80, 40, 70, 80, 80, 0, 60, 0, 70]),
    UnitType.BCOPTER: ([25, 60, 65, 0, 25, 25, 0, 0, 25, 55, 0, 0, 25, 25, 0, 10, 65, 20, 55, 55, 65, 0, 25, 0, 55]),
    UnitType.BATTLESHIP: ([85, 80, 80, 0, 50, 95, 0, 0, 60, 95, 0, 95, 95, 55, 90, 25, 90, 50, 80, 90, 85, 0, 95, 0, 80]),
    UnitType.BLACKBOAT: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    UnitType.BLACKBOMB: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    UnitType.BOMBER: ([95, 105, 105, 0, 75, 95, 0, 0, 75, 85, 0, 110, 95, 95, 110, 35, 105, 90, 105, 105, 105, 0, 95, 0, 105]),
    UnitType.CARRIER: ([0, 0, 0, 115, 0, 0, 120, 100, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 115, 0]),
    UnitType.CRUISER: ([0, 0, 0, 0, 0, 25, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 90, 0, 0]),
    UnitType.FIGHTER: ([0, 0, 0, 100, 0, 0, 120, 100, 0, 0, 55, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 85, 0, 100, 0]),
    UnitType.INFANTRY: ([5, 12, 15, 7, 0, 0, 0, 0, 0, 0, 0, 55, 0, 1, 45, 1, 25, 1, 5, 12, 25, 0, 0, 30, 5]),
    UnitType.LANDER: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    UnitType.MEDIUMTANK: ([105, 105, 105, 0, 10, 35, 0, 0, 10, 45, 0, 0, 35, 55, 0, 25, 105, 45, 85, 105, 105, 0, 10, 0, 85]),
    UnitType.MECH: ([65, 75, 70, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 15, 0, 5, 85, 15, 55, 85, 85, 0, 0, 0, 55]),
    UnitType.MEGATANK: ([195, 195, 195, 0, 45, 105, 0, 0, 45, 65, 0, 0, 75, 125, 0, 65, 195, 115, 180, 195, 195, 0, 45, 0, 180]),
    UnitType.MISSILE: ([0, 0, 0, 120, 0, 0, 120, 100, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 120, 0]),
    UnitType.NEOTANK: ([115, 125, 115, 0, 15, 40, 0, 0, 15, 50, 0, 0, 40, 75, 0, 35, 125, 55, 105, 125, 125, 0, 15, 0, 105]),
    UnitType.PIPERUNNER: ([85, 80, 80, 105, 55, 60, 120, 75, 60, 60, 65, 95, 60, 55, 90, 25, 90, 50, 80, 90, 85, 75, 85, 105, 80]),
    UnitType.RECON: ([4, 45, 45, 10, 0, 0, 0, 0, 0, 0, 0, 70, 0, 1, 65, 1, 28, 1, 6, 35, 55, 0, 0, 35, 6]),
    UnitType.ROCKET: ([85, 80, 80, 0, 55, 60, 0, 0, 60, 85, 0, 95, 60, 55, 90, 25, 90, 50, 80, 90, 85, 0, 85, 0, 80]),
    UnitType.STEALTH: ([50, 85, 75, 85, 45, 65, 120, 70, 45, 35, 45, 90, 65, 70, 90, 15, 85, 60, 80, 85, 85, 55, 55, 95, 75]),
    UnitType.SUB: ([0, 0, 0, 0, 55, 95, 0, 0, 75, 25, 0, 0, 95, 0, 0, 0, 0, 0, 0, 0, 0, 0, 55, 0, 0]),
    UnitType.TCOPTER: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    UnitType.TANK: ([65, 75, 70, 0, 1, 10, 0, 0, 1, 5, 0, 0, 10, 15, 0, 10, 85, 15, 55, 85, 85, 0, 1, 0, 55]),
}

# Secondary weapon damage table (for when out of primary ammo or specific targets)
# Used for machine guns, defensive weapons, etc.
# Unit attack values (authentic AW values)
UNIT_ATTACK_VALUES = {
    UnitType.INFANTRY: 100, UnitType.MECH: 100, UnitType.RECON: 100,
    UnitType.TANK: 100, UnitType.MEDIUMTANK: 100, UnitType.NEOTANK: 100, UnitType.MEGATANK: 100,
    UnitType.ANTIAIR: 100, UnitType.ARTILLERY: 100, UnitType.ROCKET: 100, UnitType.MISSILE: 100,
    UnitType.BCOPTER: 100, UnitType.TCOPTER: 100, UnitType.FIGHTER: 100, UnitType.BOMBER: 100,
    UnitType.STEALTH: 100, UnitType.BATTLESHIP: 100, UnitType.CRUISER: 100, UnitType.SUB: 100,
    UnitType.LANDER: 100, UnitType.CARRIER: 100, UnitType.BLACKBOAT: 100, UnitType.BLACKBOMB: 100,
    UnitType.APC: 100, UnitType.PIPERUNNER: 100
}

# Unit defense values (authentic AW values)  
UNIT_DEFENSE_VALUES = {
    UnitType.INFANTRY: 100, UnitType.MECH: 100, UnitType.RECON: 100,
    UnitType.TANK: 100, UnitType.MEDIUMTANK: 100, UnitType.NEOTANK: 100, UnitType.MEGATANK: 100,
    UnitType.ANTIAIR: 100, UnitType.ARTILLERY: 100, UnitType.ROCKET: 100, UnitType.MISSILE: 100,
    UnitType.BCOPTER: 100, UnitType.TCOPTER: 100, UnitType.FIGHTER: 100, UnitType.BOMBER: 100,
    UnitType.STEALTH: 100, UnitType.BATTLESHIP: 100, UnitType.CRUISER: 100, UnitType.SUB: 100,
    UnitType.LANDER: 100, UnitType.CARRIER: 100, UnitType.BLACKBOAT: 100, UnitType.BLACKBOMB: 100,
    UnitType.APC: 100, UnitType.PIPERUNNER: 100
}

SECONDARY_DAMAGE_TABLE = {
    UnitType.ANTIAIR: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # No secondary
    UnitType.APC: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # No weapons
    UnitType.ARTILLERY: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # No secondary
    UnitType.BCOPTER: ([6, 20, 25, 65, 0, 0, 0, 0, 0, 0, 0, 75, 0, 1, 75, 1, 35, 1, 6, 30, 35, 0, 0, 95, 6]),  # Machine gun
    UnitType.BATTLESHIP: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # No secondary
    UnitType.BLACKBOAT: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # No weapons
    UnitType.BLACKBOMB: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # No weapons
    UnitType.BOMBER: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # No secondary
    UnitType.CARRIER: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # Uses fighters
    UnitType.CRUISER: ([0, 0, 0, 115, 0, 0, 120, 65, 0, 0, 55, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 115, 0]),  # Anti-air
    UnitType.FIGHTER: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # No secondary
    UnitType.INFANTRY: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # Only one weapon
    UnitType.LANDER: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # No weapons
    UnitType.MEDIUMTANK: ([7, 45, 45, 12, 0, 0, 0, 0, 0, 0, 0, 105, 0, 1, 95, 1, 35, 1, 8, 45, 45, 0, 0, 45, 8]),  # Machine gun
    UnitType.MECH: ([6, 20, 32, 9, 0, 0, 0, 0, 0, 0, 0, 65, 0, 1, 55, 1, 35, 1, 6, 18, 35, 0, 0, 35, 6]),  # Machine gun
    UnitType.MEGATANK: ([17, 65, 65, 22, 0, 0, 0, 0, 0, 0, 0, 135, 0, 1, 125, 1, 55, 1, 10, 65, 75, 0, 0, 55, 10]),  # Machine gun
    UnitType.MISSILE: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # No secondary
    UnitType.NEOTANK: ([17, 65, 65, 22, 0, 0, 0, 0, 0, 0, 0, 125, 0, 1, 115, 1, 55, 1, 10, 65, 75, 0, 0, 55, 10]),  # Machine gun
    UnitType.PIPERUNNER: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # No secondary
    UnitType.RECON: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # No secondary in authentic table
    UnitType.ROCKET: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # No secondary
    UnitType.STEALTH: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # No secondary
    UnitType.SUB: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # Only torpedoes
    UnitType.TCOPTER: ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # No weapons
    UnitType.TANK: ([5, 54, 45, 10, 0, 0, 0, 0, 0, 0, 0, 75, 0, 1, 70, 1, 30, 1, 6, 40, 55, 0, 0, 40, 6]),  # Machine gun
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
    '''Static attributes of a unit type - these don't change during gameplay.'''
    cls: UnitClass
    cost: int
    move: int
    rangemin: int
    rangemax: int
    max_fuel: int  # Maximum fuel capacity
    vision: int
    max_hp: int    # Maximum HP (always 100 in Advance Wars)
    max_ammo: int  # Maximum ammo capacity
    
    # For backward compatibility during migration
    @property
    def fuel(self):
        return self.max_fuel
    
    @property
    def hp(self):
        return self.max_hp
        
    @property
    def ammo(self):
        return self.max_ammo


@dataclass
class UnitStatus:
    '''Dynamic status of a unit - these change during gameplay.'''
    hp: int
    fuel: int
    ammo: int
    cargo: List['Unit'] = field(default_factory=list)
    has_moved_this_turn: bool = False
    
    # Copy all the static attributes from config for easy access
    cls: UnitClass = None
    cost: int = 0
    move: int = 0
    rangemin: int = 0
    rangemax: int = 0
    vision: int = 0
    
    @classmethod
    def from_config(cls, config: UnitConfig) -> 'UnitStatus':
        '''Create a new UnitStatus from a UnitConfig with full HP/fuel/ammo.'''
        return cls(
            hp=config.max_hp,
            fuel=config.max_fuel,
            ammo=config.max_ammo,
            cargo=[],
            has_moved_this_turn=False,
            # Copy static attributes
            cls=config.cls,
            cost=config.cost,
            move=config.move,
            rangemin=config.rangemin,
            rangemax=config.rangemax,
            vision=config.vision
        )


@dataclass
class Unit:
    '''Type and status of a unit.'''
    army: Army  # DEPRECATED: Use player_id instead
    type: UnitType
    status: UnitStatus  # Now uses UnitStatus instead of UnitConfig
    config: UnitConfig  # Keep reference to static config
    id: str
    can_move: bool
    can_attack: bool
    can_capture: bool
    player_id: Optional[int] = None  # Player who owns this unit

    def attack_damage(self, target, tile):
        '''Returns the attack damage using authentic Advance Wars formula.
        Formula: Damage% = ((B * AV/100 + L - LB) * HPA/10) * ((200 - (DV + DTR * HPD))/100)'''
        
        # B: Base damage from weapon selection
        base_damage = self._select_weapon_damage(target)
        if base_damage == 0:
            return 0
        
        # AV: Attacker's attack value (default 100, modified by COs)
        attack_value = UNIT_ATTACK_VALUES.get(self.type, 100)
        
        # L: Luck damage (0-9 random bonus)
        luck = random.randint(0, 9)
        
        # LB: Bad luck damage (0 for now, could be implemented for some COs)
        bad_luck = 0
        
        # HPA: Attacker's visual HP (1-10)
        attacker_visual_hp = math.ceil(self.status.hp / 10)
        
        # DV: Defender's defense value (default 100, modified by COs)
        defense_value = UNIT_DEFENSE_VALUES.get(target.type, 100)
        
        # DTR: Defending terrain defense stars
        terrain_defense = TERRAIN_DEFENSE_STARS[tile.mapTile.type]
        
        # HPD: Defender's visual HP (1-10)
        defender_visual_hp = math.ceil(target.status.hp / 10)
        
        # Apply authentic AW damage formula
        attack_factor = (base_damage * attack_value / 100 + luck - bad_luck) * attacker_visual_hp / 10
        defense_factor = (200 - (defense_value + terrain_defense * defender_visual_hp)) / 100
        
        damage = attack_factor * defense_factor
        return max(0, int(damage))
    
    def _select_weapon_damage(self, target):
        '''Selects appropriate weapon damage based on authentic AW mechanics.
        
        Rules:
        1. Units with secondary weapons use them against specific targets (infantry/mechs/copters)
        2. Primary weapon used when: has ammo AND (no secondary OR secondary can't target OR primary preferred)
        3. Secondary weapon used when: out of primary ammo OR secondary is specialized for target
        4. Infantry/Mech have infinite ammo (no ammo limitation)
        '''
        
        primary_damage = DAMAGE_TABLE[self.type][target.type.value]
        secondary_damage = 0
        
        # Check if unit has secondary weapon capability
        if self.type in SECONDARY_DAMAGE_TABLE:
            secondary_damage = SECONDARY_DAMAGE_TABLE[self.type][target.type.value]
        
        # Infantry always uses primary (infinite ammo)
        if self.type == UnitType.INFANTRY:
            return primary_damage
        
        # Check primary weapon ammo
        has_primary_ammo = getattr(self.status, 'ammo', 0) > 0
        
        # Use secondary weapon when primary can't target (authentic AW behavior)
        if secondary_damage > 0 and primary_damage == 0:
            # Primary weapon cannot target this unit type - must use secondary
            return secondary_damage
        
        # Use primary weapon if we have ammo and it can damage the target
        if has_primary_ammo and primary_damage > 0:
            return primary_damage
        
        # Fall back to secondary weapon if available (out of primary ammo)
        if secondary_damage > 0:
            return secondary_damage
        
        # No weapon can damage this target
        return 0
    
    def _uses_secondary_weapon(self, target):
        '''Returns True if this attack will use secondary weapon (for ammo consumption logic).'''
        
        # Infantry always uses primary (infinite ammo)
        if self.type == UnitType.INFANTRY:
            return False
        
        # Check if we have secondary weapon
        if self.type not in SECONDARY_DAMAGE_TABLE:
            return False
        
        secondary_damage = SECONDARY_DAMAGE_TABLE[self.type][target.type.value]
        if secondary_damage == 0:
            return False
        
        # Check if secondary weapon will be used
        primary_damage = DAMAGE_TABLE[self.type][target.type.value]
        
        # Use secondary when primary can't target this unit type
        if secondary_damage > 0 and primary_damage == 0:
            return True
        
        # Use secondary when out of primary ammo
        has_primary_ammo = getattr(self.status, 'ammo', 0) > 0
        primary_damage = DAMAGE_TABLE[self.type][target.type.value]
        
        return not has_primary_ammo and primary_damage > 0

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
                              UnitType.RECON, UnitType.SUB,
                              UnitType.ANTIAIR, UnitType.BOMBER})

    def is_attackable(self, defender):
        '''Returns true if the unit is able to attack this type of unit.'''
        try:
            # Check if unit can damage with either primary or secondary weapon
            return self._select_weapon_damage(defender) > 0
        except (KeyError, IndexError) as e:
            # Some unit types might not be in damage table
            return False

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
                              UnitType.BLACKBOMB,})

    def is_land_unit(self):
        '''Returns true if the unit is an land unit.'''
        return self.type in ({UnitType.INFANTRY, UnitType.MECH, UnitType.TANK,
                              UnitType.MEGATANK, UnitType.NEOTANK,
                              UnitType.MEDIUMTANK, UnitType.RECON,
                              UnitType.ARTILLERY, UnitType.MISSILE,
                              UnitType.ROCKET, UnitType.PIPERUNNER})

    def type_can_capture(self):
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
        elif self.is_copter_unit():
            fuel = 2
        elif self.is_air_unit():
            fuel = 5
        elif self.is_stealth_air():
            fuel = 8
        else:
            fuel = 0
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
            if unit.type in {UnitType.INFANTRY, UnitType.MECH, UnitType.APC,
                             UnitType.TANK, UnitType.MEDIUMTANK, UnitType.NEOTANK,
                             UnitType.ANTIAIR, UnitType.RECON, UnitType.ARTILLERY,
                             UnitType.MISSILE, UnitType.ROCKET}:
                return True
        if self.type in {UnitType.CRUISER}:
            if unit.type in {UnitType.BCOPTER, UnitType.TCOPTER}:
                return True
        if self.type in {UnitType.CARRIER}:
            if unit.type in {UnitType.FIGHTER, UnitType.BOMBER,
                             UnitType.BLACKBOMB, UnitType.BCOPTER,
                             UnitType.TCOPTER}:
                return True

    def can_resupply(self):
        '''Returns true if the unit can resuppy.'''
        if self.type in {UnitType.APC, UnitType.BLACKBOAT}:
            return True
        
    def enhanced_attack_damage(self, target, tile, luck_enabled=True, board_manager=None):
        """Enhanced attack damage using authentic Advance Wars formula
        
        Args:
            target: The defending unit
            tile: The tile the defender is on
            luck_enabled: Whether to include random luck factor
            board_manager: Optional GameManager reference for COM_TOWER bonus calculation
        """
        
        # B: Base damage from weapon selection
        base_damage = self._select_weapon_damage(target)
        if base_damage == 0:
            return 0
        
        # AV: Attacker's attack value (default 100, modified by COs and COM_TOWERs)
        base_av = UNIT_ATTACK_VALUES.get(self.type, 100)
        
        # Apply all modifiers through board_manager
        if board_manager:
            attack_value = board_manager.get_modified_attack_value(self, base_av)
        else:
            attack_value = base_av
        
        # L: Luck damage (0-9 random bonus)
        luck = random.randint(0, 9) if luck_enabled else 0
        
        # LB: Bad luck damage (0 for now)
        bad_luck = 0
        
        # HPA: Attacker's visual HP (1-10)
        attacker_visual_hp = math.ceil(self.status.hp / 10)
        
        # DV: Defender's defense value (default 100, modified by COs)
        base_dv = UNIT_DEFENSE_VALUES.get(target.type, 100)
        
        # Apply defense modifiers if board_manager available
        if board_manager:
            defense_value = board_manager.get_modified_defense_value(target, base_dv)
        else:
            defense_value = base_dv
        
        # DTR: Defending terrain defense stars
        terrain_defense = TERRAIN_DEFENSE_STARS.get(tile.mapTile.type, 0)
        
        # HPD: Defender's visual HP (1-10)
        defender_visual_hp = math.ceil(target.status.hp / 10)
        
        # Apply authentic AW damage formula
        # Damage% = ((B * AV/100 + L - LB) * HPA/10) * ((200 - (DV + DTR * HPD))/100)
        attack_factor = (base_damage * attack_value / 100 + luck - bad_luck) * attacker_visual_hp / 10
        defense_factor = (200 - (defense_value + terrain_defense * defender_visual_hp)) / 100
        
        damage = attack_factor * defense_factor
        return max(0, int(damage))

    @classmethod
    def create(cls, army: Army, unit_type: UnitType, unit_config: UnitConfig):
        '''Creates the unit with proper separation of config and status.'''
        # Create a new status from the config
        unit_status = UnitStatus.from_config(unit_config)
        unit = Unit(
            army=army,
            type=unit_type,
            status=unit_status,
            config=unit_config,  # Keep reference to static config
            id=uuid.uuid4(),
            can_move=False,
            can_attack=False,
            can_capture=False  # Newly created units cannot capture until they move
        )
        
        return unit
    
    @classmethod
    def create_with_player(cls, player_id: int, unit_type: UnitType, unit_config: UnitConfig, sprite_color: str = None):
        '''Creates a unit for the new player system.'''
        # Map player to army for backward compatibility
        # This will be removed once full migration is complete
        army_map = {0: Army.RED, 1: Army.BLUE, 2: Army.GREEN, 3: Army.YELLOW, 4: Army.GREY}
        army = army_map.get(player_id, Army.GREY)
        
        unit = cls.create(army, unit_type, unit_config)
        unit.player_id = player_id
        return unit

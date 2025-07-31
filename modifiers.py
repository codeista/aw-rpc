"""
Game Modifier System for Advance Wars RPC

This module provides a flexible modifier system for game mechanics including:
- COM_TOWER bonuses
- Commanding Officer (CO) abilities
- CO Powers
- Weather effects (future)
- Terrain bonuses (future)
"""

from typing import TYPE_CHECKING, Tuple, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    from unit import Unit
    from gameboard import GameTile
    from map_system import MapType


class ModifierType(Enum):
    """Types of modifiers in the game"""
    COM_TOWER = "COM_TOWER"
    COMMANDING_OFFICER = "COMMANDING_OFFICER"
    CO_POWER = "CO_POWER"
    WEATHER = "WEATHER"
    TERRAIN = "TERRAIN"


class GameModifier(ABC):
    """
    Base class for all game modifiers (COs, COM_TOWERs, weather, etc.)
    
    Modifiers can affect:
    - Attack power
    - Defense power
    - Movement range
    - Attack range
    - Luck/Bad luck
    - Special abilities
    """
    
    modifier_type: ModifierType
    priority: int = 0  # Higher priority modifiers apply last
    
    def modify_attack_value(self, unit: 'Unit', base_av: float) -> float:
        """Modify unit's attack value. Default: no change"""
        return base_av
    
    def modify_defense_value(self, unit: 'Unit', base_dv: float) -> float:
        """Modify unit's defense value. Default: no change"""
        return base_dv
    
    def modify_movement(self, unit: 'Unit', base_move: int) -> int:
        """Modify unit's movement range. Default: no change"""
        return base_move
    
    def modify_luck(self, unit: 'Unit') -> Tuple[int, int]:
        """Modify luck and bad luck values. Returns (luck_bonus, bad_luck)"""
        return 0, 0
    
    def modify_range(self, unit: 'Unit', min_range: int, max_range: int) -> Tuple[int, int]:
        """Modify unit's attack range. Returns (new_min, new_max)"""
        return min_range, max_range
    
    def modify_vision(self, unit: 'Unit', base_vision: int) -> int:
        """Modify unit's vision range. Default: no change"""
        return base_vision
    
    def can_move_and_attack(self, unit: 'Unit') -> Optional[bool]:
        """Override whether unit can move and attack same turn. None = use default"""
        return None
    
    def get_description(self) -> str:
        """Get human-readable description of this modifier"""
        return f"{self.__class__.__name__} modifier"


class COMTowerModifier(GameModifier):
    """
    COM_TOWER modifier: +10% attack per tower owned
    
    In Advance Wars:
    - Each COM_TOWER owned provides +10% attack to all units
    - Stacks indefinitely (no maximum limit)
    - No effect on defense or other stats
    """
    
    modifier_type = ModifierType.COM_TOWER
    priority = 10  # Apply after CO bonuses
    
    def __init__(self, tower_count: int):
        self.tower_count = max(0, tower_count)
    
    def modify_attack_value(self, unit: 'Unit', base_av: float) -> float:
        """Each tower provides +10% attack"""
        multiplier = 1.0 + (0.1 * self.tower_count)
        return base_av * multiplier
    
    def get_description(self) -> str:
        if self.tower_count == 0:
            return "No COM_TOWER bonus"
        elif self.tower_count == 1:
            return f"COM_TOWER: +10% attack"
        else:
            return f"COM_TOWER x{self.tower_count}: +{self.tower_count * 10}% attack"


@dataclass
class CommandingOfficer(GameModifier):
    """
    Base class for Commanding Officers (COs)
    
    COs provide passive bonuses and can activate powers
    """
    
    modifier_type = ModifierType.COMMANDING_OFFICER
    priority = 20  # COs apply after base modifiers
    
    # CO Identity
    name: str
    description: str
    
    # Power System
    power_meter: int = 0
    power_cost: int = 90000    # Standard CO Power cost (in damage dealt/taken)
    super_cost: int = 180000   # Super CO Power cost
    is_power_active: bool = False
    is_super_active: bool = False
    
    # Day-to-day abilities are implemented in subclasses
    
    def charge_power(self, amount: int):
        """Charge the CO's power meter"""
        if not self.is_power_active and not self.is_super_active:
            self.power_meter = min(self.power_meter + amount, self.super_cost)
    
    def can_use_power(self) -> bool:
        """Check if CO Power can be activated"""
        return self.power_meter >= self.power_cost and not self.is_power_active and not self.is_super_active
    
    def can_use_super(self) -> bool:
        """Check if Super CO Power can be activated"""
        return self.power_meter >= self.super_cost and not self.is_power_active and not self.is_super_active
    
    def activate_power(self):
        """Activate CO Power"""
        if self.can_use_power():
            self.is_power_active = True
            self.power_meter = 0
    
    def activate_super(self):
        """Activate Super CO Power"""
        if self.can_use_super():
            self.is_super_active = True
            self.power_meter = 0
    
    def end_power(self):
        """End CO Power effect"""
        self.is_power_active = False
        self.is_super_active = False


# Example COs with movement bonuses
class AdderCO(CommandingOfficer):
    """
    Adder: Quick Strike specialist
    - Day-to-day: No bonus
    - CO Power: +1 movement to all units
    - Super CO Power: +2 movement to all units
    """
    
    def __init__(self):
        super().__init__(
            name="Adder",
            description="Prefers quick strikes. CO Power boosts movement.",
            power_cost=60000,  # Charges faster than normal
            super_cost=120000
        )
    
    def modify_movement(self, unit: 'Unit', base_move: int) -> int:
        if self.is_super_active:
            return base_move + 2
        elif self.is_power_active:
            return base_move + 1
        return base_move
    
    def get_description(self) -> str:
        if self.is_super_active:
            return "Adder (Super CO Power): +2 movement"
        elif self.is_power_active:
            return "Adder (CO Power): +1 movement"
        else:
            return "Adder: No day-to-day bonus"


class MaxCO(CommandingOfficer):
    """
    Max: Direct combat specialist
    - Day-to-day: +20% direct attack, -10% indirect attack, -1 indirect range
    - CO Power: +40% direct attack
    - Super CO Power: +60% direct attack
    """
    
    def __init__(self):
        super().__init__(
            name="Max",
            description="Direct combat specialist. Weak indirect units."
        )
    
    def modify_attack_value(self, unit: 'Unit', base_av: float) -> float:
        if unit.is_indirect():
            return base_av * 0.9  # -10% indirect
        else:
            # Direct unit bonuses
            if self.is_super_active:
                return base_av * 1.6  # +60%
            elif self.is_power_active:
                return base_av * 1.4  # +40%
            else:
                return base_av * 1.2  # +20% day-to-day
    
    def modify_range(self, unit: 'Unit', min_range: int, max_range: int) -> Tuple[int, int]:
        if unit.is_indirect() and max_range > 1:
            # -1 range for indirect units
            return min_range, max(min_range, max_range - 1)
        return min_range, max_range


class SamiCO(CommandingOfficer):
    """
    Sami: Infantry specialist
    - Day-to-day: Infantry +20% attack, vehicles -10% attack
    - Transport units +1 movement
    - CO Power: Infantry +40% attack, +1 movement
    - Super CO Power: Infantry +60% attack, +2 movement, capture 2x speed
    """
    
    def __init__(self):
        super().__init__(
            name="Sami",
            description="Infantry specialist. Strong foot soldiers, weak vehicles."
        )
    
    def modify_attack_value(self, unit: 'Unit', base_av: float) -> float:
        from unit import UnitType
        
        if unit.type in [UnitType.INFANTRY, UnitType.MECH]:
            # Infantry bonuses
            if self.is_super_active:
                return base_av * 1.6  # +60%
            elif self.is_power_active:
                return base_av * 1.4  # +40%
            else:
                return base_av * 1.2  # +20% day-to-day
        elif unit.type in [UnitType.TANK, UnitType.MEDIUMTANK, UnitType.NEOTANK, 
                          UnitType.MEGATANK, UnitType.RECON, UnitType.ANTIAIR,
                          UnitType.ARTILLERY, UnitType.ROCKET, UnitType.MISSILE]:
            # Vehicle penalties
            return base_av * 0.9  # -10%
        
        return base_av
    
    def modify_movement(self, unit: 'Unit', base_move: int) -> int:
        from unit import UnitType
        
        # Transport units always get +1
        if unit.type in [UnitType.APC, UnitType.TCOPTER, UnitType.LANDER, UnitType.BLACKBOAT]:
            return base_move + 1
        
        # Infantry get movement during powers
        if unit.type in [UnitType.INFANTRY, UnitType.MECH]:
            if self.is_super_active:
                return base_move + 2
            elif self.is_power_active:
                return base_move + 1
        
        return base_move


class KoalCO(CommandingOfficer):
    """
    Koal: Road specialist
    - Day-to-day: +10% attack on roads
    - +1 movement on roads
    - CO Power: +20% attack on roads, +1 movement all units
    - Super CO Power: +30% attack on roads, +2 movement all units
    """
    
    def __init__(self):
        super().__init__(
            name="Koal",
            description="Road combat specialist. Strong on paved terrain."
        )
        self._unit_tile_getter = None  # Must be set by game manager
    
    def set_unit_tile_getter(self, getter_func):
        """Set function to get unit's current tile"""
        self._unit_tile_getter = getter_func
    
    def _is_on_road(self, unit: 'Unit') -> bool:
        """Check if unit is on a road tile"""
        if not self._unit_tile_getter:
            return False
        
        tile = self._unit_tile_getter(unit)
        if not tile:
            return False
        
        from map_system import MapType
        road_types = [
            MapType.ROAD_HORT, MapType.ROAD_VERT,
            MapType.ROAD_NE, MapType.ROAD_NW, MapType.ROAD_SE, MapType.ROAD_SW,
            MapType.ROAD_N, MapType.ROAD_E, MapType.ROAD_S, MapType.ROAD_W
        ]
        
        return tile.mapTile.type in road_types
    
    def modify_attack_value(self, unit: 'Unit', base_av: float) -> float:
        if self._is_on_road(unit):
            if self.is_super_active:
                return base_av * 1.3  # +30% on roads
            elif self.is_power_active:
                return base_av * 1.2  # +20% on roads
            else:
                return base_av * 1.1  # +10% day-to-day on roads
        return base_av
    
    def modify_movement(self, unit: 'Unit', base_move: int) -> int:
        bonus = 0
        
        # Power bonuses apply to all units
        if self.is_super_active:
            bonus = 2
        elif self.is_power_active:
            bonus = 1
        # Day-to-day: +1 on roads only
        elif self._is_on_road(unit):
            bonus = 1
        
        return base_move + bonus
"""
Enhanced Combat System for AW-RPC Phase 2A
Provides advanced combat mechanics including:
- Perfect counter-attack system
- Indirect fire units
- Combat damage preview
- Critical hits and luck
- Enhanced damage calculations
"""

import random
import math
from typing import Tuple, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    from manager import GameManager
    from unit import Unit, UnitType
    from gameboard import GameTile

@dataclass
class CombatPreview:
    """Preview of combat damage before execution"""
    attacker_damage: int
    counter_damage: int
    can_counter: bool
    attacker_hp_after: int
    defender_hp_after: int
    attacker_destroyed: bool
    defender_destroyed: bool
    terrain_bonus: int
    luck_range: Tuple[int, int]
    ammo_warning: bool

@dataclass
class EnhancedCombatResult:
    """Enhanced result of combat with detailed information"""
    attacker_damage_dealt: int
    defender_damage_dealt: int
    attacker_hp_before: int
    attacker_hp_after: int
    defender_hp_before: int
    defender_hp_after: int
    defender_destroyed: bool
    attacker_destroyed: bool
    counter_attack_occurred: bool
    terrain_bonus_used: int
    luck_bonus_attacker: int
    luck_bonus_defender: int

class CombatType(Enum):
    """Types of combat engagement"""
    DIRECT = "direct"           # Normal adjacent combat
    INDIRECT = "indirect"       # Artillery, rockets, etc.
    AIR_TO_GROUND = "air_ground"
    AIR_TO_AIR = "air_air"
    NAVAL = "naval"
    SPECIAL = "special"         # Missiles, etc.

class EnhancedCombatSystem:
    """Enhanced combat system for Phase 2A"""
    
    def __init__(self, game_manager: 'GameManager'):
        self.manager = game_manager
        self.luck_enabled = True  # Random 0-9 damage variance
        
    # =============================================================================
    # ENHANCED DAMAGE CALCULATION
    # =============================================================================
    
    def calculate_enhanced_damage(self, attacker: 'Unit', defender: 'Unit', 
                                defender_tile: 'GameTile', 
                                preview_mode: bool = False) -> int:
        """
        Enhanced damage calculation using authentic Advance Wars formula
        
        Args:
            attacker: Attacking unit
            defender: Defending unit  
            defender_tile: Tile defender is on (for terrain bonus)
            preview_mode: If True, return average damage (no luck/crits)
        """
        # Use the unit's enhanced damage method which implements the authentic formula
        return attacker.enhanced_attack_damage(defender, defender_tile, luck_enabled=not preview_mode)
    
    def get_damage_range(self, attacker: 'Unit', defender: 'Unit', 
                        defender_tile: 'GameTile') -> Tuple[int, int]:
        """Get minimum and maximum damage range for preview (authentic AW luck system)"""
        base_damage = self.calculate_enhanced_damage(attacker, defender, defender_tile, preview_mode=True)
        
        if not self.luck_enabled:
            return (base_damage, base_damage)
            
        # In Advance Wars, luck adds 0-9 damage
        min_damage = base_damage  # Base damage (luck = 0)
        max_damage = base_damage + 9  # Base damage + max luck (9)
        
        return (min_damage, max_damage)
    
    # =============================================================================
    # COUNTER-ATTACK SYSTEM
    # =============================================================================
    
    def can_counter_attack(self, attacker: 'Unit', defender: 'Unit',
                          attacker_pos: Tuple[int, int], 
                          defender_pos: Tuple[int, int]) -> bool:
        """Enhanced counter-attack validation"""
        from unit import DAMAGE_TABLE, UnitType
        
        # Defender must be alive
        if defender.status.hp <= 0:
            return False
            
        # Check if defender has ammo for counter-attack
        if not self._has_ammo_for_attack(defender):
            return False
            
        # Defender must be able to damage attacker using available weapons
        try:
            counter_base_damage = defender._select_weapon_damage(attacker)
            if counter_base_damage == 0:
                return False
        except (KeyError, IndexError):
            return False
            
        # Calculate distance
        distance = abs(attacker_pos[0] - defender_pos[0]) + abs(attacker_pos[1] - defender_pos[1])
        
        # Check if defender can reach attacker
        if not (defender.status.rangemin <= distance <= defender.status.rangemax):
            return False
            
        # Special rules for indirect units
        if self._is_indirect_unit(attacker) and distance < attacker.status.rangemin:
            # Indirect units that attack at minimum range can be countered by direct units
            return self._is_direct_unit(defender)
            
        # Air units can only counter other air units (unless special anti-air)
        if self._is_air_unit(attacker) and not (self._is_air_unit(defender) or self._is_anti_air_unit(defender)):
            return False
            
        if self._is_air_unit(defender) and not (self._is_air_unit(attacker) or self._is_anti_air_unit(attacker)):
            return False
            
        return True
    
    def _has_ammo_for_attack(self, unit: 'Unit') -> bool:
        """Check if unit has ammo for attack"""
        from unit import UnitType
        
        # Infantry and Mech always have ammo (small arms)
        if unit.type in [UnitType.INFANTRY, UnitType.MECH]:
            return True
            
        # Other units need ammo
        if hasattr(unit.status, 'ammo') and unit.status.ammo > 0:
            return True
            
        return False
    
    def _is_indirect_unit(self, unit: 'Unit') -> bool:
        """Check if unit is indirect fire"""
        from unit import UnitType
        indirect_units = [UnitType.ARTILLERY, UnitType.ROCKETS, UnitType.MISSILES]
        return unit.type in indirect_units
    
    def _is_direct_unit(self, unit: 'Unit') -> bool:
        """Check if unit is direct fire"""
        return not self._is_indirect_unit(unit) and not self._is_air_unit(unit)
    
    def _is_air_unit(self, unit: 'Unit') -> bool:
        """Check if unit is air unit"""
        from unit import UnitType
        air_units = [UnitType.FIGHTER, UnitType.BOMBER, UnitType.BATTLE_COPTER, UnitType.TRANSPORT_COPTER]
        return unit.type in air_units
    
    def _is_anti_air_unit(self, unit: 'Unit') -> bool:
        """Check if unit is specialized anti-air"""
        from unit import UnitType
        anti_air_units = [UnitType.ANTI_AIR, UnitType.MISSILES, UnitType.CRUISER]
        return unit.type in anti_air_units
    
    def _is_naval_unit(self, unit: 'Unit') -> bool:
        """Check if unit is naval"""
        from unit import UnitType
        naval_units = [UnitType.BATTLESHIP, UnitType.CRUISER, UnitType.SUBMARINE, 
                      UnitType.LANDER, UnitType.BLACK_BOAT, UnitType.CARRIER]
        return unit.type in naval_units
    
    # =============================================================================
    # COMBAT PREVIEW SYSTEM
    # =============================================================================
    
    def get_combat_preview(self, attacker_x: int, attacker_y: int,
                          defender_x: int, defender_y: int) -> CombatPreview:
        """Get detailed combat preview for UI display"""
        attacker = self.manager.unit_at(attacker_x, attacker_y)
        defender = self.manager.unit_at(defender_x, defender_y)
        
        if not attacker or not defender:
            raise ValueError("Missing attacker or defender unit")
        
        attacker_tile = self.manager.tile_at(attacker_x, attacker_y)
        defender_tile = self.manager.tile_at(defender_x, defender_y)
        
        # Calculate attacker damage
        attacker_damage = self.calculate_enhanced_damage(attacker, defender, defender_tile, preview_mode=True)
        attacker_luck_range = self.get_damage_range(attacker, defender, defender_tile)
        
        # Check counter-attack possibility
        can_counter = self.can_counter_attack(attacker, defender, 
                                            (attacker_x, attacker_y), 
                                            (defender_x, defender_y))
        
        counter_damage = 0
        if can_counter:
            counter_damage = self.calculate_enhanced_damage(defender, attacker, attacker_tile, preview_mode=True)
        
        # Calculate post-combat HP
        defender_hp_after = max(0, defender.status.hp - attacker_damage)
        attacker_hp_after = attacker.status.hp
        if can_counter and defender_hp_after > 0:
            attacker_hp_after = max(0, attacker.status.hp - counter_damage)
        
        # Get terrain bonus
        from map_system import TERRAIN_DEFENSE
        terrain_bonus = TERRAIN_DEFENSE.get(defender_tile.mapTile.type, 0)
        
        # Check ammo warnings
        ammo_warning = not self._has_ammo_for_attack(attacker)
        
        return CombatPreview(
            attacker_damage=attacker_damage,
            counter_damage=counter_damage,
            can_counter=can_counter,
            attacker_hp_after=attacker_hp_after,
            defender_hp_after=defender_hp_after,
            attacker_destroyed=attacker_hp_after <= 0,
            defender_destroyed=defender_hp_after <= 0,
            terrain_bonus=terrain_bonus,
            luck_range=attacker_luck_range,
            ammo_warning=ammo_warning
        )
    
    # =============================================================================
    # ENHANCED COMBAT EXECUTION
    # =============================================================================
    
    def execute_enhanced_combat(self, attacker_x: int, attacker_y: int,
                               defender_x: int, defender_y: int) -> EnhancedCombatResult:
        """Execute combat with full Phase 2A enhancements"""
        attacker = self.manager.unit_at(attacker_x, attacker_y)
        defender = self.manager.unit_at(defender_x, defender_y)
        attacker_tile = self.manager.tile_at(attacker_x, attacker_y)
        defender_tile = self.manager.tile_at(defender_x, defender_y)
        
        if not attacker or not defender:
            raise ValueError("Missing attacker or defender unit")
        
        # Store initial HP
        attacker_hp_before = attacker.status.hp
        defender_hp_before = defender.status.hp
        
        # Calculate and apply attacker's damage
        attacker_damage = self.calculate_enhanced_damage(attacker, defender, defender_tile)
        luck_attacker = attacker_damage - self.calculate_enhanced_damage(attacker, defender, defender_tile, preview_mode=True)
        
        defender.status.hp = max(0, defender.status.hp - attacker_damage)
        
        # Consume attacker's ammo only if using primary weapon
        if (hasattr(attacker.status, 'ammo') and attacker.status.ammo > 0 and 
            not attacker._uses_secondary_weapon(defender)):
            attacker.status.ammo -= 1
        
        # Check for counter-attack
        counter_damage = 0
        luck_defender = 0
        counter_attack_occurred = False
        
        if (defender.status.hp > 0 and 
            self.can_counter_attack(attacker, defender, 
                                  (attacker_x, attacker_y), 
                                  (defender_x, defender_y))):
            
            counter_damage = self.calculate_enhanced_damage(defender, attacker, attacker_tile)
            luck_defender = counter_damage - self.calculate_enhanced_damage(defender, attacker, attacker_tile, preview_mode=True)
            
            attacker.status.hp = max(0, attacker.status.hp - counter_damage)
            counter_attack_occurred = True
            
            # Consume defender's ammo only if using primary weapon
            if (hasattr(defender.status, 'ammo') and defender.status.ammo > 0 and 
                not defender._uses_secondary_weapon(attacker)):
                defender.status.ammo -= 1
        
        # Get terrain bonus used
        from map_system import TERRAIN_DEFENSE
        terrain_bonus = TERRAIN_DEFENSE.get(defender_tile.mapTile.type, 0)
        
        # Create result
        result = EnhancedCombatResult(
            attacker_damage_dealt=attacker_damage,
            defender_damage_dealt=counter_damage,
            attacker_hp_before=attacker_hp_before,
            attacker_hp_after=attacker.status.hp,
            defender_hp_before=defender_hp_before,
            defender_hp_after=defender.status.hp,
            defender_destroyed=defender.status.hp <= 0,
            attacker_destroyed=attacker.status.hp <= 0,
            counter_attack_occurred=counter_attack_occurred,
            terrain_bonus_used=terrain_bonus,
            luck_bonus_attacker=luck_attacker,
            luck_bonus_defender=luck_defender
        )
        
        # Remove destroyed units
        if result.defender_destroyed:
            self.manager.unit_remove(defender_x, defender_y)
        
        if result.attacker_destroyed:
            self.manager.unit_remove(attacker_x, attacker_y)
        
        return result
    
    # =============================================================================
    # INDIRECT FIRE SYSTEM
    # =============================================================================
    
    def validate_indirect_attack(self, attacker: 'Unit', 
                                attacker_x: int, attacker_y: int,
                                target_x: int, target_y: int) -> bool:
        """Validate indirect fire attack"""
        if not self._is_indirect_unit(attacker):
            return True  # Not indirect, use normal validation
        
        distance = abs(attacker_x - target_x) + abs(attacker_y - target_y)
        
        # Must respect minimum range
        if distance < attacker.status.rangemin:
            return False
        
        # Must respect maximum range  
        if distance > attacker.status.rangemax:
            return False
        
        return True
    
    def get_indirect_targets(self, attacker_x: int, attacker_y: int) -> List[Tuple[int, int]]:
        """Get all valid indirect fire targets for a unit"""
        attacker = self.manager.unit_at(attacker_x, attacker_y)
        if not attacker or not self._is_indirect_unit(attacker):
            return []
        
        targets = []
        
        for x in range(self.manager.board.width):
            for y in range(self.manager.board.height):
                if self.validate_indirect_attack(attacker, attacker_x, attacker_y, x, y):
                    target_unit = self.manager.unit_at(x, y)
                    if target_unit and target_unit.army != attacker.army:
                        targets.append((x, y))
        
        return targets
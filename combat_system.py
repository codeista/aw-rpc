# combat_system.py - Standalone combat system

import random
import math
from typing import Tuple, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from manager import GameManager
    from unit import Unit
    from game_board import GameTile

@dataclass
class CombatResult:
    """Result of a combat engagement"""
    attacker_damage_dealt: int
    defender_damage_dealt: int
    attacker_hp_before: int
    attacker_hp_after: int
    defender_hp_before: int
    defender_hp_after: int
    defender_destroyed: bool
    attacker_destroyed: bool
    counter_attack_occurred: bool
    critical_hit: bool = False

class CombatSystem:
    """Enhanced combat system for AW-RPC"""
    
    def __init__(self, game_manager: 'GameManager'):
        self.manager = game_manager
    
    def calculate_damage(self, attacker: 'Unit', defender: 'Unit', 
                        defender_tile: 'GameTile', luck_enabled: bool = True) -> int:
        """Authentic Advance Wars damage calculation"""
        
        # Use the unit's enhanced damage method which implements the authentic formula
        return attacker.enhanced_attack_damage(defender, defender_tile, luck_enabled)
    
    def can_counter_attack(self, attacker: 'Unit', defender: 'Unit', 
                          attacker_pos: Tuple[int, int], defender_pos: Tuple[int, int]) -> bool:
        """Check if defender can counter-attack"""
        
        # Import here to avoid circular imports
        from unit import DAMAGE_TABLE, UnitType
        
        # Defender must be alive
        if defender.status.hp <= 0:
            return False
        
        # Defender must have ammo (if applicable)
        if hasattr(defender.status, 'ammo') and defender.status.ammo <= 0:
            if defender.type not in [UnitType.INFANTRY, UnitType.MECH]:
                return False
        
        # Calculate distance
        distance = abs(attacker_pos[0] - defender_pos[0]) + abs(attacker_pos[1] - defender_pos[1])
        
        # Defender must be able to attack attacker type using available weapons
        try:
            counter_damage = defender._select_weapon_damage(attacker)
            if counter_damage == 0:
                return False
        except (KeyError, IndexError):
            return False
        
        # Check if defender's range can reach attacker
        return defender.status.rangemin <= distance <= defender.status.rangemax
    
    def execute_combat(self, attacker_pos: Tuple[int, int], 
                      defender_pos: Tuple[int, int]) -> CombatResult:
        """Execute complete combat sequence with counter-attack"""
        
        attacker_x, attacker_y = attacker_pos
        defender_x, defender_y = defender_pos
        
        # Get units and tiles
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
        attacker_damage = self.calculate_damage(attacker, defender, defender_tile)
        defender.status.hp = max(0, defender.status.hp - attacker_damage)
        
        # Consume attacker's ammo only if using primary weapon
        if (hasattr(attacker.status, 'ammo') and attacker.status.ammo > 0 and 
            not attacker._uses_secondary_weapon(defender)):
            attacker.status.ammo -= 1
        
        # Check for counter-attack
        counter_damage = 0
        counter_attack_occurred = False
        
        if self.can_counter_attack(attacker, defender, attacker_pos, defender_pos):
            counter_damage = self.calculate_damage(defender, attacker, attacker_tile)
            attacker.status.hp = max(0, attacker.status.hp - counter_damage)
            counter_attack_occurred = True
            
            # Consume defender's ammo only if using primary weapon
            if (hasattr(defender.status, 'ammo') and defender.status.ammo > 0 and 
                not defender._uses_secondary_weapon(attacker)):
                defender.status.ammo -= 1
        
        # Create combat result
        result = CombatResult(
            attacker_damage_dealt=attacker_damage,
            defender_damage_dealt=counter_damage,
            attacker_hp_before=attacker_hp_before,
            attacker_hp_after=attacker.status.hp,
            defender_hp_before=defender_hp_before,
            defender_hp_after=defender.status.hp,
            defender_destroyed=defender.status.hp <= 0,
            attacker_destroyed=attacker.status.hp <= 0,
            counter_attack_occurred=counter_attack_occurred
        )
        
        # Remove destroyed units
        if result.defender_destroyed:
            self.manager.unit_remove(defender_x, defender_y)
        
        if result.attacker_destroyed:
            self.manager.unit_remove(attacker_x, attacker_y)
        
        return result
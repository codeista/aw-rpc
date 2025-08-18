"""Test unit join/merge mechanics"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from core.game_factory import GameFactory
from core.unit import UnitType

class TestUnitJoin:
    """Test unit join mechanics"""
    
    def setup_method(self):
        """Set up test game"""
        self.manager, self.token = GameFactory.create_standard_game('tiny')
        # Give players funds
        self.manager.board_v2.player_funds[0] = 50000
        self.manager.board_v2.player_funds[1] = 50000
    
    def test_basic_join(self):
        """Test basic unit join functionality"""
        # Store initial funds
        initial_funds = self.manager.board_v2.player_funds[0]
        
        # Create two infantry units for player 0
        unit1 = self.manager.unit_create_v2(0, "INFANTRY", 2, 2)
        assert unit1 is not None
        
        unit2 = self.manager.unit_create_v2(0, "INFANTRY", 3, 2)
        assert unit2 is not None
        
        # Get the units
        unit1 = self.manager.tile_at(2, 2).unit
        unit2 = self.manager.tile_at(3, 2).unit
        
        # Damage unit2 to 5 HP (50 internal)
        unit2.status.hp = 50
        
        # End turn to allow movement
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Join unit1 into unit2
        result = self.manager.unit_join(2, 2, 3, 2)
        if not result['success']:
            print(f"Join failed: {result.get('error')}")
        assert result['success']
        
        # Check results
        assert result['combined_hp'] == 100  # 100 + 50 = 150, capped at 100
        # 5 excess HP * 1000 cost * 10% = 500
        assert result['refund'] == 500
        
        # Verify unit1 is gone
        assert self.manager.tile_at(2, 2).unit is None
        
        # Verify unit2 has full HP
        unit2_after = self.manager.tile_at(3, 2).unit
        assert unit2_after is not None
        assert unit2_after.status.hp == 100
        
        # Verify funds were refunded
        funds_after = self.manager.board_v2.player_funds[0]
        funds_spent = 2000  # 2 infantry
        funds_refunded = 500
        # Account for income from properties during turn changes
        # We don't know exactly how much income, so just check refund happened
        assert funds_after > initial_funds - funds_spent
        assert result['refund'] == 500
    
    def test_join_different_types_fails(self):
        """Test that joining different unit types fails"""
        # Create infantry and mech
        unit1 = self.manager.unit_create_v2(0, "INFANTRY", 2, 2)
        assert unit1 is not None
        
        unit2 = self.manager.unit_create_v2(0, "MECH", 3, 2)
        assert unit2 is not None
        
        # Damage mech
        mech = self.manager.tile_at(3, 2).unit
        mech.status.hp = 50
        
        # End turn
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Try to join - should fail
        result = self.manager.unit_join(2, 2, 3, 2)
        assert not result['success']
        assert "same type" in result['error']
    
    def test_join_high_hp_target_fails(self):
        """Test that joining into high HP unit fails"""
        # Create two infantry units
        unit1 = self.manager.unit_create_v2(0, "INFANTRY", 2, 2)
        assert unit1 is not None
        
        unit2 = self.manager.unit_create_v2(0, "INFANTRY", 3, 2)
        assert unit2 is not None
        
        # Unit2 has full HP (10)
        
        # End turn
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Try to join - should fail
        result = self.manager.unit_join(2, 2, 3, 2)
        assert not result['success']
        assert "9 HP or less" in result['error']
    
    def test_join_enemy_units_fails(self):
        """Test that joining enemy units fails"""
        # Create infantry for player 0
        unit1 = self.manager.unit_create_v2(0, "INFANTRY", 2, 2)
        assert unit1 is not None
        
        # End turn
        self.manager.army_end_turn()
        
        # Create infantry for player 1
        unit2 = self.manager.unit_create_v2(1, "INFANTRY", 3, 2)
        assert unit2 is not None
        
        # Damage it
        unit2 = self.manager.tile_at(3, 2).unit
        unit2.status.hp = 50
        
        # End turn
        self.manager.army_end_turn()
        
        # Try to join enemy unit - should fail
        result = self.manager.unit_join(2, 2, 3, 2)
        assert not result['success']
        assert "enemy units" in result['error']
    
    def test_join_fuel_ammo_combination(self):
        """Test that fuel and ammo are combined correctly"""
        # Create two tanks
        unit1 = self.manager.unit_create_v2(0, "TANK", 2, 2)
        assert unit1 is not None
        
        unit2 = self.manager.unit_create_v2(0, "TANK", 3, 2)
        assert unit2 is not None
        
        # Get units
        tank1 = self.manager.tile_at(2, 2).unit
        tank2 = self.manager.tile_at(3, 2).unit
        
        # Set specific fuel/ammo values
        tank1.status.fuel = 30
        tank1.status.ammo = 3
        tank2.status.fuel = 25
        tank2.status.ammo = 4
        tank2.status.hp = 50  # Allow joining
        
        # End turn
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Join
        result = self.manager.unit_join(2, 2, 3, 2)
        assert result['success']
        
        # Check combined values
        assert result['combined_fuel'] == 54  # 30 + 25 - 1 (movement cost)
        assert result['combined_ammo'] == 7   # 3 + 4
        
        # Verify on the unit
        tank_after = self.manager.tile_at(3, 2).unit
        assert tank_after.status.fuel == 54
        assert tank_after.status.ammo == 7
    
    def test_join_excess_values_capped(self):
        """Test that excess fuel/ammo are capped at max"""
        # Create two bombers (high fuel capacity)
        unit1 = self.manager.unit_create_v2(0, "BOMBER", 2, 2)
        assert unit1 is not None
        
        unit2 = self.manager.unit_create_v2(0, "BOMBER", 3, 2)
        assert unit2 is not None
        
        # Get units
        bomber1 = self.manager.tile_at(2, 2).unit
        bomber2 = self.manager.tile_at(3, 2).unit
        
        # Set to near max values
        bomber1.status.fuel = 90
        bomber1.status.ammo = 8
        bomber2.status.fuel = 90
        bomber2.status.ammo = 8
        bomber2.status.hp = 50  # Allow joining
        
        # End turn
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Join
        result = self.manager.unit_join(2, 2, 3, 2)
        assert result['success']
        
        # Check values are capped
        bomber_after = self.manager.tile_at(3, 2).unit
        assert bomber_after.status.fuel == bomber1.config.max_fuel  # Capped
        assert bomber_after.status.ammo == bomber1.config.max_ammo  # Capped
    
    def test_join_ends_unit_turn(self):
        """Test that joining ends the joined unit's turn"""
        # Create two infantry
        unit1 = self.manager.unit_create_v2(0, "INFANTRY", 2, 2)
        assert unit1 is not None
        
        unit2 = self.manager.unit_create_v2(0, "INFANTRY", 3, 2)
        assert unit2 is not None
        
        # Damage unit2
        unit2 = self.manager.tile_at(3, 2).unit
        unit2.status.hp = 50
        
        # End turn
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Verify both can act
        unit1 = self.manager.tile_at(2, 2).unit
        unit2 = self.manager.tile_at(3, 2).unit
        assert unit1.can_move
        assert unit2.can_move
        
        # Join
        result = self.manager.unit_join(2, 2, 3, 2)
        assert result['success']
        
        # Verify joined unit cannot act
        joined_unit = self.manager.tile_at(3, 2).unit
        assert not joined_unit.can_move
        assert not joined_unit.can_attack
        assert not joined_unit.can_capture
    
    def test_expensive_unit_refund(self):
        """Test refund calculation for expensive units"""
        # Give extra funds for expensive units
        self.manager.board_v2.player_funds[0] = 100000
        
        # Create two megatanks (28000 cost each)
        unit1 = self.manager.unit_create_v2(0, "MEGATANK", 2, 2)
        assert unit1 is not None
        
        unit2 = self.manager.unit_create_v2(0, "MEGATANK", 3, 2)
        assert unit2 is not None
        
        # Damage unit2 to 6 HP
        unit2 = self.manager.tile_at(3, 2).unit
        unit2.status.hp = 60
        
        # End turn
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        initial_funds = self.manager.board_v2.player_funds[0]
        
        # Join
        result = self.manager.unit_join(2, 2, 3, 2)
        assert result['success']
        
        # 10 HP + 6 HP = 16 HP, 6 excess HP
        # Refund = 6 * 28000 * 0.1 = 16800
        assert result['refund'] == 16800
        assert self.manager.board_v2.player_funds[0] == initial_funds + 16800


if __name__ == "__main__":
    test = TestUnitJoin()
    
    print("Testing basic join...")
    test.setup_method()
    test.test_basic_join()
    print("✓ Passed")
    
    print("Testing join different types fails...")
    test.setup_method()
    test.test_join_different_types_fails()
    print("✓ Passed")
    
    print("Testing join high HP target fails...")
    test.setup_method()
    test.test_join_high_hp_target_fails()
    print("✓ Passed")
    
    print("Testing join enemy units fails...")
    test.setup_method()
    test.test_join_enemy_units_fails()
    print("✓ Passed")
    
    print("Testing fuel/ammo combination...")
    test.setup_method()
    test.test_join_fuel_ammo_combination()
    print("✓ Passed")
    
    print("Testing excess values capped...")
    test.setup_method()
    test.test_join_excess_values_capped()
    print("✓ Passed")
    
    print("Testing join ends unit turn...")
    test.setup_method()
    test.test_join_ends_unit_turn()
    print("✓ Passed")
    
    print("Testing expensive unit refund...")
    test.setup_method()
    test.test_expensive_unit_refund()
    print("✓ Passed")
    
    print("\nAll unit join tests passed!")
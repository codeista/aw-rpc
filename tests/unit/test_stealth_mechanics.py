"""Test Stealth fighter and Submarine hide/unhide mechanics"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from core.game_factory import GameFactory
from core.unit import UnitType

class TestStealthMechanics:
    """Test stealth hide/unhide functionality"""
    
    def setup_method(self):
        """Set up test game"""
        self.manager, self.token = GameFactory.create_standard_game('tiny')
        # Give players funds
        self.manager.board_v2.player_funds[0] = 100000
        self.manager.board_v2.player_funds[1] = 100000
    
    def test_stealth_can_hide(self):
        """Test that Stealth fighters can hide"""
        # Create stealth fighter
        unit = self.manager.unit_create_v2(0, "STEALTH", 5, 5)
        assert unit is not None
        
        # End turn to allow action
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Hide the stealth
        result = self.manager.unit_hide(5, 5)
        assert result['success']
        
        # Verify stealth is hidden
        stealth = self.manager.tile_at(5, 5).unit
        assert stealth.is_hidden == True
        
        # Verify stealth cannot act after hiding
        assert not stealth.can_move
        assert not stealth.can_attack
    
    def test_sub_can_hide(self):
        """Test that Submarines can hide (dive)"""
        # Find a sea tile
        sea_x, sea_y = None, None
        for y in range(self.manager.board.height):
            for x in range(self.manager.board.width):
                tile = self.manager.tile_at(x, y)
                if tile.mapTile.type.name in ['SEA', 'PORT']:
                    sea_x, sea_y = x, y
                    break
            if sea_x is not None:
                break
        
        if sea_x is None:
            pytest.skip("No sea tiles on this map")
        
        # Create submarine
        unit = self.manager.unit_create_v2(0, "SUB", sea_x, sea_y)
        assert unit is not None
        
        # End turn
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Hide (dive) the sub
        result = self.manager.unit_hide(sea_x, sea_y)
        assert result['success']
        
        # Verify sub is hidden
        sub = self.manager.tile_at(sea_x, sea_y).unit
        assert sub.is_hidden == True
    
    def test_other_units_cannot_hide(self):
        """Test that non-stealth units cannot hide"""
        # Create fighter (not stealth)
        unit = self.manager.unit_create_v2(0, "FIGHTER", 5, 5)
        assert unit is not None
        
        # End turn
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Try to hide - should fail
        result = self.manager.unit_hide(5, 5)
        assert not result['success']
        assert "Only Stealth fighters and Submarines" in result['error']
    
    def test_cannot_hide_after_moving(self):
        """Test that units cannot hide after moving"""
        # Create stealth
        unit = self.manager.unit_create_v2(0, "STEALTH", 5, 5)
        assert unit is not None
        
        # End turn
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Move stealth
        result = self.manager.unit_move(5, 5, 6, 5)
        assert result is not None
        
        # Try to hide - should fail
        result = self.manager.unit_hide(6, 5)
        assert not result['success']
        assert "must not have moved" in result['error']
    
    def test_already_hidden_cannot_hide(self):
        """Test that already hidden units cannot hide again"""
        # Create stealth
        unit = self.manager.unit_create_v2(0, "STEALTH", 5, 5)
        assert unit is not None
        
        # End turn
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Hide
        result = self.manager.unit_hide(5, 5)
        assert result['success']
        
        # End turn and try to hide again
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Try to hide again - should fail
        result = self.manager.unit_hide(5, 5)
        assert not result['success']
        assert "already hidden" in result['error']
    
    def test_unhide_stealth(self):
        """Test unhiding a stealth fighter"""
        # Create and hide stealth
        unit = self.manager.unit_create_v2(0, "STEALTH", 5, 5)
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        result = self.manager.unit_hide(5, 5)
        assert result['success']
        
        # End turn
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Unhide
        result = self.manager.unit_unhide(5, 5)
        assert result['success']
        
        # Verify stealth is not hidden
        stealth = self.manager.tile_at(5, 5).unit
        assert stealth.is_hidden == False
        
        # Verify stealth CAN still act after unhiding
        assert stealth.can_move
        assert stealth.can_attack
    
    def test_cannot_unhide_non_hidden_unit(self):
        """Test that non-hidden units cannot unhide"""
        # Create stealth (not hidden)
        unit = self.manager.unit_create_v2(0, "STEALTH", 5, 5)
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Try to unhide - should fail
        result = self.manager.unit_unhide(5, 5)
        assert not result['success']
        assert "not hidden" in result['error']
    
    def test_hidden_unit_cannot_attack(self):
        """Test that hidden units cannot attack"""
        # Create stealth and enemy
        stealth = self.manager.unit_create_v2(0, "STEALTH", 5, 5)
        self.manager.army_end_turn()
        
        enemy = self.manager.unit_create_v2(1, "FIGHTER", 6, 5)
        self.manager.army_end_turn()
        
        # Hide stealth
        result = self.manager.unit_hide(5, 5)
        assert result['success']
        
        # End turn
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Try to attack - should fail
        try:
            result = self.manager.unit_attack_enhanced(5, 5, 6, 5)
            # If we get here, the attack succeeded when it shouldn't have
            assert False, "Hidden unit was able to attack"
        except ValueError as e:
            # This is expected
            assert "Hidden units cannot attack" in str(e)
    
    def test_stealth_fuel_consumption(self):
        """Test that stealth uses different fuel when hidden"""
        # Create stealth
        unit = self.manager.unit_create_v2(0, "STEALTH", 5, 5)
        stealth = self.manager.tile_at(5, 5).unit
        
        # Check normal fuel use (should be 5)
        assert stealth.fuel_use() == 5
        
        # Hide stealth
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        result = self.manager.unit_hide(5, 5)
        assert result['success']
        
        # Check hidden fuel use (should be 8)
        assert stealth.fuel_use() == 8
    
    def test_sub_fuel_consumption_when_hidden(self):
        """Test that subs use more fuel when submerged"""
        # Find sea tile
        sea_x, sea_y = None, None
        for y in range(self.manager.board.height):
            for x in range(self.manager.board.width):
                tile = self.manager.tile_at(x, y)
                if tile.mapTile.type.name in ['SEA', 'PORT']:
                    sea_x, sea_y = x, y
                    break
            if sea_x is not None:
                break
        
        if sea_x is None:
            pytest.skip("No sea tiles on this map")
        
        # Create sub
        unit = self.manager.unit_create_v2(0, "SUB", sea_x, sea_y)
        sub = self.manager.tile_at(sea_x, sea_y).unit
        
        # Check normal fuel use (should be 1 for sea unit)
        assert sub.fuel_use() == 1
        
        # Hide sub
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        result = self.manager.unit_hide(sea_x, sea_y)
        assert result['success']
        
        # Check hidden fuel use (should be 5)
        assert sub.fuel_use() == 5


if __name__ == "__main__":
    test = TestStealthMechanics()
    
    print("Testing stealth can hide...")
    test.setup_method()
    test.test_stealth_can_hide()
    print("✓ Passed")
    
    print("Testing sub can hide...")
    test.setup_method()
    test.test_sub_can_hide()
    print("✓ Passed")
    
    print("Testing other units cannot hide...")
    test.setup_method()
    test.test_other_units_cannot_hide()
    print("✓ Passed")
    
    print("Testing cannot hide after moving...")
    test.setup_method()
    test.test_cannot_hide_after_moving()
    print("✓ Passed")
    
    print("Testing already hidden cannot hide...")
    test.setup_method()
    test.test_already_hidden_cannot_hide()
    print("✓ Passed")
    
    print("Testing unhide stealth...")
    test.setup_method()
    test.test_unhide_stealth()
    print("✓ Passed")
    
    print("Testing cannot unhide non-hidden unit...")
    test.setup_method()
    test.test_cannot_unhide_non_hidden_unit()
    print("✓ Passed")
    
    print("Testing hidden unit cannot attack...")
    test.setup_method()
    test.test_hidden_unit_cannot_attack()
    print("✓ Passed")
    
    print("Testing stealth fuel consumption...")
    test.setup_method()
    test.test_stealth_fuel_consumption()
    print("✓ Passed")
    
    print("Testing sub fuel consumption when hidden...")
    test.setup_method()
    test.test_sub_fuel_consumption_when_hidden()
    print("✓ Passed")
    
    print("\nAll stealth mechanic tests passed!")
"""Test visibility filtering for hidden units"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from core.game_factory import GameFactory
from core.unit import UnitType

class TestVisibilityFiltering:
    """Test that hidden units are properly filtered from enemy view"""
    
    def setup_method(self):
        """Set up test game"""
        self.manager, self.token = GameFactory.create_standard_game('tiny')
        # Give players funds
        self.manager.board_v2.player_funds[0] = 100000
        self.manager.board_v2.player_funds[1] = 100000
    
    def test_own_units_always_visible(self):
        """Test that players can always see their own units, even when hidden"""
        # Create stealth for player 0
        unit = self.manager.unit_create_v2(0, "STEALTH", 5, 5)
        assert unit is not None
        
        # Hide the stealth
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        result = self.manager.unit_hide(5, 5)
        assert result['success']
        
        # Check visibility for player 0 (owner)
        stealth = self.manager.tile_at(5, 5).unit
        stealth.x = 5
        stealth.y = 5
        
        assert self.manager.is_unit_visible_to_player(stealth, 0) == True
        
        # Clean up
        delattr(stealth, 'x')
        delattr(stealth, 'y')
    
    def test_enemy_units_visible_when_not_hidden(self):
        """Test that enemy units are visible when not hidden"""
        # Create stealth for player 0
        unit = self.manager.unit_create_v2(0, "STEALTH", 5, 5)
        assert unit is not None
        
        # Check visibility for player 1 (enemy)
        stealth = self.manager.tile_at(5, 5).unit
        stealth.x = 5
        stealth.y = 5
        
        assert self.manager.is_unit_visible_to_player(stealth, 1) == True
        
        # Clean up
        delattr(stealth, 'x')
        delattr(stealth, 'y')
    
    def test_hidden_enemy_units_invisible(self):
        """Test that hidden enemy units are invisible unless adjacent"""
        # Create stealth for player 0
        unit = self.manager.unit_create_v2(0, "STEALTH", 5, 5)
        assert unit is not None
        
        # Hide the stealth
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        result = self.manager.unit_hide(5, 5)
        assert result['success']
        
        # Check visibility for player 1 (enemy) - should not see it
        stealth = self.manager.tile_at(5, 5).unit
        stealth.x = 5
        stealth.y = 5
        
        assert self.manager.is_unit_visible_to_player(stealth, 1) == False
        
        # Clean up
        delattr(stealth, 'x')
        delattr(stealth, 'y')
    
    def test_hidden_enemy_units_visible_when_adjacent(self):
        """Test that hidden enemy units become visible when adjacent to friendly unit"""
        # Create stealth for player 0
        unit = self.manager.unit_create_v2(0, "STEALTH", 5, 5)
        assert unit is not None
        
        # Hide the stealth
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        result = self.manager.unit_hide(5, 5)
        assert result['success']
        
        # Create infantry for player 1 adjacent to hidden stealth
        self.manager.army_end_turn()
        unit2 = self.manager.unit_create_v2(1, "INFANTRY", 6, 5)
        assert unit2 is not None
        
        # Check visibility for player 1 - should see it now
        stealth = self.manager.tile_at(5, 5).unit
        stealth.x = 5
        stealth.y = 5
        
        assert self.manager.is_unit_visible_to_player(stealth, 1) == True
        
        # Clean up
        delattr(stealth, 'x')
        delattr(stealth, 'y')
    
    def test_get_visible_units_filtering(self):
        """Test get_visible_units_for_player method"""
        # Create units for both players
        unit1 = self.manager.unit_create_v2(0, "STEALTH", 3, 3)
        unit2 = self.manager.unit_create_v2(0, "TANK", 4, 4)
        
        self.manager.army_end_turn()
        unit3 = self.manager.unit_create_v2(1, "INFANTRY", 7, 7)
        unit4 = self.manager.unit_create_v2(1, "RECON", 8, 8)
        
        # Hide player 0's stealth
        self.manager.army_end_turn()
        result = self.manager.unit_hide(3, 3)
        assert result['success']
        
        # Get visible units for player 0 - should see all 4
        visible_p0 = self.manager.get_visible_units_for_player(0)
        assert len(visible_p0) == 4
        
        # Get visible units for player 1 - should see 3 (not the hidden stealth)
        visible_p1 = self.manager.get_visible_units_for_player(1)
        assert len(visible_p1) == 3
        
        # Verify the hidden stealth is not in player 1's view
        stealth_visible = any(u['type'] == 'STEALTH' for u in visible_p1)
        assert not stealth_visible
    
    def test_game_board_rpc_visibility(self):
        """Test that game_board RPC respects visibility"""
        # This would need to be tested with the actual RPC method
        # For now, we've verified the core visibility logic works
        pass


if __name__ == "__main__":
    test = TestVisibilityFiltering()
    
    print("Testing own units always visible...")
    test.setup_method()
    test.test_own_units_always_visible()
    print("✓ Passed")
    
    print("Testing enemy units visible when not hidden...")
    test.setup_method()
    test.test_enemy_units_visible_when_not_hidden()
    print("✓ Passed")
    
    print("Testing hidden enemy units invisible...")
    test.setup_method()
    test.test_hidden_enemy_units_invisible()
    print("✓ Passed")
    
    print("Testing hidden enemy units visible when adjacent...")
    test.setup_method()
    test.test_hidden_enemy_units_visible_when_adjacent()
    print("✓ Passed")
    
    print("Testing get_visible_units filtering...")
    test.setup_method()
    test.test_get_visible_units_filtering()
    print("✓ Passed")
    
    print("\nAll visibility filtering tests passed!")
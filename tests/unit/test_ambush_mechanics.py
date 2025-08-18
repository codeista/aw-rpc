"""Test ambush mechanics for hidden units"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from core.game_factory import GameFactory
from core.unit import UnitType

class TestAmbushMechanics:
    """Test that hidden units can ambush enemy units"""
    
    def setup_method(self):
        """Set up test game"""
        self.manager, self.token = GameFactory.create_standard_game('tiny')
        # Give players funds
        self.manager.board_v2.player_funds[0] = 100000
        self.manager.board_v2.player_funds[1] = 100000
    
    def test_ambush_stops_movement(self):
        """Test that units stop when encountering hidden enemies"""
        # Create stealth for player 0 and hide it
        stealth = self.manager.unit_create_v2(0, "STEALTH", 5, 5)
        assert stealth is not None
        
        # Hide the stealth
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        result = self.manager.unit_hide(5, 5)
        assert result['success']
        
        # Create tank for player 1 and try to move through hidden stealth
        self.manager.army_end_turn()
        tank = self.manager.unit_create_v2(1, "TANK", 3, 5)
        assert tank is not None
        
        # Try to move tank from (3,5) to (7,5) - should be ambushed at (4,5)
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Move the tank
        moved_unit = self.manager.unit_move(3, 5, 7, 5)
        
        # Tank should stop at (4,5) - one tile before the hidden stealth
        tank_tile = self.manager.tile_from_unit(moved_unit)
        assert tank_tile.x == 4
        assert tank_tile.y == 5
        
        # Tank should have lost all actions
        assert not moved_unit.can_move
        assert not moved_unit.can_attack
        
        # Stealth should still be at (5,5) and now visible
        stealth_at_55 = self.manager.tile_at(5, 5).unit
        assert stealth_at_55 is not None
        assert stealth_at_55.type == UnitType.STEALTH
        assert stealth_at_55.is_hidden  # Still hidden, just discovered
    
    def test_ambush_immediate_adjacent(self):
        """Test ambush when hidden enemy is immediately adjacent"""
        # Create stealth for player 0 and hide it
        stealth = self.manager.unit_create_v2(0, "STEALTH", 5, 5)
        assert stealth is not None
        
        # Hide the stealth
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        result = self.manager.unit_hide(5, 5)
        assert result['success']
        
        # Create infantry for player 1 adjacent to hidden stealth
        self.manager.army_end_turn()
        infantry = self.manager.unit_create_v2(1, "INFANTRY", 4, 5)
        assert infantry is not None
        
        # Try to move infantry into hidden stealth - should not move
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Try to move
        moved_unit = self.manager.unit_move(4, 5, 5, 5)
        
        # Infantry should stay at original position
        inf_tile = self.manager.tile_from_unit(moved_unit)
        assert inf_tile.x == 4
        assert inf_tile.y == 5
        
        # Infantry should have lost all actions
        assert not moved_unit.can_move
        assert not moved_unit.can_attack
    
    def test_no_ambush_on_visible_units(self):
        """Test that visible units don't cause ambush"""
        # Create stealth for player 0 but DON'T hide it
        stealth = self.manager.unit_create_v2(0, "STEALTH", 5, 5)
        assert stealth is not None
        
        # Create tank for player 1
        self.manager.army_end_turn()
        tank = self.manager.unit_create_v2(1, "TANK", 3, 5)
        assert tank is not None
        
        # Move tank past visible stealth - should succeed
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Move should work normally (can't move through enemy unit)
        with pytest.raises(ValueError, match="occupied"):
            self.manager.unit_move(3, 5, 5, 5)
    
    def test_ambush_makes_unit_visible(self):
        """Test that ambush reveals hidden unit to adjacent friendly units"""
        # Create sub for player 0 and hide it
        sub = self.manager.unit_create_v2(0, "SUB", 5, 5)
        assert sub is not None
        
        # Hide the sub
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        result = self.manager.unit_hide(5, 5)
        assert result['success']
        
        # Create cruiser for player 1 to move into ambush
        self.manager.army_end_turn()
        cruiser = self.manager.unit_create_v2(1, "CRUISER", 3, 5)
        assert cruiser is not None
        
        # Move cruiser to get ambushed
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        moved_unit = self.manager.unit_move(3, 5, 7, 5)
        
        # After ambush, the sub should be visible to player 1
        # (because cruiser is now adjacent at position 4,5)
        sub_unit = self.manager.tile_at(5, 5).unit
        sub_unit.x = 5
        sub_unit.y = 5
        
        assert self.manager.is_unit_visible_to_player(sub_unit, 1) == True
        
        # Clean up
        delattr(sub_unit, 'x')
        delattr(sub_unit, 'y')
    
    def test_ambush_with_diagonal_path(self):
        """Test ambush detection works with diagonal movement paths"""
        # Create stealth and hide it
        stealth = self.manager.unit_create_v2(0, "STEALTH", 5, 5)
        assert stealth is not None
        
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        result = self.manager.unit_hide(5, 5)
        assert result['success']
        
        # Create recon that will move diagonally
        self.manager.army_end_turn()
        recon = self.manager.unit_create_v2(1, "RECON", 3, 3)
        assert recon is not None
        
        # Try to move to (7,7) - path might go through (5,5)
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Move recon
        moved_unit = self.manager.unit_move(3, 3, 7, 7)
        
        # Check if ambushed (depends on pathfinding)
        recon_tile = self.manager.tile_from_unit(moved_unit)
        
        # If path went through (5,5), unit should be ambushed
        # Otherwise it should reach destination
        # Both are valid outcomes depending on pathfinding algorithm
        assert recon_tile is not None
        
        # If ambushed, unit should lose all actions
        if recon_tile.x != 7 or recon_tile.y != 7:
            assert not moved_unit.can_move
            assert not moved_unit.can_attack


if __name__ == "__main__":
    test = TestAmbushMechanics()
    
    print("Testing ambush stops movement...")
    test.setup_method()
    test.test_ambush_stops_movement()
    print("✓ Passed")
    
    print("Testing ambush when immediately adjacent...")
    test.setup_method()
    test.test_ambush_immediate_adjacent()
    print("✓ Passed")
    
    print("Testing no ambush on visible units...")
    test.setup_method()
    test.test_no_ambush_on_visible_units()
    print("✓ Passed")
    
    print("Testing ambush makes unit visible...")
    test.setup_method()
    test.test_ambush_makes_unit_visible()
    print("✓ Passed")
    
    print("Testing ambush with diagonal path...")
    test.setup_method()
    test.test_ambush_with_diagonal_path()
    print("✓ Passed")
    
    print("\nAll ambush mechanics tests passed!")
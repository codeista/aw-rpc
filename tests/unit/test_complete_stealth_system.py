"""Test complete stealth system including hide/unhide, visibility, and ambush"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from core.game_factory import GameFactory
from core.unit import UnitType

class TestCompleteStealthSystem:
    """Test the complete stealth system functionality"""
    
    def setup_method(self):
        """Set up test game"""
        self.manager, self.token = GameFactory.create_standard_game('tiny')
        # Give players funds
        self.manager.board_v2.player_funds[0] = 100000
        self.manager.board_v2.player_funds[1] = 100000
    
    def test_stealth_gameplay_scenario(self):
        """Test a complete stealth gameplay scenario"""
        # Player 0 creates stealth bomber
        stealth = self.manager.unit_create_v2(0, "STEALTH", 2, 2)
        assert stealth is not None
        
        # Player 1 creates fighter 
        self.manager.army_end_turn()
        fighter = self.manager.unit_create_v2(1, "FIGHTER", 8, 8)
        assert fighter is not None
        
        # Player 0 hides stealth (must hide before moving)
        self.manager.army_end_turn()
        result = self.manager.unit_hide(2, 2)
        assert result['success']
        
        # End turn, then move hidden stealth
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        self.manager.unit_move(2, 2, 5, 5)
        
        # Check visibility from Player 1's perspective
        units_p1 = self.manager.get_visible_units_for_player(1)
        # Should only see their own fighter, not the hidden stealth
        assert len(units_p1) == 1
        assert units_p1[0]['type'] == 'FIGHTER'
        
        # Player 1 moves fighter towards hidden stealth
        self.manager.army_end_turn()
        self.manager.unit_move(8, 8, 5, 6)  # Move to be orthogonally adjacent
        
        # Now fighter is adjacent - stealth should be visible
        units_p1 = self.manager.get_visible_units_for_player(1)
        assert len(units_p1) == 2  # Fighter + visible stealth
        
        # Player 0 moves stealth away and it becomes invisible again
        self.manager.army_end_turn()
        self.manager.unit_move(5, 5, 2, 5)
        
        # Check visibility - stealth no longer adjacent, should be invisible
        units_p1 = self.manager.get_visible_units_for_player(1)
        assert len(units_p1) == 1
        assert units_p1[0]['type'] == 'FIGHTER'
    
    def test_submarine_dive_and_ambush(self):
        """Test submarine diving and ambush mechanics"""
        # Player 0 creates submarine
        sub = self.manager.unit_create_v2(0, "SUB", 3, 3)
        assert sub is not None
        
        # Player 1 creates battleship and cruiser
        self.manager.army_end_turn()
        battleship = self.manager.unit_create_v2(1, "BATTLESHIP", 7, 3)
        cruiser = self.manager.unit_create_v2(1, "CRUISER", 3, 7)
        assert battleship is not None
        assert cruiser is not None
        
        # Player 0 dives submarine
        self.manager.army_end_turn()
        result = self.manager.unit_hide(3, 3)
        assert result['success']
        
        # Submarine uses more fuel when submerged
        sub_unit = self.manager.tile_at(3, 3).unit
        initial_fuel = sub_unit.status.fuel
        
        # End turn - sub should consume fuel (5 when hidden)
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        fuel_consumed = initial_fuel - sub_unit.status.fuel
        print(f"DEBUG: Sub consumed {fuel_consumed} fuel (expected 5)")
        # According to the code, SUB consumes 5 fuel when hidden
        assert fuel_consumed == 5
        
        # Player 1's turn - try to move battleship through hidden sub
        # Should be ambushed and stop at (6, 3)
        self.manager.army_end_turn()  # Switch to player 1
        moved_unit = self.manager.unit_move(7, 3, 2, 3)
        bs_tile = self.manager.tile_from_unit(moved_unit)
        
        # Battleship should stop before the sub
        assert bs_tile.x == 4  # Stopped one tile after the sub
        assert bs_tile.y == 3
        assert not moved_unit.can_move
        assert not moved_unit.can_attack
        
        # Sub should now be visible to player 1 (battleship is adjacent)
        sub_unit.x = 3
        sub_unit.y = 3
        assert self.manager.is_unit_visible_to_player(sub_unit, 1) == True
        delattr(sub_unit, 'x')
        delattr(sub_unit, 'y')
    
    def test_multiple_hidden_units(self):
        """Test visibility with multiple hidden units"""
        # Player 0 creates multiple stealth units
        stealth1 = self.manager.unit_create_v2(0, "STEALTH", 2, 2)
        stealth2 = self.manager.unit_create_v2(0, "STEALTH", 4, 4)
        sub = self.manager.unit_create_v2(0, "SUB", 6, 6)
        
        # Player 1 creates recon
        self.manager.army_end_turn()
        recon = self.manager.unit_create_v2(1, "RECON", 5, 5)
        
        # Hide all player 0 units
        self.manager.army_end_turn()
        self.manager.unit_hide(2, 2)
        self.manager.unit_hide(4, 4)
        self.manager.unit_hide(6, 6)
        
        # From player 1's view, should only see recon (not adjacent to any hidden units)
        units_p1 = self.manager.get_visible_units_for_player(1)
        assert len(units_p1) == 1
        assert units_p1[0]['type'] == 'RECON'
        
        # Move recon adjacent to second stealth
        self.manager.army_end_turn()
        self.manager.unit_move(5, 5, 4, 5)
        
        # Now should see recon + adjacent stealth2
        units_p1 = self.manager.get_visible_units_for_player(1)
        assert len(units_p1) == 2
        visible_types = {u['type'] for u in units_p1}
        assert visible_types == {'RECON', 'STEALTH'}
        
        # The visible stealth should be at (4, 4)
        stealth_visible = [u for u in units_p1 if u['type'] == 'STEALTH'][0]
        assert stealth_visible['x'] == 4
        assert stealth_visible['y'] == 4
    
    def test_stealth_unhide_does_not_end_turn(self):
        """Test that unhiding does NOT end the unit's turn"""
        # Create and hide stealth
        stealth = self.manager.unit_create_v2(0, "STEALTH", 3, 3)
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        result = self.manager.unit_hide(3, 3)
        assert result['success']
        
        # Unit should not be able to move/attack after hiding (hiding ends turn)
        unit = self.manager.tile_at(3, 3).unit
        assert not unit.can_move
        assert not unit.can_attack
        
        # Next turn, unhide
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        result = self.manager.unit_unhide(3, 3)
        assert result['success']
        
        # Unit SHOULD be able to move and attack after unhiding
        # (unhiding does not end turn)
        unit = self.manager.tile_at(3, 3).unit
        assert unit.can_move
        assert unit.can_attack
        
    def test_game_board_filters_visibility(self):
        """Test that visibility filtering works correctly in game board data"""
        # Create units for both players
        stealth = self.manager.unit_create_v2(0, "STEALTH", 3, 3)
        tank = self.manager.unit_create_v2(0, "TANK", 4, 4)
        
        self.manager.army_end_turn()
        infantry = self.manager.unit_create_v2(1, "INFANTRY", 7, 7)
        
        # Hide the stealth
        self.manager.army_end_turn()
        self.manager.unit_hide(3, 3)
        
        # Test visibility filtering directly
        # Player 0 should see all 3 units
        units_p0 = self.manager.get_visible_units_for_player(0)
        assert len(units_p0) == 3
        unit_types_p0 = {u['type'] for u in units_p0}
        assert unit_types_p0 == {'STEALTH', 'TANK', 'INFANTRY'}
        
        # Player 1 should only see 2 units (not hidden stealth)
        units_p1 = self.manager.get_visible_units_for_player(1)
        assert len(units_p1) == 2
        unit_types_p1 = {u['type'] for u in units_p1}
        assert unit_types_p1 == {'TANK', 'INFANTRY'}


if __name__ == "__main__":
    test = TestCompleteStealthSystem()
    
    print("Testing complete stealth gameplay scenario...")
    test.setup_method()
    test.test_stealth_gameplay_scenario()
    print("✓ Passed")
    
    print("Testing submarine dive and ambush...")
    test.setup_method()
    test.test_submarine_dive_and_ambush()
    print("✓ Passed")
    
    print("Testing multiple hidden units...")
    test.setup_method()
    test.test_multiple_hidden_units()
    print("✓ Passed")
    
    print("Testing stealth unhide does not end turn...")
    test.setup_method()
    test.test_stealth_unhide_does_not_end_turn()
    print("✓ Passed")
    
    print("Testing game board filters visibility...")
    test.setup_method()
    test.test_game_board_filters_visibility()
    print("✓ Passed")
    
    print("\nComplete stealth system test passed!")
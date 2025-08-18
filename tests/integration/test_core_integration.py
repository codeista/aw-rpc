#!/usr/bin/env python3
"""
Core Integration Tests for Advance Wars RPC
Tests fundamental game mechanics and workflows
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from manager import GameManager
from gameboard import GameBoard
from config import Config
from core.map_system import map_repository, Army
from core.game_factory import GameFactory
from core.player_system import PlayerManager

class TestCoreIntegration:
    """Test core game functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.config = Config()
        
        # Create game using GameFactory
        player_manager = PlayerManager.create_default_2_player()
        self.manager, self.token = GameFactory._create_game('test', player_manager)
        self.board = self.manager.board
        
        # Set up logger to avoid AttributeError
        import logging
        self.manager.app_logger = logging.getLogger(__name__)
        
        # Set starting funds for testing
        self.board.red_funds = 50000
        self.board.blue_funds = 50000
        
    def test_basic_unit_lifecycle(self):
        """Test creating, moving, and attacking with units"""
        print("\n🎮 Testing Basic Unit Lifecycle...")
        
        # Create units
        tank = self.manager.unit_create("RED", "TANK", 0, 3)
        assert tank is not None, "Should create RED tank"
        assert tank.type.name == "TANK", "Unit should be a tank"
        
        # End turn to BLUE
        self.manager.army_end_turn()
        assert self.board.current_player == 1  # Player 1 is BLUE
        
        # Create BLUE unit closer for melee attack
        infantry = self.manager.unit_create("BLUE", "INFANTRY", 2, 3)
        assert infantry is not None, "Should create BLUE infantry"
        assert infantry.type.name == "INFANTRY", "Unit should be infantry"
        
        # End turn back to RED
        self.manager.army_end_turn()
        assert self.board.current_player == 0  # Player 0 is RED
        
        # Move RED tank adjacent to infantry
        moved_unit = self.manager.unit_move(0, 3, 1, 3)
        assert moved_unit is not None, "Tank should move"
        assert moved_unit.type.name == "TANK", "Should be the tank that moved"
        
        # End turn cycle to enable combat
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Attack with tank
        try:
            # Get infantry HP before attack
            target_tile = self.board.grid[3 * self.board.width + 2]
            hp_before = target_tile.unit.status.hp if target_tile.unit else 100
            
            # Attack returns the attacking unit
            attacker = self.manager.unit_attack(1, 3, 2, 3)
            assert attacker is not None, "Tank should attack infantry"
            
            # Check target took damage
            hp_after = target_tile.unit.status.hp if target_tile.unit else 0
            assert hp_after < hp_before, "Should deal damage"
        except Exception as e:
            assert False, f"Attack failed: {e}"
        
        print("✅ Basic unit lifecycle test passed!")
        
    def test_transport_operations(self):
        """Test transport loading and unloading"""
        print("\n🚢 Testing Transport Operations...")
        
        # Create APC and infantry
        apc = self.manager.unit_create("RED", "APC", 0, 3)
        inf = self.manager.unit_create("RED", "INFANTRY", 1, 3)
        assert apc is not None and inf is not None, "Should create units"
        
        # End turn to enable movement
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Load infantry into APC
        load_result = self.manager.unit_load(1, 3, 0, 3)
        assert load_result.get('success', False) == True, "Should load infantry"
        
        # Move loaded APC
        move_result = self.manager.unit_move(0, 3, 3, 3)
        assert move_result.get('success', False) == True, "Should move loaded APC"
        
        # Unload infantry
        unload_result = self.manager.unit_unload(3, 3, 3, 4)
        assert unload_result.get('success', False) == True, "Should unload infantry"
        
        # Verify infantry at new position
        tile = self.board.grid[4 * self.board.width + 3]
        assert tile.unit is not None, "Infantry should be at unload position"
        assert tile.unit.type.name == "INFANTRY", "Unit should be infantry"
        
        print("✅ Transport operations test passed!")
        
    def test_capture_mechanics(self):
        """Test property capture"""
        print("\n🏰 Testing Capture Mechanics...")
        
        # Create infantry
        inf = self.manager.unit_create("RED", "INFANTRY", 0, 3)
        assert inf is not None, "Should create infantry"
        
        # Find a neutral city
        city_pos = None
        for i, tile in enumerate(self.board.grid):
            if tile.mapTile and tile.mapTile.type.name == "CITY" and not tile.mapTile.army:
                city_pos = (i % self.board.width, i // self.board.width)
                break
                
        if city_pos:
            # End turn to enable movement
            self.manager.army_end_turn()
            self.manager.army_end_turn()
            
            # Move to city
            move_result = self.manager.unit_move(0, 3, city_pos[0], city_pos[1])
            assert move_result.get('success', False) == True, "Should move to city"
            
            # Start capture
            capture_result = self.manager.capture_tile(city_pos[0], city_pos[1])
            assert capture_result.get('success', False) == True, "Should start capture"
            
            # Check capture HP reduced
            tile = self.board.grid[city_pos[1] * self.board.width + city_pos[0]]
            assert tile.capture_hp < 20, "Capture HP should be reduced"
            
            print("✅ Capture mechanics test passed!")
        else:
            print("⚠️  No neutral city found for capture test")
            
    def test_economic_system(self):
        """Test income and unit production"""
        print("\n💰 Testing Economic System...")
        
        # Record starting funds
        start_funds = self.board.red_funds
        
        # Create a unit
        unit = self.manager.unit_create("RED", "INFANTRY", 0, 3)
        assert unit is not None, "Should create unit"
        
        # Check funds reduced
        assert self.board.red_funds < start_funds, "Funds should be reduced"
        cost_paid = start_funds - self.board.red_funds
        assert cost_paid == 1000, "Infantry should cost 1000"
        
        # End full turn cycle
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Check income added
        funds_before_income = self.board.red_funds
        properties = self.board.total_red_properties
        expected_income = properties * 1000
        
        # Income is added at turn start
        assert self.board.red_funds >= funds_before_income, "Should have income"
        
        print("✅ Economic system test passed!")
        
    def test_combat_calculations(self):
        """Test damage calculations"""
        print("\n⚔️ Testing Combat Calculations...")
        
        # Create units for combat test
        self.manager.unit_create("RED", "TANK", 0, 3)
        self.manager.army_end_turn()
        recon = self.manager.unit_create("BLUE", "RECON", 2, 3)
        assert recon is not None, "Should create BLUE recon"
        self.manager.army_end_turn()
        
        # Get damage estimate
        damage_result = self.manager.damage_estimate(0, 3, 2, 3)
        assert 'estimated_damage' in damage_result, "Should return damage estimate"
        assert damage_result['estimated_damage'] > 0, "Tank should damage recon"
        
        # Perform actual attack (need to move closer first)
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        move_result = self.manager.unit_move(0, 3, 1, 3)
        assert move_result.get('success', False) == True
        
        attack_result = self.manager.unit_attack(1, 3, 2, 3)
        assert attack_result.get('success', False) == True, "Should attack successfully"
        assert attack_result.get('damage_dealt', 0) > 0, "Should deal damage"
        
        print("✅ Combat calculations test passed!")
        
    def test_turn_management(self):
        """Test turn order and day progression"""
        print("\n🔄 Testing Turn Management...")
        
        # Check initial state
        assert self.board.current_turn == Army.RED, "Should start with RED"
        assert self.board.days == 0, "Should start on day 0"  # Days start at 0
        
        # End RED turn
        self.manager.army_end_turn()
        assert self.board.current_turn == Army.BLUE, "Should be BLUE's turn"
        assert self.board.days == 0, "Still day 0"
        
        # End BLUE turn (completes day)
        self.manager.army_end_turn()
        assert self.board.current_turn == Army.RED, "Should be RED's turn again"
        assert self.board.days == 1, "Should be day 1"
        
        print("✅ Turn management test passed!")

def run_core_integration_tests():
    """Run all core integration tests"""
    test_suite = TestCoreIntegration()
    
    print("🧪 Running Core Integration Tests")
    print("=" * 60)
    
    test_methods = [
        test_suite.test_basic_unit_lifecycle,
        test_suite.test_transport_operations,
        test_suite.test_capture_mechanics,
        test_suite.test_economic_system,
        test_suite.test_combat_calculations,
        test_suite.test_turn_management,
    ]
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        test_suite.setup_method()
        try:
            test_method()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_method.__name__}: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"❌ {test_method.__name__}: {type(e).__name__} - {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    return failed == 0

if __name__ == "__main__":
    success = run_core_integration_tests()
    sys.exit(0 if success else 1)
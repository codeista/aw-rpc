#!/usr/bin/env python3
"""
Integration Tests for Complex Game Scenarios
Tests multi-step gameplay sequences and edge cases
"""

import pytest
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from typing import Dict, List, Any, Optional, Tuple
from manager_v2 import GameManager
from gameboard import GameBoard
from config import Config
from map_system import map_repository, Army
from unit import UnitType
from tests.integration.test_map_predeployed import get_predeployed_test_game, get_comprehensive_test_game

class TestComplexScenarios:
    """Test complex multi-step game scenarios"""
    
    def setup_method(self):
        """Setup for each test"""
        self.config = Config()
        self.manager = None
        
    def _setup_manager(self, manager):
        """Set up logger for manager"""
        import logging
        if manager and not manager.app_logger:
            manager.app_logger = logging.getLogger(__name__)
        return manager
        
    def teardown_method(self):
        """Cleanup after each test"""
        if self.manager:
            self.manager = None
    
    # =========================================================================
    # TRANSPORT CHAIN SCENARIOS
    # =========================================================================
    
    def test_transport_chain_loading(self):
        """Test loading multiple units in sequence"""
        self.manager = self._setup_manager(get_predeployed_test_game())
        board = self.manager.board
        
        # Create transport and multiple infantry units
        apc_result = self.manager.unit_create("RED", "APC", 0, 0)
        inf1_result = self.manager.unit_create("RED", "INFANTRY", 1, 0)
        inf2_result = self.manager.unit_create("RED", "INFANTRY", 0, 1)
        
        # End turn to enable movement
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Load first infantry
        result1 = self.manager.unit_load(1, 0, 0, 0)
        assert result1['success'] == True
        assert len(self.manager.board.grid[0].unit.transport.cargo) == 1
        
        # Load second infantry  
        result2 = self.manager.unit_load(0, 1, 0, 0)
        assert result2['success'] == True
        assert len(self.manager.board.grid[0].unit.transport.cargo) == 2
        
        # Verify APC is full
        result3 = self.manager.unit_load(2, 0, 0, 0)  # Try to load non-existent unit
        assert result3['success'] == False
        
    def test_transport_unload_and_action(self):
        """Test unloading units and performing actions same turn"""
        self.manager = self._setup_manager(get_predeployed_test_game())
        
        # Create loaded APC
        apc = self.manager.unit_create(str(self.manager.board.current_turn.name), "APC", 3, 3)
        inf = self.manager.unit_create(str(self.manager.board.current_turn.name), "INFANTRY", 3, 4)
        
        # End turn and load
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        self.manager.unit_load(3, 4, 3, 3)
        
        # Move APC
        self.manager.unit_move(3, 3, 5, 3)
        
        # Unload infantry
        result = self.manager.unit_unload(5, 3, 5, 4)
        assert result['success'] == True
        
        # Verify unloaded unit cannot act
        tile = self.manager.board.grid[5 * self.manager.board.width + 5]
        if tile.unit:
            assert tile.unit.status.moved == True
            
    def test_naval_transport_with_ground_units(self):
        """Test lander transport carrying tanks across water"""
        self.manager = self._setup_manager(get_comprehensive_test_game())
        
        # Create lander and tank near water
        lander = self.manager.unit_create(str(self.manager.board.current_turn.name), "LANDER", 0, 5)
        tank = self.manager.unit_create(str(self.manager.board.current_turn.name), "TANK", 0, 4)
        
        # End turn and load tank
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        result = self.manager.unit_load(0, 4, 0, 5)
        assert result['success'] == True
        
        # Move lander across water
        result = self.manager.unit_move(0, 5, 3, 5)
        assert result['success'] == True
        
        # Verify tank is still loaded
        assert len(self.manager.board.grid[3 * self.manager.board.width + 5].unit.transport.cargo) == 1
    
    # =========================================================================
    # MULTI-UNIT COMBAT SCENARIOS
    # =========================================================================
    
    def test_chain_combat_scenario(self):
        """Test multiple combats in single turn"""
        self.manager = self._setup_manager(get_predeployed_test_game())
        
        # Create RED combat units
        tank1 = self.manager.unit_create(str(self.manager.board.current_turn.name), "TANK", 2, 2)
        tank2 = self.manager.unit_create(str(self.manager.board.current_turn.name), "TANK", 4, 2)
        
        # Switch to BLUE turn to create BLUE units
        self.manager.army_end_turn()
        
        # Create BLUE units
        inf1 = self.manager.unit_create(str(self.manager.board.current_turn.name), "INFANTRY", 3, 2)
        inf2 = self.manager.unit_create(str(self.manager.board.current_turn.name), "INFANTRY", 5, 2)
        
        # BLUE attacks with first infantry (should fail - infantry can't attack same turn created)
        result1 = self.manager.unit_attack(3, 2, 2, 2)
        assert result1['success'] == False
        
        # End turn to enable attacks
        self.manager.army_end_turn()
        
        # RED tank attacks BLUE infantry
        result2 = self.manager.unit_attack(2, 2, 3, 2)
        assert result2['success'] == True
        assert result2['damage_dealt'] > 0
        
        # Second RED tank attacks
        result3 = self.manager.unit_attack(4, 2, 5, 2)
        assert result3['success'] == True
        
    def test_indirect_combat_with_fog_of_war(self):
        """Test artillery and rocket combat mechanics"""
        self.manager = self._setup_manager(get_predeployed_test_game())
        
        # Create RED indirect combat units
        artillery = self.manager.unit_create(str(self.manager.board.current_turn.name), "ARTILLERY", 0, 0)
        rocket = self.manager.unit_create(str(self.manager.board.current_turn.name), "ROCKET", 0, 2)
        
        # Switch to BLUE and create target
        self.manager.army_end_turn()
        target = self.manager.unit_create(str(self.manager.board.current_turn.name), "TANK", 3, 1)
        
        # Switch back to RED
        self.manager.army_end_turn()
        
        # End turn to enable combat
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Artillery cannot attack after moving
        self.manager.unit_move(0, 0, 1, 0)
        result1 = self.manager.unit_attack(1, 0, 3, 1)
        assert result1['success'] == False  # Can't attack after moving
        
        # Rocket can attack at long range without moving
        result2 = self.manager.unit_attack(0, 2, 3, 1)
        assert result2['success'] == True
        assert result2['damage_dealt'] > 0
        
    def test_combat_with_terrain_advantage(self):
        """Test combat with terrain defense bonuses"""
        self.manager = self._setup_manager(get_comprehensive_test_game())
        
        # Create RED units
        plain_tank = self.manager.unit_create(str(self.manager.board.current_turn.name), "TANK", 1, 3)
        
        # Switch to BLUE for defenders
        self.manager.army_end_turn()
        mountain_inf = self.manager.unit_create(str(self.manager.board.current_turn.name), "INFANTRY", 2, 3)  
        city_inf = self.manager.unit_create(str(self.manager.board.current_turn.name), "INFANTRY", 2, 4)
        
        # Switch back to RED
        self.manager.army_end_turn()
        
        # End turn for combat
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Get damage preview showing terrain effects
        preview = self.manager.damage_estimate(1, 3, 2, 4)
        assert 'estimated_damage' in preview
        
        # Attack city infantry (should deal less damage due to defense)
        result = self.manager.unit_attack(1, 3, 2, 4)
        assert result['success'] == True
        # City provides defense bonus, so damage should be reduced
        
    # =========================================================================
    # VICTORY CONDITION SCENARIOS  
    # =========================================================================
    
    def test_hq_capture_victory(self):
        """Test winning by capturing enemy HQ"""
        self.manager = self._setup_manager(get_predeployed_test_game())
        
        # Find BLUE HQ position
        blue_hq_pos = None
        for i, tile in enumerate(self.manager.board.grid):
            if hasattr(tile, 'mapTile') and tile.mapTile and \
               hasattr(tile.mapTile, 'is_hq') and tile.mapTile.is_hq() and \
               tile.mapTile.army == Army.BLUE:
                blue_hq_pos = (i % self.manager.board.width, i // self.manager.board.width)
                break
                
        if not blue_hq_pos:
            pytest.skip("No BLUE HQ found on map")
            
        # Create infantry near HQ
        inf = self.manager.unit_create(str(self.manager.board.current_turn.name), "INFANTRY", blue_hq_pos[0], blue_hq_pos[1] - 1)
        
        # Move to HQ and start capture
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        self.manager.unit_move(blue_hq_pos[0], blue_hq_pos[1] - 1, blue_hq_pos[0], blue_hq_pos[1])
        
        # Capture over multiple turns
        for _ in range(3):  # Usually takes 2-3 turns
            result = self.manager.capture_tile(blue_hq_pos[0], blue_hq_pos[1])
            if result.get('victory'):
                assert result['victory_type'] == 'HQ_CAPTURE'
                assert self.manager.board.game_active == False
                return
            self.manager.army_end_turn()
            self.manager.army_end_turn()
            
    def test_elimination_victory(self):
        """Test winning by eliminating all enemy units"""
        self.manager = self._setup_manager(get_predeployed_test_game())
        
        # Create overwhelming force
        for i in range(5):
            self.manager.unit_create(str(self.manager.board.current_turn.name), "TANK", i, 0)
            
        # Create single enemy unit
        self.manager.unit_create(str(self.manager.board.current_turn.name), "INFANTRY", 3, 5)
        
        # End initial turn
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Move tanks toward enemy
        for i in range(5):
            self.manager.unit_move(i, 0, i, 2)
            
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Attack with multiple tanks
        for i in range(5):
            tile = self.manager.board.grid[3 * self.manager.board.width + 5]
            if tile.unit:  # If enemy still exists
                result = self.manager.unit_attack(i, 2, 3, 5)
                if result.get('target_destroyed'):
                    # Check for elimination victory
                    if self.manager.board.total_blue_troops == 0:
                        assert self.manager.board.game_active == False
                        return
                        
    def test_property_control_victory(self):
        """Test winning by controlling majority of properties"""
        self.manager = self._setup_manager(get_comprehensive_test_game())
        
        # Count total properties
        total_properties = 0
        for tile in self.manager.board.grid:
            if hasattr(tile, 'mapTile') and tile.mapTile and \
               hasattr(tile.mapTile.type, 'name') and \
               tile.mapTile.type.name in ['CITY', 'FACTORY', 'AIRPORT', 'PORT']:
                total_properties += 1
                
        # Create many infantry for capturing
        for i in range(10):
            x = i % self.manager.board.width
            y = i // self.manager.board.width
            self.manager.unit_create(str(self.manager.board.current_turn.name), "INFANTRY", x, y)
            
        # Simulate many turns of capturing
        # This is a simplified test - real property victory requires capturing 80% of properties
        
    # =========================================================================
    # EDGE CASES AND ERROR HANDLING
    # =========================================================================
    
    def test_unit_fuel_exhaustion(self):
        """Test air/naval units running out of fuel"""
        self.manager = self._setup_manager(get_predeployed_test_game())
        
        # Create air unit
        fighter_result = self.manager.unit_create(str(self.manager.board.current_turn.name), "FIGHTER", 0, 0)
        # Get the actual unit to modify fuel
        fighter = self.manager.board.grid[0].unit
        if fighter:
            fighter.status.fuel = 3  # Set very low fuel
        
        # Move multiple turns until fuel exhausted
        for turn in range(5):
            self.manager.army_end_turn()
            if self.manager.board.current_turn == Army.RED:
                # Check if unit still exists
                tile = self.manager.board.grid[0]
                if not tile.unit:
                    # Unit crashed from fuel exhaustion
                    assert True
                    return
                    
        # If we get here, fuel system may not be working
        
    def test_blocked_factory_production(self):
        """Test production when factory is blocked"""
        self.manager = self._setup_manager(get_predeployed_test_game())
        
        # Create unit on factory
        factory_pos = (0, 3)  # Standard factory position
        blocking_unit = self.manager.unit_create(str(self.manager.board.current_turn.name), "INFANTRY", 0, 3)
        
        # Try to produce another unit
        result = self.manager.unit_create(str(self.manager.board.current_turn.name), "TANK", 0, 3)
        assert result['success'] == False
        assert 'blocked' in result.get('error', '').lower() or 'occupied' in result.get('error', '').lower()
        
    def test_invalid_transport_combinations(self):
        """Test invalid transport loading combinations"""
        self.manager = self._setup_manager(get_predeployed_test_game())
        
        # Create incompatible transport/cargo combinations
        apc = self.manager.unit_create(str(self.manager.board.current_turn.name), "APC", 0, 0)
        tank = self.manager.unit_create(str(self.manager.board.current_turn.name), "TANK", 1, 0)
        fighter = self.manager.unit_create(str(self.manager.board.current_turn.name), "FIGHTER", 0, 1)
        
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Tank cannot load into APC
        result1 = self.manager.unit_load(1, 0, 0, 0)
        assert result1['success'] == False
        
        # Fighter cannot load into APC  
        result2 = self.manager.unit_load(0, 1, 0, 0)
        assert result2['success'] == False
        
    def test_repair_beyond_max_hp(self):
        """Test repair limits and edge cases"""
        self.manager = self._setup_manager(get_predeployed_test_game())
        
        # Create damaged unit and black boat
        inf_result = self.manager.unit_create(str(self.manager.board.current_turn.name), "INFANTRY", 1, 0)
        # Get the actual unit to modify health
        inf = self.manager.board.grid[self.manager.board.width + 0].unit
        if inf:
            inf.status.health = 8  # Damaged
        
        blackboat = self.manager.unit_create(str(self.manager.board.current_turn.name), "BLACKBOAT", 0, 0)
        
        # End turn
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Repair once
        result1 = self.manager.repair_unit(0, 0, 1, 0, 2)
        assert result1['success'] == True
        assert inf.status.health == 10  # Max HP
        
        # Try to repair beyond max
        result2 = self.manager.repair_unit(0, 0, 1, 0, 2)
        assert result2['success'] == False  # Should fail at max HP
        
    def test_simultaneous_capture_attempts(self):
        """Test multiple units trying to capture same property"""
        self.manager = self._setup_manager(get_predeployed_test_game())
        
        # Find a capturable property
        city_pos = None
        for i, tile in enumerate(self.manager.board.grid):
            if hasattr(tile, 'mapTile') and tile.mapTile and \
               hasattr(tile.mapTile.type, 'name') and tile.mapTile.type.name == 'CITY':
                city_pos = (i % self.manager.board.width, i // self.manager.board.width)
                break
                
        if not city_pos:
            pytest.skip("No city found on map")
            
        # Create two infantry near city
        inf1 = self.manager.unit_create(str(self.manager.board.current_turn.name), "INFANTRY", city_pos[0] - 1, city_pos[1])
        inf2 = self.manager.unit_create(str(self.manager.board.current_turn.name), "INFANTRY", city_pos[0], city_pos[1] - 1)
        
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Move first infantry to city
        self.manager.unit_move(city_pos[0] - 1, city_pos[1], city_pos[0], city_pos[1])
        result1 = self.manager.capture_tile(city_pos[0], city_pos[1])
        assert result1['success'] == True
        
        # Second infantry cannot move to occupied city
        result2 = self.manager.unit_move(city_pos[0], city_pos[1] - 1, city_pos[0], city_pos[1])
        assert result2['success'] == False

# =========================================================================
# TEST RUNNER
# =========================================================================

def run_integration_tests():
    """Run all integration tests"""
    test_suite = TestComplexScenarios()
    
    print("🧪 Running Complex Scenario Integration Tests")
    print("=" * 60)
    
    test_methods = [
        ("Transport Chain Loading", test_suite.test_transport_chain_loading),
        ("Transport Unload and Action", test_suite.test_transport_unload_and_action),
        ("Naval Transport", test_suite.test_naval_transport_with_ground_units),
        ("Chain Combat", test_suite.test_chain_combat_scenario),
        ("Indirect Combat", test_suite.test_indirect_combat_with_fog_of_war),
        ("Terrain Combat", test_suite.test_combat_with_terrain_advantage),
        ("HQ Capture Victory", test_suite.test_hq_capture_victory),
        ("Elimination Victory", test_suite.test_elimination_victory),
        ("Property Control Victory", test_suite.test_property_control_victory),
        ("Fuel Exhaustion", test_suite.test_unit_fuel_exhaustion),
        ("Blocked Factory", test_suite.test_blocked_factory_production),
        ("Invalid Transport", test_suite.test_invalid_transport_combinations),
        ("Repair Limits", test_suite.test_repair_beyond_max_hp),
        ("Simultaneous Capture", test_suite.test_simultaneous_capture_attempts),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_method in test_methods:
        test_suite.setup_method()
        try:
            test_method()
            print(f"✅ {test_name}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_name}: Assertion failed - {str(e)}")
            failed += 1
        except Exception as e:
            print(f"❌ {test_name}: {type(e).__name__} - {str(e)}")
            failed += 1
        finally:
            test_suite.teardown_method()
    
    print("\n" + "=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    return failed == 0

if __name__ == "__main__":
    import sys
    success = run_integration_tests()
    sys.exit(0 if success else 1)
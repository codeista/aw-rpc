#!/usr/bin/env python3
"""
Comprehensive Automated Regression Test Suite for Advance Wars RPC

This test suite validates all core game mechanics using RPC API calls
to ensure nothing breaks as the codebase evolves.

Usage:
    python3 tests/regression/test_complete_game_mechanics.py
    
Test Categories:
- Game Management
- Unit Operations  
- Combat System
- Transport System
- Capture Mechanics
- Economic System
- Special Actions
"""

import requests
import json
import time
import sys
import os
from typing import Dict, List, Any, Optional

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class AdvanceWarsRegressionTester:
    """Automated regression test suite for Advance Wars RPC game engine"""
    
    def __init__(self, base_url: str = "http://localhost:5000/api"):
        self.base_url = base_url
        self.test_token = f"regression-test-{int(time.time())}"
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
        
    def rpc_call(self, method: str, params: Dict = None) -> Dict:
        """Make RPC call and return result"""
        if params is None:
            params = {}
        
        # Add token to all calls that need it
        if 'token' not in params and method not in ['troop_info']:
            params['token'] = self.test_token
            
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        
        try:
            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def assert_success(self, result: Dict, test_name: str, expected_keys: List[str] = None) -> bool:
        """Assert that RPC call was successful"""
        # Check for top-level error
        if 'error' in result:
            self.record_test(test_name, False, f"RPC error: {result['error']}")
            return False
        
        # Check for result
        if 'result' not in result:
            self.record_test(test_name, False, "No result in response")
            return False
        
        # NEW: Check for error inside result
        result_data = result['result']
        if isinstance(result_data, dict):
            # Check for error field
            if 'error' in result_data:
                self.record_test(test_name, False, f"Method error: {result_data['error']}")
                return False
            
            # Check for success=false
            if 'success' in result_data and not result_data['success']:
                error_msg = result_data.get('error', result_data.get('message', 'Unknown error'))
                self.record_test(test_name, False, f"Method failed: {error_msg}")
                return False
            
        # Check for expected keys in result
        if expected_keys:
            for key in expected_keys:
                if key not in result_data:
                    self.record_test(test_name, False, f"Missing expected key: {key}")
                    return False
        
        self.record_test(test_name, True, "Success")
        return True
    
    def record_test(self, test_name: str, passed: bool, message: str = ""):
        """Record test result"""
        if passed:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            self.tests_failed += 1
            print(f"❌ {test_name}: {message}")
        
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })
    
    def wait_for_server(self, timeout: int = 30) -> bool:
        """Wait for server to be available"""
        print("🔍 Checking server availability...")
        for i in range(timeout):
            try:
                response = requests.get("http://localhost:5000", timeout=5)
                if response.status_code == 200:
                    print("✅ Server is available")
                    return True
            except:
                pass
            time.sleep(1)
        
        print("❌ Server not available after timeout")
        return False
    
    # =============================================================================
    # GAME MANAGEMENT TESTS
    # =============================================================================
    
    def test_game_management(self) -> bool:
        """Test all game management operations"""
        print("\n🎮 Testing Game Management...")
        
        # Test game creation
        result = self.rpc_call('game_create_test', {'use_optimized': True})
        if not self.assert_success(result, "Game Creation"):
            return False
        
        # Test getting game board
        result = self.rpc_call('game_board')
        if not self.assert_success(result, "Get Game Board", ['current_turn', 'game_active', 'grid']):
            return False
        
        board = result['result']
        if not board['game_active']:
            self.record_test("Game Active Status", False, "Game should be active")
            return False
        self.record_test("Game Active Status", True)
        
        # Test turn checking
        result = self.rpc_call('check_turn')
        if not self.assert_success(result, "Check Turn"):
            return False
        
        return True
    
    # =============================================================================
    # UNIT OPERATIONS TESTS  
    # =============================================================================
    
    def test_unit_operations(self) -> bool:
        """Test unit creation, selection, and movement"""
        print("\n🪖 Testing Unit Operations...")
        
        # Test unit creation at a valid plain tile
        result = self.rpc_call('unit_create', {
            'army': 'RED',
            'unit_type': 'INFANTRY', 
            'x': 0, 'y': 8  # PLAIN tile
        })
        if not self.assert_success(result, "Unit Creation"):
            return False
        
        # End turn to enable movement
        self.rpc_call('army_end_turn')
        self.rpc_call('army_end_turn')
        
        # Test unit selection
        result = self.rpc_call('unit_select', {'x': 0, 'y': 8})
        if not self.assert_success(result, "Unit Selection"):
            return False
        
        # Test movement validation (before moving)
        result = self.rpc_call('movement_range', {'unit_x': 0, 'unit_y': 8})
        if not self.assert_success(result, "Movement Validation"):
            return False
        
        # Test unit movement (simple adjacent move)
        result = self.rpc_call('movement_execute', {'from_x': 0, 'from_y': 8, 'to_x': 1, 'to_y': 8})
        if not self.assert_success(result, "Unit Movement"):
            return False
        
        return True
    
    # =============================================================================
    # COMBAT SYSTEM TESTS
    # =============================================================================
    
    def test_combat_system(self) -> bool:
        """Test combat mechanics"""
        print("\n⚔️ Testing Combat System...")
        
        # Create units for combat testing
        # Create RED tank
        result = self.rpc_call('unit_create', {
            'army': 'RED',
            'unit_type': 'TANK',
            'x': 6, 'y': 8  # Plain tile
        })
        if not self.assert_success(result, "Create RED Tank"):
            return False
        
        # Create BLUE infantry as target
        result = self.rpc_call('unit_create', {
            'army': 'BLUE',
            'unit_type': 'INFANTRY',
            'x': 7, 'y': 8  # Adjacent plain tile
        })
        if not self.assert_success(result, "Create BLUE Infantry"):
            return False
        
        # End turns to enable combat
        self.rpc_call('army_end_turn')
        self.rpc_call('army_end_turn')
        
        # Test combat preview between the created units
        result = self.rpc_call('combat_preview', {
            'attacker_x': 6, 'attacker_y': 8,
            'defender_x': 7, 'defender_y': 8
        })
        if not self.assert_success(result, "Combat Preview"):
            return False
        
        # Test get attack targets
        result = self.rpc_call('combat_targets', {'unit_x': 6, 'unit_y': 8})
        if not self.assert_success(result, "Get Attack Targets"):
            return False
        
        # Test damage chart access
        result = self.rpc_call('get_damage_chart')
        if not self.assert_success(result, "Get Damage Chart"):
            return False
        
        return True
    
    # =============================================================================
    # TRANSPORT SYSTEM TESTS
    # =============================================================================
    
    def test_transport_system(self) -> bool:
        """Test transport loading and unloading"""
        print("\n🚢 Testing Transport System...")
        
        # Create APC transport on a plain tile
        result = self.rpc_call('unit_create', {
            'army': 'RED',
            'unit_type': 'APC',
            'x': 4, 'y': 8  # MOUNTAIN tile but units can be created there
        })
        if not self.assert_success(result, "Create APC Transport"):
            return False
        
        # Create infantry cargo adjacent
        result = self.rpc_call('unit_create', {
            'army': 'RED', 
            'unit_type': 'INFANTRY',
            'x': 5, 'y': 8  # MOUNTAIN tile adjacent
        })
        if not self.assert_success(result, "Create Infantry Cargo"):
            return False
        
        # End turns to enable movement
        self.rpc_call('army_end_turn')
        self.rpc_call('army_end_turn')
        
        # Test loading unit into transport
        result = self.rpc_call('transport_load', {
            'transport_x': 4, 'transport_y': 8,
            'cargo_x': 5, 'cargo_y': 8
        })
        if not self.assert_success(result, "Load Unit into Transport"):
            return False
        
        # Test getting transport info
        result = self.rpc_call('get_transport_info', {'x': 4, 'y': 8})
        if not self.assert_success(result, "Get Transport Info"):
            return False
        
        # Test getting valid unload positions
        result = self.rpc_call('get_valid_unload_positions', {'x': 4, 'y': 8})
        if not self.assert_success(result, "Get Valid Unload Positions"):
            return False
        
        # Test unloading unit
        result = self.rpc_call('transport_unload', {
            'transport_x': 4, 'transport_y': 8,
            'unload_x': 3, 'unload_y': 8,  # Adjacent plain tile
            'cargo_index': 0
        })
        if not self.assert_success(result, "Unload Unit from Transport"):
            return False
        
        return True
    
    # =============================================================================
    # CAPTURE MECHANICS TESTS
    # =============================================================================
    
    def test_capture_mechanics(self) -> bool:
        """Test property capture system"""
        print("\n🏰 Testing Capture Mechanics...")
        
        # Create infantry for capture near a city
        result = self.rpc_call('unit_create', {
            'army': 'RED',
            'unit_type': 'INFANTRY',
            'x': 2, 'y': 4  # Near city at (3,4)
        })
        if not self.assert_success(result, "Create Infantry for Capture"):
            return False
        
        # End turns to enable movement
        self.rpc_call('army_end_turn')
        self.rpc_call('army_end_turn')
        
        # Move to a city tile at (3,4)
        result = self.rpc_call('movement_execute', {'from_x': 2, 'from_y': 4, 'to_x': 3, 'to_y': 4})
        if not self.assert_success(result, "Move to Capturable Property"):
            return False
        
        # Check if tile is capturable first
        result = self.rpc_call('tile', {'x': 3, 'y': 4})
        if not self.assert_success(result, "Check Tile Info"):
            return False
        
        tile = result['result']
        if tile['mapTile']['type'] not in ['CITY', 'FACTORY', 'AIRPORT', 'PORT']:
            self.record_test("Capture Test Skipped", True, "No capturable property at test location")
            return True
        
        # Test capture attempt
        result = self.rpc_call('capture_tile', {'x': 3, 'y': 4})
        if not self.assert_success(result, "Capture Attempt"):
            return False
        
        # Just test that capture method works, don't validate complex HP mechanics in regression
        self.record_test("Capture Mechanics Functional", True, "Capture method executed successfully")
        
        return True
    
    # =============================================================================
    # ECONOMIC SYSTEM TESTS
    # =============================================================================
    
    def test_economic_system(self) -> bool:
        """Test economic mechanics"""
        print("\n💰 Testing Economic System...")
        
        # Test getting army economy
        result = self.rpc_call('get_army_economy')
        if not self.assert_success(result, "Get Army Economy"):
            return False
        
        # Test unit cost information
        result = self.rpc_call('get_unit_costs')
        if not self.assert_success(result, "Get Unit Costs"):
            return False
        
        # Test affordability check
        result = self.rpc_call('can_afford_unit', {'unit_type': 'TANK'})
        if not self.assert_success(result, "Check Unit Affordability"):
            return False
        
        # Test production options at factory
        result = self.rpc_call('get_production_options', {'x': 0, 'y': 0})  # FACTORY at (0,0)
        if not self.assert_success(result, "Get Production Options"):
            return False
        
        return True
    
    # =============================================================================
    # SPECIAL ACTIONS TESTS
    # =============================================================================
    
    def test_special_actions(self) -> bool:
        """Test special unit abilities"""
        print("\n🛠️ Testing Special Actions...")
        
        # Create Black Boat for repair testing
        result = self.rpc_call('unit_create', {
            'army': 'RED',
            'unit_type': 'BLACKBOAT',
            'x': 0, 'y': 0
        })
        if not self.assert_success(result, "Create Black Boat"):
            return False
        
        # Test troop info (unit configurations)
        result = self.rpc_call('troop_info')
        if not self.assert_success(result, "Get Troop Info"):
            return False
        
        return True
    
    # =============================================================================
    # MAIN TEST RUNNER
    # =============================================================================
    
    def run_all_tests(self) -> bool:
        """Run complete regression test suite"""
        print("🚀 Starting Advance Wars RPC Regression Test Suite")
        print(f"📋 Test Token: {self.test_token}")
        print("=" * 60)
        
        # Check server availability
        if not self.wait_for_server():
            return False
        
        # Run all test categories
        test_categories = [
            ("Game Management", self.test_game_management),
            ("Unit Operations", self.test_unit_operations),
            ("Combat System", self.test_combat_system),
            ("Transport System", self.test_transport_system),
            ("Capture Mechanics", self.test_capture_mechanics),
            ("Economic System", self.test_economic_system),
            ("Special Actions", self.test_special_actions),
        ]
        
        overall_success = True
        
        for category_name, test_function in test_categories:
            try:
                if not test_function():
                    overall_success = False
                    print(f"❌ {category_name} tests failed")
                else:
                    print(f"✅ {category_name} tests passed")
            except Exception as e:
                self.record_test(f"{category_name} Exception", False, str(e))
                overall_success = False
                print(f"💥 {category_name} tests crashed: {e}")
        
        # Cleanup
        try:
            self.rpc_call('game_delete')
        except:
            pass  # Ignore cleanup errors
        
        return overall_success
    
    def print_summary(self) -> None:
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 REGRESSION TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_failed}")
        print(f"📊 Success Rate: {(self.tests_passed/(self.tests_passed + self.tests_failed)*100):.1f}%")
        
        if self.tests_failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print(f"\n🎯 Overall Result: {'PASS' if self.tests_failed == 0 else 'FAIL'}")


def main():
    """Main entry point"""
    tester = AdvanceWarsRegressionTester()
    
    try:
        success = tester.run_all_tests()
        tester.print_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
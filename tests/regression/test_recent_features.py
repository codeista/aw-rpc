#!/usr/bin/env python3
"""
Enhanced Regression Tests for Recent Feature Updates

This test suite validates all recently added features:
- Combat preview enhancements (skip_range_check, hypothetical combat)
- Context menu improvements (Move, Delete, Cancel, Load)
- Turn mechanics (unit locking, transport exceptions)
- Unit delete functionality
- Transport ammo display fixes
"""

import requests
import json
import time
import sys
import os
from typing import Dict, List, Any, Optional

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class RecentFeaturesRegressionTester:
    """Test suite for recently added features"""
    
    def __init__(self, base_url: str = "http://localhost:5000/api"):
        self.base_url = base_url
        self.test_token = f"recent-features-test-{int(time.time())}"
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
    
    def assert_success(self, result: Dict, test_name: str) -> bool:
        """Assert that RPC call was successful"""
        if 'error' in result:
            self.record_test(test_name, False, f"RPC error: {result['error']}")
            return False
        
        if 'result' not in result:
            self.record_test(test_name, False, "No result in response")
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
    
    # =============================================================================
    # COMBAT PREVIEW ENHANCEMENT TESTS
    # =============================================================================
    
    def test_combat_preview_enhancements(self) -> bool:
        """Test enhanced combat preview features"""
        print("\n⚔️  Testing Combat Preview Enhancements...")
        
        # Create units for testing
        # Create a direct unit (TANK)
        result = self.rpc_call('unit_create', {
            'army': 'RED',
            'unit_type': 'TANK',
            'x': 2, 'y': 2
        })
        if not self.assert_success(result, "Create TANK for combat test"):
            return False
            
        # Create an indirect unit (ROCKET) 
        result = self.rpc_call('unit_create', {
            'army': 'BLUE',
            'unit_type': 'ROCKET',
            'x': 6, 'y': 2
        })
        if not self.assert_success(result, "Create ROCKET for combat test"):
            return False
            
        # Create another direct unit (ANTIAIR)
        result = self.rpc_call('unit_create', {
            'army': 'BLUE',
            'unit_type': 'ANTI_AIR',
            'x': 7, 'y': 2
        })
        if not self.assert_success(result, "Create ANTIAIR for combat test"):
            return False
        
        # Test 1: Normal combat preview (should fail due to range)
        result = self.rpc_call('combat_preview', {
            'attacker_x': 2, 'attacker_y': 2,
            'defender_x': 6, 'defender_y': 2
        })
        # This should fail with "out of range"
        if 'error' in result or (result.get('result', {}).get('success') == False):
            self.record_test("Combat preview respects range", True, "Correctly failed for out of range")
        else:
            self.record_test("Combat preview respects range", False, "Should have failed for out of range")
        
        # Test 2: Combat preview with skip_range_check
        result = self.rpc_call('combat_preview', {
            'attacker_x': 2, 'attacker_y': 2,
            'defender_x': 6, 'defender_y': 2,
            'skip_range_check': True
        })
        if not self.assert_success(result, "Combat preview with skip_range_check"):
            return False
            
        # Verify indirect unit shows no counter damage
        damage_info = result.get('result', {}).get('damage', {})
        can_counter = damage_info.get('can_counter', False)
        counter_damage = damage_info.get('counter_damage', 0)
        
        if not can_counter and counter_damage == 0:
            self.record_test("Indirect unit no counter", True, "Correctly shows no counter damage")
        else:
            self.record_test("Indirect unit no counter", False, 
                           f"Indirect unit shows counter: can_counter={can_counter}, damage={counter_damage}")
        
        # Test 3: Direct unit vs direct unit with skip_range_check (should show counter)
        result = self.rpc_call('combat_preview', {
            'attacker_x': 2, 'attacker_y': 2,
            'defender_x': 7, 'defender_y': 2,
            'skip_range_check': True
        })
        if not self.assert_success(result, "Direct vs Direct preview"):
            return False
            
        damage_info = result.get('result', {}).get('damage', {})
        can_counter = damage_info.get('can_counter', False)
        counter_damage = damage_info.get('counter_damage', 0)
        
        if can_counter and counter_damage > 0:
            self.record_test("Direct unit counter damage", True, f"Shows counter damage correctly: {counter_damage}")
        else:
            self.record_test("Direct unit counter damage", False, f"Should show counter damage: can_counter={can_counter}, damage={counter_damage}")
        
        return True
    
    # =============================================================================
    # UNIT DELETE TESTS
    # =============================================================================
    
    def test_unit_delete(self) -> bool:
        """Test unit deletion functionality"""
        print("\n🗑️  Testing Unit Delete...")
        
        # Create units for testing
        result = self.rpc_call('unit_create', {
            'army': 'RED',
            'unit_type': 'INFANTRY',
            'x': 3, 'y': 3
        })
        if not self.assert_success(result, "Create unit for delete test"):
            return False
            
        # Create enemy unit
        result = self.rpc_call('unit_create', {
            'army': 'BLUE',
            'unit_type': 'INFANTRY',
            'x': 4, 'y': 3
        })
        if not self.assert_success(result, "Create enemy unit"):
            return False
        
        # Test 1: Delete own unit
        result = self.rpc_call('unit_delete', {'x': 3, 'y': 3})
        if not self.assert_success(result, "Delete own unit"):
            return False
            
        # Verify unit is gone
        result = self.rpc_call('tile', {'x': 3, 'y': 3})
        if result.get('result', {}).get('unit') is None:
            self.record_test("Unit deleted successfully", True)
        else:
            self.record_test("Unit deleted successfully", False, "Unit still exists")
        
        # Test 2: Try to delete enemy unit (should fail)
        result = self.rpc_call('unit_delete', {'x': 4, 'y': 3})
        if result.get('result', {}).get('success') == False:
            self.record_test("Cannot delete enemy units", True, "Correctly prevented")
        else:
            self.record_test("Cannot delete enemy units", False, "Should not allow deleting enemy units")
        
        # Test 3: Delete non-existent unit
        result = self.rpc_call('unit_delete', {'x': 9, 'y': 9})
        if result.get('result', {}).get('success') == False:
            self.record_test("Delete non-existent unit", True, "Correctly failed")
        else:
            self.record_test("Delete non-existent unit", False, "Should fail for empty tile")
        
        return True
    
    # =============================================================================
    # TURN MECHANICS TESTS
    # =============================================================================
    
    def test_turn_mechanics(self) -> bool:
        """Test unit locking and transport exceptions"""
        print("\n🔄 Testing Turn Mechanics...")
        
        # Create multiple units
        # Unit 1: Infantry
        result = self.rpc_call('unit_create', {
            'army': 'RED',
            'unit_type': 'INFANTRY',
            'x': 0, 'y': 4
        })
        if not self.assert_success(result, "Create Infantry for turn test"):
            return False
            
        # Unit 2: Tank
        result = self.rpc_call('unit_create', {
            'army': 'RED',
            'unit_type': 'TANK',
            'x': 1, 'y': 4
        })
        if not self.assert_success(result, "Create Tank for turn test"):
            return False
            
        # Unit 3: APC (transport)
        result = self.rpc_call('unit_create', {
            'army': 'RED',
            'unit_type': 'APC',
            'x': 2, 'y': 4
        })
        if not self.assert_success(result, "Create APC for turn test"):
            return False
        
        # End turn to enable movement
        self.rpc_call('army_end_turn')
        self.rpc_call('army_end_turn')
        
        # Test 1: Move first unit
        result = self.rpc_call('unit_move', {
            'x': 0, 'y': 4,
            'x2': 0, 'y2': 5
        })
        if not self.assert_success(result, "Move first unit"):
            return False
        
        # Test 2: Move second unit (should lock first unit)
        result = self.rpc_call('unit_move', {
            'x': 1, 'y': 4,
            'x2': 1, 'y2': 5
        })
        if not self.assert_success(result, "Move second unit"):
            return False
        
        # Verify first unit is locked (can't act anymore)
        result = self.rpc_call('unit_capture', {'x': 0, 'y': 5})
        if result.get('result', {}).get('success') == False:
            self.record_test("First unit locked after second acts", True, "Unit correctly locked")
        else:
            self.record_test("First unit locked after second acts", False, "Unit should be locked")
        
        # Test 3: Move APC (transport)
        result = self.rpc_call('unit_move', {
            'x': 2, 'y': 4,
            'x2': 2, 'y2': 5
        })
        if not self.assert_success(result, "Move APC"):
            return False
        
        # Create infantry next to APC for loading test
        result = self.rpc_call('unit_create', {
            'army': 'RED',
            'unit_type': 'INFANTRY',
            'x': 3, 'y': 5
        })
        if not self.assert_success(result, "Create Infantry next to APC"):
            return False
        
        # End turns again
        self.rpc_call('army_end_turn')
        self.rpc_call('army_end_turn')
        
        # Test 4: Load unit into APC after it has moved (transport exception)
        result = self.rpc_call('load_unit', {
            'transport_x': 2, 'transport_y': 5,
            'cargo_x': 3, 'cargo_y': 5
        })
        # APCs should be able to load even after moving
        if self.assert_success(result, "APC can load after moving"):
            self.record_test("Transport exception works", True, "APC loaded unit after moving")
        else:
            self.record_test("Transport exception works", False, "APC should be able to load after moving")
        
        return True
    
    # =============================================================================
    # TRANSPORT DISPLAY TESTS
    # =============================================================================
    
    def test_transport_display(self) -> bool:
        """Test that transports don't show ammo warnings"""
        print("\n🚛 Testing Transport Display...")
        
        # Get board state
        result = self.rpc_call('game_board')
        if not self.assert_success(result, "Get game board"):
            return False
            
        board = result['result']
        
        # Find any APC or LANDER units
        transports_found = []
        for tile in board.get('grid', []):
            if tile.get('unit'):
                unit = tile['unit']
                if unit['type'] in ['APC', 'LANDER']:
                    transports_found.append({
                        'type': unit['type'],
                        'x': tile['x'],
                        'y': tile['y'],
                        'ammo': unit.get('status', {}).get('ammo', 0),
                        'rangemax': unit.get('rangemax', 0)
                    })
        
        if transports_found:
            for transport in transports_found:
                # Verify transport has ammo=0 and rangemax=0
                if transport['ammo'] == 0 and transport['rangemax'] == 0:
                    self.record_test(f"{transport['type']} has correct ammo/range", True, 
                                   f"ammo={transport['ammo']}, range={transport['rangemax']}")
                else:
                    self.record_test(f"{transport['type']} has correct ammo/range", False,
                                   f"ammo={transport['ammo']}, range={transport['rangemax']}")
        else:
            # Create transport to test
            result = self.rpc_call('unit_create', {
                'army': 'RED',
                'unit_type': 'APC',
                'x': 5, 'y': 5
            })
            if self.assert_success(result, "Create APC for display test"):
                # Check its properties
                result = self.rpc_call('tile', {'x': 5, 'y': 5})
                if result.get('result', {}).get('unit'):
                    unit = result['result']['unit']
                    ammo = unit.get('status', {}).get('ammo', -1)
                    rangemax = unit.get('rangemax', -1)
                    if ammo == 0 and rangemax == 0:
                        self.record_test("APC ammo/range display", True, "No ammo warnings should show")
                    else:
                        self.record_test("APC ammo/range display", False, f"ammo={ammo}, range={rangemax}")
        
        return True
    
    # =============================================================================
    # MAIN TEST RUNNER
    # =============================================================================
    
    def run_all_tests(self) -> bool:
        """Run all recent feature tests"""
        print("🚀 Starting Recent Features Regression Test Suite")
        print(f"📋 Test Token: {self.test_token}")
        print("=" * 60)
        
        # Initialize game
        result = self.rpc_call('game_create_test', {'use_optimized': True})
        if not self.assert_success(result, "Game Creation"):
            return False
        
        # Run test categories
        test_categories = [
            ("Combat Preview Enhancements", self.test_combat_preview_enhancements),
            ("Unit Delete", self.test_unit_delete),
            ("Turn Mechanics", self.test_turn_mechanics),
            ("Transport Display", self.test_transport_display),
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
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 RECENT FEATURES TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_failed}")
        print(f"📊 Success Rate: {(self.tests_passed / (self.tests_passed + self.tests_failed) * 100):.1f}%")
        
        # Cleanup
        try:
            self.rpc_call('game_delete')
        except:
            pass
        
        return overall_success
    
    def print_summary(self):
        """Print detailed test summary"""
        print("\n📋 Detailed Test Results:")
        print("-" * 60)
        for result in self.test_results:
            status = "✅" if result['passed'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")


def main():
    """Main entry point"""
    tester = RecentFeaturesRegressionTester()
    
    success = tester.run_all_tests()
    tester.print_summary()
    
    if success:
        print("\n🎯 Overall Result: PASS")
        return 0
    else:
        print("\n🎯 Overall Result: FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
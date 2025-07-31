#!/usr/bin/env python3
"""
Test All Game Interactions
Comprehensive test suite for every game mechanic and interaction
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import requests
import json
import time

def rpc_call(method: str, params: dict = None) -> dict:
    """Make RPC call to the server"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    }
    
    try:
        response = requests.post("http://localhost:5000/api", json=payload)
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
        
        result = response.json()
        if "error" in result:
            return {"error": result["error"]}
        
        return result.get("result", result)
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

class ComprehensiveGameTest:
    def __init__(self):
        self.token = "comp_test_full"
        self.passed = 0
        self.failed = 0
        self.tests_run = 0
    
    def setup_game(self):
        """Create game with comprehensive map"""
        result = rpc_call("game_create_v2", {
            "token": self.token,
            "map_name": "comprehensive_test"
        })
        
        if "error" in result:
            print(f"❌ Failed to create game: {result['error']}")
            return False
        
        print("✅ Created game with comprehensive map")
        return True
    
    def end_turn(self):
        """End current turn"""
        rpc_call("army_end_turn", {"token": self.token})
    
    def test_com_tower_mechanics(self):
        """Test COM_TOWER damage bonus system"""
        print("\n🗼 Testing COM_TOWER Mechanics...")
        
        # Create infantry to capture COM_TOWER
        infantry = rpc_call("unit_create", {
            "token": self.token,
            "army": "RED",
            "unit_type": "INFANTRY",
            "x": 4, "y": 1  # Factory
        })
        
        # Create enemy tank
        tank = rpc_call("unit_create", {
            "token": self.token,
            "army": "BLUE",
            "unit_type": "TANK",
            "x": 11, "y": 1  # Factory
        })
        
        # End turns to enable movement
        self.end_turn()
        self.end_turn()
        
        # Move infantry to COM_TOWER at (4,3)
        move = rpc_call("unit_move", {
            "token": self.token,
            "x": 4, "y": 1,
            "x2": 4, "y": 3
        })
        
        # Get damage preview before capture
        preview1 = rpc_call("combat_preview", {
            "token": self.token,
            "attacker_x": 4, "attacker_y": 1,
            "defender_x": 11, "defender_y": 1
        })
        
        base_damage = preview1.get('preview', {}).get('attacker_damage', 0)
        print(f"   Base damage (no COM_TOWER): {base_damage}%")
        
        # Capture COM_TOWER
        capture = rpc_call("unit_capture", {
            "token": self.token,
            "x": 4, "y": 3
        })
        
        if "error" not in capture:
            print("   ✅ Started capturing COM_TOWER")
            
            # Complete capture over multiple turns
            for i in range(3):
                self.end_turn()
                self.end_turn()
                capture = rpc_call("unit_capture", {
                    "token": self.token,
                    "x": 4, "y": 3
                })
            
            # Create new tank to test damage with COM_TOWER
            tank2 = rpc_call("unit_create", {
                "token": self.token,
                "army": "RED",
                "unit_type": "TANK",
                "x": 4, "y": 1
            })
            
            # Get damage with COM_TOWER
            preview2 = rpc_call("combat_preview", {
                "token": self.token,
                "attacker_x": 4, "attacker_y": 1,
                "defender_x": 11, "defender_y": 1  
            })
            
            boosted_damage = preview2.get('preview', {}).get('attacker_damage', 0)
            print(f"   Boosted damage (with COM_TOWER): {boosted_damage}%")
            
            if boosted_damage > base_damage:
                print("   ✅ COM_TOWER damage bonus working!")
                self.passed += 1
            else:
                print("   ❌ COM_TOWER damage bonus not applied")
                self.failed += 1
        else:
            print(f"   ❌ Failed to capture COM_TOWER: {capture['error']}")
            self.failed += 1
        
        self.tests_run += 1
    
    def test_missile_silo(self):
        """Test MISSILE_SILO one-time attack"""
        print("\n🚀 Testing MISSILE_SILO...")
        
        # Get missile silo location (7,5) or (8,5)
        board = rpc_call("game_board", {"token": self.token})
        
        # Create infantry to capture silo
        infantry = rpc_call("unit_create", {
            "token": self.token,
            "army": "RED",
            "unit_type": "INFANTRY",
            "x": 4, "y": 10  # Factory
        })
        
        # TODO: Implement missile silo launch test
        print("   ⚠️  MISSILE_SILO test pending implementation")
        self.tests_run += 1
    
    def test_lab_mechanics(self):
        """Test LAB special mechanics"""
        print("\n🔬 Testing LAB Mechanics...")
        
        # LABs at (6,6) and (9,6)
        # TODO: Implement LAB mechanics test
        print("   ⚠️  LAB mechanics test pending (feature not implemented)")
        self.tests_run += 1
    
    def test_river_movement(self):
        """Test river movement restrictions"""
        print("\n🌊 Testing River Movement...")
        
        # Create different unit types to test river crossing
        units = [
            ("INFANTRY", True),   # Can cross rivers slowly
            ("TANK", False),      # Cannot cross rivers
            ("RECON", False),     # Cannot cross rivers
        ]
        
        test_passed = True
        
        for unit_type, can_cross in units:
            # Create unit near river
            unit = rpc_call("unit_create", {
                "token": self.token,
                "army": "RED",
                "unit_type": unit_type,
                "x": 5, "y": 10  # Near river
            })
            
            if "error" not in unit:
                # Try to move across river
                # Rivers are at row 6 and 7
                # TODO: Test actual river crossing
                print(f"   ⚠️  {unit_type} river test pending")
        
        self.tests_run += 1
    
    def test_pipe_movement(self):
        """Test pipe movement for piperunners"""
        print("\n🔧 Testing Pipe Movement...")
        
        # Pipes at (7,7) and (8,7)
        # Only PIPERUNNER can move on pipes
        
        # TODO: Create PIPERUNNER and test pipe movement
        print("   ⚠️  Pipe movement test pending (PIPERUNNER implementation)")
        self.tests_run += 1
    
    def test_transport_mechanics(self):
        """Test all transport loading/unloading"""
        print("\n🚛 Testing Transport Mechanics...")
        
        # Test APC transport
        apc = rpc_call("unit_create", {
            "token": self.token,
            "army": "RED",
            "unit_type": "APC",
            "x": 0, "y": 10  # Factory
        })
        
        infantry = rpc_call("unit_create", {
            "token": self.token,
            "army": "RED",
            "unit_type": "INFANTRY",
            "x": 1, "y": 10
        })
        
        # End turns
        self.end_turn()
        self.end_turn()
        
        # Load infantry into APC
        load_result = rpc_call("transport_load", {
            "token": self.token,
            "unit_x": 1, "unit_y": 10,
            "transport_x": 0, "transport_y": 10
        })
        
        if "error" not in load_result:
            print("   ✅ Successfully loaded INFANTRY into APC")
            self.passed += 1
        else:
            print(f"   ❌ Failed to load unit: {load_result['error']}")
            self.failed += 1
        
        self.tests_run += 1
    
    def test_combat_interactions(self):
        """Test various combat scenarios"""
        print("\n⚔️ Testing Combat Interactions...")
        
        # Test direct combat
        tank1 = rpc_call("unit_create", {
            "token": self.token,
            "army": "RED",
            "unit_type": "TANK",
            "x": 0, "y": 1
        })
        
        tank2 = rpc_call("unit_create", {
            "token": self.token,
            "army": "BLUE",
            "unit_type": "TANK",
            "x": 2, "y": 1
        })
        
        # Get combat preview
        preview = rpc_call("combat_preview", {
            "token": self.token,
            "attacker_x": 0, "attacker_y": 1,
            "defender_x": 2, "defender_y": 1
        })
        
        if "preview" in preview:
            damage = preview['preview']['attacker_damage']
            counter = preview['preview']['counter_damage']
            print(f"   ✅ Combat preview: {damage}% damage, {counter}% counter")
            self.passed += 1
        else:
            print("   ❌ Failed to get combat preview")
            self.failed += 1
        
        self.tests_run += 1
    
    def test_production_at_all_facilities(self):
        """Test unit production at each facility type"""
        print("\n🏭 Testing Production at All Facilities...")
        
        # Test factory production
        infantry = rpc_call("unit_create", {
            "token": self.token,
            "army": "RED",
            "unit_type": "INFANTRY",
            "x": 4, "y": 1  # Factory
        })
        
        if "error" not in infantry:
            print("   ✅ Factory production working")
            self.passed += 1
        else:
            self.failed += 1
        
        # Test airport production
        tcopter = rpc_call("unit_create", {
            "token": self.token,
            "army": "RED",
            "unit_type": "TCOPTER",
            "x": 2, "y": 9  # Airport
        })
        
        if "error" not in tcopter:
            print("   ✅ Airport production working")
            self.passed += 1
        else:
            self.failed += 1
        
        # Test port production
        lander = rpc_call("unit_create", {
            "token": self.token,
            "army": "RED",
            "unit_type": "LANDER",
            "x": 0, "y": 0  # Port
        })
        
        if "error" not in lander:
            print("   ✅ Port production working")
            self.passed += 1
        else:
            self.failed += 1
        
        self.tests_run += 3
    
    def test_terrain_effects(self):
        """Test terrain defense bonuses"""
        print("\n🏔️ Testing Terrain Effects...")
        
        # Create units on different terrain
        # Mountain at (3,3), (12,3)
        # Woods at (2,4), (13,4)
        
        infantry_plain = rpc_call("unit_create", {
            "token": self.token,
            "army": "RED",
            "unit_type": "INFANTRY",
            "x": 5, "y": 5  # Plain
        })
        
        infantry_mountain = rpc_call("unit_create", {
            "token": self.token,
            "army": "BLUE", 
            "unit_type": "INFANTRY",
            "x": 3, "y": 3  # Mountain
        })
        
        # Compare defense values
        # TODO: Get actual defense calculations
        print("   ⚠️  Terrain defense test pending full implementation")
        self.tests_run += 1
    
    def test_victory_conditions(self):
        """Test different victory conditions"""
        print("\n🏆 Testing Victory Conditions...")
        
        # Test HQ capture victory
        # HQs at (1,5) for RED and (14,5) for BLUE
        
        # TODO: Implement HQ capture test
        print("   ⚠️  Victory condition tests pending")
        self.tests_run += 1
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🎮 Comprehensive Game Interaction Tests")
        print("=" * 60)
        
        if not self.setup_game():
            return
        
        # Run all test categories
        self.test_com_tower_mechanics()
        self.test_missile_silo()
        self.test_lab_mechanics()
        self.test_river_movement()
        self.test_pipe_movement()
        self.test_transport_mechanics()
        self.test_combat_interactions()
        self.test_production_at_all_facilities()
        self.test_terrain_effects()
        self.test_victory_conditions()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⚠️  Pending: {self.tests_run - self.passed - self.failed}")
        print(f"📈 Total Tests: {self.tests_run}")
        
        success_rate = (self.passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n📊 Success Rate: {success_rate:.1f}%")
        
        if self.failed == 0:
            print("\n🎉 All implemented tests passed!")
        else:
            print(f"\n⚠️ {self.failed} test(s) failed")

if __name__ == "__main__":
    # Check server
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code != 200:
            print("❌ Server not accessible")
            exit(1)
    except:
        print("❌ Server not running. Start with: python3 app.py")
        exit(1)
    
    tester = ComprehensiveGameTest()
    tester.run_all_tests()
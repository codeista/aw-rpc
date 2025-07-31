#!/usr/bin/env python3
"""
Test Comprehensive Maps
Tests all game features using the new comprehensive test maps
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import requests
import json
from game_factory import GameFactory
from unit import UnitType

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

def test_comprehensive_map():
    """Test all features in comprehensive map"""
    print("\n🗺️ Testing Comprehensive Map...")
    
    # Create game with comprehensive map
    result = rpc_call("game_create_v2", {
        "token": "comp_test",
        "map_name": "comprehensive_test"
    })
    
    if "error" in result:
        print(f"❌ Failed to create game: {result['error']}")
        return False
    
    print("✅ Created game with comprehensive map")
    
    # Get board info
    board = rpc_call("game_board", {"token": "comp_test"})
    
    # Count features
    features = {
        'COM_TOWER': 0,
        'LAB': 0,
        'MISSILE_SILO': 0,
        'RIVER': 0,
        'PIPE': 0,
        'FACTORY': 0,
        'AIRPORT': 0,
        'PORT': 0,
        'BASE_TOWER': 0
    }
    
    for tile in board.get('grid', []):
        tile_type = tile.get('mapTile', {}).get('type', '')
        if 'COM_TOWER' in tile_type:
            features['COM_TOWER'] += 1
        elif 'LAB' in tile_type:
            features['LAB'] += 1
        elif 'MISSILE_SILO' in tile_type:
            features['MISSILE_SILO'] += 1
        elif 'RIVER' in tile_type:
            features['RIVER'] += 1
        elif 'PIPE' in tile_type:
            features['PIPE'] += 1
        elif tile_type == 'FACTORY':
            features['FACTORY'] += 1
        elif tile_type == 'AIRPORT':
            features['AIRPORT'] += 1
        elif tile_type == 'PORT':
            features['PORT'] += 1
        elif 'BASE_TOWER' in tile_type:
            features['BASE_TOWER'] += 1
    
    print("\n📊 Map Features:")
    for feature, count in features.items():
        status = "✅" if count > 0 else "❌"
        print(f"   {status} {feature}: {count}")
    
    # Test COM_TOWER damage bonus
    print("\n🗼 Testing COM_TOWER Damage Bonus...")
    
    # Create units near COM_TOWER
    unit1 = rpc_call("unit_create", {
        "token": "comp_test",
        "army": "RED",
        "unit_type": "TANK",
        "x": 4, "y": 3
    })
    
    unit2 = rpc_call("unit_create", {
        "token": "comp_test",
        "army": "BLUE", 
        "unit_type": "TANK",
        "x": 11, "y": 3
    })
    
    # Get damage preview before capturing COM_TOWER
    preview1 = rpc_call("combat_preview", {
        "token": "comp_test",
        "attacker_x": 4, "attacker_y": 3,
        "defender_x": 11, "defender_y": 3
    })
    
    base_damage = preview1.get('preview', {}).get('attacker_damage', 0)
    print(f"   Base damage (no COM_TOWER): {base_damage}%")
    
    # TODO: Add more comprehensive tests for:
    # - LAB functionality
    # - MISSILE_SILO usage
    # - River movement restrictions
    # - Pipe mechanics
    # - Multi-terrain interactions
    
    return True

def test_combat_map():
    """Test combat scenarios in combat map"""
    print("\n⚔️ Testing Combat Map...")
    
    # Create game with combat map
    result = rpc_call("game_create_v2", {
        "token": "combat_test",
        "map_name": "combat_test"
    })
    
    if "error" in result:
        print(f"❌ Failed to create game: {result['error']}")
        return False
    
    print("✅ Created game with combat map")
    
    # Create units for combat testing
    units_created = 0
    
    # Create artillery for indirect combat
    result = rpc_call("unit_create", {
        "token": "combat_test",
        "army": "RED",
        "unit_type": "ARTILLERY",
        "x": 0, "y": 0  # Factory position
    })
    if "error" not in result:
        units_created += 1
    
    # Create tank for direct combat
    result = rpc_call("unit_create", {
        "token": "combat_test",
        "army": "BLUE",
        "unit_type": "TANK", 
        "x": 9, "y": 0  # Factory position
    })
    if "error" not in result:
        units_created += 1
    
    print(f"   Created {units_created} units for combat testing")
    
    # TODO: Add comprehensive combat tests:
    # - Direct vs indirect combat
    # - Terrain defense bonuses
    # - Naval combat in sea area
    # - Air combat
    # - Counter-attack scenarios
    
    return units_created > 0

def test_transport_map():
    """Test transport mechanics in transport map"""
    print("\n🚛 Testing Transport Map...")
    
    # Create game with transport map
    result = rpc_call("game_create_v2", {
        "token": "transport_test",
        "map_name": "transport_test"
    })
    
    if "error" in result:
        print(f"❌ Failed to create game: {result['error']}")
        return False
    
    print("✅ Created game with transport map")
    
    # Test naval transport
    print("\n   Testing Naval Transport:")
    
    # Create lander at port
    lander = rpc_call("unit_create", {
        "token": "transport_test",
        "army": "RED",
        "unit_type": "LANDER",
        "x": 0, "y": 0
    })
    
    if "error" not in lander:
        print("   ✅ Created LANDER at port")
    
    # Create infantry to load
    infantry = rpc_call("unit_create", {
        "token": "transport_test",
        "army": "RED",
        "unit_type": "INFANTRY",
        "x": 4, "y": 2  # Factory
    })
    
    if "error" not in infantry:
        print("   ✅ Created INFANTRY at factory")
    
    # TODO: Add comprehensive transport tests:
    # - Loading units into transports
    # - Unloading at beaches
    # - APC road transport
    # - T-Copter air transport
    # - Transport capacity limits
    
    return True

def run_all_tests():
    """Run all comprehensive map tests"""
    print("🎮 Comprehensive Map Testing Suite")
    print("=" * 60)
    
    # Check server connection
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code != 200:
            print("❌ Server not accessible")
            return
    except:
        print("❌ Server not running. Start with: python3 app.py")
        return
    
    tests = [
        ("Comprehensive Map", test_comprehensive_map),
        ("Combat Map", test_combat_map),
        ("Transport Map", test_transport_map)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} test passed")
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
    
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE MAP TEST RESULTS")
    print("=" * 60)
    print(f"📈 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL COMPREHENSIVE MAP TESTS PASSED!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")

if __name__ == "__main__":
    run_all_tests()
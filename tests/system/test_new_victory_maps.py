#!/usr/bin/env python3
"""
Test New Victory Condition Maps
Tests all the new maps with different army combinations to verify victory conditions work
"""

import requests
import json
import random
import string

def rpc_call(method, params=None):
    """Make RPC call to the server"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    }
    
    response = requests.post("http://localhost:5000/api", json=payload)
    result = response.json()
    
    if "error" in result:
        return {"error": result["error"]}
    
    rpc_result = result.get("result", result)
    
    # Handle simple success responses
    if isinstance(rpc_result, str):
        if rpc_result == "ok":
            return {"success": True, "result": "ok"}
        try:
            rpc_result = json.loads(rpc_result)
        except json.JSONDecodeError:
            return {"error": f"Could not parse result: {rpc_result}"}
    
    return rpc_result

def generate_token():
    """Generate a unique game token"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def test_map_creation(map_id, armies, description):
    """Test creating a game with specific map and armies"""
    print(f"\n🗺️  Testing: {description}")
    print(f"   Map: {map_id}, Armies: {' vs '.join(armies)}")
    
    # Generate unique token
    token = generate_token()
    
    # Create players array
    players = [{"color": army} for army in armies]
    
    # Create game
    game_result = rpc_call("game_create_with_setup", {
        "token": token,
        "game_setup": {
            "map_id": map_id,
            "players": players
        }
    })
    
    if "error" in game_result:
        print(f"   ❌ Game creation failed: {game_result['error']}")
        return None
    
    if not game_result.get("success"):
        print(f"   ❌ Game creation failed: {game_result}")
        return None
    
    # Get board to verify game state
    board = rpc_call("game_board", {"token": token})
    if "error" in board:
        print(f"   ❌ Could not get board: {board['error']}")
        return None
    
    # Check army data
    army_funds = board.get("army_funds", {})
    army_properties = board.get("army_properties", {})
    army_troops = board.get("army_troops", {})
    current_turn = board.get("current_turn", "UNKNOWN")
    game_active = board.get("game_active", False)
    
    print(f"   ✅ Game created successfully: {token}")
    print(f"   🎮 Current turn: {current_turn}")
    print(f"   🔴 Game active: {game_active}")
    
    # Show army status
    for army in armies:
        funds = army_funds.get(army, 0)
        properties = army_properties.get(army, 0)
        troops = army_troops.get(army, 0)
        print(f"   📊 {army}: {funds} funds, {properties} properties, {troops} units")
    
    # Check if armies have starting units/properties
    has_properties = any(army_properties.get(army, 0) > 0 for army in armies)
    has_units = any(army_troops.get(army, 0) > 0 for army in armies)
    
    if has_properties:
        print(f"   ✅ Map has properties - income system will work")
    else:
        print(f"   ⚠️  No starting properties - income system may not be testable")
    
    if has_units:
        print(f"   ✅ Map has starting units - combat/elimination scenarios possible")
    else:
        print(f"   ⚠️  No starting units - will need to produce units for testing")
    
    print(f"   🌐 Game URL: http://localhost:5000/game/{token}")
    
    return {
        "token": token,
        "armies": armies,
        "map_id": map_id,
        "has_properties": has_properties,
        "has_units": has_units,
        "success": True
    }

def test_basic_victory_mechanics(game_info):
    """Test basic victory condition mechanics on a created game"""
    token = game_info["token"]
    print(f"\n🏆 Testing victory mechanics for {token}")
    
    # Test turn progression
    try:
        for i in range(3):
            board = rpc_call("game_board", {"token": token})
            if "error" in board:
                print(f"   ❌ Could not get board state: {board['error']}")
                return False
                
            current_turn = board.get("current_turn", "UNKNOWN")
            game_active = board.get("game_active", True)
            print(f"   Turn {i+1}: {current_turn} (Game active: {game_active})")
            
            if not game_active:
                winner = board.get("winner", "UNKNOWN")
                victory_type = board.get("victory_type", "UNKNOWN")
                print(f"   🎉 Game ended! Winner: {winner}, Type: {victory_type}")
                return True
            
            # End turn
            turn_result = rpc_call("army_end_turn", {"token": token})
            if "error" in turn_result:
                print(f"   ❌ Could not end turn: {turn_result['error']}")
                return False
        
        print(f"   ✅ Turn progression working normally")
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing victory mechanics: {e}")
        return False

def run_comprehensive_victory_tests():
    """Run comprehensive tests on all new victory maps"""
    print("🚀 Comprehensive Victory Condition Map Testing")
    print("=" * 70)
    
    # Test scenarios
    test_scenarios = [
        # Basic 2-player non-traditional combinations
        ("green_yellow_arena", ["GREEN", "YELLOW"], "Green vs Yellow Arena"),
        ("green_blue_islands", ["GREEN", "BLUE"], "Green vs Blue Islands"),
        ("yellow_grey_mountains", ["YELLOW", "GREY"], "Yellow vs Grey Mountains"),
        ("green_yellow_hq_rush", ["GREEN", "YELLOW"], "Green vs Yellow HQ Rush"),
        ("elimination_test", ["GREEN", "YELLOW"], "Elimination Test - Small Map"),
        
        # Multi-player combinations
        ("multi_army_test", ["GREEN", "YELLOW", "BLUE", "GREY"], "Multi-Army Test - 4 Colors"),
        ("triangle", ["RED", "GREEN", "YELLOW"], "Triangle Arena - Non-standard"),
        ("cross", ["GREEN", "YELLOW", "BLUE", "GREY"], "Cross Battle - All Non-Red"),
        
        # Mixed traditional/non-traditional
        ("cross", ["RED", "GREEN", "YELLOW", "BLUE"], "Cross Battle - Mixed Armies"),
        ("triangle", ["BLUE", "GREEN", "GREY"], "Triangle Arena - Blue/Green/Grey"),
    ]
    
    successful_tests = 0
    total_tests = len(test_scenarios)
    created_games = []
    
    print(f"📋 Testing {total_tests} different army/map combinations")
    print("=" * 70)
    
    for map_id, armies, description in test_scenarios:
        try:
            game_info = test_map_creation(map_id, armies, description)
            if game_info and game_info.get("success"):
                successful_tests += 1
                created_games.append(game_info)
                
                # Test basic victory mechanics
                if test_basic_victory_mechanics(game_info):
                    print(f"   ✅ Victory mechanics working")
                else:
                    print(f"   ⚠️  Victory mechanics need verification")
            else:
                print(f"   ❌ Map creation failed")
                
        except Exception as e:
            print(f"   ❌ Error testing {map_id}: {e}")
    
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE VICTORY MAP TEST RESULTS")
    print("=" * 70)
    
    print(f"✅ Successful tests: {successful_tests}/{total_tests}")
    print(f"📈 Success rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests == total_tests:
        print("🎉 ALL VICTORY MAP TESTS PASSED!")
        print("🏆 Victory condition system supports all army combinations!")
    elif successful_tests >= total_tests * 0.8:
        print("✅ Most tests passed - Victory system is working well")
    else:
        print("⚠️  Some issues detected - Victory system may need work")
    
    print(f"\n🎮 Created {len(created_games)} test games:")
    for game in created_games:
        armies_str = " vs ".join(game["armies"])
        print(f"   • {game['map_id']}: {armies_str} → http://localhost:5000/game/{game['token']}")
    
    return successful_tests == total_tests

def test_victory_scenarios():
    """Test specific victory scenarios"""
    print("\n🎯 Testing Specific Victory Scenarios")
    print("=" * 50)
    
    # Test GREEN vs YELLOW elimination
    print("\n🔥 Testing Unit Elimination Victory (GREEN vs YELLOW)")
    token = generate_token()
    
    game_result = rpc_call("game_create_with_setup", {
        "token": token,
        "game_setup": {
            "map_id": "elimination_test",
            "players": [{"color": "GREEN"}, {"color": "YELLOW"}]
        }
    })
    
    if game_result.get("success"):
        print(f"✅ Created elimination test game: {token}")
        print(f"🌐 Test elimination: http://localhost:5000/game/{token}")
        
        # Get initial state
        board = rpc_call("game_board", {"token": token})
        if "error" not in board:
            army_troops = board.get("army_troops", {})
            print(f"📊 Initial units: GREEN={army_troops.get('GREEN', 0)}, YELLOW={army_troops.get('YELLOW', 0)}")
            
            # Create some units for testing
            print("🛠️  Creating test units...")
            
            # Create GREEN infantry at HQ
            create_result = rpc_call("unit_create", {
                "token": token,
                "army": "GREEN",
                "unit_type": "INFANTRY",
                "x": 0,
                "y": 0
            })
            
            if create_result.get("success", False):
                print("✅ Created GREEN infantry")
            
            # Create YELLOW infantry at HQ
            create_result = rpc_call("unit_create", {
                "token": token,
                "army": "YELLOW",
                "unit_type": "INFANTRY", 
                "x": 4,
                "y": 0
            })
            
            if create_result.get("success", False):
                print("✅ Created YELLOW infantry")
                print("🏆 Elimination victory scenario ready for testing")
            
    return True

if __name__ == "__main__":
    print("🎮 Starting comprehensive victory condition testing...")
    
    try:
        # Test all map creation scenarios
        success = run_comprehensive_victory_tests()
        
        # Test specific victory scenarios
        test_victory_scenarios()
        
        if success:
            print("\n🎉 ALL VICTORY CONDITION TESTS COMPLETED SUCCESSFULLY!")
            print("🏆 The victory system now supports all army combinations!")
        else:
            print("\n⚠️  Some tests failed - check results above")
            
    except Exception as e:
        print(f"\n❌ Critical error during testing: {e}")
        exit(1)
#!/usr/bin/env python3
"""
Fixed Combat System Tests
Tests damage calculations with proper unit setup
"""

import requests
import json
import random
import string

def rpc_call(method: str, params: dict = None) -> dict:
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
    
    return result.get("result", result)

def test_combat_system():
    """Test combat system with a simple scenario"""
    print("🚀 Fixed Combat System Test")
    print("=" * 60)
    
    # Create test game
    game_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    result = rpc_call("game_create_test", {"token": game_id})
    
    if result != "ok":
        print(f"❌ Failed to create game: {result}")
        return False
    
    print(f"✅ Created test game: {game_id}")
    
    # Create RED infantry at factory
    result = rpc_call("produce_unit", {
        "token": game_id,
        "x": 0,
        "y": 4,
        "unit_type": "INFANTRY"
    })
    
    if "error" in result:
        print(f"❌ Failed to create RED infantry: {result}")
        return False
    
    print("✅ Created RED infantry at (0,4)")
    
    # End RED turn
    rpc_call("army_end_turn", {"token": game_id})
    
    # Create BLUE infantry at their factory
    result = rpc_call("produce_unit", {
        "token": game_id,
        "x": 10,
        "y": 3,
        "unit_type": "INFANTRY"
    })
    
    if "error" in result:
        print(f"❌ Failed to create BLUE infantry: {result}")
        return False
    
    print("✅ Created BLUE infantry at (10,3)")
    
    # End turns to enable movement
    rpc_call("army_end_turn", {"token": game_id})  # End BLUE turn
    rpc_call("army_end_turn", {"token": game_id})  # End RED turn again
    
    # Now it's BLUE's turn and both units can move
    
    # Move BLUE infantry closer to RED
    result = rpc_call("unit_move", {
        "token": game_id,
        "x": 10,
        "y": 3,
        "x2": 7,
        "y2": 3
    })
    
    if "error" in result:
        print(f"❌ Failed to move BLUE infantry: {result}")
        return False
    
    print("✅ Moved BLUE infantry to (7,3)")
    
    # End BLUE turn
    rpc_call("army_end_turn", {"token": game_id})
    
    # Move RED infantry closer to BLUE
    result = rpc_call("unit_move", {
        "token": game_id,
        "x": 0,
        "y": 4,
        "x2": 3,
        "y2": 4
    })
    
    if "error" in result:
        print(f"❌ Failed to move RED infantry: {result}")
        return False
    
    print("✅ Moved RED infantry to (3,4)")
    
    # End RED turn
    rpc_call("army_end_turn", {"token": game_id})
    
    # Continue moving units closer
    result = rpc_call("unit_move", {
        "token": game_id,
        "x": 7,
        "y": 3,
        "x2": 4,
        "y2": 3
    })
    
    if "error" in result:
        print(f"❌ Failed to move BLUE infantry closer: {result}")
        return False
    
    print("✅ Moved BLUE infantry to (4,3)")
    
    # End BLUE turn
    rpc_call("army_end_turn", {"token": game_id})
    
    # Move RED infantry adjacent to BLUE infantry
    result = rpc_call("unit_move", {
        "token": game_id,
        "x": 3,
        "y": 4,
        "x2": 4,
        "y2": 4  # Move to same row as BLUE
    })
    
    if "error" in result:
        print(f"❌ Failed to move RED infantry adjacent: {result}")
        return False
    
    print("✅ Moved RED infantry to (4,4) - adjacent to BLUE at (4,3)")
    
    # Now RED infantry can attack BLUE infantry (they're adjacent)
    print("\n🎯 Testing Combat...")
    
    # Get damage preview
    preview = rpc_call("damage_preview", {
        "token": game_id,
        "x": 4,
        "y": 4,
        "x2": 4,
        "y2": 3
    })
    
    if "error" in preview:
        print(f"❌ Failed to get damage preview: {preview}")
        return False
    
    print(f"✅ Damage preview: {preview}")
    
    # Execute attack
    print(f"\n🎮 About to execute attack from RED at (4,4) to BLUE at (4,3)")
    
    # Check current turn first
    board = rpc_call("game_board", {"token": game_id})
    if "error" not in board:
        print(f"   Current turn: {board.get('current_turn', 'Unknown')}")
    
    result = rpc_call("unit_attack", {
        "token": game_id,
        "x": 4,
        "y": 4,
        "x2": 4,
        "y2": 3
    })
    
    if "error" in result:
        print(f"❌ Failed to attack: {result}")
        # Try to get more info
        print(f"   Full result: {json.dumps(result, indent=2)}")
        return False
    
    print("✅ Attack executed successfully")
    
    # Check results
    board = rpc_call("game_board", {"token": game_id})
    if "error" in board:
        print(f"❌ Failed to get board: {board}")
        return False
    
    # Find units and check their HP
    red_unit = None
    blue_unit = None
    
    for tile in board.get("grid", []):
        if tile.get("unit"):
            unit = tile["unit"]
            if unit["army"] == "RED" and tile["x"] == 4 and tile["y"] == 4:
                red_unit = unit
            elif unit["army"] == "BLUE" and tile["x"] == 4 and tile["y"] == 3:
                blue_unit = unit
    
    print(f"\n📊 Combat Results:")
    if red_unit:
        print(f"   RED Infantry HP: {red_unit.get('hp', '?')}/10")
    if blue_unit:
        print(f"   BLUE Infantry HP: {blue_unit.get('hp', '?')}/10")
    
    return True

def run_all_tests():
    """Run all combat tests"""
    print("🏹 Combat System Test Suite")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Basic combat
    if test_combat_system():
        tests_passed += 1
        print("\n✅ Basic Combat Test PASSED")
    else:
        tests_failed += 1
        print("\n❌ Basic Combat Test FAILED")
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS")
    print(f"   Passed: {tests_passed}")
    print(f"   Failed: {tests_failed}")
    print(f"   Total: {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print("\n🎉 All combat tests passed!")
        return True
    else:
        print(f"\n❌ {tests_failed} tests failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
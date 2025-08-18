"""
Test that unit states properly reset at turn boundaries
This test specifically checks for the bug where units remained "done" after turn cycles
"""

import requests
import json
import time

API_URL = "http://localhost:5000/api"

def rpc_call(method, params):
    """Make an RPC call to the game server"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    response = requests.post(API_URL, json=payload)
    result = response.json()
    if "error" in result:
        raise Exception(f"RPC Error: {result['error']}")
    return result.get("result")

def test_unit_state_reset_on_turn():
    """Test that unit states properly reset when their turn comes around again"""
    
    print("\n🧪 Testing Unit State Reset on Turn Cycle")
    print("=" * 60)
    
    # Create a test game
    token = f"test-turn-reset-{int(time.time())}"
    result = rpc_call("game_create_test", {"token": token})
    print(f"✅ Created test game: {token}")
    
    # Get initial board state
    board = rpc_call("game_board", {"token": token})
    current_player = board["current_player"]
    print(f"✅ Starting player: {current_player}")
    
    # Create a unit for player 0
    unit_result = rpc_call("unit_create", {
        "token": token,
        "player_id": 0,
        "unit_type": "INFANTRY",
        "x": 0,
        "y": 0
    })
    print("✅ Created infantry unit at (0,0)")
    
    # Check unit state immediately after creation
    board = rpc_call("game_board", {"token": token})
    unit = None
    for tile in board["grid"]:
        if tile.get("unit") and tile["x"] == 0 and tile["y"] == 0:
            unit = tile["unit"]
            break
    
    if not unit:
        raise Exception("❌ Unit not found after creation!")
    
    print(f"📊 Unit state after creation:")
    print(f"   - can_move: {unit.get('can_move', 'N/A')}")
    print(f"   - can_attack: {unit.get('can_attack', 'N/A')}")
    print(f"   - done: {unit.get('done', 'N/A')}")
    print(f"   - has_moved: {unit.get('has_moved', 'N/A')}")
    
    # Verify unit is marked as done after creation
    if not unit.get("done", False):
        print("⚠️  WARNING: Unit not marked as done after creation!")
    
    # End turn for player 0
    rpc_call("army_end_turn", {"token": token})
    print("✅ Ended turn for player 0")
    
    # End turn for player 1 (to cycle back to player 0)
    rpc_call("army_end_turn", {"token": token})
    print("✅ Ended turn for player 1")
    
    # Now we're back to player 0's turn - check unit state
    board = rpc_call("game_board", {"token": token})
    current_player = board["current_player"]
    print(f"✅ Back to player: {current_player}")
    
    # Find the unit again
    unit = None
    for tile in board["grid"]:
        if tile.get("unit") and tile["x"] == 0 and tile["y"] == 0:
            unit = tile["unit"]
            break
    
    if not unit:
        raise Exception("❌ Unit disappeared after turn cycle!")
    
    print(f"📊 Unit state after turn cycle:")
    print(f"   - can_move: {unit.get('can_move', 'N/A')}")
    print(f"   - can_attack: {unit.get('can_attack', 'N/A')}")
    print(f"   - done: {unit.get('done', 'N/A')}")
    print(f"   - has_moved: {unit.get('has_moved', 'N/A')}")
    
    # CRITICAL TEST: Unit should be able to act again
    errors = []
    
    if unit.get("done", True):
        errors.append("Unit still marked as done after turn cycle!")
    
    if not unit.get("can_move", False):
        errors.append("Unit cannot move after turn cycle!")
    
    if not unit.get("can_attack", False):
        errors.append("Unit cannot attack after turn cycle!")
    
    if unit.get("has_moved", True):
        errors.append("Unit still marked as has_moved after turn cycle!")
    
    # Try to actually move the unit to verify it works
    try:
        move_result = rpc_call("unit_move", {
            "token": token,
            "unit_x": 0,
            "unit_y": 0,
            "dest_x": 1,
            "dest_y": 0
        })
        print("✅ Unit successfully moved after turn cycle")
    except Exception as e:
        errors.append(f"Unit move failed after turn cycle: {e}")
    
    # Report results
    print("\n" + "=" * 60)
    if errors:
        print("❌ TEST FAILED - Issues found:")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print("✅ TEST PASSED - Unit states properly reset on turn cycle!")
        return True

if __name__ == "__main__":
    try:
        success = test_unit_state_reset_on_turn()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST CRASHED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
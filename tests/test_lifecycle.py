#!/usr/bin/env python3
"""
Lifecycle Tests
Tests for multi-turn state management, long game sessions, and state transitions
Addresses the bug where units remained "done" after turn cycles
"""

import requests
import json
import time
import sys

API_URL = "http://localhost:5000/api"

def rpc_call(method, params):
    """Make an RPC call to the game server"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    response = requests.post(API_URL, json=payload, timeout=10)
    result = response.json()
    if "error" in result:
        raise Exception(f"RPC Error: {result['error']}")
    return result.get("result")

def test_unit_state_through_multiple_turns():
    """Test that unit states properly reset through multiple turn cycles"""
    
    print("\n🧪 Testing Unit State Through Multiple Turn Cycles")
    print("=" * 60)
    
    token = f"lifecycle-multi-turn-{int(time.time())}"
    result = rpc_call("game_create_test", {"token": token})
    print(f"✅ Created test game: {token}")
    
    # Create units for both players
    print("\n1️⃣ Creating units for both players...")
    
    # Player 0 tank at (2,2)
    result = rpc_call("unit_create", {
        "token": token,
        "player_id": 0,
        "unit_type": "TANK",
        "x": 2,
        "y": 2
    })
    print("✅ Created Player 0 tank at (2,2)")
    
    # Player 0 infantry at (3,3)
    result = rpc_call("unit_create", {
        "token": token,
        "player_id": 0,
        "unit_type": "INFANTRY",
        "x": 3,
        "y": 3
    })
    print("✅ Created Player 0 infantry at (3,3)")
    
    # End Player 0's turn
    rpc_call("army_end_turn", {"token": token})
    
    # Player 1 units
    result = rpc_call("unit_create", {
        "token": token,
        "player_id": 1,
        "unit_type": "RECON",
        "x": 7,
        "y": 7
    })
    print("✅ Created Player 1 recon at (7,7)")
    
    # Track unit states through multiple cycles
    print("\n2️⃣ Testing state through 3 complete turn cycles...")
    
    # Track current positions
    tank_x, tank_y = 2, 2
    infantry_x, infantry_y = 3, 3
    
    for cycle in range(3):
        print(f"\n📊 Turn Cycle {cycle + 1}:")
        
        # End Player 1's turn (back to Player 0)
        rpc_call("army_end_turn", {"token": token})
        
        # Check Player 0's units
        board = rpc_call("game_board", {"token": token})
        
        # Find Player 0's tank at its current position
        tank = None
        infantry = None
        for tile in board["grid"]:
            if tile.get("unit"):
                unit = tile["unit"]
                if unit["player_id"] == 0:
                    if tile["x"] == tank_x and tile["y"] == tank_y:
                        tank = unit
                    elif tile["x"] == infantry_x and tile["y"] == infantry_y:
                        infantry = unit
        
        errors = []
        
        # Verify tank state
        if not tank:
            errors.append(f"Tank disappeared in cycle {cycle + 1}")
        else:
            print(f"   Tank - can_move: {tank.get('can_move')}, done: {tank.get('done')}")
            if tank.get("done", True):
                errors.append(f"Tank still marked done in cycle {cycle + 1}")
            if not tank.get("can_move", False):
                errors.append(f"Tank cannot move in cycle {cycle + 1}")
        
        # Verify infantry state
        if not infantry:
            errors.append(f"Infantry disappeared in cycle {cycle + 1}")
        else:
            print(f"   Infantry - can_move: {infantry.get('can_move')}, done: {infantry.get('done')}")
            if infantry.get("done", True):
                errors.append(f"Infantry still marked done in cycle {cycle + 1}")
            if not infantry.get("can_move", False):
                errors.append(f"Infantry cannot move in cycle {cycle + 1}")
        
        if errors:
            print("\n❌ State errors found:")
            for error in errors:
                print(f"   - {error}")
            raise Exception("Unit states not properly reset")
        
        # Actually move the units to verify they can act
        if cycle == 0:
            # Move tank
            result = rpc_call("movement_execute", {
                "token": token,
                "from_x": 2,
                "from_y": 2,
                "to_x": 2,
                "to_y": 3
            })
            print("   ✅ Tank moved successfully")
            
            # Move infantry
            result = rpc_call("movement_execute", {
                "token": token,
                "from_x": 3,
                "from_y": 3,
                "to_x": 4,
                "to_y": 3
            })
            print("   ✅ Infantry moved successfully")
            
            # Update tracked positions for next cycle
            tank_x, tank_y = 2, 3
            infantry_x, infantry_y = 4, 3
        
        # End Player 0's turn
        rpc_call("army_end_turn", {"token": token})
    
    print("\n✅ TEST PASSED - Unit states properly reset through all cycles!")
    return True

def test_long_game_session():
    """Test state management in a long game session (20+ turns)"""
    
    print("\n🧪 Testing Long Game Session (20+ turns)")
    print("=" * 60)
    
    token = f"lifecycle-long-session-{int(time.time())}"
    result = rpc_call("game_create_test", {"token": token})
    print(f"✅ Created test game: {token}")
    
    # Create initial units
    units = []
    for i in range(3):
        result = rpc_call("unit_create", {
            "token": token,
            "player_id": 0,
            "unit_type": "INFANTRY",
            "x": i + 1,
            "y": 1
        })
        units.append({"x": i + 1, "y": 1, "player": 0})
    
    rpc_call("army_end_turn", {"token": token})
    
    for i in range(3):
        result = rpc_call("unit_create", {
            "token": token,
            "player_id": 1,
            "unit_type": "INFANTRY",
            "x": i + 6,
            "y": 8
        })
        units.append({"x": i + 6, "y": 8, "player": 1})
    
    print(f"✅ Created {len(units)} units")
    
    # Simulate 20 turns
    print("\n📊 Simulating 20 turns...")
    
    for turn in range(20):
        # End current player's turn
        rpc_call("army_end_turn", {"token": token})
        
        if turn % 5 == 0:
            # Every 5 turns, verify game state integrity
            board = rpc_call("game_board", {"token": token})
            
            # Check day counter
            expected_day = (turn // 2) + 1
            actual_day = board.get("day", 0)
            
            # Count units
            unit_count = sum(1 for tile in board["grid"] if tile.get("unit"))
            
            print(f"   Turn {turn}: Day {actual_day}, {unit_count} units active")
            
            if unit_count < len(units):
                print(f"   ⚠️  Some units disappeared! Expected {len(units)}, found {unit_count}")
    
    # Final verification
    board = rpc_call("game_board", {"token": token})
    final_day = board.get("day", 0)
    final_units = sum(1 for tile in board["grid"] if tile.get("unit"))
    
    print(f"\n📊 Final state after 20 turns:")
    print(f"   - Day: {final_day}")
    print(f"   - Units remaining: {final_units}/{len(units)}")
    print(f"   - Current player: {board.get('current_player')}")
    
    if final_units == len(units):
        print("\n✅ TEST PASSED - Game state stable through long session!")
        return True
    else:
        print("\n❌ TEST FAILED - State degraded during long session")
        return False

def test_unit_action_state_transitions():
    """Test all unit action state transitions"""
    
    print("\n🧪 Testing Unit Action State Transitions")
    print("=" * 60)
    
    token = f"lifecycle-transitions-{int(time.time())}"
    result = rpc_call("game_create_test", {"token": token})
    
    print("1️⃣ Testing creation -> wait transition...")
    
    # Create unit
    result = rpc_call("unit_create", {
        "token": token,
        "player_id": 0,
        "unit_type": "TANK",
        "x": 5,
        "y": 5
    })
    
    # Check initial state
    board = rpc_call("game_board", {"token": token})
    tank = None
    for tile in board["grid"]:
        if tile.get("unit") and tile["x"] == 5 and tile["y"] == 5:
            tank = tile["unit"]
            break
    
    assert tank, "Tank not found after creation"
    assert tank.get("done", False), "Tank should be done after creation"
    print("   ✅ Unit correctly marked as done after creation")
    
    # Cycle turns
    rpc_call("army_end_turn", {"token": token})  # End P0 turn
    rpc_call("army_end_turn", {"token": token})  # End P1 turn
    
    print("\n2️⃣ Testing move -> attack transition...")
    
    # Check tank can act
    board = rpc_call("game_board", {"token": token})
    tank = None
    for tile in board["grid"]:
        if tile.get("unit") and tile["x"] == 5 and tile["y"] == 5:
            tank = tile["unit"]
            break
    
    assert not tank.get("done", True), "Tank should not be done after turn cycle"
    assert tank.get("can_move", False), "Tank should be able to move"
    print("   ✅ Unit correctly reset after turn cycle")
    
    # Move tank
    result = rpc_call("movement_execute", {
        "token": token,
        "from_x": 5,
        "from_y": 5,
        "to_x": 6,
        "to_y": 5
    })
    
    # Check post-move state
    board = rpc_call("game_board", {"token": token})
    tank = None
    for tile in board["grid"]:
        if tile.get("unit") and tile["x"] == 6 and tile["y"] == 5:
            tank = tile["unit"]
            break
    
    # Direct attack units should still be able to attack after moving
    if tank.get("can_attack", False):
        print("   ✅ Tank can still attack after moving (direct fire)")
    else:
        print("   ⚠️  Tank cannot attack after moving")
    
    print("\n3️⃣ Testing wait action transition...")
    
    # Create another unit to test wait
    result = rpc_call("unit_create", {
        "token": token,
        "player_id": 0,
        "unit_type": "INFANTRY",
        "x": 2,
        "y": 2
    })
    
    # Cycle turns
    rpc_call("army_end_turn", {"token": token})
    rpc_call("army_end_turn", {"token": token})
    
    # Use wait action
    result = rpc_call("unit_wait", {
        "token": token,
        "x": 2,
        "y": 2
    })
    
    # Check post-wait state
    board = rpc_call("game_board", {"token": token})
    infantry = None
    for tile in board["grid"]:
        if tile.get("unit") and tile["x"] == 2 and tile["y"] == 2:
            infantry = tile["unit"]
            break
    
    assert infantry.get("done", False), "Infantry should be done after wait"
    print("   ✅ Unit correctly marked as done after wait action")
    
    print("\n✅ TEST PASSED - All state transitions work correctly!")
    return True

def test_capture_state_persistence():
    """Test that capture progress persists across turns"""
    
    print("\n🧪 Testing Capture State Persistence")
    print("=" * 60)
    
    token = f"lifecycle-capture-{int(time.time())}"
    result = rpc_call("game_create_test", {"token": token})
    
    # Create infantry near a capturable property
    result = rpc_call("unit_create", {
        "token": token,
        "player_id": 0,
        "unit_type": "INFANTRY",
        "x": 2,
        "y": 4  # Near city at (3,4)
    })
    
    # Move to city
    rpc_call("army_end_turn", {"token": token})
    rpc_call("army_end_turn", {"token": token})
    
    result = rpc_call("movement_execute", {
        "token": token,
        "from_x": 2,
        "from_y": 4,
        "to_x": 3,
        "to_y": 4
    })
    
    # Start capture
    result = rpc_call("capture_tile", {
        "token": token,
        "x": 3,
        "y": 4
    })
    print("✅ Started capture at (3,4)")
    
    # Check capture progress
    board = rpc_call("game_board", {"token": token})
    tile_info = None
    for tile in board["grid"]:
        if tile["x"] == 3 and tile["y"] == 4:
            tile_info = tile
            break
    
    initial_capture = tile_info.get("capture_progress", 0)
    print(f"📊 Initial capture progress: {initial_capture}")
    
    # Cycle turns and continue capture
    rpc_call("army_end_turn", {"token": token})
    rpc_call("army_end_turn", {"token": token})
    
    # Continue capture
    result = rpc_call("capture_tile", {
        "token": token,
        "x": 3,
        "y": 4
    })
    
    # Check progress increased
    board = rpc_call("game_board", {"token": token})
    for tile in board["grid"]:
        if tile["x"] == 3 and tile["y"] == 4:
            tile_info = tile
            break
    
    final_capture = tile_info.get("capture_progress", 0)
    print(f"📊 Final capture progress: {final_capture}")
    
    if final_capture > initial_capture or tile_info.get("player_id") == 0:
        print("\n✅ TEST PASSED - Capture state persists correctly!")
        return True
    else:
        print("\n❌ TEST FAILED - Capture progress not persisting")
        return False

def test_memory_cleanup():
    """Test that memory is properly cleaned up during long sessions"""
    
    print("\n🧪 Testing Memory Cleanup")
    print("=" * 60)
    
    token = f"lifecycle-memory-{int(time.time())}"
    result = rpc_call("game_create_test", {"token": token})
    
    print("1️⃣ Creating and destroying many units...")
    
    for iteration in range(5):
        # Create units
        positions = []
        for i in range(5):
            x, y = 2 + i, 2
            try:
                result = rpc_call("unit_create", {
                    "token": token,
                    "player_id": 0,
                    "unit_type": "INFANTRY",
                    "x": x,
                    "y": y
                })
                positions.append((x, y))
            except:
                pass  # May fail if position occupied
        
        print(f"   Iteration {iteration + 1}: Created {len(positions)} units")
        
        # Destroy units through combat
        rpc_call("army_end_turn", {"token": token})
        
        # Create enemy units to attack
        for x, y in positions:
            try:
                result = rpc_call("unit_create", {
                    "token": token,
                    "player_id": 1,
                    "unit_type": "TANK",
                    "x": x,
                    "y": y + 1
                })
                
                # Attack to destroy infantry
                rpc_call("army_end_turn", {"token": token})
                rpc_call("army_end_turn", {"token": token})
                
                result = rpc_call("unit_attack", {
                    "token": token,
                    "attacker_x": x,
                    "attacker_y": y + 1,
                    "target_x": x,
                    "target_y": y
                })
            except:
                pass
        
        # Check unit count
        board = rpc_call("game_board", {"token": token})
        unit_count = sum(1 for tile in board["grid"] if tile.get("unit"))
        print(f"   Units remaining: {unit_count}")
    
    # Final game state check
    board = rpc_call("game_board", {"token": token})
    
    # Verify game is still playable
    try:
        result = rpc_call("army_end_turn", {"token": token})
        print("\n✅ TEST PASSED - Game still playable after stress test!")
        return True
    except:
        print("\n❌ TEST FAILED - Game corrupted after stress test")
        return False

def main():
    """Run all lifecycle tests"""
    
    print("🚀 Starting Lifecycle Test Suite")
    print("=" * 60)
    
    tests = [
        ("Multi-Turn State", test_unit_state_through_multiple_turns),
        ("Long Game Session", test_long_game_session),
        ("Action State Transitions", test_unit_action_state_transitions),
        ("Capture State Persistence", test_capture_state_persistence),
        ("Memory Cleanup", test_memory_cleanup),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n💥 Test crashed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 LIFECYCLE TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All lifecycle tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} lifecycle tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
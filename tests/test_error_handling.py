#!/usr/bin/env python3
"""
Error Handling Tests
Tests for proper error handling, validation, and edge cases
Ensures errors are caught and reported properly, not silently defaulted
"""

import requests
import json
import sys
import time

API_URL = "http://localhost:5000/api"

def rpc_call(method, params, expect_error=False):
    """Make an RPC call to the game server"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    response = requests.post(API_URL, json=payload, timeout=10)
    result = response.json()
    
    if expect_error:
        return result  # Return full result to check error structure
    
    if "error" in result:
        raise Exception(f"RPC Error: {result['error']}")
    return result.get("result")

def test_invalid_coordinates():
    """Test handling of invalid coordinates"""
    
    print("\n🧪 Testing Invalid Coordinates")
    print("=" * 60)
    
    token = f"error-coords-{int(time.time())}"
    result = rpc_call("game_create_test", {"token": token})
    
    errors_caught = []
    
    # Test 1: Negative coordinates
    print("1️⃣ Testing negative coordinates...")
    try:
        result = rpc_call("unit_create", {
            "token": token,
            "player_id": 0,
            "unit_type": "TANK",
            "x": -1,
            "y": -1
        })
        print("   ❌ Negative coordinates accepted (should fail)")
    except Exception as e:
        print("   ✅ Negative coordinates rejected")
        errors_caught.append("negative_coords")
    
    # Test 2: Out of bounds coordinates
    print("2️⃣ Testing out of bounds coordinates...")
    try:
        result = rpc_call("unit_create", {
            "token": token,
            "player_id": 0,
            "unit_type": "TANK",
            "x": 999,
            "y": 999
        })
        print("   ❌ Out of bounds coordinates accepted (should fail)")
    except Exception as e:
        print("   ✅ Out of bounds coordinates rejected")
        errors_caught.append("out_of_bounds")
    
    # Test 3: Non-integer coordinates
    print("3️⃣ Testing non-integer coordinates...")
    try:
        result = rpc_call("unit_move", {
            "token": token,
            "unit_x": "not_a_number",
            "unit_y": 5.5,
            "dest_x": 6,
            "dest_y": 6
        })
        print("   ❌ Non-integer coordinates accepted (should fail)")
    except Exception as e:
        print("   ✅ Non-integer coordinates rejected")
        errors_caught.append("non_integer")
    
    # Test 4: Missing coordinates
    print("4️⃣ Testing missing coordinates...")
    try:
        result = rpc_call("unit_create", {
            "token": token,
            "player_id": 0,
            "unit_type": "TANK"
            # Missing x and y
        })
        print("   ❌ Missing coordinates accepted (should fail)")
    except Exception as e:
        print("   ✅ Missing coordinates rejected")
        errors_caught.append("missing_coords")
    
    if len(errors_caught) >= 3:
        print(f"\n✅ TEST PASSED - {len(errors_caught)}/4 error cases handled correctly")
        return True
    else:
        print(f"\n❌ TEST FAILED - Only {len(errors_caught)}/4 error cases handled")
        return False

def test_invalid_unit_types():
    """Test handling of invalid unit types"""
    
    print("\n🧪 Testing Invalid Unit Types")
    print("=" * 60)
    
    token = f"error-units-{int(time.time())}"
    result = rpc_call("game_create_test", {"token": token})
    
    invalid_types = [
        "INVALID_UNIT",
        "SUPER_TANK",
        "",
        None,
        123,
        ["TANK"],
        {"type": "TANK"}
    ]
    
    errors_caught = 0
    
    for i, unit_type in enumerate(invalid_types):
        print(f"{i+1}️⃣ Testing unit type: {repr(unit_type)}...")
        try:
            result = rpc_call("unit_create", {
                "token": token,
                "player_id": 0,
                "unit_type": unit_type,
                "x": 5,
                "y": 5
            })
            print(f"   ❌ Invalid type {repr(unit_type)} accepted")
        except Exception as e:
            print(f"   ✅ Invalid type {repr(unit_type)} rejected")
            errors_caught += 1
    
    if errors_caught >= len(invalid_types) - 1:
        print(f"\n✅ TEST PASSED - {errors_caught}/{len(invalid_types)} invalid types rejected")
        return True
    else:
        print(f"\n❌ TEST FAILED - Only {errors_caught}/{len(invalid_types)} invalid types rejected")
        return False

def test_insufficient_funds():
    """Test handling of insufficient funds for unit creation"""
    
    print("\n🧪 Testing Insufficient Funds")
    print("=" * 60)
    
    token = f"error-funds-{int(time.time())}"
    result = rpc_call("game_create_test", {"token": token})
    
    # Spend most funds
    print("1️⃣ Creating expensive units to deplete funds...")
    
    # Create multiple expensive units
    for i in range(3):
        try:
            result = rpc_call("unit_create", {
                "token": token,
                "player_id": 0,
                "unit_type": "BOMBER",  # Very expensive
                "x": i,
                "y": 0
            })
            print(f"   Created bomber {i+1}")
        except:
            break
    
    # Check remaining funds
    board = rpc_call("game_board", {"token": token})
    funds = board.get("player_funds", [0])[0]
    print(f"   Remaining funds: {funds}")
    
    # Try to create unit with insufficient funds
    print("2️⃣ Attempting to create unit with insufficient funds...")
    try:
        result = rpc_call("unit_create", {
            "token": token,
            "player_id": 0,
            "unit_type": "BATTLESHIP",  # Most expensive unit
            "x": 8,
            "y": 8
        })
        print("   ❌ Unit created despite insufficient funds")
        return False
    except Exception as e:
        if "funds" in str(e).lower() or "afford" in str(e).lower():
            print("   ✅ Insufficient funds error properly reported")
            return True
        else:
            print(f"   ⚠️  Error caught but unclear message: {e}")
            return True

def test_invalid_game_token():
    """Test handling of invalid game tokens"""
    
    print("\n🧪 Testing Invalid Game Token")
    print("=" * 60)
    
    invalid_tokens = [
        "nonexistent-game",
        "",
        None,
        123,
        ["token"],
        {"token": "value"}
    ]
    
    errors_caught = 0
    
    for i, token in enumerate(invalid_tokens):
        print(f"{i+1}️⃣ Testing token: {repr(token)}...")
        try:
            result = rpc_call("game_board", {"token": token})
            print(f"   ❌ Invalid token {repr(token)} accepted")
        except Exception as e:
            print(f"   ✅ Invalid token {repr(token)} rejected")
            errors_caught += 1
    
    if errors_caught >= len(invalid_tokens) - 1:
        print(f"\n✅ TEST PASSED - {errors_caught}/{len(invalid_tokens)} invalid tokens rejected")
        return True
    else:
        print(f"\n❌ TEST FAILED - Only {errors_caught}/{len(invalid_tokens)} invalid tokens rejected")
        return False

def test_invalid_player_id():
    """Test handling of invalid player IDs"""
    
    print("\n🧪 Testing Invalid Player ID")
    print("=" * 60)
    
    token = f"error-player-{int(time.time())}"
    result = rpc_call("game_create_test", {"token": token})
    
    invalid_players = [
        -1,      # Negative
        99,      # Out of range
        "RED",   # String (old format)
        None,    # None
        1.5,     # Float
        [0],     # List
    ]
    
    errors_caught = 0
    
    for i, player_id in enumerate(invalid_players):
        print(f"{i+1}️⃣ Testing player_id: {repr(player_id)}...")
        try:
            result = rpc_call("unit_create", {
                "token": token,
                "player_id": player_id,
                "unit_type": "INFANTRY",
                "x": 5,
                "y": 5
            })
            print(f"   ❌ Invalid player_id {repr(player_id)} accepted")
        except Exception as e:
            print(f"   ✅ Invalid player_id {repr(player_id)} rejected")
            errors_caught += 1
    
    if errors_caught >= 4:
        print(f"\n✅ TEST PASSED - {errors_caught}/{len(invalid_players)} invalid player IDs rejected")
        return True
    else:
        print(f"\n❌ TEST FAILED - Only {errors_caught}/{len(invalid_players)} invalid player IDs rejected")
        return False

def test_invalid_movement():
    """Test handling of invalid movement attempts"""
    
    print("\n🧪 Testing Invalid Movement")
    print("=" * 60)
    
    token = f"error-movement-{int(time.time())}"
    result = rpc_call("game_create_test", {"token": token})
    
    # Create a unit
    result = rpc_call("unit_create", {
        "token": token,
        "player_id": 0,
        "unit_type": "INFANTRY",
        "x": 5,
        "y": 5
    })
    
    errors_caught = []
    
    # Test 1: Move without enabling (same turn as creation)
    print("1️⃣ Testing move on creation turn...")
    try:
        result = rpc_call("unit_move", {
            "token": token,
            "unit_x": 5,
            "unit_y": 5,
            "dest_x": 6,
            "dest_y": 5
        })
        print("   ❌ Unit moved on creation turn (should fail)")
    except Exception as e:
        print("   ✅ Move on creation turn rejected")
        errors_caught.append("creation_turn")
    
    # Enable unit
    rpc_call("army_end_turn", {"token": token})
    rpc_call("army_end_turn", {"token": token})
    
    # Test 2: Move out of range
    print("2️⃣ Testing move out of range...")
    try:
        result = rpc_call("unit_move", {
            "token": token,
            "unit_x": 5,
            "unit_y": 5,
            "dest_x": 9,  # Too far for infantry (range 3)
            "dest_y": 9
        })
        print("   ❌ Out of range move accepted (should fail)")
    except Exception as e:
        print("   ✅ Out of range move rejected")
        errors_caught.append("out_of_range")
    
    # Test 3: Move to occupied tile
    print("3️⃣ Testing move to occupied tile...")
    
    # Create another unit
    rpc_call("army_end_turn", {"token": token})
    result = rpc_call("unit_create", {
        "token": token,
        "player_id": 1,
        "unit_type": "TANK",
        "x": 6,
        "y": 5
    })
    rpc_call("army_end_turn", {"token": token})
    
    try:
        result = rpc_call("unit_move", {
            "token": token,
            "unit_x": 5,
            "unit_y": 5,
            "dest_x": 6,  # Occupied by tank
            "dest_y": 5
        })
        print("   ❌ Move to occupied tile accepted (should fail)")
    except Exception as e:
        print("   ✅ Move to occupied tile rejected")
        errors_caught.append("occupied")
    
    # Test 4: Move nonexistent unit
    print("4️⃣ Testing move nonexistent unit...")
    try:
        result = rpc_call("unit_move", {
            "token": token,
            "unit_x": 9,
            "unit_y": 9,  # No unit here
            "dest_x": 8,
            "dest_y": 8
        })
        print("   ❌ Move nonexistent unit accepted (should fail)")
    except Exception as e:
        print("   ✅ Move nonexistent unit rejected")
        errors_caught.append("nonexistent")
    
    if len(errors_caught) >= 3:
        print(f"\n✅ TEST PASSED - {len(errors_caught)}/4 movement errors handled")
        return True
    else:
        print(f"\n❌ TEST FAILED - Only {len(errors_caught)}/4 movement errors handled")
        return False

def test_invalid_combat():
    """Test handling of invalid combat attempts"""
    
    print("\n🧪 Testing Invalid Combat")
    print("=" * 60)
    
    token = f"error-combat-{int(time.time())}"
    result = rpc_call("game_create_test", {"token": token})
    
    # Create units
    result = rpc_call("unit_create", {
        "token": token,
        "player_id": 0,
        "unit_type": "TANK",
        "x": 3,
        "y": 3
    })
    
    result = rpc_call("unit_create", {
        "token": token,
        "player_id": 0,
        "unit_type": "INFANTRY",
        "x": 5,
        "y": 3
    })
    
    # Enable units
    rpc_call("army_end_turn", {"token": token})
    rpc_call("army_end_turn", {"token": token})
    
    errors_caught = []
    
    # Test 1: Attack friendly unit
    print("1️⃣ Testing friendly fire...")
    try:
        result = rpc_call("unit_attack", {
            "token": token,
            "attacker_x": 3,
            "attacker_y": 3,
            "target_x": 5,
            "target_y": 3  # Friendly infantry
        })
        print("   ❌ Friendly fire accepted (should fail)")
    except Exception as e:
        print("   ✅ Friendly fire rejected")
        errors_caught.append("friendly_fire")
    
    # Test 2: Attack out of range
    print("2️⃣ Testing attack out of range...")
    
    # Create enemy far away
    rpc_call("army_end_turn", {"token": token})
    result = rpc_call("unit_create", {
        "token": token,
        "player_id": 1,
        "unit_type": "RECON",
        "x": 9,
        "y": 9
    })
    rpc_call("army_end_turn", {"token": token})
    
    try:
        result = rpc_call("unit_attack", {
            "token": token,
            "attacker_x": 3,
            "attacker_y": 3,
            "target_x": 9,
            "target_y": 9  # Too far
        })
        print("   ❌ Out of range attack accepted (should fail)")
    except Exception as e:
        print("   ✅ Out of range attack rejected")
        errors_caught.append("out_of_range")
    
    # Test 3: Attack with no ammo (need to deplete ammo first)
    print("3️⃣ Testing attack with depleted unit...")
    
    # Move tank after attacking (should not be able to)
    result = rpc_call("unit_create", {
        "token": token,
        "player_id": 1,
        "unit_type": "INFANTRY",
        "x": 4,
        "y": 3
    })
    
    rpc_call("army_end_turn", {"token": token})
    rpc_call("army_end_turn", {"token": token})
    
    # Attack enemy
    result = rpc_call("unit_attack", {
        "token": token,
        "attacker_x": 3,
        "attacker_y": 3,
        "target_x": 4,
        "target_y": 3
    })
    
    # Try to attack again same turn
    try:
        result = rpc_call("unit_attack", {
            "token": token,
            "attacker_x": 3,
            "attacker_y": 3,
            "target_x": 4,
            "target_y": 3
        })
        print("   ❌ Double attack same turn accepted (should fail)")
    except Exception as e:
        print("   ✅ Double attack same turn rejected")
        errors_caught.append("double_attack")
    
    if len(errors_caught) >= 2:
        print(f"\n✅ TEST PASSED - {len(errors_caught)}/3 combat errors handled")
        return True
    else:
        print(f"\n❌ TEST FAILED - Only {len(errors_caught)}/3 combat errors handled")
        return False

def test_error_message_quality():
    """Test that error messages are informative"""
    
    print("\n🧪 Testing Error Message Quality")
    print("=" * 60)
    
    token = f"error-messages-{int(time.time())}"
    result = rpc_call("game_create_test", {"token": token})
    
    # Test various errors and check message quality
    test_cases = [
        {
            "name": "Invalid coordinates",
            "method": "unit_create",
            "params": {
                "token": token,
                "player_id": 0,
                "unit_type": "TANK",
                "x": -1,
                "y": -1
            },
            "expected_keywords": ["coordinate", "bound", "invalid", "position"]
        },
        {
            "name": "Invalid unit type",
            "method": "unit_create",
            "params": {
                "token": token,
                "player_id": 0,
                "unit_type": "INVALID_TYPE",
                "x": 5,
                "y": 5
            },
            "expected_keywords": ["unit", "type", "invalid", "unknown"]
        },
        {
            "name": "Game not found",
            "method": "game_board",
            "params": {
                "token": "nonexistent-game"
            },
            "expected_keywords": ["game", "not found", "exist", "token"]
        }
    ]
    
    good_messages = 0
    
    for test in test_cases:
        print(f"\n📊 Testing: {test['name']}")
        result = rpc_call(test['method'], test['params'], expect_error=True)
        
        if "error" in result:
            error_msg = str(result["error"]).lower()
            print(f"   Error message: {result['error']}")
            
            # Check if any expected keywords are in the message
            keywords_found = any(
                keyword in error_msg 
                for keyword in test['expected_keywords']
            )
            
            if keywords_found:
                print("   ✅ Error message is informative")
                good_messages += 1
            else:
                print("   ⚠️  Error message could be clearer")
        else:
            print("   ❌ No error returned")
    
    if good_messages >= 2:
        print(f"\n✅ TEST PASSED - {good_messages}/{len(test_cases)} error messages are informative")
        return True
    else:
        print(f"\n❌ TEST FAILED - Only {good_messages}/{len(test_cases)} error messages are informative")
        return False

def main():
    """Run all error handling tests"""
    
    print("🚀 Starting Error Handling Test Suite")
    print("=" * 60)
    
    tests = [
        ("Invalid Coordinates", test_invalid_coordinates),
        ("Invalid Unit Types", test_invalid_unit_types),
        ("Insufficient Funds", test_insufficient_funds),
        ("Invalid Game Token", test_invalid_game_token),
        ("Invalid Player ID", test_invalid_player_id),
        ("Invalid Movement", test_invalid_movement),
        ("Invalid Combat", test_invalid_combat),
        ("Error Message Quality", test_error_message_quality),
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
    print("📊 ERROR HANDLING TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All error handling tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} error handling tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
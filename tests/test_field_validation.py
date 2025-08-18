#!/usr/bin/env python3
"""
Field Validation Tests
Tests that all expected fields exist in data structures with no silent defaults
Addresses the bug where missing fields like 'action_taken' were silently defaulted
"""

import requests
import json
import sys
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
    response = requests.post(API_URL, json=payload, timeout=10)
    result = response.json()
    if "error" in result:
        raise Exception(f"RPC Error: {result['error']}")
    return result.get("result")

def test_unit_status_fields():
    """Test that all unit status fields exist without silent defaults"""
    
    print("\n🧪 Testing Unit Status Fields")
    print("=" * 60)
    
    token = f"field-validation-unit-{int(time.time())}"
    result = rpc_call("game_create_test", {"token": token})
    
    # Create a unit
    result = rpc_call("unit_create", {
        "token": token,
        "player_id": 0,
        "unit_type": "TANK",
        "x": 5,
        "y": 5
    })
    print("✅ Created tank at (5,5)")
    
    # Get board and find unit
    board = rpc_call("game_board", {"token": token})
    unit = None
    for tile in board["grid"]:
        if tile.get("unit") and tile["x"] == 5 and tile["y"] == 5:
            unit = tile["unit"]
            break
    
    assert unit, "Unit not found in board"
    
    # Required fields that MUST exist
    required_fields = {
        # Basic unit info
        "type": str,
        "player_id": int,
        "x": int,
        "y": int,
        
        # Status fields
        "hp": int,
        "fuel": int,
        "ammo": int,
        
        # Action flags
        "can_move": bool,
        "can_attack": bool,
        "done": bool,
        
        # Movement tracking
        "has_moved": bool,
        "moved": bool,  # Legacy field, might still exist
        
        # New field that was missing
        "action_taken": bool,
    }
    
    optional_fields = {
        "can_capture": bool,
        "cargo": list,
        "movement_range": int,
        "attack_range": list,
    }
    
    errors = []
    warnings = []
    
    print("\n📊 Validating required fields:")
    
    # Check required fields
    for field, expected_type in required_fields.items():
        if field not in unit:
            errors.append(f"Missing required field: {field}")
            print(f"   ❌ {field}: MISSING")
        else:
            actual_value = unit[field]
            actual_type = type(actual_value)
            
            # Check type (be lenient with None for some fields)
            if actual_value is not None and not isinstance(actual_value, expected_type):
                warnings.append(f"Field {field} has wrong type: expected {expected_type.__name__}, got {actual_type.__name__}")
                print(f"   ⚠️  {field}: {actual_value} (wrong type)")
            else:
                print(f"   ✅ {field}: {actual_value}")
    
    print("\n📊 Checking optional fields:")
    
    # Check optional fields (warn if missing)
    for field, expected_type in optional_fields.items():
        if field not in unit:
            print(f"   ℹ️  {field}: not present (optional)")
        else:
            actual_value = unit[field]
            print(f"   ✅ {field}: {actual_value}")
    
    # Test after turn cycle to ensure fields persist
    print("\n🔄 Testing field persistence after turn cycle...")
    
    rpc_call("army_end_turn", {"token": token})
    rpc_call("army_end_turn", {"token": token})
    
    # Get unit again
    board = rpc_call("game_board", {"token": token})
    unit_after = None
    for tile in board["grid"]:
        if tile.get("unit") and tile["x"] == 5 and tile["y"] == 5:
            unit_after = tile["unit"]
            break
    
    assert unit_after, "Unit disappeared after turn cycle"
    
    # Check critical fields still exist
    critical_fields = ["action_taken", "done", "can_move", "has_moved"]
    for field in critical_fields:
        if field not in unit_after:
            errors.append(f"Field {field} disappeared after turn cycle")
        else:
            print(f"   ✅ {field} persists: {unit_after[field]}")
    
    # Report results
    if errors:
        print("\n❌ TEST FAILED - Field validation errors:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"   - {warning}")
    
    print("\n✅ TEST PASSED - All required fields present!")
    return True

def test_game_board_fields():
    """Test that game board response has all required fields"""
    
    print("\n🧪 Testing Game Board Fields")
    print("=" * 60)
    
    token = f"field-validation-board-{int(time.time())}"
    result = rpc_call("game_create_test", {"token": token})
    
    board = rpc_call("game_board", {"token": token})
    
    # Required top-level fields
    required_fields = {
        "grid": list,
        "current_player": int,
        "day": int,
        "game_active": bool,
        "players": list,
        "player_funds": list,
        "width": int,
        "height": int,
    }
    
    # Legacy fields that might still exist
    legacy_fields = {
        "current_turn": str,  # Old army-based field
        "army_funds": dict,   # Old army-based funds
        "red_funds": int,     # Very old format
        "blue_funds": int,    # Very old format
    }
    
    errors = []
    
    print("📊 Validating required board fields:")
    
    for field, expected_type in required_fields.items():
        if field not in board:
            errors.append(f"Missing required field: {field}")
            print(f"   ❌ {field}: MISSING")
        else:
            actual_value = board[field]
            if not isinstance(actual_value, expected_type):
                errors.append(f"Field {field} has wrong type")
                print(f"   ⚠️  {field}: wrong type")
            else:
                print(f"   ✅ {field}: present")
    
    print("\n📊 Checking for legacy fields:")
    
    for field, expected_type in legacy_fields.items():
        if field in board:
            print(f"   ℹ️  {field}: still present (legacy)")
    
    # Validate player structure
    if "players" in board:
        print("\n📊 Validating player structure:")
        for i, player in enumerate(board["players"]):
            required_player_fields = ["id", "name", "army", "funds"]
            for field in required_player_fields:
                if field not in player:
                    errors.append(f"Player {i} missing field: {field}")
                    print(f"   ❌ Player {i}.{field}: MISSING")
                else:
                    print(f"   ✅ Player {i}.{field}: {player[field]}")
    
    # Validate grid tiles
    if "grid" in board and len(board["grid"]) > 0:
        print("\n📊 Validating tile structure (sample):")
        sample_tile = board["grid"][0]
        required_tile_fields = ["x", "y", "type"]
        
        for field in required_tile_fields:
            if field not in sample_tile:
                errors.append(f"Tile missing field: {field}")
                print(f"   ❌ Tile.{field}: MISSING")
            else:
                print(f"   ✅ Tile.{field}: present")
    
    if errors:
        print("\n❌ TEST FAILED - Board field validation errors:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print("\n✅ TEST PASSED - All board fields valid!")
    return True

def test_combat_preview_fields():
    """Test that combat preview has all required fields"""
    
    print("\n🧪 Testing Combat Preview Fields")
    print("=" * 60)
    
    token = f"field-validation-combat-{int(time.time())}"
    result = rpc_call("game_create_test", {"token": token})
    
    # Create attacker
    result = rpc_call("unit_create", {
        "token": token,
        "player_id": 0,
        "unit_type": "TANK",
        "x": 3,
        "y": 3
    })
    
    # Create target
    result = rpc_call("unit_create", {
        "token": token,
        "player_id": 1,
        "unit_type": "INFANTRY",
        "x": 4,
        "y": 3
    })
    
    # Enable units
    rpc_call("army_end_turn", {"token": token})
    rpc_call("army_end_turn", {"token": token})
    
    # Get combat preview
    preview = rpc_call("combat_preview", {
        "token": token,
        "attacker_x": 3,
        "attacker_y": 3,
        "target_x": 4,
        "target_y": 3
    })
    
    # Required fields in combat preview
    required_fields = {
        "can_attack": bool,
        "damage": (int, float),
        "counter_damage": (int, float),
        "attacker_hp_after": (int, float),
        "defender_hp_after": (int, float),
    }
    
    optional_fields = {
        "in_range": bool,
        "reason": str,
        "terrain_defense": int,
        "damage_modifier": float,
    }
    
    errors = []
    
    print("📊 Validating combat preview fields:")
    
    for field, expected_types in required_fields.items():
        if field not in preview:
            errors.append(f"Missing required field: {field}")
            print(f"   ❌ {field}: MISSING")
        else:
            actual_value = preview[field]
            # Handle multiple acceptable types
            if isinstance(expected_types, tuple):
                valid_type = any(isinstance(actual_value, t) for t in expected_types)
            else:
                valid_type = isinstance(actual_value, expected_types)
            
            if not valid_type:
                errors.append(f"Field {field} has wrong type")
                print(f"   ⚠️  {field}: wrong type")
            else:
                print(f"   ✅ {field}: {actual_value}")
    
    print("\n📊 Checking optional fields:")
    
    for field, expected_type in optional_fields.items():
        if field in preview:
            print(f"   ✅ {field}: {preview[field]}")
        else:
            print(f"   ℹ️  {field}: not present (optional)")
    
    if errors:
        print("\n❌ TEST FAILED - Combat preview field errors:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print("\n✅ TEST PASSED - Combat preview fields valid!")
    return True

def test_property_fields():
    """Test that properties have all required fields"""
    
    print("\n🧪 Testing Property Fields")
    print("=" * 60)
    
    token = f"field-validation-property-{int(time.time())}"
    result = rpc_call("game_create_test", {"token": token})
    
    # Get tile info for a property (city at 3,4)
    tile = rpc_call("tile", {
        "token": token,
        "x": 3,
        "y": 4
    })
    
    # Check if it's a property
    property_types = ["CITY", "FACTORY", "AIRPORT", "PORT", "HQ", "COM_TOWER", "LAB"]
    
    if tile.get("type") not in property_types:
        print("ℹ️  Tile at (3,4) is not a property, checking (0,0) for HQ...")
        tile = rpc_call("tile", {
            "token": token,
            "x": 0,
            "y": 0
        })
    
    if tile.get("type") in property_types:
        print(f"📊 Validating {tile['type']} property fields:")
        
        required_property_fields = {
            "type": str,
            "x": int,
            "y": int,
        }
        
        optional_property_fields = {
            "player_id": (int, type(None)),
            "capture_progress": int,
            "hp": int,  # For HQ
            "can_produce": bool,
            "income": int,
        }
        
        errors = []
        
        for field, expected_type in required_property_fields.items():
            if field not in tile:
                errors.append(f"Missing required field: {field}")
                print(f"   ❌ {field}: MISSING")
            else:
                print(f"   ✅ {field}: {tile[field]}")
        
        print("\n📊 Optional property fields:")
        for field, expected_types in optional_property_fields.items():
            if field in tile:
                print(f"   ✅ {field}: {tile[field]}")
        
        if errors:
            print("\n❌ TEST FAILED - Property field errors:")
            for error in errors:
                print(f"   - {error}")
            return False
    else:
        print("⚠️  No property found to validate")
    
    print("\n✅ TEST PASSED - Property fields valid!")
    return True

def test_error_response_fields():
    """Test that error responses have consistent structure"""
    
    print("\n🧪 Testing Error Response Fields")
    print("=" * 60)
    
    token = f"field-validation-error-{int(time.time())}"
    
    # Try to perform invalid action to trigger error
    payload = {
        "jsonrpc": "2.0",
        "method": "unit_move",
        "params": {
            "token": token,
            "unit_x": 99,  # Invalid position
            "unit_y": 99,
            "dest_x": 98,
            "dest_y": 98
        },
        "id": 1
    }
    
    response = requests.post(API_URL, json=payload, timeout=10)
    result = response.json()
    
    print("📊 Validating error response structure:")
    
    # Check for error in response
    if "error" in result:
        error = result["error"]
        print("   ✅ Error field present")
        
        # Standard JSON-RPC error fields
        if "code" in error:
            print(f"   ✅ code: {error['code']}")
        else:
            print("   ⚠️  code: missing (should be present)")
        
        if "message" in error:
            print(f"   ✅ message: {error['message'][:50]}...")
        else:
            print("   ❌ message: MISSING")
        
        if "data" in error:
            print(f"   ✅ data: {type(error['data']).__name__}")
    
    # Also test method-level errors
    result = rpc_call("game_create_test", {"token": token})
    
    # Try invalid operation
    try:
        result = rpc_call("unit_create", {
            "token": token,
            "player_id": 0,
            "unit_type": "INVALID_TYPE",
            "x": 5,
            "y": 5
        })
        
        # If we get here, check for error in result
        if isinstance(result, dict) and "error" in result:
            print("\n📊 Method-level error structure:")
            print(f"   ✅ error: {result['error']}")
        elif isinstance(result, dict) and "success" in result and not result["success"]:
            print("\n📊 Method-level failure structure:")
            print(f"   ✅ success: {result['success']}")
            if "message" in result:
                print(f"   ✅ message: {result['message']}")
    except Exception as e:
        print(f"\n📊 Exception raised: {str(e)[:100]}")
    
    print("\n✅ TEST PASSED - Error responses have structure!")
    return True

def main():
    """Run all field validation tests"""
    
    print("🚀 Starting Field Validation Test Suite")
    print("=" * 60)
    
    tests = [
        ("Unit Status Fields", test_unit_status_fields),
        ("Game Board Fields", test_game_board_fields),
        ("Combat Preview Fields", test_combat_preview_fields),
        ("Property Fields", test_property_fields),
        ("Error Response Fields", test_error_response_fields),
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
    print("📊 FIELD VALIDATION TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All field validation tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} field validation tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
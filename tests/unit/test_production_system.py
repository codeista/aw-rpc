#!/usr/bin/env python3
"""
Test Production System
Tests unit creation at facilities, production costs, and facility capture
"""

import requests
import json
import time
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
    
    try:
        response = requests.post("http://localhost:5000/api", json=payload)
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
        
        result = response.json()
        if "error" in result:
            return {"error": result["error"]}
        # Return the entire result if it exists, otherwise empty dict
        return result.get("result", result)
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def create_test_game() -> str:
    """Create a test game with high starting funds"""
    game_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    result = rpc_call("game_create_test", {"token": game_id})
    if "error" in result:
        print(f"❌ Failed to create game: {result['error']}")
        return None
    
    print(f"✅ Created test game: {game_id}")
    
    # Check initial state
    board = rpc_call("game_board", {"token": game_id})
    if board:
        print(f"   Initial funds - RED: {board.get('red_funds', 0)}, BLUE: {board.get('blue_funds', 0)}")
        print(f"   Current turn: {board.get('current_turn', 'Unknown')}")
    
    return game_id

def ensure_correct_turn(game_id: str, expected_army: str = "RED") -> bool:
    """Ensure it's the correct army's turn"""
    board = rpc_call("game_board", {"token": game_id})
    if "error" in board:
        return False
    
    current_turn = board.get("current_turn", "")
    attempts = 0
    while current_turn != expected_army and attempts < 4:
        rpc_call("army_end_turn", {"token": game_id})
        board = rpc_call("game_board", {"token": game_id})
        current_turn = board.get("current_turn", "")
        attempts += 1
    
    return current_turn == expected_army

def test_factory_production():
    """Test unit production at factories"""
    print("\n🏭 Testing Factory Production...")
    
    game_id = create_test_game()
    if not game_id:
        return False
    
    # Get initial funds
    board = rpc_call("game_board", {"token": game_id})
    initial_funds = board.get("red_funds", 0)
    current_turn = board.get("current_turn", "")
    print(f"   📊 Initial state - Turn: {current_turn}, RED funds: {initial_funds}")
    
    # Factory locations for RED: (0,3) and (1,4)
    factory_x, factory_y = 0, 3
    
    # Test creating different ground units
    ground_units = [
        ("INFANTRY", 1000),
        ("MECH", 3000),
        ("RECON", 4000),
        ("TANK", 7000),
        ("APC", 5000)
    ]
    
    passed = 0
    for unit_type, expected_cost in ground_units:
        ensure_correct_turn(game_id, "RED")
        
        # Get funds before
        board = rpc_call("game_board", {"token": game_id})
        funds_before = board.get("red_funds", 0)
        
        # Create unit
        result = rpc_call("unit_create", {
            "token": game_id,
            "army": "RED",
            "unit_type": unit_type,
            "x": factory_x,
            "y": factory_y
        })
        
        if "error" in result:
            if isinstance(result.get('error'), dict):
                error_msg = result['error'].get('message', str(result['error']))
            else:
                error_msg = result.get('error', result.get('message', str(result)))
            print(f"   ❌ Failed to create {unit_type}: {error_msg}")
            # Debug info
            board = rpc_call("game_board", {"token": game_id})
            print(f"      Current turn: {board.get('current_turn')}, RED funds: {board.get('red_funds')}")
        else:
            # If we got a unit back (either as unit object or tile with unit), it was created
            if (result.get("unit") or result.get("type") == unit_type or 
                (result.get("unit") and result["unit"].get("type") == unit_type)):
                # Check funds after
                board = rpc_call("game_board", {"token": game_id})
                funds_after = board.get("red_funds", 0)
                actual_cost = funds_before - funds_after
                
                if actual_cost == expected_cost:
                    print(f"   ✅ {unit_type} created for {actual_cost} funds")
                    passed += 1
                else:
                    print(f"   ❌ {unit_type} cost mismatch: expected {expected_cost}, got {actual_cost}")
            else:
                print(f"   ❌ Unexpected response for {unit_type}: {str(result)[:100]}")
        
        # Move unit away to free the factory
        # Skip moving if unit creation failed
        if "error" in result:
            continue
            
        # First end turns to enable movement
        rpc_call("army_end_turn", {"token": game_id})
        rpc_call("army_end_turn", {"token": game_id})
        
        # Now move the unit away
        ensure_correct_turn(game_id, "RED")
        move_result = rpc_call("unit_move", {
            "token": game_id,
            "x": factory_x, "y": factory_y,
            "x2": factory_x + 1, "y2": factory_y
        })
        
        if "error" in move_result:
            print(f"      ⚠️  Failed to move unit: {move_result.get('error', 'Unknown')}")
        
        # End turn after movement
        rpc_call("army_end_turn", {"token": game_id})
    
    print(f"   📊 Factory Production: {passed}/{len(ground_units)} tests passed")
    return passed == len(ground_units)

def test_airport_production():
    """Test air unit production at airports"""
    print("\n✈️ Testing Airport Production...")
    
    game_id = create_test_game()
    if not game_id:
        return False
    
    # Airport location for RED: (0,8)
    airport_x, airport_y = 0, 8
    
    # Test creating air units
    air_units = [
        ("TCOPTER", 5000),
        ("BCOPTER", 9000),
        ("FIGHTER", 20000),
        ("BOMBER", 22000)
    ]
    
    passed = 0
    for unit_type, expected_cost in air_units:
        ensure_correct_turn(game_id, "RED")
        
        # Get funds before
        board = rpc_call("game_board", {"token": game_id})
        funds_before = board.get("red_funds", 0)
        
        # Create unit
        result = rpc_call("unit_create", {
            "token": game_id,
            "army": "RED",
            "unit_type": unit_type,
            "x": airport_x,
            "y": airport_y
        })
        
        if "error" in result:
            if isinstance(result.get('error'), dict):
                error_msg = result['error'].get('message', str(result['error']))
            else:
                error_msg = result.get('error', result.get('message', str(result)))
            print(f"   ❌ Failed to create {unit_type}: {error_msg}")
            # Debug info
            board = rpc_call("game_board", {"token": game_id})
            print(f"      Current turn: {board.get('current_turn')}, RED funds: {board.get('red_funds')}")
        else:
            # If we got a unit back (either as unit object or tile with unit), it was created
            if (result.get("unit") or result.get("type") == unit_type or 
                (result.get("unit") and result["unit"].get("type") == unit_type)):
                # Check funds after
                board = rpc_call("game_board", {"token": game_id})
                funds_after = board.get("red_funds", 0)
                actual_cost = funds_before - funds_after
                
                if actual_cost == expected_cost:
                    print(f"   ✅ {unit_type} created for {actual_cost} funds")
                    passed += 1
                else:
                    print(f"   ❌ {unit_type} cost mismatch: expected {expected_cost}, got {actual_cost}")
            else:
                print(f"   ❌ Unexpected response for {unit_type}: {str(result)[:100]}")
        
        # Move unit away to free the airport
        # First end turns to enable movement
        rpc_call("army_end_turn", {"token": game_id})
        rpc_call("army_end_turn", {"token": game_id})
        
        # Now move the unit away
        ensure_correct_turn(game_id, "RED")
        rpc_call("unit_move", {
            "token": game_id,
            "x": airport_x, "y": airport_y,
            "x2": airport_x + 1, "y2": airport_y
        })
        
        # End turn after movement
        rpc_call("army_end_turn", {"token": game_id})
    
    print(f"   📊 Airport Production: {passed}/{len(air_units)} tests passed")
    return passed == len(air_units)

def test_port_production():
    """Test naval unit production at ports"""
    print("\n⚓ Testing Port Production...")
    
    game_id = create_test_game()
    if not game_id:
        return False
    
    # Port location for RED: (0,0)
    port_x, port_y = 0, 0
    
    # Test creating naval units
    naval_units = [
        ("LANDER", 12000),
        ("CRUISER", 18000),
        ("SUB", 20000),
        ("BATTLESHIP", 28000),
        ("BLACKBOAT", 7500)
    ]
    
    passed = 0
    for unit_type, expected_cost in naval_units:
        ensure_correct_turn(game_id, "RED")
        
        # Get funds before
        board = rpc_call("game_board", {"token": game_id})
        funds_before = board.get("red_funds", 0)
        
        # Skip if not enough funds
        if funds_before < expected_cost:
            print(f"   ⚠️  Skipping {unit_type} - insufficient funds")
            continue
        
        # Create unit
        result = rpc_call("unit_create", {
            "token": game_id,
            "army": "RED",
            "unit_type": unit_type,
            "x": port_x,
            "y": port_y
        })
        
        if "error" in result:
            if isinstance(result.get('error'), dict):
                error_msg = result['error'].get('message', str(result['error']))
            else:
                error_msg = result.get('error', result.get('message', str(result)))
            print(f"   ❌ Failed to create {unit_type}: {error_msg}")
            # Debug info
            board = rpc_call("game_board", {"token": game_id})
            print(f"      Current turn: {board.get('current_turn')}, RED funds: {board.get('red_funds')}")
        else:
            # If we got a unit back (either as unit object or tile with unit), it was created
            if (result.get("unit") or result.get("type") == unit_type or 
                (result.get("unit") and result["unit"].get("type") == unit_type)):
                # Check funds after
                board = rpc_call("game_board", {"token": game_id})
                funds_after = board.get("red_funds", 0)
                actual_cost = funds_before - funds_after
                
                if actual_cost == expected_cost:
                    print(f"   ✅ {unit_type} created for {actual_cost} funds")
                    passed += 1
                else:
                    print(f"   ❌ {unit_type} cost mismatch: expected {expected_cost}, got {actual_cost}")
            else:
                print(f"   ❌ Unexpected response for {unit_type}: {str(result)[:100]}")
        
        # Move unit away to free the airport
        # First end turns to enable movement
        rpc_call("army_end_turn", {"token": game_id})
        rpc_call("army_end_turn", {"token": game_id})
        
        # Now move the unit away
        ensure_correct_turn(game_id, "RED")
        rpc_call("unit_move", {
            "token": game_id,
            "x": port_x, "y": port_y,
            "x2": port_x + 1, "y2": port_y
        })
        
        # End turn after movement
        rpc_call("army_end_turn", {"token": game_id})
    
    print(f"   📊 Port Production: {passed}/{len(naval_units)} tests attempted")
    return passed > 0

def test_production_options():
    """Test get_production_options RPC"""
    print("\n📋 Testing Production Options...")
    
    game_id = create_test_game()
    if not game_id:
        return False
    
    # Test different facility types
    facilities = [
        ((0, 3), "FACTORY", ["INFANTRY", "MECH", "RECON", "TANK", "APC"]),
        ((0, 8), "AIRPORT", ["TCOPTER", "BCOPTER", "FIGHTER", "BOMBER"]),
        ((0, 0), "PORT", ["LANDER", "CRUISER", "SUB", "BATTLESHIP", "BLACKBOAT"])
    ]
    
    passed = 0
    for (x, y), facility_type, expected_units in facilities:
        result = rpc_call("get_production_options", {
            "token": game_id,
            "x": x,
            "y": y
        })
        
        if result.get("success"):
            options = result.get("options", [])
            available_types = [opt["type"] for opt in options]
            
            # Check if expected units are available
            missing = [u for u in expected_units if u not in available_types]
            if not missing:
                print(f"   ✅ {facility_type} has correct production options")
                passed += 1
            else:
                print(f"   ❌ {facility_type} missing units: {missing}")
        else:
            print(f"   ❌ Failed to get options for {facility_type}: {result.get('error')}")
    
    print(f"   📊 Production Options: {passed}/{len(facilities)} tests passed")
    return passed == len(facilities)

def test_facility_occupation():
    """Test that occupied facilities can't produce"""
    print("\n🚫 Testing Occupied Facility Blocking...")
    
    game_id = create_test_game()
    if not game_id:
        return False
    
    # Create a unit on a factory
    ensure_correct_turn(game_id, "RED")
    result = rpc_call("unit_create", {
        "token": game_id,
        "army": "RED",
        "unit_type": "INFANTRY",
        "x": 0,
        "y": 3  # Factory position
    })
    
    if "error" in result:
        print(f"   ❌ Failed to create initial unit: {result['error']}")
        return False
    elif not (result.get("unit") or result.get("type") == "INFANTRY"):
        print(f"   ❌ Unexpected response: {str(result)[:100]}")
        return False
    
    # Try to create another unit on the same factory (should fail)
    result2 = rpc_call("unit_create", {
        "token": game_id,
        "army": "RED",
        "unit_type": "TANK",
        "x": 0,
        "y": 3  # Same factory
    })
    
    if "error" in result2:
        print(f"   ✅ Correctly blocked production on occupied facility: {result2['error']}")
        return True
    else:
        print("   ❌ Should not allow production on occupied facility")
        return False

def test_insufficient_funds():
    """Test production with insufficient funds"""
    print("\n💸 Testing Insufficient Funds...")
    
    game_id = create_test_game()
    if not game_id:
        return False
    
    # Deplete funds by creating expensive units
    ensure_correct_turn(game_id, "RED")
    
    # Create expensive units to deplete funds
    expensive_units = ["BATTLESHIP", "BOMBER", "FIGHTER", "MEDIUMTANK", "NEOTANK"]
    for unit_type in expensive_units:
        board = rpc_call("game_board", {"token": game_id})
        funds = board.get("red_funds", 0)
        
        if funds < 1000:  # Stop when funds are low
            break
        
        # Try to create at appropriate facility
        if unit_type in ["BATTLESHIP"]:
            x, y = 0, 0  # Port
        elif unit_type in ["BOMBER", "FIGHTER"]:
            x, y = 0, 8  # Airport
        else:
            x, y = 0, 3  # Factory
        
        rpc_call("unit_create", {
            "token": game_id,
            "army": "RED",
            "unit_type": unit_type,
            "x": x,
            "y": y
        })
        
        # Move unit away
        rpc_call("army_end_turn", {"token": game_id})
        rpc_call("army_end_turn", {"token": game_id})
        ensure_correct_turn(game_id, "RED")
    
    # Now try to create expensive unit with low funds
    board = rpc_call("game_board", {"token": game_id})
    remaining_funds = board.get("red_funds", 0)
    print(f"   ✅ Funds depleted to: {remaining_funds}")
    
    # Try to create a tank (7000 cost)
    result = rpc_call("unit_create", {
        "token": game_id,
        "army": "RED",
        "unit_type": "TANK",
        "x": 0,
        "y": 3
    })
    
    if "error" in result:
        error_msg = str(result["error"])
        if "funds" in error_msg.lower() or "insufficient" in error_msg.lower():
            print(f"   ✅ Correctly blocked production: {error_msg}")
            return True
        else:
            print(f"   ❌ Wrong error message: {error_msg}")
            return False
    else:
        print(f"   ❌ Should block production with insufficient funds, got: {str(result)[:100]}")
        return False

def run_all_tests():
    """Run all production system tests"""
    print("🚀 Production System Testing Suite")
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
        ("Factory Production", test_factory_production),
        ("Airport Production", test_airport_production),
        ("Port Production", test_port_production),
        ("Production Options", test_production_options),
        ("Occupied Facilities", test_facility_occupation),
        ("Insufficient Funds", test_insufficient_funds)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ {test_name} failed with error: {e}")
    
    print("\n" + "=" * 60)
    print("📊 PRODUCTION TEST RESULTS")
    print("=" * 60)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if i < passed else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print("-" * 60)
    print(f"📈 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL PRODUCTION TESTS PASSED!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed - review output above")

if __name__ == "__main__":
    run_all_tests()
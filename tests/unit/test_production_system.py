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
        
        # Check if result contains an error structure
        result_data = result.get("result", result)
        if isinstance(result_data, dict) and result_data.get("error") == True:
            # This is an error response wrapped in result
            return {"error": result_data.get("message", "Unknown error")}
        
        return result_data
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
        red_funds = get_player_funds(board, "RED")
        blue_funds = get_player_funds(board, "BLUE")
        print(f"   Initial funds - RED: {red_funds}, BLUE: {blue_funds}")
        print(f"   Current turn: {board.get('current_turn', 'Unknown')}")
    
    return game_id

def get_player_funds(board: dict, player: str = "RED") -> int:
    """Get funds for a player, handling both v1 and v2 board formats"""
    if player == "RED":
        # Try red_funds first
        funds = board.get("red_funds", 0)
        if funds == 0 or funds is None:
            # Try player_funds for v2 games
            player_funds = board.get("player_funds", {})
            funds = int(player_funds.get("0", 0))  # Player 0 is RED
        return funds
    elif player == "BLUE":
        # Try blue_funds first
        funds = board.get("blue_funds", 0)
        if funds == 0 or funds is None:
            # Try player_funds for v2 games
            player_funds = board.get("player_funds", {})
            funds = int(player_funds.get("1", 0))  # Player 1 is BLUE
        return funds
    return 0

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
    initial_funds = get_player_funds(board, "RED")
    current_turn = board.get("current_turn", "")
    print(f"   📊 Initial state - Turn: {current_turn}, RED funds: {initial_funds}")
    
    # Factory locations for RED: (0,3) and (1,4)
    factory_x, factory_y = 0, 4
    
    # Test creating different ground units
    ground_units = [
        ("INFANTRY", 1000),
        ("MECH", 3000),
        ("RECON", 4000),
        ("TANK", 7000),
        ("APC", 5000)
    ]
    
    passed = 0
    unit_index = 0
    for unit_type, expected_cost in ground_units:
        ensure_correct_turn(game_id, "RED")
        
        # Get funds before
        board = rpc_call("game_board", {"token": game_id})
        funds_before = get_player_funds(board, "RED")
        
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
            print(f"      Current turn: {board.get('current_turn')}, RED funds: {get_player_funds(board, 'RED')}")
        else:
            # Successful unit creation returns tile info with the unit
            # Check if response contains tile info with a unit
            if "mapTile" in result and "unit" in result:
                unit_in_result = result.get("unit", {})
                if unit_in_result.get("type") == unit_type:
                    # Check funds after
                    board = rpc_call("game_board", {"token": game_id})
                    funds_after = get_player_funds(board, "RED")
                    actual_cost = funds_before - funds_after
                    
                    if actual_cost == expected_cost:
                        print(f"   ✅ {unit_type} created for {actual_cost} funds")
                        passed += 1
                    else:
                        print(f"   ❌ {unit_type} cost mismatch: expected {expected_cost}, got {actual_cost}")
                else:
                    print(f"   ❌ Wrong unit type created: expected {unit_type}, got {unit_in_result.get('type')}")
            else:
                print(f"   ❌ Unexpected response format for {unit_type}: {str(result)[:100]}")
        
        # Move unit away to free the factory
        # Skip moving if unit creation failed
        if "error" in result:
            continue
            
        # First end turns to enable movement
        rpc_call("army_end_turn", {"token": game_id})
        rpc_call("army_end_turn", {"token": game_id})
        
        # Now move the unit away
        ensure_correct_turn(game_id, "RED")
        # Move to different locations to avoid collision
        # INFANTRY to (1,4), MECH to (0,3), RECON to (0,5), etc.
        move_offsets = [(1, 0), (0, -1), (0, 1), (1, 1), (1, -1)]
        dx, dy = move_offsets[unit_index % len(move_offsets)]
        move_result = rpc_call("unit_move", {
            "token": game_id,
            "x": factory_x, "y": factory_y,
            "x2": factory_x + dx, "y2": factory_y + dy
        })
        unit_index += 1
        
        if "error" in move_result:
            if isinstance(move_result.get('error'), dict):
                error_msg = move_result['error'].get('message', str(move_result['error']))
            else:
                error_msg = move_result.get('message', move_result.get('error', 'Unknown'))
            print(f"      ⚠️  Failed to move unit: {error_msg}")
        else:
            # Move successful - check if it returned tile info
            if "mapTile" in move_result or "x" in move_result:
                print(f"      ✅ Unit moved successfully")
        
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
    
    # Airport location for RED: (0,7)
    airport_x, airport_y = 0, 7
    
    # Test creating air units
    air_units = [
        ("TCOPTER", 5000),
        ("BCOPTER", 9000),
        ("FIGHTER", 20000),
        ("BOMBER", 22000)
    ]
    
    passed = 0
    unit_index = 0
    for unit_type, expected_cost in air_units:
        ensure_correct_turn(game_id, "RED")
        
        # Get funds before
        board = rpc_call("game_board", {"token": game_id})
        funds_before = get_player_funds(board, "RED")
        
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
            print(f"      Current turn: {board.get('current_turn')}, RED funds: {get_player_funds(board, 'RED')}")
        else:
            # Successful unit creation returns tile info with the unit
            # Check if response contains tile info with a unit
            if "mapTile" in result and "unit" in result:
                unit_in_result = result.get("unit", {})
                if unit_in_result.get("type") == unit_type:
                    # Check funds after
                    board = rpc_call("game_board", {"token": game_id})
                    funds_after = get_player_funds(board, "RED")
                    actual_cost = funds_before - funds_after
                    
                    if actual_cost == expected_cost:
                        print(f"   ✅ {unit_type} created for {actual_cost} funds")
                        passed += 1
                    else:
                        print(f"   ❌ {unit_type} cost mismatch: expected {expected_cost}, got {actual_cost}")
                else:
                    print(f"   ❌ Wrong unit type created: expected {unit_type}, got {unit_in_result.get('type')}")
            else:
                print(f"   ❌ Unexpected response format for {unit_type}: {str(result)[:100]}")
        
        # Move unit away to free the airport
        # First end turns to enable movement
        rpc_call("army_end_turn", {"token": game_id})
        rpc_call("army_end_turn", {"token": game_id})
        
        # Now move the unit away
        ensure_correct_turn(game_id, "RED")
        # Move to different locations to avoid collision
        move_offsets = [(1, 0), (0, -1), (0, 1), (-1, 0)]
        dx, dy = move_offsets[unit_index % len(move_offsets)]
        rpc_call("unit_move", {
            "token": game_id,
            "x": airport_x, "y": airport_y,
            "x2": airport_x + dx, "y2": airport_y + dy
        })
        unit_index += 1
        
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
    unit_index = 0
    for unit_type, expected_cost in naval_units:
        ensure_correct_turn(game_id, "RED")
        
        # Get funds before
        board = rpc_call("game_board", {"token": game_id})
        funds_before = get_player_funds(board, "RED")
        
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
            print(f"      Current turn: {board.get('current_turn')}, RED funds: {get_player_funds(board, 'RED')}")
        else:
            # Successful unit creation returns tile info with the unit
            # Check if response contains tile info with a unit
            if "mapTile" in result and "unit" in result:
                unit_in_result = result.get("unit", {})
                if unit_in_result.get("type") == unit_type:
                    # Check funds after
                    board = rpc_call("game_board", {"token": game_id})
                    funds_after = get_player_funds(board, "RED")
                    actual_cost = funds_before - funds_after
                    
                    if actual_cost == expected_cost:
                        print(f"   ✅ {unit_type} created for {actual_cost} funds")
                        passed += 1
                    else:
                        print(f"   ❌ {unit_type} cost mismatch: expected {expected_cost}, got {actual_cost}")
                else:
                    print(f"   ❌ Wrong unit type created: expected {unit_type}, got {unit_in_result.get('type')}")
            else:
                print(f"   ❌ Unexpected response format for {unit_type}: {str(result)[:100]}")
        
        # Move unit away to free the airport
        # First end turns to enable movement
        rpc_call("army_end_turn", {"token": game_id})
        rpc_call("army_end_turn", {"token": game_id})
        
        # Now move the unit away
        ensure_correct_turn(game_id, "RED")
        # Move to different locations to avoid collision
        move_offsets = [(1, 0), (0, 1), (2, 0), (1, 1), (2, 1)]
        dx, dy = move_offsets[unit_index % len(move_offsets)]
        rpc_call("unit_move", {
            "token": game_id,
            "x": port_x, "y": port_y,
            "x2": port_x + dx, "y2": port_y + dy
        })
        unit_index += 1
        
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
        ((0, 4), "FACTORY", ["INFANTRY", "MECH", "RECON", "TANK", "APC"]),
        ((0, 7), "AIRPORT", ["TCOPTER", "BCOPTER", "FIGHTER", "BOMBER"]),
        ((0, 0), "PORT", ["LANDER", "CRUISER", "SUB", "BATTLESHIP", "BLACKBOAT"])
    ]
    
    passed = 0
    for (x, y), facility_type, expected_units in facilities:
        result = rpc_call("get_production_options", {
            "token": game_id,
            "x": x,
            "y": y
        })
        
        if "error" not in result:
            # Check the response structure
            if result.get("success") == True and "production_options" in result:
                options = result.get("production_options", {}).get("units", [])
                available_types = [opt["type"] for opt in options if isinstance(opt, dict)]
            else:
                # Handle direct response format
                options = result.get("units", [])
                available_types = [opt["type"] for opt in options if isinstance(opt, dict)]
            
            # Check if expected units are available
            missing = [u for u in expected_units if u not in available_types]
            if not missing and available_types:
                print(f"   ✅ {facility_type} has correct production options")
                passed += 1
            else:
                if not available_types:
                    print(f"   ❌ {facility_type} returned no units")
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
        "y": 4  # Factory position
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
        "y": 4  # Same factory
    })
    
    if "error" in result2:
        error_msg = result2.get('error', 'Unknown')
        # Any error is good - it means production was blocked
        print(f"   ✅ Correctly blocked production on occupied facility: {error_msg}")
        return True
    else:
        # Check if a unit was actually created
        if "mapTile" in result2 and "unit" in result2:
            print("   ❌ Should not allow production on occupied facility - unit was created!")
            return False
        else:
            print("   ❌ Unexpected response when facility should be occupied")
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
    # Use only units that we know work from our tests
    units_to_create = [
        ("BOMBER", 22000, 0, 7),  # Airport
        ("FIGHTER", 20000, 0, 7),  # Airport  
        ("BATTLESHIP", 28000, 0, 0),  # Port
    ]
    
    for unit_type, cost, x, y in units_to_create:
        board = rpc_call("game_board", {"token": game_id})
        funds = get_player_funds(board, "RED")
        
        if funds < 8000:  # Stop when funds are too low for TANK (7000)
            break
        
        if funds >= cost:
            result = rpc_call("unit_create", {
                "token": game_id,
                "army": "RED",
                "unit_type": unit_type,
                "x": x,
                "y": y
            })
            
            if "error" not in result:
                print(f"   Created {unit_type} for {cost} funds")
                # Delete unit to free facility
                rpc_call("unit_delete", {"token": game_id, "x": x, "y": y})
    
    # Now try to create expensive unit with low funds
    board = rpc_call("game_board", {"token": game_id})
    remaining_funds = get_player_funds(board, "RED")
    print(f"   ✅ Funds depleted to: {remaining_funds}")
    
    # Try to create something more expensive than remaining funds
    # If we have 8000, try BCOPTER (9000) at airport
    if remaining_funds < 10000:
        unit_to_try = "BCOPTER"
        cost_needed = 9000
        x, y = 0, 7  # Airport
    else:
        # Try something even more expensive
        unit_to_try = "FIGHTER"
        cost_needed = 20000
        x, y = 0, 7  # Airport
        
    print(f"   Trying to create {unit_to_try} (cost: {cost_needed}) with {remaining_funds} funds")
    
    result = rpc_call("unit_create", {
        "token": game_id,
        "army": "RED",
        "unit_type": unit_to_try,
        "x": x,
        "y": y
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
        # Check if unit was actually created (successful response contains tile info)
        if "mapTile" in result and "unit" in result:
            # Unit was created - check if we have sufficient funds
            if remaining_funds >= cost_needed:
                print(f"   ❌ Unit created but test expected insufficient funds (had {remaining_funds} funds, needed {cost_needed})")
            else:
                print(f"   ❌ Unit created with insufficient funds! Had {remaining_funds}, needed {cost_needed}")
            return False
        else:
            print(f"   ❌ Unexpected response format: {str(result)[:100]}")
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
    results = {}
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                results[test_name] = True
            else:
                results[test_name] = False
        except Exception as e:
            print(f"\n❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 60)
    print("📊 PRODUCTION TEST RESULTS")
    print("=" * 60)
    
    for test_name, _ in tests:
        status = "✅ PASS" if results.get(test_name, False) else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print("-" * 60)
    print(f"📈 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL PRODUCTION TESTS PASSED!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed - review output above")

if __name__ == "__main__":
    run_all_tests()
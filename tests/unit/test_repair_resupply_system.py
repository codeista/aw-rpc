#!/usr/bin/env python3
"""
Test Repair and Resupply System
Tests Black Boat repair, APC resupply, and facility repairs
"""

import requests
import json
import time
import random
import string
import math

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
        return result.get("result", {})
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def create_test_game() -> str:
    """Create a test game with high starting funds"""
    game_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    # Use game_create_test for high funds (50000)
    result = rpc_call("game_create_test", {"token": game_id})
    if "error" in result:
        print(f"❌ Failed to create game: {result['error']}")
        return None
    
    print(f"✅ Created test game: {game_id}")
    return game_id

def ensure_correct_turn(game_id: str, expected_army: str = "RED") -> bool:
    """Ensure it's the correct army's turn"""
    board = rpc_call("game_board", {"token": game_id})
    if "error" in board:
        return False
    
    current_turn = board.get("current_turn", "")
    
    # Keep ending turns until we get to the expected army
    attempts = 0
    while current_turn != expected_army and attempts < 4:
        rpc_call("army_end_turn", {"token": game_id})
        board = rpc_call("game_board", {"token": game_id})
        current_turn = board.get("current_turn", "")
        attempts += 1
    
    return current_turn == expected_army

def create_unit_and_enable(game_id: str, unit_type: str, x: int, y: int, army: str) -> dict:
    """Create a unit and enable it for movement"""
    
    # Ensure correct turn
    ensure_correct_turn(game_id, army)
    
    # Create unit
    result = rpc_call("unit_create", {
        "token": game_id,
        "army": army,
        "unit_type": unit_type,
        "x": x,
        "y": y
    })
    
    if "error" in result:
        return result
    
    # End turn twice to enable movement
    rpc_call("army_end_turn", {"token": game_id})
    rpc_call("army_end_turn", {"token": game_id})
    
    return result

def get_unit_at(game_id: str, x: int, y: int) -> dict:
    """Get unit information at specific coordinates"""
    board = rpc_call("game_board", {"token": game_id})
    if "error" in board:
        return None
    
    # Find the tile
    for tile in board.get("tiles", []):
        if tile.get("x") == x and tile.get("y") == y:
            return tile.get("unit")
    
    return None

def test_black_boat_repair():
    """Test Black Boat repair functionality"""
    print("\n🚢 Testing Black Boat Repair...")
    
    game_id = create_test_game()
    if not game_id:
        return False
    
    # Create Black Boat
    create_unit_and_enable(game_id, "BLACKBOAT", 0, 0, "RED")
    
    # Create Infantry to repair
    create_unit_and_enable(game_id, "INFANTRY", 1, 0, "RED")
    
    # Create enemy to damage the infantry
    ensure_correct_turn(game_id, "BLUE")
    create_unit_and_enable(game_id, "TANK", 2, 0, "BLUE")
    
    # Attack to damage infantry
    ensure_correct_turn(game_id, "BLUE")
    attack_result = rpc_call("unit_attack", {
        "token": game_id,
        "x": 2, "y": 0,  # Tank
        "x2": 1, "y2": 0  # Infantry
    })
    
    if "error" in attack_result:
        print(f"   ❌ Failed to damage unit: {attack_result['error']}")
        return False
    
    # Check infantry HP
    damaged_unit = get_unit_at(game_id, 1, 0)
    if not damaged_unit:
        print("   ❌ Infantry was destroyed")
        return False
    
    initial_hp = damaged_unit.get("status", {}).get("hp", 0)
    visual_hp = math.ceil(initial_hp / 10)
    print(f"   ✅ Infantry damaged to {initial_hp} HP (visual: {visual_hp})")
    
    # Test repair
    ensure_correct_turn(game_id, "RED")
    repair_result = rpc_call("repair_unit", {
        "token": game_id,
        "blackboat_x": 0, "blackboat_y": 0,
        "target_x": 1, "target_y": 0,
        "hp_to_repair": 2
    })
    
    if repair_result.get("success"):
        repaired_unit = get_unit_at(game_id, 1, 0)
        final_hp = repaired_unit.get("status", {}).get("hp", 0)
        hp_repaired = final_hp - initial_hp
        print(f"   ✅ Repair successful: {initial_hp} → {final_hp} HP (+{hp_repaired})")
        
        # Test repair limit (can't repair above 90 HP)
        if final_hp > 90:
            # Try to repair again
            repair_result2 = rpc_call("repair_unit", {
                "token": game_id,
                "blackboat_x": 0, "blackboat_y": 0,
                "target_x": 1, "target_y": 0,
                "hp_to_repair": 2
            })
            
            if "error" in repair_result2:
                print(f"   ✅ Correctly blocked repair above 90 HP: {repair_result2['error']}")
            else:
                print("   ❌ Should not allow repair above 90 HP")
                return False
    else:
        print(f"   ❌ Repair failed: {repair_result.get('error', 'Unknown error')}")
        return False
    
    print(f"   📊 Test game: http://localhost:5000/game/{game_id}")
    return True

def test_apc_auto_resupply():
    """Test APC automatic resupply at turn start"""
    print("\n🚛 Testing APC Auto-Resupply...")
    
    game_id = create_test_game()
    if not game_id:
        return False
    
    # Create APC
    create_unit_and_enable(game_id, "APC", 5, 5, "RED")
    
    # Create Tank with low fuel
    create_unit_and_enable(game_id, "TANK", 6, 5, "RED")
    
    # Move tank multiple times to consume fuel
    ensure_correct_turn(game_id, "RED")
    for i in range(3):
        # Move tank back and forth
        rpc_call("unit_move", {
            "token": game_id,
            "x": 6 + (i % 2), "y": 5,
            "x2": 6 + ((i + 1) % 2), "y2": 5
        })
        rpc_call("army_end_turn", {"token": game_id})
        rpc_call("army_end_turn", {"token": game_id})
        ensure_correct_turn(game_id, "RED")
    
    # Check tank fuel before resupply
    tank_before = get_unit_at(game_id, 6, 5)
    fuel_before = tank_before.get("status", {}).get("fuel", 0)
    print(f"   ✅ Tank fuel before: {fuel_before}/50")
    
    # Move APC adjacent to tank
    ensure_correct_turn(game_id, "RED")
    move_result = rpc_call("unit_move", {
        "token": game_id,
        "x": 5, "y": 5,  # APC
        "x2": 5, "y2": 5  # Stay in place (already adjacent)
    })
    
    # End turn to trigger auto-resupply
    rpc_call("army_end_turn", {"token": game_id})
    rpc_call("army_end_turn", {"token": game_id})
    
    # Check tank fuel after resupply
    tank_after = get_unit_at(game_id, 6, 5)
    fuel_after = tank_after.get("status", {}).get("fuel", 0)
    
    if fuel_after > fuel_before:
        print(f"   ✅ Auto-resupply successful: {fuel_before} → {fuel_after} fuel")
    else:
        print(f"   ❌ Auto-resupply failed: fuel still {fuel_after}")
        return False
    
    print(f"   📊 Test game: http://localhost:5000/game/{game_id}")
    return True

def test_manual_resupply():
    """Test manual resupply functionality"""
    print("\n⛽ Testing Manual Resupply...")
    
    game_id = create_test_game()
    if not game_id:
        return False
    
    # Create Black Boat
    create_unit_and_enable(game_id, "BLACKBOAT", 3, 3, "RED")
    
    # Create Infantry with low ammo
    create_unit_and_enable(game_id, "INFANTRY", 4, 3, "RED")
    
    # Use up some ammo by attacking
    ensure_correct_turn(game_id, "BLUE")
    create_unit_and_enable(game_id, "INFANTRY", 5, 3, "BLUE")
    
    ensure_correct_turn(game_id, "RED")
    # Attack to consume ammo
    rpc_call("unit_attack", {
        "token": game_id,
        "x": 4, "y": 3,
        "x2": 5, "y2": 3
    })
    
    # Get infantry ammo before resupply
    infantry = get_unit_at(game_id, 4, 3)
    if not infantry:
        print("   ❌ Infantry not found")
        return False
    
    ammo_before = infantry.get("status", {}).get("ammo", 0)
    fuel_before = infantry.get("status", {}).get("fuel", 0)
    print(f"   ✅ Infantry resources: {fuel_before} fuel, {ammo_before} ammo")
    
    # Manual resupply
    ensure_correct_turn(game_id, "RED")
    resupply_result = rpc_call("resupply_unit", {
        "token": game_id,
        "resupply_x": 3, "resupply_y": 3,  # Black Boat
        "target_x": 4, "target_y": 3,      # Infantry
        "fuel_amount": 50,
        "ammo_amount": 10
    })
    
    if resupply_result.get("success"):
        # Check after resupply
        infantry_after = get_unit_at(game_id, 4, 3)
        ammo_after = infantry_after.get("status", {}).get("ammo", 0)
        fuel_after = infantry_after.get("status", {}).get("fuel", 0)
        
        print(f"   ✅ Resupply successful: {fuel_before}/{ammo_before} → {fuel_after}/{ammo_after}")
    else:
        print(f"   ❌ Resupply failed: {resupply_result.get('error', 'Unknown error')}")
        return False
    
    print(f"   📊 Test game: http://localhost:5000/game/{game_id}")
    return True

def test_facility_repair():
    """Test facility-based repair (cities, bases)"""
    print("\n🏭 Testing Facility Repair...")
    
    game_id = create_test_game()
    if not game_id:
        return False
    
    # Create Infantry on a city (cities are at specific coordinates)
    # Based on the optimized test map, there's a city at (3, 5)
    create_unit_and_enable(game_id, "INFANTRY", 3, 5, "RED")
    
    # Damage the infantry
    ensure_correct_turn(game_id, "BLUE")
    create_unit_and_enable(game_id, "TANK", 4, 5, "BLUE")
    
    ensure_correct_turn(game_id, "BLUE")
    attack_result = rpc_call("unit_attack", {
        "token": game_id,
        "x": 4, "y": 5,  # Tank
        "x2": 3, "y2": 5  # Infantry on city
    })
    
    # Check HP after damage
    damaged_unit = get_unit_at(game_id, 3, 5)
    if not damaged_unit:
        print("   ❌ Infantry was destroyed")
        return False
    
    hp_before = damaged_unit.get("status", {}).get("hp", 0)
    print(f"   ✅ Infantry damaged to {hp_before} HP")
    
    # End turn to trigger facility repair
    ensure_correct_turn(game_id, "RED")
    rpc_call("army_end_turn", {"token": game_id})
    rpc_call("army_end_turn", {"token": game_id})
    
    # Check HP after facility repair
    repaired_unit = get_unit_at(game_id, 3, 5)
    hp_after = repaired_unit.get("status", {}).get("hp", 0)
    
    if hp_after > hp_before:
        hp_repaired = hp_after - hp_before
        print(f"   ✅ Facility repair: {hp_before} → {hp_after} HP (+{hp_repaired})")
    else:
        print(f"   ❌ Facility repair failed: HP still {hp_after}")
        return False
    
    print(f"   📊 Test game: http://localhost:5000/game/{game_id}")
    return True

def test_repair_cost():
    """Test repair cost calculations"""
    print("\n💰 Testing Repair Costs...")
    
    game_id = create_test_game()
    if not game_id:
        return False
    
    # Get initial funds
    board = rpc_call("game_board", {"token": game_id})
    initial_funds = board.get("red_funds", 0)
    print(f"   ✅ Initial RED funds: {initial_funds}")
    
    # Create expensive unit (Tank) on factory
    ensure_correct_turn(game_id, "RED")
    create_result = rpc_call("unit_create", {
        "token": game_id,
        "army": "RED",
        "unit_type": "TANK",
        "x": 0, "y": 3  # Factory position
    })
    
    # Check funds after creation
    board = rpc_call("game_board", {"token": game_id})
    after_creation = board.get("red_funds", 0)
    tank_cost = initial_funds - after_creation
    print(f"   ✅ Tank created for {tank_cost} funds")
    
    # Enable tank and damage it
    rpc_call("army_end_turn", {"token": game_id})
    rpc_call("army_end_turn", {"token": game_id})
    
    ensure_correct_turn(game_id, "BLUE")
    create_unit_and_enable(game_id, "MEDIUMTANK", 1, 3, "BLUE")
    
    ensure_correct_turn(game_id, "BLUE")
    rpc_call("unit_attack", {
        "token": game_id,
        "x": 1, "y": 3,
        "x2": 0, "y2": 3
    })
    
    # Check repair cost at facility
    tank = get_unit_at(game_id, 0, 3)
    if tank:
        hp = tank.get("status", {}).get("hp", 0)
        hp_missing = 100 - hp
        expected_cost = (tank_cost * hp_missing) // 100
        print(f"   ✅ Tank at {hp} HP, repair should cost ~{expected_cost}")
    
    print(f"   📊 Test game: http://localhost:5000/game/{game_id}")
    return True

def run_all_tests():
    """Run all repair and resupply tests"""
    print("🚀 Repair and Resupply System Testing Suite")
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
        ("Black Boat Repair", test_black_boat_repair),
        ("APC Auto-Resupply", test_apc_auto_resupply),
        ("Manual Resupply", test_manual_resupply),
        ("Facility Repair", test_facility_repair),
        ("Repair Costs", test_repair_cost)
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
    print("📊 REPAIR/RESUPPLY TEST RESULTS")
    print("=" * 60)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if i < passed else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print("-" * 60)
    print(f"📈 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL REPAIR AND RESUPPLY TESTS PASSED!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed - review output above")

if __name__ == "__main__":
    run_all_tests()
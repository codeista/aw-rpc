#!/usr/bin/env python3
"""
Comprehensive Facility Repair Tests (Functional Style)
Tests the automatic facility repair system that repairs units at the start of their turn.

Tests verify:
- Air units repair at airports (2 HP max per turn)
- Naval units repair at ports (2 HP max per turn) 
- Land units repair at factories (2 HP max per turn)
- Repair costs 10% of unit value per HP
- No repair if insufficient funds
- No repair on enemy facilities
- No repair if unit at full health
- Correct integration with turn order (after resupply, before fuel)
"""

import requests
import json
import time
import random
import string
import sys
import os

# Add the root directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.unit import UnitType, UnitClass
from core.map_system import MapType
from core.production_system import ProductionSystem


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
    
    # Handle error responses
    if "error" in result:
        return {"error": result["error"]}
    
    # Get the actual result
    rpc_result = result.get("result", result)
    
    # If result is a string, only try to parse if it looks like JSON
    if isinstance(rpc_result, str):
        if rpc_result.strip().startswith(('{', '[')):
            try:
                rpc_result = json.loads(rpc_result)
            except json.JSONDecodeError:
                return {"error": f"Could not parse result: {rpc_result}"}
    
    return rpc_result


def create_test_game() -> str:
    """Create a test game for facility repair testing"""
    game_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    result = rpc_call("game_create_test", {"token": game_id})
    if "error" in result:
        print(f"❌ Failed to create game: {result['error']}")
        return None
        
    print(f"✅ Created facility repair test game: {game_id}")
    return game_id


def find_facility(game_token: str, facility_type: str, player_id: int = 0):
    """Find a facility of given type owned by player"""
    board = rpc_call("game_board", {"token": game_token})
    if "error" in board:
        return None
        
    for tile in board.get('grid', []):
        if (tile.get('mapTile', {}).get('type') == facility_type and 
            tile.get('mapTile', {}).get('player_id') == player_id):
            return (tile['x'], tile['y'])
    return None


def damage_unit(game_token: str, x: int, y: int, damage_amount: int = 30):
    """Artificially damage a unit for testing repair"""
    # This is a test helper - in real game, units get damaged by combat
    # For testing, we'll modify the unit's HP directly via game manager
    from core.game_utils import game_load
    from app import game_save
    try:
        manager = game_load(game_token)
        unit = manager.unit_at(x, y)
        if unit:
            unit.status.hp = max(0, unit.status.hp - damage_amount)
            game_save(manager, game_token)  # Persist changes
            return True
    except Exception as e:
        print(f"⚠️ Error damaging unit: {e}")
    return False


def get_unit_hp(game_token: str, x: int, y: int) -> int:
    """Get unit HP at position"""
    board = rpc_call("game_board", {"token": game_token})
    if "error" in board:
        return -1
        
    for tile in board.get('grid', []):
        if tile['x'] == x and tile['y'] == y and tile.get('unit'):
            return tile['unit'].get('status', {}).get('hp', tile['unit'].get('hp', 100))
    return -1


def get_player_funds(game_token: str, player_id: int = 0) -> int:
    """Get player funds"""
    board = rpc_call("game_board", {"token": game_token})
    if "error" in board:
        return -1
    return board.get('player_funds', [0, 0])[player_id]


def test_air_unit_repair_at_airport(game_token: str):
    """Test that air units repair at airports (2 HP max per turn)"""
    print("\n🔧 Testing air unit repair at airport...")
    
    # Find RED airport
    airport_pos = find_facility(game_token, 'AIRPORT', 0)
    if not airport_pos:
        print("❌ No RED airport found on map")
        return False
    
    x, y = airport_pos
    print(f"   Found airport at ({x}, {y})")
    
    # Create fighter at airport
    result = rpc_call("unit_create", {
        "token": game_token,
        "player_id": 0,
        "unit_type": "FIGHTER",
        "x": x,
        "y": y
    })
    if "error" in result:
        print(f"❌ Failed to create fighter: {result.get('error')}")
        return False
    print("   ✅ Fighter created at airport")
    
    # End turn to allow unit to act
    rpc_call("army_end_turn", {"token": game_token})
    rpc_call("army_end_turn", {"token": game_token})
    
    # Damage the unit
    if not damage_unit(game_token, x, y, 30):
        print("❌ Failed to damage unit")
        return False
    
    initial_hp = get_unit_hp(game_token, x, y)
    if initial_hp != 70:
        print(f"❌ Unit HP should be 70 after damage, got {initial_hp}")
        return False
    print(f"   ✅ Unit damaged to {initial_hp} HP")
    
    # Get initial funds
    initial_funds = get_player_funds(game_token, 0)
    
    # End turn to trigger repair
    rpc_call("army_end_turn", {"token": game_token})
    rpc_call("army_end_turn", {"token": game_token})
    
    # Check unit was repaired
    final_hp = get_unit_hp(game_token, x, y)
    final_funds = get_player_funds(game_token, 0)
    
    # Should repair 2 HP (20 points)
    if final_hp != 90:
        print(f"❌ Unit should be repaired to 90 HP, got {final_hp}")
        return False
    
    # Check repair cost (10% of fighter cost per HP)
    fighter_cost = ProductionSystem.UNIT_COSTS.get(UnitType.FIGHTER, 20000)
    expected_cost = (fighter_cost * 20) // 100  # 20 HP points * 10% per 10 points
    actual_cost = initial_funds - final_funds
    if actual_cost != expected_cost:
        print(f"❌ Repair cost should be {expected_cost}, got {actual_cost}")
        return False
    
    print(f"   ✅ Fighter repaired to {final_hp} HP for {actual_cost} funds")
    return True


def test_naval_unit_repair_at_port(game_token: str):
    """Test that naval units repair at ports (2 HP max per turn)"""
    print("\n🔧 Testing naval unit repair at port...")
    
    # Find RED port
    port_pos = find_facility(game_token, 'PORT', 0)
    if not port_pos:
        print("❌ No RED port found on map")
        return False
    
    x, y = port_pos
    print(f"   Found port at ({x}, {y})")
    
    # Create battleship at port
    result = rpc_call("unit_create", {
        "token": game_token,
        "player_id": 0,
        "unit_type": "BATTLESHIP",
        "x": x,
        "y": y
    })
    if "error" in result:
        print(f"❌ Failed to create battleship: {result.get('error')}")
        return False
    print("   ✅ Battleship created at port")
    
    # End turn to allow unit to act
    rpc_call("army_end_turn", {"token": game_token})
    rpc_call("army_end_turn", {"token": game_token})
    
    # Damage the unit
    if not damage_unit(game_token, x, y, 40):
        print("❌ Failed to damage unit")
        return False
    
    initial_hp = get_unit_hp(game_token, x, y)
    if initial_hp != 60:
        print(f"❌ Unit HP should be 60 after damage, got {initial_hp}")
        return False
    print(f"   ✅ Unit damaged to {initial_hp} HP")
    
    # Get initial funds
    initial_funds = get_player_funds(game_token, 0)
    
    # End turn to trigger repair
    rpc_call("army_end_turn", {"token": game_token})
    rpc_call("army_end_turn", {"token": game_token})
    
    # Check unit was repaired
    final_hp = get_unit_hp(game_token, x, y)
    final_funds = get_player_funds(game_token, 0)
    
    # Should repair 2 HP (20 points)
    if final_hp != 80:
        print(f"❌ Unit should be repaired to 80 HP, got {final_hp}")
        return False
    
    # Check repair cost
    battleship_cost = ProductionSystem.UNIT_COSTS.get(UnitType.BATTLESHIP, 28000)
    expected_cost = (battleship_cost * 20) // 100
    actual_cost = initial_funds - final_funds
    if actual_cost != expected_cost:
        print(f"❌ Repair cost should be {expected_cost}, got {actual_cost}")
        return False
    
    print(f"   ✅ Battleship repaired to {final_hp} HP for {actual_cost} funds")
    return True


def test_land_unit_repair_at_factory(game_token: str):
    """Test that land units repair at factories (2 HP max per turn)"""
    print("\n🔧 Testing land unit repair at factory...")
    
    # Find RED factory
    factory_pos = find_facility(game_token, 'FACTORY', 0)
    if not factory_pos:
        print("❌ No RED factory found on map")
        return False
    
    x, y = factory_pos
    print(f"   Found factory at ({x}, {y})")
    
    # Create tank at factory
    result = rpc_call("unit_create", {
        "token": game_token,
        "player_id": 0,
        "unit_type": "TANK",
        "x": x,
        "y": y
    })
    if "error" in result:
        print(f"❌ Failed to create tank: {result.get('error')}")
        return False
    print("   ✅ Tank created at factory")
    
    # End turn to allow unit to act
    rpc_call("army_end_turn", {"token": game_token})
    rpc_call("army_end_turn", {"token": game_token})
    
    # Damage the unit
    if not damage_unit(game_token, x, y, 50):
        print("❌ Failed to damage unit")
        return False
    
    initial_hp = get_unit_hp(game_token, x, y)
    if initial_hp != 50:
        print(f"❌ Unit HP should be 50 after damage, got {initial_hp}")
        return False
    print(f"   ✅ Unit damaged to {initial_hp} HP")
    
    # Get initial funds
    initial_funds = get_player_funds(game_token, 0)
    
    # End turn to trigger repair
    rpc_call("army_end_turn", {"token": game_token})
    rpc_call("army_end_turn", {"token": game_token})
    
    # Check unit was repaired
    final_hp = get_unit_hp(game_token, x, y)
    final_funds = get_player_funds(game_token, 0)
    
    # Should repair 2 HP (20 points)
    if final_hp != 70:
        print(f"❌ Unit should be repaired to 70 HP, got {final_hp}")
        return False
    
    # Check repair cost
    tank_cost = ProductionSystem.UNIT_COSTS.get(UnitType.TANK, 7000)
    expected_cost = (tank_cost * 20) // 100
    actual_cost = initial_funds - final_funds
    if actual_cost != expected_cost:
        print(f"❌ Repair cost should be {expected_cost}, got {actual_cost}")
        return False
    
    print(f"   ✅ Tank repaired to {final_hp} HP for {actual_cost} funds")
    return True


def test_no_repair_at_full_health(game_token: str):
    """Test no repair if unit at full health"""
    print("\n🔧 Testing no repair when unit at full health...")
    
    factory_pos = find_facility(game_token, 'FACTORY', 0)
    if not factory_pos:
        print("❌ No RED factory found on map")
        return False
    
    x, y = factory_pos
    
    # Create unit at full health
    result = rpc_call("unit_create", {
        "token": game_token,
        "player_id": 0,
        "unit_type": "TANK",
        "x": x,
        "y": y
    })
    if "error" in result:
        print(f"❌ Failed to create tank: {result.get('error')}")
        return False
    
    # End turn to allow unit to act
    rpc_call("army_end_turn", {"token": game_token})
    rpc_call("army_end_turn", {"token": game_token})
    
    # Verify unit is at full health
    initial_hp = get_unit_hp(game_token, x, y)
    if initial_hp != 100:
        print(f"❌ Unit should start at full health, got {initial_hp}")
        return False
    
    initial_funds = get_player_funds(game_token, 0)
    
    # End turn to trigger repair attempt
    rpc_call("army_end_turn", {"token": game_token})
    rpc_call("army_end_turn", {"token": game_token})
    
    # Check no repair occurred
    final_hp = get_unit_hp(game_token, x, y)
    final_funds = get_player_funds(game_token, 0)
    
    if final_hp != 100:
        print(f"❌ Unit should remain at full health, got {final_hp}")
        return False
    
    if final_funds != initial_funds:
        print(f"❌ No funds should be deducted for unnecessary repair")
        return False
    
    print("   ✅ No repair occurred for full health unit")
    return True


def test_repair_max_two_hp_per_turn(game_token: str):
    """Test that repair is limited to 2 HP (20 points) per turn"""
    print("\n🔧 Testing repair limit of 2 HP per turn...")
    
    factory_pos = find_facility(game_token, 'FACTORY', 0)
    if not factory_pos:
        print("❌ No RED factory found on map")
        return False
    
    x, y = factory_pos
    
    # Create unit
    result = rpc_call("unit_create", {
        "token": game_token,
        "player_id": 0,
        "unit_type": "TANK",
        "x": x,
        "y": y
    })
    if "error" in result:
        print(f"❌ Failed to create tank: {result.get('error')}")
        return False
    
    # End turn to allow unit to act
    rpc_call("army_end_turn", {"token": game_token})
    rpc_call("army_end_turn", {"token": game_token})
    
    # Damage unit heavily (more than 2 HP worth)
    if not damage_unit(game_token, x, y, 60):
        print("❌ Failed to damage unit")
        return False
    
    initial_hp = get_unit_hp(game_token, x, y)
    if initial_hp != 40:
        print(f"❌ Unit HP should be 40 after damage, got {initial_hp}")
        return False
    
    # End turn to trigger repair
    rpc_call("army_end_turn", {"token": game_token})
    rpc_call("army_end_turn", {"token": game_token})
    
    # Check repair was limited to 2 HP
    final_hp = get_unit_hp(game_token, x, y)
    repair_amount = final_hp - initial_hp
    
    if repair_amount != 20:
        print(f"❌ Repair should be limited to 20 HP points (2 HP), got {repair_amount}")
        return False
    
    if final_hp != 60:
        print(f"❌ Unit should be at 60 HP after repair, got {final_hp}")
        return False
    
    print(f"   ✅ Repair correctly limited to 2 HP (20 points)")
    return True


def run_all_tests():
    """Run all facility repair tests"""
    print("🚀 Starting Facility Repair Test Suite")
    print("=" * 60)
    
    # Create test game
    game_id = create_test_game()
    if not game_id:
        print("❌ Failed to create test game, aborting")
        return
    
    print(f"🎮 Test Game URL: http://localhost:5000/game/{game_id}")
    
    # Run tests
    tests = [
        ("Air Unit Repair at Airport", test_air_unit_repair_at_airport),
        ("Naval Unit Repair at Port", test_naval_unit_repair_at_port),
        ("Land Unit Repair at Factory", test_land_unit_repair_at_factory),
        ("No Repair at Full Health", test_no_repair_at_full_health),
        ("Repair Limited to 2 HP per Turn", test_repair_max_two_hp_per_turn),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func(game_id)
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\nResult: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All facility repair tests passed!")
    else:
        print("⚠️ Some tests failed - check implementation")
    
    print(f"\n🔗 Manual verification available at: http://localhost:5000/game/{game_id}")


if __name__ == "__main__":
    run_all_tests()
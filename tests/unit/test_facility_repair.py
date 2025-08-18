#!/usr/bin/env python3
"""Test facility repair mechanics - airports, factories, and ports repair units at turn start."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.game_factory import GameFactory
from core.unit import UnitType
from core.map_system import MapType

def test_factory_repairs_land_units():
    """Test that factories repair land units (2 HP max, 10% cost per HP)."""
    print("\n1. Testing factory repair for land units...")
    
    # Create test game
    manager, token = GameFactory.create_standard_game('test_factory_repair')
    
    # Give player 0 enough funds for testing
    manager.board_v2.player_funds[0] = 50000
    
    # Find a factory
    factory_pos = None
    for y in range(manager.board.height):
        for x in range(manager.board.width):
            tile = manager.tile_at(x, y)
            if tile.mapTile.type == MapType.FACTORY:
                factory_pos = (x, y)
                break
        if factory_pos:
            break
    
    assert factory_pos, "No factory found on map"
    fx, fy = factory_pos
    
    # Capture factory for player 0
    tile = manager.tile_at(fx, fy)
    manager.board_v2.set_tile_owner(tile, 0)
    
    # Create damaged tank on factory (HP 30 = 3/10)
    tank = manager.unit_create_v2(0, UnitType.TANK, fx, fy)
    tank.status.hp = 30  # 3 HP
    
    # Get initial funds and property count
    initial_funds = manager.board_v2.player_funds[0]
    print(f"Initial funds for player 0: {initial_funds}")
    print(f"Properties owned by player 0: {manager.board_v2.player_properties.get(0, 0)}")
    
    # Debug: Check current player before ending turn
    print(f"Current player before end turn: {manager.board_v2.current_player}")
    
    # End turn to trigger repair
    manager.army_end_turn()
    
    # Debug: Check current player after ending turn
    print(f"Current player after end turn: {manager.board_v2.current_player}")
    
    # If we're not back to player 0, end turn again
    if manager.board_v2.current_player != 0:
        manager.army_end_turn()
        print(f"Current player after second end turn: {manager.board_v2.current_player}")
    
    # Check repair happened
    assert tank.status.hp == 50, f"Tank HP should be 50 (repaired 2 HP), but is {tank.status.hp}"
    
    # Check cost: Tank costs 7000, repair 2 HP = 7000 * 0.1 * 2 = 1400
    # But we also get income from owned properties when turn starts
    income = manager.board_v2.player_properties.get(0, 0) * 1000
    expected_funds = initial_funds + income - 1400
    actual_funds = manager.board_v2.player_funds[0]
    print(f"Income earned: {income}, Expected funds: {expected_funds}, Actual funds: {actual_funds}")
    assert actual_funds == expected_funds, f"Funds should be {expected_funds} after repair, but are {actual_funds}"
    
    print("✅ Factory repair test PASSED")

def test_airport_repairs_air_units():
    """Test that airports repair air units (2 HP max, 10% cost per HP)."""
    print("\n2. Testing airport repair for air units...")
    
    # Create test game
    manager, token = GameFactory.create_standard_game('test_airport_repair')
    
    # Give player 0 enough funds for testing
    manager.board_v2.player_funds[0] = 50000
    
    # Find an airport
    airport_pos = None
    for y in range(manager.board.height):
        for x in range(manager.board.width):
            tile = manager.tile_at(x, y)
            if tile.mapTile.type == MapType.AIRPORT:
                airport_pos = (x, y)
                break
        if airport_pos:
            break
    
    assert airport_pos, "No airport found on map"
    ax, ay = airport_pos
    
    # Capture airport for player 0
    tile = manager.tile_at(ax, ay)
    manager.board_v2.set_tile_owner(tile, 0)
    
    # Create damaged fighter on airport (HP 10 = 1/10)
    fighter = manager.unit_create_v2(0, UnitType.FIGHTER, ax, ay)
    fighter.status.hp = 10  # 1 HP
    
    # Get initial funds
    initial_funds = manager.board_v2.player_funds[0]
    
    # End turn to trigger repair
    manager.army_end_turn()
    
    # If we're not back to player 0, end turn again
    if manager.board_v2.current_player != 0:
        manager.army_end_turn()
    
    # Check repair happened (should repair to 3 HP)
    assert fighter.status.hp == 30, f"Fighter HP should be 30 (repaired 2 HP), but is {fighter.status.hp}"
    
    # Check cost: Fighter costs 20000, repair 2 HP = 20000 * 0.1 * 2 = 4000
    # But we also get income from owned properties when turn starts
    income = manager.board_v2.player_properties.get(0, 0) * 1000
    expected_funds = initial_funds + income - 4000
    actual_funds = manager.board_v2.player_funds[0]
    assert actual_funds == expected_funds, f"Funds should be {expected_funds} after repair, but are {actual_funds}"
    
    print("✅ Airport repair test PASSED")

def test_port_repairs_naval_units():
    """Test that ports repair naval units (2 HP max, 10% cost per HP)."""
    print("\n3. Testing port repair for naval units...")
    
    # Create test game
    manager, token = GameFactory.create_standard_game('test_port_repair')
    
    # Give player 0 enough funds for testing
    manager.board_v2.player_funds[0] = 50000
    
    # Find a port
    port_pos = None
    for y in range(manager.board.height):
        for x in range(manager.board.width):
            tile = manager.tile_at(x, y)
            if tile.mapTile.type == MapType.PORT:
                port_pos = (x, y)
                break
        if port_pos:
            break
    
    if not port_pos:
        print("⚠️  No port found on map, skipping naval repair test")
        return
    
    px, py = port_pos
    
    # Capture port for player 0
    tile = manager.tile_at(px, py)
    manager.board_v2.set_tile_owner(tile, 0)
    
    # Create damaged battleship on port (HP 50 = 5/10)
    battleship = manager.unit_create_v2(0, UnitType.BATTLESHIP, px, py)
    battleship.status.hp = 50  # 5 HP
    
    # Get initial funds
    initial_funds = manager.board_v2.player_funds[0]
    
    # End turn to trigger repair
    manager.army_end_turn()
    
    # If we're not back to player 0, end turn again
    if manager.board_v2.current_player != 0:
        manager.army_end_turn()
    
    # Check repair happened
    assert battleship.status.hp == 70, f"Battleship HP should be 70 (repaired 2 HP), but is {battleship.status.hp}"
    
    # Check cost: Battleship costs 28000, repair 2 HP = 28000 * 0.1 * 2 = 5600
    # But we also get income from owned properties when turn starts
    income = manager.board_v2.player_properties.get(0, 0) * 1000
    expected_funds = initial_funds + income - 5600
    actual_funds = manager.board_v2.player_funds[0]
    assert actual_funds == expected_funds, f"Funds should be {expected_funds} after repair, but are {actual_funds}"
    
    print("✅ Port repair test PASSED")

def test_repair_limited_by_funds():
    """Test that repair is limited by available funds."""
    print("\n4. Testing repair limited by funds...")
    
    # Create test game
    manager, token = GameFactory.create_standard_game('test_repair_funds')
    
    # Find a factory
    factory_pos = None
    for y in range(manager.board.height):
        for x in range(manager.board.width):
            tile = manager.tile_at(x, y)
            if tile.mapTile.type == MapType.FACTORY:
                factory_pos = (x, y)
                break
        if factory_pos:
            break
    
    fx, fy = factory_pos
    
    # Capture factory for player 0
    tile = manager.tile_at(fx, fy)
    manager.board_v2.set_tile_owner(tile, 0)
    
    # First set enough funds to create tank
    manager.board_v2.player_funds[0] = 7700  # 7000 for tank + 700 for 1 HP repair
    
    # Create damaged tank
    tank = manager.unit_create_v2(0, UnitType.TANK, fx, fy)
    tank.status.hp = 30  # 3 HP
    
    # Now we should have exactly 700 left for repair
    
    # End turn to trigger repair
    manager.army_end_turn()
    
    # If we're not back to player 0, end turn again
    if manager.board_v2.current_player != 0:
        manager.army_end_turn()
    
    # Check only 1 HP was repaired
    assert tank.status.hp == 40, f"Tank HP should be 40 (repaired 1 HP due to funds), but is {tank.status.hp}"
    # Account for income
    income = manager.board_v2.player_properties.get(0, 0) * 1000
    expected_remaining = 700 + income - 700  # Initial + income - repair cost
    assert manager.board_v2.player_funds[0] == expected_remaining, f"Funds should be {expected_remaining} after repair"
    
    print("✅ Fund-limited repair test PASSED")

def test_no_repair_on_enemy_facility():
    """Test that units don't repair on enemy facilities."""
    print("\n5. Testing no repair on enemy facilities...")
    
    # Create test game with 2 players
    manager, token = GameFactory.create_standard_game('test_enemy_repair')
    
    # Give player 0 funds to create units
    manager.board_v2.player_funds[0] = 10000
    
    # Find a factory
    factory_pos = None
    for y in range(manager.board.height):
        for x in range(manager.board.width):
            tile = manager.tile_at(x, y)
            if tile.mapTile.type == MapType.FACTORY:
                factory_pos = (x, y)
                break
        if factory_pos:
            break
    
    fx, fy = factory_pos
    
    # Capture factory for player 1 (enemy)
    tile = manager.tile_at(fx, fy)
    manager.board_v2.set_tile_owner(tile, 1)
    
    # Create damaged tank for player 0 on enemy factory
    tank = manager.unit_create_v2(0, UnitType.TANK, fx, fy)
    tank.status.hp = 30  # 3 HP
    
    initial_hp = tank.status.hp
    
    # End turn - no repair should happen
    manager.army_end_turn()
    
    # If we're not back to player 0, end turn again
    if manager.board_v2.current_player != 0:
        manager.army_end_turn()
    
    assert tank.status.hp == initial_hp, f"Tank should not repair on enemy factory"
    
    print("✅ Enemy facility test PASSED")

def test_no_repair_at_full_health():
    """Test that units at full health don't waste funds on repair."""
    print("\n6. Testing no repair at full health...")
    
    # Create test game
    manager, token = GameFactory.create_standard_game('test_full_health')
    
    # Give player 0 funds to create units
    manager.board_v2.player_funds[0] = 10000
    
    # Find a factory
    factory_pos = None
    for y in range(manager.board.height):
        for x in range(manager.board.width):
            tile = manager.tile_at(x, y)
            if tile.mapTile.type == MapType.FACTORY:
                factory_pos = (x, y)
                break
        if factory_pos:
            break
    
    fx, fy = factory_pos
    
    # Capture factory for player 0
    tile = manager.tile_at(fx, fy)
    manager.board_v2.set_tile_owner(tile, 0)
    
    # Create full health tank
    tank = manager.unit_create_v2(0, UnitType.TANK, fx, fy)
    assert tank.status.hp == 100, "Tank should start at full health"
    
    initial_funds = manager.board_v2.player_funds[0]
    
    # End turn
    manager.army_end_turn()
    
    # If we're not back to player 0, end turn again
    if manager.board_v2.current_player != 0:
        manager.army_end_turn()
    
    # Check no funds were spent (but account for income)
    income = manager.board_v2.player_properties.get(0, 0) * 1000
    expected_funds = initial_funds + income
    assert manager.board_v2.player_funds[0] == expected_funds, "No repair costs should be deducted for full health unit"
    
    print("✅ Full health test PASSED")

def test_repair_order_after_resupply():
    """Test that repair happens after resupply in turn order."""
    print("\n7. Testing repair order (after resupply)...")
    
    # Create test game
    manager, token = GameFactory.create_standard_game('test_repair_order')
    
    # Give player 0 funds to create units
    manager.board_v2.player_funds[0] = 10000
    
    # Find a factory
    factory_pos = None
    for y in range(manager.board.height):
        for x in range(manager.board.width):
            tile = manager.tile_at(x, y)
            if tile.mapTile.type == MapType.FACTORY:
                factory_pos = (x, y)
                break
        if factory_pos:
            break
    
    fx, fy = factory_pos
    
    # Capture factory for player 0
    tile = manager.tile_at(fx, fy)
    manager.board_v2.set_tile_owner(tile, 0)
    
    # Create damaged tank with low ammo
    tank = manager.unit_create_v2(0, UnitType.TANK, fx, fy)
    tank.status.hp = 30  # 3 HP
    tank.status.ammo = 1  # Low ammo
    
    initial_funds = manager.board_v2.player_funds[0]
    
    # End turn - should resupply (free) then repair (costs funds)
    manager.army_end_turn()
    
    # If we're not back to player 0, end turn again
    if manager.board_v2.current_player != 0:
        manager.army_end_turn()
    
    # Check both happened
    assert tank.status.ammo == 9, "Tank should be resupplied to full ammo"
    assert tank.status.hp == 50, "Tank should be repaired 2 HP"
    
    # Check only repair cost was deducted (plus income)
    income = manager.board_v2.player_properties.get(0, 0) * 1000
    expected_funds = initial_funds + income - 1400  # Initial + income - repair cost
    assert manager.board_v2.player_funds[0] == expected_funds, "Only repair cost should be deducted"
    
    print("✅ Repair order test PASSED")

def run_all_tests():
    """Run all facility repair tests."""
    print("=" * 50)
    print("FACILITY REPAIR TEST SUITE")
    print("=" * 50)
    
    try:
        test_factory_repairs_land_units()
        test_airport_repairs_air_units()
        test_port_repairs_naval_units()
        test_repair_limited_by_funds()
        test_no_repair_on_enemy_facility()
        test_no_repair_at_full_health()
        test_repair_order_after_resupply()
        
        print("\n" + "=" * 50)
        print("✅ ALL FACILITY REPAIR TESTS PASSED!")
        print("=" * 50)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
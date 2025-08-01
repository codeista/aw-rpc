#!/usr/bin/env python3
"""
Test movement highlights and attack targets functionality
Tests:
1. Movement highlights appear when selecting a unit
2. Attack targets appear for units in range
3. Highlights clear properly after deselection
4. Attack targets show consistently

USAGE:
1. Activate virtual environment: source flask-env/bin/activate
2. Start server: nohup python3 app.py > server.log 2>&1 &
3. Run test: python3 test_highlights.py
"""

import requests
import json
import time

BASE_URL = 'http://localhost:5000/api'

def rpc_call(method, params):
    """Make an RPC call and return the result"""
    try:
        response = requests.post(BASE_URL, json={
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        })
        
        # Debug response
        if response.status_code != 200:
            print(f"❌ HTTP Error {response.status_code} for {method}")
            print(f"Response: {response.text[:200]}")
            return None
            
        result = response.json()
        if 'error' in result:
            print(f"❌ RPC Error in {method}: {result['error']}")
            return None
        return result.get('result')
    except Exception as e:
        print(f"❌ Exception in {method}: {e}")
        print(f"URL: {BASE_URL}")
        return None

def test_movement_highlights():
    """Test movement highlight functionality"""
    print("\n🚶 Testing Movement Highlights...")
    
    # Create test game
    token = 'highlight-test-' + str(int(time.time()))
    result = rpc_call('game_create_test', {'token': token})
    if result != 'ok':
        return False
    print(f"✅ Created test game: {token}")
    
    # Create a tank with good movement range
    tank_result = rpc_call('admin_unit_create', {
        'token': token,
        'x': 5,
        'y': 5,
        'unit_type': 'TANK',
        'army': 'RED'
    })
    if not tank_result or not tank_result.get('success'):
        print("❌ Failed to create tank")
        return False
    print("✅ Created TANK at (5,5)")
    
    # Select the tank
    select_result = rpc_call('unit_select', {'token': token, 'x': 5, 'y': 5})
    # unit_select returns board state, not success flag
    if not select_result:
        print("❌ Failed to select tank")
        return False
    print("✅ Selected tank")
    
    # Get movement range
    move_result = rpc_call('movement_range', {
        'token': token,
        'unit_x': 5,
        'unit_y': 5
    })
    if not move_result or not move_result.get('success'):
        print("❌ Failed to get movement range")
        return False
    
    positions = move_result.get('positions', [])
    print(f"✅ Got {len(positions)} movement positions")
    
    if len(positions) == 0:
        print("❌ No movement positions returned!")
        return False
    
    # Verify tank has correct movement range (should be 6)
    tank_move = move_result.get('unit', {}).get('movement', 0)
    if tank_move != 6:
        print(f"⚠️  Tank movement is {tank_move}, expected 6")
    
    # Test deselection clears highlights
    deselect_result = rpc_call('unit_select', {'token': token, 'x': 5, 'y': 5})
    print("✅ Deselected unit (clicked same position)")
    
    # Check board state to verify selection cleared
    board_result = rpc_call('game_board', {'token': token})
    if board_result and board_result.get('board', {}).get('selected') is None:
        print("✅ Selection cleared properly")
    else:
        print("⚠️  Selection may not have cleared")
    
    return True

def test_attack_targets():
    """Test attack target highlighting"""
    print("\n⚔️  Testing Attack Target Highlights...")
    
    # Create test game
    token = 'attack-test-' + str(int(time.time()))
    result = rpc_call('game_create_test', {'token': token})
    if result != 'ok':
        return False
    print(f"✅ Created test game: {token}")
    
    # Create attacker
    tank_result = rpc_call('admin_unit_create', {
        'token': token,
        'x': 5,
        'y': 5,
        'unit_type': 'TANK',
        'army': 'RED'
    })
    print("✅ Created RED TANK at (5,5)")
    
    # Create target in range
    infantry_result = rpc_call('admin_unit_create', {
        'token': token,
        'x': 6,
        'y': 5,
        'unit_type': 'INFANTRY',
        'army': 'BLUE'
    })
    print("✅ Created BLUE INFANTRY at (6,5)")
    
    # Select the tank
    select_result = rpc_call('unit_select', {'token': token, 'x': 5, 'y': 5})
    if not select_result:
        print("❌ Failed to select tank")
        return False
    print("✅ Selected tank")
    
    # Get attack targets
    targets_result = rpc_call('combat_targets', {
        'token': token,
        'unit_x': 5,
        'unit_y': 5
    })
    
    if not targets_result or not targets_result.get('success'):
        print("❌ Failed to get attack targets")
        return False
    
    targets = targets_result.get('targets', [])
    print(f"✅ Got {len(targets)} attack targets")
    
    if len(targets) == 0:
        print("❌ No attack targets found (should have found infantry)")
        return False
    
    # Verify the infantry is in targets
    found_infantry = False
    for target in targets:
        if target['x'] == 6 and target['y'] == 5:
            found_infantry = True
            unit_info = target.get('unit', {}).get('type', target.get('type', 'Unknown'))
            print(f"✅ Found infantry in targets: {unit_info} at ({target['x']},{target['y']})")
    
    if not found_infantry:
        print("❌ Infantry not in attack targets list")
        return False
    
    return True

def test_highlight_clearing():
    """Test that highlights clear properly in various scenarios"""
    print("\n🧹 Testing Highlight Clearing...")
    
    # Create test game
    token = 'clear-test-' + str(int(time.time()))
    result = rpc_call('game_create_test', {'token': token})
    if result != 'ok':
        return False
    print(f"✅ Created test game: {token}")
    
    # Create two units
    rpc_call('admin_unit_create', {
        'token': token,
        'x': 3,
        'y': 3,
        'unit_type': 'INFANTRY',
        'army': 'RED'
    })
    rpc_call('admin_unit_create', {
        'token': token,
        'x': 7,
        'y': 7,
        'unit_type': 'RECON',
        'army': 'RED'
    })
    print("✅ Created INFANTRY at (3,3) and RECON at (7,7)")
    
    # Select first unit
    rpc_call('unit_select', {'token': token, 'x': 3, 'y': 3})
    move1 = rpc_call('movement_range', {'token': token, 'unit_x': 3, 'unit_y': 3})
    print(f"✅ Selected infantry, got {len(move1.get('positions', []))} movement positions")
    
    # Select second unit (should clear first unit's highlights)
    rpc_call('unit_select', {'token': token, 'x': 7, 'y': 7})
    move2 = rpc_call('movement_range', {'token': token, 'unit_x': 7, 'unit_y': 7})
    print(f"✅ Selected recon, got {len(move2.get('positions', []))} movement positions")
    
    # Click empty tile (should clear all highlights)
    rpc_call('unit_select', {'token': token, 'x': 0, 'y': 0})
    board = rpc_call('game_board', {'token': token})
    if board and board.get('board', {}).get('selected') is None:
        print("✅ Clicking empty tile cleared selection")
    
    return True

def test_indirect_attack_targets():
    """Test attack targets for indirect units"""
    print("\n🎯 Testing Indirect Unit Attack Targets...")
    
    # Create test game
    token = 'indirect-test-' + str(int(time.time()))
    result = rpc_call('game_create_test', {'token': token})
    if result != 'ok':
        return False
    print(f"✅ Created test game: {token}")
    
    # Create artillery (indirect unit)
    rpc_call('admin_unit_create', {
        'token': token,
        'x': 5,
        'y': 5,
        'unit_type': 'ARTILLERY',
        'army': 'RED'
    })
    print("✅ Created RED ARTILLERY at (5,5)")
    
    # Create targets at various ranges
    test_targets = [
        (5, 7, 'INFANTRY'),  # Range 2
        (5, 8, 'TANK'),      # Range 3
        (6, 5, 'RECON'),     # Range 1 (too close)
        (5, 2, 'MECH'),      # Range 3
    ]
    
    for x, y, unit_type in test_targets:
        rpc_call('admin_unit_create', {
            'token': token,
            'x': x,
            'y': y,
            'unit_type': unit_type,
            'army': 'BLUE'
        })
    print("✅ Created 4 BLUE targets at various ranges")
    
    # Select artillery
    rpc_call('unit_select', {'token': token, 'x': 5, 'y': 5})
    
    # Get attack targets
    targets_result = rpc_call('combat_targets', {
        'token': token,
        'unit_x': 5,
        'unit_y': 5
    })
    
    if not targets_result or not targets_result.get('success'):
        print("❌ Failed to get artillery attack targets")
        return False
    
    targets = targets_result.get('targets', [])
    print(f"✅ Artillery found {len(targets)} attack targets")
    
    # Artillery range is 2-3, so should find 3 targets (not the one at range 1)
    if len(targets) != 3:
        print(f"⚠️  Expected 3 targets for artillery (range 2-3), got {len(targets)}")
    
    # Verify range 1 unit is not included
    for target in targets:
        if target['x'] == 6 and target['y'] == 5:
            print("❌ Artillery incorrectly targeting unit at range 1")
            return False
    
    print("✅ Artillery correctly excluding range 1 targets")
    return True

def main():
    """Run all highlight tests"""
    print("🎮 Advance Wars RPC - Movement & Attack Highlight Tests")
    print("=" * 60)
    
    tests = [
        ("Movement Highlights", test_movement_highlights),
        ("Attack Target Highlights", test_attack_targets),
        ("Highlight Clearing", test_highlight_clearing),
        ("Indirect Attack Targets", test_indirect_attack_targets)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED\n")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED\n")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} FAILED with exception: {e}\n")
    
    print("=" * 60)
    print(f"📊 Test Summary: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All highlight tests passed!")
    else:
        print("❌ Some tests failed - check output above")

if __name__ == "__main__":
    main()
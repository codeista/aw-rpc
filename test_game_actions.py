#!/usr/bin/env python3
"""Test actual game actions and verify state changes"""

import requests
import json
import time
import random
import string

base_url = 'http://localhost:5000'

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def rpc_call(method, params):
    """Make an RPC call and return the result"""
    response = requests.post(f'{base_url}/api', json={
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'id': random.randint(1, 1000)
    })
    
    if response.status_code != 200:
        return None, f"HTTP {response.status_code}"
    
    result = response.json()
    if 'error' in result:
        return None, result['error'].get('message', 'Unknown error')
    
    return result.get('result'), None

def test_unit_movement(token):
    """Test unit movement and verify position change"""
    print("\n🚶 Testing Unit Movement...")
    
    # Create an infantry unit at (1, 1)
    result, error = rpc_call('unit_create', {
        'token': token,
        'army': 0,  # RED
        'unit_type': 0,  # INFANTRY
        'x': 1,
        'y': 1
    })
    
    if error:
        return f"❌ Failed to create unit: {error}"
    
    # Get initial board state
    board, error = rpc_call('game_board', {'token': token})
    if error:
        return f"❌ Failed to get board: {error}"
    
    # Verify unit at (1,1)
    tiles = board.get('tiles', board.get('board', []))
    tile_1_1 = next((t for row in tiles for t in row if t['x'] == 1 and t['y'] == 1), None)
    if not tile_1_1 or not tile_1_1.get('unit'):
        return "❌ Unit not found at (1,1) after creation"
    
    # Move unit to (2, 2)
    result, error = rpc_call('unit_move', {
        'token': token,
        'x': 1,
        'y': 1,
        'x2': 2,
        'y2': 2
    })
    
    if error:
        return f"❌ Move failed: {error}"
    
    # Get board after move
    board_after, error = rpc_call('game_board', {'token': token})
    if error:
        return f"❌ Failed to get board after move: {error}"
    
    # Verify unit moved
    tiles_after = board_after.get('tiles', board_after.get('board', []))
    tile_1_1_after = next((t for row in tiles_after for t in row if t['x'] == 1 and t['y'] == 1), None)
    tile_2_2_after = next((t for row in tiles_after for t in row if t['x'] == 2 and t['y'] == 2), None)
    
    if tile_1_1_after and tile_1_1_after.get('unit'):
        return "❌ Unit still at (1,1) after move"
    
    if not tile_2_2_after or not tile_2_2_after.get('unit'):
        return "❌ Unit not found at (2,2) after move"
    
    return "✅ Unit movement works correctly"

def test_wait_action(token):
    """Test wait action and verify unit state and sprite changes"""
    print("\n⏸️  Testing Wait Action & Sprite Status...")
    
    # Create a tank at (3, 3)
    result, error = rpc_call('unit_create', {
        'token': token,
        'army': 0,  # RED
        'unit_type': 10,  # TANK
        'x': 3,
        'y': 3
    })
    
    if error:
        return f"❌ Failed to create tank: {error}"
    
    # Get initial state
    board_initial, error = rpc_call('game_board', {'token': token})
    if error:
        return f"❌ Failed to get initial board: {error}"
    
    tile_initial = next((t for row in board_initial['tiles'] for t in row if t['x'] == 3 and t['y'] == 3), None)
    if tile_initial and tile_initial.get('unit'):
        initial_state = tile_initial['unit'].get('has_moved', False)
        print(f"  Initial unit state - has_moved: {initial_state}")
    
    # Move tank to (4, 3)
    result, error = rpc_call('unit_move', {
        'token': token,
        'x': 3,
        'y': 3,
        'x2': 4,
        'y2': 3
    })
    
    if error:
        return f"❌ Failed to move tank: {error}"
    
    # Wait the unit
    result, error = rpc_call('unit_wait', {
        'token': token,
        'x': 4,
        'y': 3
    })
    
    if error:
        return f"❌ Wait action failed: {error}"
    
    # Get board and check unit state
    board, error = rpc_call('game_board', {'token': token})
    if error:
        return f"❌ Failed to get board after wait: {error}"
    
    tile = next((t for row in board['tiles'] for t in row if t['x'] == 4 and t['y'] == 3), None)
    if tile and tile.get('unit'):
        unit = tile['unit']
        has_moved = unit.get('has_moved', False)
        can_act = unit.get('can_act', True)
        
        results = []
        if has_moved:
            results.append("✅ Unit marked as moved")
        else:
            results.append("❌ Unit not marked as moved")
            
        if not can_act:
            results.append("✅ Unit cannot act (greyed out)")
        else:
            results.append("❌ Unit can still act (should be greyed)")
            
        # Check sprite info
        sprite_state = "done" if has_moved and not can_act else "available"
        results.append(f"📍 Sprite should show: {sprite_state} state")
        
        return " | ".join(results)
    
    return "❌ Unit not found after wait"

def test_attack_action(token):
    """Test attack action and verify damage"""
    print("\n⚔️  Testing Attack Action...")
    
    # Create attacker tank at (5, 5)
    result, error = rpc_call('unit_create', {
        'token': token,
        'army': 0,  # RED
        'unit_type': 10,  # TANK
        'x': 5,
        'y': 5
    })
    
    if error:
        return f"❌ Failed to create attacker: {error}"
    
    # End turn to switch to BLUE
    rpc_call('army_end_turn', {'token': token})
    
    # Create defender infantry at (6, 5)
    result, error = rpc_call('unit_create', {
        'token': token,
        'army': 1,  # BLUE
        'unit_type': 0,  # INFANTRY
        'x': 6,
        'y': 5
    })
    
    if error:
        return f"❌ Failed to create defender: {error}"
    
    # End turn back to RED
    rpc_call('army_end_turn', {'token': token})
    
    # Get combat preview first
    preview, error = rpc_call('combat_preview', {
        'token': token,
        'attacker_x': 5,
        'attacker_y': 5,
        'defender_x': 6,
        'defender_y': 5
    })
    
    if error:
        print(f"  ⚠️  Combat preview failed: {error}")
    else:
        print(f"  📊 Preview - Damage: {preview.get('damage', '?')}%, Counter: {preview.get('counter_damage', '?')}%")
    
    # Attack
    result, error = rpc_call('unit_attack', {
        'token': token,
        'x': 5,
        'y': 5,
        'x2': 6,
        'y2': 5
    })
    
    if error:
        return f"❌ Attack failed: {error}"
    
    # Check results
    board, error = rpc_call('game_board', {'token': token})
    if error:
        return f"❌ Failed to get board after attack: {error}"
    
    defender_tile = next((t for row in board['tiles'] for t in row if t['x'] == 6 and t['y'] == 5), None)
    if defender_tile and defender_tile.get('unit'):
        defender_hp = defender_tile['unit'].get('hp', 100)
        if defender_hp < 100:
            return f"✅ Attack works - defender HP reduced to {defender_hp}"
        else:
            return "❌ Attack executed but no damage dealt"
    else:
        return "✅ Attack works - defender destroyed"

def test_unit_delete(token):
    """Test unit delete functionality"""
    print("\n🗑️  Testing Unit Delete...")
    
    # Create a unit to delete at (7, 7)
    result, error = rpc_call('unit_create', {
        'token': token,
        'army': 0,  # RED (assuming we're on RED's turn)
        'unit_type': 5,  # RECON
        'x': 7,
        'y': 7
    })
    
    if error:
        return f"❌ Failed to create unit for deletion: {error}"
    
    # Delete the unit
    result, error = rpc_call('unit_delete', {
        'token': token,
        'x': 7,
        'y': 7
    })
    
    if error:
        return f"❌ Delete failed: {error}"
    
    # Verify unit is gone
    board, error = rpc_call('game_board', {'token': token})
    if error:
        return f"❌ Failed to get board after delete: {error}"
    
    tile = next((t for row in board['tiles'] for t in row if t['x'] == 7 and t['y'] == 7), None)
    if tile and not tile.get('unit'):
        return "✅ Unit delete works correctly"
    else:
        return "❌ Unit still present after delete"

def test_sprite_status_changes(token):
    """Test that unit sprites change status correctly"""
    print("\n🎨 Testing Sprite Status Changes...")
    
    results = []
    
    # Test 1: Fresh unit (should be available/bright)
    result, error = rpc_call('unit_create', {
        'token': token,
        'army': 0,  # RED
        'unit_type': 0,  # INFANTRY
        'x': 8,
        'y': 8
    })
    
    if error:
        return f"❌ Failed to create unit: {error}"
    
    board, error = rpc_call('game_board', {'token': token})
    if not error:
        unit = next((t['unit'] for row in board['tiles'] for t in row if t['x'] == 8 and t['y'] == 8 and t.get('unit')), None)
        if unit:
            state = "available" if not unit.get('has_moved', False) and unit.get('can_act', True) else "done"
            results.append(f"Fresh unit: {state} ✅" if state == "available" else f"Fresh unit: {state} ❌")
    
    # Test 2: Unit after moving (should still be available if direct unit)
    rpc_call('unit_move', {'token': token, 'x': 8, 'y': 8, 'x2': 8, 'y2': 7})
    board, error = rpc_call('game_board', {'token': token})
    if not error:
        unit = next((t['unit'] for row in board['tiles'] for t in row if t['x'] == 8 and t['y'] == 7 and t.get('unit')), None)
        if unit:
            # Infantry is direct, so should still be able to act after move
            can_act = unit.get('can_act', True)
            state = "available" if can_act else "done"
            results.append(f"After move: {state} ✅" if state == "available" else f"After move: {state} ❌")
    
    # Test 3: Unit after wait (should be done/greyed)
    rpc_call('unit_wait', {'token': token, 'x': 8, 'y': 7})
    board, error = rpc_call('game_board', {'token': token})
    if not error:
        unit = next((t['unit'] for row in board['tiles'] for t in row if t['x'] == 8 and t['y'] == 7 and t.get('unit')), None)
        if unit:
            has_moved = unit.get('has_moved', False)
            can_act = unit.get('can_act', True)
            state = "done" if has_moved and not can_act else "available"
            results.append(f"After wait: {state} ✅" if state == "done" else f"After wait: {state} ❌")
    
    # Test 4: Check indirect unit behavior (create artillery)
    result, error = rpc_call('unit_create', {
        'token': token,
        'army': 0,  # RED  
        'unit_type': 15,  # ARTILLERY
        'x': 9,
        'y': 9
    })
    
    if not error:
        # Move artillery
        rpc_call('unit_move', {'token': token, 'x': 9, 'y': 9, 'x2': 9, 'y2': 8})
        board, error = rpc_call('game_board', {'token': token})
        if not error:
            unit = next((t['unit'] for row in board['tiles'] for t in row if t['x'] == 9 and t['y'] == 8 and t.get('unit')), None)
            if unit:
                # Artillery is indirect, should be done after moving
                has_moved = unit.get('has_moved', False)
                can_act = unit.get('can_act', True)
                state = "done" if has_moved or not can_act else "available"
                results.append(f"Indirect after move: {state} ✅" if state == "done" else f"Indirect after move: {state} ❌")
    
    return " | ".join(results) if results else "❌ No sprite tests completed"

def test_capture_action(token):
    """Test capture action on neutral property"""
    print("\n🏰 Testing Capture Action...")
    
    # Find a neutral city
    board, error = rpc_call('game_board', {'token': token})
    if error:
        return f"❌ Failed to get board: {error}"
    
    # Look for neutral city
    neutral_city = None
    tiles = board.get('tiles', board.get('board', []))
    for row in tiles:
        for tile in row:
            if tile.get('mapTile', {}).get('type') == 705 and tile.get('mapTile', {}).get('army') is None:  # CITY without army
                neutral_city = (tile['x'], tile['y'])
                break
        if neutral_city:
            break
    
    if not neutral_city:
        return "⚠️  No neutral cities found on map"
    
    city_x, city_y = neutral_city
    print(f"  Found neutral city at ({city_x}, {city_y})")
    
    # Create infantry next to city
    inf_x = city_x - 1 if city_x > 0 else city_x + 1
    inf_y = city_y
    
    result, error = rpc_call('unit_create', {
        'token': token,
        'army': 0,  # RED
        'unit_type': 0,  # INFANTRY
        'x': inf_x,
        'y': inf_y
    })
    
    if error:
        return f"❌ Failed to create infantry: {error}"
    
    # Move infantry onto city
    result, error = rpc_call('unit_move', {
        'token': token,
        'x': inf_x,
        'y': inf_y,
        'x2': city_x,
        'y2': city_y
    })
    
    if error:
        return f"❌ Failed to move infantry to city: {error}"
    
    # Capture
    result, error = rpc_call('unit_capture', {
        'token': token,
        'x': city_x,
        'y': city_y
    })
    
    if error:
        return f"❌ Capture failed: {error}"
    
    return "✅ Capture action executed successfully"

def check_server_logs():
    """Check server logs for errors"""
    print("\n📋 Checking Server Logs...")
    
    try:
        with open('server.log', 'r') as f:
            lines = f.readlines()
            
        # Get last 100 lines
        recent_lines = lines[-100:]
        
        errors = []
        warnings = []
        
        for line in recent_lines:
            if 'ERROR' in line:
                errors.append(line.strip())
            elif 'WARNING' in line and 'development server' not in line:
                warnings.append(line.strip())
        
        results = []
        if errors:
            results.append(f"❌ Found {len(errors)} errors in logs")
            for error in errors[-3:]:  # Show last 3 errors
                results.append(f"   - {error}")
        else:
            results.append("✅ No errors in recent logs")
        
        if warnings:
            results.append(f"⚠️  Found {len(warnings)} warnings")
        
        return results
    except Exception as e:
        return [f"❌ Could not read server logs: {str(e)}"]

def main():
    print("🎮 Testing Game Actions and State Changes")
    print("=" * 60)
    
    # Create a test game
    token = generate_token()
    result, error = rpc_call('game_create_v2', {
        'token': token,
        'map_name': 'test',
        'players': [
            {'name': 'Player 1', 'color': 'red', 'sprite_color': 'RED'},
            {'name': 'Player 2', 'color': 'blue', 'sprite_color': 'BLUE'}
        ]
    })
    
    if error:
        print(f"❌ Failed to create game: {error}")
        return
    
    print(f"✅ Created test game: {token}")
    
    # Run all tests
    results = []
    results.append(test_unit_movement(token))
    results.append(test_wait_action(token))
    results.append(test_attack_action(token))
    results.append(test_unit_delete(token))
    results.append(test_sprite_status_changes(token))
    results.append(test_capture_action(token))
    results.extend(check_server_logs())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 GAME ACTION TEST SUMMARY")
    print("=" * 60)
    
    for result in results:
        print(result)
    
    passed = sum(1 for r in results if r.startswith("✅"))
    failed = sum(1 for r in results if r.startswith("❌"))
    warnings = sum(1 for r in results if r.startswith("⚠️"))
    
    print("\n" + "=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Warnings: {warnings}")
    print(f"📊 Success Rate: {passed / (passed + failed) * 100:.1f}%" if (passed + failed) > 0 else "No tests run")

if __name__ == "__main__":
    main()
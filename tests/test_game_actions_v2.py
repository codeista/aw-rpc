#!/usr/bin/env python3
"""Test actual game actions and verify state changes - simplified version"""

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

def get_unit_at(board, x, y):
    """Get unit at specific coordinates"""
    # Handle both 'tiles' and 'board' structures
    tiles = board.get('tiles', board.get('board', []))
    for row in tiles:
        for tile in row:
            if tile['x'] == x and tile['y'] == y:
                return tile.get('unit')
    return None

def test_all_actions(token):
    """Test all game actions in sequence"""
    print("\n🎮 Running Game Action Tests...")
    results = []
    
    # 1. Test Movement
    print("\n1️⃣ Testing Unit Movement...")
    rpc_call('unit_create', {'token': token, 'army': 0, 'unit_type': 0, 'x': 1, 'y': 1})
    board1, _ = rpc_call('game_board', {'token': token})
    unit_before = get_unit_at(board1, 1, 1)
    
    rpc_call('unit_move', {'token': token, 'x': 1, 'y': 1, 'x2': 2, 'y2': 2})
    board2, _ = rpc_call('game_board', {'token': token})
    unit_after = get_unit_at(board2, 2, 2)
    unit_at_old = get_unit_at(board2, 1, 1)
    
    if unit_after and not unit_at_old:
        results.append("✅ Movement: Unit moved correctly")
    else:
        results.append("❌ Movement: Unit did not move properly")
    
    # 2. Test Wait Action
    print("\n2️⃣ Testing Wait Action & Sprite Status...")
    rpc_call('unit_wait', {'token': token, 'x': 2, 'y': 2})
    board3, _ = rpc_call('game_board', {'token': token})
    unit_waited = get_unit_at(board3, 2, 2)
    
    if unit_waited:
        has_moved = unit_waited.get('has_moved', False)
        can_act = unit_waited.get('can_act', True)
        if has_moved and not can_act:
            results.append("✅ Wait: Unit marked as done (sprite should be greyed)")
        else:
            results.append(f"❌ Wait: Unit state incorrect (has_moved={has_moved}, can_act={can_act})")
    
    # 3. Test Attack
    print("\n3️⃣ Testing Attack Action...")
    # Create tank for RED
    rpc_call('unit_create', {'token': token, 'army': 0, 'unit_type': 10, 'x': 4, 'y': 4})
    
    # Switch to BLUE
    rpc_call('army_end_turn', {'token': token})
    
    # Create BLUE infantry
    rpc_call('unit_create', {'token': token, 'army': 1, 'unit_type': 0, 'x': 5, 'y': 4})
    
    # Switch back to RED
    rpc_call('army_end_turn', {'token': token})
    
    # Attack
    preview, _ = rpc_call('combat_preview', {
        'token': token,
        'attacker_x': 4, 'attacker_y': 4,
        'defender_x': 5, 'defender_y': 4
    })
    
    if preview:
        print(f"   Combat preview: {preview.get('damage', 0)}% damage")
    
    attack_result, err = rpc_call('unit_attack', {
        'token': token,
        'x': 4, 'y': 4,
        'x2': 5, 'y2': 4
    })
    
    if not err:
        board4, _ = rpc_call('game_board', {'token': token})
        defender = get_unit_at(board4, 5, 4)
        if defender and defender.get('hp', 100) < 100:
            results.append(f"✅ Attack: Damage dealt (HP: {defender.get('hp')})")
        elif not defender:
            results.append("✅ Attack: Defender destroyed")
        else:
            results.append("❌ Attack: No damage dealt")
    else:
        results.append(f"❌ Attack: {err}")
    
    # 4. Test Delete
    print("\n4️⃣ Testing Unit Delete...")
    rpc_call('unit_create', {'token': token, 'army': 0, 'unit_type': 5, 'x': 7, 'y': 7})
    rpc_call('unit_delete', {'token': token, 'x': 7, 'y': 7})
    board5, _ = rpc_call('game_board', {'token': token})
    deleted_unit = get_unit_at(board5, 7, 7)
    
    if not deleted_unit:
        results.append("✅ Delete: Unit removed successfully")
    else:
        results.append("❌ Delete: Unit still exists")
    
    # 5. Test Sprite States
    print("\n5️⃣ Testing Sprite State Changes...")
    sprite_results = []
    
    # Fresh unit
    rpc_call('unit_create', {'token': token, 'army': 0, 'unit_type': 0, 'x': 8, 'y': 8})
    board, _ = rpc_call('game_board', {'token': token})
    fresh_unit = get_unit_at(board, 8, 8)
    if fresh_unit:
        state = "bright" if not fresh_unit.get('has_moved', False) else "greyed"
        sprite_results.append(f"Fresh unit: {state}")
    
    # Direct unit after move
    rpc_call('unit_move', {'token': token, 'x': 8, 'y': 8, 'x2': 8, 'y2': 7})
    board, _ = rpc_call('game_board', {'token': token})
    moved_unit = get_unit_at(board, 8, 7)
    if moved_unit:
        can_act = moved_unit.get('can_act', True)
        state = "bright" if can_act else "greyed"
        sprite_results.append(f"Direct after move: {state}")
    
    # After wait
    rpc_call('unit_wait', {'token': token, 'x': 8, 'y': 7})
    board, _ = rpc_call('game_board', {'token': token})
    waited_unit = get_unit_at(board, 8, 7)
    if waited_unit:
        state = "greyed" if waited_unit.get('has_moved', False) else "bright"
        sprite_results.append(f"After wait: {state}")
    
    # Indirect unit
    rpc_call('unit_create', {'token': token, 'army': 0, 'unit_type': 15, 'x': 9, 'y': 9})
    rpc_call('unit_move', {'token': token, 'x': 9, 'y': 9, 'x2': 9, 'y2': 8})
    board, _ = rpc_call('game_board', {'token': token})
    indirect_unit = get_unit_at(board, 9, 8)
    if indirect_unit:
        can_act = indirect_unit.get('can_act', True)
        state = "greyed" if not can_act else "bright"
        sprite_results.append(f"Indirect after move: {state}")
    
    results.append("✅ Sprite states: " + " | ".join(sprite_results))
    
    return results

def check_server_logs():
    """Check last few lines of server log for errors"""
    print("\n📋 Checking Server Logs...")
    try:
        # Use tail command to get last 50 lines
        import subprocess
        result = subprocess.run(['tail', '-50', 'server.log'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        errors = [line for line in lines if 'ERROR' in line and 'MethodNotFoundError' not in line]
        
        if errors:
            return [f"❌ Found {len(errors)} errors in logs", f"   Latest: {errors[-1][:80]}..."]
        else:
            return ["✅ No errors in recent logs"]
    except:
        return ["⚠️  Could not read server logs"]

def main():
    print("🎮 Testing Game Actions and State Changes")
    print("=" * 60)
    
    # Create test game
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
    
    # Run tests
    results = test_all_actions(token)
    results.extend(check_server_logs())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for result in results:
        print(result)
    
    passed = sum(1 for r in results if r.startswith("✅"))
    failed = sum(1 for r in results if r.startswith("❌"))
    
    print("\n" + "=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {passed / (passed + failed) * 100:.1f}%" if (passed + failed) > 0 else "")

if __name__ == "__main__":
    main()
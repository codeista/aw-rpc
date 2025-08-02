#!/usr/bin/env python3
"""Test key UI paths: move, wait, attack, delete"""

import requests
import json
import time

base_url = 'http://localhost:5000'

def rpc(method, params):
    """Make RPC call"""
    r = requests.post(f'{base_url}/api', json={
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'id': 1
    })
    return r.json()

def test_ui_paths():
    print("🎯 Testing Key UI Paths")
    print("=" * 50)
    
    # Create game
    token = 'uitest123'
    result = rpc('game_create_v2', {
        'token': token,
        'map_name': 'test',
        'players': [
            {'name': 'RED', 'color': 'red', 'sprite_color': 'RED'},
            {'name': 'BLUE', 'color': 'blue', 'sprite_color': 'BLUE'}
        ]
    })
    
    if 'error' in result:
        print(f"❌ Failed to create game: {result['error']['message']}")
        return
    
    print(f"✅ Game created: {token}")
    
    # Test 1: Move
    print("\n1. MOVE TEST")
    print("-" * 30)
    
    # Create infantry
    r1 = rpc('unit_create', {'token': token, 'army': 0, 'unit_type': 0, 'x': 2, 'y': 2})
    print(f"   Create infantry: {'✅' if 'result' in r1 else '❌'}")
    
    # Move it
    r2 = rpc('unit_move', {'token': token, 'x': 2, 'y': 2, 'x2': 3, 'y2': 3})
    print(f"   Move to (3,3): {'✅' if 'result' in r2 else '❌'}")
    
    # Test 2: Wait
    print("\n2. WAIT TEST")
    print("-" * 30)
    
    r3 = rpc('unit_wait', {'token': token, 'x': 3, 'y': 3})
    print(f"   Wait unit: {'✅' if 'result' in r3 else '❌'}")
    
    # Check unit state
    board = rpc('game_board', {'token': token})
    if 'result' in board:
        # Find unit at (3,3)
        found = False
        for row in board['result'].get('tiles', board['result'].get('board', [])):
            for tile in row:
                if tile['x'] == 3 and tile['y'] == 3 and tile.get('unit'):
                    unit = tile['unit']
                    print(f"   Unit state: has_moved={unit.get('has_moved')}, can_act={unit.get('can_act')}")
                    print(f"   Sprite should be: {'GREYED' if unit.get('has_moved') else 'BRIGHT'}")
                    found = True
                    break
            if found:
                break
    
    # Test 3: Attack
    print("\n3. ATTACK TEST")  
    print("-" * 30)
    
    # Create attacker
    r4 = rpc('unit_create', {'token': token, 'army': 0, 'unit_type': 10, 'x': 5, 'y': 5})
    print(f"   Create RED tank: {'✅' if 'result' in r4 else '❌'}")
    
    # End turn
    rpc('army_end_turn', {'token': token})
    
    # Create defender
    r5 = rpc('unit_create', {'token': token, 'army': 1, 'unit_type': 0, 'x': 6, 'y': 5})
    print(f"   Create BLUE infantry: {'✅' if 'result' in r5 else '❌'}")
    
    # End turn back
    rpc('army_end_turn', {'token': token})
    
    # Preview
    preview = rpc('combat_preview', {
        'token': token,
        'attacker_x': 5, 'attacker_y': 5,
        'defender_x': 6, 'defender_y': 5
    })
    
    if 'result' in preview:
        dmg = preview['result'].get('damage', 0)
        print(f"   Combat preview: {dmg}% damage")
    
    # Attack
    r6 = rpc('unit_attack', {'token': token, 'x': 5, 'y': 5, 'x2': 6, 'y2': 5})
    print(f"   Execute attack: {'✅' if 'result' in r6 else '❌'}")
    
    # Test 4: Delete
    print("\n4. DELETE TEST")
    print("-" * 30)
    
    # Create unit
    r7 = rpc('unit_create', {'token': token, 'army': 0, 'unit_type': 5, 'x': 8, 'y': 8})
    print(f"   Create recon: {'✅' if 'result' in r7 else '❌'}")
    
    # Delete it
    r8 = rpc('unit_delete', {'token': token, 'x': 8, 'y': 8})
    print(f"   Delete unit: {'✅' if 'result' in r8 else '❌'}")
    
    # Verify deleted
    board2 = rpc('game_board', {'token': token})
    if 'result' in board2:
        found = False
        for row in board2['result'].get('tiles', board2['result'].get('board', [])):
            for tile in row:
                if tile['x'] == 8 and tile['y'] == 8 and tile.get('unit'):
                    found = True
                    break
        print(f"   Unit gone: {'✅' if not found else '❌'}")
    
    print("\n" + "=" * 50)
    print("✅ All UI paths tested")

if __name__ == "__main__":
    test_ui_paths()
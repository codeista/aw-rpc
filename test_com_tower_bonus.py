#!/usr/bin/env python3
"""
Test COM_TOWER Damage Bonus

This test verifies that COM_TOWER ownership provides +10% attack bonus per tower.
"""

import requests
import json

BASE_URL = "http://localhost:5000/api"

def rpc(method, params=None):
    """Make RPC call"""
    if params is None:
        params = {}
    
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    
    response = requests.post(BASE_URL, json=payload)
    result = response.json()
    
    if 'error' in result:
        print(f"Error: {result['error']}")
        return None
    
    return result.get('result')

def main():
    print("=== COM_TOWER Damage Bonus Test ===\n")
    
    # Create test game with unique token and use multi_army_center map
    import time
    token = f"com-tower-test-{int(time.time())}"
    
    # First create the game with v2 and use the com_tower_test map
    result = rpc('game_create_v2', {
        'token': token,
        'map_name': 'com_tower_test',
        'players': [
            {"name": "Red Player", "color": "Red", "sprite_color": "RED"},
            {"name": "Blue Player", "color": "Blue", "sprite_color": "BLUE"}
        ]
    })
    if not result:
        print("Failed to create game")
        return
    
    print(f"✅ Created test game: {token}")
    
    # Get board to find COM_TOWERs
    board = rpc('game_board', {'token': token})
    if not board:
        print("Failed to get board")
        return
    
    # Find COM_TOWERs
    com_towers = []
    # Debug: print first tile structure
    if board['grid']:
        print(f"Debug - First tile structure: {list(board['grid'][0].keys())}")
        if 'mapTile' in board['grid'][0]:
            print(f"Debug - mapTile structure: {board['grid'][0]['mapTile']}")
    
    for tile in board['grid']:
        # Check tile structure - it should have a mapTile property
        if 'mapTile' in tile and tile['mapTile']['type'] == 'COM_TOWER':
            owner = tile['mapTile'].get('army', 'Neutral')
            com_towers.append((tile['x'], tile['y']))
            print(f"Debug - COM_TOWER at ({tile['x']}, {tile['y']}) owned by: {owner}")
    
    print(f"Found {len(com_towers)} COM_TOWERs on the map")
    
    # Create units for testing
    # RED TANK at (2, 2)
    result = rpc('unit_create', {
        'token': token,
        'army': 'RED',
        'unit_type': 'TANK',
        'x': 2, 'y': 2
    })
    print(f"Created RED TANK at (2, 2)")
    
    # BLUE TANK at (3, 2) for target
    result = rpc('unit_create', {
        'token': token,
        'army': 'BLUE',
        'unit_type': 'TANK',
        'x': 3, 'y': 2
    })
    
    # End turns so units can attack
    rpc('army_end_turn', {'token': token})  # RED turn ends
    rpc('army_end_turn', {'token': token})  # BLUE turn ends
    
    print("\n📊 Testing damage with different COM_TOWER counts:\n")
    
    # Test 1: No COM_TOWERs (baseline)
    preview = rpc('combat_preview', {
        'token': token,
        'attacker_x': 2, 'attacker_y': 2,
        'defender_x': 3, 'defender_y': 2
    })
    
    if preview and 'damage' in preview:
        base_damage = preview['damage']['attacker_damage']
        print(f"0 COM_TOWERs: {base_damage} damage (baseline)")
    else:
        print(f"Combat preview failed: {preview}")
        return
    
    # Capture COM_TOWERs for RED and test damage increase
    if com_towers:
        # Create infantry to capture
        result = rpc('unit_create', {
            'token': token,
            'army': 'RED',
            'unit_type': 'INFANTRY',
            'x': com_towers[0][0], 'y': com_towers[0][1]
        })
        
        # Capture first COM_TOWER
        print(f"\nCapturing COM_TOWER at {com_towers[0]}...")
        for turn in range(2):  # Takes 2 turns to capture
            capture_result = rpc('capture_tile', {
                'token': token,
                'x': com_towers[0][0], 'y': com_towers[0][1]
            })
            print(f"Turn {turn+1} capture result: {capture_result}")
            rpc('army_end_turn', {'token': token})
            rpc('army_end_turn', {'token': token})
        
        # Check COM_TOWER ownership after capture
        board = rpc('game_board', {'token': token})
        for tile in board['grid']:
            if tile['x'] == com_towers[0][0] and tile['y'] == com_towers[0][1]:
                print(f"COM_TOWER ownership after capture: {tile['mapTile'].get('army', 'None')}")
        
        # Test damage with 1 COM_TOWER
        preview = rpc('combat_preview', {
            'token': token,
            'attacker_x': 2, 'attacker_y': 2,
            'defender_x': 3, 'defender_y': 2
        })
        
        print(f"Debug - combat_preview result: {preview}")
        if 'damage' in preview:
            damage_1_tower = preview['damage']['attacker_damage']
        else:
            # Different RPC method might return different structure
            damage_1_tower = preview.get('attacker_damage', 0)
        expected_1 = int(base_damage * 1.1)
        print(f"1 COM_TOWER:  {damage_1_tower} damage (expected: ~{expected_1}, +10%)")
        
        # Capture second COM_TOWER if available
        if len(com_towers) > 1:
            result = rpc('unit_create', {
                'token': token,
                'army': 'RED',
                'unit_type': 'INFANTRY',
                'x': com_towers[1][0], 'y': com_towers[1][1]
            })
            
            for _ in range(2):
                rpc('capture_tile', {
                    'token': token,
                    'x': com_towers[1][0], 'y': com_towers[1][1]
                })
                rpc('army_end_turn', {'token': token})
                rpc('army_end_turn', {'token': token})
            
            # Test damage with 2 COM_TOWERs
            preview = rpc('combat_preview', {
                'token': token,
                'attacker_x': 2, 'attacker_y': 2,
                'defender_x': 3, 'defender_y': 2
            })
            
            damage_2_towers = preview['damage']['attacker_damage']
            expected_2 = int(base_damage * 1.2)
            print(f"2 COM_TOWERs: {damage_2_towers} damage (expected: ~{expected_2}, +20%)")
    
    print("\n✨ COM_TOWER damage bonus test complete!")
    
    # Verify modifiers are working
    if 'damage_1_tower' in locals():
        bonus_1 = ((damage_1_tower - base_damage) / base_damage) * 100
        print(f"\nActual bonus with 1 tower: {bonus_1:.1f}%")
        
        if 'damage_2_towers' in locals():
            bonus_2 = ((damage_2_towers - base_damage) / base_damage) * 100
            print(f"Actual bonus with 2 towers: {bonus_2:.1f}%")

if __name__ == "__main__":
    main()
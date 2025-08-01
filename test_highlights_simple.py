#!/usr/bin/env python3
"""
Simple test to verify highlight clearing
"""

import requests
import json
import time

def rpc(method, params):
    """Make RPC call"""
    response = requests.post('http://localhost:5000/rpc', json={
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'id': 1
    })
    return response.json()

# Create a test game
print("Creating test game...")
result = rpc('game_create_test', {'token': 'test-highlights', 'use_optimized': True})
print(f"Game created: {result}")

token = 'test-highlights'

# Create a tank
print("\nCreating RED tank at (3,3)...")
rpc('unit_create', {'token': token, 'army': 'RED', 'unit_type': 'TANK', 'x': 3, 'y': 3})

# End turn twice to enable movement
rpc('army_end_turn', {'token': token})
rpc('army_end_turn', {'token': token})

# Select the tank
print("\nSelecting tank...")
rpc('unit_select', {'token': token, 'x': 3, 'y': 3})

# Check board state
board = rpc('get_game_board', {'token': token})['result']['board']
move_highlights = sum(1 for t in board['grid'] if t.get('can_be_moved_to'))
print(f"Movement highlights after selection: {move_highlights}")

# Move the tank
print("\nMoving tank to (5,3)...")
rpc('movement_execute', {'token': token, 'from_x': 3, 'from_y': 3, 'to_x': 5, 'to_y': 3})

time.sleep(0.5)

# Check board state again
board = rpc('get_game_board', {'token': token})['result']['board']

# Check tile at (3,3) - original position
original_tile = None
for tile in board['grid']:
    if tile['x'] == 3 and tile['y'] == 3:
        original_tile = tile
        break

print(f"\nOriginal tile (3,3) state:")
print(f"  can_be_moved_to: {original_tile.get('can_be_moved_to', False)}")
print(f"  can_be_attacked: {original_tile.get('can_be_attacked', False)}")

# Count all highlights
move_highlights = sum(1 for t in board['grid'] if t.get('can_be_moved_to'))
attack_highlights = sum(1 for t in board['grid'] if t.get('can_be_attacked'))
print(f"\nTotal highlights after move:")
print(f"  Movement: {move_highlights}")
print(f"  Attack: {attack_highlights}")

# Create enemy for attack test
print("\n\nCreating BLUE infantry at (6,3)...")
rpc('unit_create', {'token': token, 'army': 'BLUE', 'unit_type': 'INFANTRY', 'x': 6, 'y': 3})

# Attack the enemy
print("Attacking enemy...")
rpc('combat_attack', {'token': token, 'attacker_x': 5, 'attacker_y': 3, 'defender_x': 6, 'defender_y': 3})

time.sleep(0.5)

# Final board check
board = rpc('get_game_board', {'token': token})['result']['board']
move_highlights = sum(1 for t in board['grid'] if t.get('can_be_moved_to'))
attack_highlights = sum(1 for t in board['grid'] if t.get('can_be_attacked'))

print(f"\nFinal highlights after attack:")
print(f"  Movement: {move_highlights}")
print(f"  Attack: {attack_highlights}")

# Check specific tiles
print("\nChecking specific tiles for artifacts:")
for pos in [(3,3), (5,3), (6,3)]:
    for tile in board['grid']:
        if tile['x'] == pos[0] and tile['y'] == pos[1]:
            if tile.get('can_be_moved_to') or tile.get('can_be_attacked'):
                print(f"  WARNING: Tile {pos} has highlights!")
                print(f"    can_be_moved_to: {tile.get('can_be_moved_to')}")
                print(f"    can_be_attacked: {tile.get('can_be_attacked')}")
            break

print("\nTest complete!")
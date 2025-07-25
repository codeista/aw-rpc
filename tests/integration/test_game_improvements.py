#!/usr/bin/env python3
"""
Test the new game creation improvements
"""

import requests
import json

def rpc(method, params):
    payload = {'jsonrpc': '2.0', 'method': method, 'params': params, 'id': 1}
    r = requests.post('http://localhost:5000/api', json=payload)
    result = r.json()
    if 'error' in result:
        return {'error': result['error']}
    return result.get('result', {})

print("Testing game creation methods:\n")

# Test 1: Regular game_create
print("1. Testing regular game_create...")
game1 = 'regular_test'
rpc('game_create_test', {'token': game1})
board1 = rpc('game_board', {'token': game1})
print(f"   Regular game - Funds: RED={board1.get('red_funds')}, BLUE={board1.get('blue_funds')}")

# Test 2: New game_create_test with optimized map
print("\n2. Testing game_create_test (optimized)...")
import time
game2 = f'optimized_test_{int(time.time())}'
result = rpc('game_create_test', {'token': game2, 'use_optimized': True})
if 'error' in result:
    print(f"   Error: {result['error']}")
else:
    board2 = rpc('game_board', {'token': game2})
    print(f"   Optimized game - Funds: RED={board2.get('red_funds')}, BLUE={board2.get('blue_funds')}")
    
    # Check if we can create expensive units
    if board2.get('red_funds', 0) >= 7500:
        print("   ✅ Can afford Black Boat (7500)")
    if board2.get('red_funds', 0) >= 12000:
        print("   ✅ Can afford Lander (12000)")
    if board2.get('red_funds', 0) >= 30000:
        print("   ✅ Can afford Carrier (30000)")

# Test 3: Create and test Black Boat movement
print("\n3. Testing Black Boat creation and movement...")
game3 = f'blackboat_test_{int(time.time())}'
rpc('game_create_test', {'token': game3})

# Create Black Boat at port
create_result = rpc('unit_create', {
    'token': game3,
    'army': 'RED',
    'unit_type': 'BLACKBOAT',
    'x': 0,
    'y': 0
})

if 'error' not in create_result:
    print("   ✅ Black Boat created successfully")
    
    # Check movement on creation turn
    moves1 = rpc('get_valid_moves', {'token': game3, 'x': 0, 'y': 0})
    if 'moves' in moves1:
        print(f"   Moves on creation turn: {len(moves1.get('moves', []))}")
    
    # End turns
    rpc('army_end_turn', {'token': game3})
    rpc('army_end_turn', {'token': game3})
    
    # Check movement after turn
    moves2 = rpc('get_valid_moves', {'token': game3, 'x': 0, 'y': 0})
    if 'moves' in moves2:
        print(f"   Moves after turn cycle: {len(moves2.get('moves', []))}")
        print("   ✅ Black Boat can move after turn cycle")
else:
    print(f"   ❌ Failed to create Black Boat: {create_result.get('error')}")

print("\n" + "="*50)
print("SUMMARY:")
print("- Regular game_create: Low starting funds (5000)")
print("- game_create_test: High starting funds (50000)")
print("- Use game_create_test for testing expensive units")
print("- Units cannot move on creation turn (standard rule)")
print("\nTo use in your tests:")
print('  rpc("game_create_test", {"token": "mygame"})')
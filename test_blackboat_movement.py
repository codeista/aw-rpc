#!/usr/bin/env python3
"""
Test Black Boat movement
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

# Create test game
game_id = 'blackboatmove'
print('Creating game...')
rpc('game_create', {'token': game_id})

# Generate funds
print('\nGenerating funds...')
for i in range(3):
    rpc('army_end_turn', {'token': game_id})
    rpc('army_end_turn', {'token': game_id})

# Get board
board = rpc('game_board', {'token': game_id})
print(f'Current funds: RED={board.get("red_funds")}, BLUE={board.get("blue_funds")}')

# Find a port - the test map has ports at specific locations
port_positions = [(0, 0), (11, 0)]  # Based on the test map
port_x, port_y = port_positions[0]  # Use RED port

print(f'\nCreating BLACKBOAT at port ({port_x},{port_y})...')
create_result = rpc('unit_create', {
    'token': game_id, 
    'army': 'RED', 
    'unit_type': 'BLACKBOAT', 
    'x': port_x, 
    'y': port_y
})

if 'error' in create_result:
    print(f'Error creating BLACKBOAT: {create_result["error"]}')
else:
    print('BLACKBOAT created successfully')
    
    # Try to get valid moves immediately
    moves_result = rpc('get_valid_moves', {'token': game_id, 'x': port_x, 'y': port_y})
    if 'error' not in moves_result:
        move_count = len(moves_result.get('moves', []))
        print(f'Valid moves immediately after creation: {move_count}')
        if move_count == 0:
            print('  → This is normal! Units cannot move on the turn they are created.')
    
    # End turns to enable movement
    print('\nEnding turn cycle to enable movement...')
    rpc('army_end_turn', {'token': game_id})  # End RED turn
    rpc('army_end_turn', {'token': game_id})  # End BLUE turn
    
    # Now check valid moves again
    moves_result = rpc('get_valid_moves', {'token': game_id, 'x': port_x, 'y': port_y})
    if 'error' not in moves_result:
        moves = moves_result.get('moves', [])
        print(f'Valid moves after turn cycle: {len(moves)}')
        if moves:
            print('Sample valid move positions:')
            for move in moves[:5]:  # Show first 5 moves
                print(f'  - ({move["x"]}, {move["y"]})')
    
            # Try to move the Black Boat
            if moves:
                target = moves[0]
                print(f'\nAttempting to move BLACKBOAT to ({target["x"]}, {target["y"]})...')
                move_result = rpc('unit_move', {
                    'token': game_id,
                    'x': port_x,
                    'y': port_y,
                    'x2': target['x'],
                    'y2': target['y']
                })
                if 'error' in move_result:
                    print(f'Move failed: {move_result["error"]}')
                else:
                    print('Move successful!')

print(f'\nTest complete. Game ID: {game_id}')
print('You can view the game at http://localhost:5000/test')
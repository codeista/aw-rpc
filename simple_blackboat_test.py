#!/usr/bin/env python3
"""Simple Black Boat test"""

import requests
import json

def rpc(method, params):
    payload = {'jsonrpc': '2.0', 'method': method, 'params': params, 'id': 1}
    r = requests.post('http://localhost:5000/api', json=payload)
    return r.json()

# Create game
game_id = 'simpletest'
print('Creating game...')
result = rpc('game_create', {'token': game_id})
print(f'Create result: {result}')

# Get initial board state
board_result = rpc('game_board', {'token': game_id})
if 'result' in board_result:
    board = board_result['result']
    print(f'\nInitial funds: RED={board.get("red_funds")}, BLUE={board.get("blue_funds")}')
    
    # The test map should have generous starting funds
    if board.get("red_funds", 0) >= 7500:
        print('\nTrying to create BLACKBOAT at port (0,0)...')
        create_result = rpc('unit_create', {
            'token': game_id,
            'army': 'RED', 
            'unit_type': 'BLACKBOAT',
            'x': 0,
            'y': 0
        })
        print(f'Create result: {create_result}')
        
        if 'error' not in create_result:
            print('\nChecking if BLACKBOAT can move on creation turn...')
            moves_result = rpc('get_valid_moves', {'token': game_id, 'x': 0, 'y': 0})
            print(f'Valid moves result: {moves_result}')
            
            if 'result' in moves_result:
                moves = moves_result['result'].get('moves', [])
                print(f'Number of valid moves: {len(moves)}')
                
                if len(moves) == 0:
                    print('\n✅ This is correct! Units cannot move on their creation turn.')
                    print('You need to end the turn before the unit can move.')
                    
                    # End turns
                    print('\nEnding turns...')
                    rpc('army_end_turn', {'token': game_id})
                    rpc('army_end_turn', {'token': game_id})
                    
                    # Check again
                    moves_result = rpc('get_valid_moves', {'token': game_id, 'x': 0, 'y': 0})
                    if 'result' in moves_result:
                        moves = moves_result['result'].get('moves', [])
                        print(f'\nAfter turn cycle, valid moves: {len(moves)}')
                        if moves:
                            print('✅ Black Boat can now move!')
    else:
        print(f'\nInsufficient funds for BLACKBOAT (need 7500, have {board.get("red_funds", 0)})')
        
print(f'\nGame ID: {game_id}')
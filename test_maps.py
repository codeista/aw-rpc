#!/usr/bin/env python3
"""Test all maps are loading correctly after security updates"""

import requests
import json
import time
import random
import string

base_url = 'http://localhost:5000'

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# List of maps from CLAUDE.md
maps = ['test', 'scorpion', 'triangle', 'cross', 'pentagon', 'green_yellow_arena', 
        'green_blue_islands', 'yellow_grey_mountains', 'green_yellow_hq_rush', 
        'multi_army_test', 'elimination_test', 'com_tower_test', 'naval_test', 
        'air_test', 'land_test', 'transport_test']

def test_single_map(map_name, token):
    """Test creating and loading a single map"""
    try:
        # Create game
        response = requests.post(f'{base_url}/api', json={
            'jsonrpc': '2.0',
            'method': 'game_create_v2',
            'params': {
                'token': token,
                'map_name': map_name,
                'players': [
                    {'name': 'Player 1', 'color': 'red', 'sprite_color': 'RED'},
                    {'name': 'Player 2', 'color': 'blue', 'sprite_color': 'BLUE'}
                ]
            },
            'id': 1
        })
        
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}"
        
        result = response.json()
        if 'error' in result:
            return False, result['error'].get('message', 'Unknown error')
        
        # Get board to verify
        board_response = requests.post(f'{base_url}/api', json={
            'jsonrpc': '2.0',
            'method': 'game_board',
            'params': {'token': token},
            'id': 2
        })
        
        if board_response.status_code == 200:
            board_result = board_response.json()
            if 'result' in board_result:
                board = board_result['result']
                dims = f"{board.get('width', '?')}x{board.get('height', '?')}"
                return True, dims
        
        return False, "Board retrieval failed"
        
    except Exception as e:
        return False, str(e)

def main():
    print('Testing all maps after security updates...')
    print('=' * 60)
    
    success_count = 0
    failed_maps = []
    
    for map_name in maps:
        token = generate_token()
        success, info = test_single_map(map_name, token)
        
        if success:
            print(f'✅ {map_name:20s} - Loaded successfully ({info})')
            success_count += 1
        else:
            print(f'❌ {map_name:20s} - Failed: {info}')
            failed_maps.append(map_name)
        
        time.sleep(0.1)
    
    print('=' * 60)
    print(f'Summary: {success_count}/{len(maps)} maps loaded successfully')
    if failed_maps:
        print(f'Failed maps: {failed_maps}')
    
    # Update todo list
    if success_count == len(maps):
        print('\n✅ All maps are loading correctly!')
    else:
        print(f'\n❌ {len(failed_maps)} maps failed to load')

if __name__ == '__main__':
    main()
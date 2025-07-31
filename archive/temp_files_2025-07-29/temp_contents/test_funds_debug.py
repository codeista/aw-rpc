#!/usr/bin/env python3
"""Debug funds issue with game_create_test"""

import requests
import json
import random
import string

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def rpc_call(method, params):
    response = requests.post("http://localhost:5000/api", json={
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    })
    return response.json()

# Test 1: Create test game
token = generate_token()
print(f"Creating test game: {token}")
result = rpc_call("game_create_test", {"token": token})
print(f"Result: {json.dumps(result, indent=2)}")

if "error" not in result:
    # Get board info
    board = rpc_call("game_board", {"token": token})
    board_data = board.get('result', {})
    
    print(f"\nBoard data keys: {list(board_data.keys())}")
    
    # Check for player_funds (V2 system)
    if 'player_funds' in board_data:
        print(f"\nPlayer funds (V2 system):")
        for i, funds in enumerate(board_data['player_funds']):
            print(f"  Player {i}: {funds}")
    
    # Check for red_funds/blue_funds (legacy)
    if 'red_funds' in board_data:
        print(f"\nLegacy funds:")
        print(f"  RED funds: {board_data['red_funds']}")
        print(f"  BLUE funds: {board_data['blue_funds']}")
    
    # Check current player
    if 'current_player' in board_data:
        print(f"\nCurrent player: {board_data['current_player']}")
    
    # Check if we can create expensive units
    print("\n\nTrying to create expensive units...")
    
    # Try BATTLESHIP (most expensive at 28000)
    battleship = rpc_call("unit_create", {
        "token": token,
        "army": "RED",
        "unit_type": "BATTLESHIP", 
        "x": 0, "y": 0  # Assuming water tile
    })
    print(f"\nBattleship creation: {json.dumps(battleship, indent=2)}")
    
    # Try BOMBER (22000)
    bomber = rpc_call("unit_create", {
        "token": token,
        "army": "RED",
        "unit_type": "BOMBER",
        "x": 5, "y": 5  # Assuming land tile
    })
    print(f"\nBomber creation: {json.dumps(bomber, indent=2)}")
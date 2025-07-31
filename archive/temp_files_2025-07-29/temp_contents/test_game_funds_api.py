#!/usr/bin/env python3
"""Test game funds via API"""

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

# Test both game_create_v2 and game_create_test
tokens = []

# Test 1: game_create_v2 with test map
token1 = generate_token()
print(f"Creating game_create_v2: {token1}")
result1 = rpc_call("game_create_v2", {
    "token": token1,
    "map_name": "test"
})
tokens.append(("v2", token1, result1))

# Test 2: game_create_test
token2 = generate_token()
print(f"Creating game_create_test: {token2}")
result2 = rpc_call("game_create_test", {"token": token2})
tokens.append(("test", token2, result2))

# Check boards for both
for game_type, token, create_result in tokens:
    print(f"\n--- {game_type} game: {token} ---")
    if "error" in create_result:
        print(f"Creation error: {create_result}")
        continue
        
    board = rpc_call("game_board", {"token": token})
    if "error" in board:
        print(f"Board error: {board}")
        continue
        
    board_data = board.get('result', {})
    
    # Check all fund-related fields
    print(f"player_funds: {board_data.get('player_funds', 'Not found')}")
    print(f"red_funds: {board_data.get('red_funds', 'Not found')}")
    print(f"blue_funds: {board_data.get('blue_funds', 'Not found')}")
    print(f"army_funds: {board_data.get('army_funds', 'Not found')}")
    
    # Try to create expensive unit
    print("\nTrying to create BATTLESHIP (28000 cost)...")
    battleship = rpc_call("unit_create", {
        "token": token,
        "army": "RED",
        "unit_type": "BATTLESHIP",
        "x": 0, "y": 0  # Hopefully a port/water
    })
    
    if "error" in battleship:
        print(f"Battleship error: {battleship.get('error')}")
    else:
        result = battleship.get('result', {})
        if 'unit' in result:
            print("✅ Battleship created successfully!")
        else:
            print(f"Result: {battleship}")
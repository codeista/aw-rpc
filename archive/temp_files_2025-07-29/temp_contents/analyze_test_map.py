#!/usr/bin/env python3
"""Analyze the test map structure"""

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

# Create test game
token = generate_token()
result = rpc_call("game_create_test", {"token": token})

# Get board
board = rpc_call("game_board", {"token": token})
board_data = board.get('result', {})

print(f"Map: {board_data.get('map_name')}")
print(f"Size: {board_data.get('width')}x{board_data.get('height')}")

# Get grid structure
grid = board_data.get('grid', [])
print(f"Grid type: {type(grid)}")
print(f"Grid length: {len(grid)}")

if grid and len(grid) > 0:
    print(f"First row type: {type(grid[0])}")
    if isinstance(grid[0], list) and len(grid[0]) > 0:
        print(f"First tile type: {type(grid[0][0])}")
        # Print sample tile
        sample = grid[0][0]
        print(f"Sample tile: {json.dumps(sample, indent=2)}")

# Look for specific map file
print("\n--- Checking map file ---")
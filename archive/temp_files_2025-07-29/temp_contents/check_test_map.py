#!/usr/bin/env python3
"""Check what map the test game uses"""

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

# Get board info
board = rpc_call("game_board", {"token": token})
board_data = board.get('result', {})

print(f"Map name: {board_data.get('map_name')}")
print(f"Map size: {board_data.get('width')}x{board_data.get('height')}")

# Check what's at key positions
positions = [
    (4, 1, "Factory for tanks"),
    (4, 2, "APC spawn"), 
    (3, 2, "Infantry spawn"),
    (2, 9, "Airport"),
    (0, 0, "Port"),
    (4, 3, "COM_TOWER"),
    (4, 10, "Lower factory")
]

for x, y, desc in positions:
    tile = rpc_call("tile_get", {"token": token, "x": x, "y": y})
    if "error" not in tile:
        tile_data = tile.get('result', {})
        map_tile = tile_data.get('mapTile', {})
        tile_type = map_tile.get('type', 'Unknown')
        army = map_tile.get('army', 'None')
        print(f"({x},{y}) {desc}: {tile_type} owned by {army}")
    else:
        print(f"({x},{y}) {desc}: Error - {tile.get('error')}")

# Try transport test
print("\n--- Transport Test ---")
# Create APC at actual factory
factories = []
for y in range(board_data.get('height', 10)):
    for x in range(board_data.get('width', 12)):
        tile = rpc_call("tile_get", {"token": token, "x": x, "y": y})
        if "error" not in tile:
            tile_data = tile.get('result', {})
            if tile_data.get('mapTile', {}).get('type') == 'FACTORY':
                army = tile_data.get('mapTile', {}).get('army')
                factories.append((x, y, army))

print(f"\nFactories found: {factories}")

if factories:
    # Use first RED factory
    red_factories = [(x, y) for x, y, army in factories if army == "RED"]
    if red_factories:
        fx, fy = red_factories[0]
        print(f"\nUsing RED factory at ({fx},{fy})")
        
        # Create APC
        apc = rpc_call("unit_create", {
            "token": token,
            "army": "RED",
            "unit_type": "APC",
            "x": fx, "y": fy
        })
        print(f"APC created: {'error' not in apc}")
        
        # Create infantry nearby
        inf = rpc_call("unit_create", {
            "token": token,
            "army": "RED",
            "unit_type": "INFANTRY",
            "x": fx + 1, "y": fy
        })
        print(f"Infantry created at ({fx+1},{fy}): {'error' not in inf}")
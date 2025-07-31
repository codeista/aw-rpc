#!/usr/bin/env python3
"""Simple test to check map tiles"""

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

# Get full board
board = rpc_call("game_board", {"token": token})
board_data = board.get('result', {})

print(f"Map: {board_data.get('map_name')}")
print(f"Size: {board_data.get('width')}x{board_data.get('height')}")

# Check grid data
grid = board_data.get('grid', [])
if grid and len(grid) > 0:
    # Look for facilities
    factories = []
    airports = []
    ports = []
    com_towers = []
    
    for row in grid:
        for tile in row:
            x, y = tile.get('x', 0), tile.get('y', 0)
            map_tile = tile.get('mapTile', {})
            tile_type = map_tile.get('type', '')
            army = map_tile.get('army', '')
            
            if tile_type == 'FACTORY':
                factories.append((x, y, army))
            elif tile_type == 'AIRPORT':
                airports.append((x, y, army))
            elif tile_type == 'PORT':
                ports.append((x, y, army))
            elif tile_type == 'COM_TOWER':
                com_towers.append((x, y, army))
                
    print(f"\nFactories: {factories}")
    print(f"Airports: {airports}")
    print(f"Ports: {ports}")
    print(f"COM_TOWERS: {com_towers}")
    
    # Try creating units at actual positions
    if factories:
        fx, fy, farm = factories[0]
        print(f"\nCreating APC at factory ({fx},{fy})")
        apc = rpc_call("unit_create", {
            "token": token,
            "army": farm,
            "unit_type": "APC",
            "x": fx, "y": fy
        })
        print(f"Result: {'error' not in apc}")
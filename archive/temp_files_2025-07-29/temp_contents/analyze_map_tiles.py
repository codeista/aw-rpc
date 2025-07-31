#!/usr/bin/env python3
"""Analyze map tiles properly"""

import requests
import json

def rpc_call(method, params):
    response = requests.post("http://localhost:5000/api", json={
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    })
    return response.json()

# Create test game
result = rpc_call("game_create_test", {"token": "maptest"})

# Get board
board = rpc_call("game_board", {"token": "maptest"})
board_data = board.get('result', {})

width = board_data.get('width', 12)
height = board_data.get('height', 10)
grid = board_data.get('grid', [])

# Find all facilities
facilities = {
    'FACTORY': [],
    'AIRPORT': [],
    'PORT': [],
    'COM_TOWER': [],
    'BASE_TOWER_0': [],
    'BASE_TOWER_1': []
}

for tile in grid:
    if isinstance(tile, dict):
        x = tile.get('x', 0)
        y = tile.get('y', 0)
        map_tile = tile.get('mapTile', {})
        tile_type = map_tile.get('type', '')
        army = map_tile.get('army', '')
        
        if tile_type in facilities:
            facilities[tile_type].append((x, y, army))

# Print facilities
print("=== FACILITIES FOUND ===")
for facility_type, locations in facilities.items():
    if locations:
        print(f"\n{facility_type}:")
        for x, y, army in locations:
            print(f"  ({x},{y}) - {army}")

# Create a visual map
print("\n=== MAP LAYOUT ===")
# Create 2D grid
map_grid = [[' ' for _ in range(width)] for _ in range(height)]

# Mapping of tile types to symbols
symbols = {
    'FACTORY': 'F',
    'AIRPORT': 'A', 
    'PORT': 'P',
    'COM_TOWER': 'C',
    'BASE_TOWER_0': 'H',  # HQ
    'BASE_TOWER_1': 'H',
    'CITY': 'c',
    'SEA': '~',
    'REEF': 'r',
    'PLAIN': '.',
    'MOUNTAIN': 'M',
    'WOOD': 'W',
    'ROAD': '+',
    'RIVER': '='
}

for tile in grid:
    if isinstance(tile, dict):
        x = tile.get('x', 0)
        y = tile.get('y', 0)
        map_tile = tile.get('mapTile', {})
        tile_type = map_tile.get('type', '')
        
        if 0 <= x < width and 0 <= y < height:
            symbol = symbols.get(tile_type, tile_type[0] if tile_type else '?')
            map_grid[y][x] = symbol

# Print map
print("   " + "".join(str(i % 10) for i in range(width)))
for y, row in enumerate(map_grid):
    print(f"{y:2d} {''.join(row)}")

# Test specific positions
print("\n=== KEY POSITIONS ===")
# COM_TOWER should be findable
if facilities['COM_TOWER']:
    print(f"COM_TOWER at: {facilities['COM_TOWER']}")
else:
    print("No COM_TOWER found on test map")

# Find good positions for tests
red_factories = [(x, y) for x, y, army in facilities['FACTORY'] if army == 'RED']
blue_factories = [(x, y) for x, y, army in facilities['FACTORY'] if army == 'BLUE']

print(f"\nRED factories: {red_factories}")
print(f"BLUE factories: {blue_factories}")
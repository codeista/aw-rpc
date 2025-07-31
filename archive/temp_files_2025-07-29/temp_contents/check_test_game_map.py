#!/usr/bin/env python3
"""Check what's in the test game map"""

import requests
import json

# Create test game
response = requests.post("http://localhost:5000/api", json={
    "jsonrpc": "2.0",
    "method": "game_create_test",
    "params": {"token": "mapanalysis"},
    "id": 1
})

# Get board
response = requests.post("http://localhost:5000/api", json={
    "jsonrpc": "2.0",
    "method": "game_board",
    "params": {"token": "mapanalysis"},
    "id": 2
})

board = response.json().get('result', {})
width = board.get('width', 0)
height = board.get('height', 0)

print(f"Test map size: {width}x{height}")

# Count different tile types
tile_counts = {}
production_facilities = []
special_tiles = []

for y in range(height):
    for x in range(width):
        idx = y * width + x
        if idx < len(board['grid']):
            tile = board['grid'][idx]
            tile_type = tile.get('mapTile', {}).get('type')
            army = tile.get('mapTile', {}).get('army')
            
            # Count tile types
            if tile_type not in tile_counts:
                tile_counts[tile_type] = 0
            tile_counts[tile_type] += 1
            
            # Track production facilities
            if tile_type in ['FACTORY', 'AIRPORT', 'PORT']:
                production_facilities.append({
                    'type': tile_type,
                    'position': (x, y),
                    'army': army
                })
            
            # Track special tiles
            if tile_type in ['COM_TOWER', 'LAB', 'MISSILE_SILO', 'BASE_TOWER_0', 'BASE_TOWER_1', 'BASE_TOWER_2', 'BASE_TOWER_3', 'BASE_TOWER_4']:
                special_tiles.append({
                    'type': tile_type,
                    'position': (x, y),
                    'army': army
                })

print("\nTile type counts:")
for tile_type, count in sorted(tile_counts.items()):
    print(f"  {tile_type}: {count}")

print(f"\nProduction facilities ({len(production_facilities)}):")
for facility in production_facilities:
    print(f"  {facility['type']} at {facility['position']} owned by {facility['army']}")

print(f"\nSpecial tiles ({len(special_tiles)}):")
for tile in special_tiles:
    print(f"  {tile['type']} at {tile['position']} owned by {tile['army']}")
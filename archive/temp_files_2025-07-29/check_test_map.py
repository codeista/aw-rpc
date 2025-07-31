#!/usr/bin/env python3
"""Check what facilities are in the test map"""

import requests
import json

# Create test game
response = requests.post("http://localhost:5000/api", json={
    "jsonrpc": "2.0",
    "method": "game_create_test",
    "params": {"token": "mapcheck"},
    "id": 1
})

# Get board
response = requests.post("http://localhost:5000/api", json={
    "jsonrpc": "2.0",
    "method": "game_board",
    "params": {"token": "mapcheck"},
    "id": 2
})

board = response.json().get('result', {})
width = board.get('width', 0)
height = board.get('height', 0)

print(f"Map size: {width}x{height}")

# Find all production facilities
facilities = []
for y in range(height):
    for x in range(width):
        idx = y * width + x
        if idx < len(board['grid']):
            tile = board['grid'][idx]
            tile_type = tile.get('mapTile', {}).get('type')
            army = tile.get('mapTile', {}).get('army')
            
            if tile_type in ['FACTORY', 'AIRPORT', 'PORT']:
                facilities.append((x, y, tile_type, army))

print("\nProduction facilities found:")
for x, y, ftype, army in facilities:
    print(f"  ({x},{y}): {ftype} owned by {army}")

# Check specific locations
print(f"\nChecking test locations:")
print(f"  (0,3): {board['grid'][3*width + 0].get('mapTile', {}).get('type')}")
print(f"  (0,8): {board['grid'][8*width + 0].get('mapTile', {}).get('type') if 8*width < len(board['grid']) else 'OUT OF BOUNDS'}")
print(f"  (0,7): {board['grid'][7*width + 0].get('mapTile', {}).get('type') if 7*width < len(board['grid']) else 'OUT OF BOUNDS'}")
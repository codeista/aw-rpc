#!/usr/bin/env python3
"""Check what tiles are around the factory"""

import requests

# Create test game
response = requests.post("http://localhost:5000/api", json={
    "jsonrpc": "2.0",
    "method": "game_create_test",
    "params": {"token": "mapcheck2"},
    "id": 1
})

# Get board
response = requests.post("http://localhost:5000/api", json={
    "jsonrpc": "2.0",
    "method": "game_board",
    "params": {"token": "mapcheck2"},
    "id": 2
})

board = response.json().get('result', {})
width = board.get('width', 12)

# Check tiles around factory at (0,4)
positions = [
    (0, 3), (1, 3),
    (0, 4), (1, 4), 
    (0, 5), (1, 5)
]

print("Tiles around factory at (0,4):")
for x, y in positions:
    if 0 <= x < width and 0 <= y < 10:
        idx = y * width + x
        if idx < len(board['grid']):
            tile = board['grid'][idx]
            tile_type = tile['mapTile']['type']
            army = tile['mapTile'].get('army', 'neutral')
            unit = tile.get('unit', {}).get('type', 'None') if tile.get('unit') else 'None'
            print(f"  ({x},{y}): {tile_type} ({army}) - unit: {unit}")
        else:
            print(f"  ({x},{y}): OUT OF BOUNDS")
    else:
        print(f"  ({x},{y}): INVALID COORDS")
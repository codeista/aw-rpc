#!/usr/bin/env python3
"""Understand the grid structure once and for all"""

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
result = rpc_call("game_create_test", {"token": "gridtest"})

# Get board
board = rpc_call("game_board", {"token": "gridtest"})
board_data = board.get('result', {})

grid = board_data.get('grid', [])

print("=== GRID STRUCTURE ===")
print(f"Grid type: {type(grid)}")
print(f"Grid is a list: {isinstance(grid, list)}")
print(f"Grid length: {len(grid)}")
print(f"Board size: {board_data.get('width')}x{board_data.get('height')}")

if grid:
    print(f"\nFirst element type: {type(grid[0])}")
    print(f"First element: {json.dumps(grid[0], indent=2)}")
    
    # The grid is a FLAT LIST of tiles, not a 2D array
    # Each tile has x,y coordinates
    print("\n=== UNDERSTANDING ===")
    print("Grid is a FLAT LIST of tile objects")
    print("Each tile has: x, y, mapTile, unit, etc.")
    print("To find a tile at (x,y), I need to search the list, not index grid[y][x]")
    
    # Helper function to find tile at position
    def get_tile_at(grid, x, y):
        for tile in grid:
            if tile.get('x') == x and tile.get('y') == y:
                return tile
        return None
    
    # Test it
    tile_0_0 = get_tile_at(grid, 0, 0)
    if tile_0_0:
        print(f"\nTile at (0,0): {tile_0_0.get('mapTile', {}).get('type')}")
#!/usr/bin/env python3
"""Debug transport loading issue"""

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
result = rpc_call("game_create_test", {"token": "transport_debug"})

# Create units at correct positions
apc = rpc_call("unit_create", {
    "token": "transport_debug",
    "army": "RED",
    "unit_type": "APC",
    "x": 0, "y": 4
})
print(f"APC created: {'error' not in apc}")

infantry = rpc_call("unit_create", {
    "token": "transport_debug",
    "army": "RED", 
    "unit_type": "INFANTRY",
    "x": 1, "y": 4
})
print(f"Infantry created: {'error' not in infantry}")

# Check units were created
board = rpc_call("game_board", {"token": "transport_debug"})
grid = board.get('result', {}).get('grid', [])

# Find our units
for tile in grid:
    if tile.get('unit'):
        unit = tile.get('unit')
        print(f"Unit at ({tile['x']},{tile['y']}): {unit.get('type')} - can_move={unit.get('can_move')}")

# End turns
print("\nEnding turns...")
rpc_call("army_end_turn", {"token": "transport_debug"})
rpc_call("army_end_turn", {"token": "transport_debug"})

# Check units again
board2 = rpc_call("game_board", {"token": "transport_debug"})
grid2 = board2.get('result', {}).get('grid', [])

print("\nAfter ending turns:")
for tile in grid2:
    if tile.get('unit'):
        unit = tile.get('unit')
        print(f"Unit at ({tile['x']},{tile['y']}): {unit.get('type')} - can_move={unit.get('can_move')}")

# Try to move infantry into APC
print("\nAttempting to load infantry into APC...")
move = rpc_call("unit_move", {
    "token": "transport_debug",
    "x": 1, "y": 4,
    "x2": 0, "y2": 4
})

print(f"Move result: {json.dumps(move, indent=2)}")

# Check if it's a valid transport move
valid_moves = rpc_call("unit_valid_moves", {
    "token": "transport_debug",
    "x": 1, "y": 4
})
print(f"\nValid moves for infantry: {json.dumps(valid_moves, indent=2)}")
#!/usr/bin/env python3
"""Debug why MECH can't move but INFANTRY can"""

import requests
import json

def rpc_call(method, params):
    response = requests.post("http://localhost:5000/api", json={
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    })
    return response.json().get('result', {})

# Create test game
game_id = "mechdebug"
rpc_call("game_create_test", {"token": game_id})

# Create MECH at factory
print("Creating MECH at factory (0,4)...")
result = rpc_call("unit_create", {
    "token": game_id,
    "army": "RED",
    "unit_type": "MECH",
    "x": 0, "y": 4
})

# End turns
rpc_call("army_end_turn", {"token": game_id})
rpc_call("army_end_turn", {"token": game_id})

# Get board state
board = rpc_call("game_board", {"token": game_id})
print(f"Current turn: {board['current_turn']}")

# Check where INFANTRY moved to
idx_14 = 4 * 12 + 1  # (1,4)
tile_14 = board['grid'][idx_14]
print(f"\nTile at (1,4): {tile_14['mapTile']['type']}")
if tile_14.get('unit'):
    print(f"  Unit: {tile_14['unit']['type']} ({tile_14['unit']['army']})")

# Get movement options for MECH
print("\nGetting movement range for MECH...")
move_options = rpc_call("movement_range", {
    "token": game_id,
    "unit_x": 0, "unit_y": 4
})

if "error" not in move_options:
    if "reachable_tiles" in move_options:
        tiles = move_options["reachable_tiles"]
        print(f"MECH can move to {len(tiles)} tiles:")
        for tile in tiles[:5]:  # Show first 5
            print(f"  - ({tile['x']},{tile['y']}): {tile.get('terrain_type', 'unknown')}")
    else:
        print(f"Movement options: {json.dumps(move_options, indent=2)}")
else:
    print(f"Error getting movement options: {move_options}")
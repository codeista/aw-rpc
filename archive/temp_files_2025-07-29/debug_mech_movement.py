#!/usr/bin/env python3
"""Debug MECH movement issue"""

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
game_id = "debugmech"
rpc_call("game_create_test", {"token": game_id})

# Create INFANTRY first
print("Creating INFANTRY...")
result = rpc_call("unit_create", {
    "token": game_id,
    "army": "RED",
    "unit_type": "INFANTRY",
    "x": 0, "y": 4
})
print(f"INFANTRY creation: {'SUCCESS' if 'unit' in result else 'FAILED'}")

# End turns to enable movement
rpc_call("army_end_turn", {"token": game_id})  # RED ends
rpc_call("army_end_turn", {"token": game_id})  # BLUE ends

# Try to move INFANTRY
print("\nAttempting to move INFANTRY from (0,4) to (1,4)...")
move_result = rpc_call("unit_move", {
    "token": game_id,
    "x": 0, "y": 4,
    "x2": 1, "y2": 4
})
print(f"INFANTRY move result: {json.dumps(move_result, indent=2)}")

# End turn after movement
rpc_call("army_end_turn", {"token": game_id})

# Create MECH
print("\nCreating MECH...")
result = rpc_call("unit_create", {
    "token": game_id,
    "army": "RED", 
    "unit_type": "MECH",
    "x": 0, "y": 4
})
print(f"MECH creation: {'SUCCESS' if 'unit' in result else 'FAILED'}")

# End turns to enable movement
rpc_call("army_end_turn", {"token": game_id})  # RED ends
rpc_call("army_end_turn", {"token": game_id})  # BLUE ends

# Try to move MECH
print("\nAttempting to move MECH from (0,4) to (0,5)...")
move_result = rpc_call("unit_move", {
    "token": game_id,
    "x": 0, "y": 4,
    "x2": 0, "y2": 5
})
print(f"MECH move result: {json.dumps(move_result, indent=2)}")

# Check what's at those positions
board = rpc_call("game_board", {"token": game_id})
width = board.get('width', 12)
height = board.get('height', 10)

print(f"\nBoard size: {width}x{height}")

# Check tiles
idx_04 = 4 * width + 0
idx_05 = 5 * width + 0

if idx_04 < len(board['grid']):
    tile_04 = board['grid'][idx_04]
    print(f"Tile at (0,4): {tile_04['mapTile']['type']}, unit: {tile_04.get('unit', {}).get('type', 'None')}")
else:
    print("(0,4) is out of bounds!")

if idx_05 < len(board['grid']):
    tile_05 = board['grid'][idx_05]
    print(f"Tile at (0,5): {tile_05['mapTile']['type']}, unit: {tile_05.get('unit', {}).get('type', 'None')}")
else:
    print("(0,5) is out of bounds!")

# Try different movement targets
print("\nTrying different movement targets for MECH...")
for dx, dy in [(1, 0), (0, -1), (-1, 0)]:
    target_x, target_y = 0 + dx, 4 + dy
    if 0 <= target_x < width and 0 <= target_y < height:
        print(f"\nTrying to move MECH to ({target_x},{target_y})...")
        move_result = rpc_call("unit_move", {
            "token": game_id,
            "x": 0, "y": 4,
            "x2": target_x, "y2": target_y
        })
        if "error" in move_result:
            print(f"  Failed: {move_result.get('message', 'Unknown error')}")
        else:
            print(f"  Success! Moved to ({target_x},{target_y})")
            break
#!/usr/bin/env python3
"""Test unit delete fix"""

import requests
import json
import time

def rpc_call(method, params):
    response = requests.post("http://localhost:5000/api", json={
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    })
    return response.json()

# Use a unique token for this test
token = "delete_test_fix"
print(f"Creating game with token: {token}")

# Create test game
result = rpc_call("game_create_test", {"token": token})
print(f"Game created: {result}")

# Create a unit
print("\nCreating INFANTRY at (0,4)...")
unit = rpc_call("unit_create", {
    "token": token,
    "army": "RED",
    "unit_type": "INFANTRY",
    "x": 0, "y": 4
})
print(f"Unit created: {'error' not in unit}")

# Wait a moment for logs
time.sleep(0.5)

# Delete the unit
print("\nDeleting unit at (0,4)...")
delete = rpc_call("unit_delete", {
    "token": token,
    "x": 0, "y": 4
})
print(f"Delete response: {json.dumps(delete, indent=2)}")

# Check if unit is gone
print("\nChecking if unit was deleted...")
board = rpc_call("game_board", {"token": token})
grid = board.get('result', {}).get('grid', [])

# Find tile at (0,4)
unit_found = False
for tile in grid:
    if tile.get('x') == 0 and tile.get('y') == 4:
        if tile.get('unit'):
            unit_found = True
            print(f"ERROR: Unit still exists at (0,4)!")
        else:
            print(f"SUCCESS: No unit at (0,4)")
        break

print("\nTest complete. Check logs for any errors.")
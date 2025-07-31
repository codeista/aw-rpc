#!/usr/bin/env python3
"""Debug test issues"""

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

# Test COM_TOWER bonus issue
token = generate_token()
print("=== Testing COM_TOWER Bonus ===")
result = rpc_call("game_create_test", {"token": token})
print(f"Game created: {token}")

# Create tanks
tank1 = rpc_call("unit_create", {
    "token": token,
    "army": "RED",
    "unit_type": "TANK",
    "x": 4, "y": 1
})
print(f"Tank1 result: {'error' in tank1}")

tank2 = rpc_call("unit_create", {
    "token": token,
    "army": "BLUE", 
    "unit_type": "TANK",
    "x": 11, "y": 1
})
print(f"Tank2 result: {'error' in tank2}")

# Test combat preview
preview = rpc_call("combat_preview", {
    "token": token,
    "attacker_x": 4, "attacker_y": 1,
    "defender_x": 11, "defender_y": 1
})
print(f"Combat preview: {json.dumps(preview, indent=2)}")

# Test transport issue
print("\n=== Testing Transport ===")
token2 = generate_token()
result = rpc_call("game_create_test", {"token": token2})

# Check board for factory location
board = rpc_call("game_board", {"token": token2})
board_data = board.get('result', {})
print(f"Board size: {board_data.get('width')}x{board_data.get('height')}")

# Create APC and infantry
apc = rpc_call("unit_create", {
    "token": token2,
    "army": "RED",
    "unit_type": "APC",
    "x": 4, "y": 2
})
print(f"APC create: {'error' in apc}")

infantry = rpc_call("unit_create", {
    "token": token2,
    "army": "RED", 
    "unit_type": "INFANTRY",
    "x": 3, "y": 2
})
print(f"Infantry create: {'error' in infantry}")

# End turns to enable movement
rpc_call("army_end_turn", {"token": token2})
rpc_call("army_end_turn", {"token": token2})

# Try to move infantry into APC
move = rpc_call("unit_move", {
    "token": token2,
    "x": 3, "y": 2,
    "x2": 4, "y2": 2
})
print(f"Move result: {json.dumps(move, indent=2)}")

# Test production variety funds
print("\n=== Testing Production Funds ===")
token3 = generate_token()
result = rpc_call("game_create_test", {"token": token3})

# Check funds
board = rpc_call("game_board", {"token": token3})
board_data = board.get('result', {})
print(f"Player funds: {board_data.get('player_funds')}")
print(f"Army funds: {board_data.get('army_funds')}")

# Try expensive units
units_to_test = [
    ("MISSILE", 12000),
    ("BOMBER", 22000),
    ("BATTLESHIP", 28000)
]

for unit_type, cost in units_to_test:
    unit = rpc_call("unit_create", {
        "token": token3,
        "army": "RED",
        "unit_type": unit_type,
        "x": 5, "y": 5
    })
    if "error" in unit:
        print(f"{unit_type} ({cost}): {unit.get('error', {}).get('message', 'Unknown error')}")
    else:
        print(f"{unit_type} ({cost}): ✅ Created")
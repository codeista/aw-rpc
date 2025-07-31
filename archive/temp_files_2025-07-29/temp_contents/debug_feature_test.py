#!/usr/bin/env python3
"""Debug feature test issues"""

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

# Test 1: Create test game
token = generate_token()
print(f"Creating test game: {token}")
result = rpc_call("game_create_test", {"token": token})
print(f"Result: {json.dumps(result, indent=2)}")

if "error" not in result:
    # Get board info
    board = rpc_call("game_board", {"token": token})
    board_data = board.get('result', {})
    
    # Check funds
    print(f"\nRED funds: {board_data.get('red_funds', 0)}")
    print(f"BLUE funds: {board_data.get('blue_funds', 0)}")
    
    # Try to create expensive unit
    print("\nCreating TANK...")
    tank = rpc_call("unit_create", {
        "token": token,
        "army": "RED",
        "unit_type": "TANK",
        "x": 0, "y": 4  # Factory position
    })
    print(f"Tank result: {json.dumps(tank, indent=2)}")
    
    # Try combat preview
    print("\nCreating second tank...")
    tank2 = rpc_call("unit_create", {
        "token": token,
        "army": "BLUE",
        "unit_type": "TANK",
        "x": 8, "y": 4  # Factory position
    })
    
    print("\nTrying combat preview...")
    preview = rpc_call("combat_preview", {
        "token": token,
        "attacker_x": 0, "attacker_y": 4,
        "target_x": 8, "target_y": 4
    })
    print(f"Preview result: {json.dumps(preview, indent=2)}")
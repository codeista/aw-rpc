#!/usr/bin/env python3
"""Debug unit creation flags"""

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

# Create test game
token = generate_token()
result = rpc_call("game_create_test", {"token": token})
print(f"Game created: {token}")

# Create a tank and check its flags
tank = rpc_call("unit_create", {
    "token": token,
    "army": "RED",
    "unit_type": "TANK",
    "x": 5, "y": 5
})

if "error" not in tank:
    unit_data = tank.get('result', {}).get('unit', {})
    print(f"\nUnit created:")
    print(f"  Type: {unit_data.get('type')}")
    print(f"  Army: {unit_data.get('army')}")
    print(f"  can_move: {unit_data.get('can_move')}")
    print(f"  can_attack: {unit_data.get('can_attack')}")
    print(f"  can_capture: {unit_data.get('can_capture')}")
    print(f"  has_moved_this_turn: {unit_data.get('status', {}).get('has_moved_this_turn')}")
    
    # Check tile info
    tile_info = rpc_call("tile_info", {
        "token": token,
        "x": 5, "y": 5
    })
    
    if "error" not in tile_info:
        unit_from_tile = tile_info.get('result', {}).get('unit', {})
        print(f"\nUnit from tile_info:")
        print(f"  can_move: {unit_from_tile.get('can_move')}")
        print(f"  can_attack: {unit_from_tile.get('can_attack')}")
        
# Test after ending turn
print("\n--- After ending turns ---")
rpc_call("army_end_turn", {"token": token})
rpc_call("army_end_turn", {"token": token})

tile_info2 = rpc_call("tile_info", {
    "token": token,
    "x": 5, "y": 5
})

if "error" not in tile_info2:
    unit_after = tile_info2.get('result', {}).get('unit', {})
    print(f"Unit after turn:")
    print(f"  can_move: {unit_after.get('can_move')}")
    print(f"  can_attack: {unit_after.get('can_attack')}")
    
# Test combat preview now
tank2 = rpc_call("unit_create", {
    "token": token,
    "army": "BLUE",
    "unit_type": "TANK",
    "x": 7, "y": 5
})

preview = rpc_call("combat_preview", {
    "token": token,
    "attacker_x": 5, "attacker_y": 5,
    "defender_x": 7, "defender_y": 5
})

print(f"\nCombat preview: {json.dumps(preview, indent=2)}")
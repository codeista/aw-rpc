#!/usr/bin/env python3
"""Test adjacent combat"""

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

# Create adjacent tanks
tank1 = rpc_call("unit_create", {
    "token": token,
    "army": "RED",
    "unit_type": "TANK",
    "x": 5, "y": 5
})

tank2 = rpc_call("unit_create", {
    "token": token,
    "army": "BLUE",
    "unit_type": "TANK",
    "x": 6, "y": 5  # Adjacent
})

print("Created adjacent tanks at (5,5) and (6,5)")

# End turns to enable actions
print("\nEnding turns...")
rpc_call("army_end_turn", {"token": token})
rpc_call("army_end_turn", {"token": token})

# Check unit status
tile1 = rpc_call("tile_info", {"token": token, "x": 5, "y": 5})
if "error" not in tile1:
    unit1 = tile1.get('result', {}).get('unit', {})
    print(f"\nRED tank after turn:")
    print(f"  can_attack: {unit1.get('can_attack')}")
    print(f"  can_move: {unit1.get('can_move')}")

# Try combat preview
preview = rpc_call("combat_preview", {
    "token": token,
    "attacker_x": 5, "attacker_y": 5,
    "defender_x": 6, "defender_y": 5
})

print(f"\nCombat preview: {json.dumps(preview, indent=2)}")

# Try actual attack
attack = rpc_call("unit_attack", {
    "token": token,
    "x": 5, "y": 5,
    "x2": 6, "y2": 5
})

print(f"\nAttack result: {json.dumps(attack, indent=2)}")
#!/usr/bin/env python3
"""Debug COM_TOWER test"""

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

# Replicate the COM_TOWER test
token = generate_token()
result = rpc_call("game_create_test", {"token": token})
print(f"Game created: {token}")

# Create tanks
tank1 = rpc_call("unit_create", {
    "token": token,
    "army": "RED",
    "unit_type": "TANK",
    "x": 5, "y": 5
})
print(f"Tank1 created: {'error' not in tank1}")

tank2 = rpc_call("unit_create", {
    "token": token,
    "army": "BLUE",
    "unit_type": "TANK", 
    "x": 6, "y": 5
})
print(f"Tank2 created: {'error' not in tank2}")

# End turns
rpc_call("army_end_turn", {"token": token})
rpc_call("army_end_turn", {"token": token})

# Try combat preview
preview1 = rpc_call("combat_preview", {
    "token": token,
    "attacker_x": 5, "attacker_y": 5,
    "defender_x": 6, "defender_y": 5
})

print(f"\nCombat preview response:")
print(json.dumps(preview1, indent=2))

# Check the actual structure
if "result" in preview1:
    result = preview1["result"]
    print(f"\nResult type: {type(result)}")
    print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
    
    # Check for different possible structures
    if "damage" in result:
        print(f"Has 'damage' key")
        damage = result["damage"]
        print(f"Damage info: {damage}")
    
    if "damage_info" in result:
        print(f"Has 'damage_info' key")
        
    if "attacker_damage" in result.get("damage", {}):
        print(f"Attacker damage: {result['damage']['attacker_damage']}")
#!/usr/bin/env python3
"""Debug transport_load response"""

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
result = rpc_call("game_create_test", {"token": "loadtest"})

# Create units
apc = rpc_call("unit_create", {
    "token": "loadtest",
    "army": "RED",
    "unit_type": "APC",
    "x": 0, "y": 4
})

infantry = rpc_call("unit_create", {
    "token": "loadtest",
    "army": "RED", 
    "unit_type": "INFANTRY",
    "x": 1, "y": 4
})

# End turns
rpc_call("army_end_turn", {"token": "loadtest"})
rpc_call("army_end_turn", {"token": "loadtest"})

# Try transport_load
load = rpc_call("transport_load", {
    "token": "loadtest",
    "transport_x": 0, "transport_y": 4,
    "cargo_x": 1, "cargo_y": 4
})

print("Load response:")
print(json.dumps(load, indent=2))

# Check structure
print(f"\nHas 'error' key: {'error' in load}")
print(f"Has 'result' key: {'result' in load}")

if 'result' in load:
    result = load['result']
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
    
# Also check what the test expects
print(f"\nTest condition: 'error' not in load = {'error' not in load}")
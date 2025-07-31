#!/usr/bin/env python3
"""Debug production funds issue"""

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
token = "prodtest"
result = rpc_call("game_create_test", {"token": token})
print(f"Game created: {result}")

# Check funds
board = rpc_call("game_board", {"token": token})
board_data = board.get('result', {})

print(f"\nFunds check:")
print(f"  player_funds: {board_data.get('player_funds')}")
print(f"  army_funds: {board_data.get('army_funds')}")

# Try to create units starting with cheap ones
units = [
    ("INFANTRY", 1000),
    ("MECH", 3000),
    ("RECON", 4000),
    ("TANK", 7000),
    ("MISSILE", 12000),
    ("BOMBER", 22000),
    ("BATTLESHIP", 28000)
]

# First delete any existing unit at factory
rpc_call("unit_delete", {"token": token, "x": 0, "y": 4})

total_spent = 0
for unit_type, cost in units:
    print(f"\nTrying {unit_type} (cost: {cost}, total so far: {total_spent})")
    
    # Delete previous unit
    rpc_call("unit_delete", {"token": token, "x": 0, "y": 4})
    
    # Create unit
    result = rpc_call("unit_create", {
        "token": token,
        "army": "RED",
        "unit_type": unit_type,
        "x": 0, "y": 4
    })
    
    if "error" in result:
        print(f"  Failed: {result.get('error')}")
        break
    else:
        # Check if it's an error wrapped in result
        result_data = result.get('result', {})
        if isinstance(result_data, dict) and result_data.get('error'):
            print(f"  Failed: {result_data.get('message', 'Unknown error')}")
            break
        else:
            print(f"  ✅ Created successfully")
            total_spent += cost
            
            # Check remaining funds
            board = rpc_call("game_board", {"token": token})
            board_data = board.get('result', {})
            player_funds = board_data.get('player_funds', {})
            print(f"  Remaining funds: {player_funds.get('0', 'Unknown')}")
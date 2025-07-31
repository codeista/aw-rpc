#!/usr/bin/env python3
"""Test production funds issue"""

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

# Test exactly like the feature test does
print("Testing production variety funds issue...")

token = generate_token()
print(f"Generated token: {token}")

result = rpc_call("game_create_test", {"token": token})
print(f"Game created: {result}")

# Check funds immediately
board = rpc_call("game_board", {"token": token})
board_data = board.get('result', {})
player_funds = board_data.get('player_funds', {})
print(f"\nPlayer funds: {player_funds}")
print(f"Fund for player '0': {player_funds.get('0', 'Not found')}")

# Try creating a unit to see if funds work
unit = rpc_call("unit_create", {
    "token": token,
    "army": "RED",
    "unit_type": "INFANTRY",
    "x": 0, "y": 4
})

if "error" not in unit:
    print("\nUnit created successfully")
    
    # Check funds again
    board2 = rpc_call("game_board", {"token": token})
    board_data2 = board2.get('result', {})
    player_funds2 = board_data2.get('player_funds', {})
    print(f"Player funds after unit: {player_funds2.get('0', 'Not found')}")
else:
    print(f"\nFailed to create unit: {unit}")
    
# Check the rpc_call function from the test
def test_rpc_call(method: str, params: dict = None) -> dict:
    """Make RPC call to the server - exactly as in test"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    }
    
    try:
        response = requests.post("http://localhost:5000/api", json=payload)
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
        
        result = response.json()
        if "error" in result:
            return {"error": result["error"]}
        
        # Check if result contains an error structure
        result_data = result.get("result", result)
        if isinstance(result_data, dict) and result_data.get("error") == True:
            # This is an error response wrapped in result
            return {"error": result_data.get("message", "Unknown error")}
        
        return result_data
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

print("\n--- Testing with test's rpc_call ---")
token2 = generate_token()
result2 = test_rpc_call("game_create_test", {"token": token2})
print(f"Result2: {result2}")

board3 = test_rpc_call("game_board", {"token": token2})
print(f"Board3 type: {type(board3)}")
print(f"Board3 player_funds: {board3.get('player_funds', 'Not found')}")
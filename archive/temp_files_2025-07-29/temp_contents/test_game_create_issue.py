#!/usr/bin/env python3
"""Test game_create_test issue"""

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

# Test 1: Direct game_create_test  
token1 = "direct_test"
result1 = rpc_call("game_create_test", {"token": token1})
print(f"Direct test result: {result1}")

board1 = rpc_call("game_board", {"token": token1})
board_data1 = board1.get('result', {})
print(f"Direct test funds: {board_data1.get('player_funds')}")

# Test 2: Generated token like in test
import random
import string
def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

token2 = generate_token()
result2 = rpc_call("game_create_test", {"token": token2})
print(f"\nGenerated token result: {result2}")

board2 = rpc_call("game_board", {"token": token2})
board_data2 = board2.get('result', {})
print(f"Generated token funds: {board_data2.get('player_funds')}")

# Test 3: Check if it's a player_funds format issue
if board_data2.get('player_funds'):
    for key, value in board_data2['player_funds'].items():
        print(f"  Player {key}: {value} (type: {type(value)})")
        
# Check army_funds too
print(f"\nArmy funds: {board_data2.get('army_funds')}")
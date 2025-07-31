#!/usr/bin/env python3
"""Debug production options issue"""

import requests
import json

def rpc_call(method, params):
    response = requests.post("http://localhost:5000/api", json={
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    })
    return response.json().get('result', {})

# Create test game
game_id = "debugprod"
rpc_call("game_create_test", {"token": game_id})

# Get production options for each facility type
facilities = [
    (0, 4, "FACTORY"),   # RED factory
    (0, 7, "AIRPORT"),   # RED airport  
    (0, 0, "PORT")       # RED port
]

for x, y, facility_type in facilities:
    print(f"\n=== {facility_type} at ({x},{y}) ===")
    
    # Check tile first
    board = rpc_call("game_board", {"token": game_id})
    idx = y * 12 + x  # 12 is map width
    tile = board['grid'][idx]
    print(f"Tile type: {tile['mapTile']['type']}")
    print(f"Tile army: {tile['mapTile']['army']}")
    
    # Get production options
    result = rpc_call("get_production_options", {"token": game_id, "x": x, "y": y})
    print(f"Production options result: {json.dumps(result, indent=2)}")
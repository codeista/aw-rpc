#!/usr/bin/env python3
"""
Simple test to verify transport features work
"""

import requests
import json

def rpc_call(method: str, params: dict = None) -> dict:
    """Make RPC call to the server"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    }
    
    response = requests.post("http://localhost:5000/api", json=payload)
    result = response.json()
    if "error" in result:
        return {"error": result["error"]}
    return result.get("result", {})

# Create test game
game_id = "transporttest"
print("Creating test game...")
rpc_call("game_create", {"token": game_id})

# Generate funds
print("\nGenerating funds...")
for i in range(3):
    rpc_call("army_end_turn", {"token": game_id})
    rpc_call("army_end_turn", {"token": game_id})

# Check funds
board = rpc_call("game_board", {"token": game_id})
print(f"Funds - RED: {board.get('red_funds')}, BLUE: {board.get('blue_funds')}")

# Test 1: APC Auto-Resupply
print("\n=== TEST 1: APC Auto-Resupply ===")
print("Creating APC and Infantry...")
rpc_call("unit_create", {"token": game_id, "army": "RED", "unit_type": "APC", "x": 5, "y": 5})
rpc_call("unit_create", {"token": game_id, "army": "RED", "unit_type": "INFANTRY", "x": 6, "y": 5})

# Check if they were created
board = rpc_call("game_board", {"token": game_id})
units_created = []
for y, row in enumerate(board.get("tiles", [])):
    for x, tile in enumerate(row):
        if tile.get("unit"):
            unit = tile["unit"]
            print(f"Found {unit['type']} at ({x},{y}) - Army: {unit['army']}, HP: {unit['hp']}, Fuel: {unit.get('fuel', '?')}")
            units_created.append(unit)

# Test 2: Black Boat Repair
print("\n=== TEST 2: Black Boat Repair ===")

# First find a port on the map
board = rpc_call("game_board", {"token": game_id})
tiles = board.get("tiles", [])
port_pos = None
print("Looking for ports...")
for y, row in enumerate(tiles):
    for x, tile in enumerate(row):
        if 'PORT' in str(tile.get('type', '')):
            port_pos = (x, y)
            print(f"Found port at ({x},{y})")
            break
    if port_pos:
        break

if not port_pos:
    print("No port found, skipping Black Boat test")
else:
    port_x, port_y = port_pos
    print(f"Creating BLACKBOAT at port ({port_x},{port_y})...")
    bb_result = rpc_call("unit_create", {"token": game_id, "army": "RED", "unit_type": "BLACKBOAT", "x": port_x, "y": port_y})
    print(f"BLACKBOAT creation: {'Success' if 'error' not in bb_result else bb_result['error']}")
    
    # Create infantry adjacent to port
    inf_x, inf_y = port_x + 1, port_y  # Try to place adjacent
    inf_result = rpc_call("unit_create", {"token": game_id, "army": "RED", "unit_type": "INFANTRY", "x": inf_x, "y": inf_y})
    print(f"Infantry creation at ({inf_x},{inf_y}): {'Success' if 'error' not in inf_result else inf_result['error']}")

if port_pos:
    # End turn to enable actions
    rpc_call("army_end_turn", {"token": game_id})
    rpc_call("army_end_turn", {"token": game_id})
    
    # Create enemy to damage infantry
    tank_x, tank_y = inf_x + 1, inf_y  # Place tank adjacent to infantry
    tank_result = rpc_call("unit_create", {"token": game_id, "army": "BLUE", "unit_type": "TANK", "x": tank_x, "y": tank_y})
    print(f"Enemy tank creation at ({tank_x},{tank_y}): {'Success' if 'error' not in tank_result else tank_result['error']}")
    
    # Attack to damage infantry
    attack_result = rpc_call("unit_attack", {"token": game_id, "x": tank_x, "y": tank_y, "x2": inf_x, "y2": inf_y})
    print(f"Attack result: {'Success' if 'error' not in attack_result else attack_result['error']}")
    
    # Check damage
    board = rpc_call("game_board", {"token": game_id})
    print("\nUnits after attack:")
    for y, row in enumerate(board.get("tiles", [])):
        for x, tile in enumerate(row):
            if tile.get("unit"):
                unit = tile["unit"]
                if (x,y) in [(port_x, port_y), (inf_x, inf_y), (tank_x, tank_y)]:
                    print(f"  {unit['type']} at ({x},{y}) - Army: {unit['army']}, HP: {unit['hp']}")
    
    # End turn to get back to RED
    rpc_call("army_end_turn", {"token": game_id})
    
    # Try repair
    print("\nAttempting repair...")
    repair_result = rpc_call("repair_unit", {
        "token": game_id,
        "blackboat_x": port_x, "blackboat_y": port_y,
        "target_x": inf_x, "target_y": inf_y,
        "hp_to_repair": 2
    })
    
    if "error" in repair_result:
        print(f"Repair failed: {repair_result['error']}")
    else:
        print(f"Repair successful!")
        print(f"  HP repaired: {repair_result.get('hp_repaired')}")
        print(f"  New HP: {repair_result.get('new_hp')}")
        print(f"  Cost: {repair_result.get('repair_cost')}")

print(f"\nTest game ID: {game_id}")
print("You can check the game at http://localhost:5000/test")
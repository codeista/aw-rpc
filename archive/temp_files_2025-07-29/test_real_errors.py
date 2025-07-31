#!/usr/bin/env python3
"""Test to see real error messages"""

import requests
import json
import random
import string

game_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# Create game
response = requests.post("http://localhost:5000/api", json={
    "jsonrpc": "2.0",
    "method": "game_create_test",
    "params": {"token": game_id},
    "id": 1
})
print(f"Game created: {game_id}")

# Get board to find factory locations
response = requests.post("http://localhost:5000/api", json={
    "jsonrpc": "2.0",
    "method": "game_board",
    "params": {"token": game_id},
    "id": 2  
})
board = response.json().get('result', {})
width = board.get('width', 12)
height = board.get('height', 10)

# Find RED factory
factory_x, factory_y = None, None
for y in range(height):
    for x in range(width):
        idx = y * width + x
        tile = board['grid'][idx]
        if tile.get('mapTile', {}).get('type') == 'FACTORY' and tile.get('mapTile', {}).get('army') == 'RED':
            factory_x, factory_y = x, y
            print(f"Found RED factory at ({x}, {y})")
            break
    if factory_x is not None:
        break

# Create first unit
response = requests.post("http://localhost:5000/api", json={
    "jsonrpc": "2.0",
    "method": "unit_create", 
    "params": {"token": game_id, "army": "RED", "unit_type": "INFANTRY", "x": factory_x, "y": factory_y},
    "id": 3
})
result = response.json()
if 'error' not in result:
    print(f"✅ Created INFANTRY at factory ({factory_x}, {factory_y})")
else:
    print(f"❌ Failed to create INFANTRY: {result}")

# Try to create second unit on same factory
print("\nTrying to create TANK on occupied factory...")
response = requests.post("http://localhost:5000/api", json={
    "jsonrpc": "2.0",
    "method": "unit_create",
    "params": {"token": game_id, "army": "RED", "unit_type": "TANK", "x": factory_x, "y": factory_y},
    "id": 4
})
result = response.json()
error_info = result.get('result', {})
if isinstance(error_info, dict) and error_info.get('error'):
    print(f"Error code: {error_info.get('error_code')}")
    print(f"Error message: {error_info.get('message')}")
    print(f"Details: {error_info.get('details')}")

# Test production options  
print(f"\nTesting production options at factory ({factory_x}, {factory_y})...")
response = requests.post("http://localhost:5000/api", json={
    "jsonrpc": "2.0",
    "method": "get_production_options",
    "params": {"token": game_id, "x": factory_x, "y": factory_y},
    "id": 5
})
result = response.json()
prod_result = result.get('result', {})
if prod_result.get('success'):
    print(f"✅ Production options: {prod_result}")
else:
    print(f"❌ Production options failed: {prod_result}")

# Test insufficient funds
print("\nTesting insufficient funds...")
# Set funds to 500 (not enough for any unit)
response = requests.post("http://localhost:5000/api", json={
    "jsonrpc": "2.0", 
    "method": "set_funds",  # This may not exist
    "params": {"token": game_id, "army": "RED", "amount": 500},
    "id": 6
})

# Or just create expensive units to deplete funds...
# Delete the infantry first
response = requests.post("http://localhost:5000/api", json={
    "jsonrpc": "2.0",
    "method": "unit_delete",
    "params": {"token": game_id, "x": factory_x, "y": factory_y},
    "id": 7  
})

# Create expensive units until funds are low
units = ["BOMBER", "FIGHTER", "BATTLESHIP"]
for unit in units:
    # Skip if not enough game progression
    pass

print("\nDone!")
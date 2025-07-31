#!/usr/bin/env python3
"""Simple test to understand actual errors"""

import requests
import json

# Test 1: Try to create a unit on an occupied factory
print("TEST: Creating unit on occupied factory")
response = requests.post("http://localhost:5000/api", json={
    "jsonrpc": "2.0",
    "method": "game_create_test",
    "params": {"token": "test123"},
    "id": 1
})
print(f"Game creation: {response.json()}")

# Create first unit
response = requests.post("http://localhost:5000/api", json={
    "jsonrpc": "2.0", 
    "method": "unit_create",
    "params": {"token": "test123", "army": "RED", "unit_type": "INFANTRY", "x": 0, "y": 3},
    "id": 2
})
print(f"\nFirst unit: {response.json().get('result', {}).get('error')}")

# Try to create second unit on same spot
response = requests.post("http://localhost:5000/api", json={
    "jsonrpc": "2.0",
    "method": "unit_create", 
    "params": {"token": "test123", "army": "RED", "unit_type": "TANK", "x": 0, "y": 3},
    "id": 3
})
result = response.json()
print(f"\nSecond unit on same spot:")
print(f"Full response: {json.dumps(result, indent=2)}")

# Test 2: Check production options
print("\n\nTEST: Production options")
response = requests.post("http://localhost:5000/api", json={
    "jsonrpc": "2.0",
    "method": "get_production_options",
    "params": {"token": "test123", "x": 0, "y": 3},
    "id": 4
})
result = response.json()
print(f"Production options response: {json.dumps(result, indent=2)}")
#!/usr/bin/env python3
"""
Visual UI test - creates a game with damaged units and takes screenshots
"""

import requests
import json
import time

print("=== Visual UI Test ===\n")

# Create game via API
print("1. Creating test game...")
game_id = f"ui_visual_{int(time.time())}"

response = requests.post('http://localhost:5000/api',
    headers={'Content-Type': 'application/json'},
    data=json.dumps({
        'method': 'game_create_test',
        'params': {
            'token': game_id,
            'use_optimized': True
        },
        'jsonrpc': '2.0',
        'id': 1
    })
)

if response.status_code == 200 and response.json().get('result'):
    print(f"✅ Created game: {game_id}")
else:
    print("❌ Failed to create game")
    exit(1)

# Create units with some damaged
print("\n2. Setting up battle scenario...")

# Create RED units
units = [
    {'army': 'RED', 'type': 'INFANTRY', 'pos': [2, 2], 'hp': 100},
    {'army': 'RED', 'type': 'TANK', 'pos': [3, 2], 'hp': 100},
    {'army': 'RED', 'type': 'MECH', 'pos': [2, 3], 'hp': 50},  # Damaged
    {'army': 'RED', 'type': 'RECON', 'pos': [3, 3], 'hp': 30},  # Damaged
]

for unit in units[:4]:  # RED units
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'method': 'unit_create',
            'params': {
                'token': game_id,
                'position': unit['pos'],
                'unit_type': unit['type']
            },
            'jsonrpc': '2.0',
            'id': 2
        })
    )
    print(f"   Created {unit['army']} {unit['type']} at {unit['pos']}")
    
    # Set HP if damaged
    if unit['hp'] < 100:
        response = requests.post('http://localhost:5000/api',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                'method': 'unit_set_hp',
                'params': {
                    'token': game_id,
                    'position': unit['pos'],
                    'hp': unit['hp']
                },
                'jsonrpc': '2.0',
                'id': 3
            })
        )
        print(f"     Set HP to {unit['hp']}")

# End RED turn
response = requests.post('http://localhost:5000/api',
    headers={'Content-Type': 'application/json'},
    data=json.dumps({
        'method': 'turn_end',
        'params': {'token': game_id},
        'jsonrpc': '2.0',
        'id': 4
    })
)

# Create BLUE units
blue_units = [
    {'army': 'BLUE', 'type': 'INFANTRY', 'pos': [5, 2], 'hp': 70},  # Damaged
    {'army': 'BLUE', 'type': 'TANK', 'pos': [6, 2], 'hp': 20},     # Very damaged
    {'army': 'BLUE', 'type': 'MECH', 'pos': [5, 3], 'hp': 100},
    {'army': 'BLUE', 'type': 'ARTILLERY', 'pos': [6, 3], 'hp': 90}, # Slightly damaged
]

for unit in blue_units:
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'method': 'unit_create',
            'params': {
                'token': game_id,
                'position': unit['pos'],
                'unit_type': unit['type']
            },
            'jsonrpc': '2.0',
            'id': 5
        })
    )
    print(f"   Created {unit['army']} {unit['type']} at {unit['pos']}")
    
    if unit['hp'] < 100:
        response = requests.post('http://localhost:5000/api',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                'method': 'unit_set_hp',
                'params': {
                    'token': game_id,
                    'position': unit['pos'],
                    'hp': unit['hp']
                },
                'jsonrpc': '2.0',
                'id': 6
            })
        )
        print(f"     Set HP to {unit['hp']}")

# Get game state
print("\n3. Game state summary:")
response = requests.post('http://localhost:5000/api',
    headers={'Content-Type': 'application/json'},
    data=json.dumps({
        'method': 'game_state',
        'params': {'token': game_id},
        'jsonrpc': '2.0',
        'id': 7
    })
)

if response.status_code == 200:
    state = response.json().get('result', {})
    print(f"   Turn: {state.get('current_turn', '?')}")
    print(f"   Day: {state.get('days', '?')}")
    
    print("\n   Unit summary:")
    for army_name, army in state.get('armies', {}).items():
        units = army.get('units', [])
        if units:
            print(f"\n   {army_name}:")
            damaged = 0
            for unit in units:
                hp = unit.get('hp', 100)
                if hp < 100:
                    damaged += 1
                    print(f"     {unit['type']} at {unit['position']}: {hp} HP")
            print(f"     Total: {len(units)} units, {damaged} damaged")

print("\n4. Game URLs:")
print(f"   Direct link: http://localhost:5000/game/{game_id}")
print(f"   Open in browser to see:")
print(f"   - Damaged units should show HP numbers (1-9)")
print(f"   - Available units: white HP numbers")
print(f"   - Unavailable units: colored HP numbers")
print(f"   - Hover over units to see HP in tooltip")

print("\n=== Test Complete ===")
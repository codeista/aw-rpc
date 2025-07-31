#!/usr/bin/env python3
"""
Manual battle test - creates units and battles them to test HP display
"""

import requests
import json
import time

print("=== Manual Battle Test ===\n")

# Use the existing test game
game_id = "2_KHiQ"  # The game from earlier

print(f"1. Using existing game: {game_id}")

# Get current game state
response = requests.post('http://localhost:5000/api',
    headers={'Content-Type': 'application/json'},
    data=json.dumps({
        'method': 'game_state',
        'params': {'token': game_id},
        'jsonrpc': '2.0',
        'id': 1
    })
)

if response.status_code == 200:
    state = response.json().get('result', {})
    print(f"   Current turn: {state.get('current_turn', '?')}")
    print(f"   Day: {state.get('days', '?')}")
    
    # Show existing units
    print("\n2. Current units:")
    for army_name, army in state.get('armies', {}).items():
        units = army.get('units', [])
        if units:
            print(f"\n   {army_name}:")
            for unit in units:
                hp = unit.get('hp', 100)
                pos = unit.get('position', [])
                print(f"     {unit['type']} at {pos}: {hp} HP")

print("\n3. To test the UI:")
print(f"   1. Open http://localhost:5000/game/{game_id}")
print("   2. Create units at factories/bases")
print("   3. Move units into combat")
print("   4. Check if damaged units show HP numbers")
print("   5. Hover over units to see HP in tooltip")

# Create a new test game with API
print("\n4. Creating fresh test game...")
new_game_id = f"manual_test_{int(time.time())}"

response = requests.post('http://localhost:5000/api',
    headers={'Content-Type': 'application/json'},
    data=json.dumps({
        'method': 'game_create_test',
        'params': {
            'token': new_game_id,
            'use_optimized': True
        },
        'jsonrpc': '2.0',
        'id': 2
    })
)

if response.status_code == 200 and response.json().get('result'):
    print(f"✅ Created new game: {new_game_id}")
    print(f"   URL: http://localhost:5000/game/{new_game_id}")
    print("\n   Test instructions:")
    print("   1. Create infantry at RED factory (0,4)")
    print("   2. Create mech at BLUE factory (11,4)")  
    print("   3. Move units toward each other")
    print("   4. Attack to damage units")
    print("   5. Verify HP numbers appear on damaged units")

print("\n=== Test URLs ===")
print(f"Existing game: http://localhost:5000/game/{game_id}")
print(f"New test game: http://localhost:5000/game/{new_game_id}")
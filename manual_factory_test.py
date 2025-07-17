#!/usr/bin/env python3
"""
Manual test for factory clicks
"""

import requests
import uuid

# Create a test game
token = str(uuid.uuid4())[:8]
print(f"Creating test game with token: {token}")

response = requests.post('http://localhost:5000/api', json={
    'jsonrpc': '2.0',
    'method': 'game_create_test',
    'params': {'token': token},
    'id': 1
})

result = response.json()
print(f"API Response: {result}")

if 'result' in result:
    print(f"\nGame created successfully!")
    print(f"Visit: http://localhost:5000/game/{token}")
    print(f"\nTo test factory clicks:")
    print(f"1. Open browser console (F12)")
    print(f"2. Click on the RED factory at position (0,4)")
    print(f"3. Look for these messages in console:")
    print(f"   - '🖱️ Click at tile (0, 4)'")
    print(f"   - '🏭 Factory clicked!'")
    print(f"   - '✅ Unit creation modal opened!'")
    print(f"\n4. If modal doesn't appear, run in console:")
    print(f"   checkGameState()")
    print(f"   debugFactoryClick()")
    print(f"   testFactoryClick()")
else:
    print(f"Error creating game: {result.get('error', 'Unknown error')}")
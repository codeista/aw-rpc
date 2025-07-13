#!/usr/bin/env python3
"""
Create a test game with Black Boat ready to use
"""

import requests
import json

def rpc(method, params):
    payload = {'jsonrpc': '2.0', 'method': method, 'params': params, 'id': 1}
    r = requests.post('http://localhost:5000/api', json=payload)
    result = r.json()
    if 'error' in result:
        return {'error': result['error']}
    return result.get('result', {})

# Create game
game_id = 'blackboatgame'
print('Creating game with Black Boat test...')
rpc('game_create', {'token': game_id})

# Instructions for proper Black Boat movement
print(f"""
✅ Game created: {game_id}

📝 Instructions for Black Boat movement:

1. Go to: http://localhost:5000/{game_id}

2. End the first turn to get funds:
   - Click "End Turn" button
   - Blue will auto-end turn
   - You'll gain 1000 funds per property owned

3. After a few turns, you'll have enough funds (7500) for a Black Boat

4. Create a Black Boat:
   - Click on the RED PORT (top-left at 0,0)
   - Select "BLACKBOAT" from the menu
   - The Black Boat will appear but CANNOT MOVE YET

5. Enable movement:
   - End your turn again
   - After Blue's turn, your Black Boat can move!

6. Test repair:
   - Create an Infantry near the port
   - Have an enemy damage it
   - Select the Black Boat
   - Right-click the damaged Infantry
   - Choose "Repair Unit (2 HP)" from context menu

💡 Key Points:
- Units CANNOT move on their creation turn (standard AW rule)
- Black Boats can only be created on ports
- Repair costs 10% of unit cost per HP (max 2 HP)
- Only adjacent friendly units can be repaired

Alternative: Use the test interface at http://localhost:5000/test_interface
""")

# Show initial state
board = rpc('game_board', {'token': game_id})
print(f"\nInitial game state:")
print(f"- RED funds: {board.get('red_funds', 0)}")
print(f"- BLUE funds: {board.get('blue_funds', 0)}")
print(f"- Current turn: {board.get('current_turn', 'Unknown')}")
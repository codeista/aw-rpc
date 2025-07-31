#!/usr/bin/env python3
"""Check fund serialization issue"""

import sys
sys.path.insert(0, '/home/box/Documents/aw-rpc')

from game_board_v2 import GameBoardV2
from player_manager import PlayerManager, Player
from army import Army

# Create player manager with test players
pm = PlayerManager()
pm.add_player(Player(0, "Test 1", "Red", Army.RED))
pm.add_player(Player(1, "Test 2", "Blue", Army.BLUE))

# Create board
board = GameBoardV2(12, 10)
board.initialize_player_state(pm)

print(f"Initial player_funds: {board.player_funds}")

# Set funds
board.player_funds[0] = 50000
board.player_funds[1] = 50000

print(f"After setting funds: {board.player_funds}")

# Test serialization
import jsons

# Try to serialize
serialized = jsons.dump(board)
print(f"\nSerialized type: {type(serialized)}")

# Check player_funds in serialized data
if isinstance(serialized, dict):
    print(f"Serialized player_funds: {serialized.get('player_funds', 'Not found')}")
    
# Also check the properties
print(f"\nred_funds property: {board.red_funds}")
print(f"blue_funds property: {board.blue_funds}")

# Try setting via properties
board.red_funds = 60000
board.blue_funds = 70000

print(f"\nAfter setting via properties:")
print(f"player_funds: {board.player_funds}")
print(f"red_funds: {board.red_funds}")
print(f"blue_funds: {board.blue_funds}")
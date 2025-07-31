#!/usr/bin/env python3
"""Test board_v2 structure"""

import sys
sys.path.insert(0, '/home/box/Documents/aw-rpc')

from game_factory import GameFactory

# Create game with GameFactory
players = [
    {"name": "Test Player 1", "color": "Red", "sprite_color": "RED"},
    {"name": "Test Player 2", "color": "Blue", "sprite_color": "BLUE"}
]

manager, token = GameFactory.create_game_with_players('test', players)

print(f"Manager type: {type(manager)}")
print(f"Has board_v2: {hasattr(manager, 'board_v2')}")
print(f"Has board: {hasattr(manager, 'board')}")

if hasattr(manager, 'board_v2'):
    print(f"\nboard_v2 type: {type(manager.board_v2)}")
    print(f"board_v2 player_funds: {getattr(manager.board_v2, 'player_funds', 'No player_funds')}")
    
if hasattr(manager, 'board'):
    print(f"\nboard type: {type(manager.board)}")
    print(f"board has player_funds: {hasattr(manager.board, 'player_funds')}")
    print(f"board has red_funds: {hasattr(manager.board, 'red_funds')}")
    
    if hasattr(manager.board, 'player_funds'):
        print(f"board.player_funds: {manager.board.player_funds}")
        
# Test setting funds
print("\n--- Testing fund setting ---")
if hasattr(manager, 'board_v2') and hasattr(manager.board_v2, 'player_funds'):
    print("Setting board_v2.player_funds[0] = 50000")
    manager.board_v2.player_funds[0] = 50000
    print(f"board_v2.player_funds after: {manager.board_v2.player_funds}")
elif hasattr(manager.board, 'player_funds'):
    print("Setting board.player_funds[0] = 50000")
    manager.board.player_funds[0] = 50000
    print(f"board.player_funds after: {manager.board.player_funds}")
    
# Check red_funds/blue_funds
if hasattr(manager.board, 'red_funds'):
    print(f"\nLegacy funds before:")
    print(f"  red_funds: {manager.board.red_funds}")
    print(f"  blue_funds: {manager.board.blue_funds}")
    
    manager.board.red_funds = 60000
    manager.board.blue_funds = 70000
    
    print(f"\nLegacy funds after:")
    print(f"  red_funds: {manager.board.red_funds}")
    print(f"  blue_funds: {manager.board.blue_funds}")
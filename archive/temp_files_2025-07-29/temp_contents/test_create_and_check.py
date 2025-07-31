#!/usr/bin/env python3
"""Test game creation and immediate fund check"""

import sys
sys.path.insert(0, '/home/box/Documents/aw-rpc')

from app import games, game_create_test_rpc, game_board_rpc

# Create test game
token = "test_funds_check"
result = game_create_test_rpc(token)
print(f"Creation result: {result}")

# Check the game directly from memory
if token in games:
    manager = games[token]
    print(f"\nDirect check from games dict:")
    print(f"Manager type: {type(manager)}")
    print(f"Has board_v2: {hasattr(manager, 'board_v2')}")
    
    if hasattr(manager, 'board_v2'):
        print(f"board_v2.player_funds: {manager.board_v2.player_funds}")
        print(f"board.red_funds: {manager.board.red_funds}")
        print(f"board.blue_funds: {manager.board.blue_funds}")
    
# Check via RPC
board_data = game_board_rpc(token)
print(f"\nVia game_board_rpc:")
print(f"player_funds: {board_data.get('player_funds', 'Not found')}")
print(f"red_funds: {board_data.get('red_funds', 'Not found')}")
print(f"blue_funds: {board_data.get('blue_funds', 'Not found')}")

# Try to understand the exact issue
if 'player_funds' in board_data:
    print(f"\nplayer_funds type: {type(board_data['player_funds'])}")
    print(f"player_funds contents: {board_data['player_funds']}")
    for k, v in board_data['player_funds'].items():
        print(f"  Key: {k} (type: {type(k)}), Value: {v} (type: {type(v)})")
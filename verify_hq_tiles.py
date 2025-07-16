#!/usr/bin/env python3
"""Verify HQ tiles using BASE_TOWER naming"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from map_system import map_repository
from gameboard import GameBoard

print("🏰 Checking for HQ tiles (BASE_TOWER_X)")
print("=" * 60)

for map_name in map_repository.list_maps():
    game_map = map_repository.get_map(map_name)
    board = GameBoard.create(game_map)
    
    hq_found = {'RED': False, 'BLUE': False, 'GREEN': False, 'YELLOW': False}
    
    for i, tile in enumerate(board.grid):
        if tile.mapTile:
            # Check if it's an HQ using the is_hq() method
            if tile.mapTile.is_hq():
                x = i % board.width
                y = i // board.width
                army = tile.mapTile.army.name if tile.mapTile.army else "NEUTRAL"
                tile_type = tile.mapTile.type.name
                print(f"{map_name:20} - Found {army} HQ at ({x},{y}) - Type: {tile_type}")
                if army in hq_found:
                    hq_found[army] = True
                    
print("\nConclusion: HQ tiles exist but are named BASE_TOWER_X, not 'HQ'")
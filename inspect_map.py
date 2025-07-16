#!/usr/bin/env python3
"""Inspect map structure"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from map_system import map_repository
from gameboard import GameBoard

# Get test map
test_map = map_repository.get_map('test')
print(f"Map name: {test_map.name}")
print(f"Map size: {test_map.width}x{test_map.height}")
print(f"Total tiles: {len(test_map.tiles)}")

# Create a board to see how properties are distributed
board = GameBoard.create(test_map)
print(f"\nBoard created: {board.width}x{board.height}")
print(f"Total tiles in grid: {len(board.grid)}")

# Count properties
property_types = ['HQ', 'FACTORY', 'CITY', 'AIRPORT', 'PORT']
property_counts = {
    'RED': {},
    'BLUE': {},
    'NEUTRAL': {},
    'Total': {}
}

for i, tile in enumerate(board.grid):
    if tile.mapTile and hasattr(tile.mapTile.type, 'name'):
        tile_type = tile.mapTile.type.name
        if tile_type in property_types:
            army = 'NEUTRAL'
            if tile.mapTile.army:
                army = tile.mapTile.army.name
                
            if army not in property_counts:
                property_counts[army] = {}
                
            property_counts[army][tile_type] = property_counts[army].get(tile_type, 0) + 1
            property_counts['Total'][tile_type] = property_counts['Total'].get(tile_type, 0) + 1

print("\nProperty Distribution:")
for army, props in property_counts.items():
    if props:
        print(f"\n{army}:")
        for prop_type, count in props.items():
            print(f"  {prop_type}: {count}")
            
# Check starting funds
print(f"\nStarting Funds:")
print(f"  RED: {board.red_funds}")
print(f"  BLUE: {board.blue_funds}")

# Count total properties for income calculation
print(f"\nTotal Properties by Army:")
print(f"  RED: {board.total_red_properties} (Income: {board.total_red_properties * 1000}/turn)")
print(f"  BLUE: {board.total_blue_properties} (Income: {board.total_blue_properties * 1000}/turn)")
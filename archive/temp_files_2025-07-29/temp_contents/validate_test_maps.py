#!/usr/bin/env python3
"""Validate the new test maps"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from map_system import Map
from unit import Army

test_maps = [
    'comprehensive_test.txt',
    'combat_test.txt', 
    'transport_test.txt'
]

for map_file in test_maps:
    print(f"\n{'='*50}")
    print(f"Validating: {map_file}")
    print('='*50)
    
    try:
        # Load map
        with open(f'maps_v2/{map_file}', 'r') as f:
            map_data = f.read()
        
        # Parse map
        board = Map.parse(map_data)
        
        print(f"✅ Map loaded successfully")
        print(f"   Size: {board.width}x{board.height}")
        print(f"   Players: {board.numPlayers}")
        
        # Count features
        buildings = {}
        terrain = {}
        
        for y in range(board.height):
            for x in range(board.width):
                tile = board.tile_at(x, y)
                tile_type = tile.type.name
                
                if tile_type not in terrain:
                    terrain[tile_type] = 0
                terrain[tile_type] += 1
                
                if tile_type in ['FACTORY', 'AIRPORT', 'PORT', 'BASE_TOWER_1', 'COM_TOWER', 'LAB', 'MISSILE_SILO']:
                    if tile_type not in buildings:
                        buildings[tile_type] = {'RED': 0, 'BLUE': 0, 'neutral': 0}
                    
                    if tile.army == Army.RED:
                        buildings[tile_type]['RED'] += 1
                    elif tile.army == Army.BLUE:
                        buildings[tile_type]['BLUE'] += 1
                    else:
                        buildings[tile_type]['neutral'] += 1
        
        print("\n   Buildings:")
        for building, counts in sorted(buildings.items()):
            total = sum(counts.values())
            print(f"     {building}: {total} (RED: {counts['RED']}, BLUE: {counts['BLUE']}, neutral: {counts['neutral']})")
        
        print("\n   Terrain types:", len(terrain))
        special_terrain = [t for t in terrain.keys() if t not in ['PLAIN', 'CITY']]
        print(f"   Special terrain: {', '.join(sorted(special_terrain))}")
        
    except Exception as e:
        print(f"❌ Failed to load map: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*50)
print("Map validation complete!")
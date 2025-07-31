#!/usr/bin/env python3
"""Validate the V2 test maps"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from map_parser_v2 import MapParserV2
from map_system import MapType

test_maps = [
    'maps_v2/comprehensive_test.txt',
    'maps_v2/combat_test.txt', 
    'maps_v2/transport_test.txt'
]

for map_file in test_maps:
    print(f"\n{'='*50}")
    print(f"Validating: {map_file}")
    print('='*50)
    
    try:
        # Parse map using V2 parser
        parser = MapParserV2()
        player_manager, tiles = parser.parse_file(map_file)
        
        print(f"✅ Map loaded successfully")
        print(f"   Size: {parser.width}x{parser.height}")
        print(f"   Players: {player_manager.get_player_count()}")
        
        # Show player info
        print("\n   Player Configuration:")
        for i in range(player_manager.get_player_count()):
            player = player_manager.get_player(i)
            print(f"     Player {i}: {player.name} ({player.color}, sprite: {player.sprite_color.value})")
        
        # Count features
        buildings = {}
        terrain = {}
        
        for y, row in enumerate(tiles):
            for x, (tile_type, owner) in enumerate(row):
                tile_name = tile_type.name
                
                if tile_name not in terrain:
                    terrain[tile_name] = 0
                terrain[tile_name] += 1
                
                if tile_type in [MapType.FACTORY, MapType.AIRPORT, MapType.PORT, 
                               MapType.BASE_TOWER_1, MapType.COM_TOWER, MapType.LAB, 
                               MapType.MISSILE_SILO]:
                    if tile_name not in buildings:
                        buildings[tile_name] = {}
                    
                    owner_str = f"Player {owner}" if owner is not None else "neutral"
                    if owner_str not in buildings[tile_name]:
                        buildings[tile_name][owner_str] = 0
                    buildings[tile_name][owner_str] += 1
        
        print("\n   Buildings:")
        for building, owners in sorted(buildings.items()):
            total = sum(owners.values())
            owner_list = ', '.join([f"{owner}: {count}" for owner, count in sorted(owners.items())])
            print(f"     {building}: {total} ({owner_list})")
        
        print("\n   Terrain types:", len(terrain))
        special_terrain = [t for t in terrain.keys() if 'BEACH' not in t and t not in ['PLAIN', 'CITY', 'SEA']]
        print(f"   Special terrain: {', '.join(sorted(special_terrain))}")
        
        # Check for missing features
        missing = []
        if 'COM_TOWER' not in buildings and map_file == 'maps_v2/comprehensive_test.txt':
            missing.append("COM_TOWER")
        if 'LAB' not in buildings and map_file == 'maps_v2/comprehensive_test.txt':
            missing.append("LAB")
        if 'MISSILE_SILO' not in buildings and map_file == 'maps_v2/comprehensive_test.txt':
            missing.append("MISSILE_SILO")
            
        if missing:
            print(f"\n   ⚠️  Missing expected features: {', '.join(missing)}")
        
    except Exception as e:
        print(f"❌ Failed to load map: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*50)
print("Map validation complete!")
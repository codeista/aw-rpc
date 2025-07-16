#!/usr/bin/env python3
"""Check all maps for properties and HQ presence"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from map_system import map_repository
from gameboard import GameBoard

def analyze_map(map_name):
    """Analyze a single map"""
    try:
        game_map = map_repository.get_map(map_name)
        board = GameBoard.create(game_map)
        
        property_types = ['HQ', 'FACTORY', 'CITY', 'AIRPORT', 'PORT']
        has_hq = {'RED': False, 'BLUE': False}
        property_counts = {'RED': 0, 'BLUE': 0, 'NEUTRAL': 0}
        
        for tile in board.grid:
            if tile.mapTile and hasattr(tile.mapTile.type, 'name'):
                tile_type = tile.mapTile.type.name
                if tile_type in property_types:
                    army = 'NEUTRAL'
                    if tile.mapTile.army:
                        army = tile.mapTile.army.name
                        
                    property_counts[army] = property_counts.get(army, 0) + 1
                    
                    if tile_type == 'HQ' and army in has_hq:
                        has_hq[army] = True
                        
        return {
            'name': map_name,
            'size': f"{board.width}x{board.height}",
            'has_red_hq': has_hq['RED'],
            'has_blue_hq': has_hq['BLUE'],
            'red_properties': property_counts.get('RED', 0),
            'blue_properties': property_counts.get('BLUE', 0),
            'neutral_properties': property_counts.get('NEUTRAL', 0),
            'red_income': property_counts.get('RED', 0) * 1000,
            'blue_income': property_counts.get('BLUE', 0) * 1000,
        }
    except Exception as e:
        return {'name': map_name, 'error': str(e)}

# Analyze all maps
print("🗺️ Map Analysis - Property and HQ Check")
print("=" * 80)
print(f"{'Map Name':20} {'Size':8} {'RED HQ':7} {'BLUE HQ':8} {'RED Props':10} {'BLUE Props':11} {'Income'}")
print("-" * 80)

maps = map_repository.list_maps()
maps_with_hq = []
maps_without_hq = []

for map_name in maps:
    info = analyze_map(map_name)
    
    if 'error' in info:
        print(f"{map_name:20} ERROR: {info['error']}")
        continue
        
    print(f"{info['name']:20} {info['size']:8} "
          f"{'✅' if info['has_red_hq'] else '❌':7} "
          f"{'✅' if info['has_blue_hq'] else '❌':8} "
          f"{info['red_properties']:10} "
          f"{info['blue_properties']:11} "
          f"R:{info['red_income']:,}/B:{info['blue_income']:,}")
          
    if info['has_red_hq'] and info['has_blue_hq']:
        maps_with_hq.append(map_name)
    else:
        maps_without_hq.append(map_name)

print("\n" + "=" * 80)
print(f"\n📊 Summary:")
print(f"Total maps: {len(maps)}")
print(f"Maps with HQs: {len(maps_with_hq)} - {', '.join(maps_with_hq) if maps_with_hq else 'None'}")
print(f"Maps without HQs: {len(maps_without_hq)} - {', '.join(maps_without_hq)}")
print("\n⚠️  Maps without HQs cannot support HQ capture victory condition!")
print("💡 Use elimination or property control victory instead.")
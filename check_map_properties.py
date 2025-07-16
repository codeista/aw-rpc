#!/usr/bin/env python3
"""Check properties provided by each map"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from map_system import map_repository, MapType, Army

def analyze_map(map_name):
    """Analyze a map and return property information"""
    try:
        game_map = map_repository.get_map(map_name)
        if not game_map:
            return None
            
        properties = {
            'RED': {'HQ': 0, 'FACTORY': 0, 'CITY': 0, 'AIRPORT': 0, 'PORT': 0, 'total': 0},
            'BLUE': {'HQ': 0, 'FACTORY': 0, 'CITY': 0, 'AIRPORT': 0, 'PORT': 0, 'total': 0},
            'NEUTRAL': {'HQ': 0, 'FACTORY': 0, 'CITY': 0, 'AIRPORT': 0, 'PORT': 0, 'total': 0},
            'GREEN': {'HQ': 0, 'FACTORY': 0, 'CITY': 0, 'AIRPORT': 0, 'PORT': 0, 'total': 0},
            'YELLOW': {'HQ': 0, 'FACTORY': 0, 'CITY': 0, 'AIRPORT': 0, 'PORT': 0, 'total': 0},
        }
        
        # Count properties
        for tile in game_map.tiles:
            if tile.type in [MapType.HQ, MapType.FACTORY, MapType.CITY, 
                            MapType.AIRPORT, MapType.PORT]:
                army_name = tile.army.name if tile.army else 'NEUTRAL'
                prop_type = tile.type.name
                if army_name in properties:
                    properties[army_name][prop_type] += 1
                    properties[army_name]['total'] += 1
                    
        # Also check terrain types
        terrain_counts = {}
        for tile in game_map.tiles:
            terrain_counts[tile.type.name] = terrain_counts.get(tile.type.name, 0) + 1
            
        return {
            'name': game_map.name,
            'size': f"{game_map.width}x{game_map.height}",
            'properties': properties,
            'terrain': terrain_counts,
            'description': game_map.description
        }
    except Exception as e:
        return {'error': str(e)}

def main():
    """Check all available maps"""
    print("🗺️ Advance Wars RPC - Map Property Analysis")
    print("=" * 80)
    
    # Get all available maps
    available_maps = map_repository.list_maps()
    print(f"Found {len(available_maps)} maps: {', '.join(available_maps)}\n")
    
    for map_name in available_maps:
        print(f"\n📍 Map: {map_name}")
        print("-" * 40)
        
        info = analyze_map(map_name)
        if not info:
            print(f"❌ Failed to load map")
            continue
            
        if 'error' in info:
            print(f"❌ Error: {info['error']}")
            continue
            
        print(f"Size: {info['size']}")
        print(f"Description: {info['description']}")
        
        # Show property distribution
        print("\nProperties by Army:")
        for army, props in info['properties'].items():
            if props['total'] > 0:
                print(f"  {army:8} - Total: {props['total']:2} | ", end="")
                details = []
                for prop_type in ['HQ', 'FACTORY', 'CITY', 'AIRPORT', 'PORT']:
                    if props[prop_type] > 0:
                        details.append(f"{prop_type}: {props[prop_type]}")
                print(", ".join(details))
                
        # Show terrain summary
        print("\nTerrain Distribution:")
        terrain_sorted = sorted(info['terrain'].items(), key=lambda x: x[1], reverse=True)
        for terrain, count in terrain_sorted[:8]:  # Show top 8 terrain types
            percentage = (count / (int(info['size'].split('x')[0]) * int(info['size'].split('x')[1]))) * 100
            print(f"  {terrain:12} - {count:3} tiles ({percentage:4.1f}%)")
            
        # Calculate income potential
        print("\nIncome Analysis:")
        for army in ['RED', 'BLUE']:
            if info['properties'][army]['total'] > 0:
                income = info['properties'][army]['total'] * 1000
                print(f"  {army}: {income:,} funds/turn from {info['properties'][army]['total']} properties")
                
    print("\n" + "=" * 80)
    print("Summary:")
    print("- Most maps have 5-6 properties per army for balanced income")
    print("- HQ is always present (1 per army) for victory conditions")
    print("- Factories are the main production facilities")
    print("- Neutral properties provide expansion opportunities")

if __name__ == "__main__":
    main()
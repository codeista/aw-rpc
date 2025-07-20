#!/usr/bin/env python3
"""
Simple tile verification output
"""

import json

def simple_tile_verification():
    # Load mapping
    with open("aw2_mixed_tile_mapping.json", "r") as f:
        mapping = json.load(f)
    
    print("TILE VERIFICATION LIST")
    print("=" * 60)
    print()
    
    # Group by category for easier review
    categories = {
        "TERRAIN": ["PLAIN", "WOOD", "MOUNTAIN"],
        "ROADS": [],
        "PIPES": [],
        "BUILDINGS": ["CITY", "FACTORY", "AIRPORT", "PORT", "HQ"],
        "WATER": ["SEA", "REEF", "SHOAL"],
        "WATER_ANIMATED": [],
        "RIVERS": [],
        "SPECIAL": ["VOLCANO", "RIVER"]
    }
    
    # Sort tiles into categories
    for tile_name in mapping["tiles"]:
        if tile_name.startswith("ROAD_"):
            categories["ROADS"].append(tile_name)
        elif tile_name.startswith("PIPE_"):
            categories["PIPES"].append(tile_name)
        elif tile_name.startswith("WATER_"):
            categories["WATER_ANIMATED"].append(tile_name)
        elif tile_name.startswith("RIVER_"):
            categories["RIVERS"].append(tile_name)
    
    # Print each category
    for cat_name, tile_names in categories.items():
        if not tile_names:
            continue
            
        print(f"\n{cat_name}:")
        print("-" * 40)
        
        for tile_name in sorted(tile_names):
            if tile_name in mapping["tiles"]:
                tile = mapping["tiles"][tile_name]
                print(f"{tile_name:<20} at ({tile['x']:3}, {tile['y']:3}) size {tile['width']}x{tile['height']}")
                
                # Additional info
                if tile.get("animation_frames"):
                    print(f"  └─ Animated: {tile['animation_frames']} frames")
                if tile.get("army_variants"):
                    print(f"  └─ Has army color variants")

if __name__ == "__main__":
    simple_tile_verification()
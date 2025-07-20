#!/usr/bin/env python3
"""
Create a mapping for the new AW2 RGB tileset
Since it has a different layout than the old tileset, we need new coordinates
"""

import json
import os

def create_new_mapping():
    # The new tileset uses 8x8 tiles on a 9px grid
    # Based on the labeled sections we found:
    
    mapping = {
        "metadata": {
            "source": "Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png",
            "base_tile_size": 8,
            "grid_step": 9,
            "render_size": 16,  # Tiles need to be scaled 2x for rendering
            "created": "2025-07-18"
        },
        "tiles": {
            # Based on the tileset labels and visual inspection
            # Plains are yellowish/tan, not green
            "PLAIN": {
                "x": 225,  # This might be a grass tile, need to find yellow plain
                "y": 27,
                "note": "Need to verify - looking for yellow/tan plain tile"
            },
            "WOOD": {
                "x": 234,  # Approximate - need to find forest tiles
                "y": 27,
                "note": "Forest/woods tiles"
            },
            "MOUNTAIN": {
                "x": 243,  # Approximate - need to find mountain tiles
                "y": 27,
                "note": "Mountain tiles"
            },
            "ROAD_HORT": {
                "x": 0,  # Roads are in the left section
                "y": 27,
                "note": "Horizontal road"
            },
            "ROAD_VERT": {
                "x": 9,  # Next tile in grid
                "y": 27,
                "note": "Vertical road"
            },
            "SEA": {
                "x": 0,  # Water section starts around y=140
                "y": 140,
                "note": "Sea/water tile"
            },
            "CITY": {
                "x": 495,  # Cities are often in the buildings section
                "y": 0,
                "note": "Neutral city"
            },
            "FACTORY": {
                "x": 504,  # Next to city
                "y": 0,
                "note": "Neutral factory"
            }
        }
    }
    
    # Save the mapping
    with open("new_tileset_mapping.json", "w") as f:
        json.dump(mapping, f, indent=2)
    
    print("Created new_tileset_mapping.json")
    print("\nThis is a starting point. We need to:")
    print("1. Find the actual yellow/tan PLAIN tiles (not green grass)")
    print("2. Verify all tile positions by visual inspection")
    print("3. Add all missing tile types")
    print("\nThe old coordinate system CANNOT be used with the new tileset!")

if __name__ == "__main__":
    create_new_mapping()
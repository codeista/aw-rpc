#!/usr/bin/env python3
"""
Convert 8x8 based tile mapping to 16x16 equivalent for rendering.
This doubles all coordinates and sizes to match the standard tile size.
"""

import json

def convert_mapping_to_16x16():
    """Convert 8x8 tile mapping to 16x16 scale"""
    
    # Load the 8x8 mapping
    with open('templates/aw2_tileset_corrected_mapping(1).json', 'r') as f:
        mapping_8x8 = json.load(f)
    
    # Create 16x16 version
    mapping_16x16 = {
        "metadata": {
            "source": mapping_8x8["metadata"]["source"],
            "base_tile_size": 16,  # Changed from 8 to 16
            "original_tile_size": 8,
            "scale_factor": 2,
            "created": mapping_8x8["metadata"]["created"],
            "description": "Scaled 2x from 8x8 to 16x16 for standard tile rendering"
        },
        "tiles": {}
    }
    
    # Scale all tile coordinates and sizes by 2
    for tile_name, tile_data in mapping_8x8["tiles"].items():
        mapping_16x16["tiles"][tile_name] = {
            "x": tile_data["x"] * 2,
            "y": tile_data["y"] * 2,
            "width": tile_data["width"] * 2,
            "height": tile_data["height"] * 2,
            "category": tile_data["category"],
            "original_8x8": {
                "x": tile_data["x"],
                "y": tile_data["y"],
                "width": tile_data["width"],
                "height": tile_data["height"]
            }
        }
    
    # Save the 16x16 version
    with open('static/img/aw2_tileset_16x16_mapping.json', 'w') as f:
        json.dump(mapping_16x16, f, indent=2)
    
    print("Conversion complete!")
    print(f"Original 8x8 tiles: {len(mapping_8x8['tiles'])}")
    print(f"Converted 16x16 tiles: {len(mapping_16x16['tiles'])}")
    print("\nExample conversions:")
    for i, (name, tile) in enumerate(mapping_16x16['tiles'].items()):
        if i < 3:  # Show first 3 examples
            orig = tile['original_8x8']
            print(f"  {name}: ({orig['x']},{orig['y']}) {orig['width']}x{orig['height']} → ({tile['x']},{tile['y']}) {tile['width']}x{tile['height']}")
    
    return mapping_16x16

if __name__ == "__main__":
    convert_mapping_to_16x16()
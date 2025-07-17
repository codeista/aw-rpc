#!/usr/bin/env python3
"""Debug tileset extraction to see what's going wrong"""

import json
from PIL import Image
import os

def debug_extraction():
    # Load tile map
    with open('templates/tile_sprite_map.json', 'r') as f:
        tile_map = json.load(f)
    
    # Load source image
    source_path = 'static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png'
    source_image = Image.open(source_path)
    print(f"Source image size: {source_image.size}")
    print(f"Source image mode: {source_image.mode}")
    
    center_x = tile_map['sprite_sheet']['center_x']
    center_y = tile_map['sprite_sheet']['center_y']
    print(f"Center point: ({center_x}, {center_y})")
    
    # Test extract a few tiles
    test_tiles = ['PLAIN', 'WOOD', 'MOUNTAIN', 'CITY']
    
    for tile_name in test_tiles:
        if tile_name == 'CITY':
            # Test city with RED variant
            tile_data = tile_map['tiles'][tile_name]['variants']['RED']
        else:
            tile_data = tile_map['tiles'][tile_name]
        
        x = int(center_x + tile_data['x'])
        y = int(center_y + tile_data['y'])
        w = tile_data['width']
        h = tile_data['height']
        
        print(f"\n{tile_name}:")
        print(f"  Offset: ({tile_data['x']}, {tile_data['y']})")
        print(f"  Calculated position: ({x}, {y})")
        print(f"  Size: {w}x{h}")
        
        # Check if coordinates are valid
        if x < 0 or y < 0 or x + w > source_image.width or y + h > source_image.height:
            print(f"  ❌ INVALID COORDINATES! Out of bounds")
            print(f"     Image bounds: 0,0 to {source_image.width},{source_image.height}")
        else:
            # Extract and save test tile
            tile_img = source_image.crop((x, y, x + w, y + h))
            tile_img.save(f'test_tile_{tile_name}.png')
            print(f"  ✅ Extracted and saved as test_tile_{tile_name}.png")
            
            # Check if tile is empty
            pixels = list(tile_img.getdata())
            non_transparent = sum(1 for p in pixels if (len(p) == 4 and p[3] > 0) or (len(p) == 3 and p != (0,0,0)))
            if non_transparent == 0:
                print(f"  ⚠️  WARNING: Tile appears to be empty/transparent!")

if __name__ == '__main__':
    debug_extraction()
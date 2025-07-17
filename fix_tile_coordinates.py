#!/usr/bin/env python3
"""Fix tile coordinates in the sprite map by converting legacy offsets"""

import json

def fix_coordinates():
    # Load the tile map
    with open('templates/tile_sprite_map.json', 'r') as f:
        tile_map = json.load(f)
    
    # The center point is correct
    center_x = tile_map['sprite_sheet']['center_x']  # 222.5
    center_y = tile_map['sprite_sheet']['center_y']  # 581.5
    
    print(f"Center: ({center_x}, {center_y})")
    
    # Fix all tiles with negative y coordinates
    for tile_name, tile_data in tile_map['tiles'].items():
        if 'variants' in tile_data:
            for variant_name, variant_data in tile_data['variants'].items():
                old_y = variant_data['y']
                if old_y < 0:
                    # Convert negative offset to positive
                    # In legacy: y = center_y + offset (where offset is negative)
                    # For sprite map: we want the actual position relative to center
                    # So if legacy says y = y - 766, that means offset = -766
                    # But we want to store it as positive offset from center
                    new_y = abs(old_y)
                    variant_data['y'] = new_y
                    print(f"Fixed {tile_name}_{variant_name}: y {old_y} -> {new_y}")
        else:
            if 'y' in tile_data and tile_data['y'] < 0:
                old_y = tile_data['y']
                new_y = abs(old_y)
                tile_data['y'] = new_y
                print(f"Fixed {tile_name}: y {old_y} -> {new_y}")
    
    # Save the fixed map
    with open('templates/tile_sprite_map_fixed.json', 'w') as f:
        json.dump(tile_map, f, indent=2)
    
    print("\nSaved fixed tile map to tile_sprite_map_fixed.json")

if __name__ == '__main__':
    fix_coordinates()
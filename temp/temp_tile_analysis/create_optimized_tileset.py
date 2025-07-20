#!/usr/bin/env python3
"""
Create an optimized tileset for Advance Wars RPC
Repacks tiles more efficiently and generates a new sprite map
"""

import json
import os
from PIL import Image
import math

def load_tile_map():
    """Load the tile sprite map configuration"""
    with open('templates/tile_sprite_map.json', 'r') as f:
        return json.load(f)

def extract_tiles(source_image, tile_map):
    """Extract all tiles from the source image"""
    tiles = {}
    
    center_x = tile_map['sprite_sheet']['center_x']
    center_y = tile_map['sprite_sheet']['center_y']
    
    for tile_name, tile_data in tile_map['tiles'].items():
        if 'variants' in tile_data:
            # Handle tiles with army variants
            for variant_name, variant_data in tile_data['variants'].items():
                key = f"{tile_name}_{variant_name}"
                x = int(center_x + variant_data['x'])
                y = int(center_y + variant_data['y'])
                w = variant_data['width']
                h = variant_data['height']
                
                # Validate bounds
                if x < 0 or y < 0 or x + w > source_image.width or y + h > source_image.height:
                    print(f"  Warning: {tile_name}_{variant_name} out of bounds: ({x},{y},{w},{h})")
                    continue
                
                # Extract tile
                tile_img = source_image.crop((x, y, x + w, y + h))
                tiles[key] = {
                    'image': tile_img,
                    'width': w,
                    'height': h,
                    'type': tile_name,
                    'variant': variant_name
                }
        else:
            # Handle simple tiles
            x = int(center_x + tile_data['x'])
            y = int(center_y + tile_data['y'])
            w = tile_data['width']
            h = tile_data['height']
            
            # Validate bounds
            if x < 0 or y < 0 or x + w > source_image.width or y + h > source_image.height:
                print(f"  Warning: {tile_name} out of bounds: ({x},{y},{w},{h})")
                continue
            
            # Extract tile
            tile_img = source_image.crop((x, y, x + w, y + h))
            tiles[tile_name] = {
                'image': tile_img,
                'width': w,
                'height': h,
                'type': tile_name,
                'variant': None
            }
    
    return tiles

def pack_tiles(tiles, padding=1):
    """Pack tiles efficiently into a new sprite sheet"""
    # Sort tiles by height (tallest first) for better packing
    sorted_tiles = sorted(tiles.items(), key=lambda x: (x[1]['height'], x[1]['width']), reverse=True)
    
    # Calculate approximate dimensions needed
    total_area = sum(t['width'] * t['height'] for _, t in sorted_tiles)
    sheet_size = int(math.sqrt(total_area) * 1.2)  # Add 20% buffer
    
    # Round up to nearest power of 2 for better GPU performance
    sheet_size = 2 ** math.ceil(math.log2(sheet_size))
    
    # Create new sprite sheet
    sprite_sheet = Image.new('RGBA', (sheet_size, sheet_size), (0, 0, 0, 0))
    
    # Simple packing algorithm (row-based)
    placements = {}
    current_x = padding
    current_y = padding
    row_height = 0
    
    for tile_name, tile_data in sorted_tiles:
        tile_img = tile_data['image']
        w = tile_data['width']
        h = tile_data['height']
        
        # Check if tile fits in current row
        if current_x + w + padding > sheet_size:
            # Move to next row
            current_x = padding
            current_y += row_height + padding
            row_height = 0
        
        # Place tile
        sprite_sheet.paste(tile_img, (current_x, current_y))
        
        # Record placement
        placements[tile_name] = {
            'x': current_x,
            'y': current_y,
            'width': w,
            'height': h,
            'type': tile_data['type'],
            'variant': tile_data['variant']
        }
        
        # Update position
        current_x += w + padding
        row_height = max(row_height, h)
    
    # Trim unused space
    max_x = max(p['x'] + p['width'] for p in placements.values()) + padding
    max_y = max(p['y'] + p['height'] for p in placements.values()) + padding
    
    sprite_sheet = sprite_sheet.crop((0, 0, max_x, max_y))
    
    return sprite_sheet, placements

def create_optimized_map(placements):
    """Create optimized tile map JSON"""
    optimized_map = {
        'sprite_sheet': {
            'version': '2.0',
            'optimized': True
        },
        'tiles': {}
    }
    
    # Reorganize placements back into original structure
    for placement_name, placement_data in placements.items():
        tile_type = placement_data['type']
        variant = placement_data['variant']
        
        tile_info = {
            'x': placement_data['x'],
            'y': placement_data['y'],
            'width': placement_data['width'],
            'height': placement_data['height']
        }
        
        if variant:
            # This is a variant tile
            if tile_type not in optimized_map['tiles']:
                optimized_map['tiles'][tile_type] = {'variants': {}}
            optimized_map['tiles'][tile_type]['variants'][variant] = tile_info
        else:
            # This is a simple tile
            optimized_map['tiles'][tile_type] = tile_info
    
    return optimized_map

def main():
    print("Creating optimized tileset...")
    
    # Load original tile map
    tile_map = load_tile_map()
    
    # Process each tileset
    tilesets = [
        ('Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png', 'optimized_tileset_transparent.png'),
        ('Advance_Wars_Dual_Strike_Tileset_Normal.png', 'optimized_tileset_normal.png')
    ]
    
    for source_file, output_file in tilesets:
        source_path = f'static/img/{source_file}'
        
        if not os.path.exists(source_path):
            print(f"Skipping {source_file} - not found")
            continue
        
        print(f"\nProcessing {source_file}...")
        
        # Load source image
        source_image = Image.open(source_path)
        print(f"Original mode: {source_image.mode}")
        
        # For palette mode images, we need to handle transparency correctly
        if source_image.mode == 'P':
            # Check if image has transparency
            if 'transparency' in source_image.info:
                # Convert palette to RGBA preserving transparency
                source_image = source_image.convert('RGBA')
            else:
                # No transparency info, just convert
                source_image = source_image.convert('RGBA')
        elif source_image.mode != 'RGBA':
            source_image = source_image.convert('RGBA')
            
        print(f"Converted to: {source_image.mode}, size: {source_image.size}")
        
        # Extract tiles
        tiles = extract_tiles(source_image, tile_map)
        print(f"Extracted {len(tiles)} tiles")
        
        # Pack tiles
        sprite_sheet, placements = pack_tiles(tiles)
        print(f"Optimized size: {sprite_sheet.size}")
        
        # Save optimized sprite sheet
        output_path = f'static/img/{output_file}'
        sprite_sheet.save(output_path, 'PNG', optimize=True)
        
        # Calculate size reduction
        original_size = os.path.getsize(source_path)
        optimized_size = os.path.getsize(output_path)
        reduction = (1 - optimized_size / original_size) * 100
        
        print(f"Original: {original_size:,} bytes")
        print(f"Optimized: {optimized_size:,} bytes")
        print(f"Reduction: {reduction:.1f}%")
        
        # Create optimized map for the transparent version (our default)
        if 'transparent' in output_file:
            optimized_map = create_optimized_map(placements)
            optimized_map['sprite_sheet']['width'] = sprite_sheet.width
            optimized_map['sprite_sheet']['height'] = sprite_sheet.height
            optimized_map['sprite_sheet']['file'] = output_file
            
            # Save optimized map
            with open('static/img/optimized_tileset_map.json', 'w') as f:
                json.dump(optimized_map, f, indent=2)
            print(f"\nSaved optimized tile map")

if __name__ == '__main__':
    main()
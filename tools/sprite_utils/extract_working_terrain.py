#!/usr/bin/env python3
"""
Extract only the terrain tiles that have positive coordinates and work
"""

from PIL import Image
import os
import zipfile

def extract_working_terrain_tiles():
    """Extract only terrain tiles that have positive coordinates"""
    
    tileset_path = "/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png"
    tileset = Image.open(tileset_path)
    
    # Base coordinates
    base_x = 445/2 - 16/2  # 214.5
    base_y = 1163/2 - 16/2  # 573.5
    
    # Only include tiles that had positive coordinates in our previous test
    working_tiles = [
        ('PLAIN', -8, -64, False),
        ('MOUNTAIN', -25, -39, True),  # 16x32
        ('SEA', -76, -94, False),
        ('REEF', -195, -145, False),
        ('ROAD_HORT', -42, -64, False),
        ('ROAD_VERT', -59, -64, False),
        ('ROAD_NW', -42, -13, False),
        ('ROAD_NE', -76, -13, False),
        ('ROAD_SE', -76, -47, False),
        ('ROAD_SW', -42, -47, False),
        ('HBridge', -76, -64, False),
        ('VBridge', -94, -64, False),
        ('BEACH_E', -214, -321, False),
        ('PIPE_VERT', -212, -30, False),
        ('PIPE_HORT', -195, -30, False),
        ('PIPE_END_N', -178, -30, False),
        ('PIPE_END_S', -178, -47, False),
        ('PIPE_END_W', -144, -64, False),
        ('PIPE_END_E', -161, -64, False),
    ]
    
    print("=== EXTRACTING WORKING TERRAIN TILES ===\n")
    print(f"Tileset: {tileset.width}x{tileset.height}")
    print(f"Extracting {len(working_tiles)} confirmed working tiles\n")
    
    os.makedirs("temp/working_terrain", exist_ok=True)
    
    extracted_tiles = []
    
    for terrain_name, x_offset, y_offset, is_double in working_tiles:
        final_x = int(base_x + x_offset)
        final_y = int(base_y + y_offset)
        height = 32 if is_double else 16
        
        print(f"{terrain_name}: ({final_x}, {final_y}) size 16x{height}")
        
        # Extract tile
        tile = tileset.crop((final_x, final_y, final_x + 16, final_y + height))
        
        # Save
        filename = f"{terrain_name}.png"
        filepath = f"temp/working_terrain/{filename}"
        tile.save(filepath)
        
        extracted_tiles.append({
            "name": terrain_name,
            "filename": filename,
            "x": final_x,
            "y": final_y,
            "width": 16,
            "height": height,
            "double_height": is_double
        })
        
        print(f"  ✓ Saved as {filename}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Extracted {len(extracted_tiles)} working terrain tiles")
    print(f"Saved to: temp/working_terrain/")
    
    # Create a combined sprite batch with units + working terrain
    print(f"\n=== CREATING COMBINED SPRITE BATCH ===")
    
    # We need to combine:
    # 1. Unit sprites (250 sprites)
    # 2. Working terrain tiles (19 tiles)
    
    # First, copy unit sprites
    unit_sprites = []
    for i in range(250):
        unit_file = f"temp/sprites_for_upscaling/unit_{i:04d}.png"
        if os.path.exists(unit_file):
            unit_sprites.append(unit_file)
    
    print(f"Found {len(unit_sprites)} unit sprites")
    
    # Create combined batch
    with zipfile.ZipFile("temp/combined_sprites_batch.zip", 'w') as zf:
        # Add unit sprites
        for sprite_path in unit_sprites:
            filename = os.path.basename(sprite_path)
            zf.write(sprite_path, f"units/{filename}")
        
        # Add terrain sprites
        for tile_info in extracted_tiles:
            sprite_path = f"temp/working_terrain/{tile_info['filename']}"
            zf.write(sprite_path, f"terrain/{tile_info['filename']}")
    
    print(f"\nCombined batch created: temp/combined_sprites_batch.zip")
    print(f"Contains: {len(unit_sprites)} units + {len(extracted_tiles)} terrain tiles")
    
    # Create test batch with just a few of each
    with zipfile.ZipFile("temp/test_combined_batch.zip", 'w') as zf:
        # Add first 10 unit sprites
        for i in range(min(10, len(unit_sprites))):
            sprite_path = unit_sprites[i]
            filename = os.path.basename(sprite_path)
            zf.write(sprite_path, f"units/{filename}")
        
        # Add first 5 terrain tiles
        for i in range(min(5, len(extracted_tiles))):
            tile_info = extracted_tiles[i]
            sprite_path = f"temp/working_terrain/{tile_info['filename']}"
            zf.write(sprite_path, f"terrain/{tile_info['filename']}")
    
    print(f"Test batch created: temp/test_combined_batch.zip")
    print(f"Contains: 10 units + 5 terrain tiles for testing")
    
    return extracted_tiles

def main():
    extract_working_terrain_tiles()
    
    print("\n✅ READY FOR UPSCALING!")
    print("\nNext steps:")
    print("1. Upload temp/test_combined_batch.zip to waifu2x to test quality")
    print("2. If good, upload temp/combined_sprites_batch.zip for full batch")
    print("3. Download results and reassemble")

if __name__ == "__main__":
    main()
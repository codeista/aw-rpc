#!/usr/bin/env python3
"""
Extract sprites from original tilesets with correct sizes
- Most tiles: 16x16
- Special buildings/terrain: 16x32 (2x height)
"""

from PIL import Image
import os
import json
import zipfile

# Tiles that are 2x height (16x32) based on render_legacy.js
DOUBLE_HEIGHT_TILES = [
    'HQ', 'MOUNTAIN', 'CITY', 'FACTORY', 'AIRPORT', 'PORT',
    'BASE_TOWER_0', 'BASE_TOWER_1', 'BASE_TOWER_2', 'BASE_TOWER_3', 'BASE_TOWER_4',
    'LAB', 'COM_TOWER', 'MISSILE_SILO', 'EMPTY_SILO'
]

def extract_unit_sprites(output_dir):
    """Extract 250 unit sprites from complete sheet - all 16x16"""
    
    sheet_path = "/home/box/Documents/aw-rpc/static/img/units_sprite_sheet_complete.png"
    sheet = Image.open(sheet_path)
    
    print(f"Extracting unit sprites from units_sprite_sheet_complete.png")
    print(f"Sheet size: {sheet.width}x{sheet.height} (10x25 grid)")
    print("All unit sprites are 16x16 pixels")
    
    sprites = []
    sprite_count = 0
    
    # Extract all 16x16 sprites
    for y in range(0, sheet.height, 16):
        for x in range(0, sheet.width, 16):
            sprite = sheet.crop((x, y, x + 16, y + 16))
            
            # Skip empty sprites
            if sprite.getbbox() is None:
                continue
            
            filename = f"unit_{sprite_count:04d}.png"
            filepath = os.path.join(output_dir, filename)
            sprite.save(filepath)
            
            sprites.append({
                "id": sprite_count,
                "filename": filename,
                "type": "unit",
                "size": "16x16",
                "original_x": x,
                "original_y": y,
                "sheet": "units_sprite_sheet_complete.png"
            })
            
            sprite_count += 1
    
    print(f"Extracted {sprite_count} unit sprites (all 16x16)")
    return sprites

def extract_terrain_tiles(output_dir):
    """Extract terrain tiles from original AWDS tileset"""
    
    tileset_path = "/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png"
    sheet = Image.open(tileset_path)
    
    print(f"\nExtracting terrain tiles from ORIGINAL AWDS tileset")
    print(f"Sheet size: {sheet.width}x{sheet.height}")
    print("Most tiles are 16x16, some buildings are 16x32")
    
    sprites = []
    sprite_count = 0
    tiles_16x16 = 0
    tiles_16x32 = 0
    
    # The tileset is 445x1163 - not perfectly divisible by 16
    # We'll extract what we can in 16x16 chunks
    
    # For now, extract everything as 16x16 and note which might be double height
    for y in range(0, sheet.height - 15, 16):  # Stop 16 pixels from bottom
        for x in range(0, sheet.width - 15, 16):  # Stop 16 pixels from right
            # Extract 16x16 tile
            tile = sheet.crop((x, y, x + 16, y + 16))
            
            # Skip empty tiles
            if tile.getbbox() is None:
                continue
            
            # Check if this could be a double-height tile
            # (This is approximate - in real game it's determined by tile type)
            is_double = False
            if y + 32 <= sheet.height:
                bottom_tile = sheet.crop((x, y + 16, x + 16, y + 32))
                # If bottom tile has content and looks like continuation
                if bottom_tile.getbbox() is not None:
                    # This is a heuristic - might need refinement
                    is_double = True
            
            size = "16x32" if is_double else "16x16"
            
            if is_double:
                # Extract 16x32 tile
                tile = sheet.crop((x, y, x + 16, y + 32))
                tiles_16x32 += 1
            else:
                tiles_16x16 += 1
            
            filename = f"terrain_{sprite_count:04d}_{size.replace('x', '_')}.png"
            filepath = os.path.join(output_dir, filename)
            tile.save(filepath)
            
            sprites.append({
                "id": sprite_count,
                "filename": filename,
                "type": "terrain",
                "size": size,
                "original_x": x,
                "original_y": y,
                "sheet": "Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png"
            })
            
            sprite_count += 1
    
    print(f"Extracted {sprite_count} terrain tiles")
    print(f"  - 16x16 tiles: {tiles_16x16}")
    print(f"  - 16x32 tiles: {tiles_16x32}")
    return sprites

def create_verification_preview(sprites, output_dir):
    """Create preview images for verification"""
    
    print("\nCreating verification previews...")
    
    # Separate by type and size
    units = [s for s in sprites if s["type"] == "unit"]
    terrain_16x16 = [s for s in sprites if s["type"] == "terrain" and s["size"] == "16x16"]
    terrain_16x32 = [s for s in sprites if s["type"] == "terrain" and s["size"] == "16x32"]
    
    # Units preview
    if units:
        cols = 25
        rows = (len(units) + cols - 1) // cols
        preview = Image.new('RGBA', (cols * 20, rows * 20 + 30), (200, 200, 200, 255))
        
        for i, sprite_info in enumerate(units[:250]):
            sprite = Image.open(os.path.join(output_dir, sprite_info["filename"]))
            x = (i % cols) * 20 + 2
            y = (i // cols) * 20 + 20
            preview.paste(sprite, (x, y))
        
        preview.save("temp/verify_units.png")
        print("  - Created temp/verify_units.png")
    
    # Terrain 16x16 preview (first 400)
    if terrain_16x16:
        cols = 20
        rows = 20
        preview = Image.new('RGBA', (cols * 20, rows * 20 + 30), (200, 200, 200, 255))
        
        for i, sprite_info in enumerate(terrain_16x16[:400]):
            sprite = Image.open(os.path.join(output_dir, sprite_info["filename"]))
            x = (i % cols) * 20 + 2
            y = (i // cols) * 20 + 20
            preview.paste(sprite, (x, y))
        
        preview.save("temp/verify_terrain_16x16.png")
        print("  - Created temp/verify_terrain_16x16.png")
    
    # Terrain 16x32 preview
    if terrain_16x32:
        cols = 15
        rows = min(10, (len(terrain_16x32) + cols - 1) // cols)
        preview = Image.new('RGBA', (cols * 20, rows * 40 + 30), (200, 200, 200, 255))
        
        for i, sprite_info in enumerate(terrain_16x32[:150]):
            sprite = Image.open(os.path.join(output_dir, sprite_info["filename"]))
            sprite_scaled = sprite.resize((16, 32), Image.NEAREST)
            x = (i % cols) * 20 + 2
            y = (i // cols) * 40 + 20
            preview.paste(sprite_scaled, (x, y))
        
        preview.save("temp/verify_terrain_16x32.png")
        print("  - Created temp/verify_terrain_16x32.png")

def create_batches(sprites, output_dir):
    """Create ZIP batches for upload"""
    
    print("\n=== Creating upload batches ===")
    
    # Create test batch first
    test_sprites = sprites[:30]  # Mix of different types
    with zipfile.ZipFile("temp/test_batch_mixed.zip", 'w') as zf:
        for sprite_info in test_sprites:
            sprite_path = os.path.join(output_dir, sprite_info["filename"])
            zf.write(sprite_path, sprite_info["filename"])
    print(f"Test batch: 30 sprites → temp/test_batch_mixed.zip")
    
    # Full batches
    batch_size = 500
    batch_num = 1
    
    for i in range(0, len(sprites), batch_size):
        batch = sprites[i:i+batch_size]
        zip_path = f"temp/batch_{batch_num}_mixed.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for sprite_info in batch:
                sprite_path = os.path.join(output_dir, sprite_info["filename"])
                zf.write(sprite_path, sprite_info["filename"])
        
        units_in_batch = sum(1 for s in batch if s["type"] == "unit")
        terrain_in_batch = sum(1 for s in batch if s["type"] == "terrain")
        
        print(f"Batch {batch_num}: {len(batch)} sprites ({units_in_batch} units, {terrain_in_batch} terrain) → {zip_path}")
        batch_num += 1

def main():
    output_dir = "temp/sprites_for_upscaling"
    os.makedirs(output_dir, exist_ok=True)
    
    print("=== EXTRACTING SPRITES WITH CORRECT SIZES ===\n")
    
    all_sprites = []
    
    # 1. Extract unit sprites (all 16x16)
    unit_sprites = extract_unit_sprites(output_dir)
    all_sprites.extend(unit_sprites)
    
    # 2. Extract terrain tiles (mix of 16x16 and 16x32)
    terrain_sprites = extract_terrain_tiles(output_dir)
    all_sprites.extend(terrain_sprites)
    
    # Save mapping
    with open(os.path.join(output_dir, "sprite_mapping.json"), "w") as f:
        json.dump({
            "total_sprites": len(all_sprites),
            "unit_sprites": len(unit_sprites),
            "terrain_sprites": len(terrain_sprites),
            "sprites": all_sprites
        }, f, indent=2)
    
    # Create verification previews
    create_verification_preview(all_sprites, output_dir)
    
    # Create upload batches
    create_batches(all_sprites, output_dir)
    
    print(f"\n=== EXTRACTION COMPLETE ===")
    print(f"Total sprites: {len(all_sprites)}")
    print(f"  - Units: {len(unit_sprites)} (all 16x16)")
    print(f"  - Terrain: {len(terrain_sprites)} (mixed sizes)")
    print(f"\nPlease review verification images before uploading!")

if __name__ == "__main__":
    main()
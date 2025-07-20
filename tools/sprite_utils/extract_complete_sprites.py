#!/usr/bin/env python3
"""
Extract sprites from both unit sheet and terrain tileset
"""

from PIL import Image
import os
import json
import zipfile

def extract_unit_sprites(output_dir):
    """Extract 250 unit sprites from complete sheet"""
    
    sheet_path = "/home/box/Documents/aw-rpc/static/img/units_sprite_sheet_complete.png"
    sheet = Image.open(sheet_path)
    
    print(f"Extracting unit sprites from units_sprite_sheet_complete.png")
    print(f"Sheet size: {sheet.width}x{sheet.height} (10x25 grid)")
    
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
                "original_x": x,
                "original_y": y,
                "sheet": "units_sprite_sheet_complete.png"
            })
            
            sprite_count += 1
    
    print(f"Extracted {sprite_count} unit sprites")
    return sprites

def extract_terrain_tiles(output_dir):
    """Extract terrain tiles from AWDS tileset"""
    
    # Use the tileset that render_legacy.js uses
    sheet_path = "/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal.png"
    sheet = Image.open(sheet_path)
    
    print(f"\nExtracting terrain tiles from AWDS tileset")
    print(f"Sheet size: {sheet.width}x{sheet.height}")
    
    sprites = []
    sprite_count = 0
    
    # Extract all 16x16 tiles
    for y in range(0, sheet.height, 16):
        for x in range(0, sheet.width, 16):
            if x + 16 > sheet.width or y + 16 > sheet.height:
                continue
                
            tile = sheet.crop((x, y, x + 16, y + 16))
            
            # Skip empty tiles
            if tile.getbbox() is None:
                continue
            
            filename = f"terrain_{sprite_count:04d}.png"
            filepath = os.path.join(output_dir, filename)
            tile.save(filepath)
            
            sprites.append({
                "id": sprite_count,
                "filename": filename,
                "type": "terrain",
                "original_x": x,
                "original_y": y,
                "sheet": "Advance_Wars_Dual_Strike_Tileset_Normal.png"
            })
            
            sprite_count += 1
    
    print(f"Extracted {sprite_count} terrain tiles")
    return sprites

def create_preview(sprites, output_dir):
    """Create a preview of extracted sprites"""
    
    # Separate by type
    units = [s for s in sprites if s["type"] == "unit"][:50]
    terrain = [s for s in sprites if s["type"] == "terrain"][:50]
    
    # Create preview image
    preview = Image.new('RGBA', (600, 400), (64, 64, 64, 255))
    
    # Draw units
    print("\nCreating preview...")
    for i, sprite_info in enumerate(units):
        sprite = Image.open(os.path.join(output_dir, sprite_info["filename"]))
        x = (i % 25) * 20 + 10
        y = (i // 25) * 20 + 10
        preview.paste(sprite, (x, y), sprite)
    
    # Draw terrain
    for i, sprite_info in enumerate(terrain):
        sprite = Image.open(os.path.join(output_dir, sprite_info["filename"]))
        x = (i % 25) * 20 + 10
        y = (i // 25) * 20 + 100
        preview.paste(sprite, (x, y), sprite)
    
    preview.save("temp/complete_sprites_preview.png")
    print("Preview saved to temp/complete_sprites_preview.png")

def create_batches(sprites, output_dir):
    """Create ZIP batches for upload"""
    
    print("\n=== Creating upload batches ===")
    
    batch_size = 500
    batch_num = 1
    
    for i in range(0, len(sprites), batch_size):
        batch = sprites[i:i+batch_size]
        zip_path = f"temp/complete_batch_{batch_num}.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for sprite_info in batch:
                sprite_path = os.path.join(output_dir, sprite_info["filename"])
                zf.write(sprite_path, sprite_info["filename"])
        
        print(f"Batch {batch_num}: {len(batch)} sprites → {zip_path}")
        batch_num += 1
    
    # Create test batch with first 20 sprites
    test_batch = sprites[:20]
    with zipfile.ZipFile("temp/complete_test_batch.zip", 'w') as zf:
        for sprite_info in test_batch:
            sprite_path = os.path.join(output_dir, sprite_info["filename"])
            zf.write(sprite_path, sprite_info["filename"])
    
    print(f"\nTest batch: 20 sprites → temp/complete_test_batch.zip")

def main():
    output_dir = "temp/complete_sprites_to_upscale"
    os.makedirs(output_dir, exist_ok=True)
    
    print("=== EXTRACTING COMPLETE SPRITE SET ===\n")
    
    # Extract both units and terrain
    all_sprites = []
    
    # 1. Extract unit sprites
    unit_sprites = extract_unit_sprites(output_dir)
    all_sprites.extend(unit_sprites)
    
    # 2. Extract terrain tiles
    terrain_sprites = extract_terrain_tiles(output_dir)
    all_sprites.extend(terrain_sprites)
    
    # Save mapping
    with open(os.path.join(output_dir, "complete_sprite_mapping.json"), "w") as f:
        json.dump({
            "total_sprites": len(all_sprites),
            "unit_sprites": len(unit_sprites),
            "terrain_sprites": len(terrain_sprites),
            "sprites": all_sprites
        }, f, indent=2)
    
    # Create preview
    create_preview(all_sprites, output_dir)
    
    # Create upload batches
    create_batches(all_sprites, output_dir)
    
    print(f"\n=== SUMMARY ===")
    print(f"Total sprites extracted: {len(all_sprites)}")
    print(f"  - Units: {len(unit_sprites)}")
    print(f"  - Terrain: {len(terrain_sprites)}")
    print(f"\nReady for AI upscaling!")
    print(f"\nNext steps:")
    print(f"1. Upload temp/complete_test_batch.zip to waifu2x to test")
    print(f"2. If good, upload complete_batch_*.zip files")
    print(f"3. Download to temp/complete_sprites_upscaled/")
    print(f"4. Run reassembly script")

if __name__ == "__main__":
    main()
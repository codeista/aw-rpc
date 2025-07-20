#!/usr/bin/env python3
"""
Extract ALL sprites as 16x16 (per user confirmation)
Includes both units and terrain tiles
"""

from PIL import Image
import os
import json

def extract_sprites_16x16(sheet_path, output_dir, sheet_name):
    """Extract all sprites as 16x16"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    sheet = Image.open(sheet_path)
    sprite_info = []
    sprite_count = 0
    
    print(f"\nExtracting 16x16 sprites from {sheet_name}")
    print(f"Sheet size: {sheet.width}x{sheet.height}")
    
    # Extract all as 16x16
    for y in range(0, sheet.height, 16):
        for x in range(0, sheet.width, 16):
            if x + 16 > sheet.width or y + 16 > sheet.height:
                continue
                
            sprite = sheet.crop((x, y, x + 16, y + 16))
            
            # Skip if completely transparent
            if sprite.getbbox() is None:
                continue
            
            filename = f"{sheet_name}_sprite_{sprite_count:04d}.png"
            filepath = os.path.join(output_dir, filename)
            sprite.save(filepath)
            
            sprite_info.append({
                "id": sprite_count,
                "filename": filename,
                "original_x": x,
                "original_y": y,
                "size": 16,
                "sheet": sheet_name
            })
            
            sprite_count += 1
    
    print(f"Extracted {sprite_count} sprites from {sheet_name}")
    return sprite_info

def main():
    """Extract all game sprites for upscaling"""
    
    all_sprites = []
    output_base = "temp/all_sprites_16x16"
    
    print("=== EXTRACTING ALL 16x16 SPRITES ===")
    
    # 1. Unit sprites (use v2 since complete is missing)
    unit_sheet = "/home/box/Documents/aw-rpc/static/img/units_sprite_sheet_v2.png"
    if os.path.exists(unit_sheet):
        sprites = extract_sprites_16x16(unit_sheet, output_base, "units")
        all_sprites.extend(sprites)
    
    # 2. Terrain tiles - the ones actually used
    terrain_sheets = [
        ("Advance_Wars_Dual_Strike_Tileset_Normal.png", "terrain_normal"),
        ("Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png", "terrain_transparent")
    ]
    
    for filename, sheet_name in terrain_sheets:
        path = f"/home/box/Documents/aw-rpc/static/img/{filename}"
        if os.path.exists(path):
            sprites = extract_sprites_16x16(path, output_base, sheet_name)
            all_sprites.extend(sprites)
    
    # Save complete mapping
    with open(os.path.join(output_base, "all_sprites_mapping.json"), "w") as f:
        json.dump(all_sprites, f, indent=2)
    
    # Create preview
    create_combined_preview(output_base, all_sprites)
    
    # Summary
    print(f"\n=== EXTRACTION COMPLETE ===")
    print(f"Total sprites extracted: {len(all_sprites)}")
    
    by_sheet = {}
    for sprite in all_sprites:
        sheet = sprite["sheet"]
        by_sheet[sheet] = by_sheet.get(sheet, 0) + 1
    
    for sheet, count in by_sheet.items():
        print(f"  - {sheet}: {count} sprites")
    
    print(f"\nAll sprites saved to: {output_base}/")
    print("Preview saved to: temp/all_sprites_preview.png")

def create_combined_preview(sprite_dir, sprite_info):
    """Create a preview of all extracted sprites"""
    
    # Sample sprites from each sheet
    samples_per_sheet = 50
    sampled = []
    
    sheets = list(set(s["sheet"] for s in sprite_info))
    
    for sheet in sheets:
        sheet_sprites = [s for s in sprite_info if s["sheet"] == sheet]
        sampled.extend(sheet_sprites[:samples_per_sheet])
    
    # Create preview
    cols = 25
    rows = (len(sampled) + cols - 1) // cols
    
    preview = Image.new('RGBA', 
        (cols * 18, rows * 18), 
        (64, 64, 64, 255))
    
    for i, sprite_info in enumerate(sampled):
        sprite_path = os.path.join(sprite_dir, sprite_info["filename"])
        sprite = Image.open(sprite_path)
        
        x = (i % cols) * 18
        y = (i // cols) * 18
        
        preview.paste(sprite, (x, y), sprite)
    
    preview.save("temp/all_sprites_preview.png")

def create_batch_zips():
    """Create ZIP files for batch uploading"""
    
    import zipfile
    from pathlib import Path
    
    sprite_dir = Path("temp/all_sprites_16x16")
    sprites = list(sprite_dir.glob("*.png"))
    
    print(f"\n=== CREATING BATCH ZIP FILES ===")
    print(f"Total sprites to batch: {len(sprites)}")
    
    batch_size = 500
    batch_num = 1
    
    for i in range(0, len(sprites), batch_size):
        batch = sprites[i:i+batch_size]
        zip_name = f"temp/all_sprites_batch_{batch_num}.zip"
        
        with zipfile.ZipFile(zip_name, 'w') as zf:
            for sprite in batch:
                zf.write(sprite, sprite.name)
        
        print(f"Created {zip_name} with {len(batch)} sprites")
        batch_num += 1

if __name__ == "__main__":
    main()
    create_batch_zips()
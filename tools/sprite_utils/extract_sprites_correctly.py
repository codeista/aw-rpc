#!/usr/bin/env python3
"""
Extract sprites with correct sizes - buildings are 32x32!
"""

from PIL import Image
import os
import json

def extract_mixed_size_sprites(sheet_path, output_dir="temp/sprites_correct_size"):
    """Extract sprites with proper sizes - 16x16 for units, 32x32 for buildings"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    sheet = Image.open(sheet_path)
    sprite_info = []
    sprite_count = 0
    
    print(f"Extracting sprites with correct sizes from {sheet_path}")
    
    # Buildings are at y=768 and y=800 (rows 48 and 50)
    building_rows = [768, 800]
    
    # Process the sprite sheet
    y = 0
    while y < sheet.height:
        x = 0
        while x < sheet.width:
            sprite_size = 16  # Default
            
            # Check if this is a building row
            if y in building_rows:
                # Buildings are 32x32
                sprite_size = 32
                
            # Extract sprite
            sprite = sheet.crop((x, y, x + sprite_size, y + sprite_size))
            
            # Skip if completely transparent
            if sprite.getbbox() is None:
                x += sprite_size
                continue
            
            # Save sprite
            filename = f"sprite_{sprite_count:04d}_{sprite_size}x{sprite_size}.png"
            filepath = os.path.join(output_dir, filename)
            sprite.save(filepath)
            
            # Store mapping
            sprite_info.append({
                "id": sprite_count,
                "filename": filename,
                "original_x": x,
                "original_y": y,
                "size": sprite_size,
                "type": "building" if y in building_rows else "unit"
            })
            
            sprite_count += 1
            x += sprite_size
            
        # Move to next row
        if y in building_rows:
            y += 32
        else:
            y += 16
    
    # Save mapping
    with open(os.path.join(output_dir, "sprite_mapping.json"), "w") as f:
        json.dump(sprite_info, f, indent=2)
    
    print(f"Extracted {sprite_count} sprites (mixed sizes)")
    
    # Summary
    units = sum(1 for s in sprite_info if s["type"] == "unit")
    buildings = sum(1 for s in sprite_info if s["type"] == "building")
    print(f"  - Units (16x16): {units}")
    print(f"  - Buildings (32x32): {buildings}")
    
    return sprite_info

def create_mixed_preview(sprite_dir):
    """Create preview showing both unit and building sprites"""
    
    with open(os.path.join(sprite_dir, "sprite_mapping.json"), "r") as f:
        sprite_info = json.load(f)
    
    # Separate by type
    units = [s for s in sprite_info if s["type"] == "unit"][:50]
    buildings = [s for s in sprite_info if s["type"] == "building"][:20]
    
    # Create preview
    preview = Image.new('RGBA', (800, 400), (64, 64, 64, 255))
    
    # Draw units (16x16)
    y_offset = 10
    for i, unit in enumerate(units):
        sprite = Image.open(os.path.join(sprite_dir, unit["filename"]))
        x = (i % 20) * 20 + 10
        y = (i // 20) * 20 + y_offset
        preview.paste(sprite, (x, y), sprite)
    
    # Draw buildings (32x32)
    y_offset = 100
    for i, building in enumerate(buildings):
        sprite = Image.open(os.path.join(sprite_dir, building["filename"]))
        x = (i % 10) * 40 + 10
        y = (i // 10) * 40 + y_offset
        preview.paste(sprite, (x, y), sprite)
    
    preview.save("temp/mixed_sprite_preview.png")
    print("Preview saved to temp/mixed_sprite_preview.png")

def main():
    # Extract with correct sizes
    sprite_info = extract_mixed_size_sprites(
        "/home/box/Documents/aw-rpc/static/img/units_sprite_sheet_v2.png"
    )
    
    # Create preview
    create_mixed_preview("temp/sprites_correct_size")
    
    print("\n✅ Sprites extracted with CORRECT sizes!")
    print("Buildings are properly extracted as 32x32")
    print("Units remain 16x16")

if __name__ == "__main__":
    main()
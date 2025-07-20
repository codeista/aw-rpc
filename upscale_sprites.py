#!/usr/bin/env python3
"""
Extract and prepare sprites for AI upscaling
"""

from PIL import Image
import os
import json

def extract_sprites_from_sheet(sheet_path, sprite_size=16, output_dir="temp/sprites_to_upscale"):
    """Extract individual sprites from sprite sheet"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    sheet = Image.open(sheet_path)
    sprite_info = []
    sprite_count = 0
    
    print(f"Extracting sprites from {sheet_path}")
    print(f"Sheet size: {sheet.width}x{sheet.height}")
    
    for y in range(0, sheet.height, sprite_size):
        for x in range(0, sheet.width, sprite_size):
            # Extract sprite
            sprite = sheet.crop((x, y, x + sprite_size, y + sprite_size))
            
            # Skip if completely transparent
            if sprite.getbbox() is None:
                continue
            
            # Save individual sprite
            filename = f"sprite_{sprite_count:04d}.png"
            filepath = os.path.join(output_dir, filename)
            sprite.save(filepath)
            
            # Store mapping info
            sprite_info.append({
                "id": sprite_count,
                "filename": filename,
                "original_x": x,
                "original_y": y,
                "size": sprite_size
            })
            
            sprite_count += 1
    
    # Save mapping
    with open(os.path.join(output_dir, "sprite_mapping.json"), "w") as f:
        json.dump(sprite_info, f, indent=2)
    
    print(f"Extracted {sprite_count} sprites to {output_dir}")
    return sprite_info

def upscale_with_nearest_neighbor(input_dir, output_dir, scale=3):
    """Simple nearest neighbor upscaling (fallback if no AI available)"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load mapping
    with open(os.path.join(input_dir, "sprite_mapping.json"), "r") as f:
        sprite_info = json.load(f)
    
    print(f"Upscaling {len(sprite_info)} sprites with nearest neighbor...")
    
    for info in sprite_info:
        input_path = os.path.join(input_dir, info["filename"])
        output_path = os.path.join(output_dir, info["filename"])
        
        # Open and upscale
        sprite = Image.open(input_path)
        upscaled = sprite.resize(
            (sprite.width * scale, sprite.height * scale),
            Image.NEAREST
        )
        upscaled.save(output_path)
    
    # Copy mapping with updated size
    for info in sprite_info:
        info["size"] = info["size"] * scale
    
    with open(os.path.join(output_dir, "sprite_mapping.json"), "w") as f:
        json.dump(sprite_info, f, indent=2)
    
    print(f"Upscaled sprites saved to {output_dir}")

def reassemble_sprite_sheet(sprite_dir, output_path, sprite_size=48, columns=32):
    """Reassemble individual sprites into a sprite sheet"""
    
    # Load mapping
    with open(os.path.join(sprite_dir, "sprite_mapping.json"), "r") as f:
        sprite_info = json.load(f)
    
    # Calculate sheet dimensions
    max_x = max(info["original_x"] for info in sprite_info) // 16
    max_y = max(info["original_y"] for info in sprite_info) // 16
    
    sheet_width = (max_x + 1) * sprite_size
    sheet_height = (max_y + 1) * sprite_size
    
    print(f"Creating sprite sheet: {sheet_width}x{sheet_height}")
    
    # Create new sheet
    sheet = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
    
    # Place sprites
    for info in sprite_info:
        sprite_path = os.path.join(sprite_dir, info["filename"])
        sprite = Image.open(sprite_path)
        
        # Calculate position (scale up the original coordinates)
        x = (info["original_x"] // 16) * sprite_size
        y = (info["original_y"] // 16) * sprite_size
        
        sheet.paste(sprite, (x, y), sprite)
    
    sheet.save(output_path)
    print(f"Sprite sheet saved to {output_path}")
    
    return sheet

def create_coordinate_mapping(original_size=16, new_size=48):
    """Create coordinate mapping for the game code"""
    
    scale = new_size / original_size
    
    mapping = {
        "scale": scale,
        "original_sprite_size": original_size,
        "new_sprite_size": new_size,
        "coordinate_multiplier": scale
    }
    
    print("\nCoordinate mapping for game code:")
    print(f"  Replace sprite coordinates: multiply by {scale}")
    print(f"  Example: (32, 64) becomes ({32*scale}, {64*scale})")
    
    return mapping

def main():
    # Paths
    unit_sprites = "/home/box/Documents/aw-rpc/static/img/units_sprite_sheet_v2.png"
    
    print("=== Sprite Upscaling Preparation ===\n")
    
    # Step 1: Extract sprites
    print("Step 1: Extracting sprites...")
    sprite_info = extract_sprites_from_sheet(unit_sprites)
    
    # Step 2: Simple upscale (for testing)
    print("\nStep 2: Upscaling with nearest neighbor...")
    upscale_with_nearest_neighbor(
        "temp/sprites_to_upscale",
        "temp/sprites_upscaled",
        scale=3
    )
    
    # Step 3: Reassemble
    print("\nStep 3: Reassembling sprite sheet...")
    reassemble_sprite_sheet(
        "temp/sprites_upscaled",
        "temp/units_sprite_sheet_48x48.png"
    )
    
    # Step 4: Create mapping
    print("\nStep 4: Creating coordinate mapping...")
    mapping = create_coordinate_mapping()
    
    print("\n✅ Complete!")
    print("\nNext steps:")
    print("1. For better quality, upload temp/sprites_to_upscale/*.png to waifu2x")
    print("2. Download results to temp/sprites_upscaled_ai/")
    print("3. Run: python upscale_sprites.py --reassemble-only")
    print("\nOr use the nearest neighbor version at: temp/units_sprite_sheet_48x48.png")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--reassemble-only":
        # Just reassemble from AI upscaled sprites
        reassemble_sprite_sheet(
            "temp/sprites_upscaled_ai",
            "static/img/units_sprite_sheet_48x48_ai.png"
        )
    else:
        main()
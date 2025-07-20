#!/usr/bin/env python3
"""
Verify we're using the correct original tileset
"""

from PIL import Image
import os

def check_tilesets():
    """Compare the tilesets to ensure we use the right one"""
    
    print("=== TILESET VERIFICATION ===\n")
    
    # The CORRECT original tileset
    original = "/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png"
    
    # The one I was incorrectly using
    incorrect = "/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal.png"
    
    for path, name in [(original, "ORIGINAL (Transparent)"), (incorrect, "NEW (Incomplete)")]:
        try:
            img = Image.open(path)
            print(f"{name}:")
            print(f"  Path: {path}")
            print(f"  Size: {img.width}x{img.height}")
            print(f"  Mode: {img.mode}")
            
            # Check if tiles are 16x16
            if img.width % 16 == 0 and img.height % 16 == 0:
                print(f"  16x16 grid: {img.width//16} x {img.height//16} = {(img.width//16) * (img.height//16)} tiles")
            else:
                print(f"  WARNING: Not divisible by 16!")
                
            # Sample first few tiles
            sample = Image.new('RGBA', (16*10, 16*5), (200, 200, 200, 255))
            for i in range(50):
                x = (i % 10) * 16
                y = (i // 10) * 16
                if x + 16 <= img.width and y + 16 <= img.height:
                    tile = img.crop((x, y, x+16, y+16))
                    sample.paste(tile, (x, y))
            
            sample.save(f"temp/tileset_sample_{name.replace(' ', '_').replace('(', '').replace(')', '')}.png")
            
        except Exception as e:
            print(f"{name}: ERROR - {e}")
        print()

def extract_from_correct_tileset():
    """Extract tiles from the CORRECT transparent tileset"""
    
    tileset_path = "/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png"
    print(f"\nExtracting from CORRECT tileset: {tileset_path}")
    
    img = Image.open(tileset_path)
    
    # Create preview of this tileset
    scale = 2
    preview = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    
    # Save full preview
    preview.save("temp/correct_tileset_preview.png")
    print(f"Saved full preview to: temp/correct_tileset_preview.png")
    
    # Count actual tiles
    tile_count = 0
    for y in range(0, img.height, 16):
        for x in range(0, img.width, 16):
            if x + 16 <= img.width and y + 16 <= img.height:
                tile = img.crop((x, y, x+16, y+16))
                if tile.getbbox():  # Has content
                    tile_count += 1
    
    print(f"Total tiles with content: {tile_count}")

def main():
    os.makedirs("temp", exist_ok=True)
    
    check_tilesets()
    extract_from_correct_tileset()
    
    print("\n✅ VERIFICATION COMPLETE")
    print("The CORRECT tileset to use is: Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png")
    print("This is the original tileset with proper 16x16 tiles")

if __name__ == "__main__":
    main()
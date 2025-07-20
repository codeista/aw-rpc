#!/usr/bin/env python3
"""
Verify the complete sprite sheet that we're actually using
"""

from PIL import Image
import json

def check_sprite_sheets():
    """Check all sprite sheets to understand what we have"""
    
    print("=== SPRITE SHEET VERIFICATION ===\n")
    
    sheets = [
        "/home/box/Documents/aw-rpc/static/img/units_sprite_sheet_complete.png",
        "/home/box/Documents/aw-rpc/static/img/units_sprite_sheet_v2.png",
        "/home/box/Documents/aw-rpc/temp/units_sprite_sheet_48x48.png"
    ]
    
    for sheet_path in sheets:
        try:
            img = Image.open(sheet_path)
            print(f"{sheet_path.split('/')[-1]}:")
            print(f"  - Size: {img.width}x{img.height}")
            print(f"  - 16x16 grid: {img.width//16} x {img.height//16} = {(img.width//16) * (img.height//16)} sprites")
            
            # Check if it's the upscaled one
            if "48x48" in sheet_path:
                print(f"  - 48x48 grid: {img.width//48} x {img.height//48} = {(img.width//48) * (img.height//48)} sprites")
            
            # Sample first sprite
            first_sprite = img.crop((0, 0, 16, 16))
            if first_sprite.getbbox():
                print(f"  - First sprite has content")
                
        except Exception as e:
            print(f"{sheet_path}: ERROR - {e}")
        print()
    
    # Check sprite map
    try:
        with open("/home/box/Documents/aw-rpc/static/img/units_sprite_map_complete.json", "r") as f:
            sprite_map = json.load(f)
            
        print("units_sprite_map_complete.json:")
        print(f"  - Total sprites defined: {sprite_map.get('total_sprites', 'N/A')}")
        print(f"  - Sample keys: {list(sprite_map.get('sprites', {}).keys())[:5]}")
    except Exception as e:
        print(f"Sprite map error: {e}")

def main():
    check_sprite_sheets()
    
    print("\n=== CONCLUSION ===")
    print("The game uses units_sprite_sheet_complete.png (160x400, 250 sprites)")
    print("All sprites are 16x16 pixels")
    print("We already extracted 3000 sprites from units_sprite_sheet_v2.png")
    print("\nShould we:")
    print("1. Use the already extracted sprites from v2 (3000 sprites)")
    print("2. Extract from the complete sheet (250 sprites)")
    print("3. Extract terrain tiles as well")

if __name__ == "__main__":
    main()
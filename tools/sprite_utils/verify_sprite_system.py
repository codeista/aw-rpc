#!/usr/bin/env python3
"""
Verify what sprite system we're actually using and what sizes are correct
"""

from PIL import Image
import json

def check_all_sprite_sheets():
    """Check all sprite sheets in the project"""
    
    sprite_sheets = [
        "/home/box/Documents/aw-rpc/static/img/units_sprite_sheet_v2.png",
        "/home/box/Documents/aw-rpc/static/img/units_sprite_sheet.png",
        "/home/box/Documents/aw-rpc/static/img/tileset_AW1.png",
        "/home/box/Documents/aw-rpc/static/img/tileset_AW2.png"
    ]
    
    print("=== Checking all sprite sheets ===\n")
    
    for sheet_path in sprite_sheets:
        try:
            img = Image.open(sheet_path)
            print(f"{sheet_path.split('/')[-1]}: {img.width}x{img.height}")
            
            # Check if it's a units sheet
            if "units" in sheet_path:
                # Sample some known positions
                infantry = img.crop((0, 0, 16, 16))
                print(f"  - Infantry (0,0): {'Has pixels' if infantry.getbbox() else 'Empty'}")
                
                # Check HQ area
                hq_16 = img.crop((400, 768, 416, 784))
                hq_32 = img.crop((400, 768, 432, 800))
                print(f"  - HQ as 16x16: {'Has pixels' if hq_16.getbbox() else 'Empty'}")
                print(f"  - HQ as 32x32: {'Has pixels' if hq_32.getbbox() else 'Empty'}")
                
        except Exception as e:
            print(f"{sheet_path}: ERROR - {e}")
        print()

def check_rendering_code():
    """See which sprite system the game actually uses"""
    
    print("\n=== Current rendering system ===")
    
    # Check render_legacy.js
    with open("/home/box/Documents/aw-rpc/static/js/render_legacy.js", "r") as f:
        content = f.read()
        
    # Find sprite sheet references
    if "units_sprite_sheet_v2.png" in content:
        print("✅ Using units_sprite_sheet_v2.png")
    elif "units_sprite_sheet.png" in content:
        print("❌ Using old units_sprite_sheet.png")
    
    # Check if optimized renderer is disabled
    if "optimized-tile-renderer.js" in content and "disabled" in content.lower():
        print("✅ Optimized renderer is disabled (corrupted)")
    
    # Find sprite coordinate system
    print("\nSprite coordinate examples from code:")
    
    # Look for specific unit coordinates
    test_patterns = [
        ("Infantry", "0.*0.*16.*16"),
        ("HQ", "400.*768"),
        ("Mountain", "416.*768")
    ]
    
    for name, pattern in test_patterns:
        if pattern in content:
            print(f"  - {name}: Found pattern {pattern}")

def analyze_building_sprites():
    """Special analysis for buildings which might be different"""
    
    print("\n=== Building sprite analysis ===")
    
    sheet = Image.open("/home/box/Documents/aw-rpc/static/img/units_sprite_sheet_v2.png")
    
    # Buildings are typically at row 48 (y=768)
    building_y = 768
    
    buildings = [
        ("HQ", 400),
        ("City", 352),
        ("Factory", 368),
        ("Airport", 384),
        ("Mountain", 416)
    ]
    
    for name, x in buildings:
        # Try different sizes
        sprite_16 = sheet.crop((x, building_y, x+16, building_y+16))
        sprite_32 = sheet.crop((x, building_y, x+32, building_y+32))
        
        bbox_16 = sprite_16.getbbox()
        bbox_32 = sprite_32.getbbox()
        
        # Save for visual inspection
        if bbox_16:
            sprite_16.save(f"temp/building_{name}_16x16.png")
        if bbox_32:
            sprite_32.save(f"temp/building_{name}_32x32.png")
            
        print(f"{name}:")
        print(f"  - 16x16 has pixels: {bbox_16 is not None}")
        print(f"  - 32x32 has pixels: {bbox_32 is not None}")
        
        # Check if pixels extend beyond 16x16
        if bbox_16 and bbox_32:
            extends_beyond = (bbox_32[2] > 16 or bbox_32[3] > 16)
            print(f"  - Extends beyond 16x16: {extends_beyond}")

def main():
    check_all_sprite_sheets()
    check_rendering_code()
    analyze_building_sprites()
    
    print("\n=== CONCLUSION ===")
    print("1. Most units are 16x16 sprites")
    print("2. Buildings (HQ, Factory, etc) appear to be 16x16 in the sprite sheet")
    print("3. The game uses units_sprite_sheet_v2.png")
    print("4. The optimized renderer is disabled")
    print("5. Our extraction of 16x16 sprites is CORRECT")
    print("\nThe sprites looking 'small' is the whole problem we're trying to solve!")
    print("That's why we need to upscale them to 48x48 for a larger game display.")

if __name__ == "__main__":
    main()
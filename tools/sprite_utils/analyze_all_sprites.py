#!/usr/bin/env python3
"""
Analyze ALL sprite sheets - units and terrain
"""

from PIL import Image
import os

def analyze_all_assets():
    """Check all game assets that need upscaling"""
    
    print("=== COMPLETE ASSET ANALYSIS ===\n")
    
    # Unit sprites
    print("1. UNIT SPRITES:")
    unit_sheet = "/home/box/Documents/aw-rpc/static/img/units_sprite_sheet_v2.png"
    
    try:
        img = Image.open(unit_sheet)
        print(f"   - units_sprite_sheet_v2.png: {img.width}x{img.height}")
        print(f"   - Grid: {img.width//16} x {img.height//16} tiles")
        print(f"   - Total 16x16 sprites: ~{(img.width//16) * (img.height//16)}")
        print(f"   - Has buildings at y=768 that are 32x32")
    except Exception as e:
        print(f"   - Error: {e}")
    
    # Terrain tilesets
    print("\n2. TERRAIN TILESETS:")
    
    terrain_sheets = [
        "Advance_Wars_Dual_Strike_Tileset_Normal.png",
        "Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png",
        "optimized_tileset_normal.png",
        "optimized_tileset_transparent.png"
    ]
    
    for sheet in terrain_sheets:
        path = f"/home/box/Documents/aw-rpc/static/img/{sheet}"
        try:
            img = Image.open(path)
            print(f"   - {sheet}: {img.width}x{img.height}")
            
            # Guess tile size
            if img.width % 16 == 0 and img.height % 16 == 0:
                print(f"     16x16 grid: {img.width//16} x {img.height//16} tiles")
            if img.width % 32 == 0 and img.height % 32 == 0:
                print(f"     32x32 grid: {img.width//32} x {img.height//32} tiles")
                
        except Exception as e:
            print(f"   - {sheet}: Not found or error")
    
    # Check which tileset is actually used
    print("\n3. CHECKING WHICH ASSETS ARE USED:")
    
    with open("/home/box/Documents/aw-rpc/static/js/render_legacy.js", "r") as f:
        render_code = f.read()
    
    assets = [
        "units_sprite_sheet_v2.png",
        "Advance_Wars_Dual_Strike_Tileset_Normal.png",
        "optimized_tileset_normal.png",
        "Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png",
        "optimized_tileset_transparent.png"
    ]
    
    for asset in assets:
        if asset in render_code:
            print(f"   ✅ {asset} - USED in render_legacy.js")
        else:
            print(f"   ❌ {asset} - NOT used")
    
    # Summary
    print("\n4. UPSCALING REQUIREMENTS:")
    print("   - Unit sprites: Mix of 16x16 and 32x32 → scale to 48x48 and 96x96")
    print("   - Terrain tiles: Check tile size, likely 16x16 → scale to 48x48")
    print("   - Need to identify which terrain tileset is active")

def check_terrain_tile_size():
    """Determine actual terrain tile size"""
    
    print("\n\n=== TERRAIN TILE SIZE ANALYSIS ===")
    
    # Load one tileset
    tileset = Image.open("/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal.png")
    
    # Extract sample tiles at different sizes
    test_sizes = [16, 32]
    
    for size in test_sizes:
        print(f"\nTesting {size}x{size} tiles:")
        
        # Extract first few tiles
        for i in range(3):
            x = i * size
            y = 0
            
            if x + size <= tileset.width:
                tile = tileset.crop((x, y, x + size, y + size))
                tile.save(f"temp/terrain_test_{size}x{size}_tile{i}.png")
                
                bbox = tile.getbbox()
                print(f"   Tile {i}: {'Has content' if bbox else 'Empty'}")

def main():
    analyze_all_assets()
    check_terrain_tile_size()
    
    print("\n\n=== NEXT STEPS ===")
    print("1. Extract unit sprites with mixed sizes (16x16 and 32x32)")
    print("2. Extract terrain tiles (need to confirm size)")
    print("3. Upscale everything to 3x size")
    print("4. Update game to use larger assets")

if __name__ == "__main__":
    main()
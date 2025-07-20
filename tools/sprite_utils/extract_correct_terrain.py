#!/usr/bin/env python3
"""
Extract terrain with correct coordinates provided by user
"""

from PIL import Image
import os

def extract_plain_variants():
    """Extract the PLAIN tile variants at the given coordinates"""
    
    tileset = Image.open("/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png")
    
    # User provided coordinates for PLAIN
    plain_coords = [
        (8, 64, "PLAIN_1"),
        (23, 64, "PLAIN_2"), 
        (8, 79, "PLAIN_3"),
        (23, 79, "PLAIN_4")
    ]
    
    print("=== EXTRACTING PLAIN VARIANTS ===\n")
    
    os.makedirs("temp/correct_terrain", exist_ok=True)
    
    for x, y, name in plain_coords:
        print(f"{name} at ({x}, {y})")
        
        # Extract 16x16 tile
        tile = tileset.crop((x, y, x + 16, y + 16))
        
        if tile.getbbox():
            filename = f"temp/correct_terrain/{name}.png"
            tile.save(filename)
            print(f"  ✓ Saved as {filename}")
        else:
            print(f"  ✗ Empty tile")
    
    # Now let me examine the pattern - these coordinates are much simpler!
    # Let me extract a larger area to see the tile layout
    extract_area = tileset.crop((0, 60, 100, 100))
    extract_area.save("temp/correct_terrain/plains_area.png")
    
    print(f"\nSaved plains area (0,60 to 100,100) as temp/correct_terrain/plains_area.png")

def find_terrain_pattern():
    """Try to understand the coordinate pattern"""
    
    # The coordinates (8,64), (23,64), (8,79), (23,79) suggest:
    # - X spacing of 15 pixels between variants (23-8=15)
    # - Y spacing of 15 pixels between rows (79-64=15)
    # - Starting at (8,64)
    
    print("\n=== ANALYZING COORDINATE PATTERN ===")
    print("PLAIN coordinates suggest a 15-pixel spacing pattern:")
    print("- Base: (8, 64)")
    print("- X spacing: 15 pixels") 
    print("- Y spacing: 15 pixels")
    print("- This is NOT a standard 16x16 grid!")
    
    # Let me check if other terrain follows this pattern
    tileset = Image.open("/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png")
    
    # Test extraction around this area
    test_coords = []
    for row in range(5):
        for col in range(8):
            x = 8 + col * 15
            y = 64 + row * 15
            test_coords.append((x, y, f"tile_{row}_{col}"))
    
    os.makedirs("temp/pattern_test", exist_ok=True)
    
    for x, y, name in test_coords:
        if x + 16 <= tileset.width and y + 16 <= tileset.height:
            tile = tileset.crop((x, y, x + 16, y + 16))
            if tile.getbbox():
                tile.save(f"temp/pattern_test/{name}_at_{x}_{y}.png")

def main():
    extract_plain_variants()
    find_terrain_pattern()
    
    print("\n✅ Check temp/correct_terrain/ and temp/pattern_test/")
    print("Now I understand the coordinate system is NOT the Two.js offsets!")

if __name__ == "__main__":
    main()
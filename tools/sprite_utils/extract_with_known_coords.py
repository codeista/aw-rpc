#!/usr/bin/env python3
"""
Extract terrain tiles using known coordinates from user
"""

from PIL import Image
import os

def extract_known_terrain():
    """Extract terrain with known coordinates"""
    
    tileset = Image.open("/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png")
    
    # Known coordinates from user
    known_coords = [
        # PLAIN variants
        (8, 64, "PLAIN_1"),
        (23, 64, "PLAIN_2"),
        (8, 79, "PLAIN_3"), 
        (23, 79, "PLAIN_4"),
        
        # ROAD_HORT variants
        (42, 64, "ROAD_HORT_1"),
        (57, 79, "ROAD_HORT_2"),  # Note: different Y coordinate
    ]
    
    print("=== EXTRACTING KNOWN TERRAIN TILES ===\n")
    
    os.makedirs("temp/known_terrain", exist_ok=True)
    
    for x, y, name in known_coords:
        print(f"{name} at ({x}, {y})")
        
        # Extract 16x16 tile
        tile = tileset.crop((x, y, x + 16, y + 16))
        
        if tile.getbbox():
            filename = f"temp/known_terrain/{name}.png"
            tile.save(filename)
            print(f"  ✓ Saved as {filename}")
        else:
            print(f"  ✗ Empty tile")
    
    # Extract a larger area to see the pattern
    area = tileset.crop((0, 60, 120, 100))
    area.save("temp/known_terrain/terrain_area_60_100.png")
    
    print(f"\nSaved terrain area for analysis: temp/known_terrain/terrain_area_60_100.png")

def analyze_tileset_structure():
    """Try to understand the tileset layout"""
    
    tileset = Image.open("/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png")
    
    print(f"\n=== TILESET STRUCTURE ANALYSIS ===")
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # Check for grey separators
    print(f"\nLooking for grey separator pattern...")
    
    # Sample some pixels to find the separator color
    separators = []
    
    # Check vertical lines that might be separators
    for x in range(0, min(100, tileset.width)):
        pixel = tileset.getpixel((x, 64))
        if isinstance(pixel, tuple) and len(pixel) >= 3:
            # Check if it's greyish
            r, g, b = pixel[:3]
            if r == g == b and 50 < r < 200:  # Grey range
                separators.append((x, pixel))
    
    if separators:
        print(f"Found potential separators at X positions: {[x for x, _ in separators[:10]]}")
        sep_color = separators[0][1]
        print(f"Separator color: {sep_color}")
    
    # Extract a systematic grid with the known pattern
    print(f"\nExtracting systematic grid around known areas...")
    
    # Based on known coordinates, try to extract a grid
    os.makedirs("temp/systematic_grid", exist_ok=True)
    
    # Start from (8, 64) and extract in a pattern
    start_x, start_y = 8, 64
    
    for row in range(5):
        for col in range(10):
            # Try different spacing patterns
            x = start_x + col * 17  # 16 + 1 pixel gap
            y = start_y + row * 15  # 15 pixel spacing (as observed)
            
            if x + 16 <= tileset.width and y + 16 <= tileset.height:
                tile = tileset.crop((x, y, x + 16, y + 16))
                if tile.getbbox():
                    filename = f"temp/systematic_grid/tile_r{row}_c{col}_at_{x}_{y}.png"
                    tile.save(filename)

def main():
    extract_known_terrain()
    analyze_tileset_structure()
    
    print(f"\n✅ Check results in temp/known_terrain/ and temp/systematic_grid/")
    print(f"Please provide coordinates for more terrain types:")
    print(f"  - MOUNTAIN")
    print(f"  - SEA") 
    print(f"  - ROAD_VERT")
    print(f"  - CITY/FACTORY/HQ")
    print(f"  - Any others you know")

if __name__ == "__main__":
    main()
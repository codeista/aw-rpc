#!/usr/bin/env python3
"""
Scan for plain/grass tiles in the new AW2 tileset
"""

from PIL import Image
import os

def is_likely_plain_tile(img, x, y, size=8):
    """Check if a tile looks like a plain/grass tile"""
    tile = img.crop((x, y, x + size, y + size))
    pixels = list(tile.getdata())
    
    # Count green-ish pixels
    green_count = 0
    for pixel in pixels:
        if len(pixel) >= 3:  # RGB or RGBA
            r, g, b = pixel[:3]
            # Check if green is dominant
            if g > r and g > b and g > 100:
                green_count += 1
    
    # Plain tiles should be mostly green
    return green_count > (size * size * 0.5)

def scan_tileset():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    
    if not os.path.exists(tileset_path):
        print(f"Error: Tileset not found at {tileset_path}")
        return
    
    tileset = Image.open(tileset_path).convert('RGBA')
    width, height = tileset.size
    print(f"Tileset size: {width}x{height}")
    
    # First, let's check what's at the mapped location
    print("\nChecking mapped location (129, 10):")
    tile = tileset.crop((129, 10, 137, 18))
    pixels = list(tile.getdata())
    # Get color info
    unique_colors = set(pixels)
    print(f"Colors at (129, 10): {list(unique_colors)[:5]}...")  # Show first 5 colors
    
    # Scan for green tiles (likely plain/grass)
    print("\nScanning for green/grass tiles (8x8 grid):")
    found_tiles = []
    
    # Scan in 8x8 grid
    for y in range(0, min(height - 8, 200), 8):  # Limit scan to first 200 pixels height
        for x in range(0, min(width - 8, 400), 8):  # Limit scan to first 400 pixels width
            if is_likely_plain_tile(tileset, x, y):
                found_tiles.append((x, y))
    
    # Show first 10 found tiles
    print(f"\nFound {len(found_tiles)} potential plain/grass tiles.")
    print("First 10 locations:")
    for i, (x, y) in enumerate(found_tiles[:10]):
        print(f"  {i+1}. Position: ({x}, {y})")
        
        # Save a sample
        if i < 5:
            tile = tileset.crop((x, y, x + 8, y + 8))
            tile_scaled = tile.resize((64, 64), Image.NEAREST)
            tile_scaled.save(f"potential_plain_{i+1}_at_{x}_{y}.png")
    
    # Also check common plain tile locations in AW tilesets
    print("\nChecking common plain tile positions:")
    common_positions = [
        (0, 0), (8, 0), (16, 0), (24, 0),
        (0, 8), (8, 8), (16, 8), (24, 8),
        (0, 16), (8, 16), (16, 16), (24, 16),
        (128, 8), (128, 16), (136, 8), (136, 16),
        (144, 8), (144, 16), (152, 8), (152, 16)
    ]
    
    for x, y in common_positions:
        if x < width - 8 and y < height - 8:
            tile = tileset.crop((x, y, x + 8, y + 8))
            pixels = list(tile.getdata())
            # Get dominant color
            if pixels:
                avg_color = tuple(sum(c[i] for c in pixels) // len(pixels) for i in range(3))
                print(f"  ({x}, {y}): Average RGB = {avg_color}")

if __name__ == "__main__":
    scan_tileset()
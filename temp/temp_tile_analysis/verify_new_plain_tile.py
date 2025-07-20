#!/usr/bin/env python3
"""
Verify the plain tile in the new AW2 tileset
"""

from PIL import Image
import os

def verify_plain_tile():
    # Load the new tileset
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    
    if not os.path.exists(tileset_path):
        print(f"Error: Tileset not found at {tileset_path}")
        return
    
    tileset = Image.open(tileset_path)
    print(f"Tileset size: {tileset.size}")
    
    # Extract the plain tile at (129, 10) with size 8x8
    plain_x, plain_y = 129, 10
    plain_size = 8
    
    # Extract the tile
    plain_tile = tileset.crop((plain_x, plain_y, plain_x + plain_size, plain_y + plain_size))
    
    # Save it for inspection
    plain_tile_scaled = plain_tile.resize((64, 64), Image.NEAREST)
    plain_tile_scaled.save("new_plain_tile_8x8_scaled.png")
    print(f"Saved plain tile from ({plain_x}, {plain_y}) as new_plain_tile_8x8_scaled.png")
    
    # Also extract surrounding area to see context
    context_size = 32
    context_x = max(0, plain_x - context_size//2)
    context_y = max(0, plain_y - context_size//2)
    
    context = tileset.crop((context_x, context_y, context_x + context_size, context_y + context_size))
    context_scaled = context.resize((context_size * 4, context_size * 4), Image.NEAREST)
    context_scaled.save("new_plain_tile_context.png")
    print(f"Saved context around plain tile as new_plain_tile_context.png")
    
    # Analyze the plain tile
    print("\nPlain tile analysis:")
    pixels = list(plain_tile.getdata())
    unique_colors = len(set(pixels))
    print(f"- Unique colors: {unique_colors}")
    
    # Get dominant color
    color_counts = {}
    for pixel in pixels:
        if pixel in color_counts:
            color_counts[pixel] += 1
        else:
            color_counts[pixel] = 1
    
    dominant_color = max(color_counts, key=color_counts.get)
    print(f"- Dominant color: RGB{dominant_color[:3]} (appears {color_counts[dominant_color]} times)")

if __name__ == "__main__":
    verify_plain_tile()
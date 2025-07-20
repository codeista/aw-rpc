#!/usr/bin/env python3
"""
Find tiles by looking for visual separators (blue lines) in the tileset
"""

from PIL import Image, ImageDraw
import os

def analyze_separator_pattern():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    
    if not os.path.exists(tileset_path):
        print(f"Error: Tileset not found at {tileset_path}")
        return
    
    tileset = Image.open(tileset_path).convert('RGBA')
    width, height = tileset.size
    print(f"Tileset size: {width}x{height}")
    
    # Let's examine the specific area around (129, 10) more carefully
    # Based on user saying "can you find all the tiles by the blue line separating them"
    
    # Extract a larger area to see the pattern
    sample_x, sample_y = 120, 0
    sample_width, sample_height = 80, 40
    
    sample = tileset.crop((sample_x, sample_y, sample_x + sample_width, sample_y + sample_height))
    sample_scaled = sample.resize((sample_width * 4, sample_height * 4), Image.NEAREST)
    sample_scaled.save("separator_pattern_analysis.png")
    
    print(f"\nAnalyzing region from ({sample_x}, {sample_y}) to ({sample_x + sample_width}, {sample_y + sample_height})")
    
    # Look for repeating patterns - tiles might be 8x8 with 1-pixel separators
    # Or they might be 9x9 including the separator
    
    # Check different tile sizes and patterns
    for tile_size in [8, 9, 16, 17]:
        print(f"\nChecking for {tile_size}x{tile_size} tile pattern:")
        
        # Create a visualization
        vis = sample.copy()
        draw = ImageDraw.Draw(vis)
        
        tiles_found = []
        
        # Draw grid based on tile size
        for y in range(0, sample_height, tile_size):
            for x in range(0, sample_width, tile_size):
                # Draw grid lines
                draw.rectangle([x, y, x + tile_size - 1, y + tile_size - 1], outline=(255, 0, 0, 128), width=1)
                
                # Check what's at this position in the original tileset
                tile_x = sample_x + x
                tile_y = sample_y + y
                
                if tile_x + tile_size <= width and tile_y + tile_size <= height:
                    # Sample the tile
                    tile = tileset.crop((tile_x, tile_y, tile_x + tile_size, tile_y + tile_size))
                    
                    # Check if this looks like a valid tile (not all blue)
                    pixels = list(tile.getdata())
                    blue_pixels = sum(1 for p in pixels if len(p) >= 3 and p[2] > 150 and p[0] < 100 and p[1] < 150)
                    
                    if blue_pixels < len(pixels) * 0.5:  # Less than 50% blue
                        tiles_found.append((tile_x, tile_y))
        
        vis_scaled = vis.resize((sample_width * 4, sample_height * 4), Image.NEAREST)
        vis_scaled.save(f"grid_pattern_{tile_size}x{tile_size}.png")
        
        if tiles_found:
            print(f"  Found {len(tiles_found)} potential tiles")
            for i, (x, y) in enumerate(tiles_found[:5]):
                print(f"    Tile {i+1}: ({x}, {y})")
    
    # Specifically check the tile at (129, 10) and its neighbors
    print("\n\nChecking tiles around (129, 10):")
    
    # Try different interpretations
    interpretations = [
        ("8x8 tiles with 1px separator", 9, 8),
        ("8x8 tiles no separator", 8, 8),
        ("9x9 tiles including separator", 9, 9),
    ]
    
    for desc, step, size in interpretations:
        print(f"\n{desc}:")
        # Calculate aligned position
        aligned_x = (129 // step) * step
        aligned_y = (10 // step) * step
        
        print(f"  Aligned position: ({aligned_x}, {aligned_y})")
        
        # Extract and save this tile
        if aligned_x + size <= width and aligned_y + size <= height:
            tile = tileset.crop((aligned_x, aligned_y, aligned_x + size, aligned_y + size))
            tile_scaled = tile.resize((64, 64), Image.NEAREST)
            filename = f"tile_interpretation_{desc.replace(' ', '_')}.png"
            tile_scaled.save(filename)
            print(f"  Saved as: {filename}")
    
    # Create a visual guide showing the tile at (129, 10) in context
    context_size = 50
    context_x = max(0, 129 - context_size//2)
    context_y = max(0, 10 - context_size//2)
    
    context = tileset.crop((context_x, context_y, 
                           min(width, context_x + context_size), 
                           min(height, context_y + context_size)))
    
    # Draw a red box around (129, 10) with 8x8 size
    draw = ImageDraw.Draw(context)
    rel_x = 129 - context_x
    rel_y = 10 - context_y
    draw.rectangle([rel_x, rel_y, rel_x + 7, rel_y + 7], outline=(255, 0, 0), width=1)
    
    context_scaled = context.resize((context_size * 4, context_size * 4), Image.NEAREST)
    context_scaled.save("tile_at_129_10_context.png")
    
    print("\n\nCreated visualization files:")
    print("- separator_pattern_analysis.png: Overview of the area")
    print("- grid_pattern_*.png: Different grid interpretations")
    print("- tile_interpretation_*.png: Different ways to extract the tile")
    print("- tile_at_129_10_context.png: The specific tile in context (red box)")

if __name__ == "__main__":
    analyze_separator_pattern()
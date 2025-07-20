#!/usr/bin/env python3
"""
Recalibrate tile positions based on the correct PLAIN position
"""

from PIL import Image
import json

def recalibrate_positions():
    # The PLAIN tile was off by:
    # X: 238 - 216 = 22 pixels
    # Y: 18 - 26 = -8 pixels
    
    print("Recalibrating tile positions...")
    print("PLAIN tile correction: +22 in X, -8 in Y")
    
    # Load current mapping
    with open("aw2_mixed_tile_mapping.json", "r") as f:
        mapping = json.load(f)
    
    # Let's check the terrain section more carefully
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print("\nAnalyzing terrain section around correct PLAIN position...")
    
    # The terrain tiles seem to be on a 17x17 grid (16x16 tile + 1px separator)
    # Starting from PLAIN at (238, 18)
    terrain_start_x = 238
    terrain_start_y = 18
    grid_step = 17
    
    # Expected terrain tiles in order
    terrain_tiles = ['PLAIN', 'GRASS?', 'WOOD?', 'MOUNTAIN?']
    
    print("\nTerrain tiles on 17x17 grid:")
    for i in range(4):
        x = terrain_start_x + (i * grid_step)
        y = terrain_start_y
        
        if x + 16 <= tileset.width:
            tile = tileset.crop((x, y, x + 16, y + 16))
            pixels = list(tile.getdata())
            
            # Get dominant color
            color_sum = [0, 0, 0]
            count = 0
            for pixel in pixels:
                if len(pixel) >= 3 and (len(pixel) < 4 or pixel[3] > 0):
                    color_sum[0] += pixel[0]
                    color_sum[1] += pixel[1]
                    color_sum[2] += pixel[2]
                    count += 1
            
            if count > 0:
                avg_color = tuple(c // count for c in color_sum)
                r, g, b = avg_color
                
                # Guess tile type
                tile_type = "Unknown"
                if r > 180 and g > 180:  # Yellow/tan
                    tile_type = "PLAIN"
                elif g > r and g > b and g > 150:  # Green
                    tile_type = "GRASS/WOOD"
                elif abs(r - g) < 30 and abs(g - b) < 30 and r > 150:  # Gray
                    tile_type = "MOUNTAIN/ROCK"
                elif r > g and r > b:  # Brown/red
                    tile_type = "DIRT/DESERT"
                
                print(f"  Position ({x}, {y}): RGB{avg_color} - Likely: {tile_type}")
    
    # Check roads which might be in a different section
    print("\nChecking road positions...")
    # Roads were originally at (44, 26) - let's check if they need adjustment too
    road_positions = [
        (44, 26, "Original ROAD_HORT"),
        (44, 18, "Adjusted Y position"),
        (66, 18, "Possible adjusted position (+22 X, -8 Y)")
    ]
    
    for x, y, desc in road_positions:
        if x + 16 <= tileset.width and y + 16 <= tileset.height:
            tile = tileset.crop((x, y, x + 16, y + 16))
            pixels = list(tile.getdata())
            
            # Check for road-like colors (usually gray)
            gray_count = 0
            for pixel in pixels:
                if len(pixel) >= 3:
                    r, g, b = pixel[:3]
                    if abs(r - g) < 20 and abs(g - b) < 20 and 80 < r < 150:
                        gray_count += 1
            
            is_road = gray_count > len(pixels) * 0.3
            print(f"  {desc} at ({x}, {y}): {'Looks like road' if is_road else 'Not road'}")
    
    print("\nNext steps:")
    print("1. Update WOOD position (probably at 255, 18)")
    print("2. Update MOUNTAIN position (probably at 272, 18)")
    print("3. Check if road tiles need Y adjustment to 18")
    print("4. Buildings and water tiles might be in different sections, check separately")

if __name__ == "__main__":
    recalibrate_positions()
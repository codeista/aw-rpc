#!/usr/bin/env python3
"""
Check for pink border around the first column of water tile set
"""

from PIL import Image, ImageDraw
import json

def check_first_column_pink():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Water tiles at y=58 (we confirmed these are water)
    water_y = 58
    
    # Create visualization
    vis = Image.new('RGBA', (800, 400), (40, 40, 40, 255))
    
    # Get wider view to see what's before the water tiles
    area = tileset.crop((0, water_y - 10, 150, water_y + 30))
    area_scaled = area.resize((600, 160), Image.NEAREST)
    vis.paste(area_scaled, (100, 50))
    
    draw = ImageDraw.Draw(vis)
    draw.text((400, 20), "Water Tiles - Checking for pink border before first column", 
             fill=(255, 255, 255), anchor="mm")
    
    print(f"Checking for pink border before water tiles at y={water_y}:")
    
    # The water tiles start at x=0
    # Check if there's a pink border BEFORE x=0 (which would be at the edge)
    # Or if the pink border is meant to be drawn separately
    
    # Check the column at x=0 (first water column)
    print("\nFirst water tile column (x=0):")
    for dy in range(8):
        pixel = tileset.getpixel((0, water_y + dy))
        r, g, b, a = pixel
        if r > 200 and b > 200 and g < 150:
            print(f"  y+{dy}: PINK ({r},{g},{b})")
        else:
            print(f"  y+{dy}: Not pink ({r},{g},{b})")
    
    # Since we can't check x=-1, let's understand the pattern
    # Maybe the pink border is meant to be added programmatically
    
    # Let's also check if the water section has any pink pixels nearby
    print("\nChecking area around water tiles for pink pixels...")
    
    pink_locations = []
    
    # Check a wider area
    for y in range(max(0, water_y - 20), min(water_y + 40, tileset.height)):
        for x in range(0, 10):  # Just check first 10 columns
            pixel = tileset.getpixel((x, y))
            if pixel[0] > 200 and pixel[2] > 200 and pixel[1] < 150:
                pink_locations.append((x, y))
    
    if pink_locations:
        print(f"Found {len(pink_locations)} pink pixels near water area:")
        for x, y in pink_locations[:10]:  # Show first 10
            print(f"  Pink at ({x}, {y})")
        
        # Mark them on visualization
        for x, y in pink_locations:
            vis_x = 100 + x * 4
            vis_y = 50 + (y - (water_y - 10)) * 4
            if 0 <= vis_x < 800 and 0 <= vis_y < 400:
                draw.rectangle([vis_x-1, vis_y-1, vis_x+1, vis_y+1], 
                             fill=(255, 255, 0))
    
    # Draw guides
    # Mark where water tiles start
    water_start_x = 100  # In vis coordinates
    draw.line([(water_start_x, 50), (water_start_x, 210)], 
             fill=(0, 255, 0), width=2)
    draw.text((water_start_x, 220), "Water tiles start", 
             fill=(0, 255, 0), anchor="mm")
    
    # Understanding the description:
    # "pink/magenta border around the first column"
    # This might mean:
    # 1. A vertical pink line should be drawn at x=-1 (before tiles)
    # 2. The game engine adds this border when rendering
    # 3. The border is stored elsewhere in the tileset
    
    print("\nInterpretation:")
    print("The 'pink border around first column' likely means:")
    print("1. When rendering water/edge/beach tiles, add a 1px pink vertical line")
    print("2. This line goes BEFORE the first tile (at x=-1 relative to tile)")
    print("3. The actual tiles start at x=0 without pink in them")
    print("\nThis is probably a visual indicator in the tileset that should")
    print("be removed or handled specially when rendering in-game.")
    
    # Create a mock-up showing how it should look
    mock = Image.new('RGBA', (300, 100), (40, 40, 40, 255))
    mock_draw = ImageDraw.Draw(mock)
    
    # Draw pink border
    mock_draw.line([(49, 20), (49, 60)], fill=(255, 0, 255), width=1)
    
    # Draw water tiles
    for i in range(4):
        x = 50 + i * 30
        mock_draw.rectangle([x, 20, x + 24, 44], fill=(84, 109, 142), outline=(200, 200, 200))
        mock_draw.text((x + 12, 32), f"W{i+1}", fill=(255, 255, 255), anchor="mm")
    
    mock_draw.text((150, 70), "Pink border + Water tiles", fill=(255, 255, 255), anchor="mm")
    
    vis.paste(mock, (250, 250))
    
    vis.save("first_column_pink_border.png")
    print("\nCreated first_column_pink_border.png")

if __name__ == "__main__":
    check_first_column_pink()
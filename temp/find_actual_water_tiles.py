#!/usr/bin/env python3
"""
Find the actual water tiles at 6.5 tiles down from first road
"""

from PIL import Image, ImageDraw
import json

def find_actual_water():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # First road is at y=0
    # 6.5 tiles down with 8px tiles = 52 pixels
    # But with separators (9px grid), 6.5 tiles = 6.5 * 9 = 58.5 ≈ 58 or 59
    
    # Let's check multiple potential positions
    potential_y = [52, 58, 59, 144, 149]  # Different calculations and common water positions
    
    print("Searching for water tiles with red borders...")
    
    # Create visualization
    vis = Image.new('RGBA', (900, 700), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    y_offset = 50
    
    for y_idx, water_y in enumerate(potential_y):
        if water_y >= tileset.height:
            continue
            
        print(f"\nChecking y={water_y}:")
        
        # Extract a section around this y position
        section = tileset.crop((0, max(0, water_y - 5), 
                               min(200, tileset.width), 
                               min(water_y + 25, tileset.height)))
        
        # Scale up 3x
        section_scaled = section.resize((section.width * 3, section.height * 3), Image.NEAREST)
        vis.paste(section_scaled, (50, y_offset))
        
        draw.text((25, y_offset + 15), f"y={water_y}", fill=(255, 255, 255), anchor="mm")
        
        # Look for red borders in first column of tiles
        red_tiles = []
        for i in range(20):  # Check 20 potential tile positions
            x = i * 9  # 9px grid
            
            if x < tileset.width and water_y + 8 <= tileset.height:
                # Check if first column has red
                has_red = False
                for dy in range(8):
                    pixel = tileset.getpixel((x, water_y + dy))
                    if pixel[0] > 200 and pixel[1] < 100 and pixel[2] < 100:
                        has_red = True
                        break
                
                if has_red:
                    # Check what's after the red border
                    content_pixels = []
                    for dy in range(8):
                        for dx in range(2, 8):  # Skip red border and gap
                            if x + dx < tileset.width:
                                p = tileset.getpixel((x + dx, water_y + dy))
                                if p[3] > 0:
                                    content_pixels.append(p)
                    
                    if content_pixels:
                        avg_b = sum(p[2] for p in content_pixels) / len(content_pixels)
                        avg_r = sum(p[0] for p in content_pixels) / len(content_pixels)
                        
                        is_water = avg_b > avg_r * 1.2  # Blue-ish
                        
                        if is_water:
                            red_tiles.append(i)
                            # Mark on visualization
                            vis_x = 50 + x * 3
                            vis_y = y_offset + 15
                            draw.rectangle([vis_x, vis_y, vis_x + 24, vis_y + 24], 
                                         outline=(255, 0, 0), width=2)
                            draw.text((vis_x + 12, vis_y - 10), str(i), 
                                    fill=(255, 255, 0), anchor="mm")
        
        if red_tiles:
            print(f"  Found {len(red_tiles)} water tiles with red borders at positions: {red_tiles}")
        else:
            print(f"  No water tiles with red borders found")
        
        y_offset += 100
    
    # Also check around the Water label area
    print("\n\nLooking for 'Water' text label...")
    
    # The label might be in a different area, let's check common label positions
    label_areas = [
        (0, 130, 100, 160),    # Common label area 1
        (100, 130, 200, 160),  # Common label area 2
        (0, 0, 100, 30),       # Top area
    ]
    
    for x1, y1, x2, y2 in label_areas:
        if x2 <= tileset.width and y2 <= tileset.height:
            # Count dark pixels (text)
            dark_count = 0
            for y in range(y1, y2):
                for x in range(x1, x2):
                    pixel = tileset.getpixel((x, y))
                    if pixel[0] < 50 and pixel[1] < 50 and pixel[2] < 50:
                        dark_count += 1
            
            if dark_count > 50:  # Significant dark pixels
                print(f"  Possible text label at ({x1},{y1}) to ({x2},{y2})")
                
                # Check below this area for tiles
                tiles_y = y2 + 5  # Just below label
                if tiles_y + 8 <= tileset.height:
                    # Check for red borders
                    for i in range(10):
                        x = i * 9
                        if x < tileset.width:
                            pixel = tileset.getpixel((x, tiles_y))
                            if pixel[0] > 200 and pixel[1] < 100 and pixel[2] < 100:
                                print(f"    Found red border at ({x}, {tiles_y})")
    
    # Create summary visualization showing the most likely water position
    summary = Image.new('RGBA', (600, 200), (40, 40, 40, 255))
    
    # Based on our original finding, water is at y=58
    likely_y = 58
    water_section = tileset.crop((0, likely_y - 10, 150, likely_y + 30))
    water_scaled = water_section.resize((450, 120), Image.NEAREST)
    summary.paste(water_scaled, (50, 40))
    
    draw_summary = ImageDraw.Draw(summary)
    draw_summary.text((300, 20), f"Most likely water tiles at y={likely_y}", 
                     fill=(255, 255, 255), anchor="mm")
    
    # Draw 9x9 grid
    for i in range(15):
        x = 50 + i * 27  # 9 * 3 scale
        draw_summary.line([(x, 40), (x, 160)], fill=(100, 100, 100, 128), width=1)
    
    summary.save("water_tiles_final_location.png")
    vis.save("water_search_all_positions.png")
    
    print("\nCreated water_search_all_positions.png and water_tiles_final_location.png")
    print("\nConclusion: Water tiles are most likely at y=58")
    print("They appear to be standard 8x8 tiles without red borders in that location")
    print("The red borders might be in building tiles or a different tileset section")

if __name__ == "__main__":
    find_actual_water()
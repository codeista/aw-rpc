#!/usr/bin/env python3
"""
Find the Water label and the tiles with red borders below it
"""

from PIL import Image, ImageDraw
import json

def find_water_label_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # The water tiles we found at y=58 might be something else
    # Let's search for "Water" label text and look below it
    
    # Create visualization of larger area
    vis = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    
    # Look at a larger vertical section to find the Water label
    # Water label is probably written in darker pixels
    
    # Scan for areas with text-like patterns (many dark pixels in a row)
    print("Scanning for Water label...")
    
    # Check different y positions for potential label locations
    for y in range(0, min(300, tileset.height), 10):
        dark_pixels = 0
        for x in range(0, min(100, tileset.width)):
            pixel = tileset.getpixel((x, y))
            # Text is usually dark
            if pixel[0] < 50 and pixel[1] < 50 and pixel[2] < 50 and pixel[3] > 200:
                dark_pixels += 1
        
        if dark_pixels > 20:  # Might be text
            print(f"Potential text at y={y} ({dark_pixels} dark pixels)")
    
    # Let's check specific areas where water tiles with red borders might be
    # Based on your description, let's look further down
    
    # Check multiple sections
    sections_to_check = [
        (0, 100, 200, 200, "Section 1: y=100-200"),
        (0, 140, 300, 240, "Section 2: y=140-240 (Water label area?)"),
        (0, 180, 300, 280, "Section 3: y=180-280"),
    ]
    
    for i, (x1, y1, x2, y2, label) in enumerate(sections_to_check):
        if y2 <= tileset.height and x2 <= tileset.width:
            section = tileset.crop((x1, y1, x2, y2))
            vis.paste(section, (50 + i * 250, 50))
            
            draw = ImageDraw.Draw(vis)
            draw.text((50 + i * 250 + 100, 30), label, fill=(255, 255, 255), anchor="mm")
            
            # Look for red pixels in this section
            for y in range(y1, y2):
                for x in range(x1, min(x1 + 100, x2)):
                    pixel = tileset.getpixel((x, y))
                    r, g, b, a = pixel
                    
                    # Check for red border
                    if r > 200 and g < 100 and b < 100:
                        # Found red pixel, mark it
                        vis_x = 50 + i * 250 + (x - x1)
                        vis_y = 50 + (y - y1)
                        draw.rectangle([vis_x-1, vis_y-1, vis_x+1, vis_y+1], 
                                     fill=(255, 255, 0))
                        
                        print(f"Found red pixel at ({x}, {y}) in {label}")
    
    # Let's specifically check around y=144 which is a common position for water tiles
    print("\nChecking specific water tile area around y=144...")
    
    water_area = tileset.crop((0, 140, 400, 180))
    water_scaled = water_area.resize((800, 80), Image.NEAREST)
    vis.paste(water_scaled, (0, 350))
    
    draw = ImageDraw.Draw(vis)
    draw.text((400, 340), "Zoomed 2x: Potential Water tile area", fill=(255, 255, 255), anchor="mm")
    
    # Check for red borders in this area
    for y in range(140, 180):
        for x in range(0, 100):
            pixel = tileset.getpixel((x, y))
            r, g, b, a = pixel
            
            if r > 200 and g < 100 and b < 100:
                print(f"Red border found at ({x}, {y})")
                
                # Check what's after the red border
                if x + 2 < tileset.width:
                    next_pixel = tileset.getpixel((x + 2, y))
                    if next_pixel[2] > next_pixel[0]:  # More blue
                        print(f"  -> Likely water tile starting at x={x+2}")
    
    vis.save("water_label_search.png")
    print("\nCreated water_label_search.png")
    print("Yellow dots mark red pixels found")

if __name__ == "__main__":
    find_water_label_tiles()
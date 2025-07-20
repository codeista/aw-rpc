#!/usr/bin/env python3
"""
Examine the red border more closely
"""

from PIL import Image, ImageDraw
import json

def examine_red_border():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Water starts at y=58
    water_y = 58
    
    # Create detailed view
    vis = Image.new('RGBA', (800, 400), (40, 40, 40, 255))
    
    # Get a zoomed view of the first water tile area
    # Extract 20x20 area around first water tile
    sample = tileset.crop((0, water_y, 100, water_y + 20))
    
    # Scale up 10x for detailed view
    sample_scaled = sample.resize((1000, 200), Image.NEAREST)
    vis.paste(sample_scaled, (0, 0))
    
    draw = ImageDraw.Draw(vis)
    
    # Draw grid lines every 10 pixels (representing 1 pixel in original)
    for x in range(0, 1000, 10):
        draw.line([(x, 0), (x, 200)], fill=(100, 100, 100, 128), width=1)
    for y in range(0, 200, 10):
        draw.line([(0, y), (1000, y)], fill=(100, 100, 100, 128), width=1)
    
    # Mark expected tile boundaries (9px apart)
    for i in range(10):
        x = i * 90  # 9 pixels * 10x scale
        draw.line([(x, 0), (x, 200)], fill=(255, 255, 0, 128), width=2)
    
    # Analyze first tile column by column
    print("Analyzing first water tile pixel by pixel:")
    print("(Looking at first 10 pixels of first row)")
    
    for x in range(10):
        pixel = tileset.getpixel((x, water_y))
        r, g, b, a = pixel
        
        # Categorize pixel
        if r > 200 and g < 100 and b < 100:
            pixel_type = "RED BORDER"
            color = (255, 0, 0)
        elif abs(r - 149) < 20 and abs(g - 177) < 20 and abs(b - 200) < 20:
            pixel_type = "SEPARATOR"
            color = (200, 200, 200)
        elif a == 0:
            pixel_type = "TRANSPARENT"
            color = (255, 0, 255)
        elif b > r and b > g:
            pixel_type = "WATER"
            color = (0, 200, 255)
        else:
            pixel_type = "OTHER"
            color = (255, 255, 255)
        
        print(f"  x={x}: RGB({r},{g},{b}) A={a} - {pixel_type}")
        
        # Mark on visualization
        draw.text((x * 10 + 5, 210), str(x), fill=color, anchor="mm")
        draw.rectangle([x * 10, 220, x * 10 + 10, 240], fill=color)
    
    # Let's also check a few rows down
    print("\nChecking 5 pixels down:")
    for x in range(10):
        pixel = tileset.getpixel((x, water_y + 5))
        r, g, b, a = pixel
        
        if r > 200 and g < 100 and b < 100:
            print(f"  x={x}: RED")
        elif b > r and b > g:
            print(f"  x={x}: WATER")
        else:
            print(f"  x={x}: OTHER ({r},{g},{b})")
    
    # Add labels
    draw.text((400, 250), "Zoomed 10x view of water tiles", fill=(255, 255, 255), anchor="mm")
    draw.text((400, 270), "Yellow lines = Expected 9px tile boundaries", fill=(255, 255, 0), anchor="mm")
    draw.text((400, 290), "Bottom row shows pixel types:", fill=(255, 255, 255), anchor="mm")
    draw.text((400, 310), "RED=Border, BLUE=Water, GRAY=Separator, MAGENTA=Transparent", fill=(255, 255, 255), anchor="mm")
    
    # Check the actual water content bounds
    print("\nFinding actual water content bounds in first tile:")
    
    # Find first water pixel
    first_water_x = None
    last_water_x = None
    
    for x in range(20):
        has_water = False
        for y in range(water_y, water_y + 8):
            pixel = tileset.getpixel((x, y))
            if pixel[2] > pixel[0] and pixel[2] > pixel[1] and pixel[3] > 0:  # Blue and not transparent
                has_water = True
                if first_water_x is None:
                    first_water_x = x
                last_water_x = x
                break
    
    if first_water_x is not None:
        print(f"Water content starts at x={first_water_x}")
        print(f"Water content ends at x={last_water_x}")
        print(f"Water content width: {last_water_x - first_water_x + 1} pixels")
        
        # Draw the actual bounds
        draw.rectangle([first_water_x * 10, 350, (last_water_x + 1) * 10, 370], 
                      fill=(0, 200, 255), outline=(255, 255, 255))
        draw.text((200, 360), f"Actual water: x={first_water_x} to x={last_water_x}", 
                 fill=(255, 255, 255), anchor="mm")
    
    vis.save("red_border_detail.png")
    print("\nCreated red_border_detail.png with detailed pixel analysis")

if __name__ == "__main__":
    examine_red_border()
#!/usr/bin/env python3
"""
Inspect the pipe area to see what colors are there
"""

from PIL import Image, ImageDraw
import json

def inspect_pipe_area():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Pipes start after roads (8 columns)
    pipe_start_x = 8 * 9  # 72
    pipe_start_y = 0
    
    print(f"Inspecting pipe area starting at ({pipe_start_x}, {pipe_start_y})")
    
    # Check first few tiles to understand the colors
    print("\nColor analysis of first few pipe positions:")
    
    for row in range(2):
        for col in range(2):
            x = pipe_start_x + col * 9
            y = pipe_start_y + row * 9
            
            print(f"\nPosition ({row},{col}) at pixel ({x},{y}):")
            
            # Get color statistics
            colors = {}
            
            for dy in range(8):
                for dx in range(8):
                    pixel = tileset.getpixel((x + dx, y + dy))
                    r, g, b, a = pixel
                    
                    # Categorize color
                    if abs(r - 149) < 20 and abs(g - 177) < 20 and abs(b - 200) < 20:
                        color_type = "SEPARATOR"
                    elif r > 200 and b > 200 and g < 150:
                        color_type = "PINK"
                    elif a == 0:
                        color_type = "TRANSPARENT"
                    elif r < 50 and g < 50 and b < 50:
                        color_type = "BLACK"
                    elif 50 < r < 100 and 50 < g < 100 and 50 < b < 100:
                        color_type = "DARK_GREY"
                    elif 100 < r < 150 and 100 < g < 150 and 100 < b < 150:
                        color_type = "LIGHT_GREY"
                    elif g > r and g > b:
                        color_type = "GREEN"
                    elif abs(r - g) < 20 and abs(g - b) < 20:
                        color_type = "GREY"
                    else:
                        color_type = f"OTHER({r},{g},{b})"
                    
                    colors[color_type] = colors.get(color_type, 0) + 1
            
            # Print color distribution
            for color_type, count in sorted(colors.items(), key=lambda x: -x[1]):
                if count > 0:
                    print(f"  {color_type}: {count} pixels")
    
    # Create visual inspection
    vis = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    
    # Show larger area to see pipe section
    area = tileset.crop((pipe_start_x - 10, 0, pipe_start_x + 100, 50))
    area_scaled = area.resize((area.width * 4, area.height * 4), Image.NEAREST)
    vis.paste(area_scaled, (50, 50))
    
    draw = ImageDraw.Draw(vis)
    draw.text((400, 20), "Pipe Section Inspection", fill=(255, 255, 255), anchor="mm")
    
    # Mark pipe start
    pipe_vis_x = 50 + 10 * 4  # Account for -10 offset
    draw.line([(pipe_vis_x, 50), (pipe_vis_x, 250)], fill=(255, 255, 0), width=2)
    draw.text((pipe_vis_x, 260), "Pipes start", fill=(255, 255, 0), anchor="mm")
    
    # Draw grid
    for i in range(12):  # Columns
        x = 50 + i * 36  # 9 * 4 scale
        draw.line([(x, 50), (x, 250)], fill=(80, 80, 80), width=1)
    
    vis.save("pipe_area_inspection.png")
    print("\nCreated pipe_area_inspection.png")

if __name__ == "__main__":
    inspect_pipe_area()
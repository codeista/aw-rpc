#!/usr/bin/env python3
"""
Analyze the road tile area to find correct tile sizes and grid spacing
"""

from PIL import Image, ImageDraw
import json

def analyze_road_area():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Starting point given by user
    start_x = 12
    start_y = 19
    
    # Create visualization
    vis = Image.new('RGBA', (1200, 800), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    # Extract a larger area around the first road tile
    area_x = start_x - 5
    area_y = start_y - 5
    area_width = 150
    area_height = 100
    
    area = tileset.crop((area_x, area_y, area_x + area_width, area_y + area_height))
    area_scaled = area.resize((area.width * 4, area.height * 4), Image.NEAREST)
    vis.paste(area_scaled, (50, 50))
    
    # Draw grid lines at the start position
    grid_x = 50 + (start_x - area_x) * 4
    grid_y = 50 + (start_y - area_y) * 4
    
    # Highlight the first tile area
    draw.rectangle([grid_x, grid_y, grid_x + 60, grid_y + 60], outline=(255, 255, 0), width=2)
    draw.text((grid_x + 30, grid_y - 10), "First tile", fill=(255, 255, 0), anchor="mm")
    
    # Analyze for separator lines
    separator_color = (149, 177, 200)  # Light blue/grey
    
    print(f"Analyzing road area starting at ({start_x}, {start_y})")
    print("\nLooking for separator lines...")
    
    # Find horizontal separators
    h_separators = []
    for y in range(start_y, min(start_y + 80, tileset.height)):
        # Check if this row is mostly separator color
        sep_count = 0
        for x in range(start_x, min(start_x + 130, tileset.width)):
            pixel = tileset.getpixel((x, y))
            if len(pixel) >= 3:
                r, g, b = pixel[:3]
                if abs(r - separator_color[0]) < 15 and abs(g - separator_color[1]) < 15 and abs(b - separator_color[2]) < 15:
                    sep_count += 1
        
        if sep_count > 80:  # Most of the row is separator
            h_separators.append(y)
            # Draw on visualization
            vis_y = 50 + (y - area_y) * 4
            draw.line([(50, vis_y), (50 + area_width * 4, vis_y)], fill=(0, 255, 0), width=1)
    
    # Find vertical separators
    v_separators = []
    for x in range(start_x, min(start_x + 130, tileset.width)):
        # Check if this column is mostly separator color
        sep_count = 0
        for y in range(start_y, min(start_y + 80, tileset.height)):
            pixel = tileset.getpixel((x, y))
            if len(pixel) >= 3:
                r, g, b = pixel[:3]
                if abs(r - separator_color[0]) < 15 and abs(g - separator_color[1]) < 15 and abs(b - separator_color[2]) < 15:
                    sep_count += 1
        
        if sep_count > 40:  # Most of the column is separator
            v_separators.append(x)
            # Draw on visualization
            vis_x = 50 + (x - area_x) * 4
            draw.line([(vis_x, 50), (vis_x, 50 + area_height * 4)], fill=(0, 255, 0), width=1)
    
    print(f"\nHorizontal separators found: {h_separators[:5]}")
    print(f"Vertical separators found: {v_separators[:5]}")
    
    # Calculate tile sizes
    if len(h_separators) >= 2:
        tile_height = h_separators[1] - h_separators[0] - 1
        print(f"\nTile height (between separators): {tile_height}")
    else:
        # Try to find next content after first tile
        for y in range(start_y + 15, min(start_y + 20, tileset.height)):
            has_separator = True
            for x in range(start_x, start_x + 15):
                pixel = tileset.getpixel((x, y))
                if not (abs(pixel[0] - separator_color[0]) < 15 and 
                       abs(pixel[1] - separator_color[1]) < 15 and 
                       abs(pixel[2] - separator_color[2]) < 15):
                    has_separator = False
                    break
            if has_separator:
                tile_height = y - start_y
                print(f"\nTile height (to separator): {tile_height}")
                break
    
    if len(v_separators) >= 2:
        tile_width = v_separators[1] - v_separators[0] - 1
        print(f"Tile width (between separators): {tile_width}")
    else:
        # Try to find next content after first tile
        for x in range(start_x + 15, min(start_x + 20, tileset.width)):
            has_separator = True
            for y in range(start_y, start_y + 15):
                pixel = tileset.getpixel((x, y))
                if not (abs(pixel[0] - separator_color[0]) < 15 and 
                       abs(pixel[1] - separator_color[1]) < 15 and 
                       abs(pixel[2] - separator_color[2]) < 15):
                    has_separator = False
                    break
            if has_separator:
                tile_width = x - start_x
                print(f"Tile width (to separator): {tile_width}")
                break
    
    # Check actual content bounds of first tile
    print("\nAnalyzing first tile content bounds...")
    min_x, max_x = start_x + 15, start_x
    min_y, max_y = start_y + 15, start_y
    
    for y in range(start_y, start_y + 16):
        for x in range(start_x, start_x + 16):
            if x < tileset.width and y < tileset.height:
                pixel = tileset.getpixel((x, y))
                # Check if not separator and has content
                if not (abs(pixel[0] - separator_color[0]) < 15 and 
                       abs(pixel[1] - separator_color[1]) < 15 and 
                       abs(pixel[2] - separator_color[2]) < 15) and pixel[3] > 0:
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)
    
    content_width = max_x - min_x + 1
    content_height = max_y - min_y + 1
    print(f"Content bounds: ({min_x}, {min_y}) to ({max_x}, {max_y})")
    print(f"Content size: {content_width}x{content_height}")
    
    # Draw content bounds
    content_x = 50 + (min_x - area_x) * 4
    content_y = 50 + (min_y - area_y) * 4
    content_w = content_width * 4
    content_h = content_height * 4
    draw.rectangle([content_x, content_y, content_x + content_w, content_y + content_h], 
                  outline=(255, 0, 0), width=2)
    
    # Info text
    draw.text((700, 50), "Road Tile Analysis", fill=(255, 255, 255))
    draw.text((700, 80), f"First tile at: ({start_x}, {start_y})", fill=(200, 200, 200))
    draw.text((700, 100), f"Content size: {content_width}x{content_height}", fill=(200, 200, 200))
    draw.text((700, 130), "Green lines = Separators", fill=(0, 255, 0))
    draw.text((700, 150), "Yellow box = Expected 15x15", fill=(255, 255, 0))
    draw.text((700, 170), "Red box = Actual content", fill=(255, 0, 0))
    
    if h_separators and v_separators:
        grid_width = v_separators[1] - v_separators[0] if len(v_separators) > 1 else 0
        grid_height = h_separators[1] - h_separators[0] if len(h_separators) > 1 else 0
        draw.text((700, 200), f"Grid spacing: {grid_width}x{grid_height}", fill=(200, 200, 200))
    
    vis.save("road_area_analysis.png")
    print("\nCreated road_area_analysis.png")

if __name__ == "__main__":
    analyze_road_area()
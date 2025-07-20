#!/usr/bin/env python3
"""
Check if the first water tile at y=58 has a pink border
"""

from PIL import Image, ImageDraw
import json

def check_first_water_tile():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Water tiles at y=58
    water_y = 58
    
    # Create detailed visualization
    vis = Image.new('RGBA', (800, 400), (40, 40, 40, 255))
    
    # Get water tile area - zoom in on first few tiles
    area = tileset.crop((0, water_y - 2, 100, water_y + 10))
    
    # Scale up 10x for pixel-level view
    area_scaled = area.resize((1000, 120), Image.NEAREST)
    vis.paste(area_scaled, (0, 50))
    
    draw = ImageDraw.Draw(vis)
    draw.text((400, 20), "First Water Tile - Pixel Analysis (10x zoom)", fill=(255, 255, 255), anchor="mm")
    
    # Analyze first tile pixel by pixel
    print(f"Analyzing first water tile at y={water_y}:")
    print("First 10 columns:")
    
    for x in range(10):
        col_info = []
        
        for y in range(water_y, water_y + 8):
            if y < tileset.height:
                pixel = tileset.getpixel((x, y))
                r, g, b, a = pixel
                
                # Categorize pixel
                if r > 200 and b > 200 and g < 150:
                    pixel_type = "PINK"
                elif abs(r - 149) < 20 and abs(g - 177) < 20 and abs(b - 200) < 20:
                    pixel_type = "SEP"
                elif b > r and b > g:
                    pixel_type = "WATER"
                else:
                    pixel_type = "OTHER"
                
                col_info.append(pixel_type)
        
        # Summary for this column
        types = set(col_info)
        if "PINK" in types:
            print(f"  x={x}: PINK COLUMN")
        elif "WATER" in types:
            print(f"  x={x}: WATER")
        elif "SEP" in types:
            print(f"  x={x}: SEPARATOR")
        else:
            print(f"  x={x}: {col_info[0]}")
        
        # Draw column markers
        for i, ptype in enumerate(col_info):
            y_pos = 50 + 20 + i * 10
            x_pos = x * 10 + 5
            
            if ptype == "PINK":
                color = (255, 0, 255)
            elif ptype == "WATER":
                color = (0, 150, 255)
            elif ptype == "SEP":
                color = (150, 150, 150)
            else:
                color = (255, 255, 255)
            
            draw.rectangle([x_pos - 2, y_pos - 2, x_pos + 2, y_pos + 2], fill=color)
    
    # Draw grid
    for x in range(0, 100, 10):
        draw.line([(x, 50), (x, 170)], fill=(100, 100, 100, 128), width=1)
        draw.text((x + 5, 180), str(x // 10), fill=(255, 255, 255), anchor="mm")
    
    # Check if the very first water frame has pink border
    print("\nChecking all 4 water animation frames:")
    
    for frame in range(4):
        frame_x = frame * 9  # Each frame 9px apart
        
        # Check first column of this frame
        pink_count = 0
        for dy in range(8):
            p = tileset.getpixel((frame_x, water_y + dy))
            if p[0] > 200 and p[2] > 200 and p[1] < 150:
                pink_count += 1
        
        if pink_count > 0:
            print(f"  Frame {frame} at x={frame_x}: {pink_count} pink pixels in first column!")
        else:
            print(f"  Frame {frame} at x={frame_x}: No pink border")
    
    # Also check the column just before first tile
    if water_y > 0:
        print(f"\nChecking column before first tile (x=-1 equivalent):")
        # Since we can't check x=-1, check what's at the edge
        edge_pixels = []
        for dy in range(8):
            p = tileset.getpixel((0, water_y + dy))
            edge_pixels.append(p)
        
        # Check if edge has water characteristics
        avg_b = sum(p[2] for p in edge_pixels) / len(edge_pixels)
        avg_r = sum(p[0] for p in edge_pixels) / len(edge_pixels)
        
        if avg_b > avg_r:
            print("  Edge is water-colored (no pink border on first tile)")
        else:
            print("  Edge is not water-colored")
    
    # Add legend
    draw.text((50, 220), "Column Analysis:", fill=(255, 255, 255))
    draw.rectangle([50, 240, 60, 250], fill=(255, 0, 255))
    draw.text((70, 245), "Pink/Magenta", fill=(255, 0, 255), anchor="lm")
    draw.rectangle([50, 260, 60, 270], fill=(0, 150, 255))
    draw.text((70, 265), "Water (blue)", fill=(0, 150, 255), anchor="lm")
    draw.rectangle([50, 280, 60, 290], fill=(150, 150, 150))
    draw.text((70, 285), "Separator", fill=(150, 150, 150), anchor="lm")
    
    # Summary
    draw.text((50, 320), "If first column (x=0) has pink pixels, then water tiles have pink border", 
             fill=(255, 255, 255))
    draw.text((50, 340), "Otherwise, pink border might be only on edge/beach tiles", 
             fill=(255, 255, 255))
    
    vis.save("first_water_tile_analysis.png")
    print("\nCreated first_water_tile_analysis.png")

if __name__ == "__main__":
    check_first_water_tile()
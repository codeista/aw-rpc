#!/usr/bin/env python3
"""
Find water tiles with pink/magenta borders
"""

from PIL import Image, ImageDraw
import json

def find_pink_border_water():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # Look for pink/magenta pixels (high red, high blue, low green)
    def is_pink_magenta(pixel):
        r, g, b, a = pixel
        return r > 200 and b > 200 and g < 150 and a > 200
    
    # Create visualization
    vis = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    # Scan for areas with pink/magenta
    print("Scanning for pink/magenta borders...")
    
    pink_areas = []
    
    # Check multiple y positions
    for y in range(0, min(200, tileset.height), 5):
        for x in range(0, min(200, tileset.width), 5):
            # Check if this position has pink
            if x < tileset.width and y < tileset.height:
                pixel = tileset.getpixel((x, y))
                if is_pink_magenta(pixel):
                    # Check if this could be a border (vertical line of pink)
                    pink_count = 0
                    for dy in range(8):
                        if y + dy < tileset.height:
                            p = tileset.getpixel((x, y + dy))
                            if is_pink_magenta(p):
                                pink_count += 1
                    
                    if pink_count >= 4:  # Significant vertical pink
                        pink_areas.append((x, y))
    
    print(f"Found {len(pink_areas)} areas with pink/magenta")
    
    # Group by y coordinate to find rows
    y_groups = {}
    for x, y in pink_areas:
        y_key = y // 10 * 10
        if y_key not in y_groups:
            y_groups[y_key] = []
        y_groups[y_key].append(x)
    
    # Find rows with multiple pink borders (likely tile rows)
    print("\nRows with pink borders:")
    water_candidates = []
    
    for y_key, x_positions in sorted(y_groups.items()):
        if len(x_positions) >= 3:  # Multiple tiles
            print(f"  y≈{y_key}: {len(x_positions)} pink borders at x={sorted(x_positions)[:5]}...")
            water_candidates.append(y_key)
    
    # Examine the most promising candidate
    if water_candidates:
        check_y = water_candidates[0]
        print(f"\nExamining tiles at y≈{check_y} in detail:")
        
        # Get exact y by checking around the approximate position
        exact_y = None
        for y in range(max(0, check_y - 5), min(check_y + 15, tileset.height)):
            # Check if there's a pink pixel at x=0 (or near start)
            for x in range(20):
                if is_pink_magenta(tileset.getpixel((x, y))):
                    exact_y = y
                    break
            if exact_y:
                break
        
        if exact_y:
            print(f"Exact pink border starts at y={exact_y}")
            
            # Extract and scale this area
            area = tileset.crop((0, max(0, exact_y - 5), 200, min(exact_y + 25, tileset.height)))
            area_scaled = area.resize((600, 90), Image.NEAREST)
            vis.paste(area_scaled, (50, 50))
            
            draw.text((400, 30), f"Water tiles with pink borders at y={exact_y}", 
                     fill=(255, 255, 255), anchor="mm")
            
            # Analyze tile structure
            tiles_info = []
            
            for i in range(15):  # Check 15 potential tiles
                x = i * 9  # 9px grid
                
                if x + 8 < tileset.width:
                    # Check first column for pink
                    has_pink = False
                    for dy in range(8):
                        if exact_y + dy < tileset.height:
                            p = tileset.getpixel((x, exact_y + dy))
                            if is_pink_magenta(p):
                                has_pink = True
                                break
                    
                    if has_pink:
                        # Analyze content after pink border
                        # Check at x+1 (gap) and x+2 (start of content)
                        gap_pixel = tileset.getpixel((x + 1, exact_y)) if x + 1 < tileset.width else (0,0,0,0)
                        content_pixels = []
                        
                        for dy in range(8):
                            for dx in range(2, 8):
                                if x + dx < tileset.width and exact_y + dy < tileset.height:
                                    p = tileset.getpixel((x + dx, exact_y + dy))
                                    if p[3] > 0:
                                        content_pixels.append(p)
                        
                        content_type = "UNKNOWN"
                        if content_pixels:
                            avg_r = sum(p[0] for p in content_pixels) / len(content_pixels)
                            avg_g = sum(p[1] for p in content_pixels) / len(content_pixels)
                            avg_b = sum(p[2] for p in content_pixels) / len(content_pixels)
                            
                            if avg_b > avg_r * 1.3:
                                content_type = "WATER"
                            elif avg_r > 180 and avg_g > 150:
                                content_type = "BEACH"
                            else:
                                content_type = f"OTHER({int(avg_r)},{int(avg_g)},{int(avg_b)})"
                        
                        tiles_info.append({
                            'index': i,
                            'x': x,
                            'has_pink': has_pink,
                            'gap_is_transparent': gap_pixel[3] < 100,
                            'content_type': content_type
                        })
                        
                        # Mark on visualization
                        vis_x = 50 + x * 3
                        vis_y = 50 + 15
                        
                        # Pink border line
                        draw.line([(vis_x, vis_y), (vis_x, vis_y + 24)], 
                                fill=(255, 0, 255), width=3)
                        
                        # Content area
                        draw.rectangle([vis_x + 6, vis_y, vis_x + 24, vis_y + 24], 
                                     outline=(0, 255, 255), width=2)
                        
                        # Label
                        draw.text((vis_x + 12, vis_y - 10), str(i), 
                                fill=(255, 255, 255), anchor="mm")
            
            print(f"\nFound {len(tiles_info)} tiles with pink borders:")
            for tile in tiles_info:
                print(f"  Tile {tile['index']} at x={tile['x']}: {tile['content_type']}")
            
            # Add legend
            draw.text((50, 200), "Pink/Magenta borders found!", fill=(255, 0, 255))
            draw.text((50, 220), "Pink lines = 1px pink border", fill=(255, 0, 255))
            draw.text((50, 240), "Cyan boxes = Tile content area (6x8)", fill=(0, 255, 255))
            draw.text((50, 260), "These are the water/edge/beach tiles", fill=(255, 255, 255))
    
    else:
        # Try looking at the previously identified water position
        print("\nChecking y=58 for pink borders...")
        y = 58
        
        area = tileset.crop((0, y - 5, 150, y + 25))
        area_scaled = area.resize((450, 90), Image.NEAREST)
        vis.paste(area_scaled, (50, 50))
        
        for x in range(0, 100, 9):
            for dy in range(8):
                if y + dy < tileset.height and x < tileset.width:
                    p = tileset.getpixel((x, y + dy))
                    if is_pink_magenta(p):
                        print(f"Pink pixel at ({x}, {y + dy})")
                        # Mark it
                        vis_x = 50 + x * 3
                        vis_y = 50 + 15 + dy * 3
                        draw.rectangle([vis_x-1, vis_y-1, vis_x+1, vis_y+1], 
                                     fill=(255, 255, 0))
    
    vis.save("water_pink_borders.png")
    print("\nCreated water_pink_borders.png")

if __name__ == "__main__":
    find_pink_border_water()
#!/usr/bin/env python3
"""
Check the y=20 row where we found actual red borders
"""

from PIL import Image, ImageDraw
import json

def check_y20_water():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # From search results, red borders were found at y=20, starting around x=489
    y = 20
    
    # Create detailed visualization
    vis = Image.new('RGBA', (800, 400), (40, 40, 40, 255))
    
    # Extract wider area to see the pattern
    area = tileset.crop((480, 10, 650, 50))
    area_scaled = area.resize((680, 160), Image.NEAREST)
    vis.paste(area_scaled, (50, 50))
    
    draw = ImageDraw.Draw(vis)
    draw.text((400, 20), "Water/Edge/Beach Tiles with Red Borders (y=20)", fill=(255, 255, 255), anchor="mm")
    
    # Check tile pattern starting from x=489 (where red was found)
    base_x = 489
    
    print(f"Analyzing tiles at y={y} starting from x={base_x}:")
    
    tiles_found = []
    
    for i in range(12):  # Check more tiles to see edge/beach
        x = base_x + i * 9  # 9px grid (8px tile + 1px separator)
        
        if x + 8 < tileset.width:
            # Check first column for red
            red_found = False
            for check_y in range(y, y + 8):
                pixel = tileset.getpixel((x, check_y))
                if pixel[0] > 200 and pixel[1] < 100 and pixel[2] < 100:
                    red_found = True
                    break
            
            # Check content after red border and gap
            content_type = "UNKNOWN"
            if x + 2 < tileset.width:
                # Sample a few pixels to determine type
                sample_pixels = []
                for sy in range(y, min(y + 8, tileset.height)):
                    for sx in range(x + 2, min(x + 8, tileset.width)):
                        p = tileset.getpixel((sx, sy))
                        if p[3] > 0:  # Not transparent
                            sample_pixels.append(p)
                
                if sample_pixels:
                    # Average color
                    avg_r = sum(p[0] for p in sample_pixels) / len(sample_pixels)
                    avg_g = sum(p[1] for p in sample_pixels) / len(sample_pixels)
                    avg_b = sum(p[2] for p in sample_pixels) / len(sample_pixels)
                    
                    if avg_b > avg_r and avg_b > avg_g:
                        content_type = "WATER/SEA"
                    elif avg_r > 180 and avg_g > 150:
                        content_type = "BEACH/SAND"
                    elif avg_g > avg_r and avg_g > avg_b:
                        content_type = "EDGE/GRASS"
                    else:
                        content_type = f"OTHER({int(avg_r)},{int(avg_g)},{int(avg_b)})"
            
            print(f"  Tile {i} at x={x}: {'RED BORDER' if red_found else 'NO RED'} -> {content_type}")
            
            if red_found:
                tiles_found.append({
                    'index': i,
                    'x': x,
                    'y': y,
                    'type': content_type
                })
                
                # Mark on visualization
                vis_x = 50 + (x - 480) * 4
                vis_y = 50 + (y - 10) * 4
                
                # Red border indicator
                draw.line([(vis_x, vis_y), (vis_x, vis_y + 32)], fill=(255, 0, 0), width=4)
                
                # Content area
                draw.rectangle([vis_x + 8, vis_y, vis_x + 32, vis_y + 32], 
                             outline=(0, 255, 255), width=2)
                
                # Label
                draw.text((vis_x + 16, vis_y - 10), str(i), fill=(255, 255, 255), anchor="mm")
    
    # Check other potential water rows
    print("\nChecking other rows for similar pattern:")
    for check_y in [28, 36, 44]:  # Possible animation frames
        red_count = 0
        for i in range(8):
            x = base_x + i * 9
            if x < tileset.width and check_y < tileset.height:
                pixel = tileset.getpixel((x, check_y))
                if pixel[0] > 200 and pixel[1] < 100 and pixel[2] < 100:
                    red_count += 1
        
        if red_count > 0:
            print(f"  y={check_y}: {red_count} tiles with red borders (animation frame)")
    
    # Draw grid lines
    for i in range(15):
        x = 50 + (base_x - 480 + i * 9) * 4
        draw.line([(x, 50), (x, 210)], fill=(100, 100, 100, 128), width=1)
    
    # Legend
    draw.text((50, 250), "Red lines: Red border (1px)", fill=(255, 0, 0))
    draw.text((50, 270), "Cyan boxes: Actual tile content (6x8)", fill=(0, 255, 255))
    draw.text((50, 290), "Tile types detected:", fill=(255, 255, 255))
    
    type_counts = {}
    for tile in tiles_found:
        type_counts[tile['type']] = type_counts.get(tile['type'], 0) + 1
    
    y_pos = 310
    for tile_type, count in type_counts.items():
        draw.text((50, y_pos), f"  {tile_type}: {count} tiles", fill=(200, 200, 200))
        y_pos += 20
    
    vis.save("water_tiles_y20_detailed.png")
    
    print(f"\nFound {len(tiles_found)} tiles with red borders")
    print("Created water_tiles_y20_detailed.png")

if __name__ == "__main__":
    check_y20_water()
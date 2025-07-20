#!/usr/bin/env python3
"""
Find Water label and the tiles directly below it
"""

from PIL import Image, ImageDraw, ImageFont
import json

def find_water_label_and_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # Look for text labels - they're usually darker pixels in groups
    # Water label should be somewhere in the tileset
    
    # Create visualization
    vis = Image.new('RGBA', (1000, 800), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    # Let's check different sections where labels might be
    sections = [
        (0, 0, 200, 300, "Left section"),
        (100, 100, 300, 300, "Middle section"),
        (0, 130, 200, 170, "Common label area"),
    ]
    
    print("Searching for Water label and tiles with pink borders below...")
    
    # Let me check the actual water tiles we found and see if there's a label above
    water_y = 58  # Where we found water tiles
    
    # Check area above water tiles for label
    label_area = tileset.crop((0, max(0, water_y - 30), 100, water_y))
    label_scaled = label_area.resize((300, 90), Image.NEAREST)
    vis.paste(label_scaled, (50, 50))
    
    draw.text((200, 30), f"Area above water tiles (y={water_y})", fill=(255, 255, 255), anchor="mm")
    
    # Now let's specifically look for tiles with pink first column
    # Scan more comprehensively
    print("\nScanning entire tileset for 8x8 tiles with pink first column...")
    
    pink_tile_locations = []
    
    # Check every potential 8x8 tile position on 9x9 grid
    for y in range(0, min(tileset.height - 8, 300), 9):
        for x in range(0, min(tileset.width - 8, 200), 9):
            # Check if first column is pink/magenta
            pink_pixels = 0
            
            for dy in range(8):
                pixel = tileset.getpixel((x, y + dy))
                r, g, b, a = pixel
                
                if r > 200 and b > 200 and g < 150 and a > 200:
                    pink_pixels += 1
            
            if pink_pixels >= 4:  # At least half the column is pink
                # Check what's after the pink (content type)
                content_pixels = []
                for dy in range(8):
                    for dx in range(2, 8):  # Skip pink and gap
                        if x + dx < tileset.width and y + dy < tileset.height:
                            p = tileset.getpixel((x + dx, y + dy))
                            if p[3] > 0:
                                content_pixels.append(p)
                
                content_type = "UNKNOWN"
                if content_pixels:
                    avg_b = sum(p[2] for p in content_pixels) / len(content_pixels)
                    avg_r = sum(p[0] for p in content_pixels) / len(content_pixels)
                    avg_g = sum(p[1] for p in content_pixels) / len(content_pixels)
                    
                    if avg_b > avg_r * 1.2:
                        content_type = "WATER"
                    elif avg_r > 180 and avg_g > 140:
                        content_type = "BEACH/SAND"
                    
                pink_tile_locations.append((x, y, content_type))
    
    print(f"\nFound {len(pink_tile_locations)} tiles with pink first column:")
    
    # Group by y position
    y_groups = {}
    for x, y, ctype in pink_tile_locations:
        if y not in y_groups:
            y_groups[y] = []
        y_groups[y].append((x, ctype))
    
    # Find rows with water/beach tiles
    water_rows = []
    
    for y, tiles in sorted(y_groups.items()):
        if len(tiles) >= 3:  # Multiple tiles in row
            water_count = sum(1 for _, t in tiles if "WATER" in t or "BEACH" in t)
            if water_count > 0:
                print(f"  y={y}: {len(tiles)} tiles ({water_count} water/beach)")
                water_rows.append(y)
    
    # Show the most promising water row
    if water_rows:
        show_y = water_rows[0]
        
        # Extract this row
        row_area = tileset.crop((0, show_y - 2, 200, show_y + 20))
        row_scaled = row_area.resize((600, 66), Image.NEAREST)
        vis.paste(row_scaled, (50, 200))
        
        draw.text((350, 180), f"Water tiles with pink borders at y={show_y}", 
                 fill=(255, 255, 255), anchor="mm")
        
        # Mark the tiles
        for x, ctype in y_groups[show_y]:
            vis_x = 50 + x * 3
            vis_y = 200 + 6
            
            # Pink border
            draw.line([(vis_x, vis_y), (vis_x, vis_y + 24)], fill=(255, 0, 255), width=3)
            
            # Content area
            draw.rectangle([vis_x + 6, vis_y, vis_x + 24, vis_y + 24], 
                         outline=(0, 255, 255), width=2)
            
            # Label content type
            if "WATER" in ctype:
                label = "W"
            elif "BEACH" in ctype:
                label = "B"
            else:
                label = "?"
            
            draw.text((vis_x + 12, vis_y - 10), label, fill=(255, 255, 255), anchor="mm")
        
        print(f"\nWater tiles with pink borders found at y={show_y}")
        print("These are 8x8 tiles where:")
        print("- Column 0: Pink/magenta border")
        print("- Column 1: Gap (may be transparent)")
        print("- Columns 2-7: Actual tile content (6x8)")
    
    else:
        print("\nNo clear water tile rows with pink borders found")
        print("Pink borders might be on edge/beach tiles only")
    
    # Also show what's at y=144 (another common water position)
    alt_y = 144
    if alt_y < tileset.height:
        alt_area = tileset.crop((0, alt_y - 2, 200, alt_y + 20))
        alt_scaled = alt_area.resize((600, 66), Image.NEAREST)
        vis.paste(alt_scaled, (50, 350))
        
        draw.text((350, 330), f"Alternative water position at y={alt_y}", 
                 fill=(255, 255, 255), anchor="mm")
        
        # Check for pink
        for x in range(0, 100, 9):
            has_pink = False
            for dy in range(8):
                if alt_y + dy < tileset.height:
                    p = tileset.getpixel((x, alt_y + dy))
                    if p[0] > 200 and p[2] > 200 and p[1] < 150:
                        has_pink = True
                        break
            
            if has_pink:
                vis_x = 50 + x * 3
                vis_y = 350 + 6
                draw.line([(vis_x, vis_y), (vis_x, vis_y + 24)], 
                        fill=(255, 0, 255), width=2)
    
    vis.save("water_label_and_pink_tiles.png")
    print("\nCreated water_label_and_pink_tiles.png")

if __name__ == "__main__":
    find_water_label_and_tiles()
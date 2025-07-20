#!/usr/bin/env python3
"""
Search entire tileset for Water label and red borders
"""

from PIL import Image, ImageDraw
import json

def search_entire_tileset():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # Find all areas with significant red pixels
    red_areas = []
    
    print("Scanning entire tileset for red borders...")
    
    # Scan in chunks
    for y in range(0, tileset.height, 10):
        for x in range(0, tileset.width, 10):
            red_count = 0
            
            # Check 10x10 area
            for dy in range(10):
                for dx in range(10):
                    if x + dx < tileset.width and y + dy < tileset.height:
                        pixel = tileset.getpixel((x + dx, y + dy))
                        r, g, b, a = pixel
                        
                        # Strong red color
                        if r > 200 and g < 100 and b < 100 and a > 200:
                            red_count += 1
            
            if red_count > 5:  # Significant red in this area
                red_areas.append((x, y, red_count))
    
    print(f"\nFound {len(red_areas)} areas with significant red pixels:")
    for x, y, count in sorted(red_areas, key=lambda a: a[1])[:20]:  # Show first 20 by y position
        print(f"  Area at ({x}, {y}): {count} red pixels")
    
    # Create visualization showing all red areas
    vis = tileset.copy()
    draw = ImageDraw.Draw(vis)
    
    # Highlight red areas
    for x, y, count in red_areas:
        draw.rectangle([x-2, y-2, x+12, y+12], outline=(255, 255, 0), width=2)
    
    # Save full view
    vis_scaled = vis.resize((tileset.width // 2, tileset.height // 2), Image.LANCZOS)
    vis_scaled.save("tileset_red_areas_full.png")
    
    # Now let's check the most promising areas for water tiles
    if red_areas:
        # Group by y coordinate to find rows
        y_groups = {}
        for x, y, count in red_areas:
            y_key = y // 10 * 10  # Group by 10px ranges
            if y_key not in y_groups:
                y_groups[y_key] = []
            y_groups[y_key].append((x, y, count))
        
        print("\nRed areas grouped by row:")
        for y_key in sorted(y_groups.keys())[:10]:
            areas = y_groups[y_key]
            print(f"  Row around y={y_key}: {len(areas)} red areas")
            
            # If this row has multiple red areas, might be water tiles
            if len(areas) >= 4:
                print(f"    -> Possible water tile row!")
                
                # Check first area in detail
                first_x, first_y, _ = areas[0]
                
                # Create detailed view of this area
                detail = tileset.crop((first_x - 5, first_y - 5, first_x + 100, first_y + 20))
                detail_scaled = detail.resize((detail.width * 4, detail.height * 4), Image.NEAREST)
                
                detail_vis = Image.new('RGBA', (500, 100), (40, 40, 40))
                detail_vis.paste(detail_scaled, (10, 10))
                
                draw_detail = ImageDraw.Draw(detail_vis)
                draw_detail.text((250, 5), f"Detail of potential water tiles at y={first_y}", 
                               fill=(255, 255, 255), anchor="mm")
                
                detail_vis.save(f"water_detail_y{first_y}.png")
                print(f"    -> Created water_detail_y{first_y}.png")
                
                # Analyze the pattern
                print(f"    -> Checking tile pattern:")
                for i in range(5):
                    x = first_x + i * 9  # Assuming 8+1 grid
                    if x < tileset.width:
                        # Check first column
                        pixel1 = tileset.getpixel((x, first_y))
                        # Check after red border (x+2)
                        if x + 2 < tileset.width:
                            pixel2 = tileset.getpixel((x + 2, first_y))
                            
                            type1 = "RED" if pixel1[0] > 200 and pixel1[1] < 100 else "OTHER"
                            type2 = "BLUE" if pixel2[2] > pixel2[0] else "OTHER"
                            
                            print(f"       Tile {i}: x={x} [{type1}], x+2={x+2} [{type2}]")
    
    print(f"\nCreated tileset_red_areas_full.png showing all red areas")
    print("Yellow boxes indicate areas with significant red pixels")

if __name__ == "__main__":
    search_entire_tileset()
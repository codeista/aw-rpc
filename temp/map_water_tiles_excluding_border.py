#!/usr/bin/env python3
"""
Map water/edge/beach tiles excluding the red border and internal gap
"""

from PIL import Image, ImageDraw
import json

def map_water_tiles_properly():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # Water starts at y=58 (6.5 tiles down from first road at y=0)
    water_y = 58
    
    # Check for red border
    print(f"\nChecking for red border at water tiles (y={water_y})...")
    
    # Sample the first few pixels of where water tiles should be
    for x in range(0, 50):
        pixel = tileset.getpixel((x, water_y))
        r, g, b, a = pixel
        # Check if this is reddish
        if r > 200 and g < 100 and b < 100:
            print(f"Found red pixel at x={x}: {pixel}")
    
    # Create visualization
    vis = Image.new('RGBA', (400, 200), (40, 40, 40, 255))
    
    # Copy water section
    water_section = tileset.crop((0, water_y - 10, 400, water_y + 100))
    vis.paste(water_section, (0, 0))
    
    draw = ImageDraw.Draw(vis)
    
    # If red border is 1px and internal gap is 1px, then:
    # - Skip first pixel (red border)
    # - Skip second pixel (gap)
    # - Actual tile starts at x+2
    # - Actual tile is 6x8 (8 - red border - gap)
    
    print("\nMapping water tiles with border adjustment...")
    
    water_tiles = []
    
    # For each expected water tile position
    for i in range(8):  # Check up to 8 tiles
        base_x = i * 9  # Normal 8x8 + 1px separator grid
        
        # Check different offsets
        for offset in [0, 1, 2]:
            x = base_x + offset
            y = water_y
            
            # Sample a few pixels to see if this looks like water content
            has_water = False
            for sy in range(y, y + 8):
                for sx in range(x, x + 6):  # Check 6 pixels wide
                    if sx < tileset.width and sy < tileset.height:
                        pixel = tileset.getpixel((sx, sy))
                        # Water is typically blueish
                        if pixel[2] > pixel[0] and pixel[2] > pixel[1]:  # More blue than red/green
                            has_water = True
                            break
                if has_water:
                    break
            
            if has_water:
                # Found water content at this offset
                water_tiles.append({
                    "index": i,
                    "base_x": base_x,
                    "actual_x": x,
                    "offset": offset,
                    "y": y
                })
                
                # Draw what we found
                # Show original position in red
                draw.rectangle([base_x, y - water_y + 50, base_x + 8, y - water_y + 50 + 8], 
                             outline=(255, 0, 0), width=1)
                # Show adjusted position in cyan
                draw.rectangle([x, y - water_y + 50, x + 6, y - water_y + 50 + 8], 
                             outline=(0, 255, 255), width=2)
                
                draw.text((base_x, y - water_y + 35), f"T{i}", fill=(255, 255, 255))
                
                break
    
    # Print findings
    print(f"\nFound {len(water_tiles)} water tiles:")
    for tile in water_tiles:
        print(f"  Tile {tile['index']}: original x={tile['base_x']}, adjusted x={tile['actual_x']} (offset={tile['offset']})")
    
    # If we found a consistent offset, use it
    if water_tiles and all(t['offset'] == water_tiles[0]['offset'] for t in water_tiles):
        offset = water_tiles[0]['offset']
        print(f"\nConsistent offset found: {offset} pixels")
        print(f"Red border: 1px, Gap: 1px, Total offset: {offset}px")
        print(f"Actual tile size: {8-offset}x8")
    
    # Also check beach tiles (should be on same row after water)
    print("\nChecking beach/edge tiles...")
    beach_start = 4 * 9  # After 4 water frames
    
    for i in range(4):  # Check a few beach tiles
        base_x = beach_start + (i * 9)
        
        # Check with same offset pattern
        for offset in [0, 1, 2]:
            x = base_x + offset
            
            # Check if has content
            has_content = False
            for sy in range(water_y, water_y + 8):
                for sx in range(x, x + 6):
                    if sx < tileset.width and sy < tileset.height:
                        pixel = tileset.getpixel((sx, sy))
                        if pixel[3] > 0 and not (abs(pixel[0] - 149) < 15 and abs(pixel[1] - 177) < 15):
                            has_content = True
                            break
            
            if has_content:
                draw.rectangle([x, water_y - water_y + 50, x + 6, water_y - water_y + 50 + 8], 
                             outline=(255, 255, 0), width=1)
                draw.text((base_x, water_y - water_y + 35), f"B{i}", fill=(255, 255, 0))
                break
    
    draw.text((200, 20), "Water Tile Border Analysis", fill=(255, 255, 255), anchor="mm")
    draw.text((10, 170), "Red boxes: Original 8x8 positions", fill=(255, 0, 0))
    draw.text((10, 180), "Cyan boxes: Adjusted water positions", fill=(0, 255, 255))
    draw.text((10, 190), "Yellow boxes: Beach tile positions", fill=(255, 255, 0))
    
    vis.save("water_border_analysis.png")
    
    print("\nCreated water_border_analysis.png")
    print("This shows the red border and how tiles need to be adjusted")

if __name__ == "__main__":
    map_water_tiles_properly()
#!/usr/bin/env python3
"""
Map the actual water tiles with red borders correctly
"""

from PIL import Image, ImageDraw
import json

def map_water_tiles_correct():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # Based on search results, water tiles are around y=10-30
    # Let's examine this area carefully
    
    # Create visualization
    vis = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    
    # Extract the water tile area
    water_area = tileset.crop((480, 0, 600, 100))
    water_scaled = water_area.resize((480, 400), Image.NEAREST)
    vis.paste(water_scaled, (50, 50))
    
    draw = ImageDraw.Draw(vis)
    draw.text((400, 20), "Water Tiles Area (4x scale)", fill=(255, 255, 255), anchor="mm")
    
    # Based on the pattern we found:
    # - Tiles start at x=490, y=10
    # - Red border on first column
    # - 1px gap after red border
    # - Actual tile content starts at x+2
    
    water_tiles = []
    
    # Check the y=10 row (first water row)
    y = 10
    base_x = 490
    
    print(f"\nAnalyzing water tiles at y={y}:")
    
    for i in range(8):  # Check 8 tiles
        x = base_x + i * 9  # 8px tile + 1px separator
        
        # Check tile pattern
        if x + 8 < tileset.width:
            # Check first pixel (should be red border)
            first_pixel = tileset.getpixel((x, y))
            
            # Check pixel after gap (x+2, should be water)
            if x + 2 < tileset.width:
                water_pixel = tileset.getpixel((x + 2, y))
                
                is_red = first_pixel[0] > 200 and first_pixel[1] < 100
                is_water = water_pixel[2] > water_pixel[0]  # More blue
                
                print(f"  Tile {i} at x={x}:")
                print(f"    First column: {'RED' if is_red else 'NOT RED'} {first_pixel}")
                print(f"    After gap (x+2): {'WATER' if is_water else 'NOT WATER'} {water_pixel}")
                
                if is_water:
                    # This is a valid water tile
                    # Actual content is from x+2 to x+7 (6 pixels wide)
                    water_tiles.append({
                        'index': i,
                        'original_x': x,
                        'content_x': x + 2,
                        'y': y,
                        'width': 6,
                        'height': 8
                    })
                    
                    # Draw on visualization
                    # Scale factor is 4
                    vis_x = 50 + (x - 480) * 4
                    vis_y = 50 + y * 4
                    
                    # Show original tile boundary in red
                    draw.rectangle([vis_x, vis_y, vis_x + 32, vis_y + 32], 
                                 outline=(255, 0, 0), width=2)
                    
                    # Show actual content area in cyan
                    content_vis_x = 50 + (x + 2 - 480) * 4
                    draw.rectangle([content_vis_x, vis_y, content_vis_x + 24, vis_y + 32], 
                                 outline=(0, 255, 255), width=2)
                    
                    draw.text((vis_x + 16, vis_y - 10), f"W{i}", fill=(255, 255, 255), anchor="mm")
    
    print(f"\nFound {len(water_tiles)} water tiles")
    
    # Check other water rows
    other_rows = [20, 30, 40]  # Possible animation frames
    
    for row_y in other_rows:
        has_water = False
        for i in range(4):
            x = base_x + i * 9
            if x + 2 < tileset.width and row_y < tileset.height:
                pixel = tileset.getpixel((x + 2, row_y))
                if pixel[2] > pixel[0]:  # Blue-ish
                    has_water = True
                    break
        
        if has_water:
            print(f"Additional water row found at y={row_y} (animation frame)")
    
    # Create mapping
    mapping = {
        "water_tiles": {
            "description": "Water tiles with red border and 1px gap",
            "tile_grid": "9x9 (8px tile + 1px separator)",
            "content_offset": 2,
            "content_size": "6x8",
            "tiles": []
        }
    }
    
    # Add water tiles to mapping
    water_names = ["WATER_NW", "WATER_N", "WATER_NE", "WATER_W", 
                   "WATER_CENTER", "WATER_E", "WATER_SW", "WATER_S"]
    
    for i, tile in enumerate(water_tiles):
        if i < len(water_names):
            mapping["water_tiles"]["tiles"].append({
                "name": water_names[i],
                "original_x": tile['original_x'],
                "content_x": tile['content_x'],
                "y": tile['y'],
                "width": tile['width'],
                "height": tile['height'],
                "description": f"Water tile - {water_names[i].split('_')[1]}"
            })
    
    # Save mapping
    with open("water_tiles_mapping.json", "w") as f:
        json.dump(mapping, f, indent=2)
    
    # Add legend
    draw.text((50, 480), "Legend:", fill=(255, 255, 255))
    draw.text((50, 500), "Red boxes: Original 8x8 tile boundaries", fill=(255, 0, 0))
    draw.text((50, 520), "Cyan boxes: Actual 6x8 water content (after red border + gap)", fill=(0, 255, 255))
    draw.text((50, 540), "Water tiles need special handling to skip red border", fill=(255, 255, 255))
    
    vis.save("water_tiles_mapped_correct.png")
    
    print("\nCreated water_tiles_mapped_correct.png")
    print("Water tiles have:")
    print("- 1px red border on left")
    print("- 1px gap after red border")
    print("- 6x8 actual content")
    print(f"\nMapped {len(mapping['water_tiles']['tiles'])} water tiles")

if __name__ == "__main__":
    map_water_tiles_correct()
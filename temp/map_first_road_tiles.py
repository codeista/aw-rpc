#!/usr/bin/env python3
"""
Map the road tiles from the first section of the tileset
"""

from PIL import Image, ImageDraw
import json

def map_first_road_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Roads are at the very beginning of the sheet
    # Let's map them systematically
    vis = Image.new('RGBA', (800, 400), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    # Starting from top-left of tileset
    start_x = 0
    start_y = 0
    
    # First, let's see what's in the top-left area
    print("Examining first section of tileset for road tiles...")
    
    # Check first few rows with different grid patterns
    # Roads might be on a different grid than terrain
    
    road_mapping = {}
    tile_count = 0
    
    # Check with 17x17 grid (16+1 separator)
    for row in range(4):
        for col in range(8):
            x = start_x + col * 17
            y = start_y + row * 17
            
            if x + 16 <= tileset.width and y + 16 <= tileset.height:
                tile = tileset.crop((x, y, x + 16, y + 16))
                
                # Place all tiles in visualization to see what we have
                vis_x = 20 + col * 90
                vis_y = 20 + row * 90
                
                tile_scaled = tile.resize((64, 64), Image.NEAREST)
                vis.paste(tile_scaled, (vis_x, vis_y))
                draw.rectangle([vis_x-1, vis_y-1, vis_x+64, vis_y+64], outline=(150, 150, 150))
                draw.text((vis_x, vis_y + 67), f"({x},{y})", fill=(200, 200, 200))
                
                # Identify road tiles by appearance
                road_type = analyze_road_tile(tile)
                if road_type:
                    draw.text((vis_x, vis_y - 15), road_type, fill=(255, 255, 0))
                    road_mapping[f"ROAD_{road_type.upper().replace(' ', '_')}"] = {
                        "x": x,
                        "y": y,
                        "width": 16,
                        "height": 16,
                        "description": f"Road - {road_type}"
                    }
                
                tile_count += 1
    
    vis.save("first_section_roads.png")
    print(f"Created first_section_roads.png with {tile_count} tiles")
    
    # Also check with 9x9 grid (8+1 separator) in case roads are smaller
    vis2 = Image.new('RGBA', (800, 400), (40, 40, 40, 255))
    draw2 = ImageDraw.Draw(vis2)
    
    print("\nChecking with 9x9 grid...")
    for row in range(6):
        for col in range(10):
            x = start_x + col * 9
            y = start_y + row * 9
            
            if x + 8 <= tileset.width and y + 8 <= tileset.height:
                tile = tileset.crop((x, y, x + 8, y + 8))
                
                # Scale up for visibility
                tile_scaled = tile.resize((64, 64), Image.NEAREST)
                vis_x = 20 + (col % 10) * 75
                vis_y = 20 + row * 75
                
                vis2.paste(tile_scaled, (vis_x, vis_y))
                draw2.rectangle([vis_x-1, vis_y-1, vis_x+64, vis_y+64], outline=(150, 150, 150))
                draw2.text((vis_x, vis_y + 67), f"({x},{y})", fill=(200, 200, 200), font=None)
    
    vis2.save("first_section_roads_8x8.png")
    
    return road_mapping

def analyze_road_tile(tile):
    """Analyze a tile to determine if it's a road and what type"""
    pixels = tile.load()
    width, height = tile.size
    
    # Count dark pixels (road surface is usually dark gray/black)
    dark_count = 0
    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            if len(pixel) >= 3:
                r, g, b = pixel[:3]
                # Dark gray to black
                if r < 80 and g < 80 and b < 80:
                    dark_count += 1
    
    # If not enough dark pixels, probably not a road
    if dark_count < 30:
        return None
    
    # Simple pattern matching for road types
    # Check corners and edges
    has_top = any(pixels[x, 0][:3] == (0, 0, 0) or sum(pixels[x, 0][:3]) < 150 for x in range(2, width-2))
    has_bottom = any(pixels[x, height-1][:3] == (0, 0, 0) or sum(pixels[x, height-1][:3]) < 150 for x in range(2, width-2))
    has_left = any(pixels[0, y][:3] == (0, 0, 0) or sum(pixels[0, y][:3]) < 150 for y in range(2, height-2))
    has_right = any(pixels[width-1, y][:3] == (0, 0, 0) or sum(pixels[width-1, y][:3]) < 150 for y in range(2, height-2))
    
    connections = sum([has_top, has_bottom, has_left, has_right])
    
    if connections >= 2:
        if has_left and has_right and not has_top and not has_bottom:
            return "HORT"
        elif has_top and has_bottom and not has_left and not has_right:
            return "VERT"
        elif has_top and has_right:
            return "NE"
        elif has_top and has_left:
            return "NW"
        elif has_bottom and has_right:
            return "SE"
        elif has_bottom and has_left:
            return "SW"
    
    return None

if __name__ == "__main__":
    road_mapping = map_first_road_tiles()
    
    if road_mapping:
        print(f"\nFound {len(road_mapping)} road tiles:")
        for name, info in road_mapping.items():
            print(f"  {name}: ({info['x']}, {info['y']})")
        
        # Update main mapping
        with open("aw2_mixed_tile_mapping.json", "r") as f:
            main_mapping = json.load(f)
        
        main_mapping["tiles"].update(road_mapping)
        
        with open("aw2_mixed_tile_mapping.json", "w") as f:
            json.dump(main_mapping, f, indent=2)
        
        print("\nUpdated main mapping file with road tiles")
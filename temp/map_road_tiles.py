#!/usr/bin/env python3
"""
Map all road tile variations from the tileset
"""

from PIL import Image, ImageDraw
import json

def map_road_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Roads appear to be in the second row of the terrain grid
    # Starting position based on our grid analysis
    road_start_x = 238
    road_start_y = 35  # Second row (18 + 17)
    grid_step = 17
    
    # Create visualization
    vis = Image.new('RGBA', (600, 400), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    # Road tile types we need to find
    road_types = [
        "ROAD_HORT",     # Horizontal road
        "ROAD_VERT",     # Vertical road  
        "ROAD_CROSS",    # Crossroads/intersection
        "ROAD_NE",       # Turn North-East
        "ROAD_SE",       # Turn South-East
        "ROAD_NW",       # Turn North-West
        "ROAD_SW",       # Turn South-West
        "ROAD_T_N",      # T-junction North
        "ROAD_T_S",      # T-junction South
        "ROAD_T_E",      # T-junction East
        "ROAD_T_W",      # T-junction West
        "ROAD_END_N",    # Dead end North
        "ROAD_END_S",    # Dead end South
        "ROAD_END_E",    # Dead end East
        "ROAD_END_W"     # Dead end West
    ]
    
    road_tiles = {}
    
    # Check multiple rows and columns for road tiles
    print("Searching for road tiles:")
    print("-" * 60)
    
    tile_index = 0
    for row in range(3):  # Check 3 rows
        for col in range(6):  # Check 6 columns
            x = road_start_x + (col * grid_step)
            y = road_start_y + (row * grid_step)
            
            if x + 16 <= tileset.width and y + 16 <= tileset.height:
                tile = tileset.crop((x, y, x + 16, y + 16))
                pixels = list(tile.getdata())
                
                # Check if it's a road (grayish color)
                gray_pixels = 0
                total_non_bg = 0
                
                for pixel in pixels:
                    if len(pixel) >= 3:
                        r, g, b = pixel[:3]
                        # Not background color
                        if not (abs(r - 149) < 10 and abs(g - 177) < 10 and abs(b - 200) < 10):
                            total_non_bg += 1
                            # Check for gray (road color)
                            if abs(r - g) < 20 and abs(g - b) < 20 and 60 < r < 150:
                                gray_pixels += 1
                
                # If it's mostly gray, it's likely a road
                if total_non_bg > 0 and gray_pixels > total_non_bg * 0.5:
                    # Place in visualization
                    vis_x = 20 + (tile_index % 8) * 70
                    vis_y = 20 + (tile_index // 8) * 100
                    
                    tile_scaled = tile.resize((64, 64), Image.NEAREST)
                    vis.paste(tile_scaled, (vis_x, vis_y))
                    draw.rectangle([vis_x-1, vis_y-1, vis_x+64, vis_y+64], outline=(200, 200, 200))
                    
                    # Add coordinates
                    draw.text((vis_x, vis_y + 67), f"({x},{y})", fill=(150, 150, 150))
                    
                    # Try to identify road type by visual inspection
                    road_type = identify_road_type(tile)
                    if tile_index < len(road_types):
                        road_name = road_types[tile_index]
                    else:
                        road_name = f"ROAD_{tile_index}"
                    
                    road_tiles[road_name] = {
                        "x": x,
                        "y": y,
                        "width": 16,
                        "height": 16,
                        "description": road_type
                    }
                    
                    draw.text((vis_x, vis_y - 15), road_name.replace("ROAD_", ""), fill=(255, 255, 0))
                    
                    print(f"Found road at ({x}, {y}): {road_type}")
                    tile_index += 1
    
    vis.save("road_tiles_map.png")
    print(f"\nFound {len(road_tiles)} road tiles")
    print("Created road_tiles_map.png")
    
    # Save road mapping
    with open("road_tiles_mapping.json", "w") as f:
        json.dump(road_tiles, f, indent=2)
    
    return road_tiles

def identify_road_type(tile):
    """Try to identify road type by checking pixel patterns"""
    pixels = tile.load()
    width, height = tile.size
    
    # Check edges for road connections
    top_road = False
    bottom_road = False
    left_road = False
    right_road = False
    
    # Check top edge
    gray_count = 0
    for x in range(width):
        pixel = pixels[x, 0]
        if len(pixel) >= 3:
            r, g, b = pixel[:3]
            if abs(r - g) < 20 and abs(g - b) < 20 and 60 < r < 150:
                gray_count += 1
    top_road = gray_count > width * 0.5
    
    # Check bottom edge
    gray_count = 0
    for x in range(width):
        pixel = pixels[x, height-1]
        if len(pixel) >= 3:
            r, g, b = pixel[:3]
            if abs(r - g) < 20 and abs(g - b) < 20 and 60 < r < 150:
                gray_count += 1
    bottom_road = gray_count > width * 0.5
    
    # Check left edge
    gray_count = 0
    for y in range(height):
        pixel = pixels[0, y]
        if len(pixel) >= 3:
            r, g, b = pixel[:3]
            if abs(r - g) < 20 and abs(g - b) < 20 and 60 < r < 150:
                gray_count += 1
    left_road = gray_count > height * 0.5
    
    # Check right edge
    gray_count = 0
    for y in range(height):
        pixel = pixels[width-1, y]
        if len(pixel) >= 3:
            r, g, b = pixel[:3]
            if abs(r - g) < 20 and abs(g - b) < 20 and 60 < r < 150:
                gray_count += 1
    right_road = gray_count > height * 0.5
    
    # Identify type based on connections
    connections = sum([top_road, bottom_road, left_road, right_road])
    
    if connections == 4:
        return "Crossroads"
    elif connections == 3:
        if not top_road:
            return "T-junction South"
        elif not bottom_road:
            return "T-junction North"
        elif not left_road:
            return "T-junction East"
        elif not right_road:
            return "T-junction West"
    elif connections == 2:
        if top_road and bottom_road:
            return "Vertical road"
        elif left_road and right_road:
            return "Horizontal road"
        elif top_road and right_road:
            return "Turn North-East"
        elif top_road and left_road:
            return "Turn North-West"
        elif bottom_road and right_road:
            return "Turn South-East"
        elif bottom_road and left_road:
            return "Turn South-West"
    elif connections == 1:
        if top_road:
            return "Dead end North"
        elif bottom_road:
            return "Dead end South"
        elif left_road:
            return "Dead end West"
        elif right_road:
            return "Dead end East"
    
    return "Unknown road type"

if __name__ == "__main__":
    road_tiles = map_road_tiles()
    
    # Update the main mapping file with road tiles
    print("\nUpdating main mapping file...")
    with open("aw2_mixed_tile_mapping.json", "r") as f:
        main_mapping = json.load(f)
    
    # Update road tiles in main mapping
    for road_name, road_info in road_tiles.items():
        if road_name in main_mapping["tiles"]:
            main_mapping["tiles"][road_name].update(road_info)
            print(f"Updated existing {road_name}")
        else:
            main_mapping["tiles"][road_name] = road_info
            print(f"Added new {road_name}")
    
    with open("aw2_mixed_tile_mapping.json", "w") as f:
        json.dump(main_mapping, f, indent=2)
    
    print("\nRoad tile mapping complete!")
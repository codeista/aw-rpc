#!/usr/bin/env python3
"""
Map pipe tiles from the tileset
"""

from PIL import Image, ImageDraw
import json

def map_pipe_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Pipes should be after roads, let's check the area after the road tiles
    # Roads end around x=85, y=51, so pipes might start after that
    
    vis = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    # Let's search for pipe tiles - they typically have a distinct orange/red color
    print("Searching for pipe tiles...")
    
    pipe_tiles = {}
    vis_index = 0
    
    # Check the area after roads
    # Let's look at the next sections on the 17x17 grid
    search_areas = [
        # Continue from where roads end
        {"start_x": 102, "start_y": 17, "cols": 8, "rows": 4},  # Next to roads
        {"start_x": 0, "start_y": 68, "cols": 10, "rows": 3},   # Next rows down
        {"start_x": 102, "start_y": 34, "cols": 8, "rows": 4},  # More tiles
    ]
    
    for area in search_areas:
        for row in range(area["rows"]):
            for col in range(area["cols"]):
                x = area["start_x"] + col * 17
                y = area["start_y"] + row * 17
                
                if x + 16 <= tileset.width and y + 16 <= tileset.height:
                    tile = tileset.crop((x, y, x + 16, y + 16))
                    
                    # Check if it's a pipe tile (orange/red colors)
                    if is_pipe_tile(tile):
                        # Add to visualization
                        if vis_index < 48:
                            vis_x = 20 + (vis_index % 8) * 95
                            vis_y = 20 + (vis_index // 8) * 95
                            
                            tile_scaled = tile.resize((64, 64), Image.NEAREST)
                            vis.paste(tile_scaled, (vis_x, vis_y))
                            draw.rectangle([vis_x-1, vis_y-1, vis_x+64, vis_y+64], outline=(255, 255, 255))
                            draw.text((vis_x, vis_y + 67), f"({x},{y})", fill=(200, 200, 200))
                            
                            # Identify pipe type
                            pipe_type = identify_pipe_type(tile)
                            draw.text((vis_x, vis_y - 15), pipe_type, fill=(255, 127, 0))
                            
                            pipe_name = f"PIPE_{pipe_type.upper()}"
                            pipe_tiles[pipe_name] = {
                                "x": x,
                                "y": y,
                                "width": 16,
                                "height": 16,
                                "description": f"Pipe - {pipe_type}"
                            }
                            
                            vis_index += 1
                            print(f"Found pipe at ({x}, {y}): {pipe_type}")
    
    # Also check the first few rows in case pipes are there
    print("\nChecking first section for pipes...")
    for row in range(5):
        for col in range(10):
            x = col * 17
            y = row * 17
            
            if x + 16 <= tileset.width and y + 16 <= tileset.height:
                tile = tileset.crop((x, y, x + 16, y + 16))
                
                if is_pipe_tile(tile):
                    if vis_index < 48:
                        vis_x = 20 + (vis_index % 8) * 95
                        vis_y = 20 + (vis_index // 8) * 95
                        
                        tile_scaled = tile.resize((64, 64), Image.NEAREST)
                        vis.paste(tile_scaled, (vis_x, vis_y))
                        draw.rectangle([vis_x-1, vis_y-1, vis_x+64, vis_y+64], outline=(255, 255, 255))
                        draw.text((vis_x, vis_y + 67), f"({x},{y})", fill=(200, 200, 200))
                        
                        pipe_type = identify_pipe_type(tile)
                        draw.text((vis_x, vis_y - 15), pipe_type, fill=(255, 127, 0))
                        
                        vis_index += 1
                        print(f"Found pipe at ({x}, {y}): {pipe_type}")
    
    vis.save("pipe_tiles_found.png")
    print(f"\nFound {len(pipe_tiles)} pipe tiles")
    print("Created pipe_tiles_found.png")
    
    return pipe_tiles

def is_pipe_tile(tile):
    """Check if a tile is a pipe by looking for orange/red colors"""
    pixels = list(tile.getdata())
    orange_count = 0
    red_count = 0
    
    for pixel in pixels:
        if len(pixel) >= 3:
            r, g, b = pixel[:3]
            # Orange pipes (high red, medium green, low blue)
            if r > 180 and 80 < g < 150 and b < 80:
                orange_count += 1
            # Red pipes
            elif r > 150 and g < 80 and b < 80:
                red_count += 1
    
    # If significant orange/red pixels, it's likely a pipe
    return (orange_count + red_count) > 20

def identify_pipe_type(tile):
    """Identify the type of pipe tile"""
    pixels = tile.load()
    width, height = tile.size
    
    # Check edges for pipe connections
    has_top = False
    has_bottom = False
    has_left = False
    has_right = False
    
    # Check for orange/red pixels at edges
    for x in range(width):
        # Top edge
        pixel = pixels[x, 1]
        if pixel[0] > 150 and pixel[2] < 100:
            has_top = True
            break
    
    for x in range(width):
        # Bottom edge
        pixel = pixels[x, height-2]
        if pixel[0] > 150 and pixel[2] < 100:
            has_bottom = True
            break
    
    for y in range(height):
        # Left edge
        pixel = pixels[1, y]
        if pixel[0] > 150 and pixel[2] < 100:
            has_left = True
            break
    
    for y in range(height):
        # Right edge
        pixel = pixels[width-2, y]
        if pixel[0] > 150 and pixel[2] < 100:
            has_right = True
            break
    
    # Identify type based on connections
    connections = sum([has_top, has_bottom, has_left, has_right])
    
    if connections >= 3:
        return "CROSS"
    elif connections == 2:
        if has_top and has_bottom:
            return "VERT"
        elif has_left and has_right:
            return "HORT"
        elif has_top and has_right:
            return "NE"
        elif has_top and has_left:
            return "NW"
        elif has_bottom and has_right:
            return "SE"
        elif has_bottom and has_left:
            return "SW"
    elif connections == 1:
        if has_top:
            return "END_N"
        elif has_bottom:
            return "END_S"
        elif has_left:
            return "END_W"
        elif has_right:
            return "END_E"
    
    return "UNKNOWN"

if __name__ == "__main__":
    pipe_tiles = map_pipe_tiles()
    
    if pipe_tiles:
        # Update main mapping
        with open("aw2_mixed_tile_mapping.json", "r") as f:
            main_mapping = json.load(f)
        
        main_mapping["tiles"].update(pipe_tiles)
        
        with open("aw2_mixed_tile_mapping.json", "w") as f:
            json.dump(main_mapping, f, indent=2)
        
        print("\nUpdated main mapping file with pipe tiles")
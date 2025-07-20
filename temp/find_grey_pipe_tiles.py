#!/usr/bin/env python3
"""
Find pipe tiles - grey with yellow/green edges
"""

from PIL import Image, ImageDraw
import json

def find_grey_pipe_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Pipes are between roads and grass area
    # Roads end around y=68, grass/terrain starts around y=18 but x=238
    # So pipes might be in between these areas
    
    vis = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    print("Searching for grey pipe tiles with yellow/green edges...")
    
    pipe_tiles = {}
    vis_index = 0
    
    # Search area between roads and terrain
    # Let's check the area after roads horizontally
    search_areas = [
        # After road tiles horizontally
        {"name": "After roads row 2", "x_start": 102, "y_start": 17, "x_end": 238, "y_end": 35},
        {"name": "After roads row 3", "x_start": 102, "y_start": 34, "x_end": 238, "y_end": 52},
        {"name": "After roads row 4", "x_start": 102, "y_start": 51, "x_end": 238, "y_end": 69},
        {"name": "Row below roads", "x_start": 0, "y_start": 68, "x_end": 238, "y_end": 86},
    ]
    
    for area in search_areas:
        print(f"\nSearching {area['name']}...")
        
        # Check tiles on 17x17 grid
        for y in range(area['y_start'], area['y_end'], 17):
            for x in range(area['x_start'], area['x_end'], 17):
                if x + 16 <= tileset.width and y + 16 <= tileset.height:
                    tile = tileset.crop((x, y, x + 16, y + 16))
                    
                    # Check if it's a pipe tile
                    if is_grey_pipe_tile(tile):
                        print(f"  Found potential pipe at ({x}, {y})")
                        
                        # Add to visualization
                        if vis_index < 48:
                            vis_x = 20 + (vis_index % 8) * 95
                            vis_y = 20 + (vis_index // 8) * 95
                            
                            tile_scaled = tile.resize((64, 64), Image.NEAREST)
                            vis.paste(tile_scaled, (vis_x, vis_y))
                            draw.rectangle([vis_x-1, vis_y-1, vis_x+64, vis_y+64], outline=(255, 255, 255))
                            draw.text((vis_x, vis_y + 67), f"({x},{y})", fill=(200, 200, 200))
                            
                            # Identify pipe type
                            pipe_type = identify_grey_pipe_type(tile)
                            draw.text((vis_x, vis_y - 15), pipe_type, fill=(255, 255, 0))
                            
                            pipe_name = f"PIPE_{pipe_type.upper().replace(' ', '_').replace('-', '_')}"
                            pipe_tiles[pipe_name] = {
                                "x": x,
                                "y": y,
                                "width": 16,
                                "height": 16,
                                "description": f"Pipe - {pipe_type}"
                            }
                            
                            vis_index += 1
    
    vis.save("grey_pipe_tiles_found.png")
    print(f"\nFound {len(pipe_tiles)} pipe tiles")
    print("Created grey_pipe_tiles_found.png")
    
    return pipe_tiles

def is_grey_pipe_tile(tile):
    """Check if a tile is a grey pipe with yellow/green edges"""
    pixels = list(tile.getdata())
    grey_count = 0
    yellow_green_count = 0
    bg_count = 0
    
    for pixel in pixels:
        if len(pixel) >= 3:
            r, g, b = pixel[:3]
            
            # Background color
            if abs(r - 149) < 10 and abs(g - 177) < 10 and abs(b - 200) < 10:
                bg_count += 1
            # Grey (pipe body)
            elif abs(r - g) < 20 and abs(g - b) < 20 and 60 < r < 140:
                grey_count += 1
            # Yellow/green (pipe edges/details)
            elif (g > r and g > 150) or (r > 180 and g > 150 and b < 100):
                yellow_green_count += 1
    
    # Pipe tiles should have significant grey and some yellow/green
    total_non_bg = len(pixels) - bg_count
    return total_non_bg > 100 and grey_count > 50 and yellow_green_count > 5

def identify_grey_pipe_type(tile):
    """Identify the type of grey pipe tile"""
    pixels = tile.load()
    width, height = tile.size
    
    # Check edges for pipe connections by looking for grey pixels
    def has_pipe_edge(edge_pixels):
        grey_count = 0
        for pixel in edge_pixels:
            if len(pixel) >= 3:
                r, g, b = pixel[:3]
                if abs(r - g) < 20 and abs(g - b) < 20 and 60 < r < 140:
                    grey_count += 1
        return grey_count > len(edge_pixels) * 0.3
    
    # Get edge pixels
    top_edge = [pixels[x, 1] for x in range(2, width-2)]
    bottom_edge = [pixels[x, height-2] for x in range(2, width-2)]
    left_edge = [pixels[1, y] for y in range(2, height-2)]
    right_edge = [pixels[width-2, y] for y in range(2, height-2)]
    
    has_top = has_pipe_edge(top_edge)
    has_bottom = has_pipe_edge(bottom_edge)
    has_left = has_pipe_edge(left_edge)
    has_right = has_pipe_edge(right_edge)
    
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
            return "END-N"
        elif has_bottom:
            return "END-S"
        elif has_left:
            return "END-W"
        elif has_right:
            return "END-E"
    
    # Check for special pipe tiles
    # Count yellow/green pixels to identify special tiles
    yellow_green_count = 0
    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            if len(pixel) >= 3:
                r, g, b = pixel[:3]
                if (g > r and g > 150) or (r > 180 and g > 150 and b < 100):
                    yellow_green_count += 1
    
    if yellow_green_count > 50:
        return "SEAM"  # Pipe seam/joint
    
    return "PLAIN"

if __name__ == "__main__":
    pipe_tiles = find_grey_pipe_tiles()
    
    if pipe_tiles:
        # Update main mapping
        with open("aw2_mixed_tile_mapping.json", "r") as f:
            main_mapping = json.load(f)
        
        # Clean up any old pipe entries first
        old_pipe_keys = [k for k in main_mapping["tiles"].keys() if k.startswith("PIPE_")]
        for key in old_pipe_keys:
            del main_mapping["tiles"][key]
        
        main_mapping["tiles"].update(pipe_tiles)
        
        with open("aw2_mixed_tile_mapping.json", "w") as f:
            json.dump(main_mapping, f, indent=2)
        
        print("\nUpdated main mapping file with pipe tiles")
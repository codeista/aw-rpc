#!/usr/bin/env python3
"""
Find river tiles after the beach tiles
"""

from PIL import Image, ImageDraw
import json

def find_river_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Beach tiles were found around y=161-178
    # Rivers should be after that
    river_start_y = 195  # Start looking after the beach tiles
    
    print(f"Looking for river tiles starting from y={river_start_y}")
    
    # Create visualization
    vis = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    draw.text((400, 20), "River Tiles (4 frames each)", fill=(255, 255, 255), anchor="mm")
    
    river_types = {}
    vis_index = 0
    
    # Search for river tiles
    for row in range(8):  # Check 8 rows
        y = river_start_y + row * 17
        
        if y + 16 > tileset.height:
            break
            
        # Each river type has 4 frames horizontally
        for river_type_index in range(6):  # Check up to 6 different river types per row
            frames = []
            base_x = river_type_index * 68  # 4 frames * 17 pixels
            
            # Collect 4 animation frames
            all_frames_valid = True
            first_tile = None
            
            for frame in range(4):
                x = base_x + frame * 17
                
                if x + 16 <= tileset.width and y + 16 <= tileset.height:
                    tile = tileset.crop((x, y, x + 16, y + 16))
                    
                    # Check if it's a river tile
                    if is_river_tile(tile):
                        frames.append((x, y))
                        if frame == 0:
                            first_tile = tile
                    else:
                        all_frames_valid = False
                        break
                else:
                    all_frames_valid = False
                    break
            
            # If we found 4 valid river frames
            if all_frames_valid and len(frames) == 4 and first_tile is not None:
                river_name = identify_river_type(first_tile, base_x, y)
                
                if river_name and vis_index < 16:
                    # Show first frame
                    x, y = frames[0]
                    tile = tileset.crop((x, y, x + 16, y + 16))
                    tile_scaled = tile.resize((64, 64), Image.NEAREST)
                    
                    vis_x = 50 + (vis_index % 6) * 120
                    vis_y = 80 + (vis_index // 6) * 120
                    
                    vis.paste(tile_scaled, (vis_x, vis_y))
                    draw.rectangle([vis_x-1, vis_y-1, vis_x+64, vis_y+64], outline=(255, 255, 255))
                    draw.text((vis_x + 32, vis_y + 75), river_name, fill=(100, 200, 255), anchor="mm")
                    draw.text((vis_x + 32, vis_y + 90), f"({x},{y})", fill=(150, 150, 150), anchor="mm")
                    
                    # Store river tile info
                    river_types[f"RIVER_{river_name.upper().replace(' ', '_').replace('-', '_')}"] = {
                        "x": frames[0][0],
                        "y": frames[0][1],
                        "width": 16,
                        "height": 16,
                        "animation_frames": 4,
                        "frame_spacing": 17,
                        "description": f"River - {river_name} (animated)"
                    }
                    
                    print(f"Found river {river_name} at ({frames[0][0]}, {frames[0][1]}) with 4 frames")
                    vis_index += 1
    
    # Also check individual tiles that might not have 4 frames
    print("\nChecking for single river tiles...")
    for y in range(river_start_y, min(tileset.height, river_start_y + 170), 17):
        for x in range(0, min(tileset.width, 400), 17):
            if x + 16 <= tileset.width and y + 16 <= tileset.height:
                tile = tileset.crop((x, y, x + 16, y + 16))
                
                if is_river_tile(tile) and vis_index < 24:
                    # Check if this is part of an already found animation set
                    is_part_of_set = False
                    for river_info in river_types.values():
                        if y == river_info["y"] and abs(x - river_info["x"]) < 68:
                            is_part_of_set = True
                            break
                    
                    if not is_part_of_set:
                        river_name = identify_river_type(tile, x, y)
                        if river_name:
                            print(f"  Found single river tile {river_name} at ({x}, {y})")
    
    vis.save("river_tiles_found.png")
    print(f"\nFound {len(river_types)} river tile types")
    print("Created river_tiles_found.png")
    
    return river_types

def is_river_tile(tile):
    """Check if a tile is a river by looking for specific water colors"""
    pixels = list(tile.getdata())
    water_count = 0
    bg_count = 0
    green_blue_count = 0
    
    for pixel in pixels:
        if len(pixel) >= 3:
            r, g, b = pixel[:3]
            # Background color
            if abs(r - 149) < 10 and abs(g - 177) < 10 and abs(b - 200) < 10:
                bg_count += 1
            # Blue/teal water colors (rivers tend to be more teal/green-blue)
            elif b > 80 and g > 60 and r < 100 and (b > r + 20 or g > r + 20):
                water_count += 1
            # Green-blue (river specific)
            elif g > 100 and b > 100 and r < 80:
                green_blue_count += 1
    
    # Rivers should have water colors but not be all background
    total = len(pixels)
    return (water_count + green_blue_count) > 30 and bg_count < total * 0.7

def identify_river_type(tile, x, y):
    """Identify the type of river tile based on its pattern"""
    pixels = tile.load()
    width, height = tile.size
    
    # Check for water at edges to determine river direction
    has_water_top = False
    has_water_bottom = False
    has_water_left = False
    has_water_right = False
    
    # Check edges
    for i in range(width):
        # Top edge
        pixel = pixels[i, 0]
        if is_water_pixel(pixel):
            has_water_top = True
            break
    
    for i in range(width):
        # Bottom edge
        pixel = pixels[i, height-1]
        if is_water_pixel(pixel):
            has_water_bottom = True
            break
    
    for i in range(height):
        # Left edge
        pixel = pixels[0, i]
        if is_water_pixel(pixel):
            has_water_left = True
            break
    
    for i in range(height):
        # Right edge
        pixel = pixels[width-1, i]
        if is_water_pixel(pixel):
            has_water_right = True
            break
    
    # Determine river type based on water edges
    water_edges = sum([has_water_top, has_water_bottom, has_water_left, has_water_right])
    
    if water_edges >= 3:
        return "CROSS"
    elif water_edges == 2:
        if has_water_left and has_water_right:
            return "HORT"
        elif has_water_top and has_water_bottom:
            return "VERT"
        elif has_water_top and has_water_right:
            return "NE"
        elif has_water_top and has_water_left:
            return "NW"
        elif has_water_bottom and has_water_right:
            return "SE"
        elif has_water_bottom and has_water_left:
            return "SW"
    elif water_edges == 1:
        if has_water_top:
            return "END-N"
        elif has_water_bottom:
            return "END-S"
        elif has_water_left:
            return "END-W"
        elif has_water_right:
            return "END-E"
    
    # If no clear pattern, return a generic name based on position
    if y < 220:
        return "MOUTH"
    else:
        return "STREAM"

def is_water_pixel(pixel):
    """Check if a pixel is water colored"""
    if len(pixel) >= 3:
        r, g, b = pixel[:3]
        return (b > 80 and g > 60 and r < 100) or (g > 100 and b > 100 and r < 80)
    return False

if __name__ == "__main__":
    river_tiles = find_river_tiles()
    
    if river_tiles:
        # Update main mapping
        with open("aw2_mixed_tile_mapping.json", "r") as f:
            main_mapping = json.load(f)
        
        main_mapping["tiles"].update(river_tiles)
        
        with open("aw2_mixed_tile_mapping.json", "w") as f:
            json.dump(main_mapping, f, indent=2)
        
        print("\nUpdated main mapping file with river tiles")
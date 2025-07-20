#!/usr/bin/env python3
"""
Map pipe tiles with the correct coordinates
"""

from PIL import Image, ImageDraw
import json

def map_pipes_final():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # Correct pipe tile corners
    pipe_tl = (167, 166)
    pipe_tr = (182, 166)
    pipe_bl = (167, 181)
    pipe_br = (182, 181)
    
    # Calculate dimensions
    width = pipe_tr[0] - pipe_tl[0]  # 15
    height = pipe_bl[1] - pipe_tl[1]  # 15
    
    print(f"\nFirst pipe tile at ({pipe_tl[0]}, {pipe_tl[1]})")
    print(f"Tile size: {width}x{height}")
    
    # Grid size is 17x17 (15px tile + 2px separator)
    grid_size = 17
    
    # Create visualization
    vis = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    
    # Extract pipe area
    area_x = pipe_tl[0] - 10
    area_y = pipe_tl[1] - 10
    area = tileset.crop((area_x, area_y, area_x + 100, area_y + 100))
    area_scaled = area.resize((area.width * 4, area.height * 4), Image.NEAREST)
    vis.paste(area_scaled, (50, 50))
    
    draw = ImageDraw.Draw(vis)
    draw.text((400, 20), "Pipe Tiles - Final Mapping", fill=(255, 255, 255), anchor="mm")
    
    # Pipe tile patterns
    pipe_names = [
        # Row 0
        "PIPE_HORT", "PIPE_VERT", "PIPE_NE", "PIPE_SE",
        # Row 1
        "PIPE_SW", "PIPE_NW", "PIPE_CROSS", "PIPE_T_N",
        # Row 2
        "PIPE_T_E", "PIPE_T_S", "PIPE_T_W", "PIPE_END_N",
        # Row 3
        "PIPE_END_E", "PIPE_END_S", "PIPE_END_W", "PIPE_SEAM"
    ]
    
    # Map pipes
    pipe_mapping = {
        "pipe_tiles": {
            "description": "Pipe tiles - 15x15 pixels on 17x17 grid",
            "first_tile_corners": {
                "top_left": pipe_tl,
                "top_right": pipe_tr,
                "bottom_left": pipe_bl,
                "bottom_right": pipe_br
            },
            "tile_size": {"width": width, "height": height},
            "grid_size": grid_size,
            "grid_layout": "4x4",
            "special_notes": "Pink/magenta areas should be transparent",
            "tiles": []
        }
    }
    
    # Map the 4x4 grid of pipes
    tile_index = 0
    pipes_found = 0
    
    for row in range(4):
        for col in range(4):
            # Calculate position
            x = pipe_tl[0] + col * grid_size
            y = pipe_tl[1] + row * grid_size
            
            # Check if this tile exists and has content
            if x + width <= tileset.width and y + height <= tileset.height:
                # Sample the tile
                has_content = False
                pink_pixels = 0
                grey_pixels = 0
                
                for dy in range(height):
                    for dx in range(width):
                        pixel = tileset.getpixel((x + dx, y + dy))
                        r, g, b, a = pixel
                        
                        # Check for pink/magenta (transparent areas)
                        if r > 200 and b > 200 and g < 150:
                            pink_pixels += 1
                        # Check for grey pipe pixels
                        elif 50 < r < 150 and 50 < g < 150 and 50 < b < 150 and abs(r-g) < 20 and abs(g-b) < 20:
                            grey_pixels += 1
                            has_content = True
                        # Check for other content (not separator)
                        elif not (abs(r - 149) < 20 and abs(g - 177) < 20 and abs(b - 200) < 20):
                            if a > 0:
                                has_content = True
                
                if has_content:
                    tile_name = pipe_names[tile_index] if tile_index < len(pipe_names) else f"PIPE_{tile_index}"
                    
                    pipe_mapping["pipe_tiles"]["tiles"].append({
                        "name": tile_name,
                        "index": tile_index,
                        "grid_position": {"row": row, "col": col},
                        "x": x,
                        "y": y,
                        "width": width,
                        "height": height,
                        "has_pink": pink_pixels > 0,
                        "pink_pixels": pink_pixels,
                        "grey_pixels": grey_pixels
                    })
                    
                    pipes_found += 1
                    
                    # Draw on visualization
                    tile_vis_x = 50 + (x - area_x) * 4
                    tile_vis_y = 50 + (y - area_y) * 4
                    
                    draw.rectangle([tile_vis_x, tile_vis_y, 
                                   tile_vis_x + width * 4, tile_vis_y + height * 4], 
                                  outline=(255, 128, 0), width=2)
                    
                    # Mark if has pink
                    if pink_pixels > 0:
                        draw.text((tile_vis_x + width * 2, tile_vis_y + height * 2), 
                                 "P", fill=(255, 0, 255), anchor="mm")
                    
                    # Add tile number
                    draw.text((tile_vis_x + width * 2, tile_vis_y - 10), 
                             str(tile_index), fill=(255, 255, 255), anchor="mm")
                    
                    # Label
                    short_name = tile_name.replace("PIPE_", "")
                    draw.text((tile_vis_x + width * 2, tile_vis_y + height * 4 + 10), 
                             short_name, fill=(255, 128, 0), anchor="mm")
                    
                    print(f"  {tile_name:15s} at ({x:3d}, {y:3d})", end="")
                    if pink_pixels > 0:
                        print(f" - {pink_pixels} pink pixels")
                    else:
                        print()
            
            tile_index += 1
    
    # Draw grid overlay
    for i in range(5):  # 5 lines for 4x4 grid
        # Vertical lines
        x = 50 + (pipe_tl[0] - area_x + i * grid_size) * 4
        draw.line([(x, 50), (x, 50 + 80 * 4)], fill=(80, 80, 80), width=1)
        # Horizontal lines
        y = 50 + (pipe_tl[1] - area_y + i * grid_size) * 4
        draw.line([(50, y), (50 + 80 * 4, y)], fill=(80, 80, 80), width=1)
    
    # Info
    draw.text((50, 480), f"Pipe tiles: {width}x{height} pixels", fill=(255, 255, 255))
    draw.text((50, 500), f"Grid: 4x4 tiles on {grid_size}x{grid_size} spacing", fill=(255, 255, 255))
    draw.text((50, 520), f"Total pipes found: {pipes_found}/16", fill=(255, 128, 0))
    draw.text((50, 540), "P = Has pink/magenta (should be transparent)", fill=(255, 0, 255))
    draw.text((50, 560), "Orange = Pipe tile", fill=(255, 128, 0))
    
    # Save
    with open("pipe_tiles_final.json", "w") as f:
        json.dump(pipe_mapping, f, indent=2)
    
    vis.save("pipe_tiles_final.png")
    print(f"\nTotal pipe tiles mapped: {pipes_found}")
    print("Created pipe_tiles_final.png and pipe_tiles_final.json")

if __name__ == "__main__":
    map_pipes_final()
#!/usr/bin/env python3
"""
Map pipe tiles at the correct location
"""

from PIL import Image, ImageDraw
import json

def map_pipes_correct():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # First pipe tile corners
    pipe_tl = (164, 168)
    pipe_tr = (179, 178)  # Note: y is different
    pipe_bl = (164, 183)
    pipe_br = (179, 183)
    
    # Calculate dimensions
    width = pipe_br[0] - pipe_tl[0]  # 15
    height = pipe_br[1] - pipe_tl[1]  # 15
    
    print(f"\nFirst pipe tile at ({pipe_tl[0]}, {pipe_tl[1]})")
    print(f"Tile size: {width}x{height}")
    
    # The tiles are on a grid, likely 17x17 (15px tile + 2px separator)
    # Or could be 16x16 with 1px separator
    grid_size = 17  # Let's check
    
    # Create visualization
    vis = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    
    # Extract pipe area
    area_x = pipe_tl[0] - 10
    area_y = pipe_tl[1] - 10
    area = tileset.crop((area_x, area_y, area_x + 100, area_y + 100))
    area_scaled = area.resize((area.width * 4, area.height * 4), Image.NEAREST)
    vis.paste(area_scaled, (50, 50))
    
    draw = ImageDraw.Draw(vis)
    draw.text((400, 20), "Pipe Tiles at Correct Location", fill=(255, 255, 255), anchor="mm")
    
    # Mark the first pipe tile
    vis_x = 50 + (pipe_tl[0] - area_x) * 4
    vis_y = 50 + (pipe_tl[1] - area_y) * 4
    draw.rectangle([vis_x, vis_y, vis_x + width * 4, vis_y + height * 4], 
                   outline=(0, 255, 0), width=2)
    draw.text((vis_x + width * 2, vis_y - 15), "First pipe", fill=(0, 255, 0), anchor="mm")
    
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
    
    # Map pipes in 4x4 grid
    pipe_mapping = {
        "pipe_tiles": {
            "description": "Pipe tiles with correct positioning",
            "first_tile": {
                "top_left": pipe_tl,
                "dimensions": {"width": width, "height": height}
            },
            "grid_size": grid_size,
            "tile_size": {"width": width, "height": height},
            "special_notes": "Pipes have pink/magenta areas that should be transparent",
            "tiles": []
        }
    }
    
    # Map the 4x4 grid of pipes
    tile_index = 0
    
    for row in range(4):
        for col in range(4):
            # Calculate position based on grid
            x = pipe_tl[0] + col * grid_size
            y = pipe_tl[1] + row * grid_size
            
            # Check if this tile exists
            if x + width <= tileset.width and y + height <= tileset.height:
                # Sample the tile
                has_content = False
                pink_pixels = 0
                
                for dy in range(height):
                    for dx in range(width):
                        pixel = tileset.getpixel((x + dx, y + dy))
                        r, g, b, a = pixel
                        
                        # Check for pink/magenta
                        if r > 200 and b > 200 and g < 150:
                            pink_pixels += 1
                        # Check for content (not separator color)
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
                        "pink_pixels": pink_pixels
                    })
                    
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
                    
                    print(f"  {tile_name:15s} at ({x}, {y})")
                    if pink_pixels > 0:
                        print(f"    -> Has {pink_pixels} pink pixels (transparent areas)")
            
            tile_index += 1
    
    # Info
    draw.text((50, 500), f"Pipe tiles: {width}x{height} pixels", fill=(255, 255, 255))
    draw.text((50, 520), f"Grid spacing: {grid_size}x{grid_size}", fill=(255, 255, 255))
    draw.text((50, 540), f"Total pipes found: {len(pipe_mapping['pipe_tiles']['tiles'])}", fill=(255, 128, 0))
    draw.text((50, 560), "Pink areas (P) should be transparent when rendering", fill=(255, 0, 255))
    
    # Save
    with open("pipe_tiles_correct.json", "w") as f:
        json.dump(pipe_mapping, f, indent=2)
    
    vis.save("pipe_tiles_correct.png")
    print(f"\nTotal pipe tiles mapped: {len(pipe_mapping['pipe_tiles']['tiles'])}")
    print("Created pipe_tiles_correct.png and pipe_tiles_correct.json")

if __name__ == "__main__":
    map_pipes_correct()
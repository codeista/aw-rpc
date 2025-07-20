#!/usr/bin/env python3
"""
Map pipe tiles in the 4x4 grid section
"""

from PIL import Image, ImageDraw
import json

def map_pipe_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    print("\nPipe tiles are in 4x4 grid after road section")
    
    # Pipes come after roads (8 columns)
    # So they start at x = 8 * 9 = 72
    pipe_start_x = 8 * 9  # 72
    pipe_start_y = 0
    
    # Create visualization
    vis = Image.new('RGBA', (600, 400), (40, 40, 40, 255))
    
    # Extract pipe area (4x4 grid)
    # 4 columns * 9px = 36px wide
    # 4 rows * 9px = 36px tall
    grid_width = 4 * 9
    grid_height = 4 * 9
    
    pipe_area = tileset.crop((pipe_start_x, pipe_start_y, 
                             pipe_start_x + grid_width, 
                             pipe_start_y + grid_height))
    pipe_scaled = pipe_area.resize((pipe_area.width * 5, pipe_area.height * 5), Image.NEAREST)
    vis.paste(pipe_scaled, (50, 50))
    
    draw = ImageDraw.Draw(vis)
    draw.text((300, 20), "Pipe Tiles - 4x4 Grid", fill=(255, 255, 255), anchor="mm")
    
    # Pipe tile patterns
    pipe_names = [
        # Row 0
        "PIPE_HORT",      # Horizontal pipe
        "PIPE_VERT",      # Vertical pipe
        "PIPE_NE",        # Turn North-East
        "PIPE_SE",        # Turn South-East
        
        # Row 1
        "PIPE_SW",        # Turn South-West
        "PIPE_NW",        # Turn North-West
        "PIPE_CROSS",     # Cross intersection
        "PIPE_T_N",       # T-junction North
        
        # Row 2
        "PIPE_T_E",       # T-junction East
        "PIPE_T_S",       # T-junction South
        "PIPE_T_W",       # T-junction West
        "PIPE_END_N",     # End facing North
        
        # Row 3
        "PIPE_END_E",     # End facing East
        "PIPE_END_S",     # End facing South
        "PIPE_END_W",     # End facing West
        "PIPE_SEAM",      # Pipe seam/joint
    ]
    
    # Map the 4x4 grid
    pipe_mapping = {
        "pipe_tiles": {
            "description": "Pipe tiles in 4x4 grid",
            "grid_dimensions": {"columns": 4, "rows": 4},
            "tile_size": 8,
            "grid_spacing": 9,
            "start_position": {"x": pipe_start_x, "y": pipe_start_y},
            "special_notes": "Pipes have pink/magenta areas that should be transparent",
            "tiles": []
        }
    }
    
    # Check each position in the 4x4 grid
    grid_index = 0
    
    for row in range(4):
        for col in range(4):
            x = pipe_start_x + col * 9
            y = pipe_start_y + row * 9
            
            # Check if this tile has content
            has_content = False
            pink_pixels = 0
            grey_pixels = 0
            
            for dy in range(8):
                for dx in range(8):
                    pixel = tileset.getpixel((x + dx, y + dy))
                    r, g, b, a = pixel
                    
                    # Check for pink/magenta (transparent areas)
                    if r > 200 and b > 200 and g < 150:
                        pink_pixels += 1
                    # Check for grey pipe pixels
                    elif 60 < r < 120 and 60 < g < 120 and 60 < b < 120:
                        grey_pixels += 1
                        has_content = True
                    # Check for separator
                    elif abs(r - 149) < 20 and abs(g - 177) < 20 and abs(b - 200) < 20:
                        pass  # Separator
                    elif a > 0:
                        has_content = True
            
            # Determine tile status
            if grey_pixels > 10:  # Has pipe content
                status = "pipe"
                tile_name = pipe_names[grid_index] if grid_index < len(pipe_names) else f"PIPE_{grid_index}"
            elif has_content:
                status = "other"
                tile_name = "UNKNOWN"
            else:
                status = "empty"
                tile_name = "EMPTY"
            
            # Add to mapping
            pipe_mapping["pipe_tiles"]["tiles"].append({
                "grid_position": {"row": row, "col": col},
                "index": grid_index,
                "x": x,
                "y": y,
                "name": tile_name,
                "status": status,
                "pink_pixels": pink_pixels,
                "notes": "Pink areas should be transparent" if pink_pixels > 0 else ""
            })
            
            # Draw on visualization
            vis_x = 50 + col * 45  # 9 * 5 scale
            vis_y = 50 + row * 45
            
            if status == "empty":
                # Draw empty indicator
                draw.rectangle([vis_x, vis_y, vis_x + 40, vis_y + 40], 
                             outline=(100, 100, 100), width=1)
                draw.line([(vis_x, vis_y), (vis_x + 40, vis_y + 40)], 
                         fill=(100, 100, 100), width=1)
            elif status == "pipe":
                # Draw pipe tile
                draw.rectangle([vis_x, vis_y, vis_x + 40, vis_y + 40], 
                             outline=(255, 128, 0), width=2)
                
                # If has pink, mark it
                if pink_pixels > 0:
                    draw.text((vis_x + 20, vis_y + 20), "P", 
                             fill=(255, 0, 255), anchor="mm")
            else:
                # Other content
                draw.rectangle([vis_x, vis_y, vis_x + 40, vis_y + 40], 
                             outline=(200, 200, 200), width=1)
            
            # Add grid position
            draw.text((vis_x + 20, vis_y - 10), f"{row},{col}", 
                     fill=(255, 255, 255), anchor="mm")
            
            # Add name for pipe tiles
            if status == "pipe":
                short_name = tile_name.replace("PIPE_", "")
                draw.text((vis_x + 20, vis_y + 50), short_name, 
                         fill=(255, 128, 0), anchor="mm")
            
            grid_index += 1
    
    # Draw grid lines
    for i in range(5):  # Columns
        x = 50 + i * 45  # 9 * 5 scale
        draw.line([(x, 50), (x, 50 + 180)], fill=(80, 80, 80), width=1)
    for i in range(5):  # Rows
        y = 50 + i * 45
        draw.line([(50, y), (50 + 180, y)], fill=(80, 80, 80), width=1)
    
    # Summary
    total_tiles = len(pipe_mapping["pipe_tiles"]["tiles"])
    pipe_tiles = sum(1 for t in pipe_mapping["pipe_tiles"]["tiles"] if t["status"] == "pipe")
    empty_tiles = sum(1 for t in pipe_mapping["pipe_tiles"]["tiles"] if t["status"] == "empty")
    
    draw.text((50, 250), f"4x4 Grid Analysis:", fill=(255, 255, 255))
    draw.text((50, 270), f"Pipe tiles: {pipe_tiles}", fill=(255, 128, 0))
    draw.text((50, 290), f"Empty tiles: {empty_tiles}", fill=(100, 100, 100))
    
    draw.text((50, 320), "Orange = Pipe tile", fill=(255, 128, 0))
    draw.text((50, 340), "P = Has pink/magenta (should be transparent)", fill=(255, 0, 255))
    draw.text((50, 360), "Grey X = Empty position", fill=(100, 100, 100))
    
    # Print summary
    print(f"\nPipe tiles found: {pipe_tiles}")
    for tile in pipe_mapping["pipe_tiles"]["tiles"]:
        if tile["status"] == "pipe":
            print(f"  {tile['name']:15s} at ({tile['x']:3d}, {tile['y']:3d})", end="")
            if tile['pink_pixels'] > 0:
                print(f" - has {tile['pink_pixels']} pink pixels")
            else:
                print()
    
    # Save
    with open("pipe_tiles_4x4_grid.json", "w") as f:
        json.dump(pipe_mapping, f, indent=2)
    
    vis.save("pipe_tiles_4x4_grid.png")
    print("\nCreated pipe_tiles_4x4_grid.png and pipe_tiles_4x4_grid.json")

if __name__ == "__main__":
    map_pipe_tiles()
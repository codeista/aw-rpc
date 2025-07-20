#!/usr/bin/env python3
"""
Map road tiles in exact 8x4 grid as specified
"""

from PIL import Image, ImageDraw
import json

def map_road_8x4_grid():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    print("\nRoad tiles are in 8x4 grid (8 columns, 4 rows)")
    
    # Create visualization
    vis = Image.new('RGBA', (800, 400), (40, 40, 40, 255))
    
    # Extract exact 8x4 grid area
    # 8 columns * 9px = 72px wide
    # 4 rows * 9px = 36px tall
    grid_width = 8 * 9
    grid_height = 4 * 9
    
    road_area = tileset.crop((0, 0, grid_width, grid_height))
    road_scaled = road_area.resize((road_area.width * 4, road_area.height * 4), Image.NEAREST)
    vis.paste(road_scaled, (50, 50))
    
    draw = ImageDraw.Draw(vis)
    draw.text((400, 20), "Road Tiles - 8x4 Grid", fill=(255, 255, 255), anchor="mm")
    
    # Map the 8x4 grid
    road_mapping = {
        "road_tiles": {
            "description": "Road tiles in 8x4 grid",
            "grid_dimensions": {"columns": 8, "rows": 4},
            "tile_size": 8,
            "grid_spacing": 9,
            "start_position": {"x": 0, "y": 0},
            "tiles": []
        }
    }
    
    # Standard road patterns (in order)
    road_names = [
        # Row 0
        "ROAD_HORT", "ROAD_VERT", "ROAD_NE", "ROAD_SE", 
        "ROAD_SW", "ROAD_NW", "ROAD_CROSS", "ROAD_T_N",
        
        # Row 1  
        "ROAD_T_E", "ROAD_T_S", "ROAD_T_W", "ROAD_END_N",
        "ROAD_END_E", "ROAD_END_S", "ROAD_END_W", "EMPTY",
        
        # Row 2
        "EMPTY", "EMPTY", "EMPTY", "EMPTY",
        "EMPTY", "EMPTY", "EMPTY", "EMPTY",
        
        # Row 3
        "EMPTY", "EMPTY", "EMPTY", "EMPTY", 
        "EMPTY", "EMPTY", "EMPTY", "EMPTY"
    ]
    
    # Check each position in the 8x4 grid
    grid_index = 0
    
    for row in range(4):
        for col in range(8):
            x = col * 9
            y = row * 9
            
            # Check if this tile has content
            has_content = False
            empty_pixels = 0
            total_pixels = 64  # 8x8
            
            for dy in range(8):
                for dx in range(8):
                    pixel = tileset.getpixel((x + dx, y + dy))
                    
                    # Check if separator color
                    if abs(pixel[0] - 149) < 20 and abs(pixel[1] - 177) < 20 and abs(pixel[2] - 200) < 20:
                        empty_pixels += 1
                    elif pixel[3] == 0:  # Transparent
                        empty_pixels += 1
                    else:
                        has_content = True
            
            # Determine tile status
            is_empty = empty_pixels > 50  # Most pixels are empty
            is_partial = has_content and empty_pixels > 20  # Some content but also empty
            
            tile_name = road_names[grid_index] if grid_index < len(road_names) else "UNKNOWN"
            
            if is_empty:
                tile_name = "EMPTY"
                status = "empty"
            elif is_partial:
                status = "partial"
            else:
                status = "full"
            
            # Add to mapping
            road_mapping["road_tiles"]["tiles"].append({
                "grid_position": {"row": row, "col": col},
                "index": grid_index,
                "x": x,
                "y": y,
                "name": tile_name,
                "status": status
            })
            
            # Draw on visualization
            vis_x = 50 + x * 4
            vis_y = 50 + y * 4
            
            if status == "empty":
                # Draw empty indicator
                draw.rectangle([vis_x, vis_y, vis_x + 32, vis_y + 32], 
                             outline=(100, 100, 100), width=1)
                draw.line([(vis_x, vis_y), (vis_x + 32, vis_y + 32)], 
                         fill=(100, 100, 100), width=1)
            elif status == "partial":
                # Draw partial indicator
                draw.rectangle([vis_x, vis_y, vis_x + 32, vis_y + 32], 
                             outline=(255, 150, 0), width=2)
                draw.text((vis_x + 16, vis_y + 16), "P", 
                         fill=(255, 150, 0), anchor="mm")
            else:
                # Draw full tile
                draw.rectangle([vis_x, vis_y, vis_x + 32, vis_y + 32], 
                             outline=(0, 255, 0), width=2)
            
            # Add grid position
            draw.text((vis_x + 16, vis_y - 10), f"{row},{col}", 
                     fill=(255, 255, 255), anchor="mm")
            
            grid_index += 1
    
    # Draw grid lines
    for i in range(9):  # Columns
        x = 50 + i * 36  # 9 * 4 scale
        draw.line([(x, 50), (x, 50 + 144)], fill=(80, 80, 80), width=1)
    for i in range(5):  # Rows
        y = 50 + i * 36
        draw.line([(50, y), (50 + 288, y)], fill=(80, 80, 80), width=1)
    
    # Summary
    total_tiles = len(road_mapping["road_tiles"]["tiles"])
    full_tiles = sum(1 for t in road_mapping["road_tiles"]["tiles"] if t["status"] == "full")
    empty_tiles = sum(1 for t in road_mapping["road_tiles"]["tiles"] if t["status"] == "empty")
    partial_tiles = sum(1 for t in road_mapping["road_tiles"]["tiles"] if t["status"] == "partial")
    
    draw.text((50, 220), f"8x4 Grid Analysis:", fill=(255, 255, 255))
    draw.text((50, 240), f"Total positions: {total_tiles}", fill=(200, 200, 200))
    draw.text((50, 260), f"Full tiles: {full_tiles}", fill=(0, 255, 0))
    draw.text((50, 280), f"Empty tiles: {empty_tiles}", fill=(100, 100, 100))
    draw.text((50, 300), f"Partial tiles: {partial_tiles}", fill=(255, 150, 0))
    
    draw.text((50, 330), "Green = Full road tile", fill=(0, 255, 0))
    draw.text((50, 350), "Grey X = Empty position", fill=(100, 100, 100))
    draw.text((50, 370), "Orange P = Partial content", fill=(255, 150, 0))
    
    # Save
    with open("road_tiles_8x4_grid.json", "w") as f:
        json.dump(road_mapping, f, indent=2)
    
    vis.save("road_tiles_8x4_grid.png")
    print(f"\nGrid analysis complete:")
    print(f"Full tiles: {full_tiles}")
    print(f"Empty tiles: {empty_tiles}")
    print(f"Partial tiles: {partial_tiles}")
    print("\nCreated road_tiles_8x4_grid.png and road_tiles_8x4_grid.json")

if __name__ == "__main__":
    map_road_8x4_grid()
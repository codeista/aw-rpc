#!/usr/bin/env python3
"""
Detailed analysis of terrain tiles with visual output
"""

from PIL import Image, ImageDraw, ImageFont
import json

def analyze_terrain_grid():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Create larger visualization
    vis = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    # Starting position for terrain tiles
    terrain_x = 238
    terrain_y = 18
    grid_step = 17
    
    # Try to use a simple font
    try:
        from PIL import ImageFont
        font = ImageFont.load_default()
    except:
        font = None
    
    # Analyze multiple rows
    tile_data = []
    
    for row in range(4):  # Check 4 rows
        y = terrain_y + (row * grid_step)
        if y + 16 > tileset.height:
            break
            
        for col in range(6):  # Check 6 columns
            x = terrain_x + (col * grid_step)
            if x + 16 > tileset.width:
                break
            
            # Extract tile
            tile = tileset.crop((x, y, x + 16, y + 16))
            
            # Check if it's not just background
            pixels = list(tile.getdata())
            bg_count = 0
            color_sum = [0, 0, 0]
            pixel_count = 0
            
            for pixel in pixels:
                if len(pixel) >= 3:
                    r, g, b = pixel[:3]
                    if abs(r - 149) < 10 and abs(g - 177) < 10 and abs(b - 200) < 10:
                        bg_count += 1
                    else:
                        color_sum[0] += r
                        color_sum[1] += g
                        color_sum[2] += b
                        pixel_count += 1
            
            if bg_count < len(pixels) * 0.9:  # Has content
                # Place in visualization
                tile_scaled = tile.resize((64, 64), Image.NEAREST)
                vis_x = 20 + col * 70
                vis_y = 20 + row * 100
                
                vis.paste(tile_scaled, (vis_x, vis_y))
                draw.rectangle([vis_x-1, vis_y-1, vis_x+64, vis_y+64], outline=(100, 100, 100))
                
                # Add coordinates
                coord_text = f"({x},{y})"
                draw.text((vis_x, vis_y + 67), coord_text, fill=(200, 200, 200), font=font)
                
                # Calculate average color
                if pixel_count > 0:
                    avg_color = (
                        color_sum[0] // pixel_count,
                        color_sum[1] // pixel_count,
                        color_sum[2] // pixel_count
                    )
                    
                    # Color indicator
                    draw.rectangle([vis_x, vis_y + 80, vis_x + 64, vis_y + 90], 
                                 fill=avg_color, outline=(150, 150, 150))
                
                tile_data.append({
                    "row": row,
                    "col": col,
                    "x": x,
                    "y": y,
                    "has_content": True,
                    "avg_color": avg_color if pixel_count > 0 else None
                })
    
    # Add labels for known tiles
    known_positions = [
        (238, 18, "PLAIN"),
        (255, 18, "FOREST?"),
        (272, 18, "MOUNTAIN?"),
        (238, 35, "ROAD?"),
    ]
    
    for x, y, label in known_positions:
        # Find matching tile
        for data in tile_data:
            if data['x'] == x and data['y'] == y:
                vis_x = 20 + data['col'] * 70
                vis_y = 20 + data['row'] * 100
                draw.text((vis_x, vis_y - 15), label, fill=(255, 255, 0), font=font)
    
    vis.save("terrain_grid_analysis.png")
    print("Created terrain_grid_analysis.png")
    
    # Now let's properly identify tiles based on the game's terrain types
    terrain_mapping = {
        "PLAIN": {"x": 238, "y": 18, "description": "Plain terrain (yellow/tan)"},
        "WOOD": {"x": 255, "y": 18, "description": "Forest (has trees)"},
        "MOUNTAIN": {"x": 272, "y": 18, "description": "Mountain (rocky terrain)"},
        "ROAD_HORT": {"x": 238, "y": 35, "description": "Horizontal road"},
        "ROAD_VERT": {"x": 255, "y": 35, "description": "Vertical road"},
        "ROAD_CROSS": {"x": 272, "y": 35, "description": "Road intersection"},
        "ROAD_NE": {"x": 289, "y": 35, "description": "Road turn NE"},
        "ROAD_SE": {"x": 306, "y": 35, "description": "Road turn SE"},
        "ROAD_NW": {"x": 323, "y": 35, "description": "Road turn NW"},
        "ROAD_SW": {"x": 238, "y": 52, "description": "Road turn SW"},
        "RIVER_HORT": {"x": 255, "y": 52, "description": "Horizontal river"},
        "RIVER_VERT": {"x": 272, "y": 52, "description": "Vertical river"}
    }
    
    # Create final mapping file
    final_mapping = {
        "metadata": {
            "source": tileset_path,
            "grid_size": 17,
            "tile_size": 16,
            "terrain_start": {"x": 238, "y": 18}
        },
        "tiles": {}
    }
    
    for name, info in terrain_mapping.items():
        final_mapping["tiles"][name] = {
            "x": info["x"],
            "y": info["y"],
            "width": 16,
            "height": 16,
            "description": info["description"]
        }
    
    # Add water tiles which seem to be in a different section
    # Based on the original mapping, water tiles were around (0, 149) as 8x8 tiles
    # Let's check that area
    water_y = 149
    water_tiles = {
        "SEA": {"x": 0, "y": water_y, "size": 8},
        "REEF": {"x": 81, "y": water_y, "size": 8},
        "SHOAL": {"x": 90, "y": water_y, "size": 8}
    }
    
    for name, info in water_tiles.items():
        final_mapping["tiles"][name] = {
            "x": info["x"],
            "y": info["y"],
            "width": info["size"],
            "height": info["size"],
            "description": f"{name} water tile"
        }
    
    with open("aw2_terrain_mapping_corrected.json", "w") as f:
        json.dump(final_mapping, f, indent=2)
    
    print("Created aw2_terrain_mapping_corrected.json")

if __name__ == "__main__":
    analyze_terrain_grid()
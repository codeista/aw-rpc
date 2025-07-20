#!/usr/bin/env python3
"""
Map terrain tiles based on the 17x17 grid pattern
"""

from PIL import Image
import json

def map_terrain_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Based on the separator analysis, terrain tiles start after x=237
    # and are on a 17x17 grid (16x16 tile + 1px separator)
    
    # PLAIN is at (238, 18), so let's use that as our reference
    terrain_start_x = 238
    terrain_start_y = 18
    grid_step = 17  # 16px tile + 1px separator
    
    terrain_tiles = {}
    
    # Map the first row of terrain tiles
    terrain_names = [
        "PLAIN",
        "GRASS",
        "WOOD", 
        "MOUNTAIN",
        "UNKNOWN1",
        "UNKNOWN2"
    ]
    
    print("Mapping terrain tiles on 17x17 grid:")
    print(f"Starting from PLAIN at ({terrain_start_x}, {terrain_start_y})")
    print("-" * 60)
    
    for i, name in enumerate(terrain_names):
        x = terrain_start_x + (i * grid_step)
        y = terrain_start_y
        
        if x + 16 <= tileset.width:
            # Extract tile
            tile = tileset.crop((x, y, x + 16, y + 16))
            
            # Analyze dominant color
            pixels = list(tile.getdata())
            color_sum = [0, 0, 0]
            count = 0
            
            for pixel in pixels:
                if len(pixel) >= 3 and (len(pixel) < 4 or pixel[3] > 0):
                    color_sum[0] += pixel[0]
                    color_sum[1] += pixel[1]
                    color_sum[2] += pixel[2]
                    count += 1
            
            if count > 0:
                avg_color = tuple(c // count for c in color_sum)
                r, g, b = avg_color
                
                # Try to identify tile type
                description = ""
                if r > 180 and g > 160 and b < 150:  # Yellowish
                    description = "Plain/field (tan/yellow)"
                elif g > r and g > b and g > 120:  # Green dominant
                    if g > 150:
                        description = "Grass (bright green)"
                    else:
                        description = "Forest/woods (darker green)"
                elif abs(r - g) < 30 and abs(g - b) < 30:  # Greyish
                    if r > 150:
                        description = "Mountain/rock (light grey)"
                    else:
                        description = "Road/path (darker grey)"
                elif b > r and b > g:  # Blue dominant
                    description = "Water/sea"
                
                terrain_tiles[name] = {
                    "x": x,
                    "y": y,
                    "width": 16,
                    "height": 16,
                    "avg_color": avg_color,
                    "description": description
                }
                
                print(f"{name:12} at ({x:3}, {y:3}): RGB{avg_color} - {description}")
    
    # Check second row of terrain (y + 17)
    print("\nChecking second row of terrain tiles:")
    second_row_y = terrain_start_y + grid_step
    
    for i in range(6):
        x = terrain_start_x + (i * grid_step)
        y = second_row_y
        
        if x + 16 <= tileset.width and y + 16 <= tileset.height:
            tile = tileset.crop((x, y, x + 16, y + 16))
            pixels = list(tile.getdata())
            
            # Check if it's not just background
            bg_count = 0
            for pixel in pixels:
                if len(pixel) >= 3:
                    r, g, b = pixel[:3]
                    if abs(r - 149) < 10 and abs(g - 177) < 10 and abs(b - 200) < 10:
                        bg_count += 1
            
            if bg_count < len(pixels) * 0.9:  # Not mostly background
                print(f"  Tile at ({x:3}, {y:3}): Has content")
    
    # Save updated mapping
    mapping = {
        "metadata": {
            "source": "Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png",
            "render_size": 16,
            "grid_size": 17,
            "description": "AW2 RGB tileset with 17x17 grid (16x16 tiles + 1px separators)"
        },
        "tiles": terrain_tiles
    }
    
    with open("terrain_tile_mapping.json", "w") as f:
        json.dump(mapping, f, indent=2)
    
    print(f"\nSaved terrain mapping to terrain_tile_mapping.json")
    
    # Create visual grid
    vis = Image.new('RGBA', (400, 200), (40, 40, 40, 255))
    
    for i, (name, info) in enumerate(terrain_tiles.items()):
        if i < 6:  # First row
            tile = tileset.crop((info['x'], info['y'], info['x'] + 16, info['y'] + 16))
            tile_scaled = tile.resize((64, 64), Image.NEAREST)
            x_pos = 10 + i * 65
            y_pos = 10
            vis.paste(tile_scaled, (x_pos, y_pos))
    
    vis.save("terrain_tiles_grid.png")
    print("Created terrain_tiles_grid.png")

if __name__ == "__main__":
    map_terrain_tiles()
#!/usr/bin/env python3
"""
Map terrain tiles (plain, mountain, trees/wood)
"""

from PIL import Image, ImageDraw
import json

def map_terrain_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # Plain tile corners
    plain_tl = (232, 90)
    plain_tr = (247, 90)
    plain_bl = (232, 105)
    plain_br = (247, 105)
    
    # Calculate dimensions
    width = plain_tr[0] - plain_tl[0]  # 15
    height = plain_bl[1] - plain_tl[1]  # 15
    
    print(f"\nFirst terrain tile (PLAIN) at ({plain_tl[0]}, {plain_tl[1]})")
    print(f"Tile size: {width}x{height}")
    
    # Grid size (likely 17x17 like pipes)
    grid_size = 17
    
    # Create visualization
    vis = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    
    # Extract terrain area
    area_x = plain_tl[0] - 20
    area_y = plain_tl[1] - 20
    area = tileset.crop((area_x, area_y, area_x + 120, area_y + 120))
    area_scaled = area.resize((area.width * 3, area.height * 3), Image.NEAREST)
    vis.paste(area_scaled, (50, 50))
    
    draw = ImageDraw.Draw(vis)
    draw.text((400, 20), "Terrain Tiles", fill=(255, 255, 255), anchor="mm")
    
    # Terrain tile names
    # Based on what we know, we have plain, wood/forest, and mountain
    terrain_names = [
        "PLAIN",      # Grass/field
        "WOOD",       # Forest/trees
        "MOUNTAIN",   # Mountain
        # There might be more terrain types
    ]
    
    # Map terrain tiles
    terrain_mapping = {
        "terrain_tiles": {
            "description": "Terrain tiles - 15x15 pixels",
            "first_tile_corners": {
                "top_left": plain_tl,
                "top_right": plain_tr,
                "bottom_left": plain_bl,
                "bottom_right": plain_br
            },
            "tile_size": {"width": width, "height": height},
            "grid_size": grid_size,
            "tiles": []
        }
    }
    
    # Check for terrain tiles in the area
    # They might be arranged horizontally or in a grid
    tiles_found = 0
    
    # Check horizontally first (common for terrain)
    for i in range(5):  # Check up to 5 positions
        x = plain_tl[0] + i * grid_size
        y = plain_tl[1]
        
        if x + width <= tileset.width:
            # Sample the tile
            has_content = False
            
            # Get dominant color to identify terrain type
            color_counts = {}
            
            for dy in range(height):
                for dx in range(width):
                    pixel = tileset.getpixel((x + dx, y + dy))
                    r, g, b, a = pixel
                    
                    # Skip separator colors
                    if not (abs(r - 149) < 20 and abs(g - 177) < 20 and abs(b - 200) < 20):
                        if a > 0:
                            has_content = True
                            
                            # Categorize color
                            if g > r and g > b:  # Greenish
                                color_type = "GREEN"
                            elif r > 180 and g > 150:  # Tan/yellow
                                color_type = "TAN"
                            elif r < 100 and g < 100 and b < 100:  # Dark
                                color_type = "DARK"
                            elif abs(r - g) < 20 and abs(g - b) < 20:  # Grey
                                color_type = "GREY"
                            else:
                                color_type = "OTHER"
                            
                            color_counts[color_type] = color_counts.get(color_type, 0) + 1
            
            if has_content:
                # Determine terrain type based on colors
                dominant_color = max(color_counts.items(), key=lambda x: x[1])[0] if color_counts else "NONE"
                
                if i == 0:  # First tile is PLAIN
                    tile_name = "PLAIN"
                    terrain_type = "Plain/Field"
                elif dominant_color == "GREEN" or dominant_color == "DARK":
                    tile_name = "WOOD"
                    terrain_type = "Forest/Trees"
                elif dominant_color == "GREY":
                    tile_name = "MOUNTAIN"
                    terrain_type = "Mountain"
                else:
                    tile_name = f"TERRAIN_{i}"
                    terrain_type = f"Unknown terrain (color: {dominant_color})"
                
                terrain_mapping["terrain_tiles"]["tiles"].append({
                    "name": tile_name,
                    "index": tiles_found,
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "type": terrain_type,
                    "dominant_color": dominant_color
                })
                
                tiles_found += 1
                
                # Draw on visualization
                tile_vis_x = 50 + (x - area_x) * 3
                tile_vis_y = 50 + (y - area_y) * 3
                
                # Color based on type
                if tile_name == "PLAIN":
                    outline_color = (255, 200, 100)  # Sandy
                elif tile_name == "WOOD":
                    outline_color = (0, 200, 0)  # Green
                elif tile_name == "MOUNTAIN":
                    outline_color = (150, 150, 150)  # Grey
                else:
                    outline_color = (255, 255, 255)  # White
                
                draw.rectangle([tile_vis_x, tile_vis_y, 
                               tile_vis_x + width * 3, tile_vis_y + height * 3], 
                              outline=outline_color, width=2)
                
                # Label
                draw.text((tile_vis_x + width * 1.5, tile_vis_y - 10), 
                         tile_name, fill=outline_color, anchor="mm")
                
                print(f"  {tile_name:10s} at ({x:3d}, {y:3d}) - {terrain_type}")
    
    # Also check vertically in case there are more terrain types
    for i in range(1, 4):  # Check rows below
        x = plain_tl[0]
        y = plain_tl[1] + i * grid_size
        
        if y + height <= tileset.height:
            # Quick check for content
            has_content = False
            for dy in range(0, height, 3):
                for dx in range(0, width, 3):
                    pixel = tileset.getpixel((x + dx, y + dy))
                    if not (abs(pixel[0] - 149) < 20 and abs(pixel[1] - 177) < 20 and abs(pixel[2] - 200) < 20):
                        if pixel[3] > 0:
                            has_content = True
                            break
                if has_content:
                    break
            
            if has_content:
                print(f"  Additional terrain found at ({x}, {y})")
    
    # Draw grid
    for i in range(6):  # Show 5x5 grid area
        # Vertical lines
        x = 50 + (plain_tl[0] - area_x + i * grid_size) * 3
        if x < 50 + 360:
            draw.line([(x, 50), (x, 50 + 360)], fill=(80, 80, 80), width=1)
        # Horizontal lines
        y = 50 + (plain_tl[1] - area_y + i * grid_size) * 3
        if y < 50 + 360:
            draw.line([(50, y), (50 + 360, y)], fill=(80, 80, 80), width=1)
    
    # Info
    draw.text((50, 450), f"Terrain tiles: {width}x{height} pixels", fill=(255, 255, 255))
    draw.text((50, 470), f"Grid spacing: {grid_size}x{grid_size}", fill=(255, 255, 255))
    draw.text((50, 490), f"Terrain types found: {tiles_found}", fill=(255, 255, 255))
    
    draw.text((50, 520), "Tile types:", fill=(255, 255, 255))
    draw.text((50, 540), "Sandy = Plain/Field", fill=(255, 200, 100))
    draw.text((50, 560), "Green = Forest/Wood", fill=(0, 200, 0))
    draw.text((250, 540), "Grey = Mountain", fill=(150, 150, 150))
    
    # Save
    with open("terrain_tiles.json", "w") as f:
        json.dump(terrain_mapping, f, indent=2)
    
    vis.save("terrain_tiles.png")
    print(f"\nTotal terrain tiles mapped: {tiles_found}")
    print("Created terrain_tiles.png and terrain_tiles.json")

if __name__ == "__main__":
    map_terrain_tiles()
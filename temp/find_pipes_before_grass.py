#!/usr/bin/env python3
"""
Find pipe tiles one tile width back from grass area
"""

from PIL import Image, ImageDraw
import json

def find_pipes_before_grass():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Grass starts at x=238, so one tile back (17 pixels) would be x=221
    # Let's check the column at x=221 and surrounding area
    
    vis = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    print("Looking for pipes one tile back from grass area...")
    print("Grass starts at x=238, checking x=221 and nearby columns")
    
    pipe_tiles = {}
    vis_index = 0
    
    # Check columns just before grass
    x_positions = [204, 221]  # Two tiles back and one tile back
    
    for x in x_positions:
        print(f"\nChecking column at x={x}:")
        
        # Check multiple rows
        for row in range(6):
            y = row * 17
            
            if x + 16 <= tileset.width and y + 16 <= tileset.height:
                tile = tileset.crop((x, y, x + 16, y + 16))
                
                # Save each tile for inspection
                tile.save(f"check_x{x}_y{y}.png")
                
                # Add to visualization
                if vis_index < 24:
                    vis_x = 20 + (vis_index % 6) * 120
                    vis_y = 20 + (vis_index // 6) * 120
                    
                    tile_scaled = tile.resize((96, 96), Image.NEAREST)
                    vis.paste(tile_scaled, (vis_x, vis_y))
                    draw.rectangle([vis_x-1, vis_y-1, vis_x+96, vis_y+96], outline=(255, 255, 255))
                    draw.text((vis_x, vis_y + 100), f"({x},{y})", fill=(200, 200, 200))
                    
                    # Analyze tile
                    tile_type = analyze_tile(tile)
                    if tile_type != "BACKGROUND":
                        draw.text((vis_x, vis_y - 15), tile_type, fill=(255, 255, 0))
                        print(f"  Found {tile_type} at ({x}, {y})")
                        
                        if "PIPE" in tile_type:
                            pipe_name = f"PIPE_{tile_type.replace('PIPE ', '').upper()}"
                            pipe_tiles[pipe_name] = {
                                "x": x,
                                "y": y,
                                "width": 16,
                                "height": 16,
                                "description": tile_type
                            }
                    
                    vis_index += 1
    
    # Also check the area between roads and grass more systematically
    print("\n\nChecking area between roads and grass (x=102 to x=237):")
    
    vis2 = Image.new('RGBA', (800, 400), (40, 40, 40, 255))
    draw2 = ImageDraw.Draw(vis2)
    vis_index2 = 0
    
    # Sample every 17 pixels in the gap
    for x in range(102, 238, 17):
        for y in range(0, 86, 17):
            if x + 16 <= tileset.width and y + 16 <= tileset.height:
                tile = tileset.crop((x, y, x + 16, y + 16))
                
                if vis_index2 < 40:
                    vis_x = 20 + (vis_index2 % 10) * 75
                    vis_y = 20 + (vis_index2 // 10) * 90
                    
                    tile_scaled = tile.resize((64, 64), Image.NEAREST)
                    vis2.paste(tile_scaled, (vis_x, vis_y))
                    draw2.rectangle([vis_x-1, vis_y-1, vis_x+64, vis_y+64], outline=(150, 150, 150))
                    draw2.text((vis_x, vis_y + 67), f"{x},{y}", fill=(200, 200, 200), font=None)
                    
                    vis_index2 += 1
    
    vis.save("pipes_before_grass.png")
    vis2.save("gap_between_roads_grass.png")
    
    print(f"\nFound {len(pipe_tiles)} pipe tiles")
    print("Created pipes_before_grass.png and gap_between_roads_grass.png")
    
    return pipe_tiles

def analyze_tile(tile):
    """Analyze what type of tile this is"""
    pixels = list(tile.getdata())
    
    # Count different color types
    bg_count = 0
    grey_count = 0
    yellow_green_count = 0
    pink_count = 0
    dark_count = 0
    
    for pixel in pixels:
        if len(pixel) >= 3:
            r, g, b = pixel[:3]
            
            # Background color
            if abs(r - 149) < 10 and abs(g - 177) < 10 and abs(b - 200) < 10:
                bg_count += 1
            # Grey
            elif abs(r - g) < 15 and abs(g - b) < 15 and 50 < r < 150:
                grey_count += 1
            # Yellow/green
            elif (g > r and g > 140) or (r > 170 and g > 140 and b < 100):
                yellow_green_count += 1
            # Pink/magenta (might be transparency placeholder)
            elif r > 200 and b > 200 and g < 150:
                pink_count += 1
            # Dark/black
            elif r < 40 and g < 40 and b < 40:
                dark_count += 1
    
    total = len(pixels)
    
    # Determine tile type
    if bg_count > total * 0.9:
        return "BACKGROUND"
    elif grey_count > 50:
        if yellow_green_count > 10:
            return "PIPE WITH EDGE"
        elif pink_count > 20:
            return "PIPE (pink areas)"
        else:
            return "PIPE GREY"
    elif dark_count > 100:
        return "DARK TILE"
    else:
        return "UNKNOWN"

if __name__ == "__main__":
    pipe_tiles = find_pipes_before_grass()
    
    if pipe_tiles:
        # Update main mapping
        with open("aw2_mixed_tile_mapping.json", "r") as f:
            main_mapping = json.load(f)
        
        main_mapping["tiles"].update(pipe_tiles)
        
        with open("aw2_mixed_tile_mapping.json", "w") as f:
            json.dump(main_mapping, f, indent=2)
        
        print("\nUpdated main mapping file with pipe tiles")
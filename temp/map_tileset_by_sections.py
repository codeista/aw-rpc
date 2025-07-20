#!/usr/bin/env python3
"""
Map tileset by sections using separators and labels
"""

from PIL import Image, ImageDraw
import json

def map_tileset_sections():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # Start fresh mapping
    mapping = {
        "metadata": {
            "source": tileset_path,
            "description": "AW2 RGB tileset with section labels",
            "sections": {
                "roads": "8x8 tiles",
                "pipes": "8x8 tiles", 
                "terrain": "8x8 tiles",
                "water": "8x8 tiles with 4 frames",
                "reefs": "8x8 tiles",
                "buildings": "8x16 tiles with army variants",
                "rivers": "16x16 tiles with multiple frames"
            }
        },
        "tiles": {}
    }
    
    # We know these are correct
    known_tiles = {
        "PLAIN": {"x": 238, "y": 18, "width": 16, "height": 16},
        "WOOD": {"x": 238, "y": 35, "width": 16, "height": 16},
        "MOUNTAIN": {"x": 255, "y": 18, "width": 16, "height": 16}
    }
    
    # Background separator color
    separator_color = (149, 177, 200)
    
    def is_separator(pixel):
        """Check if pixel is separator color"""
        if len(pixel) >= 3:
            r, g, b = pixel[:3]
            return (abs(r - separator_color[0]) < 15 and 
                    abs(g - separator_color[1]) < 15 and 
                    abs(b - separator_color[2]) < 15)
        return False
    
    # Create visualization
    vis = tileset.crop((0, 0, min(800, tileset.width), min(600, tileset.height)))
    draw = ImageDraw.Draw(vis)
    
    # Scan for the first road tile
    # Roads should be in top-left area, let's scan the first 100x100 pixels
    print("\nScanning for first road tile...")
    
    first_tile_x = None
    first_tile_y = None
    
    # Look for first non-separator pixel that could be a road
    for y in range(0, 50):
        for x in range(0, 50):
            pixel = tileset.getpixel((x, y))
            if not is_separator(pixel) and pixel[3] > 0:  # Not transparent
                # Check if this is start of a tile (has separator to left and top)
                if x == 0 or is_separator(tileset.getpixel((x-1, y))):
                    if y == 0 or is_separator(tileset.getpixel((x, y-1))):
                        first_tile_x = x
                        first_tile_y = y
                        break
        if first_tile_x is not None:
            break
    
    if first_tile_x is not None:
        print(f"Found first tile at ({first_tile_x}, {first_tile_y})")
        
        # Map road tiles (8x8 + 1px separator = 9x9 grid)
        road_tiles = []
        y = first_tile_y
        
        # First row of roads
        for i in range(10):  # Check up to 10 tiles
            x = first_tile_x + (i * 9)
            if x + 8 <= tileset.width:
                # Check if tile exists (not all separator)
                has_content = False
                for py in range(y, y + 8):
                    for px in range(x, x + 8):
                        if px < tileset.width and py < tileset.height:
                            if not is_separator(tileset.getpixel((px, py))):
                                has_content = True
                                break
                    if has_content:
                        break
                
                if has_content:
                    road_tiles.append((x, y))
                    draw.rectangle([x-1, y-1, x+8, y+8], outline=(255, 255, 0), width=1)
        
        print(f"Found {len(road_tiles)} road tiles in first row")
        
        # Map basic road types
        road_names = ["ROAD_HORT", "ROAD_VERT", "ROAD_NE", "ROAD_SE", "ROAD_NW", "ROAD_SW", "ROAD_CROSS"]
        for i, (x, y) in enumerate(road_tiles[:len(road_names)]):
            if i < len(road_names):
                mapping["tiles"][road_names[i]] = {
                    "x": x,
                    "y": y,
                    "width": 8,
                    "height": 8,
                    "description": f"Road tile {i+1}"
                }
    
    # Calculate water position (6.5 tiles down from first road)
    if first_tile_y is not None:
        water_y = first_tile_y + int(6.5 * 9)  # 6.5 tiles with 9px spacing
        print(f"\nWater tiles should start around y={water_y}")
        
        # Look for water tiles
        water_x_start = 0
        for x in range(0, 200):
            if not is_separator(tileset.getpixel((x, water_y))):
                water_x_start = x
                break
        
        if water_x_start is not None:
            # Map water tiles (4 frames)
            for frame in range(4):
                x = water_x_start + (frame * 9)
                mapping["tiles"][f"WATER_F{frame+1}"] = {
                    "x": x,
                    "y": water_y,
                    "width": 8,
                    "height": 8,
                    "description": f"Water animation frame {frame+1}"
                }
                draw.rectangle([x-1, water_y-1, x+8, water_y+8], outline=(0, 255, 255), width=1)
            
            # We'll use frame 1 as the main water tile
            mapping["tiles"]["WATER"] = mapping["tiles"]["WATER_F1"].copy()
            mapping["tiles"]["WATER"]["description"] = "Water tile (using frame 1)"
    
    # Add known correct tiles
    mapping["tiles"].update(known_tiles)
    
    # Mark known tiles on visualization
    for name, tile in known_tiles.items():
        draw.rectangle([tile["x"]-1, tile["y"]-1, tile["x"]+tile["width"], tile["y"]+tile["height"]], 
                      outline=(0, 255, 0), width=2)
        draw.text((tile["x"], tile["y"]-10), name, fill=(0, 255, 0))
    
    # Save visualization
    vis.save("tileset_sections_mapped.png")
    
    # Save mapping
    with open("aw2_sectioned_mapping.json", "w") as f:
        json.dump(mapping, f, indent=2)
    
    print("\nCreated tileset_sections_mapped.png")
    print("- Yellow boxes: Road tiles (8x8)")
    print("- Cyan boxes: Water tiles (8x8)")
    print("- Green boxes: Known correct terrain tiles")
    print(f"\nMapped {len(mapping['tiles'])} tiles total")
    
    # Print mapped tiles
    print("\nMapped tiles:")
    for name, tile in mapping["tiles"].items():
        print(f"  {name}: ({tile['x']}, {tile['y']}) {tile['width']}x{tile['height']}")

if __name__ == "__main__":
    map_tileset_sections()
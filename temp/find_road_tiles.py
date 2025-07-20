#!/usr/bin/env python3
"""
Find road tiles in the tileset
"""

from PIL import Image, ImageDraw
import json

def find_road_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # From the original mapping, roads were around (44, 26)
    # Let's search that area
    print("Searching for road tiles around original coordinates...")
    
    # Create visualization
    vis = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    # Check area around (44, 26)
    search_areas = [
        # Original road area
        {"name": "Original area", "x_start": 0, "y_start": 0, "x_end": 100, "y_end": 100},
        # Also check other areas that might have roads
        {"name": "Building area", "x_start": 0, "y_start": 100, "x_end": 200, "y_end": 200},
    ]
    
    found_roads = []
    vis_index = 0
    
    for area in search_areas:
        print(f"\nSearching {area['name']}...")
        
        # Sample tiles in a grid pattern
        for y in range(area['y_start'], area['y_end'], 17):  # 17 pixel steps
            for x in range(area['x_start'], area['x_end'], 17):
                if x + 16 <= tileset.width and y + 16 <= tileset.height:
                    tile = tileset.crop((x, y, x + 16, y + 16))
                    
                    # Analyze tile
                    pixels = list(tile.getdata())
                    gray_pixels = 0
                    dark_pixels = 0
                    bg_pixels = 0
                    
                    for pixel in pixels:
                        if len(pixel) >= 3:
                            r, g, b = pixel[:3]
                            # Background color
                            if abs(r - 149) < 10 and abs(g - 177) < 10 and abs(b - 200) < 10:
                                bg_pixels += 1
                            # Gray road color (darker gray)
                            elif abs(r - g) < 15 and abs(g - b) < 15 and 50 < r < 120:
                                gray_pixels += 1
                            # Very dark (black road lines)
                            elif r < 40 and g < 40 and b < 40:
                                dark_pixels += 1
                    
                    # Roads have gray pixels and dark outlines
                    if gray_pixels > 30 or (gray_pixels > 20 and dark_pixels > 10):
                        print(f"  Potential road at ({x}, {y}): {gray_pixels} gray, {dark_pixels} dark pixels")
                        
                        # Add to visualization
                        if vis_index < 48:  # Limit to 48 tiles
                            vis_x = 20 + (vis_index % 8) * 95
                            vis_y = 20 + (vis_index // 8) * 95
                            
                            tile_scaled = tile.resize((64, 64), Image.NEAREST)
                            vis.paste(tile_scaled, (vis_x, vis_y))
                            draw.rectangle([vis_x-1, vis_y-1, vis_x+64, vis_y+64], outline=(255, 255, 255))
                            draw.text((vis_x, vis_y + 67), f"({x},{y})", fill=(200, 200, 200))
                            
                            vis_index += 1
                            found_roads.append((x, y))
    
    vis.save("found_road_tiles.png")
    print(f"\nFound {len(found_roads)} potential road tiles")
    print("Created found_road_tiles.png")
    
    # Let's specifically check the coordinates from the original mapping
    print("\nChecking original road coordinates:")
    original_roads = [
        ("ROAD_HORT", 44, 26),
        ("ROAD_VERT", 44, 43),
        ("ROAD_NE", 10, 26),
        ("ROAD_SE", 10, 43),
        ("ROAD_NW", 27, 26),
        ("ROAD_SW", 27, 43)
    ]
    
    for name, x, y in original_roads:
        if x + 16 <= tileset.width and y + 16 <= tileset.height:
            tile = tileset.crop((x, y, x + 16, y + 16))
            tile.save(f"check_{name.lower()}_at_{x}_{y}.png")
            print(f"  Saved {name} from ({x}, {y})")

if __name__ == "__main__":
    find_road_tiles()
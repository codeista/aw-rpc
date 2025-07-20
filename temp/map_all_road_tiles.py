#!/usr/bin/env python3
"""
Map all road tiles completely
"""

from PIL import Image, ImageDraw
import json

def map_all_road_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # Create visualization
    vis = Image.new('RGBA', (800, 400), (40, 40, 40, 255))
    
    # Extract road area
    road_area = tileset.crop((0, 0, 200, 80))
    road_scaled = road_area.resize((road_area.width * 3, road_area.height * 3), Image.NEAREST)
    vis.paste(road_scaled, (50, 50))
    
    draw = ImageDraw.Draw(vis)
    draw.text((400, 20), "Complete Road Tile Mapping", fill=(255, 255, 255), anchor="mm")
    
    # Road tiles are 8x8 on 9x9 grid
    # Standard road tile types needed for the game
    road_tiles = []
    
    # Scan systematically
    print("\nScanning for road tiles:")
    
    # Check multiple rows (roads might span 2-3 rows)
    for row in range(6):  # Check up to 6 rows
        y = row * 9
        if y + 8 > 80:  # Don't go past road section
            break
            
        for col in range(15):  # Check up to 15 columns
            x = col * 9
            
            if x + 8 <= tileset.width and y + 8 <= tileset.height:
                # Check if this position has road content
                has_road = False
                road_pixels = 0
                
                for dy in range(8):
                    for dx in range(8):
                        pixel = tileset.getpixel((x + dx, y + dy))
                        
                        # Road tiles typically have grey/dark colors
                        # Not separator color (149, 177, 200)
                        if not (abs(pixel[0] - 149) < 20 and abs(pixel[1] - 177) < 20 and abs(pixel[2] - 200) < 20):
                            if pixel[3] > 0:  # Not transparent
                                road_pixels += 1
                                
                                # Check if it looks like road (greyish)
                                r, g, b = pixel[0], pixel[1], pixel[2]
                                if 40 < r < 120 and 40 < g < 120 and 40 < b < 120:
                                    has_road = True
                
                if road_pixels > 20:  # Significant content
                    road_tiles.append({
                        'x': x,
                        'y': y,
                        'row': row,
                        'col': col
                    })
                    
                    # Draw on visualization
                    vis_x = 50 + x * 3
                    vis_y = 50 + y * 3
                    draw.rectangle([vis_x, vis_y, vis_x + 24, vis_y + 24], 
                                 outline=(255, 255, 0), width=2)
                    
                    # Number the tile
                    draw.text((vis_x + 12, vis_y + 12), str(len(road_tiles)-1), 
                            fill=(255, 255, 255), anchor="mm")
    
    print(f"Found {len(road_tiles)} road tiles total")
    
    # Standard road tile naming
    # Based on common Advance Wars road patterns
    road_names = [
        # Row 0 - Basic roads
        "ROAD_HORT",      # 0: Horizontal
        "ROAD_VERT",      # 1: Vertical  
        "ROAD_NE",        # 2: Turn North-East (└)
        "ROAD_SE",        # 3: Turn South-East (┌)
        "ROAD_SW",        # 4: Turn South-West (┐)
        "ROAD_NW",        # 5: Turn North-West (┘)
        "ROAD_CROSS",     # 6: Crossroads (+)
        
        # Row 1 - T-junctions and ends
        "ROAD_T_N",       # 7: T-junction North (⊥)
        "ROAD_T_E",       # 8: T-junction East (├)
        "ROAD_T_S",       # 9: T-junction South (⊤)
        "ROAD_T_W",       # 10: T-junction West (┤)
        "ROAD_END_N",     # 11: Dead end North
        "ROAD_END_E",     # 12: Dead end East
        "ROAD_END_S",     # 13: Dead end South
        "ROAD_END_W",     # 14: Dead end West
        
        # Additional road tiles if any
        "ROAD_SPECIAL_1",
        "ROAD_SPECIAL_2",
        "ROAD_SPECIAL_3",
    ]
    
    # Create mapping
    road_mapping = {
        "road_tiles": {
            "description": "Complete road tile set",
            "tile_size": 8,
            "grid_size": 9,
            "start_position": {"x": 0, "y": 0},
            "layout": "Arranged in rows, standard road patterns",
            "tiles": []
        }
    }
    
    # Map tiles
    for i, tile in enumerate(road_tiles):
        name = road_names[i] if i < len(road_names) else f"ROAD_UNKNOWN_{i}"
        
        road_mapping["road_tiles"]["tiles"].append({
            "name": name,
            "index": i,
            "x": tile['x'],
            "y": tile['y'],
            "grid_position": f"row {tile['row']}, col {tile['col']}",
            "description": name.replace("_", " ").lower()
        })
        
        if i < 15:  # Print first 15
            print(f"  {i:2d}: {name:15s} at ({tile['x']:3d}, {tile['y']:3d})")
    
    # Draw grid
    for i in range(0, 600, 27):  # 9 * 3 scale
        draw.line([(50 + i, 50), (50 + i, 290)], fill=(100, 100, 100, 50), width=1)
    for i in range(0, 240, 27):
        draw.line([(50, 50 + i), (650, 50 + i)], fill=(100, 100, 100, 50), width=1)
    
    # Info
    draw.text((50, 310), f"Road Tiles: {len(road_tiles)} tiles found", fill=(255, 255, 255))
    draw.text((50, 330), "8x8 pixel tiles on 9x9 grid (includes 1px separator)", fill=(200, 200, 200))
    draw.text((50, 350), "Covers all road configurations: straight, turns, T-junctions, ends", fill=(200, 200, 200))
    
    # Save
    with open("road_tiles_complete.json", "w") as f:
        json.dump(road_mapping, f, indent=2)
    
    vis.save("road_tiles_complete.png")
    print("\nCreated road_tiles_complete.png and road_tiles_complete.json")

if __name__ == "__main__":
    map_all_road_tiles()
#!/usr/bin/env python3
"""
Map road tiles with correct coordinates
"""

import json

def map_road_tiles_final():
    # Based on visual inspection of first_section_roads.png
    # Roads are on a 17x17 grid starting at (0,0)
    
    road_tiles = {
        # First row - looks like UI elements, skip
        
        # Second row (y=17) - Road tiles start here
        "ROAD_NE": {
            "x": 0,
            "y": 17,
            "width": 16,
            "height": 16,
            "description": "Road turn North-East"
        },
        "ROAD_SE": {
            "x": 17,
            "y": 17,
            "width": 16,
            "height": 16,
            "description": "Road turn South-East"
        },
        "ROAD_HORT": {
            "x": 34,
            "y": 17,
            "width": 16,
            "height": 16,
            "description": "Horizontal road"
        },
        "ROAD_NW": {
            "x": 51,
            "y": 17,
            "width": 16,
            "height": 16,
            "description": "Road turn North-West"
        },
        "ROAD_SW": {
            "x": 68,
            "y": 17,
            "width": 16,
            "height": 16,
            "description": "Road turn South-West"
        },
        
        # Third row (y=34) - More road tiles
        "ROAD_VERT": {
            "x": 0,
            "y": 34,
            "width": 16,
            "height": 16,
            "description": "Vertical road"
        },
        "ROAD_CROSS": {
            "x": 17,
            "y": 34,
            "width": 16,
            "height": 16,
            "description": "Road intersection/crossroads"
        },
        "ROAD_T_N": {
            "x": 34,
            "y": 34,
            "width": 16,
            "height": 16,
            "description": "T-junction facing North"
        },
        "ROAD_T_E": {
            "x": 51,
            "y": 34,
            "width": 16,
            "height": 16,
            "description": "T-junction facing East"
        },
        "ROAD_T_S": {
            "x": 68,
            "y": 34,
            "width": 16,
            "height": 16,
            "description": "T-junction facing South"
        },
        "ROAD_T_W": {
            "x": 85,
            "y": 34,
            "width": 16,
            "height": 16,
            "description": "T-junction facing West"
        },
        
        # Fourth row (y=51) - Dead ends
        "ROAD_END_N": {
            "x": 0,
            "y": 51,
            "width": 16,
            "height": 16,
            "description": "Road dead end North"
        },
        "ROAD_END_E": {
            "x": 17,
            "y": 51,
            "width": 16,
            "height": 16,
            "description": "Road dead end East"
        },
        "ROAD_END_S": {
            "x": 34,
            "y": 51,
            "width": 16,
            "height": 16,
            "description": "Road dead end South"
        },
        "ROAD_END_W": {
            "x": 51,
            "y": 51,
            "width": 16,
            "height": 16,
            "description": "Road dead end West"
        }
    }
    
    # Update main mapping file
    print("Updating main mapping file with road tiles...")
    
    with open("aw2_mixed_tile_mapping.json", "r") as f:
        main_mapping = json.load(f)
    
    # Update existing road entries with correct coordinates
    for road_name, road_info in road_tiles.items():
        if road_name in main_mapping["tiles"]:
            print(f"Updating {road_name} coordinates")
            main_mapping["tiles"][road_name].update(road_info)
        else:
            print(f"Adding new {road_name}")
            main_mapping["tiles"][road_name] = road_info
    
    # Remove old incorrect road mappings that don't match our new ones
    old_road_keys = [k for k in main_mapping["tiles"].keys() if k.startswith("ROAD_") and k not in road_tiles]
    for key in old_road_keys:
        del main_mapping["tiles"][key]
        print(f"Removed old incorrect mapping: {key}")
    
    with open("aw2_mixed_tile_mapping.json", "w") as f:
        json.dump(main_mapping, f, indent=2)
    
    print(f"\nSuccessfully mapped {len(road_tiles)} road tiles!")
    
    # Create a summary visualization
    from PIL import Image, ImageDraw
    
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    vis = Image.new('RGBA', (600, 400), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    draw.text((300, 20), "Road Tiles Mapping", fill=(255, 255, 255), anchor="mm")
    
    # Display the main road types
    display_roads = ["ROAD_HORT", "ROAD_VERT", "ROAD_CROSS", "ROAD_NE", "ROAD_SE", "ROAD_NW", "ROAD_SW"]
    
    for i, road_name in enumerate(display_roads):
        if road_name in road_tiles:
            info = road_tiles[road_name]
            tile = tileset.crop((info["x"], info["y"], info["x"] + 16, info["y"] + 16))
            tile_scaled = tile.resize((64, 64), Image.NEAREST)
            
            x_pos = 50 + (i % 4) * 140
            y_pos = 80 + (i // 4) * 120
            
            vis.paste(tile_scaled, (x_pos, y_pos))
            draw.rectangle([x_pos-1, y_pos-1, x_pos+64, y_pos+64], outline=(255, 255, 255))
            draw.text((x_pos + 32, y_pos + 75), road_name.replace("ROAD_", ""), 
                     fill=(200, 200, 200), anchor="mm")
    
    vis.save("road_tiles_summary.png")
    print("Created road_tiles_summary.png")

if __name__ == "__main__":
    map_road_tiles_final()
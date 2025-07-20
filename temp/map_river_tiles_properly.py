#!/usr/bin/env python3
"""
Map river tiles properly by visual inspection
"""

from PIL import Image, ImageDraw
import json

def map_river_tiles_properly():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Based on the river_tiles_found.png, I can see the river tiles
    # They appear to be in different styles/colors
    # Let me map the main river tile types manually based on visual inspection
    
    river_tiles = {
        # Standard blue rivers (first set)
        "RIVER_HORT": {
            "x": 204,
            "y": 331,
            "width": 16,
            "height": 16,
            "animation_frames": 4,
            "frame_spacing": 17,
            "description": "River horizontal (animated)"
        },
        "RIVER_VERT": {
            "x": 238,
            "y": 195,
            "width": 16,
            "height": 16,
            "animation_frames": 4,
            "frame_spacing": 17,
            "description": "River vertical (animated)"
        },
        "RIVER_NE": {
            "x": 238,
            "y": 297,
            "width": 16,
            "height": 16,
            "animation_frames": 4,
            "frame_spacing": 17,
            "description": "River turn North-East (animated)"
        },
        "RIVER_SE": {
            "x": 51,
            "y": 348,
            "width": 16,
            "height": 16,
            "animation_frames": 4,
            "frame_spacing": 17,
            "description": "River turn South-East (animated)"
        },
        "RIVER_NW": {
            "x": 289,
            "y": 348,
            "width": 16,
            "height": 16,
            "animation_frames": 4,
            "frame_spacing": 17,
            "description": "River turn North-West (animated)"
        },
        "RIVER_SW": {
            "x": 221,
            "y": 195,
            "width": 16,
            "height": 16,
            "animation_frames": 4,
            "frame_spacing": 17,
            "description": "River turn South-West (animated)"
        },
        "RIVER_MOUTH_E": {
            "x": 306,
            "y": 212,
            "width": 16,
            "height": 16,
            "animation_frames": 4,
            "frame_spacing": 17,
            "description": "River mouth facing East (animated)"
        },
        "RIVER_MOUTH_W": {
            "x": 221,
            "y": 331,
            "width": 16,
            "height": 16,
            "animation_frames": 4,
            "frame_spacing": 17,
            "description": "River mouth facing West (animated)"
        },
        
        # Different style rivers (darker/different water)
        "RIVER_ALT_CROSS": {
            "x": 0,
            "y": 195,
            "width": 16,
            "height": 16,
            "animation_frames": 4,
            "frame_spacing": 17,
            "description": "Alternative river crossing (animated)"
        },
        "RIVER_ALT_STYLE": {
            "x": 340,
            "y": 195,
            "width": 16,
            "height": 16,
            "animation_frames": 4,
            "frame_spacing": 17,
            "description": "Alternative river style (animated)"
        }
    }
    
    # Create visualization
    vis = Image.new('RGBA', (800, 500), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    draw.text((400, 20), "River Tiles Mapping", fill=(255, 255, 255), anchor="mm")
    
    # Display the river tiles
    for i, (river_name, river_info) in enumerate(river_tiles.items()):
        if i < 12:
            # Show first frame
            x = river_info["x"]
            y = river_info["y"]
            
            if x + 16 <= tileset.width and y + 16 <= tileset.height:
                tile = tileset.crop((x, y, x + 16, y + 16))
                tile_scaled = tile.resize((64, 64), Image.NEAREST)
                
                vis_x = 50 + (i % 5) * 150
                vis_y = 80 + (i // 5) * 140
                
                vis.paste(tile_scaled, (vis_x, vis_y))
                draw.rectangle([vis_x-1, vis_y-1, vis_x+64, vis_y+64], outline=(255, 255, 255))
                draw.text((vis_x + 32, vis_y + 75), river_name.replace("RIVER_", ""), 
                         fill=(100, 200, 255), anchor="mm")
                draw.text((vis_x + 32, vis_y + 90), f"({x},{y})", 
                         fill=(150, 150, 150), anchor="mm")
                draw.text((vis_x + 32, vis_y + 105), "4 frames", 
                         fill=(100, 100, 100), anchor="mm")
    
    vis.save("river_tiles_mapped_proper.png")
    print("Created river_tiles_mapped_proper.png")
    
    # Update main mapping
    with open("aw2_mixed_tile_mapping.json", "r") as f:
        main_mapping = json.load(f)
    
    # Remove the generic RIVER_CROSS entry
    if "RIVER_CROSS" in main_mapping["tiles"]:
        del main_mapping["tiles"]["RIVER_CROSS"]
    
    # Add specific river tiles
    main_mapping["tiles"].update(river_tiles)
    
    with open("aw2_mixed_tile_mapping.json", "w") as f:
        json.dump(main_mapping, f, indent=2)
    
    print(f"\nSuccessfully mapped {len(river_tiles)} river tile types!")
    
    return river_tiles

if __name__ == "__main__":
    river_tiles = map_river_tiles_properly()
    
    for name, info in river_tiles.items():
        print(f"{name}: ({info['x']}, {info['y']}) - {info['description']}")
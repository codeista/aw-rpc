#!/usr/bin/env python3
"""
Map the pipe tiles correctly - they are around x=170-204
"""

from PIL import Image, ImageDraw
import json

def map_pipe_tiles_correct():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Based on the visualization, pipes are around x=170-204
    # Let me map them systematically
    
    pipe_tiles = {
        # Based on visual inspection of the gap visualization
        # Row at y=17
        "PIPE_HORT": {
            "x": 170,
            "y": 17,
            "width": 16,
            "height": 16,
            "description": "Horizontal pipe"
        },
        "PIPE_VERT": {
            "x": 187,
            "y": 17,
            "width": 16,
            "height": 16,
            "description": "Vertical pipe"
        },
        
        # Row at y=34
        "PIPE_NE": {
            "x": 170,
            "y": 34,
            "width": 16,
            "height": 16,
            "description": "Pipe turn North-East"
        },
        "PIPE_SE": {
            "x": 187,
            "y": 34,
            "width": 16,
            "height": 16,
            "description": "Pipe turn South-East"
        },
        "PIPE_CROSS": {
            "x": 204,
            "y": 34,
            "width": 16,
            "height": 16,
            "description": "Pipe intersection"
        },
        
        # Row at y=51
        "PIPE_NW": {
            "x": 170,
            "y": 51,
            "width": 16,
            "height": 16,
            "description": "Pipe turn North-West"
        },
        "PIPE_SW": {
            "x": 187,
            "y": 51,
            "width": 16,
            "height": 16,
            "description": "Pipe turn South-West"
        },
        "PIPE_SEAM": {
            "x": 204,
            "y": 51,
            "width": 16,
            "height": 16,
            "description": "Pipe seam/joint"
        },
        
        # Row at y=68
        "PIPE_END_N": {
            "x": 187,
            "y": 68,
            "width": 16,
            "height": 16,
            "description": "Pipe end facing North"
        },
        "PIPE_END_S": {
            "x": 204,
            "y": 68,
            "width": 16,
            "height": 16,
            "description": "Pipe end facing South"
        }
    }
    
    # Create visualization
    vis = Image.new('RGBA', (600, 400), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    draw.text((300, 20), "Pipe Tiles Mapping", fill=(255, 255, 255), anchor="mm")
    
    # Display the pipe tiles
    display_pipes = ["PIPE_HORT", "PIPE_VERT", "PIPE_CROSS", "PIPE_NE", "PIPE_SE", "PIPE_NW", "PIPE_SW"]
    
    for i, pipe_name in enumerate(display_pipes):
        if pipe_name in pipe_tiles:
            info = pipe_tiles[pipe_name]
            tile = tileset.crop((info["x"], info["y"], info["x"] + 16, info["y"] + 16))
            
            # Replace pink/magenta with transparency for display
            tile = tile.convert('RGBA')
            pixels = tile.load()
            for y in range(16):
                for x in range(16):
                    r, g, b, a = pixels[x, y]
                    # If pink/magenta, make transparent
                    if r > 200 and b > 200 and g < 150:
                        pixels[x, y] = (r, g, b, 0)
            
            tile_scaled = tile.resize((64, 64), Image.NEAREST)
            
            x_pos = 50 + (i % 4) * 140
            y_pos = 80 + (i // 4) * 120
            
            # Draw background first
            draw.rectangle([x_pos, y_pos, x_pos+64, y_pos+64], fill=(100, 100, 100))
            vis.paste(tile_scaled, (x_pos, y_pos), tile_scaled)
            draw.rectangle([x_pos-1, y_pos-1, x_pos+64, y_pos+64], outline=(255, 255, 255))
            draw.text((x_pos + 32, y_pos + 75), pipe_name.replace("PIPE_", ""), 
                     fill=(200, 200, 200), anchor="mm")
    
    vis.save("pipe_tiles_summary.png")
    print("Created pipe_tiles_summary.png")
    
    # Update main mapping
    with open("aw2_mixed_tile_mapping.json", "r") as f:
        main_mapping = json.load(f)
    
    # Remove any old pipe entries
    old_pipe_keys = [k for k in main_mapping["tiles"].keys() if k.startswith("PIPE_")]
    for key in old_pipe_keys:
        del main_mapping["tiles"][key]
        print(f"Removed old pipe entry: {key}")
    
    # Add new pipe tiles
    main_mapping["tiles"].update(pipe_tiles)
    
    with open("aw2_mixed_tile_mapping.json", "w") as f:
        json.dump(main_mapping, f, indent=2)
    
    print(f"\nSuccessfully mapped {len(pipe_tiles)} pipe tiles!")
    
    return pipe_tiles

if __name__ == "__main__":
    pipe_tiles = map_pipe_tiles_correct()
    
    for name, info in pipe_tiles.items():
        print(f"{name}: ({info['x']}, {info['y']}) - {info['description']}")
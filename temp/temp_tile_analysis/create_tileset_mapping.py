#!/usr/bin/env python3
"""
Create a mapping for the AW2 RGB tileset.
This script helps identify and map tiles to their proper names.
"""

import json
from PIL import Image

def analyze_tileset():
    """Analyze the AW2 tileset and create initial mapping"""
    
    # Load the tileset
    tileset = Image.open('static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png')
    print(f"Tileset size: {tileset.size}")
    
    # Standard tile size in Advance Wars
    TILE_SIZE = 16
    
    # Calculate grid dimensions
    cols = tileset.width // TILE_SIZE
    rows = tileset.height // TILE_SIZE
    print(f"Grid: {cols} columns x {rows} rows = {cols * rows} potential tiles")
    
    # Define tile categories based on visual analysis
    tile_mapping = {
        "metadata": {
            "source": "Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png",
            "tile_size": 16,
            "color_mode": "RGB",
            "total_columns": cols,
            "total_rows": rows
        },
        "tiles": {}
    }
    
    # Based on visual inspection, here's the layout:
    # Top left: Roads
    # Top middle: Pipes
    # Top right: Buildings (Red, Green, Blue, Yellow, Grey)
    # Bottom: Water tiles, bridges, terrain features
    
    # Roads section (left side)
    road_types = {
        "road_horizontal": (0, 2),
        "road_vertical": (1, 2),
        "road_corner_tl": (2, 2),
        "road_corner_tr": (3, 2),
        "road_corner_bl": (2, 3),
        "road_corner_br": (3, 3),
        "road_t_up": (4, 2),
        "road_t_down": (4, 3),
        "road_t_left": (5, 2),
        "road_t_right": (5, 3),
        "road_cross": (6, 2),
    }
    
    # Pipes section (middle area)
    pipe_base_x = 10
    pipe_types = {
        "pipe_horizontal": (pipe_base_x, 0),
        "pipe_vertical": (pipe_base_x + 1, 0),
        "pipe_corner_tl": (pipe_base_x + 2, 0),
        "pipe_corner_tr": (pipe_base_x + 3, 0),
        "pipe_corner_bl": (pipe_base_x + 2, 1),
        "pipe_corner_br": (pipe_base_x + 3, 1),
        "pipe_end_up": (pipe_base_x + 4, 0),
        "pipe_end_down": (pipe_base_x + 4, 1),
        "pipe_end_left": (pipe_base_x + 5, 0),
        "pipe_end_right": (pipe_base_x + 5, 1),
    }
    
    # Buildings section (analyzing the colored buildings on the right)
    # Each army has its own column of buildings
    building_base_x = 30  # Approximate start of buildings
    armies = ['RED', 'GREEN', 'BLUE', 'YELLOW', 'GREY']
    building_types = ['HQ', 'CITY', 'BASE', 'AIRPORT', 'PORT']
    
    # Add tiles to mapping
    for tile_name, (x, y) in road_types.items():
        tile_mapping["tiles"][tile_name] = {
            "x": x * TILE_SIZE,
            "y": y * TILE_SIZE,
            "width": TILE_SIZE,
            "height": TILE_SIZE,
            "category": "roads"
        }
    
    for tile_name, (x, y) in pipe_types.items():
        tile_mapping["tiles"][tile_name] = {
            "x": x * TILE_SIZE,
            "y": y * TILE_SIZE,
            "width": TILE_SIZE,
            "height": TILE_SIZE,
            "category": "pipes"
        }
    
    # Terrain tiles
    terrain_types = {
        "grass": (0, 0),
        "forest": (1, 0),
        "mountain": (2, 0),
        "water": (0, 10),
        "shore_n": (1, 10),
        "shore_s": (2, 10),
        "shore_e": (3, 10),
        "shore_w": (4, 10),
    }
    
    for tile_name, (x, y) in terrain_types.items():
        tile_mapping["tiles"][tile_name] = {
            "x": x * TILE_SIZE,
            "y": y * TILE_SIZE,
            "width": TILE_SIZE,
            "height": TILE_SIZE,
            "category": "terrain"
        }
    
    return tile_mapping

def create_visual_grid():
    """Create a visual grid reference for manual mapping"""
    tileset = Image.open('static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png')
    
    # Create a copy with grid overlay
    grid_img = tileset.copy()
    from PIL import ImageDraw, ImageFont
    
    draw = ImageDraw.Draw(grid_img)
    TILE_SIZE = 16
    
    # Draw grid lines
    for x in range(0, tileset.width, TILE_SIZE):
        draw.line([(x, 0), (x, tileset.height)], fill=(255, 255, 255, 128), width=1)
    
    for y in range(0, tileset.height, TILE_SIZE):
        draw.line([(0, y), (tileset.width, y)], fill=(255, 255, 255, 128), width=1)
    
    # Add coordinate labels
    try:
        # Try to use a small font
        font = ImageFont.load_default()
        for x in range(0, tileset.width // TILE_SIZE):
            for y in range(0, tileset.height // TILE_SIZE):
                # Draw coordinates in top-left of each tile
                text = f"{x},{y}"
                draw.text((x * TILE_SIZE + 2, y * TILE_SIZE + 2), text, 
                         fill=(255, 255, 0), font=font)
    except:
        pass
    
    grid_img.save('static/img/aw2_tileset_grid_reference.png')
    print("Saved grid reference image to: static/img/aw2_tileset_grid_reference.png")

def main():
    print("Analyzing AW2 RGB tileset...")
    
    # Create initial mapping
    mapping = analyze_tileset()
    
    # Save mapping
    output_file = 'static/img/aw2_tileset_mapping.json'
    with open(output_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    print(f"Saved initial mapping to: {output_file}")
    
    # Create visual grid
    create_visual_grid()
    
    # Print summary
    print(f"\nMapping created with {len(mapping['tiles'])} tiles")
    
    # Group by category
    categories = {}
    for tile_name, tile_data in mapping['tiles'].items():
        cat = tile_data['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tile_name)
    
    print("\nTiles by category:")
    for cat, tiles in categories.items():
        print(f"  {cat}: {len(tiles)} tiles")

if __name__ == "__main__":
    main()
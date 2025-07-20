#!/usr/bin/env python3
"""
Create AW2 tileset mapping based on the visible text labels in the image.
"""

import json
from PIL import Image

def create_mapping_from_labels():
    """Create tileset mapping based on the visible labels"""
    
    tileset = Image.open('static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png')
    
    mapping = {
        "metadata": {
            "source": "Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png",
            "base_tile_size": 16,
            "color_mode": "RGB",
            "width": tileset.width,
            "height": tileset.height,
            "description": "Tileset with labeled sections for roads, pipes, buildings, etc."
        },
        "tiles": {}
    }
    
    # Based on visible labels in the image:
    
    # ROAD section (top left, labeled "Road")
    road_x, road_y = 16, 16  # Approximate start position
    road_tiles = [
        ("road_h", 0, 0, 16, 16),        # Horizontal
        ("road_v", 16, 0, 16, 16),       # Vertical
        ("road_ne", 32, 0, 16, 16),      # Corner NE
        ("road_se", 32, 16, 16, 16),     # Corner SE
        ("road_sw", 48, 16, 16, 16),     # Corner SW
        ("road_nw", 48, 0, 16, 16),      # Corner NW
        ("road_cross", 64, 0, 16, 16),   # Cross
        ("road_end_n", 0, 32, 16, 16),   # End pieces
        ("road_end_s", 16, 32, 16, 16),
        ("road_end_e", 32, 32, 16, 16),
        ("road_end_w", 48, 32, 16, 16),
    ]
    
    for name, x, y, w, h in road_tiles:
        mapping["tiles"][name] = {
            "x": road_x + x,
            "y": road_y + y,
            "width": w,
            "height": h,
            "category": "roads"
        }
    
    # PIPE section (labeled "Pipe")
    pipe_x, pipe_y = 164, 16  # Based on label position
    pipe_tiles = [
        ("pipe_h", 0, 0, 16, 16),
        ("pipe_v", 16, 0, 16, 16),
        ("pipe_ne", 32, 0, 16, 16),
        ("pipe_se", 32, 16, 16, 16),
        ("pipe_sw", 48, 16, 16, 16),
        ("pipe_nw", 48, 0, 16, 16),
        ("pipe_cross", 64, 0, 16, 16),
        ("pipe_end_n", 0, 32, 16, 16),
        ("pipe_end_s", 16, 32, 16, 16),
        ("pipe_end_e", 32, 32, 16, 16),
        ("pipe_end_w", 48, 32, 16, 16),
        ("pipe_seam", 64, 32, 16, 16),
    ]
    
    for name, x, y, w, h in pipe_tiles:
        mapping["tiles"][name] = {
            "x": pipe_x + x,
            "y": pipe_y + y,
            "width": w,
            "height": h,
            "category": "pipes"
        }
    
    # Grass/Mountains/Trees & Shadows/Volcano section (labeled at top right)
    terrain_x, terrain_y = 304, 16
    terrain_tiles = [
        ("grass", 0, 0, 16, 16),
        ("mountain", 0, 16, 16, 16),
        ("forest", 0, 32, 16, 16),
        ("volcano", 64, 0, 32, 32),  # Volcano is larger
    ]
    
    for name, x, y, w, h in terrain_tiles:
        mapping["tiles"][name] = {
            "x": terrain_x + x,
            "y": terrain_y + y,
            "width": w,
            "height": h,
            "category": "terrain"
        }
    
    # Buildings sections (labeled "Red", "Blue", "Green+Snow", "Red + Snow", etc.)
    # RED buildings (top row)
    red_x, red_y = 488, 16
    # BLUE buildings
    blue_x, blue_y = 680, 16
    # GREEN buildings
    green_x, green_y = 872, 16
    # YELLOW buildings
    yellow_x, yellow_y = 488, 176
    # BLACK/GREY buildings
    grey_x, grey_y = 680, 176
    
    building_types = [
        ("hq", 0, 0, 32, 32),         # HQ is 2x2
        ("city", 32, 0, 16, 16),      # City is 1x1
        ("base", 48, 0, 16, 16),      # Base/Factory is 1x1
        ("airport", 64, 0, 32, 16),   # Airport is 2x1
        ("port", 96, 0, 32, 16),      # Port is 2x1
        ("com_tower", 0, 32, 32, 32), # Com Tower is 2x2
        ("lab", 32, 32, 32, 32),      # Lab is 2x2
        ("missile_silo", 64, 32, 16, 16), # Missile silo is 1x1
    ]
    
    # Add buildings for each army
    armies = [
        ("red", red_x, red_y),
        ("blue", blue_x, blue_y),
        ("green", green_x, green_y),
        ("yellow", yellow_x, yellow_y),
        ("grey", grey_x, grey_y)
    ]
    
    for army_name, base_x, base_y in armies:
        for building, x, y, w, h in building_types:
            tile_name = f"{building}_{army_name}"
            mapping["tiles"][tile_name] = {
                "x": base_x + x,
                "y": base_y + y,
                "width": w,
                "height": h,
                "category": "buildings",
                "army": army_name.upper()
            }
    
    # Water/Edges/Beaches section (bottom left, labeled)
    water_x, water_y = 16, 128
    water_tiles = [
        ("water", 0, 0, 16, 16),
        ("beach_n", 16, 0, 16, 16),
        ("beach_s", 32, 0, 16, 16),
        ("beach_e", 48, 0, 16, 16),
        ("beach_w", 64, 0, 16, 16),
        ("beach_ne", 80, 0, 16, 16),
        ("beach_se", 80, 16, 16, 16),
        ("beach_sw", 96, 16, 16, 16),
        ("beach_nw", 96, 0, 16, 16),
    ]
    
    for name, x, y, w, h in water_tiles:
        mapping["tiles"][name] = {
            "x": water_x + x,
            "y": water_y + y,
            "width": w,
            "height": h,
            "category": "water"
        }
    
    # Rivers section (labeled)
    river_x, river_y = 304, 128
    river_tiles = [
        ("river_h", 0, 0, 16, 16),
        ("river_v", 16, 0, 16, 16),
        ("river_ne", 32, 0, 16, 16),
        ("river_se", 32, 16, 16, 16),
        ("river_sw", 48, 16, 16, 16),
        ("river_nw", 48, 0, 16, 16),
    ]
    
    for name, x, y, w, h in river_tiles:
        mapping["tiles"][name] = {
            "x": river_x + x,
            "y": river_y + y,
            "width": w,
            "height": h,
            "category": "rivers"
        }
    
    # Fog & Snow section (labeled)
    fog_tiles = [
        ("fog", 488, 280, 16, 16),
        ("snow", 680, 280, 16, 16),
    ]
    
    for name, x, y, w, h in fog_tiles:
        mapping["tiles"][name] = {
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "category": "weather"
        }
    
    # Bridges (labeled "Bridge+Explosive Buildings")
    bridge_x, bridge_y = 488, 336
    bridge_tiles = [
        ("bridge_h", 0, 0, 16, 16),
        ("bridge_v", 16, 0, 16, 16),
    ]
    
    for name, x, y, w, h in bridge_tiles:
        mapping["tiles"][name] = {
            "x": bridge_x + x,
            "y": bridge_y + y,
            "width": w,
            "height": h,
            "category": "bridges"
        }
    
    # Animation sequences (bottom right)
    # These are labeled but are multi-frame animations
    mapping["tiles"]["animation_explosion"] = {
        "x": 816,
        "y": 480,
        "width": 48,
        "height": 48,
        "category": "animations",
        "frames": 8,
        "description": "Large explosion animation sequence"
    }
    
    return mapping

def main():
    print("Creating AW2 tileset mapping from visible labels...")
    
    mapping = create_mapping_from_labels()
    
    # Save mapping
    output_file = 'static/img/aw2_tileset_labeled_mapping.json'
    with open(output_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"Saved mapping to: {output_file}")
    print(f"Total tiles mapped: {len(mapping['tiles'])}")
    
    # Count by category
    categories = {}
    for tile in mapping['tiles'].values():
        cat = tile['category']
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1
    
    print("\nTiles by category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count} tiles")
    
    # Count by size
    sizes = {}
    for tile in mapping['tiles'].values():
        size = f"{tile['width']}x{tile['height']}"
        if size not in sizes:
            sizes[size] = 0
        sizes[size] += 1
    
    print("\nTiles by size:")
    for size, count in sorted(sizes.items()):
        print(f"  {size}: {count} tiles")

if __name__ == "__main__":
    main()
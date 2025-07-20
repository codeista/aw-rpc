#!/usr/bin/env python3
"""
Analyze the AW2 tileset to identify different tile sizes and create proper mapping.
This handles variable-sized tiles, not just 16x16.
"""

import json
from PIL import Image

def analyze_tileset_structure():
    """Analyze the AW2 tileset structure with variable tile sizes"""
    
    tileset = Image.open('static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png')
    print(f"Tileset size: {tileset.size}")
    
    # After visual inspection, here's what I see:
    mapping = {
        "metadata": {
            "source": "Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png",
            "base_tile_size": 16,
            "color_mode": "RGB",
            "width": tileset.width,
            "height": tileset.height
        },
        "tiles": {}
    }
    
    # Roads section (16x16 tiles)
    roads_base = (0, 128)  # Approximate position
    road_tiles = [
        ("road_h", 0, 0, 16, 16),
        ("road_v", 16, 0, 16, 16),
        ("road_ne", 32, 0, 16, 16),
        ("road_se", 32, 16, 16, 16),
        ("road_sw", 48, 16, 16, 16),
        ("road_nw", 48, 0, 16, 16),
        ("road_t_n", 64, 0, 16, 16),
        ("road_t_s", 64, 16, 16, 16),
        ("road_t_e", 80, 0, 16, 16),
        ("road_t_w", 80, 16, 16, 16),
        ("road_cross", 96, 0, 16, 16),
    ]
    
    for name, x, y, w, h in road_tiles:
        mapping["tiles"][name] = {
            "x": roads_base[0] + x,
            "y": roads_base[1] + y,
            "width": w,
            "height": h,
            "category": "roads"
        }
    
    # Buildings section - these are LARGER (32x32 or more)
    # Looking at the sprite sheet, buildings start around x=480
    buildings_x = 480
    
    # Each army column appears to be about 48 pixels wide
    army_positions = {
        "RED": 0,
        "BLUE": 48,
        "GREEN": 96,
        "YELLOW": 144,
        "GREY": 192
    }
    
    # Building types with their sizes
    building_defs = [
        ("hq", 0, 0, 32, 32),      # HQ is 32x32
        ("city", 0, 48, 16, 16),    # City is 16x16
        ("base", 16, 48, 16, 16),   # Base is 16x16
        ("airport", 0, 64, 32, 16), # Airport is 32x16
        ("port", 0, 80, 32, 16),    # Port is 32x16
    ]
    
    # Add buildings for each army
    for army, x_offset in army_positions.items():
        for building, bx, by, bw, bh in building_defs:
            tile_name = f"{building}_{army.lower()}"
            mapping["tiles"][tile_name] = {
                "x": buildings_x + x_offset + bx,
                "y": by,
                "width": bw,
                "height": bh,
                "category": "buildings",
                "army": army
            }
    
    # Terrain tiles (mostly 16x16)
    terrain_tiles = [
        ("plain", 0, 0, 16, 16),
        ("forest", 304, 32, 16, 16),
        ("mountain", 304, 16, 16, 16),
        ("wasteland", 320, 0, 16, 16),
    ]
    
    for name, x, y, w, h in terrain_tiles:
        mapping["tiles"][name] = {
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "category": "terrain"
        }
    
    # Water tiles (16x16)
    water_base = (0, 320)
    water_tiles = [
        ("sea", 0, 0, 16, 16),
        ("reef", 128, 0, 16, 16),
        ("shore_n", 16, 0, 16, 16),
        ("shore_s", 32, 0, 16, 16),
        ("shore_e", 48, 0, 16, 16),
        ("shore_w", 64, 0, 16, 16),
    ]
    
    for name, x, y, w, h in water_tiles:
        mapping["tiles"][name] = {
            "x": water_base[0] + x,
            "y": water_base[1] + y,
            "width": w,
            "height": h,
            "category": "water"
        }
    
    # Animated tiles (various sizes)
    # Some animated sequences like explosions are much larger
    mapping["tiles"]["explosion_large"] = {
        "x": 816,
        "y": 0,
        "width": 48,
        "height": 48,
        "category": "animations",
        "frames": 8
    }
    
    return mapping

def create_visual_reference():
    """Create a visual reference showing different tile sizes"""
    from PIL import Image, ImageDraw
    
    tileset = Image.open('static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png')
    visual = tileset.copy()
    draw = ImageDraw.Draw(visual)
    
    # Load our mapping
    mapping = analyze_tileset_structure()
    
    # Color code by size
    colors = {
        (16, 16): (255, 255, 0, 100),    # Yellow for 16x16
        (32, 32): (255, 0, 0, 100),      # Red for 32x32
        (32, 16): (0, 255, 0, 100),      # Green for 32x16
        (48, 48): (0, 0, 255, 100),      # Blue for large
    }
    
    # Draw rectangles around identified tiles
    for tile_name, tile_data in mapping["tiles"].items():
        x, y = tile_data["x"], tile_data["y"]
        w, h = tile_data["width"], tile_data["height"]
        
        color = colors.get((w, h), (255, 255, 255, 100))
        
        # Draw rectangle
        draw.rectangle([x, y, x + w - 1, y + h - 1], outline=color[:3], width=2)
        
        # Add label if space permits
        if w >= 32:
            try:
                draw.text((x + 2, y + 2), tile_name.split('_')[0][:4], fill=(255, 255, 255))
            except:
                pass
    
    visual.save('static/img/aw2_tileset_analysis.png')
    print("Saved visual analysis to: static/img/aw2_tileset_analysis.png")

def main():
    print("Analyzing AW2 tileset with variable tile sizes...")
    
    mapping = analyze_tileset_structure()
    
    # Save mapping
    with open('static/img/aw2_tileset_variable_mapping.json', 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"\nCreated mapping with {len(mapping['tiles'])} tiles")
    
    # Analyze sizes
    sizes = {}
    for tile in mapping['tiles'].values():
        size = (tile['width'], tile['height'])
        if size not in sizes:
            sizes[size] = 0
        sizes[size] += 1
    
    print("\nTile size distribution:")
    for size, count in sorted(sizes.items()):
        print(f"  {size[0]}x{size[1]}: {count} tiles")
    
    # Create visual reference
    create_visual_reference()

if __name__ == "__main__":
    main()
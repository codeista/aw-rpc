#!/usr/bin/env python3
"""
Finalize water/river mapping with correct identifications
"""

from PIL import Image, ImageDraw
import json

def finalize_water_mapping():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # All boxes with correct identifications
    all_boxes = [
        {
            'name': 'Water/Sea',
            'type': 'water',
            'top_left': (38, 131),
            'bottom_right': (57, 337),
            'description': 'Sea/water tiles with animation frames'
        },
        {
            'name': 'Edge/Beach 1',
            'type': 'edge',
            'top_left': (63, 131),
            'bottom_right': (82, 337),
            'description': 'Water edge/beach variant 1'
        },
        {
            'name': 'Edge/Beach 2',
            'type': 'edge',
            'top_left': (88, 131),
            'bottom_right': (107, 337),
            'description': 'Water edge/beach variant 2'
        },
        {
            'name': 'Edge/Beach 3',
            'type': 'edge',
            'top_left': (113, 131),
            'bottom_right': (132, 337),
            'description': 'Water edge/beach variant 3'
        },
        {
            'name': 'Rivers',
            'type': 'river',
            'top_left': (16, 143),
            'bottom_right': (42, 371),
            'description': 'River tiles - taller box with more variations'
        },
        {
            'name': 'Reef',
            'type': 'reef',
            'top_left': (15, 339),
            'bottom_right': (34, 358),
            'description': 'Reef tiles - small box with 4 reef variants'
        }
    ]
    
    # Create final mapping
    mapping = {
        "water_tileset": {
            "description": "Complete water tileset: water, edges, rivers, and reefs",
            "tile_size": 8,
            "grid_size": 9,
            "border_info": {
                "type": "pink/magenta",
                "width": 2,
                "position": "left side of each box"
            },
            "sections": {
                "water": [],
                "edge": [],
                "river": [],
                "reef": []
            }
        }
    }
    
    # Process each box
    for i, box in enumerate(all_boxes):
        width = box['bottom_right'][0] - box['top_left'][0]
        height = box['bottom_right'][1] - box['top_left'][1]
        
        # Tiles start at +2 from box edge (after pink border)
        tile_x = box['top_left'][0] + 2
        tile_y = box['top_left'][1] + 2
        
        # Calculate tile count
        content_width = width - 2
        content_height = height - 2
        tiles_horizontal = max(1, content_width // 9)
        tiles_vertical = max(1, content_height // 9)
        
        # Animation frames (for tall boxes)
        if height > 100:
            # Each frame is roughly 52 pixels tall (including separators)
            animation_frames = 4  # Standard for water tiles
        else:
            animation_frames = 1
        
        box_data = {
            "box_index": i + 1,
            "name": box['name'],
            "top_left": box['top_left'],
            "bottom_right": box['bottom_right'],
            "box_width": width,
            "box_height": height,
            "tile_start": {"x": tile_x, "y": tile_y},
            "tiles_per_row": tiles_horizontal,
            "tile_rows": tiles_vertical,
            "animation_frames": animation_frames,
            "description": box['description']
        }
        
        # Add to appropriate section
        mapping["water_tileset"]["sections"][box['type']].append(box_data)
        
        print(f"\n{box['name']}:")
        print(f"  Position: {box['top_left']} to {box['bottom_right']}")
        print(f"  Box size: {width}x{height}")
        print(f"  Tiles: {tiles_horizontal}x{tiles_vertical}")
        print(f"  Animation frames: {animation_frames}")
    
    # Save final mapping
    with open("water_tileset_final.json", "w") as f:
        json.dump(mapping, f, indent=2)
    
    # Create visual summary
    vis = Image.new('RGBA', (1000, 800), (40, 40, 40, 255))
    
    # Extract tileset area
    area = tileset.crop((0, 120, 400, 380))
    area_scaled = area.resize((area.width * 2, area.height * 2), Image.NEAREST)
    vis.paste(area_scaled, (50, 50))
    
    draw = ImageDraw.Draw(vis)
    draw.text((500, 20), "Final Water Tileset Mapping", fill=(255, 255, 255), anchor="mm")
    
    # Color code by type
    type_colors = {
        'water': (0, 150, 255),    # Blue
        'edge': (255, 200, 100),   # Sandy
        'river': (0, 200, 200),    # Cyan
        'reef': (150, 100, 200)    # Purple
    }
    
    # Draw boxes with color coding
    vis_scale = 2
    vis_offset_x = 50
    vis_offset_y = 50
    
    for box in all_boxes:
        tl = box['top_left']
        br = box['bottom_right']
        
        vis_tl = ((tl[0] - 0) * vis_scale + vis_offset_x,
                  (tl[1] - 120) * vis_scale + vis_offset_y)
        vis_br = ((br[0] - 0) * vis_scale + vis_offset_x,
                  (br[1] - 120) * vis_scale + vis_offset_y)
        
        color = type_colors[box['type']]
        draw.rectangle([vis_tl, vis_br], outline=color, width=3)
        draw.text((vis_tl[0], vis_tl[1] - 15), box['name'], fill=color, anchor="lb")
    
    # Legend
    draw.text((50, 600), "Water Tileset Structure:", fill=(255, 255, 255))
    draw.text((50, 620), "• Blue boxes: Water/Sea tiles (4 animation frames)", fill=(0, 150, 255))
    draw.text((50, 640), "• Sandy boxes: Edge/Beach variants (4 animation frames)", fill=(255, 200, 100))
    draw.text((50, 660), "• Cyan box: River tiles (many variations)", fill=(0, 200, 200))
    draw.text((50, 680), "• Purple box: Reef tiles (4 variants)", fill=(150, 100, 200))
    draw.text((50, 710), "All tiles are 8x8 pixels, arranged on 9x9 grid", fill=(200, 200, 200))
    draw.text((50, 730), "Pink border (2px) on left side should be excluded when rendering", fill=(255, 0, 255))
    
    vis.save("water_tileset_final.png")
    
    print("\n\nSummary:")
    print(f"- Water/Edge boxes: 4 boxes with animation frames")
    print(f"- River box: 1 tall box with many river tile variations")
    print(f"- Reef box: 1 small box with 4 reef variants")
    print("\nCreated water_tileset_final.png and water_tileset_final.json")

if __name__ == "__main__":
    finalize_water_mapping()
#!/usr/bin/env python3
"""
Correct the pink border understanding - only first column of each type
"""

from PIL import Image, ImageDraw
import json

def correct_pink_border():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print("Correcting pink border understanding...")
    print("Pink border is only on the FIRST COLUMN of each tile type section\n")
    
    # Box definitions with corrected understanding
    all_boxes = [
        {
            'name': 'Water/Sea',
            'type': 'water',
            'top_left': (38, 131),
            'bottom_right': (57, 337),
            'pink_border_columns': 1,  # Only first column
            'tile_columns': 2  # Remaining columns are tiles
        },
        {
            'name': 'Edge/Beach 1',
            'type': 'edge',
            'top_left': (63, 131),
            'bottom_right': (82, 337),
            'pink_border_columns': 1,
            'tile_columns': 2
        },
        {
            'name': 'Edge/Beach 2',
            'type': 'edge',
            'top_left': (88, 131),
            'bottom_right': (107, 337),
            'pink_border_columns': 1,
            'tile_columns': 2
        },
        {
            'name': 'Edge/Beach 3',
            'type': 'edge',
            'top_left': (113, 131),
            'bottom_right': (132, 337),
            'pink_border_columns': 1,
            'tile_columns': 2
        },
        {
            'name': 'Rivers',
            'type': 'river',
            'top_left': (16, 143),
            'bottom_right': (42, 371),
            'pink_border_columns': 1,
            'tile_columns': 3  # Wider box
        },
        {
            'name': 'Reef',
            'type': 'reef',
            'top_left': (15, 339),
            'bottom_right': (34, 358),
            'pink_border_columns': 1,
            'tile_columns': 2
        }
    ]
    
    # Create corrected mapping
    mapping = {
        "water_tileset": {
            "description": "Water tileset with pink border only on first column of each type",
            "tile_size": 8,
            "grid_size": 9,
            "pink_border_info": {
                "description": "Pink/magenta border appears only on the first column of each tile type section",
                "width": 1,  # Just 1 pixel wide
                "purpose": "Visual separator between tile type sections"
            },
            "sections": {}
        }
    }
    
    # Process each box with corrected understanding
    for box in all_boxes:
        width = box['bottom_right'][0] - box['top_left'][0]
        height = box['bottom_right'][1] - box['top_left'][1]
        
        # First column is pink border
        # Tiles start at x+1 (after pink column)
        tile_start_x = box['top_left'][0] + 1
        tile_start_y = box['top_left'][1]
        
        # Available width for tiles
        tile_area_width = width - 1  # Subtract pink column
        
        # Calculate actual tiles
        tiles_horizontal = tile_area_width // 9  # 8px tile + 1px separator
        tiles_vertical = height // 9
        
        print(f"{box['name']}:")
        print(f"  Box position: {box['top_left']} to {box['bottom_right']}")
        print(f"  Box size: {width}x{height}")
        print(f"  Pink border: First column only (x={box['top_left'][0]})")
        print(f"  Tiles start at: ({tile_start_x}, {tile_start_y})")
        print(f"  Tile arrangement: {tiles_horizontal}x{tiles_vertical}")
        
        # For tall boxes, calculate animation frames
        if tiles_vertical > 10:
            # Assuming 4 animation frames for water tiles
            frames = 4
            tiles_per_frame = tiles_vertical // frames
            print(f"  Animation: {frames} frames, ~{tiles_per_frame} tiles per frame")
        else:
            frames = 1
            tiles_per_frame = tiles_vertical
        
        print()
        
        # Add to mapping
        if box['type'] not in mapping["water_tileset"]["sections"]:
            mapping["water_tileset"]["sections"][box['type']] = []
        
        mapping["water_tileset"]["sections"][box['type']].append({
            "name": box['name'],
            "box_bounds": {
                "top_left": box['top_left'],
                "bottom_right": box['bottom_right']
            },
            "pink_border_x": box['top_left'][0],
            "tiles_start": {"x": tile_start_x, "y": tile_start_y},
            "tile_grid": f"{tiles_horizontal}x{tiles_vertical}",
            "animation_frames": frames,
            "tiles_per_frame": tiles_per_frame
        })
    
    # Create visualization
    vis = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    
    # Show a sample box structure
    sample_x = 100
    sample_y = 100
    scale = 10
    
    draw = ImageDraw.Draw(vis)
    draw.text((400, 50), "Pink Border Structure (10x scale)", fill=(255, 255, 255), anchor="mm")
    
    # Draw sample box
    # Pink column (1px)
    draw.rectangle([sample_x, sample_y, sample_x + scale, sample_y + 8*scale], 
                  fill=(255, 0, 255))
    draw.text((sample_x + scale//2, sample_y - 20), "Pink", fill=(255, 0, 255), anchor="mm")
    
    # First tile (8px)
    draw.rectangle([sample_x + scale, sample_y, sample_x + 9*scale, sample_y + 8*scale], 
                  fill=(100, 150, 200))
    draw.text((sample_x + 5*scale, sample_y + 4*scale), "Tile 1", fill=(255, 255, 255), anchor="mm")
    
    # Separator (1px)
    draw.rectangle([sample_x + 9*scale, sample_y, sample_x + 10*scale, sample_y + 8*scale], 
                  fill=(149, 177, 200))
    
    # Second tile (8px)
    draw.rectangle([sample_x + 10*scale, sample_y, sample_x + 18*scale, sample_y + 8*scale], 
                  fill=(100, 150, 200))
    draw.text((sample_x + 14*scale, sample_y + 4*scale), "Tile 2", fill=(255, 255, 255), anchor="mm")
    
    # Labels
    draw.text((sample_x, sample_y + 10*scale), "1px", fill=(255, 0, 255))
    draw.text((sample_x + 5*scale, sample_y + 10*scale), "8px", fill=(255, 255, 255))
    draw.text((sample_x + 9.5*scale, sample_y + 10*scale), "1", fill=(200, 200, 200))
    draw.text((sample_x + 14*scale, sample_y + 10*scale), "8px", fill=(255, 255, 255))
    
    # Explanation
    draw.text((100, 250), "Each tile type section:", fill=(255, 255, 255))
    draw.text((100, 280), "• First column: Pink/magenta border (1px)", fill=(255, 0, 255))
    draw.text((100, 300), "• Then: Normal tile grid (8px tiles + 1px separators)", fill=(200, 200, 200))
    draw.text((100, 320), "• Pink border only appears once per section", fill=(255, 255, 255))
    
    # Save corrected mapping
    with open("water_tileset_corrected.json", "w") as f:
        json.dump(mapping, f, indent=2)
    
    vis.save("pink_border_structure.png")
    print("Created pink_border_structure.png and water_tileset_corrected.json")

if __name__ == "__main__":
    correct_pink_border()
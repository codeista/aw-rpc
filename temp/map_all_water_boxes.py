#!/usr/bin/env python3
"""
Map all water/edge/beach boxes using the corner coordinates
"""

from PIL import Image, ImageDraw
import json

def map_all_water_boxes():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # Box corners provided by user
    box1 = {
        'top_left': (38, 131),
        'top_right': (57, 131),
        'bottom_left': (38, 337),
        'bottom_right': (57, 337)
    }
    
    bottom_box = {
        'top_left': (15, 339),
        'top_right': (34, 339),
        'bottom_left': (15, 358),
        'bottom_right': (34, 358)
    }
    
    # Calculate dimensions
    box1_width = box1['top_right'][0] - box1['top_left'][0]  # 19
    box1_height = box1['bottom_left'][1] - box1['top_left'][1]  # 206
    
    bottom_width = bottom_box['top_right'][0] - bottom_box['top_left'][0]  # 19
    bottom_height = bottom_box['bottom_left'][1] - bottom_box['top_left'][1]  # 19
    
    print(f"\nBox 1: {box1_width}x{box1_height} at ({box1['top_left'][0]}, {box1['top_left'][1]})")
    print(f"Bottom box: {bottom_width}x{bottom_height} at ({bottom_box['top_left'][0]}, {bottom_box['top_left'][1]})")
    
    # The bottom box is much smaller - likely reef tiles
    # Box 1 is tall - likely has multiple animation frames
    
    # Create visualization
    vis = Image.new('RGBA', (1000, 800), (40, 40, 40, 255))
    
    # Extract area containing all boxes
    area = tileset.crop((0, 120, 400, 380))
    area_scaled = area.resize((area.width * 2, area.height * 2), Image.NEAREST)
    vis.paste(area_scaled, (50, 50))
    
    draw = ImageDraw.Draw(vis)
    draw.text((500, 20), "All Water/Edge/Beach/Reef Boxes", fill=(255, 255, 255), anchor="mm")
    
    # Draw box outlines
    vis_scale = 2
    vis_offset_x = 50
    vis_offset_y = 50
    
    # Draw box 1
    box1_vis_tl = ((box1['top_left'][0] - 0) * vis_scale + vis_offset_x,
                   (box1['top_left'][1] - 120) * vis_scale + vis_offset_y)
    box1_vis_br = ((box1['bottom_right'][0] - 0) * vis_scale + vis_offset_x,
                   (box1['bottom_right'][1] - 120) * vis_scale + vis_offset_y)
    
    draw.rectangle([box1_vis_tl, box1_vis_br], outline=(255, 0, 0), width=2)
    draw.text(box1_vis_tl, "Box 1", fill=(255, 0, 0), anchor="lb")
    
    # Draw bottom box
    bottom_vis_tl = ((bottom_box['top_left'][0] - 0) * vis_scale + vis_offset_x,
                     (bottom_box['top_left'][1] - 120) * vis_scale + vis_offset_y)
    bottom_vis_br = ((bottom_box['bottom_right'][0] - 0) * vis_scale + vis_offset_x,
                     (bottom_box['bottom_right'][1] - 120) * vis_scale + vis_offset_y)
    
    draw.rectangle([bottom_vis_tl, bottom_vis_br], outline=(0, 255, 255), width=2)
    draw.text(bottom_vis_tl, "Reef", fill=(0, 255, 255), anchor="lb")
    
    # Find the other boxes
    # They should be between box1 and bottom_box in the x direction
    # And similar height to box1
    
    boxes = []
    
    # Box 1
    boxes.append({
        'name': 'Water/Sea',
        'corners': box1,
        'width': box1_width,
        'height': box1_height
    })
    
    # Look for boxes between x=57 and x=110 (approximate)
    # Assuming similar spacing
    box_spacing = 25  # Approximate
    
    for i in range(1, 5):  # Boxes 2-5
        x = box1['top_left'][0] + i * box_spacing
        
        if x < 110:  # Don't go too far
            # Check if there's content here
            has_content = False
            for dy in range(10):
                for dx in range(10):
                    if x + dx < tileset.width and box1['top_left'][1] + dy < tileset.height:
                        p = tileset.getpixel((x + dx, box1['top_left'][1] + dy))
                        # Not background color
                        if not (p[0] == 149 and p[1] == 177 and p[2] == 200):
                            has_content = True
                            break
            
            if has_content:
                box = {
                    'name': f'Edge/Beach {i}',
                    'corners': {
                        'top_left': (x, box1['top_left'][1]),
                        'top_right': (x + box1_width, box1['top_left'][1]),
                        'bottom_left': (x, box1['bottom_left'][1]),
                        'bottom_right': (x + box1_width, box1['bottom_left'][1])
                    },
                    'width': box1_width,
                    'height': box1_height
                }
                boxes.append(box)
                
                # Draw this box
                box_vis_tl = ((x - 0) * vis_scale + vis_offset_x,
                             (box1['top_left'][1] - 120) * vis_scale + vis_offset_y)
                box_vis_br = ((x + box1_width - 0) * vis_scale + vis_offset_x,
                             (box1['bottom_left'][1] - 120) * vis_scale + vis_offset_y)
                
                draw.rectangle([box_vis_tl, box_vis_br], outline=(255, 255, 0), width=2)
                draw.text(box_vis_tl, f"Box {i+1}", fill=(255, 255, 0), anchor="lb")
    
    # Bottom box (reef)
    boxes.append({
        'name': 'Reef tiles',
        'corners': bottom_box,
        'width': bottom_width,
        'height': bottom_height
    })
    
    print(f"\nTotal boxes found: {len(boxes)}")
    
    # Analyze box contents
    mapping = {
        "water_tileset": {
            "description": "Water/Edge/Beach/Reef tiles in box format",
            "boxes": []
        }
    }
    
    for box_idx, box in enumerate(boxes):
        print(f"\nAnalyzing {box['name']}:")
        
        # Calculate tile positions
        # Pink border is 2px, tiles start at +2
        tile_x = box['corners']['top_left'][0] + 2
        tile_y = box['corners']['top_left'][1] + 2
        
        # Calculate how many tiles fit
        content_width = box['width'] - 2  # Remove borders
        content_height = box['height'] - 2
        
        tiles_horizontal = content_width // 9 if content_width >= 8 else 1
        tiles_vertical = content_height // 9 if content_height >= 8 else 1
        
        print(f"  Position: ({box['corners']['top_left'][0]}, {box['corners']['top_left'][1]})")
        print(f"  Size: {box['width']}x{box['height']}")
        print(f"  Tiles: {tiles_horizontal}x{tiles_vertical}")
        
        # For tall boxes, might have animation frames
        if box['height'] > 100:
            frames = box['height'] // 52  # Approximate frame height
            print(f"  Animation frames: ~{frames}")
        
        mapping["water_tileset"]["boxes"].append({
            "name": box['name'],
            "top_left": box['corners']['top_left'],
            "width": box['width'],
            "height": box['height'],
            "tile_start": {"x": tile_x, "y": tile_y},
            "tiles_horizontal": tiles_horizontal,
            "tiles_vertical": tiles_vertical,
            "tile_size": 8,
            "grid_size": 9
        })
    
    # Save mapping
    with open("water_boxes_complete_mapping.json", "w") as f:
        json.dump(mapping, f, indent=2)
    
    # Add legend
    draw.text((50, 600), "Box Layout:", fill=(255, 255, 255))
    draw.text((50, 620), "- Red: Box 1 (Water/Sea) - Tall box with animation frames", fill=(255, 0, 0))
    draw.text((50, 640), "- Yellow: Boxes 2-5 (Edge/Beach variations)", fill=(255, 255, 0))
    draw.text((50, 660), "- Cyan: Bottom box (Reef tiles) - Small box", fill=(0, 255, 255))
    draw.text((50, 680), "Each box has 2px pink border, tiles are 8x8 on 9x9 grid", fill=(200, 200, 200))
    
    vis.save("water_boxes_complete.png")
    print("\nCreated water_boxes_complete.png and water_boxes_complete_mapping.json")

if __name__ == "__main__":
    map_all_water_boxes()
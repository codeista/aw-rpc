#!/usr/bin/env python3
"""
Map all pink borders and their associated tile sections
"""

from PIL import Image, ImageDraw
import json

def map_all_pink_borders():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # Pink border positions provided by user
    pink_borders = [
        (40, 140, "First water section"),
        (55, 141, "Second section"),
        (33, 139, "Third section"),
        (110, 139, "Fourth section"),
        (80, 138, "Fifth section")
    ]
    
    # Sort by x position for better visualization
    pink_borders.sort(key=lambda b: b[0])
    
    print("\nPink border positions (sorted by x):")
    for x, y, desc in pink_borders:
        print(f"  ({x}, {y}): {desc}")
    
    # Create visualization
    vis = Image.new('RGBA', (1000, 600), (40, 40, 40, 255))
    
    # Extract area that includes all these sections
    min_x = min(b[0] for b in pink_borders) - 5
    min_y = min(b[1] for b in pink_borders) - 5
    max_x = max(b[0] for b in pink_borders) + 100
    max_y = max(b[1] for b in pink_borders) + 50
    
    area = tileset.crop((min_x, min_y, min(max_x, tileset.width), min(max_y, tileset.height)))
    area_scaled = area.resize((area.width * 3, area.height * 3), Image.NEAREST)
    vis.paste(area_scaled, (50, 50))
    
    draw = ImageDraw.Draw(vis)
    draw.text((500, 20), "All Water/Edge/Beach Sections with Pink Borders", 
             fill=(255, 255, 255), anchor="mm")
    
    # Analyze each pink border section
    sections = []
    
    for border_x, border_y, desc in pink_borders:
        print(f"\nAnalyzing section at ({border_x}, {border_y}):")
        
        # Check how far the pink border extends down
        pink_height = 0
        for y in range(border_y, min(border_y + 100, tileset.height)):
            pixel = tileset.getpixel((border_x, y))
            if pixel[0] > 200 and pixel[2] > 200 and pixel[1] < 150:
                pink_height += 1
            else:
                if pink_height > 0:
                    break  # End of pink column
        
        print(f"  Pink border extends {pink_height} pixels down")
        
        # Check what's to the right of the pink border
        # Tiles typically start 2 pixels to the right
        tile_x = border_x + 2
        tile_y = border_y + 2
        
        # Identify tile types in this section
        tiles_in_section = []
        
        for i in range(10):  # Check up to 10 tiles horizontally
            check_x = tile_x + i * 9  # 9px grid
            
            if check_x + 8 <= tileset.width and tile_y + 8 <= tileset.height:
                # Sample tile content
                sample_pixels = []
                for dy in range(8):
                    for dx in range(8):
                        p = tileset.getpixel((check_x + dx, tile_y + dy))
                        if p[3] > 0:
                            sample_pixels.append(p)
                
                if sample_pixels:
                    avg_r = sum(p[0] for p in sample_pixels) / len(sample_pixels)
                    avg_g = sum(p[1] for p in sample_pixels) / len(sample_pixels)
                    avg_b = sum(p[2] for p in sample_pixels) / len(sample_pixels)
                    
                    # Determine type
                    if avg_b > avg_r * 1.3:
                        tile_type = "WATER"
                    elif avg_r > 180 and avg_g > 150:
                        tile_type = "BEACH"
                    elif avg_g > avg_r and avg_g > avg_b:
                        tile_type = "EDGE"
                    else:
                        tile_type = "OTHER"
                    
                    tiles_in_section.append({
                        'index': i,
                        'x': check_x,
                        'y': tile_y,
                        'type': tile_type
                    })
        
        sections.append({
            'border_pos': (border_x, border_y),
            'desc': desc,
            'pink_height': pink_height,
            'tiles': tiles_in_section
        })
        
        print(f"  Found {len(tiles_in_section)} tiles: {[t['type'] for t in tiles_in_section[:5]]}")
        
        # Mark on visualization
        vis_border_x = 50 + (border_x - min_x) * 3
        vis_border_y = 50 + (border_y - min_y) * 3
        
        # Draw pink border line
        draw.line([(vis_border_x, vis_border_y), 
                  (vis_border_x, vis_border_y + pink_height * 3)], 
                 fill=(255, 0, 255), width=3)
        
        # Label the section
        draw.text((vis_border_x, vis_border_y - 15), 
                 f"{border_x},{border_y}", 
                 fill=(255, 0, 255), anchor="mm")
        
        # Draw tile boxes
        for tile in tiles_in_section[:5]:  # Show first 5 tiles
            tile_vis_x = 50 + (tile['x'] - min_x) * 3
            tile_vis_y = 50 + (tile['y'] - min_y) * 3
            
            # Color based on type
            if tile['type'] == "WATER":
                color = (0, 150, 255)
            elif tile['type'] == "BEACH":
                color = (255, 200, 100)
            elif tile['type'] == "EDGE":
                color = (100, 255, 100)
            else:
                color = (200, 200, 200)
            
            draw.rectangle([tile_vis_x, tile_vis_y, 
                          tile_vis_x + 24, tile_vis_y + 24], 
                         outline=color, width=2)
    
    # Create mapping
    mapping = {
        "water_sections": {
            "description": "Multiple water/edge/beach sections with pink column borders",
            "sections": []
        }
    }
    
    for section in sections:
        mapping["water_sections"]["sections"].append({
            "border_x": section['border_pos'][0],
            "border_y": section['border_pos'][1],
            "description": section['desc'],
            "pink_height": section['pink_height'],
            "tiles_start": {
                "x": section['border_pos'][0] + 2,
                "y": section['border_pos'][1] + 2
            },
            "tile_count": len(section['tiles']),
            "tile_types": [t['type'] for t in section['tiles']]
        })
    
    # Save mapping
    with open("all_water_sections_mapping.json", "w") as f:
        json.dump(mapping, f, indent=2)
    
    # Add legend
    draw.text((50, 450), "Legend:", fill=(255, 255, 255))
    draw.text((50, 470), "Pink lines: Column borders (extend full height)", fill=(255, 0, 255))
    draw.text((50, 490), "Blue boxes: Water tiles", fill=(0, 150, 255))
    draw.text((50, 510), "Orange boxes: Beach tiles", fill=(255, 200, 100))
    draw.text((50, 530), "Green boxes: Edge tiles", fill=(100, 255, 100))
    draw.text((50, 550), "Each section starts 2px right and 2px down from pink border", fill=(200, 200, 200))
    
    vis.save("all_pink_borders_mapped.png")
    
    print(f"\nTotal sections found: {len(sections)}")
    print("Created all_pink_borders_mapped.png and all_water_sections_mapping.json")

if __name__ == "__main__":
    map_all_pink_borders()
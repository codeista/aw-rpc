#!/usr/bin/env python3
"""
Map 8x16 building tiles with army color variants
"""

from PIL import Image, ImageDraw
import json

def map_buildings_8x16():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # Building tiles are 8x16 starting at x=480
    building_start_x = 480
    building_width = 8
    building_height = 16
    
    # Army colors/variants
    armies = [
        {"name": "RED", "row": 0},      # Red Star/Orange Star
        {"name": "BLUE", "row": 1},     # Blue Moon
        {"name": "YELLOW", "row": 2},   # Yellow Comet
        {"name": "GREEN", "row": 3},    # Green Earth
        {"name": "BLACK", "row": 4},    # Black Hole
        {"name": "NEUTRAL", "row": 5},  # White/Neutral
        {"name": "FOG", "row": 6},      # Fog variants
    ]
    
    # Building types (in order they appear)
    building_types = [
        "HQ",       # Headquarters
        "CITY",     # City
        "BASE",     # Factory/Base
        "AIRPORT",  # Airport
        "PORT",     # Seaport
        "TOWER",    # Communication Tower
        "LAB",      # Lab
        "RUINS",    # Ruins/Destroyed
        # More types in second row
        "SILO",     # Missile Silo
        # Add more as we identify them
    ]
    
    # Create visualization
    vis = Image.new('RGBA', (1200, 800), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    # Building mapping
    building_mapping = {
        "building_tiles": {
            "description": "Building tiles - 8x16 pixels with pink background to be made transparent",
            "tile_size": {"width": building_width, "height": building_height},
            "start_x": building_start_x,
            "grid_spacing": building_width,  # No separator between buildings
            "special_notes": "Pink/magenta background (#FF00FF) should be made transparent",
            "armies": armies,
            "tiles": []
        }
    }
    
    # Map buildings
    buildings_mapped = 0
    
    # Each army has 2 rows of buildings
    for army_idx, army in enumerate(armies):
        army_y_start = 54 * army_idx  # Each army section is 54 pixels apart
        
        if army["name"] == "NEUTRAL":
            army_y_start = 280  # Neutral is lower
        elif army["name"] == "FOG":
            army_y_start = 334  # Fog is even lower
        
        # Check two rows per army
        for row in range(2):
            y = army_y_start + row * 17  # 16 pixels + 1 separator
            
            # Check up to 20 buildings per row
            for col in range(20):
                x = building_start_x + col * building_width
                
                if x + building_width > tileset.width or y + building_height > tileset.height:
                    break
                
                # Check if this position has a building
                has_content = False
                pink_pixels = 0
                
                for dy in range(building_height):
                    for dx in range(building_width):
                        pixel = tileset.getpixel((x + dx, y + dy))
                        r, g, b, a = pixel
                        
                        # Check for pink background
                        if r > 240 and b > 240 and g < 100:
                            pink_pixels += 1
                        # Check for building content (non-pink)
                        elif a > 0:
                            has_content = True
                
                if has_content:
                    # Determine building type
                    building_idx = row * 20 + col
                    if building_idx < len(building_types):
                        building_type = building_types[building_idx]
                    else:
                        building_type = f"BUILDING_{building_idx}"
                    
                    tile_data = {
                        "name": f"{building_type}_{army['name']}",
                        "type": building_type,
                        "army": army["name"],
                        "x": x,
                        "y": y,
                        "width": building_width,
                        "height": building_height,
                        "row": row,
                        "col": col,
                        "has_pink_bg": pink_pixels > 0
                    }
                    
                    building_mapping["building_tiles"]["tiles"].append(tile_data)
                    buildings_mapped += 1
                    
                    # Draw on visualization
                    if army_idx < 4:  # Only show first 4 armies to avoid clutter
                        vis_x = 50 + (col * building_width * 3)
                        vis_y = 50 + (army_idx * 120) + (row * 50)
                        
                        # Extract and paste building
                        building_img = tileset.crop((x, y, x + building_width, y + building_height))
                        building_scaled = building_img.resize((building_width * 3, building_height * 3), Image.NEAREST)
                        vis.paste(building_scaled, (vis_x, vis_y))
                        
                        # Draw border
                        color = {
                            "RED": (255, 100, 100),
                            "BLUE": (100, 100, 255),
                            "YELLOW": (255, 255, 100),
                            "GREEN": (100, 255, 100)
                        }.get(army["name"], (200, 200, 200))
                        
                        draw.rectangle([vis_x, vis_y, 
                                       vis_x + building_width * 3, vis_y + building_height * 3], 
                                      outline=color, width=1)
                else:
                    break  # No more buildings in this row
        
        print(f"{army['name']:8s}: Found buildings at y={army_y_start}")
    
    # Labels
    draw.text((500, 20), "Building Tiles (8x16)", fill=(255, 255, 255), anchor="mm")
    
    # Army labels
    for i, army in enumerate(armies[:4]):
        y_pos = 50 + i * 120
        color = {
            "RED": (255, 100, 100),
            "BLUE": (100, 100, 255),
            "YELLOW": (255, 255, 100),
            "GREEN": (100, 255, 100)
        }.get(army["name"], (200, 200, 200))
        draw.text((30, y_pos + 25), army["name"], fill=color, anchor="rm")
    
    # Building type labels
    for i, btype in enumerate(building_types[:8]):
        x_pos = 50 + i * 24
        draw.text((x_pos + 12, 40), btype[0], fill=(200, 200, 200), anchor="mm")
    
    # Summary
    draw.text((50, 550), f"Total buildings mapped: {buildings_mapped}", fill=(255, 255, 255))
    draw.text((50, 570), "Building size: 8x16 pixels", fill=(200, 200, 200))
    draw.text((50, 590), "Pink background (#FF00FF) should be transparent", fill=(255, 0, 255))
    draw.text((50, 610), "Each army has multiple building variants", fill=(200, 200, 200))
    
    # Special buildings info
    draw.text((50, 640), "Special buildings at bottom:", fill=(255, 255, 255))
    draw.text((50, 660), "- Campaign exclusive buildings", fill=(200, 200, 200))
    draw.text((50, 680), "- Snow variants (with '+Snow' suffix)", fill=(200, 200, 200))
    
    # Save
    vis.save("buildings_8x16_mapped.png")
    print(f"\nTotal buildings mapped: {buildings_mapped}")
    print("Created buildings_8x16_mapped.png")
    
    with open("buildings_8x16_mapping.json", "w") as f:
        json.dump(building_mapping, f, indent=2)
    print("Created buildings_8x16_mapping.json")
    
    # Create a summary of unique building types
    unique_types = set()
    for tile in building_mapping["building_tiles"]["tiles"]:
        unique_types.add(tile["type"])
    
    print(f"\nUnique building types found: {len(unique_types)}")
    for btype in sorted(unique_types):
        print(f"  - {btype}")

if __name__ == "__main__":
    map_buildings_8x16()
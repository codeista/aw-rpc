#!/usr/bin/env python3
"""
Find the exact coordinates of 8x16 building tiles
"""

from PIL import Image, ImageDraw
import json

def find_building_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # Look at the building area with pink backgrounds
    # Based on the image, buildings appear to be in the right section
    # Starting around x=480+ with pink backgrounds
    
    # Create visualization
    vis = Image.new('RGBA', (1000, 800), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    # Extract the building area (right side with pink backgrounds)
    area_x = 480
    area_y = 0
    area_width = tileset.width - area_x
    area_height = 400
    
    area = tileset.crop((area_x, area_y, area_x + area_width, area_y + area_height))
    area_scaled = area.resize((area.width * 2, area.height * 2), Image.NEAREST)
    vis.paste(area_scaled, (50, 50))
    
    draw.text((500, 20), "Building Area with Pink Backgrounds", fill=(255, 255, 255), anchor="mm")
    
    # Look for a specific building by checking for pink background
    # and building content
    print("\nSearching for buildings with pink backgrounds...")
    
    buildings_found = []
    
    # Scan in a grid pattern looking for 8x16 areas
    for y in range(0, 400, 16):
        for x in range(480, tileset.width, 8):
            # Check if this could be a building tile
            pink_count = 0
            content_count = 0
            
            # Sample a few pixels
            for dy in [0, 8, 15]:
                for dx in [0, 4, 7]:
                    if x + dx < tileset.width and y + dy < tileset.height:
                        pixel = tileset.getpixel((x + dx, y + dy))
                        r, g, b, a = pixel
                        
                        # Pink/magenta background
                        if r > 240 and b > 240 and g < 100:
                            pink_count += 1
                        # Non-pink content
                        elif a > 0 and not (r > 240 and b > 240 and g < 100):
                            content_count += 1
            
            # If we have both pink background and content, likely a building
            if pink_count > 0 and content_count > 3:
                # Check if this is a full 8x16 tile
                is_building = True
                
                # Verify it's roughly 8x16
                if x + 8 <= tileset.width and y + 16 <= tileset.height:
                    buildings_found.append((x, y))
                    
                    if len(buildings_found) <= 5:
                        print(f"  Building found at ({x}, {y})")
                        
                        # Mark on visualization
                        vis_x = 50 + (x - area_x) * 2
                        vis_y = 50 + y * 2
                        draw.rectangle([vis_x, vis_y, vis_x + 16, vis_y + 32], 
                                     outline=(0, 255, 0), width=2)
    
    print(f"\nTotal potential buildings found: {len(buildings_found)}")
    
    # Check the first building in detail
    if buildings_found:
        x, y = buildings_found[0]
        print(f"\nAnalyzing first building at ({x}, {y}):")
        
        # Count exact dimensions by finding edges
        # Find right edge
        width = 8
        for dx in range(8, 20):
            if x + dx < tileset.width:
                all_pink = True
                for dy in range(16):
                    if y + dy < tileset.height:
                        pixel = tileset.getpixel((x + dx, y + dy))
                        r, g, b, a = pixel
                        if not (r > 240 and b > 240 and g < 100):
                            all_pink = False
                            break
                if all_pink:
                    width = dx
                    break
        
        # Find bottom edge
        height = 16
        for dy in range(16, 32):
            if y + dy < tileset.height:
                all_pink = True
                for dx in range(8):
                    if x + dx < tileset.width:
                        pixel = tileset.getpixel((x + dx, y + dy))
                        r, g, b, a = pixel
                        if not (r > 240 and b > 240 and g < 100):
                            all_pink = False
                            break
                if all_pink:
                    height = dy
                    break
        
        print(f"  Detected size: {width}x{height}")
        
        # Show zoomed in view of first building
        if x + width <= tileset.width and y + height <= tileset.height:
            building = tileset.crop((x, y, x + width, y + height))
            building_scaled = building.resize((width * 8, height * 8), Image.NEAREST)
            vis.paste(building_scaled, (600, 100))
            draw.text((600 + width * 4, 80), f"First Building ({width}x{height})", 
                     fill=(0, 255, 0), anchor="mm")
            draw.rectangle([600, 100, 600 + width * 8, 100 + height * 8], 
                          outline=(0, 255, 0), width=2)
    
    # Look specifically around the coordinates that were given
    check_coords = [
        (481, 54),   # Near the Red section
        (498, 54),   # Next building
        (515, 54),   # Another one
        (481, 330),  # Bottom area
    ]
    
    print("\nChecking specific building locations:")
    for i, (x, y) in enumerate(check_coords):
        if x + 8 <= tileset.width and y + 16 <= tileset.height:
            # Sample the tile
            has_pink = False
            has_content = False
            
            for dy in range(16):
                for dx in range(8):
                    pixel = tileset.getpixel((x + dx, y + dy))
                    r, g, b, a = pixel
                    
                    if r > 240 and b > 240 and g < 100:
                        has_pink = True
                    elif a > 0:
                        has_content = True
            
            if has_pink and has_content:
                print(f"  Building confirmed at ({x}, {y})")
                
                # Mark on visualization
                vis_x = 50 + (x - area_x) * 2
                vis_y = 50 + y * 2
                draw.rectangle([vis_x, vis_y, vis_x + 16, vis_y + 32], 
                             outline=(255, 255, 0), width=2)
                draw.text((vis_x + 8, vis_y - 5), str(i+1), 
                         fill=(255, 255, 0), anchor="mm")
    
    vis.save("find_building_tiles.png")
    print("\nCreated find_building_tiles.png")
    
    # Return the first few building coordinates
    if buildings_found:
        print("\nFirst building tile corners (8x16):")
        x, y = buildings_found[0]
        print(f"Top-left: ({x}, {y})")
        print(f"Top-right: ({x+7}, {y})")
        print(f"Bottom-left: ({x}, {y+15})")
        print(f"Bottom-right: ({x+7}, {y+15})")

if __name__ == "__main__":
    find_building_tiles()
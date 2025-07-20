#!/usr/bin/env python3
"""
Map building tiles (8x16) with army color variants
"""

from PIL import Image, ImageDraw
import json

def map_building_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # First building tile corners provided
    building_tl = (233, 60)
    building_tr = (243, 60)
    building_bl = (233, 117)
    building_br = (243, 117)
    
    # Calculate dimensions
    width = building_tr[0] - building_tl[0]    # 10
    height = building_bl[1] - building_tl[1]    # 57
    
    print(f"\nFirst building tile at ({building_tl[0]}, {building_tl[1]})")
    print(f"Tile size: {width}x{height}")
    
    # This suggests 15x31 tiles, which is unusual
    # Let's check if this is correct or if we need to adjust
    
    # Create visualization
    vis = Image.new('RGBA', (1000, 800), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    # Extract building area
    area_x = building_tl[0] - 20
    area_y = building_tl[1] - 20
    area_width = 400
    area_height = 300
    
    if area_x + area_width > tileset.width:
        area_width = tileset.width - area_x
    if area_y + area_height > tileset.height:
        area_height = tileset.height - area_y
    
    area = tileset.crop((area_x, area_y, area_x + area_width, area_y + area_height))
    area_scaled = area.resize((area.width * 2, area.height * 2), Image.NEAREST)
    vis.paste(area_scaled, (50, 50))
    
    draw.text((500, 20), "Building Tiles Analysis", fill=(255, 255, 255), anchor="mm")
    
    # Mark the specified tile
    tile_vis_x = 50 + (building_tl[0] - area_x) * 2
    tile_vis_y = 50 + (building_tl[1] - area_y) * 2
    
    draw.rectangle([tile_vis_x, tile_vis_y, 
                   tile_vis_x + width * 2, tile_vis_y + height * 2], 
                  outline=(255, 255, 0), width=2)
    
    draw.text((tile_vis_x + width, tile_vis_y - 10), 
             "First Building", fill=(255, 255, 0), anchor="mm")
    
    # Check for pink pixels
    pink_pixels = 0
    building_pixels = 0
    
    for dy in range(height):
        for dx in range(width):
            pixel = tileset.getpixel((building_tl[0] + dx, building_tl[1] + dy))
            r, g, b, a = pixel
            
            # Check for pink/magenta
            if r > 200 and b > 200 and g < 150:
                pink_pixels += 1
            elif a > 0:
                building_pixels += 1
    
    print(f"\nPixel analysis:")
    print(f"  Pink pixels: {pink_pixels}")
    print(f"  Building pixels: {building_pixels}")
    
    # Let's also check if buildings are on a grid
    # Try different grid spacings
    for grid_test in [17, 16, 18, 32, 33]:
        next_x = building_tl[0] + grid_test
        if next_x + width <= tileset.width:
            has_content = False
            for dy in range(5):
                for dx in range(5):
                    if next_x + dx < tileset.width and building_tl[1] + dy < tileset.height:
                        pixel = tileset.getpixel((next_x + dx, building_tl[1] + dy))
                        if pixel[3] > 0 and not (pixel[0] > 200 and pixel[2] > 200 and pixel[1] < 150):
                            has_content = True
                            break
                if has_content:
                    break
            
            if has_content:
                print(f"\nFound content at x+{grid_test}, suggesting grid spacing of {grid_test}")
                
                # Mark this tile too
                next_tile_vis_x = 50 + (next_x - area_x) * 2
                draw.rectangle([next_tile_vis_x, tile_vis_y, 
                               next_tile_vis_x + width * 2, tile_vis_y + height * 2], 
                              outline=(0, 255, 0), width=2)
                break
    
    # Building mapping structure
    building_mapping = {
        "building_tiles": {
            "description": "Building tiles",
            "first_tile_corners": {
                "top_left": building_tl,
                "top_right": building_tr,
                "bottom_left": building_bl,
                "bottom_right": building_br
            },
            "tile_size": {"width": width, "height": height},
            "special_notes": "Pink/magenta background should be transparent",
            "tiles": []
        }
    }
    
    # Common building types we expect
    building_types = [
        "HQ",           # Headquarters
        "CITY",         # City
        "BASE",         # Factory/Base
        "AIRPORT",      # Airport
        "PORT",         # Port/Seaport
        "COM_TOWER",    # Communication Tower
        "MISSILE",      # Missile Silo
        "LAB",          # Lab
        # Properties that might have multiple variants
        "PROPERTY_1",   # Various property types
        "PROPERTY_2",
        # etc.
    ]
    
    print("\nExpected building types:")
    for bt in building_types[:8]:
        print(f"  - {bt}")
    print("  - (and more...)")
    
    print("\nBuildings typically have variants for:")
    print("  - Neutral (grey)")
    print("  - Red Star (player 1)")
    print("  - Blue Moon (player 2)")
    print("  - Green Earth")
    print("  - Yellow Comet")
    print("  - Black Hole")
    
    # Save visualization
    vis.save("building_tiles_analysis.png")
    print("\nCreated building_tiles_analysis.png")
    
    # Save initial mapping
    with open("building_tiles_mapping.json", "w") as f:
        json.dump(building_mapping, f, indent=2)
    
    print("\nThe coordinates suggest tiles are 15x31 pixels.")
    print("This is larger than expected for 8x16 building tiles.")
    print("Please check the visualization to confirm the tile boundaries.")

if __name__ == "__main__":
    map_building_tiles()
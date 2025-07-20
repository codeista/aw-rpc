#!/usr/bin/env python3
"""
Map water/beach/river tiles with animation frames
"""

from PIL import Image, ImageDraw
import json

def map_water_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # First road starts at (0, 17), so directly under would be x=0
    # 6.5 tiles down = 6.5 * 17 = 110.5, so around y=127-128
    water_start_x = 0
    water_start_y = 127  # Approximately 6.5 tiles down from road
    
    print(f"Looking for water tiles starting at ({water_start_x}, {water_start_y})")
    
    # Create visualization
    vis = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    draw.text((400, 20), "Water/Beach/River Tiles (4 frames each)", fill=(255, 255, 255), anchor="mm")
    
    water_types = {}
    vis_index = 0
    
    # Water tiles are typically arranged in rows with 4 animation frames each
    # Let's check several rows
    for row in range(8):  # Check 8 rows
        y = water_start_y + row * 17
        
        # Each water type has 4 frames horizontally
        for water_type_index in range(4):  # Up to 4 different water types per row
            frames = []
            base_x = water_start_x + water_type_index * 68  # 4 frames * 17 pixels
            
            # Collect 4 animation frames
            all_frames_valid = True
            for frame in range(4):
                x = base_x + frame * 17
                
                if x + 16 <= tileset.width and y + 16 <= tileset.height:
                    tile = tileset.crop((x, y, x + 16, y + 16))
                    
                    # Check if it's a water tile (blueish)
                    if is_water_tile(tile):
                        frames.append((x, y))
                    else:
                        all_frames_valid = False
                        break
                else:
                    all_frames_valid = False
                    break
            
            # If we found 4 valid water frames, it's a water animation set
            if all_frames_valid and len(frames) == 4:
                water_name = identify_water_type(tileset, frames[0][0], frames[0][1])
                
                if water_name and vis_index < 12:  # Limit visualization
                    # Show first frame of each water type
                    x, y = frames[0]
                    tile = tileset.crop((x, y, x + 16, y + 16))
                    tile_scaled = tile.resize((64, 64), Image.NEAREST)
                    
                    vis_x = 50 + (vis_index % 6) * 120
                    vis_y = 80 + (vis_index // 6) * 150
                    
                    vis.paste(tile_scaled, (vis_x, vis_y))
                    draw.rectangle([vis_x-1, vis_y-1, vis_x+64, vis_y+64], outline=(255, 255, 255))
                    draw.text((vis_x + 32, vis_y + 75), water_name, fill=(100, 200, 255), anchor="mm")
                    draw.text((vis_x + 32, vis_y + 90), f"({x},{y})", fill=(150, 150, 150), anchor="mm")
                    draw.text((vis_x + 32, vis_y + 105), "4 frames", fill=(100, 100, 100), anchor="mm")
                    
                    # Store water tile info
                    water_types[f"WATER_{water_name.upper()}"] = {
                        "x": frames[0][0],
                        "y": frames[0][1],
                        "width": 16,
                        "height": 16,
                        "animation_frames": 4,
                        "frame_spacing": 17,
                        "description": f"{water_name} water tile (animated)"
                    }
                    
                    print(f"Found {water_name} at ({frames[0][0]}, {frames[0][1]}) with 4 animation frames")
                    vis_index += 1
    
    vis.save("water_tiles_mapped.png")
    print(f"\nFound {len(water_types)} water tile types")
    print("Created water_tiles_mapped.png")
    
    # Also create a detailed view showing animation frames
    if water_types:
        create_animation_preview(tileset, list(water_types.values())[:4])
    
    return water_types

def is_water_tile(tile):
    """Check if a tile is water by looking for blue colors"""
    pixels = list(tile.getdata())
    blue_count = 0
    bg_count = 0
    
    for pixel in pixels:
        if len(pixel) >= 3:
            r, g, b = pixel[:3]
            # Background color
            if abs(r - 149) < 10 and abs(g - 177) < 10 and abs(b - 200) < 10:
                bg_count += 1
            # Blue water colors
            elif b > r and b > g and b > 100:
                blue_count += 1
            # Darker blue/teal
            elif b > 50 and g > 50 and r < 100 and b >= g:
                blue_count += 1
    
    # Water tiles should have significant blue pixels
    return blue_count > 20 and bg_count < len(pixels) * 0.8

def identify_water_type(tileset, x, y):
    """Identify the type of water tile"""
    tile = tileset.crop((x, y, x + 16, y + 16))
    pixels = list(tile.getdata())
    
    # Analyze colors to determine water type
    dark_blue = 0
    light_blue = 0
    sandy = 0
    grey = 0
    
    for pixel in pixels:
        if len(pixel) >= 3:
            r, g, b = pixel[:3]
            
            # Dark blue (deep water)
            if b > 100 and r < 50 and g < 80:
                dark_blue += 1
            # Light blue (shallow water)
            elif b > 150 and r < 100 and g < 130:
                light_blue += 1
            # Sandy/beach colors
            elif r > 180 and g > 160 and b > 100:
                sandy += 1
            # Grey (rocks/reef)
            elif abs(r - g) < 20 and abs(g - b) < 20 and 80 < r < 150:
                grey += 1
    
    # Determine type based on color distribution
    if dark_blue > 100:
        return "SEA"
    elif sandy > 30:
        return "BEACH"
    elif grey > 40:
        return "REEF"
    elif light_blue > 80:
        return "SHOAL"
    elif dark_blue > 50:
        return "RIVER"
    else:
        # Check position for more context
        if y < 150:
            return "COAST"
        else:
            return "SHORE"

def create_animation_preview(tileset, water_types):
    """Create a preview showing animation frames"""
    preview = Image.new('RGBA', (600, 300), (40, 40, 40, 255))
    draw = ImageDraw.Draw(preview)
    
    draw.text((300, 20), "Water Animation Frames Preview", fill=(255, 255, 255), anchor="mm")
    
    for i, water_info in enumerate(water_types):
        if i >= 4:
            break
            
        y_pos = 60 + i * 60
        
        # Show all 4 frames
        for frame in range(4):
            x = water_info["x"] + frame * water_info["frame_spacing"]
            y = water_info["y"]
            
            tile = tileset.crop((x, y, x + 16, y + 16))
            tile_scaled = tile.resize((48, 48), Image.NEAREST)
            
            x_pos = 50 + frame * 60
            preview.paste(tile_scaled, (x_pos, y_pos))
            draw.rectangle([x_pos-1, y_pos-1, x_pos+48, y_pos+48], outline=(100, 100, 100))
            
            if frame == 0:
                draw.text((x_pos - 40, y_pos + 24), water_info["description"].split()[0], 
                         fill=(100, 200, 255), anchor="mm")
        
        # Arrow showing animation
        draw.text((290, y_pos + 24), "→", fill=(255, 255, 255))
    
    preview.save("water_animation_preview.png")
    print("Created water_animation_preview.png")

if __name__ == "__main__":
    water_tiles = map_water_tiles()
    
    if water_tiles:
        # Update main mapping
        with open("aw2_mixed_tile_mapping.json", "r") as f:
            main_mapping = json.load(f)
        
        # Update existing water entries or add new ones
        for water_name, water_info in water_tiles.items():
            # Remove the old single-frame water entries if they exist
            old_name = water_name.replace("WATER_", "")
            if old_name in main_mapping["tiles"]:
                del main_mapping["tiles"][old_name]
                print(f"Removed old entry: {old_name}")
            
            main_mapping["tiles"][water_name] = water_info
        
        with open("aw2_mixed_tile_mapping.json", "w") as f:
            json.dump(main_mapping, f, indent=2)
        
        print("\nUpdated main mapping file with animated water tiles")
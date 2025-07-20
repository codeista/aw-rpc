#!/usr/bin/env python3
"""
Find tiles separated by blue lines in the AW2 tileset
"""

from PIL import Image
import os

def is_blue_line(pixel):
    """Check if a pixel is blue (used as separator)"""
    if len(pixel) >= 3:
        r, g, b = pixel[:3]
        # Blue should have high blue value and low red/green
        return b > 150 and r < 100 and g < 150
    return False

def find_blue_separated_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    
    if not os.path.exists(tileset_path):
        print(f"Error: Tileset not found at {tileset_path}")
        return
    
    tileset = Image.open(tileset_path).convert('RGBA')
    width, height = tileset.size
    print(f"Tileset size: {width}x{height}")
    
    # Find horizontal blue lines
    print("\nFinding horizontal blue lines:")
    h_blue_lines = []
    for y in range(height):
        # Check if entire row is mostly blue
        blue_count = 0
        for x in range(min(width, 200)):  # Check first 200 pixels
            pixel = tileset.getpixel((x, y))
            if is_blue_line(pixel):
                blue_count += 1
        
        if blue_count > 150:  # Most of the row is blue
            h_blue_lines.append(y)
    
    # Group consecutive lines
    h_line_groups = []
    current_group = []
    for y in h_blue_lines:
        if not current_group or y == current_group[-1] + 1:
            current_group.append(y)
        else:
            if current_group:
                h_line_groups.append(current_group)
            current_group = [y]
    if current_group:
        h_line_groups.append(current_group)
    
    print(f"Found {len(h_line_groups)} horizontal blue line groups:")
    for i, group in enumerate(h_line_groups[:10]):  # Show first 10
        print(f"  Line {i+1}: y={group[0]} to {group[-1]} (thickness: {len(group)})")
    
    # Find vertical blue lines
    print("\nFinding vertical blue lines:")
    v_blue_lines = []
    for x in range(min(width, 400)):  # Check first 400 pixels width
        # Check if entire column is mostly blue
        blue_count = 0
        for y in range(min(height, 100)):  # Check first 100 pixels height
            pixel = tileset.getpixel((x, y))
            if is_blue_line(pixel):
                blue_count += 1
        
        if blue_count > 50:  # Most of the column is blue
            v_blue_lines.append(x)
    
    # Group consecutive lines
    v_line_groups = []
    current_group = []
    for x in v_blue_lines:
        if not current_group or x == current_group[-1] + 1:
            current_group.append(x)
        else:
            if current_group:
                v_line_groups.append(current_group)
            current_group = [x]
    if current_group:
        v_line_groups.append(current_group)
    
    print(f"\nFound {len(v_line_groups)} vertical blue line groups:")
    for i, group in enumerate(v_line_groups[:10]):  # Show first 10
        print(f"  Line {i+1}: x={group[0]} to {group[-1]} (thickness: {len(group)})")
    
    # Calculate tile positions based on blue lines
    print("\n\nTile regions (between blue lines):")
    
    # For simplicity, let's look at the area around where user found tiles
    # Based on the blue lines found
    if len(h_line_groups) > 0 and len(v_line_groups) > 0:
        # Get tile regions
        tile_regions = []
        
        # Add region before first lines
        if h_line_groups[0][0] > 0 and v_line_groups[0][0] > 0:
            tile_regions.append({
                'x': 0, 
                'y': 0, 
                'width': v_line_groups[0][0], 
                'height': h_line_groups[0][0]
            })
        
        # Add regions between lines
        for i in range(len(h_line_groups) - 1):
            y_start = h_line_groups[i][-1] + 1
            y_end = h_line_groups[i + 1][0]
            
            for j in range(len(v_line_groups) - 1):
                x_start = v_line_groups[j][-1] + 1
                x_end = v_line_groups[j + 1][0]
                
                if x_end > x_start and y_end > y_start:
                    tile_regions.append({
                        'x': x_start,
                        'y': y_start,
                        'width': x_end - x_start,
                        'height': y_end - y_start
                    })
        
        print(f"Found {len(tile_regions)} tile regions")
        for i, region in enumerate(tile_regions[:20]):  # Show first 20
            print(f"  Region {i+1}: x={region['x']}, y={region['y']}, size={region['width']}x{region['height']}")
            
            # Save sample tiles
            if i < 10 and region['width'] > 0 and region['height'] > 0:
                try:
                    tile = tileset.crop((region['x'], region['y'], 
                                       region['x'] + min(region['width'], 16), 
                                       region['y'] + min(region['height'], 16)))
                    # Scale up small tiles
                    if tile.width < 16:
                        scale = 16 // tile.width
                        tile = tile.resize((tile.width * scale, tile.height * scale), Image.NEAREST)
                    
                    tile.save(f"blue_separated_tile_{i+1}_at_{region['x']}_{region['y']}.png")
                except Exception as e:
                    print(f"    Error saving tile: {e}")
    
    # Also check the specific area around (129, 10) that user mentioned
    print("\n\nAnalyzing area around (129, 10):")
    context_size = 50
    context = tileset.crop((100, 0, 180, 50))
    context.save("blue_lines_context_129_10.png")
    
    # Find tiles in this region
    print("Looking for 8x8 tiles with blue separators in this region...")
    # The pattern seems to be tiles separated by 1-pixel blue lines
    # So tiles would be at positions like: 0, 9, 18, 27, etc. (8 pixel tile + 1 pixel separator)
    
    tiles_found = []
    y = 10  # The y position user mentioned
    for x in range(120, 160, 9):  # 8 pixel tile + 1 pixel separator
        if x + 8 <= width and y + 8 <= height:
            # Check if there's a blue line at x+8
            has_separator = False
            if x + 8 < width:
                pixel = tileset.getpixel((x + 8, y))
                has_separator = is_blue_line(pixel)
            
            tiles_found.append({
                'x': x,
                'y': y,
                'has_separator': has_separator
            })
    
    print(f"\nPotential 8x8 tiles at y=10:")
    for tile in tiles_found:
        print(f"  x={tile['x']}: {'has blue separator' if tile['has_separator'] else 'no separator'}")

if __name__ == "__main__":
    find_blue_separated_tiles()
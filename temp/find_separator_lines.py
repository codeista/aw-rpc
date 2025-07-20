#!/usr/bin/env python3
"""
Find grey separator lines in the tileset to identify tile boundaries
"""

from PIL import Image, ImageDraw
import os

def find_separator_lines():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    
    if not os.path.exists(tileset_path):
        print(f"Error: Tileset not found")
        return
    
    tileset = Image.open(tileset_path).convert('RGBA')
    width, height = tileset.size
    print(f"Tileset size: {width}x{height}")
    
    # Sample background color near the PLAIN tile
    bg_pixel = tileset.getpixel((237, 18))  # Just left of PLAIN
    print(f"Background color at (237, 18): {bg_pixel}")
    
    # Look for light blue/grey separator lines (same as background)
    def is_separator_color(pixel):
        """Check if pixel is the light blue/grey background color"""
        if len(pixel) >= 3:
            r, g, b = pixel[:3]
            # Background color is approximately (149, 177, 200)
            # Allow some tolerance for slight variations
            if abs(r - 149) < 10 and abs(g - 177) < 10 and abs(b - 200) < 10:
                return True
        return False
    
    # Find vertical grey lines
    print("\nSearching for vertical grey separator lines...")
    v_grey_lines = []
    # Focus on terrain area around PLAIN tile
    for x in range(200, min(width, 400)):  # Check terrain section
        grey_count = 0
        for y in range(0, 100):  # Check top area where terrain tiles are
            pixel = tileset.getpixel((x, y))
            if is_separator_color(pixel):
                grey_count += 1
        
        if grey_count > 20:  # Lower threshold since lines are 1px
            v_grey_lines.append(x)
    
    # Find horizontal grey lines
    print("Searching for horizontal grey separator lines...")
    h_grey_lines = []
    for y in range(0, 100):  # Check top area where terrain tiles are
        grey_count = 0
        for x in range(200, min(width, 400)):  # Check terrain section
            pixel = tileset.getpixel((x, y))
            if is_separator_color(pixel):
                grey_count += 1
        
        if grey_count > 20:  # Lower threshold since lines are 1px
            h_grey_lines.append(y)
    
    # Group consecutive lines
    def group_lines(lines):
        if not lines:
            return []
        
        groups = []
        current_group = [lines[0]]
        
        for i in range(1, len(lines)):
            if lines[i] == lines[i-1] + 1:
                current_group.append(lines[i])
            else:
                groups.append(current_group)
                current_group = [lines[i]]
        
        groups.append(current_group)
        return groups
    
    v_groups = group_lines(v_grey_lines)
    h_groups = group_lines(h_grey_lines)
    
    print(f"\nFound {len(v_groups)} vertical separator groups:")
    for i, group in enumerate(v_groups[:15]):
        print(f"  V-Line {i+1}: x={group[0]} (thickness: {len(group)})")
    
    print(f"\nFound {len(h_groups)} horizontal separator groups:")
    for i, group in enumerate(h_groups[:15]):
        print(f"  H-Line {i+1}: y={group[0]} (thickness: {len(group)})")
    
    # Calculate tile regions based on separators
    print("\n\nCalculating tile positions based on separators:")
    
    # Get single x positions (use first pixel of each group)
    v_positions = [group[0] for group in v_groups]
    h_positions = [group[0] for group in h_groups]
    
    # Calculate tile sizes between separators
    if len(v_positions) > 1:
        x_gaps = []
        for i in range(1, len(v_positions)):
            gap = v_positions[i] - v_positions[i-1]
            x_gaps.append(gap)
        print(f"X-axis gaps between separators: {set(x_gaps)}")
    
    if len(h_positions) > 1:
        y_gaps = []
        for i in range(1, len(h_positions)):
            gap = h_positions[i] - h_positions[i-1]
            y_gaps.append(gap)
        print(f"Y-axis gaps between separators: {set(y_gaps)}")
    
    # Create visualization
    vis = tileset.crop((0, 0, min(600, width), min(400, height)))
    vis_draw = ImageDraw.Draw(vis)
    
    # Draw vertical lines in red
    for group in v_groups:
        if group[0] < 600:
            vis_draw.line([(group[0], 0), (group[0], min(400, height))], fill=(255, 0, 0), width=1)
    
    # Draw horizontal lines in red
    for group in h_groups:
        if group[0] < 400:
            vis_draw.line([(0, group[0]), (min(600, width), group[0])], fill=(255, 0, 0), width=1)
    
    vis.save("separator_lines_visualization.png")
    
    # Now let's check what's between the separators around the PLAIN tile
    print("\n\nChecking tiles around PLAIN position (238, 18):")
    
    # Find which separators PLAIN is between
    plain_x = 238
    plain_y = 18
    
    # Find surrounding separators
    left_sep = max([x for x in v_positions if x < plain_x], default=0)
    right_sep = min([x for x in v_positions if x > plain_x], default=width)
    top_sep = max([y for y in h_positions if y < plain_y], default=0)
    bottom_sep = min([y for y in h_positions if y > plain_y], default=height)
    
    print(f"PLAIN tile is between:")
    print(f"  X: {left_sep} and {right_sep} (width: {right_sep - left_sep})")
    print(f"  Y: {top_sep} and {bottom_sep} (height: {bottom_sep - top_sep})")
    
    # Extract a sample showing the grid
    sample = tileset.crop((220, 0, 320, 100))
    sample_scaled = sample.resize((400, 400), Image.NEAREST)
    sample_draw = ImageDraw.Draw(sample_scaled)
    
    # Mark PLAIN position
    plain_rel_x = (plain_x - 220) * 4
    plain_rel_y = (plain_y - 0) * 4
    sample_draw.rectangle([plain_rel_x, plain_rel_y, plain_rel_x + 64, plain_rel_y + 64], 
                         outline=(0, 255, 0), width=2)
    sample_draw.text((plain_rel_x, plain_rel_y - 15), "PLAIN", fill=(0, 255, 0))
    
    sample_scaled.save("grid_sample_with_plain.png")
    
    print("\n\nCreated files:")
    print("- separator_lines_visualization.png: Shows detected separator lines")
    print("- grid_sample_with_plain.png: Zoomed view of grid around PLAIN tile")

if __name__ == "__main__":
    find_separator_lines()
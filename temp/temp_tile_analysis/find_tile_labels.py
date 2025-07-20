#!/usr/bin/env python3
"""
Find tile labels in the AW2 tileset
"""

from PIL import Image, ImageDraw
import os

def find_labeled_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    
    if not os.path.exists(tileset_path):
        print(f"Error: Tileset not found at {tileset_path}")
        return
    
    tileset = Image.open(tileset_path).convert('RGBA')
    width, height = tileset.size
    print(f"Tileset size: {width}x{height}")
    
    # Let's look at different sections of the tileset to find labels
    # Labels are often in white or light colored text next to tiles
    
    # Create sections to examine
    sections = [
        {"name": "Top section", "x": 0, "y": 0, "w": 400, "h": 100},
        {"name": "Left section", "x": 0, "y": 0, "w": 100, "h": 400},
        {"name": "Middle section", "x": 200, "y": 0, "w": 400, "h": 200},
        {"name": "Right section", "x": 600, "y": 0, "w": 600, "h": 200},
    ]
    
    for i, section in enumerate(sections):
        x, y, w, h = section["x"], section["y"], section["w"], section["h"]
        
        # Ensure we don't go out of bounds
        w = min(w, width - x)
        h = min(h, height - y)
        
        if w > 0 and h > 0:
            crop = tileset.crop((x, y, x + w, y + h))
            crop.save(f"section_{i}_{section['name'].replace(' ', '_')}.png")
            print(f"Saved {section['name']}: ({x}, {y}) to ({x+w}, {y+h})")
    
    # Look for areas with text (usually have many light pixels in a row)
    print("\nSearching for text labels (areas with many light pixels):")
    
    # Scan for horizontal lines with many light pixels (text)
    text_regions = []
    for y in range(0, min(height, 200), 2):  # Check every other line for speed
        light_pixels = 0
        for x in range(width):
            pixel = tileset.getpixel((x, y))
            if len(pixel) >= 3:
                r, g, b = pixel[:3]
                # Check for light colored pixels (text is usually white or light)
                if r > 200 and g > 200 and b > 200:
                    light_pixels += 1
        
        # If many light pixels in a row, might be text
        if light_pixels > 20:
            text_regions.append(y)
    
    # Group consecutive lines
    if text_regions:
        print(f"Found potential text at y-coordinates: {text_regions[:10]}...")
    
    # Let's specifically look at the area with tiles and see if there are labels
    # Based on the grid pattern, let's check areas next to tile groups
    
    # Create a visualization focusing on areas that might have labels
    # The tileset might have labels in specific regions
    
    # Check right side of tileset where labels often appear
    right_section = tileset.crop((900, 0, min(width, 1200), min(height, 400)))
    right_section.save("right_section_with_labels.png")
    
    # Check areas around the tiles we found
    # Labels might be to the right of tile groups
    label_search = Image.new('RGBA', (800, 600), (30, 30, 30, 255))
    draw = ImageDraw.Draw(label_search)
    
    # Look for text patterns near our tile area
    print("\nChecking for labels near tile grid areas:")
    
    # The 9x9 grid pattern starts early in the tileset
    # Labels might be at the edges or in specific rows/columns
    
    # Extract wider area to see labels
    tile_area_with_labels = tileset.crop((0, 0, min(width, 600), min(height, 300)))
    tile_area_with_labels.save("tile_area_with_possible_labels.png")
    
    # Also check if there's a legend or label area
    # Often at the bottom or right side
    if height > 400:
        bottom_section = tileset.crop((0, height - 200, width, height))
        bottom_section.save("bottom_section_labels.png")
    
    # Create a full overview at reduced scale to see the overall structure
    overview = tileset.copy()
    overview.thumbnail((600, 400), Image.Resampling.NEAREST)
    overview.save("tileset_overview.png")
    
    print("\nCreated visualization files:")
    print("- section_*.png: Different sections of the tileset")
    print("- right_section_with_labels.png: Right side where labels often appear")
    print("- tile_area_with_possible_labels.png: Tile area that might have labels")
    print("- bottom_section_labels.png: Bottom section check")
    print("- tileset_overview.png: Full tileset overview")
    
    print("\nNOTE: Check these images to locate the text labels next to tiles.")

if __name__ == "__main__":
    find_labeled_tiles()
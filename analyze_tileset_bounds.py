#!/usr/bin/env python3
"""Analyze the tileset to understand the actual layout"""

from PIL import Image, ImageDraw
import json

def analyze_tileset():
    # Load source image
    img = Image.open('static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png')
    print(f"Image size: {img.size}")
    print(f"Image mode: {img.mode}")
    
    # Convert to RGBA for analysis
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Create a debug image with grid
    debug_img = img.copy()
    draw = ImageDraw.Draw(debug_img)
    
    # Draw grid every 16 pixels
    for x in range(0, img.width, 16):
        draw.line([(x, 0), (x, img.height)], fill=(255, 0, 0, 128), width=1)
    for y in range(0, img.height, 16):
        draw.line([(0, y), (img.width, y)], fill=(255, 0, 0, 128), width=1)
    
    debug_img.save('tileset_grid_debug.png')
    print("Saved tileset_grid_debug.png with 16x16 grid overlay")
    
    # Find non-empty regions
    print("\nSearching for non-empty tile regions...")
    
    # Scan for cities (they should be around y=766 based on the map)
    # But the center offset puts them at negative positions
    # Let's find where they actually are
    
    # Look for vertical strips of content
    for x in range(0, img.width, 16):
        has_content = False
        for y in range(0, img.height):
            pixel = img.getpixel((x, y))
            if len(pixel) == 4 and pixel[3] > 0:  # Non-transparent
                has_content = True
                break
        if has_content:
            print(f"Column at x={x} has content")
    
    # Let's specifically look for cities
    # Cities should be tall structures (32 pixels high)
    print("\nLooking for 32-pixel tall structures (cities, ports, etc.)...")
    
    # Check specific areas where cities might be
    test_areas = [
        (87, 766, "Expected neutral city"),
        (87, 812, "Expected red city"),
        (87, 847, "Expected blue city"),
        (135, 766, "Alternative city location"),
        (135, 812, "Alternative red city")
    ]
    
    for x, y, desc in test_areas:
        if x < img.width and y < img.height - 32:
            # Check if there's content in a 16x32 area
            has_content = False
            for dy in range(32):
                for dx in range(16):
                    if x + dx < img.width and y + dy < img.height:
                        pixel = img.getpixel((x + dx, y + dy))
                        if len(pixel) == 4 and pixel[3] > 0:
                            has_content = True
                            break
                if has_content:
                    break
            
            print(f"{desc} at ({x}, {y}): {'✓ Found' if has_content else '✗ Empty'}")

if __name__ == '__main__':
    analyze_tileset()
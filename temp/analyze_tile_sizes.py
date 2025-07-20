#!/usr/bin/env python3
"""
Analyze the actual tile sizes in the AW2 tileset
Not all tiles are 8x8!
"""

from PIL import Image, ImageDraw
import os

def analyze_tile_sizes():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    
    if not os.path.exists(tileset_path):
        print(f"Error: Tileset not found at {tileset_path}")
        return
    
    tileset = Image.open(tileset_path).convert('RGBA')
    width, height = tileset.size
    print(f"Tileset size: {width}x{height}")
    
    # Let's examine different sections more carefully
    print("\nAnalyzing tile sizes in different sections:")
    
    # Create a visual analysis
    analysis = tileset.copy()
    draw = ImageDraw.Draw(analysis)
    
    # 1. Check the terrain section (Grass, Mountains, Trees)
    print("\n1. Terrain Section (starting at ~216, 27):")
    # These appear to be 16x16 tiles
    for i in range(5):
        x = 216 + i * 17  # 16px tile + 1px separator
        y = 26
        if x + 16 <= width:
            draw.rectangle([x, y, x + 15, y + 15], outline=(0, 255, 0), width=1)
            draw.text((x, y - 10), "16x16", fill=(0, 255, 0))
    
    # 2. Check the buildings section
    print("\n2. Buildings Section (starting at ~486, 0):")
    # These appear to be 8x8 tiles
    for i in range(5):
        x = 495 + i * 9  # 8px tile + 1px separator
        y = 9
        if x + 8 <= width:
            draw.rectangle([x, y, x + 7, y + 7], outline=(255, 0, 0), width=1)
            draw.text((x, y - 10), "8x8", fill=(255, 0, 0))
    
    # 3. Check the water section
    print("\n3. Water Section (starting at ~0, 140):")
    # Let's measure some tiles
    water_y = 149
    for i in range(5):
        x = i * 9  # Testing 8x8 grid
        draw.rectangle([x, water_y, x + 7, water_y + 7], outline=(0, 128, 255), width=1)
    
    # 4. Check larger structures (like volcanoes)
    print("\n4. Large structures:")
    # The volcano at the end of terrain section appears to be 48x48
    volcano_x = 360
    volcano_y = 26
    draw.rectangle([volcano_x, volcano_y, volcano_x + 47, volcano_y + 47], outline=(255, 128, 0), width=2)
    draw.text((volcano_x, volcano_y - 10), "48x48", fill=(255, 128, 0))
    
    analysis.save("tile_size_analysis.png")
    
    # Let's also check by looking for blue separator lines
    print("\n\nLooking for blue separator patterns:")
    
    # Horizontal blue lines
    blue_rows = []
    for y in range(height):
        blue_count = 0
        for x in range(min(width, 500)):
            pixel = tileset.getpixel((x, y))
            if len(pixel) >= 3:
                r, g, b = pixel[:3]
                if b > 200 and r < 100 and g < 150:  # Blue
                    blue_count += 1
        if blue_count > 100:  # Significant blue line
            blue_rows.append(y)
    
    # Analyze gaps between blue lines
    if len(blue_rows) > 1:
        gaps = []
        for i in range(1, len(blue_rows)):
            gap = blue_rows[i] - blue_rows[i-1]
            if gap > 1:  # Ignore consecutive blue pixels
                gaps.append(gap)
        
        print(f"Blue line positions (first 10): {blue_rows[:10]}")
        print(f"Gaps between blue lines: {set(gaps)}")
    
    # Create a detailed view of a mixed section
    detail = Image.new('RGBA', (600, 400), (40, 40, 40, 255))
    detail_draw = ImageDraw.Draw(detail)
    detail_draw.text((10, 10), "TILE SIZE VARIATIONS", fill=(255, 255, 255))
    
    # Show different tile sizes
    examples = [
        ("8x8 Building", 495, 9, 8, 8),
        ("16x16 Terrain", 216, 26, 16, 16),
        ("16x16 Mountain", 252, 26, 16, 16),
        ("48x48 Volcano", 360, 26, 48, 48),
    ]
    
    for i, (name, x, y, w, h) in enumerate(examples):
        if x + w <= width and y + h <= height:
            tile = tileset.crop((x, y, x + w, y + h))
            
            # Position in detail view
            dx = 20 + (i % 4) * 140
            dy = 50 + (i // 4) * 150
            
            # Scale to fit
            scale = min(100 / w, 100 / h)
            tile_scaled = tile.resize((int(w * scale), int(h * scale)), Image.NEAREST)
            
            detail.paste(tile_scaled, (dx, dy))
            detail_draw.rectangle([dx-1, dy-1, dx + w*scale, dy + h*scale], outline=(200, 200, 200))
            detail_draw.text((dx, dy + h*scale + 5), name, fill=(255, 255, 255))
            detail_draw.text((dx, dy + h*scale + 20), f"{w}x{h} pixels", fill=(150, 150, 150))
    
    detail.save("tile_size_examples.png")
    
    print("\n\nSUMMARY:")
    print("- Buildings: 8x8 pixels (with 1px separators)")
    print("- Terrain tiles: 16x16 pixels (with 1px separators)")
    print("- Large structures: 48x48 pixels (like volcanoes)")
    print("- Water tiles: Appear to be 8x8")
    print("\nThe tileset uses MIXED tile sizes!")
    print("\nCreated files:")
    print("- tile_size_analysis.png: Visual analysis of tile sizes")
    print("- tile_size_examples.png: Examples of different tile sizes")

if __name__ == "__main__":
    analyze_tile_sizes()
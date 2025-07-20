#!/usr/bin/env python3
"""
Verify the PLAIN tile at the new position (238, 18)
"""

from PIL import Image, ImageDraw
import os

def verify_plain_position():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    
    if not os.path.exists(tileset_path):
        print(f"Error: Tileset not found")
        return
    
    tileset = Image.open(tileset_path).convert('RGBA')
    print(f"Tileset size: {tileset.size}")
    
    # Create verification image
    verify = Image.new('RGBA', (600, 400), (40, 40, 40, 255))
    draw = ImageDraw.Draw(verify)
    
    # Original position vs new position
    positions = [
        ("Old (Wrong)", 216, 26),
        ("New (Correct)", 238, 18)
    ]
    
    draw.text((300, 20), "PLAIN Tile Position Verification", fill=(255, 255, 255), anchor="mm")
    
    for i, (label, x, y) in enumerate(positions):
        # Draw context area
        context_size = 40
        context = tileset.crop((x - 10, y - 10, x + context_size, y + context_size))
        context_scaled = context.resize((context_size * 4, context_size * 4), Image.NEAREST)
        
        x_pos = 50 + i * 300
        y_pos = 60
        
        verify.paste(context_scaled, (x_pos, y_pos))
        
        # Draw box around the 16x16 tile
        box_x = x_pos + 10 * 4  # 10 pixel offset * 4 scale
        box_y = y_pos + 10 * 4
        draw.rectangle([box_x, box_y, box_x + 63, box_y + 63], outline=(255, 0, 0), width=2)
        
        # Label
        draw.text((x_pos + 80, y_pos + 180), label, fill=(255, 255, 255), anchor="mm")
        draw.text((x_pos + 80, y_pos + 200), f"Position: ({x}, {y})", fill=(150, 150, 150), anchor="mm")
        
        # Extract just the 16x16 tile
        tile = tileset.crop((x, y, x + 16, y + 16))
        tile_large = tile.resize((64, 64), Image.NEAREST)
        verify.paste(tile_large, (x_pos + 50, y_pos + 230))
        draw.rectangle([x_pos + 49, y_pos + 229, x_pos + 114, y_pos + 294], outline=(200, 200, 200))
    
    verify.save("verify_plain_position.png")
    print("\nCreated verify_plain_position.png")
    
    # Also check what's at various positions in the terrain section
    print("\nChecking terrain section tiles:")
    terrain_positions = [
        (216, 26, "Original mapped position"),
        (238, 18, "Your corrected position"),
        (233, 26, "Wood position"),
        (250, 26, "Mountain position"),
    ]
    
    for x, y, desc in terrain_positions:
        if x + 16 <= tileset.width and y + 16 <= tileset.height:
            tile = tileset.crop((x, y, x + 16, y + 16))
            pixels = list(tile.getdata())
            
            # Analyze dominant color
            color_sum = [0, 0, 0]
            count = 0
            for pixel in pixels:
                if len(pixel) >= 3 and (len(pixel) < 4 or pixel[3] > 0):
                    color_sum[0] += pixel[0]
                    color_sum[1] += pixel[1]
                    color_sum[2] += pixel[2]
                    count += 1
            
            if count > 0:
                avg_color = [c // count for c in color_sum]
                print(f"  ({x}, {y}): {desc} - Average RGB: {avg_color}")

if __name__ == "__main__":
    verify_plain_position()
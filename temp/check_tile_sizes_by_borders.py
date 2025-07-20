#!/usr/bin/env python3
"""
Check actual tile sizes by finding grey separator borders
"""

from PIL import Image, ImageDraw
import json

def check_tile_sizes():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # Grey separator color
    separator_color = (149, 177, 200)
    
    def is_separator(pixel):
        """Check if pixel is separator grey"""
        if len(pixel) >= 3:
            r, g, b = pixel[:3]
            return (abs(r - separator_color[0]) < 15 and 
                    abs(g - separator_color[1]) < 15 and 
                    abs(b - separator_color[2]) < 15)
        return False
    
    # Known tile positions to check
    tiles_to_check = [
        ("PLAIN (showcase)", 238, 18),
        ("WOOD (showcase)", 238, 35),
        ("MOUNTAIN (showcase)", 255, 18),
        ("Road (first)", 0, 0),
        ("Pipe (first)", 167, 166),
        ("Water (first in box)", 42, 142),
        ("PLAIN (new coords)", 232, 90),
        ("Building/HQ area", 0, 18)
    ]
    
    print("\nChecking tile sizes by finding separator borders:\n")
    
    for name, x, y in tiles_to_check:
        print(f"{name} at ({x}, {y}):")
        
        # Find right edge (next separator)
        right_edge = x
        for check_x in range(x + 1, min(x + 20, tileset.width)):
            # Check if this column is mostly separator
            sep_count = 0
            total_pixels = 0
            for check_y in range(y, min(y + 17, tileset.height)):
                if is_separator(tileset.getpixel((check_x, check_y))):
                    sep_count += 1
                total_pixels += 1
            
            # Found separator column if most pixels are separator color
            if total_pixels > 0 and sep_count / total_pixels > 0.5:
                right_edge = check_x
                break
        
        # Find bottom edge (next separator)
        bottom_edge = y
        for check_y in range(y + 1, min(y + 20, tileset.height)):
            # Check if this row is mostly separator
            sep_count = 0
            total_pixels = 0
            for check_x in range(x, min(x + 17, tileset.width)):
                if is_separator(tileset.getpixel((check_x, check_y))):
                    sep_count += 1
                total_pixels += 1
            
            # Found separator row if most pixels are separator color
            if total_pixels > 0 and sep_count / total_pixels > 0.5:
                bottom_edge = check_y
                break
        
        width = right_edge - x
        height = bottom_edge - y
        
        print(f"  Tile size: {width}x{height}")
        
        # Check what's after the separator (grid spacing)
        if right_edge + 2 < tileset.width:
            # Check if there's another tile after separator
            has_content = False
            for dy in range(5):
                for dx in range(5):
                    if right_edge + dx + 1 < tileset.width and y + dy < tileset.height:
                        pixel = tileset.getpixel((right_edge + dx + 1, y + dy))
                        if not is_separator(pixel) and pixel[3] > 0:
                            has_content = True
                            break
                if has_content:
                    break
            
            if has_content:
                next_tile_x = right_edge + 1
                # Find how many separator pixels
                sep_width = next_tile_x - right_edge
                print(f"  Grid spacing: {width + sep_width} (tile + {sep_width}px separator)")
        
        print()
    
    # Create visualization
    vis = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    # Show PLAIN tile area with grid
    plain_area = tileset.crop((230, 15, 280, 40))
    plain_scaled = plain_area.resize((plain_area.width * 8, plain_area.height * 8), Image.NEAREST)
    vis.paste(plain_scaled, (50, 50))
    
    draw.text((400, 20), "Tile Size Analysis - PLAIN area", fill=(255, 255, 255), anchor="mm")
    
    # Mark separators
    for x in range(230, 280):
        for y in range(15, 40):
            if is_separator(tileset.getpixel((x, y))):
                vis_x = 50 + (x - 230) * 8
                vis_y = 50 + (y - 15) * 8
                draw.rectangle([vis_x, vis_y, vis_x + 8, vis_y + 8], 
                             fill=(149, 177, 200, 128))
    
    # Mark the PLAIN tile
    plain_vis_x = 50 + (238 - 230) * 8
    plain_vis_y = 50 + (18 - 15) * 8
    draw.rectangle([plain_vis_x, plain_vis_y, plain_vis_x + 16 * 8, plain_vis_y + 16 * 8], 
                   outline=(0, 255, 0), width=2)
    draw.text((plain_vis_x + 64, plain_vis_y - 15), "PLAIN", fill=(0, 255, 0), anchor="mm")
    
    # Show pipe area
    pipe_area = tileset.crop((165, 164, 220, 185))
    pipe_scaled = pipe_area.resize((pipe_area.width * 4, pipe_area.height * 4), Image.NEAREST)
    vis.paste(pipe_scaled, (50, 300))
    
    draw.text((50, 280), "Pipe area:", fill=(255, 255, 255))
    
    # Mark first pipe
    pipe_vis_x = 50 + (167 - 165) * 4
    pipe_vis_y = 300 + (166 - 164) * 4
    draw.rectangle([pipe_vis_x, pipe_vis_y, pipe_vis_x + 15 * 4, pipe_vis_y + 15 * 4], 
                   outline=(255, 128, 0), width=2)
    
    vis.save("tile_size_analysis.png")
    print("Created tile_size_analysis.png")

if __name__ == "__main__":
    check_tile_sizes()
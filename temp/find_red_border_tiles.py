#!/usr/bin/env python3
"""
Find tiles with red borders in water/beach section
"""

from PIL import Image, ImageDraw
import json

def find_red_borders():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Water row at y=58
    water_y = 58
    
    # Create visualization
    vis = Image.new('RGBA', (800, 300), (40, 40, 40, 255))
    
    # Copy wider water section to see beach tiles too
    water_section = tileset.crop((0, water_y - 5, 400, water_y + 30))
    vis.paste(water_section, (0, 50))
    
    draw = ImageDraw.Draw(vis)
    
    print("Scanning for red borders in water/beach section...")
    print(f"Checking y={water_y} to y={water_y + 8}")
    
    # Check each potential tile position
    tiles_with_red = []
    
    for tile_idx in range(20):  # Check 20 tile positions
        x_start = tile_idx * 9
        
        # Check first column of this tile for red
        has_red_border = False
        red_pixels = []
        
        for y in range(water_y, water_y + 8):
            if x_start < tileset.width:
                pixel = tileset.getpixel((x_start, y))
                r, g, b, a = pixel
                
                # Check if red (high red, low green/blue)
                if r > 200 and g < 100 and b < 100:
                    has_red_border = True
                    red_pixels.append(y - water_y)
        
        if has_red_border:
            tiles_with_red.append({
                'index': tile_idx,
                'x': x_start,
                'red_rows': red_pixels
            })
            
            # Mark on visualization
            draw.rectangle([x_start, 50, x_start + 8, 50 + 8], 
                          outline=(255, 0, 0), width=2)
            draw.text((x_start + 4, 45), f"{tile_idx}", fill=(255, 0, 0), anchor="mm")
    
    print(f"\nFound {len(tiles_with_red)} tiles with red borders:")
    for tile in tiles_with_red:
        print(f"  Tile {tile['index']} at x={tile['x']}: red on rows {tile['red_rows']}")
    
    # Let's also check the content after the red border
    if tiles_with_red:
        print("\nAnalyzing first tile with red border:")
        first_red = tiles_with_red[0]
        x_base = first_red['x']
        
        # Check first 10 pixels horizontally
        print(f"Tile at x={x_base}:")
        for x_offset in range(10):
            x = x_base + x_offset
            if x < tileset.width:
                pixel = tileset.getpixel((x, water_y))
                r, g, b, a = pixel
                
                if r > 200 and g < 100 and b < 100:
                    pixel_type = "RED"
                elif abs(r - 149) < 20 and abs(g - 177) < 20 and abs(b - 200) < 20:
                    pixel_type = "SEP"
                elif a == 0:
                    pixel_type = "TRANS"
                elif b > r and b > g:
                    pixel_type = "WATER"
                else:
                    pixel_type = f"?({r},{g},{b})"
                
                print(f"  x+{x_offset}: {pixel_type}")
        
        # Create zoomed view of this tile
        zoom_size = 20
        sample = tileset.crop((x_base, water_y, x_base + zoom_size, water_y + 8))
        sample_scaled = sample.resize((zoom_size * 20, 8 * 20), Image.NEAREST)
        
        vis.paste(sample_scaled, (50, 120))
        
        # Draw grid
        for x in range(zoom_size):
            x_pos = 50 + x * 20
            draw.line([(x_pos, 120), (x_pos, 280)], fill=(100, 100, 100, 128))
            draw.text((x_pos + 10, 290), str(x), fill=(255, 255, 255), anchor="mm")
        
        draw.text((250, 200), f"Zoomed view of tile {first_red['index']}", fill=(255, 255, 255), anchor="mm")
    
    # Check if beach tiles have different pattern
    print("\nChecking beach tile area (after water tiles):")
    beach_start = 36  # Approximate, after 4 water frames
    
    for i in range(10):
        x = beach_start + i * 9
        if x < tileset.width:
            pixel = tileset.getpixel((x, water_y))
            r, g, b, a = pixel
            if r > 200 and g < 100 and b < 100:
                print(f"  Beach tile {i} at x={x} has RED border")
    
    draw.text((400, 20), "Water/Beach Section - Red Border Search", fill=(255, 255, 255), anchor="mm")
    draw.text((10, 10), "Red boxes = Tiles with red borders", fill=(255, 0, 0))
    
    vis.save("red_border_search.png")
    print("\nCreated red_border_search.png")

if __name__ == "__main__":
    find_red_borders()
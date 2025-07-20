#!/usr/bin/env python3
"""
Check if terrain tiles have transparency
"""

from PIL import Image

def check_transparency():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Check tiles based on corrected understanding
    tiles_to_check = [
        ("PLAIN", 238, 18),
        ("FOREST (below plain)", 238, 35),
        ("LOW_MOUNTAIN", 255, 18),
        ("DOUBLE_MOUNTAIN_TOP", 272, 18),
        ("DOUBLE_MOUNTAIN_BOTTOM", 272, 35),
        ("Tile at (255, 35)", 255, 35),
        ("Tile at (289, 18)", 289, 18),
        ("Tile at (289, 35)", 289, 35),
    ]
    
    print("Checking tile transparency:")
    print("-" * 60)
    
    for name, x, y in tiles_to_check:
        tile = tileset.crop((x, y, x + 16, y + 16))
        pixels = list(tile.getdata())
        
        # Count transparent/semi-transparent pixels
        fully_transparent = 0
        semi_transparent = 0
        opaque = 0
        bg_colored = 0  # Background color pixels
        
        for pixel in pixels:
            if len(pixel) == 4:  # Has alpha channel
                r, g, b, a = pixel
                if a == 0:
                    fully_transparent += 1
                elif a < 255:
                    semi_transparent += 1
                else:
                    # Check if it's background color
                    if abs(r - 149) < 10 and abs(g - 177) < 10 and abs(b - 200) < 10:
                        bg_colored += 1
                    else:
                        opaque += 1
            else:
                opaque += 1
        
        total = len(pixels)
        print(f"\n{name} at ({x}, {y}):")
        print(f"  Total pixels: {total}")
        print(f"  Fully transparent: {fully_transparent} ({fully_transparent*100/total:.1f}%)")
        print(f"  Semi-transparent: {semi_transparent} ({semi_transparent*100/total:.1f}%)")
        print(f"  Background colored: {bg_colored} ({bg_colored*100/total:.1f}%)")
        print(f"  Opaque content: {opaque} ({opaque*100/total:.1f}%)")
        
        # Save individual tiles for inspection
        tile.save(f"tile_{name.replace(' ', '_').replace('(', '').replace(')', '')}_at_{x}_{y}.png")
    
    # Create a visual showing tile arrangement
    vis = Image.new('RGBA', (300, 300), (40, 40, 40, 255))
    
    # Draw grid lines
    from PIL import ImageDraw
    draw = ImageDraw.Draw(vis)
    
    # Terrain grid starting position
    start_x = 238
    start_y = 18
    grid_step = 17
    
    # Show 3x3 grid of terrain tiles
    for row in range(3):
        for col in range(3):
            x = start_x + col * grid_step
            y = start_y + row * grid_step
            
            if x + 16 <= tileset.width and y + 16 <= tileset.height:
                tile = tileset.crop((x, y, x + 16, y + 16))
                tile_scaled = tile.resize((64, 64), Image.NEAREST)
                
                vis_x = 20 + col * 90
                vis_y = 20 + row * 90
                
                # Draw background first
                draw.rectangle([vis_x, vis_y, vis_x + 64, vis_y + 64], 
                             fill=(149, 177, 200, 255))
                
                # Paste tile with transparency
                vis.paste(tile_scaled, (vis_x, vis_y), tile_scaled)
                
                # Draw border
                draw.rectangle([vis_x, vis_y, vis_x + 64, vis_y + 64], 
                             outline=(255, 255, 255), width=1)
                
                # Label
                if row == 0 and col == 0:
                    draw.text((vis_x, vis_y - 15), "PLAIN", fill=(255, 255, 0))
                elif row == 1 and col == 0:
                    draw.text((vis_x, vis_y - 15), "FOREST", fill=(255, 255, 0))
                elif row == 0 and col == 1:
                    draw.text((vis_x, vis_y - 15), "LOW MTN", fill=(255, 255, 0))
                elif row == 0 and col == 2:
                    draw.text((vis_x, vis_y - 15), "DBL MTN TOP", fill=(255, 255, 0))
                elif row == 1 and col == 2:
                    draw.text((vis_x, vis_y - 15), "DBL MTN BTM", fill=(255, 255, 0))
    
    vis.save("terrain_transparency_check.png")
    print("\nCreated terrain_transparency_check.png")

if __name__ == "__main__":
    check_transparency()
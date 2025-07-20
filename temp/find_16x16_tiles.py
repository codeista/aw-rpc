#!/usr/bin/env python3
"""
Find tiles assuming they are all 16x16 with content inside
"""

from PIL import Image, ImageDraw
import json

def find_16x16_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # Create visualization
    vis = Image.new('RGBA', (1200, 800), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    # Known working terrain tiles
    print("\nKnown working terrain tiles (16x16):")
    print("PLAIN: (238, 18)")
    print("WOOD: (238, 35)")
    print("MOUNTAIN: (255, 18)")
    
    # Check roads - they might be 16x16 with 8x8 content inside
    print("\nChecking road area for 16x16 tiles...")
    road_y = 0
    road_x_start = 0
    
    # Roads are on a 9x9 grid, but maybe we need to look at 17x17 grid for 16x16 tiles?
    # Or maybe the 8x8 tiles need to be centered in 16x16 space
    
    # Check different grid spacings
    for grid_size in [17, 18, 16]:
        print(f"\nTrying grid size {grid_size}:")
        found_road = False
        
        for col in range(8):
            x = road_x_start + col * grid_size
            y = road_y
            
            if x + 16 <= tileset.width:
                # Check for content in 16x16 area
                has_content = False
                for dy in range(16):
                    for dx in range(16):
                        pixel = tileset.getpixel((x + dx, y + dy))
                        # Skip separator color
                        if not (abs(pixel[0] - 149) < 20 and abs(pixel[1] - 177) < 20 and abs(pixel[2] - 200) < 20):
                            if pixel[3] > 0:
                                has_content = True
                                break
                    if has_content:
                        break
                
                if has_content:
                    print(f"  Found content at ({x}, {y})")
                    found_road = True
                    
                    # Draw on vis
                    area = tileset.crop((x, y, x + 16, y + 16))
                    area_scaled = area.resize((64, 64), Image.NEAREST)
                    vis.paste(area_scaled, (50 + col * 70, 50))
                    draw.rectangle([50 + col * 70, 50, 50 + col * 70 + 64, 114], outline=(255, 255, 0), width=2)
                    draw.text((50 + col * 70 + 32, 120), f"Road {col}", fill=(255, 255, 255), anchor="mm")
        
        if found_road:
            draw.text((500, 80), f"Roads found with grid size {grid_size}", fill=(0, 255, 0), anchor="mm")
            break
    
    # Check water/beach area - maybe they're also 16x16
    print("\nChecking water area for 16x16 tiles...")
    
    # Water starts around (40, 140) with pink border
    # But the actual tile might be centered in a 16x16 area
    water_tests = [
        (40, 140),  # Pink border start
        (38, 139),  # Adjusted
        (42, 142),  # Inside pink border
        (40-4, 140-4),  # Centered for 16x16
    ]
    
    for i, (wx, wy) in enumerate(water_tests):
        if wx >= 0 and wy >= 0 and wx + 16 <= tileset.width and wy + 16 <= tileset.height:
            area = tileset.crop((wx, wy, wx + 16, wy + 16))
            area_scaled = area.resize((64, 64), Image.NEAREST)
            vis.paste(area_scaled, (50 + i * 70, 200))
            draw.rectangle([50 + i * 70, 200, 50 + i * 70 + 64, 264], outline=(0, 150, 255), width=2)
            draw.text((50 + i * 70 + 32, 270), f"Water test {i+1}", fill=(0, 150, 255), anchor="mm")
            print(f"  Water test {i+1} at ({wx}, {wy})")
    
    # Check buildings - maybe they're 16x16 with 8x16 content
    print("\nChecking building area for 16x16 tiles...")
    
    # Buildings start at x=480
    building_tests = [
        (480, 0),     # Original
        (478, 0),     # Adjusted left
        (480, 54),    # Blue buildings
        (478, 54),    # Blue adjusted
    ]
    
    for i, (bx, by) in enumerate(building_tests):
        if bx + 16 <= tileset.width and by + 16 <= tileset.height:
            area = tileset.crop((bx, by, bx + 16, by + 16))
            area_scaled = area.resize((64, 64), Image.NEAREST)
            vis.paste(area_scaled, (50 + i * 70, 350))
            
            # Make pink transparent in display
            draw.rectangle([50 + i * 70, 350, 50 + i * 70 + 64, 414], outline=(255, 100, 100), width=2)
            draw.text((50 + i * 70 + 32, 420), f"Building {i+1}", fill=(255, 100, 100), anchor="mm")
            print(f"  Building test {i+1} at ({bx}, {by})")
    
    # Look for cities specifically
    print("\nSearching for city tiles...")
    
    # Cities might be in a different location
    # Let's scan for 16x16 areas with building-like content
    city_candidates = []
    
    for y in range(0, tileset.height - 16, 17):  # 17x17 grid
        for x in range(240, tileset.width - 16, 17):  # Start after terrain
            # Check for building-like content
            has_building = False
            pink_count = 0
            content_count = 0
            
            for dy in range(16):
                for dx in range(16):
                    pixel = tileset.getpixel((x + dx, y + dy))
                    r, g, b, a = pixel
                    
                    if r > 240 and b > 240 and g < 100:
                        pink_count += 1
                    elif a > 0 and not (abs(r - 149) < 20 and abs(g - 177) < 20 and abs(b - 200) < 20):
                        content_count += 1
            
            # Buildings have pink background and content
            if pink_count > 50 and content_count > 50:
                city_candidates.append((x, y))
                if len(city_candidates) <= 4:
                    print(f"  Found building-like tile at ({x}, {y})")
    
    # Show first few city candidates
    for i, (cx, cy) in enumerate(city_candidates[:4]):
        area = tileset.crop((cx, cy, cx + 16, cy + 16))
        area_scaled = area.resize((64, 64), Image.NEAREST)
        vis.paste(area_scaled, (50 + i * 70, 500))
        draw.rectangle([50 + i * 70, 500, 50 + i * 70 + 64, 564], outline=(255, 255, 0), width=2)
        draw.text((50 + i * 70 + 32, 570), f"City? {i+1}", fill=(255, 255, 0), anchor="mm")
    
    draw.text((600, 20), "Finding 16x16 Tile Boundaries", fill=(255, 255, 255), anchor="mm")
    
    vis.save("find_16x16_tiles.png")
    print("\nCreated find_16x16_tiles.png")

if __name__ == "__main__":
    find_16x16_tiles()
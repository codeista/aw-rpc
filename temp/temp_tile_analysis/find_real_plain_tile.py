#!/usr/bin/env python3
"""
Find the actual plain/grass tile in the original AW:DS tileset
"""

from PIL import Image, ImageDraw
import os

def find_real_plain():
    # Check both possible locations
    tileset_paths = [
        "static/img/backup_tilesets_20250718_142606/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png",
        "static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png"
    ]
    
    tileset = None
    tileset_path = None
    for path in tileset_paths:
        if os.path.exists(path):
            tileset = Image.open(path).convert('RGBA')
            tileset_path = path
            break
    
    if not tileset:
        print("Error: Could not find tileset")
        return
    
    print(f"Loaded tileset: {tileset_path}")
    print(f"Tileset size: {tileset.size}")
    
    # Let's search the entire tileset for green grass tiles
    # Plain tiles in AW are typically light green
    
    grass_tiles = []
    
    # Scan the entire tileset in 16x16 blocks
    for y in range(0, tileset.height - 16, 16):
        for x in range(0, tileset.width - 16, 16):
            tile = tileset.crop((x, y, x + 16, y + 16))
            pixels = list(tile.getdata())
            
            # Count green pixels
            green_count = 0
            light_green_count = 0
            total_non_transparent = 0
            
            for pixel in pixels:
                if len(pixel) >= 4 and pixel[3] > 0:  # Not transparent
                    total_non_transparent += 1
                    r, g, b = pixel[:3]
                    
                    # Check for green
                    if g > r and g > b:
                        green_count += 1
                        # Check for light green (typical plain tile color)
                        if g > 150 and g < 220 and r > 100 and r < 180:
                            light_green_count += 1
            
            # If mostly light green, it's likely a plain tile
            if total_non_transparent > 200 and light_green_count > total_non_transparent * 0.5:
                grass_tiles.append({
                    'pos': (x, y),
                    'green_ratio': light_green_count / total_non_transparent if total_non_transparent > 0 else 0
                })
    
    print(f"\nFound {len(grass_tiles)} potential grass/plain tiles")
    
    # Sort by how green they are
    grass_tiles.sort(key=lambda t: t['green_ratio'], reverse=True)
    
    # Create visualization
    showcase = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    draw = ImageDraw.Draw(showcase)
    draw.text((10, 10), "GRASS/PLAIN TILE CANDIDATES", fill=(255, 255, 255))
    draw.text((10, 30), "Sorted by green content (most green first)", fill=(150, 150, 150))
    
    # Show top candidates
    for i, tile_info in enumerate(grass_tiles[:30]):
        x, y = tile_info['pos']
        
        col = i % 10
        row = i // 10
        sx = 20 + col * 75
        sy = 60 + row * 120
        
        tile = tileset.crop((x, y, x + 16, y + 16))
        tile_scaled = tile.resize((60, 60), Image.NEAREST)
        showcase.paste(tile_scaled, (sx, sy))
        
        draw.rectangle([sx-1, sy-1, sx+60, sy+60], outline=(0, 255, 0) if i == 0 else (200, 200, 200), width=2)
        draw.text((sx, sy + 64), f"({x},{y})", fill=(255, 255, 255), font=None)
        draw.text((sx, sy + 78), f"{tile_info['green_ratio']:.1%}", fill=(150, 255, 150), font=None)
    
    showcase.save("real_plain_tile_candidates.png")
    
    # Also check specific areas where grass tiles usually are
    print("\nChecking common grass tile locations...")
    
    # In AW tilesets, terrain tiles are often in the upper areas
    common_areas = [
        (0, 0, 100, 100),      # Top left
        (100, 0, 200, 100),    # Top middle
        (0, 100, 100, 200),    # Middle left
        (345, 0, 445, 100),    # Top right
    ]
    
    area_showcase = Image.new('RGBA', (600, 400), (40, 40, 40, 255))
    area_draw = ImageDraw.Draw(area_showcase)
    area_draw.text((10, 10), "CHECKING COMMON TERRAIN AREAS", fill=(255, 255, 255))
    
    tile_count = 0
    for area_idx, (x1, y1, x2, y2) in enumerate(common_areas):
        area_draw.text((10, 50 + area_idx * 20), f"Area {area_idx + 1}: ({x1},{y1}) to ({x2},{y2})", fill=(150, 150, 150))
        
        for y in range(y1, min(y2, tileset.height - 16), 16):
            for x in range(x1, min(x2, tileset.width - 16), 16):
                if tile_count >= 20:
                    break
                    
                tile = tileset.crop((x, y, x + 16, y + 16))
                
                col = tile_count % 10
                row = tile_count // 10
                sx = 20 + col * 55
                sy = 150 + row * 70
                
                tile_scaled = tile.resize((48, 48), Image.NEAREST)
                area_showcase.paste(tile_scaled, (sx, sy))
                
                area_draw.rectangle([sx-1, sy-1, sx+48, sy+48], outline=(200, 200, 200), width=1)
                area_draw.text((sx, sy + 50), f"{x},{y}", fill=(100, 100, 100), font=None)
                
                tile_count += 1
    
    area_showcase.save("tileset_area_samples.png")
    
    # If we found grass tiles, suggest the best one
    if grass_tiles:
        best_tile = grass_tiles[0]
        print(f"\n✅ Best plain/grass tile candidate: {best_tile['pos']}")
        print(f"   Green ratio: {best_tile['green_ratio']:.1%}")
        
        # Extract and save the best candidate
        x, y = best_tile['pos']
        best_tile_img = tileset.crop((x, y, x + 16, y + 16))
        best_tile_large = best_tile_img.resize((128, 128), Image.NEAREST)
        best_tile_large.save("best_plain_tile_candidate.png")
        
        print(f"\nSaved best candidate as: best_plain_tile_candidate.png")
    
    print("\nCreated visualization files:")
    print("- real_plain_tile_candidates.png: All grass tile candidates")
    print("- tileset_area_samples.png: Samples from common terrain areas")
    print("- best_plain_tile_candidate.png: The most likely plain tile")

if __name__ == "__main__":
    find_real_plain()
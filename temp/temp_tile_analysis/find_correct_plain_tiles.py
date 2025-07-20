#!/usr/bin/env python3
"""
Find the correct plain tiles by examining both tilesets more carefully
"""

from PIL import Image, ImageDraw
import os

def find_plain_tiles():
    # Load both tilesets
    old_tileset_path = "static/img/backup_tilesets_20250718_142606/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png"
    new_tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    
    # First, let's check what the current game actually uses for PLAIN
    print("Checking render_legacy.js PLAIN tile calculation:")
    print("  spriteSheetWidth = 445, spriteSheetHeight = 1163")
    print("  x = 445/2 - 16/2 = 214.5")
    print("  y = 1163/2 - 16/2 = 573.5")
    print("  PLAIN offset: x - 8, y - 64")
    print("  Final: (206, 509)")
    
    if os.path.exists(old_tileset_path):
        old_tileset = Image.open(old_tileset_path).convert('RGBA')
        print(f"\nOld tileset size: {old_tileset.size}")
        
        # Extract what's at (206, 509)
        if old_tileset.width > 206 + 16 and old_tileset.height > 509 + 16:
            current_plain = old_tileset.crop((206, 509, 206 + 16, 509 + 16))
            current_plain_scaled = current_plain.resize((128, 128), Image.NEAREST)
            current_plain_scaled.save("current_plain_tile_check.png")
            
            # Analyze the tile
            pixels = list(current_plain.getdata())
            # Count color types
            green_pixels = 0
            brown_pixels = 0
            gray_pixels = 0
            
            for pixel in pixels:
                if len(pixel) >= 3:
                    r, g, b = pixel[:3]
                    if g > r and g > b:
                        green_pixels += 1
                    elif r > 100 and abs(r - g) < 30 and abs(g - b) < 30:
                        gray_pixels += 1
                    elif r > g and r > b and g > b:
                        brown_pixels += 1
            
            print(f"\nCurrent tile at (206, 509) analysis:")
            print(f"  Green pixels: {green_pixels}")
            print(f"  Brown pixels: {brown_pixels}")
            print(f"  Gray pixels: {gray_pixels}")
    
    # Now let's search both tilesets for actual plain tiles
    # Plain tiles in AW are typically light green with some variation
    
    print("\n\nSearching for plain tiles in old tileset...")
    if os.path.exists(old_tileset_path):
        old_tileset = Image.open(old_tileset_path).convert('RGBA')
        
        # Common plain tile locations in AW tilesets
        plain_candidates_old = []
        
        # Search in common areas
        search_areas = [
            (0, 0, 100, 100),      # Top left
            (200, 500, 250, 550),  # Around current position
            (0, 250, 100, 350),    # Middle left
            (100, 0, 200, 100),    # Top middle
        ]
        
        for area in search_areas:
            x1, y1, x2, y2 = area
            for y in range(y1, min(y2, old_tileset.height - 16), 16):
                for x in range(x1, min(x2, old_tileset.width - 16), 16):
                    tile = old_tileset.crop((x, y, x + 16, y + 16))
                    pixels = list(tile.getdata())
                    
                    # Look for light green tiles
                    light_green_count = 0
                    for pixel in pixels:
                        if len(pixel) >= 3:
                            r, g, b = pixel[:3]
                            # Light green: green dominant, fairly bright
                            if g > r and g > b and g > 150 and g < 220:
                                light_green_count += 1
                    
                    if light_green_count > len(pixels) * 0.5:
                        plain_candidates_old.append((x, y))
        
        print(f"Found {len(plain_candidates_old)} potential plain tiles in old tileset")
        
        # Save samples
        if plain_candidates_old:
            showcase = Image.new('RGBA', (400, 200), (40, 40, 40, 255))
            draw = ImageDraw.Draw(showcase)
            draw.text((10, 10), "OLD TILESET PLAIN CANDIDATES", fill=(255, 255, 255))
            
            for i, (x, y) in enumerate(plain_candidates_old[:8]):
                col = i % 4
                row = i // 4
                sx = 20 + col * 90
                sy = 40 + row * 90
                
                tile = old_tileset.crop((x, y, x + 16, y + 16))
                tile_scaled = tile.resize((64, 64), Image.NEAREST)
                showcase.paste(tile_scaled, (sx, sy))
                
                draw.rectangle([sx-1, sy-1, sx+64, sy+64], outline=(200, 200, 200), width=1)
                draw.text((sx, sy + 68), f"({x},{y})", fill=(150, 150, 150))
            
            showcase.save("old_tileset_plain_candidates.png")
    
    print("\n\nSearching for plain tiles in new tileset...")
    if os.path.exists(new_tileset_path):
        new_tileset = Image.open(new_tileset_path).convert('RGBA')
        
        # For the new tileset with 8x8 tiles on 9px grid
        plain_candidates_new = []
        
        # Search the entire tileset systematically
        for y in range(0, min(300, new_tileset.height - 8), 9):
            for x in range(0, min(400, new_tileset.width - 8), 9):
                tile = new_tileset.crop((x, y, x + 8, y + 8))
                pixels = list(tile.getdata())
                
                # Look for light green tiles
                light_green_count = 0
                total_brightness = 0
                
                for pixel in pixels:
                    if len(pixel) >= 3:
                        r, g, b = pixel[:3]
                        brightness = (r + g + b) / 3
                        total_brightness += brightness
                        
                        # Light green check
                        if g > r and g > b and g > 150 and r > 100:
                            light_green_count += 1
                
                avg_brightness = total_brightness / len(pixels)
                
                # Plain tiles are typically light green and bright
                if light_green_count > len(pixels) * 0.4 and avg_brightness > 150:
                    plain_candidates_new.append((x, y))
        
        print(f"Found {len(plain_candidates_new)} potential plain tiles in new tileset")
        
        # Save samples
        if plain_candidates_new:
            showcase = Image.new('RGBA', (600, 300), (40, 40, 40, 255))
            draw = ImageDraw.Draw(showcase)
            draw.text((10, 10), "NEW TILESET PLAIN CANDIDATES (8x8 tiles)", fill=(255, 255, 255))
            
            for i, (x, y) in enumerate(plain_candidates_new[:15]):
                col = i % 5
                row = i // 5
                sx = 20 + col * 110
                sy = 40 + row * 90
                
                tile = new_tileset.crop((x, y, x + 8, y + 8))
                tile_scaled = tile.resize((64, 64), Image.NEAREST)
                showcase.paste(tile_scaled, (sx, sy))
                
                draw.rectangle([sx-1, sy-1, sx+64, sy+64], outline=(200, 200, 200), width=1)
                draw.text((sx, sy + 68), f"({x},{y})", fill=(150, 150, 150))
            
            showcase.save("new_tileset_plain_candidates.png")
    
    # Let's also check what a typical AW plain tile looks like
    print("\n\nCreating reference plain tile (what it should look like):")
    reference = Image.new('RGBA', (16, 16), (180, 210, 140, 255))  # Light green
    draw = ImageDraw.Draw(reference)
    
    # Add some texture
    for y in range(0, 16, 2):
        for x in range(0, 16, 2):
            if (x + y) % 4 == 0:
                draw.point((x, y), fill=(170, 200, 130, 255))
    
    reference_scaled = reference.resize((128, 128), Image.NEAREST)
    reference_scaled.save("reference_plain_tile.png")
    
    print("\nCreated visualization files:")
    print("- current_plain_tile_check.png: What's currently at (206, 509)")
    print("- old_tileset_plain_candidates.png: Potential plains in old tileset")
    print("- new_tileset_plain_candidates.png: Potential plains in new tileset")
    print("- reference_plain_tile.png: What a plain tile typically looks like")

if __name__ == "__main__":
    find_plain_tiles()
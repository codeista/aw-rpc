#!/usr/bin/env python3
"""
Extract the original PLAIN tile from the AW:DS tileset using the exact coordinates from render_legacy.js
"""

from PIL import Image, ImageDraw
import os

def extract_original_plain():
    # The original tileset used in the game
    tileset_path = "static/img/backup_tilesets_20250718_142606/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png"
    
    if not os.path.exists(tileset_path):
        # Try the current location
        tileset_path = "static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png"
        if not os.path.exists(tileset_path):
            print(f"Error: Could not find tileset")
            return
    
    tileset = Image.open(tileset_path).convert('RGBA')
    print(f"Tileset size: {tileset.size}")
    
    # From render_legacy.js:
    # spriteSheetWidth = 445, spriteSheetHeight = 1163
    # SPRITESIZE = 16
    # x = spriteSheetWidth/2 - SPRITESIZE/2 = 445/2 - 8 = 214.5
    # y = spriteSheetHeight/2 - SPRITESIZE/2 = 1163/2 - 8 = 573.5
    # PLAIN offset: x - 8, y - 64
    # Final: x = 206.5, y = 509.5 (rounds to 206, 509)
    
    # Let's extract tiles around this position to find the actual plain tile
    positions_to_check = [
        (206, 509),  # Calculated position
        (206, 517),  # Try +8 in y
        (214, 509),  # Try without x offset
        (214, 517),  # Try without x offset and +8 y
        (222, 509),  # Try +16 in x
        (222, 517),  # Try +16 in x and +8 y
    ]
    
    showcase = Image.new('RGBA', (600, 400), (40, 40, 40, 255))
    draw = ImageDraw.Draw(showcase)
    draw.text((10, 10), "SEARCHING FOR ORIGINAL PLAIN TILE", fill=(255, 255, 255))
    draw.text((10, 30), f"Tileset: {os.path.basename(tileset_path)}", fill=(150, 150, 150))
    
    # Also create a larger search area
    search_area = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    search_draw = ImageDraw.Draw(search_area)
    search_draw.text((10, 10), "EXPANDED SEARCH AREA", fill=(255, 255, 255))
    
    # Check specific positions
    for i, (x, y) in enumerate(positions_to_check):
        if x + 16 <= tileset.width and y + 16 <= tileset.height:
            tile = tileset.crop((x, y, x + 16, y + 16))
            
            # Position in showcase
            col = i % 3
            row = i // 3
            sx = 20 + col * 190
            sy = 60 + row * 170
            
            # Scale up for visibility
            tile_scaled = tile.resize((128, 128), Image.NEAREST)
            showcase.paste(tile_scaled, (sx, sy))
            
            # Draw border
            draw.rectangle([sx-1, sy-1, sx+128, sy+128], outline=(200, 200, 200), width=1)
            
            # Add position label
            draw.text((sx, sy + 132), f"Position: ({x}, {y})", fill=(255, 255, 255))
            
            # Analyze tile
            pixels = list(tile.getdata())
            colors = {}
            for pixel in pixels:
                if len(pixel) >= 3:
                    r, g, b = pixel[:3]
                    color_type = "unknown"
                    if g > r and g > b and g > 100:
                        color_type = "green"
                    elif b > r and b > g and b > 100:
                        color_type = "blue"
                    elif abs(r - g) < 20 and abs(g - b) < 20:
                        color_type = "gray"
                    elif r > g and g > b:
                        color_type = "brown"
                    
                    colors[color_type] = colors.get(color_type, 0) + 1
            
            # Show color analysis
            color_info = ", ".join([f"{k}: {v}" for k, v in sorted(colors.items(), key=lambda x: -x[1])])
            draw.text((sx, sy + 148), color_info, fill=(150, 150, 150))
    
    showcase.save("original_plain_tile_search.png")
    
    # Do a broader search in the area
    print("\nSearching broader area around calculated position...")
    search_x_start = max(0, 190)
    search_y_start = max(0, 490)
    search_x_end = min(tileset.width, 240)
    search_y_end = min(tileset.height, 540)
    
    grid_size = 16
    found_tiles = []
    
    for y in range(search_y_start, search_y_end - 16, grid_size):
        for x in range(search_x_start, search_x_end - 16, grid_size):
            tile = tileset.crop((x, y, x + 16, y + 16))
            pixels = list(tile.getdata())
            
            # Look for tiles that are mostly one color (typical for terrain)
            color_counts = {}
            for pixel in pixels:
                if len(pixel) >= 3:
                    # Round colors to reduce variations
                    r, g, b = pixel[:3]
                    key = (r//10*10, g//10*10, b//10*10)
                    color_counts[key] = color_counts.get(key, 0) + 1
            
            # If dominated by one color, it's likely a terrain tile
            if color_counts:
                max_count = max(color_counts.values())
                if max_count > len(pixels) * 0.6:  # 60% same color
                    dominant_color = [k for k, v in color_counts.items() if v == max_count][0]
                    found_tiles.append({
                        'pos': (x, y),
                        'color': dominant_color,
                        'count': max_count
                    })
    
    # Create visualization of found tiles
    if found_tiles:
        for i, tile_info in enumerate(found_tiles[:20]):
            x, y = tile_info['pos']
            
            col = i % 10
            row = i // 10
            sx = 20 + col * 70
            sy = 60 + row * 100
            
            tile = tileset.crop((x, y, x + 16, y + 16))
            tile_scaled = tile.resize((48, 48), Image.NEAREST)
            search_area.paste(tile_scaled, (sx, sy))
            
            search_draw.rectangle([sx-1, sy-1, sx+48, sy+48], outline=(200, 200, 200), width=1)
            search_draw.text((sx, sy + 52), f"({x},{y})", fill=(150, 150, 150), font=None)
            
            # Show dominant color
            r, g, b = tile_info['color']
            color_rect = Image.new('RGBA', (48, 10), (r, g, b, 255))
            search_area.paste(color_rect, (sx, sy + 68))
    
    search_area.save("original_tileset_search_area.png")
    
    print(f"\nFound {len(found_tiles)} potential terrain tiles in search area")
    print("\nCreated files:")
    print("- original_plain_tile_search.png: Specific positions checked")
    print("- original_tileset_search_area.png: Broader search results")
    
    # Let's also check what other tile types look like at their calculated positions
    print("\n\nChecking other tile types for reference:")
    
    # From render_legacy.js, other tile offsets:
    tile_types = {
        'PLAIN': (-8, -64),
        'WOOD': (-352, -56),
        'MOUNTAIN': (-25, -39),
        'ROAD_HORT': (-42, -64),
        'CITY': (-93, -294),
        'FACTORY': (-212, -294),
    }
    
    reference = Image.new('RGBA', (800, 300), (40, 40, 40, 255))
    ref_draw = ImageDraw.Draw(reference)
    ref_draw.text((10, 10), "TILE TYPE REFERENCE FROM RENDER_LEGACY.JS", fill=(255, 255, 255))
    
    base_x = 445/2 - 8  # 214.5
    base_y = 1163/2 - 8  # 573.5
    
    for i, (tile_type, (x_offset, y_offset)) in enumerate(tile_types.items()):
        x = int(base_x + x_offset)
        y = int(base_y + y_offset)
        
        if 0 <= x < tileset.width - 16 and 0 <= y < tileset.height - 16:
            tile = tileset.crop((x, y, x + 16, y + 16))
            
            col = i % 6
            row = i // 6
            sx = 20 + col * 120
            sy = 50 + row * 120
            
            tile_scaled = tile.resize((80, 80), Image.NEAREST)
            reference.paste(tile_scaled, (sx, sy))
            
            ref_draw.rectangle([sx-1, sy-1, sx+80, sy+80], outline=(200, 200, 200), width=1)
            ref_draw.text((sx, sy + 84), tile_type, fill=(255, 255, 255))
            ref_draw.text((sx, sy + 100), f"({x}, {y})", fill=(150, 150, 150))
    
    reference.save("tile_type_reference.png")
    print("- tile_type_reference.png: Reference tiles from different types")

if __name__ == "__main__":
    extract_original_plain()
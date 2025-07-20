#!/usr/bin/env python3
"""
Simple sprite verification without transparency issues
"""

from PIL import Image, ImageDraw
import os

def verify_unit_sprites():
    """Create simple unit sprite grid"""
    
    sheet = Image.open("/home/box/Documents/aw-rpc/static/img/units_sprite_sheet_complete.png")
    
    # Create preview at 3x scale
    scale = 3
    preview = Image.new('RGBA', (sheet.width * scale + 40, sheet.height * scale + 40), (200, 200, 200, 255))
    draw = ImageDraw.Draw(preview)
    
    # Title
    draw.text((10, 10), "UNIT SPRITES (250 total) - 10x25 grid", fill=(0, 0, 0))
    
    # Scale up the entire sheet
    sheet_scaled = sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST)
    preview.paste(sheet_scaled, (20, 30))
    
    # Draw grid
    for x in range(0, sheet.width + 1, 16):
        draw.line([(20 + x * scale, 30), (20 + x * scale, 30 + sheet.height * scale)], fill=(128, 128, 128))
    for y in range(0, sheet.height + 1, 16):
        draw.line([(20, 30 + y * scale), (20 + sheet.width * scale, 30 + y * scale)], fill=(128, 128, 128))
    
    # Add row/column numbers
    for col in range(10):
        draw.text((25 + col * 16 * scale, 15), str(col), fill=(0, 0, 0))
    for row in range(25):
        draw.text((5, 35 + row * 16 * scale), str(row), fill=(0, 0, 0))
    
    preview.save("temp/unit_sprites_grid.png")
    print("Created: temp/unit_sprites_grid.png")

def verify_terrain_tiles():
    """Create terrain tile samples"""
    
    sheet = Image.open("/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal.png")
    
    # Create sample sheets
    scale = 3
    samples_per_page = 400
    sample_cols = 20
    
    # Extract some tiles
    tiles = []
    for y in range(0, sheet.height, 16):
        for x in range(0, sheet.width, 16):
            if x + 16 > sheet.width or y + 16 > sheet.height:
                continue
            tile = sheet.crop((x, y, x + 16, y + 16))
            if tile.getbbox():  # Has content
                tiles.append((x, y, tile))
    
    print(f"Found {len(tiles)} terrain tiles")
    
    # Create sample pages
    for page in range(3):  # Just first 3 pages
        start_idx = page * samples_per_page
        end_idx = min(start_idx + samples_per_page, len(tiles))
        
        if start_idx >= len(tiles):
            break
            
        rows = ((end_idx - start_idx) + sample_cols - 1) // sample_cols
        
        preview = Image.new('RGBA', 
            (sample_cols * 16 * scale + 40, rows * 16 * scale + 60),
            (200, 200, 200, 255))
        draw = ImageDraw.Draw(preview)
        
        # Title
        draw.text((10, 10), f"TERRAIN TILES - Page {page + 1} (tiles {start_idx}-{end_idx-1})", fill=(0, 0, 0))
        
        # Draw tiles
        for i, (x, y, tile) in enumerate(tiles[start_idx:end_idx]):
            col = i % sample_cols
            row = i // sample_cols
            
            x_dst = col * 16 * scale + 20
            y_dst = row * 16 * scale + 40
            
            # Scale tile
            tile_scaled = tile.resize((16 * scale, 16 * scale), Image.NEAREST)
            
            # Draw background
            draw.rectangle([x_dst, y_dst, x_dst + 16*scale - 1, y_dst + 16*scale - 1], 
                          fill=(255, 255, 255), outline=(128, 128, 128))
            
            # Paste tile
            preview.paste(tile_scaled, (x_dst, y_dst))
            
            # Add tile number
            draw.text((x_dst + 2, y_dst + 2), str(start_idx + i), fill=(255, 0, 0))
        
        filename = f"temp/terrain_tiles_page_{page + 1}.png"
        preview.save(filename)
        print(f"Created: {filename}")

def create_summary():
    """Create extraction summary"""
    
    # Also extract first few sprites to check
    os.makedirs("temp/sample_sprites", exist_ok=True)
    
    # Extract first 10 unit sprites
    sheet = Image.open("/home/box/Documents/aw-rpc/static/img/units_sprite_sheet_complete.png")
    for i in range(10):
        x = (i % 10) * 16
        y = (i // 10) * 16
        sprite = sheet.crop((x, y, x + 16, y + 16))
        sprite.save(f"temp/sample_sprites/unit_{i:03d}.png")
    
    # Extract first 10 terrain tiles
    sheet = Image.open("/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal.png")
    count = 0
    for y in range(0, min(100, sheet.height), 16):
        for x in range(0, sheet.width, 16):
            if x + 16 <= sheet.width and y + 16 <= sheet.height:
                tile = sheet.crop((x, y, x + 16, y + 16))
                if tile.getbbox():
                    tile.save(f"temp/sample_sprites/terrain_{count:03d}.png")
                    count += 1
                    if count >= 10:
                        break
        if count >= 10:
            break
    
    print("\n=== VERIFICATION SUMMARY ===")
    print("Created verification images:")
    print("- temp/unit_sprites_grid.png - All 250 unit sprites in grid")
    print("- temp/terrain_tiles_page_1.png - First 400 terrain tiles")
    print("- temp/terrain_tiles_page_2.png - Next 400 terrain tiles")
    print("- temp/terrain_tiles_page_3.png - Next 400 terrain tiles")
    print("\nExtracted samples to temp/sample_sprites/")
    print("\nPlease review these images to verify sprites are correct")

def main():
    os.makedirs("temp", exist_ok=True)
    
    print("=== CREATING SPRITE VERIFICATION ===\n")
    
    verify_unit_sprites()
    verify_terrain_tiles()
    create_summary()

if __name__ == "__main__":
    main()
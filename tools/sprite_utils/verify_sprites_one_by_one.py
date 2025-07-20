#!/usr/bin/env python3
"""
Verify each sprite one by one before upscaling
"""

from PIL import Image, ImageDraw, ImageFont
import os
import json

def create_unit_verification_sheet():
    """Create a verification sheet for unit sprites"""
    
    sheet_path = "/home/box/Documents/aw-rpc/static/img/units_sprite_sheet_complete.png"
    sheet = Image.open(sheet_path)
    
    # Create larger preview with labels
    preview_scale = 4  # Show sprites at 4x size
    cols = 10
    rows = 25
    cell_size = 16 * preview_scale + 20  # Extra space for labels
    
    preview = Image.new('RGBA', 
        (cols * cell_size + 20, rows * cell_size + 40), 
        (200, 200, 200, 255))
    
    # Draw grid and sprites
    draw = ImageDraw.Draw(preview)
    
    # Title
    draw.text((10, 10), "UNIT SPRITES VERIFICATION (250 sprites)", fill=(0, 0, 0))
    
    sprite_count = 0
    
    # Known unit order (based on typical AW sprite sheets)
    unit_names = [
        # Row 0-4: Red Army
        "Infantry", "Mech", "Recon", "Tank", "MDTank",
        "Neotank", "APC", "Artillery", "Rocket", "AntiAir",
        "Missile", "Fighter", "Bomber", "BCopter", "TCopter",
        "BShip", "Cruiser", "Lander", "Sub", "Stealth",
        "BlackBomb", "Carrier", "MegaTank", "PipeRunner", "BlackBoat",
        
        # Rows 5-9: Blue Army (same order)
        # Rows 10-14: Green Army
        # Rows 15-19: Yellow Army  
        # Rows 20-24: Black Army
    ]
    
    armies = ["RED", "BLUE", "GREEN", "YELLOW", "BLACK"]
    states = ["idle", "used"]
    
    for row in range(rows):
        for col in range(cols):
            x_src = col * 16
            y_src = row * 16
            
            # Extract sprite
            sprite = sheet.crop((x_src, y_src, x_src + 16, y_src + 16))
            
            # Calculate position in preview
            x_dst = col * cell_size + 20
            y_dst = row * cell_size + 40
            
            # Draw cell border
            draw.rectangle(
                [x_dst, y_dst, x_dst + cell_size - 1, y_dst + cell_size - 1],
                outline=(128, 128, 128)
            )
            
            # Scale and paste sprite
            sprite_scaled = sprite.resize((16 * preview_scale, 16 * preview_scale), Image.NEAREST)
            preview.paste(sprite_scaled, (x_dst + 10, y_dst + 10), sprite_scaled)
            
            # Add label
            army_idx = row // 5
            unit_idx = (row % 5) * 2 + (col % 2)
            state = states[col % 2]
            
            if army_idx < len(armies) and unit_idx < len(unit_names):
                army = armies[army_idx]
                unit = unit_names[unit_idx]
                label = f"{sprite_count}: {unit}"
                
                # Draw sprite number
                draw.text((x_dst + 2, y_dst + 2), str(sprite_count), fill=(0, 0, 0))
                
            sprite_count += 1
    
    preview.save("temp/unit_sprites_verification.png")
    print(f"Created unit verification sheet: temp/unit_sprites_verification.png")
    print(f"Total unit sprites: {sprite_count}")

def create_terrain_verification_sheet():
    """Create verification sheets for terrain tiles"""
    
    sheet_path = "/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal.png"
    sheet = Image.open(sheet_path)
    
    # Create multiple sheets (too many tiles for one image)
    tiles_per_sheet = 500
    preview_scale = 3
    cols = 25
    
    tile_count = 0
    sheet_num = 0
    
    # Common terrain types we expect
    terrain_types = {
        0: "Plains/Road tiles",
        100: "Forest/Mountain tiles", 
        200: "Water/Bridge tiles",
        300: "Building tiles",
        400: "More buildings",
        500: "Special terrain"
    }
    
    current_preview = None
    sprites_in_current = 0
    
    for y in range(0, sheet.height, 16):
        for x in range(0, sheet.width, 16):
            if x + 16 > sheet.width or y + 16 > sheet.height:
                continue
                
            tile = sheet.crop((x, y, x + 16, y + 16))
            
            # Skip empty
            if tile.getbbox() is None:
                continue
            
            # Create new preview sheet if needed
            if sprites_in_current == 0:
                rows_needed = (min(tiles_per_sheet, 1944 - tile_count) + cols - 1) // cols
                current_preview = Image.new('RGBA',
                    (cols * 16 * preview_scale + 40, rows_needed * 16 * preview_scale + 60),
                    (200, 200, 200, 255))
                draw = ImageDraw.Draw(current_preview)
                
                # Title
                title = f"TERRAIN TILES VERIFICATION - Sheet {sheet_num + 1}"
                if tile_count in terrain_types:
                    title += f" ({terrain_types[tile_count]})"
                draw.text((10, 10), title, fill=(0, 0, 0))
            
            # Position in preview
            col = sprites_in_current % cols
            row = sprites_in_current // cols
            x_dst = col * 16 * preview_scale + 20
            y_dst = row * 16 * preview_scale + 40
            
            # Scale and paste
            tile_scaled = tile.resize((16 * preview_scale, 16 * preview_scale), Image.NEAREST)
            current_preview.paste(tile_scaled, (x_dst, y_dst), tile_scaled)
            
            # Draw border and number
            draw.rectangle(
                [x_dst, y_dst, x_dst + 16 * preview_scale - 1, y_dst + 16 * preview_scale - 1],
                outline=(128, 128, 128)
            )
            draw.text((x_dst + 2, y_dst + 2), str(tile_count), fill=(0, 0, 0))
            
            tile_count += 1
            sprites_in_current += 1
            
            # Save sheet when full
            if sprites_in_current >= tiles_per_sheet:
                filename = f"temp/terrain_tiles_verification_{sheet_num + 1}.png"
                current_preview.save(filename)
                print(f"Created terrain verification sheet {sheet_num + 1}: {filename}")
                sheet_num += 1
                sprites_in_current = 0
    
    # Save last sheet
    if sprites_in_current > 0:
        filename = f"temp/terrain_tiles_verification_{sheet_num + 1}.png"
        current_preview.save(filename)
        print(f"Created terrain verification sheet {sheet_num + 1}: {filename}")
    
    print(f"Total terrain tiles: {tile_count}")

def create_extraction_summary():
    """Create a summary of what we're extracting"""
    
    summary = """
=== SPRITE EXTRACTION SUMMARY ===

UNIT SPRITES (250 total):
- Source: units_sprite_sheet_complete.png (160x400)
- Layout: 10 columns x 25 rows
- Organization: 5 armies x 25 units x 2 states (idle/used)
- Army order: Red, Blue, Green, Yellow, Black
- All sprites are 16x16 pixels

TERRAIN TILES (~1944 total):
- Source: Advance_Wars_Dual_Strike_Tileset_Normal.png (445x1163)
- Includes: Plains, roads, forests, mountains, water, bridges, buildings
- All tiles are 16x16 pixels

VERIFICATION FILES CREATED:
- temp/unit_sprites_verification.png - All 250 unit sprites with grid
- temp/terrain_tiles_verification_1.png - First 500 terrain tiles
- temp/terrain_tiles_verification_2.png - Next 500 terrain tiles
- temp/terrain_tiles_verification_3.png - Next 500 terrain tiles
- temp/terrain_tiles_verification_4.png - Remaining terrain tiles

Please review these verification sheets before proceeding with upscaling.
"""
    
    with open("temp/sprite_extraction_summary.txt", "w") as f:
        f.write(summary)
    
    print(summary)

def main():
    os.makedirs("temp", exist_ok=True)
    
    print("=== CREATING SPRITE VERIFICATION SHEETS ===\n")
    
    # Create verification sheets
    create_unit_verification_sheet()
    print()
    create_terrain_verification_sheet()
    print()
    create_extraction_summary()
    
    print("\n✅ Verification complete!")
    print("Please review the verification images in temp/ folder")
    print("Once verified, we can proceed with extraction and upscaling")

if __name__ == "__main__":
    main()
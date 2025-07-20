#!/usr/bin/env python3
"""
Extract terrain tiles using the EXACT coordinate system from render_legacy.js
"""

from PIL import Image, ImageDraw
import os

def extract_terrain_tiles_correct():
    """Extract terrain tiles using exact render.js coordinates"""
    
    tileset_path = "/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png"
    tileset = Image.open(tileset_path)
    
    print(f"Tileset: {tileset.width}x{tileset.height}")
    
    # Exact coordinates from render_legacy.js
    # Base calculation:
    spriteSheetWidth = 445
    spriteSheetHeight = 1163
    SPRITESIZE = 16
    
    base_x = spriteSheetWidth/2 - SPRITESIZE/2  # 222.5 - 8 = 214.5
    base_y = spriteSheetHeight/2 - SPRITESIZE/2  # 581.5 - 8 = 573.5
    
    print(f"Base coordinates: ({base_x}, {base_y})")
    
    # Extract coordinates EXACTLY as they appear in render_legacy.js
    terrain_tiles = [
        # Basic terrain
        ('PLAIN', -8, -64, False),
        ('WOOD', -352, -56, True),  # _2xHeight = true
        ('MOUNTAIN', -25, -39, True),  # _2xHeight = true
        ('SEA', -76, -94, False),
        ('REEF', -195, -145, False),
        
        # Roads
        ('ROAD_HORT', -42, -64, False),
        ('ROAD_VERT', -59, -64, False),
        ('ROAD_NW', -42, -13, False),
        ('ROAD_NE', -76, -13, False),
        ('ROAD_SE', -76, -47, False),
        ('ROAD_SW', -42, -47, False),
        
        # Bridges
        ('HBridge', -76, -64, False),
        ('VBridge', -94, -64, False),
        
        # Rivers
        ('RIVER_HORT', -386, -145, False),
        ('RIVER_VERT', -420, -111, False),
        ('RIVER_NE', -369, -94, False),
        ('RIVER_NW', -403, -94, False),
        ('RIVER_SE', -403, -128, False),
        ('RIVER_SW', -369, -128, False),
        
        # Beaches
        ('BEACH_N', -265, -111, False),
        ('BEACH_E', -214, -321, False),
        ('BEACH_S', -265, -304, False),
        ('BEACH_W', -231, -321, False),
        ('BEACH_NE', -333, -198, False),
        ('BEACH_NW', -282, -355, False),
        ('BEACH_SW', -350, -355, False),
        ('BEACH_SE', -333, -145, False),
        
        # Buildings (RED army coordinates)
        ('CITY', -87, -812, True),  # _2xHeight = true
        ('FACTORY', -102, -818, True),
        ('AIRPORT', -120, -818, True),
        ('PORT', -137, -811, True),
        ('HQ', -154, -811, True),
        ('COM_TOWER', -1, -812, True),
        ('LAB', -171, -812, True),
        
        # Special
        ('MISSILE_SILO', -188, -766, True),
        ('EMPTY_SILO', -205, -767, True),
        
        # Pipes
        ('PIPE_VERT', -212, -30, False),
        ('PIPE_HORT', -195, -30, False),
        ('PIPE_END_N', -178, -30, False),
        ('PIPE_END_S', -178, -47, False),
        ('PIPE_END_W', -144, -64, False),
        ('PIPE_END_E', -161, -64, False),
    ]
    
    os.makedirs("temp/terrain_extracted", exist_ok=True)
    
    extracted = 0
    failed = 0
    
    # Create verification image
    verify_img = tileset.convert('RGBA').copy()
    draw = ImageDraw.Draw(verify_img)
    
    for terrain_name, x_offset, y_offset, is_double in terrain_tiles:
        # Calculate final coordinates
        final_x = int(base_x + x_offset)
        final_y = int(base_y + y_offset)
        height = 32 if is_double else 16
        
        print(f"\n{terrain_name}:")
        print(f"  Offset: ({x_offset}, {y_offset})")
        print(f"  Final pos: ({final_x}, {final_y})")
        print(f"  Size: 16x{height}")
        
        # Check bounds - Two.js might handle this differently!
        # The texture offset is used by Two.js to select which part of the image to show
        # It doesn't necessarily need to be within positive bounds
        
        if final_x < 0 or final_y < 0:
            print(f"  ! Negative coordinates - Two.js handles this")
            failed += 1
            continue
            
        if final_x + 16 > tileset.width or final_y + height > tileset.height:
            print(f"  ! Out of bounds: needs ({final_x + 16}, {final_y + height}) but tileset is ({tileset.width}, {tileset.height})")
            failed += 1
            continue
        
        # Extract tile
        tile = tileset.crop((final_x, final_y, final_x + 16, final_y + height))
        
        if tile.getbbox():
            print(f"  ✓ Extracted successfully")
            extracted += 1
            
            # Save tile
            filename = f"{terrain_name}.png"
            tile.save(f"temp/terrain_extracted/{filename}")
            
            # Mark on verification
            color = (255, 0, 0) if is_double else (0, 255, 0)
            draw.rectangle([final_x, final_y, final_x + 15, final_y + height - 1], 
                         outline=color, width=1)
            draw.text((final_x + 1, final_y + 1), terrain_name[:4], fill=(255, 255, 0))
        else:
            print(f"  ✗ Empty tile")
            failed += 1
    
    # Save verification
    verify_img.save("temp/terrain_extraction_verification.png")
    
    print(f"\n=== RESULTS ===")
    print(f"Extracted: {extracted}")
    print(f"Failed: {failed}")
    print(f"Total attempted: {len(terrain_tiles)}")
    
    if extracted > 0:
        print(f"\nExtracted tiles saved to: temp/terrain_extracted/")
        print(f"Verification image: temp/terrain_extraction_verification.png")
    
    return extracted, failed

def main():
    print("=== EXTRACTING TERRAIN TILES WITH EXACT RENDER.JS COORDINATES ===\n")
    
    extracted, failed = extract_terrain_tiles_correct()
    
    if failed > 0:
        print(f"\n⚠️  {failed} tiles failed extraction")
        print("This might be normal if some coordinates are meant for Two.js offset handling")

if __name__ == "__main__":
    main()
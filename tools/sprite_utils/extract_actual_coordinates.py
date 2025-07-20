#!/usr/bin/env python3
"""
Extract actual sprite coordinates from render_legacy.js
"""

from PIL import Image, ImageDraw
import os

def get_terrain_coordinates():
    """Extract terrain sprite coordinates from render.js"""
    
    # Base coordinates from render.js
    # var x = spriteSheetWidth/2 - SPRITESIZE/2;
    # var y = spriteSheetHeight/2 - SPRITESIZE/2;
    # spriteSheetWidth = 445, spriteSheetHeight = 1163, SPRITESIZE = 16
    
    base_x = 445/2 - 16/2  # 222.5 - 8 = 214.5
    base_y = 1163/2 - 16/2  # 581.5 - 8 = 573.5
    
    # Manually extracted coordinates from render.js
    terrain_coords = {
        'PLAIN': {'x': base_x - 8, 'y': base_y - 64, 'height': 16},
        'WOOD': {'x': base_x - 352, 'y': base_y - 56, 'height': 32},
        'MOUNTAIN': {'x': base_x - 25, 'y': base_y - 39, 'height': 32},
        'ROAD_HORT': {'x': base_x - 42, 'y': base_y - 64, 'height': 16},
        'ROAD_VERT': {'x': base_x - 59, 'y': base_y - 64, 'height': 16},
        'SEA': {'x': base_x - 76, 'y': base_y - 94, 'height': 16},
        'HBridge': {'x': base_x - 76, 'y': base_y - 64, 'height': 16},
        'VBridge': {'x': base_x - 94, 'y': base_y - 64, 'height': 16},
        'REEF': {'x': base_x - 195, 'y': base_y - 145, 'height': 16},
        'RIVER_HORT': {'x': base_x - 386, 'y': base_y - 145, 'height': 16},
        'RIVER_VERT': {'x': base_x - 420, 'y': base_y - 111, 'height': 16},
        
        # Buildings - most are 32 pixels tall
        'CITY': {'x': base_x - 87, 'y': base_y - 812, 'height': 32},  # RED army
        'FACTORY': {'x': base_x - 102, 'y': base_y - 818, 'height': 32},  # RED army
        'AIRPORT': {'x': base_x - 120, 'y': base_y - 818, 'height': 32},  # RED army
        'PORT': {'x': base_x - 137, 'y': base_y - 811, 'height': 32},  # RED army
        'HQ': {'x': base_x - 154, 'y': base_y - 811, 'height': 32},  # RED army
        'COM_TOWER': {'x': base_x - 1, 'y': base_y - 812, 'height': 32},  # RED army
        'LAB': {'x': base_x - 171, 'y': base_y - 812, 'height': 32},  # RED army
        'MISSILE_SILO': {'x': base_x - 188, 'y': base_y - 766, 'height': 32},
        'EMPTY_SILO': {'x': base_x - 205, 'y': base_y - 767, 'height': 32},
    }
    
    # Convert to integers
    for terrain, coord in terrain_coords.items():
        coord['x'] = int(coord['x'])
        coord['y'] = int(coord['y'])
    
    return terrain_coords

def verify_and_extract_tiles():
    """Extract tiles based on actual coordinates"""
    
    tileset_path = "/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png"
    tileset = Image.open(tileset_path)
    
    coords = get_terrain_coordinates()
    
    print("=== EXTRACTING TILES FROM ACTUAL COORDINATES ===\n")
    print(f"Tileset: {tileset.width}x{tileset.height}")
    print(f"Base coordinates: (214, 573)\n")
    
    # Create output directory
    os.makedirs("temp/extracted_tiles", exist_ok=True)
    
    # Create verification image
    verify_img = tileset.convert('RGBA').copy()
    draw = ImageDraw.Draw(verify_img)
    
    extracted = 0
    failed = 0
    
    for terrain_type, coord in coords.items():
        x = coord['x']
        y = coord['y']
        height = coord['height']
        
        print(f"{terrain_type}:")
        print(f"  Position: ({x}, {y})")
        print(f"  Size: 16x{height}")
        
        # Check bounds
        if x < 0 or y < 0 or x + 16 > tileset.width or y + height > tileset.height:
            print(f"  ✗ Out of bounds!")
            failed += 1
            continue
        
        # Extract tile
        tile = tileset.crop((x, y, x + 16, y + height))
        
        # Check if has content
        if tile.getbbox():
            print(f"  ✓ Extracted successfully")
            extracted += 1
            
            # Save tile
            filename = f"{terrain_type}_16x{height}.png"
            tile.save(f"temp/extracted_tiles/{filename}")
            
            # Mark on verification image
            color = (255, 0, 0) if height == 32 else (0, 255, 0)
            draw.rectangle([x, y, x + 15, y + height - 1], outline=color, width=2)
            draw.text((x + 2, y + 2), terrain_type[:4], fill=(255, 255, 0))
        else:
            print(f"  ✗ Empty tile!")
            failed += 1
    
    # Save verification image
    verify_img.save("temp/tileset_with_extracted_marked.png")
    
    print(f"\n=== SUMMARY ===")
    print(f"Successfully extracted: {extracted}")
    print(f"Failed: {failed}")
    print(f"\nExtracted tiles saved to: temp/extracted_tiles/")
    print(f"Verification image: temp/tileset_with_extracted_marked.png")

def create_tile_preview():
    """Create a preview of extracted tiles"""
    
    tile_dir = "temp/extracted_tiles"
    if not os.path.exists(tile_dir):
        return
    
    tiles = []
    for filename in sorted(os.listdir(tile_dir)):
        if filename.endswith('.png'):
            path = os.path.join(tile_dir, filename)
            img = Image.open(path)
            name = filename.replace('.png', '').replace('_16x16', '').replace('_16x32', ' (2x)')
            tiles.append((name, img))
    
    if not tiles:
        return
    
    # Create preview
    cols = 10
    cell_width = 120
    cell_height = 50
    
    rows = (len(tiles) + cols - 1) // cols
    
    preview = Image.new('RGBA', (cols * cell_width, rows * cell_height + 30), (200, 200, 200, 255))
    draw = ImageDraw.Draw(preview)
    
    draw.text((10, 10), "EXTRACTED TERRAIN TILES", fill=(0, 0, 0))
    
    for i, (name, tile) in enumerate(tiles):
        col = i % cols
        row = i // cols
        
        x = col * cell_width + 10
        y = row * cell_height + 30
        
        # Draw tile (scale if needed)
        if tile.height == 32:
            # Scale down for display
            display_tile = tile.resize((16, 32), Image.NEAREST)
        else:
            display_tile = tile
        
        # Background
        draw.rectangle([x, y, x + 20, y + 36], fill=(255, 255, 255), outline=(128, 128, 128))
        
        # Paste tile
        preview.paste(display_tile, (x + 2, y + 2))
        
        # Label
        draw.text((x + 25, y + 10), name, fill=(0, 0, 0))
    
    preview.save("temp/extracted_tiles_preview.png")
    print("\nCreated preview: temp/extracted_tiles_preview.png")

def main():
    verify_and_extract_tiles()
    create_tile_preview()

if __name__ == "__main__":
    main()
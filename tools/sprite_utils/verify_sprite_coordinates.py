#!/usr/bin/env python3
"""
Verify sprite coordinates from render.js match actual tileset
"""

from PIL import Image, ImageDraw
import re

def extract_terrain_coordinates():
    """Extract terrain tile coordinates from render.js"""
    
    print("=== EXTRACTING COORDINATES FROM render_legacy.js ===\n")
    
    with open("/home/box/Documents/aw-rpc/static/js/render_legacy.js", "r") as f:
        content = f.read()
    
    # Find the drawTerrainSprite function
    terrain_section = content[content.find("function drawTerrainSprite"):content.find("function drawUnitSprite")]
    
    # Extract coordinates for each terrain type
    terrain_coords = {}
    
    # Pattern to find case statements and their coordinates
    # Looking for patterns like:
    # case 'PLAIN':
    #     x = x - 8;
    #     y = y - 23;
    
    lines = terrain_section.split('\n')
    current_case = None
    base_x = None
    base_y = None
    
    # Find the base coordinates
    if "var x = spriteSheetWidth/2 - SPRITESIZE/2;" in terrain_section:
        # spriteSheetWidth is 445, SPRITESIZE is 16
        base_x = 445/2 - 16/2  # 222.5 - 8 = 214.5
        base_y = 1163/2 - 16/2  # 581.5 - 8 = 573.5
        print(f"Base coordinates: x={base_x}, y={base_y}")
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Find case statements
        if line.startswith("case '") and line.endswith("':"):
            current_case = line[6:-2]  # Extract terrain type
            
            # Look for x and y adjustments in next few lines
            x_offset = 0
            y_offset = 0
            is_double = False
            
            for j in range(i+1, min(i+10, len(lines))):
                next_line = lines[j].strip()
                
                # Extract x offset
                if "x = x -" in next_line:
                    match = re.search(r'x = x - (\d+)', next_line)
                    if match:
                        x_offset = -int(match.group(1))
                elif "x = x +" in next_line:
                    match = re.search(r'x = x \+ (\d+)', next_line)
                    if match:
                        x_offset = int(match.group(1))
                
                # Extract y offset
                if "y = y -" in next_line:
                    match = re.search(r'y = y - (\d+)', next_line)
                    if match:
                        y_offset = -int(match.group(1))
                elif "y = y +" in next_line:
                    match = re.search(r'y = y \+ (\d+)', next_line)
                    if match:
                        y_offset = int(match.group(1))
                
                # Check for double height
                if "_2xHeight = true" in next_line:
                    is_double = True
                
                # Stop at break statement
                if "break;" in next_line:
                    break
            
            if base_x is not None and x_offset != 0 or y_offset != 0:
                final_x = int(base_x + x_offset)
                final_y = int(base_y + y_offset)
                
                terrain_coords[current_case] = {
                    "x": final_x,
                    "y": final_y,
                    "double_height": is_double,
                    "x_offset": x_offset,
                    "y_offset": y_offset
                }
    
    return terrain_coords

def verify_coordinates_on_tileset(coords):
    """Verify the coordinates point to actual tiles"""
    
    tileset_path = "/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png"
    tileset = Image.open(tileset_path)
    
    print(f"\n=== VERIFYING COORDINATES ON TILESET ===")
    print(f"Tileset size: {tileset.width}x{tileset.height}\n")
    
    # Create a verification image
    verify_img = tileset.convert('RGBA').copy()
    draw = ImageDraw.Draw(verify_img)
    
    # Sample some important terrain types
    important_types = ['PLAIN', 'MOUNTAIN', 'CITY', 'FACTORY', 'HQ', 'AIRPORT', 'PORT', 
                      'ROAD_HORT', 'ROAD_VERT', 'WOOD', 'SEA']
    
    found = 0
    for terrain_type, coord in coords.items():
        if terrain_type not in important_types:
            continue
            
        x = coord['x']
        y = coord['y']
        height = 32 if coord['double_height'] else 16
        
        print(f"{terrain_type}:")
        print(f"  Position: ({x}, {y})")
        print(f"  Size: 16x{height}")
        
        # Check if coordinates are valid
        if x < 0 or y < 0 or x + 16 > tileset.width or y + height > tileset.height:
            print(f"  ERROR: Coordinates out of bounds!")
            continue
        
        # Extract the tile
        tile = tileset.crop((x, y, x + 16, y + height))
        
        # Check if it has content
        if tile.getbbox():
            print(f"  ✓ Has content")
            found += 1
            
            # Draw rectangle on verification image
            color = (255, 0, 0) if coord['double_height'] else (0, 255, 0)
            draw.rectangle([x, y, x + 15, y + height - 1], outline=color, width=2)
            draw.text((x + 2, y + 2), terrain_type[:4], fill=(255, 255, 255))
        else:
            print(f"  ✗ Empty!")
    
    # Save verification image
    verify_img.save("temp/tileset_coordinates_verify.png")
    print(f"\n✓ Found {found}/{len(important_types)} important terrain types")
    print("Saved verification image: temp/tileset_coordinates_verify.png")
    
    return coords

def check_unit_coordinates():
    """Check unit sprite coordinates"""
    
    print("\n=== CHECKING UNIT SPRITE COORDINATES ===")
    
    # Unit sprites use a different system - they're in a grid
    sheet = Image.open("/home/box/Documents/aw-rpc/static/img/units_sprite_sheet_complete.png")
    
    print(f"Unit sprite sheet: {sheet.width}x{sheet.height}")
    print(f"Grid: {sheet.width//16} x {sheet.height//16} = {(sheet.width//16) * (sheet.height//16)} sprites")
    print("All unit sprites are 16x16 pixels")
    
    # The unit coordinates in render.js use a different calculation
    # They multiply unit type and army indices by sprite size

def main():
    # Extract terrain coordinates
    terrain_coords = extract_terrain_coordinates()
    
    print(f"\nFound {len(terrain_coords)} terrain type coordinates")
    
    # Show some examples
    print("\nExample coordinates:")
    for terrain_type in ['PLAIN', 'MOUNTAIN', 'HQ', 'CITY', 'FACTORY']:
        if terrain_type in terrain_coords:
            coord = terrain_coords[terrain_type]
            print(f"  {terrain_type}: ({coord['x']}, {coord['y']}) {'[2x height]' if coord['double_height'] else ''}")
    
    # Verify on tileset
    verify_coordinates_on_tileset(terrain_coords)
    
    # Check units
    check_unit_coordinates()
    
    print("\n✅ Coordinate verification complete!")
    print("Check temp/tileset_coordinates_verify.png to see marked tiles")

if __name__ == "__main__":
    main()
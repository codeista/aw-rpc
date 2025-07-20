#!/usr/bin/env python3
from PIL import Image

# Road tile coordinates from render_legacy.js
centerX = 222.5
centerY = 581.5
SPRITESIZE = 16

road_offsets = [
    ('ROAD_HORT', -42, -64),
    ('ROAD_VERT', -59, -64),
    ('ROAD_NW', -42, -13),
    ('ROAD_NE', -76, -13),
    ('ROAD_SE', -76, -47),
    ('ROAD_SW', -42, -47),
    ('SWNRoad', -93, -47),
    ('NESRoad', -110, -47),
    ('WNERoad', -110, -81),
    ('ESWRoad', -93, -81),
    ('CRoad', -59, -30),
]

# Load the AW2 tileset
tileset = Image.open('static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png')

print("Road tiles from game coordinates:")
print("-" * 50)

for name, x_offset, y_offset in road_offsets:
    # Calculate actual sprite position
    x = int(centerX - SPRITESIZE/2 + x_offset)
    y = int(centerY - SPRITESIZE/2 + y_offset)
    
    # Check if coordinates are valid
    if 0 <= x < tileset.width - SPRITESIZE and 0 <= y < tileset.height - SPRITESIZE:
        # Extract the tile
        tile = tileset.crop((x, y, x + SPRITESIZE, y + SPRITESIZE))
        
        # Check if it's not empty (has non-transparent pixels)
        has_content = any(pixel[3] > 0 for pixel in tile.getdata() if len(pixel) > 3)
        
        print(f"{name:12} at ({x:3}, {y:3}) - {'Has content' if has_content else 'Empty/Transparent'}")
    else:
        print(f"{name:12} at ({x:3}, {y:3}) - Out of bounds!")

print("\nNow checking the new road tile area (starting at 12,19):")
print("-" * 50)

# Check the new road tiles
start_x, start_y = 12, 19
for row in range(2):
    for col in range(8):
        x = start_x + col * 17
        y = start_y + row * 17
        
        if x < tileset.width - 16 and y < tileset.height - 16:
            tile = tileset.crop((x, y, x + 16, y + 16))
            has_content = any(pixel[3] > 0 for pixel in tile.getdata() if len(pixel) > 3)
            print(f"Row {row}, Col {col} at ({x:3}, {y:3}) - {'Has content' if has_content else 'Empty'}")
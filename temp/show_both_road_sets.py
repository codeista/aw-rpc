#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont

# Create output image
output = Image.new('RGBA', (800, 600), (51, 51, 51, 255))
draw = ImageDraw.Draw(output)

# Load tileset
tileset = Image.open('static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png')

# Set 1: Current game road tiles (from render_legacy.js)
centerX = 222.5
centerY = 581.5
SPRITESIZE = 16

current_roads = [
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

# Draw title
draw.text((20, 10), "Current Game Road Tiles (from render_legacy.js)", fill=(255, 255, 255))

# Draw current road tiles
x_pos = 20
y_pos = 40
for i, (name, x_offset, y_offset) in enumerate(current_roads):
    # Calculate position
    src_x = int(centerX - SPRITESIZE/2 + x_offset)
    src_y = int(centerY - SPRITESIZE/2 + y_offset)
    
    # Extract and paste tile (scaled 4x)
    tile = tileset.crop((src_x, src_y, src_x + 16, src_y + 16))
    tile_scaled = tile.resize((64, 64), Image.NEAREST)
    output.paste(tile_scaled, (x_pos, y_pos), tile_scaled)
    
    # Draw label
    draw.text((x_pos, y_pos + 66), name, fill=(200, 200, 200))
    draw.text((x_pos, y_pos + 78), f"({src_x},{src_y})", fill=(150, 150, 150))
    
    x_pos += 70
    if (i + 1) % 8 == 0:
        x_pos = 20
        y_pos += 100

# Set 2: New road tiles at (12,19)
draw.text((20, 300), "New Road Tiles (starting at 12,19)", fill=(255, 255, 255))

road_names = [
    'SE corner', 'Horizontal', 'SW corner', 'T-WNE', 'Vertical', 'NE corner', 'T-ESW', 'T-SWN',
    'NW corner', 'T-NES', 'Cross/4way', 'H-Bridge', 'V-Bridge', '', '', ''
]

x_pos = 20
y_pos = 330
start_x, start_y = 12, 19
for row in range(2):
    for col in range(8):
        idx = row * 8 + col
        if idx < len(road_names) and road_names[idx]:
            src_x = start_x + col * 17
            src_y = start_y + row * 17
            
            # Extract and paste tile (scaled 4x)
            tile = tileset.crop((src_x, src_y, src_x + 16, src_y + 16))
            tile_scaled = tile.resize((64, 64), Image.NEAREST)
            output.paste(tile_scaled, (x_pos, y_pos), tile_scaled)
            
            # Draw label
            draw.text((x_pos, y_pos + 66), road_names[idx], fill=(200, 200, 200))
            draw.text((x_pos, y_pos + 78), f"({src_x},{src_y})", fill=(150, 150, 150))
        
        x_pos += 95
        if col == 7:
            x_pos = 20
            y_pos += 100

# Save output
output.save('road_tiles_comparison.png')
print("Created road_tiles_comparison.png")
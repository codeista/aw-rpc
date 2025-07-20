#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import json

# Load the new coordinate mapping
with open('new_tileset_coordinates.json', 'r') as f:
    mapping = json.load(f)

# Create output image
output = Image.new('RGBA', (800, 400), (51, 51, 51, 255))
draw = ImageDraw.Draw(output)

# Load tileset
tileset = Image.open('static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png')

# Draw title
draw.text((20, 10), "New Road Tile Mapping Verification", fill=(255, 255, 255))

# Get road tiles
road_data = mapping['tiles']['roads']
road_tiles = road_data['tiles']

# Sort by grid position for display
sorted_roads = sorted(road_tiles.items(), key=lambda x: (x[1]['grid'][0], x[1]['grid'][1]))

# Display tiles
x_pos = 20
y_pos = 50
col = 0

for name, info in sorted_roads:
    # Extract tile from new coordinates
    src_x = info['x']
    src_y = info['y']
    
    # Get the tile (16x16)
    tile = tileset.crop((src_x, src_y, src_x + 16, src_y + 16))
    
    # Scale up 4x for display
    tile_scaled = tile.resize((64, 64), Image.NEAREST)
    
    # Paste tile
    output.paste(tile_scaled, (x_pos, y_pos), tile_scaled)
    
    # Draw name
    draw.text((x_pos, y_pos + 66), name, fill=(255, 255, 255))
    draw.text((x_pos, y_pos + 78), f"({src_x},{src_y})", fill=(180, 180, 180))
    
    # Draw visual description based on name
    desc = ""
    if name == "ROAD_HORT":
        desc = "━━━"
    elif name == "ROAD_VERT":
        desc = "┃"
    elif name == "ROAD_NW":
        desc = "┏"
    elif name == "ROAD_NE":
        desc = "┓"
    elif name == "ROAD_SE":
        desc = "┛"
    elif name == "ROAD_SW":
        desc = "┗"
    elif "Road" in name:
        if name == "WNERoad":
            desc = "┳"
        elif name == "ESWRoad":
            desc = "┻"
        elif name == "SWNRoad":
            desc = "┣"
        elif name == "NESRoad":
            desc = "┫"
        elif name == "CRoad":
            desc = "╋"
    elif name == "HBridge":
        desc = "═"
    elif name == "VBridge":
        desc = "║"
    
    draw.text((x_pos + 70, y_pos + 25), desc, fill=(100, 255, 100), font=None)
    
    x_pos += 100
    col += 1
    if col >= 8:
        col = 0
        x_pos = 20
        y_pos += 100

# Add note
draw.text((20, 350), "Note: Visual symbols show expected road connections", fill=(150, 150, 150))

# Save
output.save('new_road_mapping_verification.png')
print("Created new_road_mapping_verification.png")
print("\nRoad tiles mapped:")
for name, info in sorted_roads:
    print(f"  {name:12} at ({info['x']}, {info['y']})")
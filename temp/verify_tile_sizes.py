#!/usr/bin/env python3
"""
Verify tile sizes for different sections of the tileset
"""

from PIL import Image, ImageDraw, ImageFont
import json

def verify_tile_sizes():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    
    # Create visualization
    vis = Image.new('RGBA', (1000, 800), (40, 40, 40, 255))
    draw = ImageDraw.Draw(vis)
    
    # Section 1: Roads (8x8 tiles)
    road_area = tileset.crop((0, 0, 72, 36))  # 8x4 grid of 8x8 tiles + separators
    road_scaled = road_area.resize((road_area.width * 4, road_area.height * 4), Image.NEAREST)
    vis.paste(road_scaled, (50, 50))
    draw.text((50, 30), "Roads: 8x8 tiles on 9x9 grid", fill=(255, 255, 255))
    
    # Draw grid for roads
    for i in range(9):  # 8 tiles + 1
        x = 50 + i * 9 * 4
        if i < 8:
            draw.line([(x, 50), (x, 50 + 144)], fill=(255, 100, 100), width=1)
    for i in range(5):  # 4 tiles + 1
        y = 50 + i * 9 * 4
        if i < 4:
            draw.line([(50, y), (50 + 288, y)], fill=(255, 100, 100), width=1)
    
    # Section 2: Terrain tiles (16x16)
    terrain_area = tileset.crop((238, 18, 273, 53))  # PLAIN and below
    terrain_scaled = terrain_area.resize((terrain_area.width * 4, terrain_area.height * 4), Image.NEAREST)
    vis.paste(terrain_scaled, (400, 50))
    draw.text((400, 30), "Terrain: 16x16 tiles on 17x17 grid", fill=(255, 255, 255))
    
    # Mark PLAIN
    draw.rectangle([400, 50, 400 + 64, 50 + 64], outline=(0, 255, 0), width=2)
    draw.text((432, 120), "PLAIN", fill=(0, 255, 0), anchor="mm")
    
    # Mark WOOD
    draw.rectangle([400, 50 + 68, 400 + 64, 50 + 68 + 64], outline=(0, 200, 0), width=2)
    draw.text((432, 190), "WOOD", fill=(0, 200, 0), anchor="mm")
    
    # Section 3: Pipes (15x15)
    pipe_area = tileset.crop((167, 166, 235, 234))  # 4x4 grid of pipes
    pipe_scaled = pipe_area.resize((pipe_area.width * 3, pipe_area.height * 3), Image.NEAREST)
    vis.paste(pipe_scaled, (50, 250))
    draw.text((50, 230), "Pipes: 15x15 tiles on 17x17 grid", fill=(255, 255, 255))
    
    # Draw grid for pipes
    for i in range(5):  # 4 tiles + 1
        coord = 50 + i * 17 * 3
        if coord < 50 + 204:
            draw.line([(coord, 250), (coord, 250 + 204)], fill=(255, 128, 0), width=1)
            draw.line([(50, coord - 200), (50 + 204, coord - 200)], fill=(255, 128, 0), width=1)
    
    # Section 4: Water tiles (8x8)
    water_area = tileset.crop((40, 140, 58, 158))  # First water box
    water_scaled = water_area.resize((water_area.width * 6, water_area.height * 6), Image.NEAREST)
    vis.paste(water_scaled, (400, 250))
    draw.text((400, 230), "Water: 8x8 tiles on 9x9 grid", fill=(255, 255, 255))
    
    # Mark the actual water tile (not the pink border)
    draw.rectangle([400 + 12, 250 + 12, 400 + 12 + 48, 250 + 12 + 48], outline=(0, 150, 255), width=2)
    
    # Section 5: Buildings (8x16)
    building_area = tileset.crop((481, 330, 497, 362))  # A building tile
    building_scaled = building_area.resize((building_area.width * 6, building_area.height * 3), Image.NEAREST)
    vis.paste(building_scaled, (50, 500))
    draw.text((50, 480), "Buildings: 8x16 tiles", fill=(255, 255, 255))
    
    # Summary text
    draw.text((400, 500), "Tile Size Summary:", fill=(255, 255, 255))
    draw.text((400, 530), "• Roads: 8x8 pixels", fill=(200, 200, 200))
    draw.text((400, 550), "• Water/Edges: 8x8 pixels", fill=(200, 200, 200))
    draw.text((400, 570), "• Buildings: 8x16 pixels", fill=(200, 200, 200))
    draw.text((400, 590), "• Pipes: 15x15 pixels", fill=(200, 200, 200))
    draw.text((400, 610), "• Terrain: 16x16 pixels", fill=(200, 200, 200))
    
    draw.text((400, 650), "Grid spacings:", fill=(255, 255, 255))
    draw.text((400, 680), "• 8x8 tiles: 9x9 grid (1px separator)", fill=(200, 200, 200))
    draw.text((400, 700), "• 15x15 tiles: 17x17 grid (2px separator)", fill=(200, 200, 200))
    draw.text((400, 720), "• 16x16 tiles: 17x17 grid (1px separator)", fill=(200, 200, 200))
    
    # Check the "new" plain coordinates
    if 232 <= tileset.width and 105 <= tileset.height:
        new_plain_area = tileset.crop((232, 90, 248, 106))
        sample_pixels = []
        for y in range(90, 106):
            for x in range(232, 248):
                pixel = tileset.getpixel((x, y))
                if pixel[3] > 0:  # Has alpha
                    sample_pixels.append(pixel)
        
        if sample_pixels:
            avg_color = tuple(sum(p[i] for p in sample_pixels) // len(sample_pixels) for i in range(4))
            print(f"\nPixels at 'new PLAIN' coords (232,90): Average color {avg_color}")
            
            # Show this area
            new_scaled = new_plain_area.resize((new_plain_area.width * 6, new_plain_area.height * 6), Image.NEAREST)
            vis.paste(new_scaled, (700, 50))
            draw.text((700, 30), "Area at (232,90):", fill=(255, 255, 0))
        else:
            print("\nNo content found at (232,90)")
    
    vis.save("tile_size_verification.png")
    print("\nCreated tile_size_verification.png")
    
    # Create a summary JSON
    tile_sizes = {
        "tileset_info": {
            "filename": "Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png",
            "dimensions": {"width": tileset.width, "height": tileset.height}
        },
        "tile_categories": {
            "roads": {
                "tile_size": {"width": 8, "height": 8},
                "grid_spacing": 9,
                "separator_width": 1,
                "location": "Top left of tileset",
                "example_coord": {"x": 0, "y": 0}
            },
            "water_edges_beaches": {
                "tile_size": {"width": 8, "height": 8},
                "grid_spacing": 9,
                "separator_width": 1,
                "location": "Left column with pink borders",
                "example_coord": {"x": 42, "y": 142},
                "note": "Pink borders are only on first column of each section"
            },
            "buildings": {
                "tile_size": {"width": 8, "height": 16},
                "grid_spacing": "varies",
                "location": "Bottom center with pink backgrounds",
                "example_coord": {"x": 481, "y": 330},
                "note": "Pink background should be transparent"
            },
            "pipes": {
                "tile_size": {"width": 15, "height": 15},
                "grid_spacing": 17,
                "separator_width": 2,
                "location": "Middle section",
                "example_coord": {"x": 167, "y": 166}
            },
            "terrain": {
                "tile_size": {"width": 16, "height": 16},
                "grid_spacing": 17,
                "separator_width": 1,
                "location": "Right side of tileset",
                "example_coord": {"x": 238, "y": 18},
                "verified_tiles": {
                    "PLAIN": {"x": 238, "y": 18},
                    "WOOD": {"x": 238, "y": 35},
                    "MOUNTAIN": {"x": 255, "y": 18}
                }
            }
        },
        "notes": [
            "The tileset contains mixed tile sizes",
            "Most tiles use grey separators between them",
            "Pink/magenta areas should be made transparent",
            "The game engine expects 16x16 tiles, so conversion may be needed"
        ]
    }
    
    with open("tile_sizes_summary.json", "w") as f:
        json.dump(tile_sizes, f, indent=2)
    
    print("Created tile_sizes_summary.json")

if __name__ == "__main__":
    verify_tile_sizes()
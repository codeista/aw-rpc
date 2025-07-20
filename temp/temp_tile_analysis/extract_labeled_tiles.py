#!/usr/bin/env python3
"""
Extract tiles based on the visible labels in the AW2 tileset
"""

from PIL import Image, ImageDraw
import os
import json

def extract_labeled_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    
    if not os.path.exists(tileset_path):
        print(f"Error: Tileset not found at {tileset_path}")
        return
    
    tileset = Image.open(tileset_path).convert('RGBA')
    width, height = tileset.size
    print(f"Tileset size: {width}x{height}")
    
    # Based on the visible labels, let's map the tile regions
    # The tileset uses 8x8 tiles with 1px separators (9px grid)
    
    tile_regions = {
        "Road": {
            "label_pos": (14, 11),
            "tiles_start": (0, 27),  # Approximate start of road tiles
            "description": "Road tiles section"
        },
        "Pipe": {
            "label_pos": (167, 11),
            "tiles_start": (162, 27),
            "description": "Pipe tiles section"
        },
        "Grass/Plains": {
            "label_pos": (218, 11),
            "tiles_start": (216, 27),
            "tiles_area": (216, 27, 280, 90),
            "description": "Grass, Mountains, Trees & Shadows tiles"
        },
        "Water": {
            "label_pos": (14, 123),
            "tiles_start": (0, 140),
            "description": "Water, Edges, Beaches tiles"
        },
        "Rivers": {
            "label_pos": (316, 123),
            "tiles_start": (306, 140),
            "description": "River tiles"
        }
    }
    
    # Let's focus on finding grass/plain tiles
    print("\nLooking for grass/plain tiles in the labeled area...")
    
    # The grass section appears to be around x=216-280, y=27-90
    # Using the 9px grid pattern
    grass_tiles = []
    
    # Create visualization
    vis = tileset.copy()
    draw = ImageDraw.Draw(vis)
    
    # Mark the grass area
    grass_area = (216, 27, 280, 90)
    draw.rectangle(grass_area, outline=(0, 255, 0), width=2)
    draw.text((grass_area[0], grass_area[1] - 15), "GRASS/PLAINS", fill=(0, 255, 0))
    
    # Extract grass tiles using 9px grid
    grid_step = 9
    tile_size = 8
    
    print(f"\nExtracting grass tiles from area {grass_area}:")
    
    for y in range(grass_area[1], grass_area[3], grid_step):
        for x in range(grass_area[0], grass_area[2], grid_step):
            if x + tile_size <= width and y + tile_size <= height:
                # Extract tile
                tile = tileset.crop((x, y, x + tile_size, y + tile_size))
                
                # Check if it looks like grass (greenish)
                pixels = list(tile.getdata())
                green_count = 0
                for pixel in pixels:
                    if len(pixel) >= 3:
                        r, g, b = pixel[:3]
                        if g > r and g > b and g > 80:  # Green dominant
                            green_count += 1
                
                if green_count > len(pixels) * 0.3:  # At least 30% green
                    grass_tiles.append((x, y))
                    draw.rectangle([x, y, x + tile_size - 1, y + tile_size - 1], 
                                 outline=(0, 255, 0), width=1)
    
    print(f"Found {len(grass_tiles)} grass tiles")
    
    # Save visualization
    vis.save("labeled_grass_tiles.png")
    
    # Create a showcase of grass tiles
    if grass_tiles:
        showcase = Image.new('RGBA', (400, 300), (40, 40, 40, 255))
        showcase_draw = ImageDraw.Draw(showcase)
        
        showcase_draw.text((10, 10), "GRASS/PLAIN TILES FROM LABELED SECTION", fill=(255, 255, 255))
        
        for i, (tx, ty) in enumerate(grass_tiles[:20]):  # Show first 20
            if i >= 20:
                break
            
            # Position in showcase
            col = i % 5
            row = i // 5
            sx = 20 + col * 70
            sy = 40 + row * 70
            
            # Extract and paste tile
            tile = tileset.crop((tx, ty, tx + tile_size, ty + tile_size))
            
            # Scale up for visibility
            tile_scaled = tile.resize((48, 48), Image.NEAREST)
            showcase.paste(tile_scaled, (sx, sy))
            
            # Add border
            showcase_draw.rectangle([sx-1, sy-1, sx+48, sy+48], outline=(200, 200, 200), width=1)
            
            # Add coordinates
            showcase_draw.text((sx, sy + 52), f"({tx},{ty})", fill=(150, 150, 150), anchor="lt")
        
        showcase.save("grass_tiles_showcase.png")
        
        # Also check other tile types
        print("\n\nChecking other labeled sections:")
        
        # Water tiles
        water_area = (0, 140, 100, 200)
        water_count = 0
        for y in range(water_area[1], water_area[3], grid_step):
            for x in range(water_area[0], water_area[2], grid_step):
                if x + tile_size <= width and y + tile_size <= height:
                    tile = tileset.crop((x, y, x + tile_size, y + tile_size))
                    pixels = list(tile.getdata())
                    blue_count = sum(1 for p in pixels if len(p) >= 3 and p[2] > p[0] and p[2] > p[1])
                    if blue_count > len(pixels) * 0.3:
                        water_count += 1
                        if water_count == 1:  # Save first water tile position
                            print(f"  First water tile at: ({x}, {y})")
        
        print(f"  Found {water_count} water tiles in water section")
        
        # Find a good plain tile for comparison
        if grass_tiles:
            print(f"\n✅ Recommended plain/grass tile position: {grass_tiles[0]}")
            
            # Update the mapping file
            mapping = {
                "metadata": {
                    "source": tileset_path,
                    "base_tile_size": 8,
                    "grid_step": 9,
                    "created": "2025-07-18T03:30:00.000Z"
                },
                "tiles": {
                    "plain": {
                        "x": grass_tiles[0][0],
                        "y": grass_tiles[0][1],
                        "width": 8,
                        "height": 8,
                        "category": "terrain",
                        "section": "Grass/Plains"
                    }
                }
            }
            
            with open("corrected_tile_mapping.json", "w") as f:
                json.dump(mapping, f, indent=2)
            
            print(f"\nSaved corrected mapping to corrected_tile_mapping.json")

if __name__ == "__main__":
    extract_labeled_tiles()
#!/usr/bin/env python3
"""
Extract all tiles from the AW2 tileset that are separated by blue lines
The pattern is 8x8 tiles with 1-pixel blue separators (9x9 grid)
"""

from PIL import Image, ImageDraw
import os
import json

def extract_tiles_from_grid():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    
    if not os.path.exists(tileset_path):
        print(f"Error: Tileset not found at {tileset_path}")
        return
    
    tileset = Image.open(tileset_path).convert('RGBA')
    width, height = tileset.size
    print(f"Tileset size: {width}x{height}")
    
    # The pattern is 8x8 tiles with 1-pixel separators
    # So the grid step is 9 pixels
    tile_size = 8
    grid_step = 9
    
    # Create output directory
    os.makedirs("extracted_tiles", exist_ok=True)
    
    # Extract tiles
    tiles = []
    tile_count = 0
    
    # Start from the grid origin
    # Based on the pattern, tiles seem to start at positions aligned to the 9-pixel grid
    start_x = 0
    start_y = 0
    
    # Create a visualization of the entire tileset with grid
    vis = tileset.copy()
    draw = ImageDraw.Draw(vis)
    
    print(f"\nExtracting {tile_size}x{tile_size} tiles with {grid_step-tile_size}px separators:")
    
    for y in range(start_y, height - tile_size, grid_step):
        for x in range(start_x, width - tile_size, grid_step):
            # Extract the tile
            tile = tileset.crop((x, y, x + tile_size, y + tile_size))
            
            # Check if this is a valid tile (not entirely blue/separator)
            pixels = list(tile.getdata())
            
            # Count blue pixels
            blue_pixels = 0
            total_alpha = 0
            for pixel in pixels:
                if len(pixel) >= 3:
                    r, g, b = pixel[:3]
                    a = pixel[3] if len(pixel) > 3 else 255
                    total_alpha += a
                    # Check for blue separator color
                    if b > 150 and r < 100 and g < 150:
                        blue_pixels += 1
            
            # Skip if mostly blue or transparent
            avg_alpha = total_alpha / len(pixels)
            if blue_pixels < len(pixels) * 0.8 and avg_alpha > 50:
                # This looks like a valid tile
                tile_info = {
                    'id': tile_count,
                    'x': x,
                    'y': y,
                    'width': tile_size,
                    'height': tile_size,
                    'grid_x': x // grid_step,
                    'grid_y': y // grid_step
                }
                tiles.append(tile_info)
                
                # Save the tile
                tile_scaled = tile.resize((32, 32), Image.NEAREST)  # Scale to 32x32 for visibility
                tile_scaled.save(f"extracted_tiles/tile_{tile_count:04d}_at_{x}_{y}.png")
                
                # Draw rectangle on visualization
                draw.rectangle([x, y, x + tile_size - 1, y + tile_size - 1], 
                             outline=(255, 0, 0), width=1)
                
                # Show info for tiles in the area where user was looking
                if 120 <= x <= 140 and 0 <= y <= 20:
                    print(f"  Tile {tile_count}: ({x}, {y}) - Grid position ({tile_info['grid_x']}, {tile_info['grid_y']})")
                
                tile_count += 1
    
    print(f"\nExtracted {tile_count} tiles")
    
    # Save the visualization
    vis.save("tileset_with_extracted_tiles.png")
    
    # Save tile data
    with open("extracted_tiles_data.json", "w") as f:
        json.dump({
            'tileset': tileset_path,
            'tile_size': tile_size,
            'grid_step': grid_step,
            'total_tiles': tile_count,
            'tiles': tiles
        }, f, indent=2)
    
    # Create a showcase of tiles around (129, 10)
    print("\n\nTiles near position (129, 10):")
    showcase = Image.new('RGBA', (400, 200), (50, 50, 50, 255))
    showcase_draw = ImageDraw.Draw(showcase)
    
    showcase_tiles = []
    for tile_info in tiles:
        # Check if tile is near (129, 10)
        if abs(tile_info['x'] - 129) <= 20 and abs(tile_info['y'] - 10) <= 20:
            showcase_tiles.append(tile_info)
    
    # Sort by distance from (129, 10)
    showcase_tiles.sort(key=lambda t: abs(t['x'] - 129) + abs(t['y'] - 10))
    
    # Display first 12 tiles
    for i, tile_info in enumerate(showcase_tiles[:12]):
        if i >= 12:
            break
            
        # Position in showcase
        col = i % 6
        row = i // 6
        sx = 10 + col * 65
        sy = 10 + row * 90
        
        # Extract and paste tile
        tile = tileset.crop((tile_info['x'], tile_info['y'], 
                           tile_info['x'] + tile_size, 
                           tile_info['y'] + tile_size))
        tile_scaled = tile.resize((48, 48), Image.NEAREST)
        showcase.paste(tile_scaled, (sx, sy))
        
        # Add border
        showcase_draw.rectangle([sx-1, sy-1, sx+48, sy+48], outline=(200, 200, 200), width=1)
        
        # Add label
        label = f"({tile_info['x']}, {tile_info['y']})"
        showcase_draw.text((sx, sy + 52), label, fill=(255, 255, 255))
        
        # Highlight the one at (129, 10) or closest to it
        if tile_info['x'] == 129 and tile_info['y'] == 10:
            showcase_draw.rectangle([sx-2, sy-2, sx+49, sy+49], outline=(255, 255, 0), width=2)
            showcase_draw.text((sx, sy + 65), "YOUR TILE", fill=(255, 255, 0))
        
        print(f"  {i+1}. Position ({tile_info['x']}, {tile_info['y']}) - Distance: {abs(tile_info['x'] - 129) + abs(tile_info['y'] - 10)}")
    
    showcase.save("tiles_near_129_10_showcase.png")
    
    print("\n\nCreated files:")
    print("- extracted_tiles/: Directory with all extracted tiles")
    print("- tileset_with_extracted_tiles.png: Visualization of extraction")
    print("- extracted_tiles_data.json: Data about all extracted tiles")
    print("- tiles_near_129_10_showcase.png: Tiles near your selected position")

if __name__ == "__main__":
    extract_tiles_from_grid()
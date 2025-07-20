#!/usr/bin/env python3
"""
Extract terrain tiles from the visible area we can see
"""

from PIL import Image
import os

def extract_visible_terrain_grid():
    """Extract terrain from the visible area systematically"""
    
    tileset = Image.open("/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png")
    
    print("=== EXTRACTING TERRAIN FROM VISIBLE GRID ===\n")
    
    os.makedirs("temp/terrain_grid", exist_ok=True)
    
    # Based on the visible area, I can see the pattern:
    # Start at (8, 64) for first terrain tile
    # The spacing appears to be 17 pixels horizontally 
    
    start_x = 8
    start_y = 64
    
    terrain_types = [
        # Row 1 (y=64): Plains and roads
        ["PLAIN", "PLAIN_var", "ROAD_HORT", "ROAD_VERT", "ROAD_CORNER"],
        # Row 2 (y=79): More plains and road variants
        ["PLAIN_var2", "PLAIN_var3", "ROAD_var", "ROAD_var2", "ROAD_var3"],
    ]
    
    extracted_terrain = []
    
    for row_idx, row_types in enumerate(terrain_types):
        y = start_y + row_idx * 15  # 15 pixel vertical spacing
        
        for col_idx, terrain_name in enumerate(row_types):
            x = start_x + col_idx * 17  # 17 pixel horizontal spacing (16 + 1 gap)
            
            if x + 16 <= tileset.width and y + 16 <= tileset.height:
                print(f"Extracting {terrain_name} at ({x}, {y})")
                
                tile = tileset.crop((x, y, x + 16, y + 16))
                
                if tile.getbbox():
                    filename = f"temp/terrain_grid/{terrain_name}_{x}_{y}.png"
                    tile.save(filename)
                    
                    extracted_terrain.append({
                        "name": terrain_name,
                        "x": x,
                        "y": y,
                        "filename": filename
                    })
                    
                    print(f"  ✓ Saved as {filename}")
                else:
                    print(f"  ✗ Empty tile")
    
    # Also extract from other visible rows in the image
    print(f"\nExtracting additional visible tiles...")
    
    # I can see there are more rows below - let's extract systematically
    for row in range(6):  # Extract 6 rows worth
        y = start_y + row * 15
        
        for col in range(8):  # Extract 8 columns worth  
            x = start_x + col * 17
            
            if x + 16 <= tileset.width and y + 16 <= tileset.height:
                tile = tileset.crop((x, y, x + 16, y + 16))
                
                if tile.getbbox():
                    filename = f"temp/terrain_grid/tile_r{row}_c{col}_{x}_{y}.png"
                    tile.save(filename)
    
    print(f"\nExtracted {len(extracted_terrain)} labeled terrain tiles")
    print(f"Plus systematic grid saved to temp/terrain_grid/")
    
    return extracted_terrain

def identify_terrain_types():
    """Try to identify terrain types from the extracted tiles"""
    
    print(f"\n=== IDENTIFYING TERRAIN TYPES ===")
    print(f"Check temp/terrain_grid/ and manually identify:")
    print(f"  - Green tiles = PLAIN variants")
    print(f"  - Grey tiles = ROAD variants") 
    print(f"  - Brown/dark = MOUNTAIN/WOOD")
    print(f"  - Blue = SEA/WATER")
    print(f"  - Buildings = CITY/FACTORY/HQ")

def main():
    extracted = extract_visible_terrain_grid()
    identify_terrain_types()
    
    print(f"\n✅ TERRAIN EXTRACTION COMPLETE")
    print(f"Next: Manually identify the key terrain types from temp/terrain_grid/")
    print(f"Then we can create proper labeled batches for upscaling")

if __name__ == "__main__":
    main()
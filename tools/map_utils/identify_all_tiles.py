#!/usr/bin/env python3
"""
Systematically identify all tiles in the new AW2 RGB tileset
Using the text labels as guides
"""

from PIL import Image, ImageDraw, ImageFont
import os
import json

def identify_all_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    
    if not os.path.exists(tileset_path):
        print(f"Error: Tileset not found at {tileset_path}")
        return
    
    tileset = Image.open(tileset_path).convert('RGBA')
    width, height = tileset.size
    print(f"Tileset size: {width}x{height}")
    print("Grid: 8x8 tiles with 1px separators (9px grid)")
    
    # Based on the visual inspection of the tileset, here are the labeled sections:
    # We saw these labels in the tileset overview
    sections = {
        "Road": {
            "start": (0, 27),
            "description": "Road tiles - various directions and intersections"
        },
        "Pipe": {
            "start": (162, 27),
            "description": "Pipe tiles"
        },
        "Grass_Mountains_Trees": {
            "start": (216, 27),
            "description": "Grass, Mountains, Trees & Shadows, Volcano"
        },
        "Water_Edges_Beaches": {
            "start": (0, 140),
            "description": "Water, Edges, Beaches"
        },
        "Rivers": {
            "start": (306, 140),
            "description": "River tiles"
        },
        "Buildings": {
            "start": (486, 0),
            "description": "Cities, Factories, Airports, etc"
        },
        "Fog": {
            "start": (486, 270),
            "description": "Fog tiles"
        }
    }
    
    # Create a visual map of all sections
    overview = tileset.copy()
    draw = ImageDraw.Draw(overview)
    
    # Draw section boundaries
    for section_name, section_info in sections.items():
        x, y = section_info["start"]
        # Draw a colored rectangle around the section start
        color = {
            "Road": (255, 0, 0),
            "Pipe": (128, 0, 255),
            "Grass_Mountains_Trees": (0, 255, 0),
            "Water_Edges_Beaches": (0, 128, 255),
            "Rivers": (0, 200, 255),
            "Buildings": (255, 128, 0),
            "Fog": (128, 128, 128)
        }.get(section_name, (255, 255, 255))
        
        draw.rectangle([x-2, y-2, x+50, y+50], outline=color, width=2)
        # Add label
        draw.rectangle([x-2, y-12, x+80, y-2], fill=color)
        draw.text((x, y-12), section_name, fill=(255, 255, 255))
    
    overview.save("tileset_sections_overview.png")
    
    # Now let's extract tiles from each section
    tile_mapping = {
        "metadata": {
            "source": tileset_path,
            "tile_size": 8,
            "grid_step": 9,
            "render_size": 16,
            "sections": sections
        },
        "tiles": {}
    }
    
    # Extract sample tiles from each section
    print("\nExtracting tiles from each section:")
    
    for section_name, section_info in sections.items():
        print(f"\n{section_name}:")
        start_x, start_y = section_info["start"]
        
        # Create a showcase for this section
        showcase = Image.new('RGBA', (600, 400), (40, 40, 40, 255))
        showcase_draw = ImageDraw.Draw(showcase)
        showcase_draw.text((10, 10), f"{section_name.upper()} TILES", fill=(255, 255, 255))
        showcase_draw.text((10, 30), section_info["description"], fill=(150, 150, 150))
        
        # Extract tiles in a grid pattern from this section
        tiles_found = 0
        for row in range(5):  # 5 rows
            for col in range(10):  # 10 columns
                x = start_x + col * 9
                y = start_y + row * 9
                
                if x + 8 <= width and y + 8 <= height:
                    # Extract tile
                    tile = tileset.crop((x, y, x + 8, y + 8))
                    
                    # Check if it's not empty/separator
                    pixels = list(tile.getdata())
                    non_transparent = sum(1 for p in pixels if len(p) > 3 and p[3] > 0)
                    
                    if non_transparent > 32:  # More than half the pixels are visible
                        # Add to showcase
                        sx = 20 + (tiles_found % 10) * 55
                        sy = 60 + (tiles_found // 10) * 65
                        
                        tile_scaled = tile.resize((48, 48), Image.NEAREST)
                        showcase.paste(tile_scaled, (sx, sy))
                        showcase_draw.rectangle([sx-1, sy-1, sx+48, sy+48], outline=(200, 200, 200))
                        showcase_draw.text((sx, sy+50), f"{col},{row}", fill=(150, 150, 150))
                        
                        # Add to mapping with temporary names
                        tile_key = f"{section_name.lower()}_{col}_{row}"
                        tile_mapping["tiles"][tile_key] = {
                            "x": x,
                            "y": y,
                            "section": section_name,
                            "grid_pos": (col, row)
                        }
                        
                        tiles_found += 1
                        if tiles_found >= 30:
                            break
            if tiles_found >= 30:
                break
        
        showcase.save(f"section_{section_name.lower()}_tiles.png")
        print(f"  Found {tiles_found} tiles, saved to section_{section_name.lower()}_tiles.png")
    
    # Save the mapping
    with open("new_tileset_full_mapping.json", "w") as f:
        json.dump(tile_mapping, f, indent=2)
    
    print("\n\nCreated files:")
    print("- tileset_sections_overview.png: Overview with section labels")
    print("- section_*_tiles.png: Sample tiles from each section")
    print("- new_tileset_full_mapping.json: Complete tile mapping data")
    
    # Create a quick reference guide
    print("\n\nQUICK REFERENCE:")
    print("- Road tiles: Start at (0, 27)")
    print("- Pipe tiles: Start at (162, 27)")
    print("- Terrain (grass/mountains/trees): Start at (216, 27)")
    print("- Water/beaches: Start at (0, 140)")
    print("- Rivers: Start at (306, 140)")
    print("- Buildings: Start at (486, 0)")
    print("- Fog: Start at (486, 270)")

if __name__ == "__main__":
    identify_all_tiles()
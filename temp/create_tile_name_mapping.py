#!/usr/bin/env python3
"""
Create a proper mapping with actual tile names based on visual identification
"""

import json
from PIL import Image, ImageDraw
import os

def create_tile_name_mapping():
    # Based on visual inspection of the tileset sections
    # Using the 9px grid (8x8 tiles + 1px separator)
    
    tile_mapping = {
        "metadata": {
            "source": "Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png",
            "tile_size": 8,
            "grid_step": 9,
            "render_size": 16,
            "description": "Complete tile mapping for AW2 RGB tileset"
        },
        "tiles": {
            # TERRAIN TILES (from Grass_Mountains_Trees section starting at 216, 27)
            "PLAIN": {
                "x": 216,  # First tile in terrain section - tan/beige
                "y": 27,
                "description": "Plain/field tile (tan/yellowish)"
            },
            "WOOD": {
                "x": 225,  # Green forest tile
                "y": 27,
                "description": "Forest/woods tile"
            },
            "MOUNTAIN": {
                "x": 252,  # Mountain tiles appear later in the row
                "y": 27,
                "description": "Mountain tile"
            },
            
            # ROAD TILES (from Road section starting at 0, 27)
            "ROAD_HORT": {
                "x": 27,  # Horizontal road
                "y": 27,
                "description": "Horizontal road"
            },
            "ROAD_VERT": {
                "x": 27,  # Vertical road
                "y": 36,
                "description": "Vertical road"
            },
            "ROAD_NE": {
                "x": 0,
                "y": 27,
                "description": "Road corner NE"
            },
            "ROAD_NW": {
                "x": 9,
                "y": 27,
                "description": "Road corner NW"
            },
            "ROAD_SE": {
                "x": 0,
                "y": 36,
                "description": "Road corner SE"
            },
            "ROAD_SW": {
                "x": 9,
                "y": 36,
                "description": "Road corner SW"
            },
            
            # WATER TILES (from Water_Edges_Beaches section starting at 0, 140)
            "SEA": {
                "x": 0,
                "y": 149,  # Skip the label row
                "description": "Ocean/sea tile"
            },
            "REEF": {
                "x": 81,  # Reef tiles are usually after basic water
                "y": 149,
                "description": "Reef tile"
            },
            "SHOAL": {
                "x": 90,  # Beach/shoal tiles
                "y": 149,
                "description": "Shoal/beach tile"
            },
            
            # RIVER TILES (from Rivers section starting at 306, 140)
            "RIVER": {
                "x": 315,  # Basic river tile
                "y": 149,
                "description": "River tile"
            },
            
            # BUILDING TILES (from Buildings section starting at 486, 0)
            # These are organized by army (red, blue, yellow, green)
            "CITY": {
                "x": 495,  # Neutral city
                "y": 81,
                "description": "Neutral city",
                "variants": {
                    "RED": {"x": 495, "y": 9},
                    "BLUE": {"x": 495, "y": 27},
                    "YELLOW": {"x": 495, "y": 45},
                    "GREEN": {"x": 495, "y": 63}
                }
            },
            "FACTORY": {
                "x": 504,  # Neutral factory
                "y": 81,
                "description": "Neutral factory",
                "variants": {
                    "RED": {"x": 504, "y": 9},
                    "BLUE": {"x": 504, "y": 27},
                    "YELLOW": {"x": 504, "y": 45},
                    "GREEN": {"x": 504, "y": 63}
                }
            },
            "AIRPORT": {
                "x": 513,  # Neutral airport
                "y": 81,
                "description": "Neutral airport",
                "variants": {
                    "RED": {"x": 513, "y": 9},
                    "BLUE": {"x": 513, "y": 27},
                    "YELLOW": {"x": 513, "y": 45},
                    "GREEN": {"x": 513, "y": 63}
                }
            },
            "PORT": {
                "x": 522,  # Neutral port
                "y": 81,
                "description": "Neutral port",
                "variants": {
                    "RED": {"x": 522, "y": 9},
                    "BLUE": {"x": 522, "y": 27},
                    "YELLOW": {"x": 522, "y": 45},
                    "GREEN": {"x": 522, "y": 63}
                }
            },
            "HQ": {
                "x": 531,  # HQ tiles
                "y": 9,
                "description": "Headquarters",
                "variants": {
                    "RED": {"x": 531, "y": 9},
                    "BLUE": {"x": 531, "y": 27},
                    "YELLOW": {"x": 531, "y": 45},
                    "GREEN": {"x": 531, "y": 63}
                }
            },
            
            # PIPE TILES (from Pipe section starting at 162, 27)
            "PIPE": {
                "x": 171,
                "y": 27,
                "description": "Pipe segment"
            },
            "PIPESEAM": {
                "x": 180,
                "y": 45,
                "description": "Pipe seam (destructible)"
            }
        }
    }
    
    # Save the mapping
    with open("aw2_tile_name_mapping.json", "w") as f:
        json.dump(tile_mapping, f, indent=2)
    
    # Create a visual reference
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    if os.path.exists(tileset_path):
        tileset = Image.open(tileset_path).convert('RGBA')
        
        # Create showcase of main tiles
        showcase = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
        draw = ImageDraw.Draw(showcase)
        draw.text((10, 10), "AW2 TILESET - MAIN TILE TYPES", fill=(255, 255, 255))
        
        col = 0
        row = 0
        for tile_name, tile_info in tile_mapping["tiles"].items():
            if "variants" in tile_info:
                continue  # Skip variants for now
                
            x = tile_info["x"]
            y = tile_info["y"]
            
            # Extract tile
            tile = tileset.crop((x, y, x + 8, y + 8))
            
            # Position in showcase
            sx = 20 + (col % 8) * 90
            sy = 50 + (row // 8) * 100
            
            # Scale up
            tile_scaled = tile.resize((64, 64), Image.NEAREST)
            showcase.paste(tile_scaled, (sx, sy))
            
            # Border
            draw.rectangle([sx-1, sy-1, sx+64, sy+64], outline=(200, 200, 200))
            
            # Label
            draw.text((sx, sy + 68), tile_name, fill=(255, 255, 255))
            draw.text((sx, sy + 82), f"({x},{y})", fill=(150, 150, 150))
            
            col += 1
            if col % 8 == 0:
                row += 1
        
        showcase.save("aw2_main_tiles_reference.png")
        print("Created aw2_main_tiles_reference.png")
    
    print("Created aw2_tile_name_mapping.json")
    print("\nMain terrain tiles identified:")
    print("- PLAIN: (216, 27) - Tan/yellowish field tile")
    print("- WOOD: (225, 27) - Green forest tile")
    print("- MOUNTAIN: (252, 27) - Mountain tile")
    print("\nAnd many more - check the JSON file for complete mapping!")

if __name__ == "__main__":
    create_tile_name_mapping()
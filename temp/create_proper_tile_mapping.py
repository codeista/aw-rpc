#!/usr/bin/env python3
"""
Create a proper tile mapping accounting for different tile sizes
"""

import json
from PIL import Image, ImageDraw
import os

def create_proper_tile_mapping():
    # The AW2 tileset uses MIXED tile sizes
    tile_mapping = {
        "metadata": {
            "source": "Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png",
            "render_size": 16,  # All tiles render at 16x16 in game
            "description": "AW2 RGB tileset with mixed tile sizes"
        },
        "tiles": {
            # TERRAIN TILES - 16x16 pixels (with 1px separators = 17px grid)
            "PLAIN": {
                "x": 216,
                "y": 26,
                "width": 16,
                "height": 16,
                "description": "Plain/field tile (tan/yellowish)"
            },
            "WOOD": {
                "x": 233,  # 216 + 17 (16px + 1px separator)
                "y": 26,
                "width": 16,
                "height": 16,
                "description": "Forest/woods tile (green)"
            },
            "MOUNTAIN": {
                "x": 250,  # 233 + 17
                "y": 26,
                "width": 16,
                "height": 16,
                "description": "Mountain tile"
            },
            
            # ROAD TILES - Also 16x16 in terrain section
            "ROAD_HORT": {
                "x": 44,
                "y": 26,
                "width": 16,
                "height": 16,
                "description": "Horizontal road"
            },
            "ROAD_VERT": {
                "x": 44,
                "y": 43,  # 26 + 17
                "width": 16,
                "height": 16,
                "description": "Vertical road"
            },
            "ROAD_NE": {
                "x": 10,
                "y": 26,
                "width": 16,
                "height": 16,
                "description": "Road turn North-East"
            },
            "ROAD_SE": {
                "x": 10,
                "y": 43,
                "width": 16,
                "height": 16,
                "description": "Road turn South-East"
            },
            "ROAD_NW": {
                "x": 27,
                "y": 26,
                "width": 16,
                "height": 16,
                "description": "Road turn North-West"
            },
            "ROAD_SW": {
                "x": 27,
                "y": 43,
                "width": 16,
                "height": 16,
                "description": "Road turn South-West"
            },
            
            # WATER TILES - 8x8 pixels (with 1px separators = 9px grid)
            "SEA": {
                "x": 0,
                "y": 149,
                "width": 8,
                "height": 8,
                "description": "Ocean/sea tile"
            },
            "SHOAL": {
                "x": 90,  # Beach tiles
                "y": 149,
                "width": 8,
                "height": 8,
                "description": "Shoal/beach tile"
            },
            "REEF": {
                "x": 81,
                "y": 149,
                "width": 8,
                "height": 8,
                "description": "Reef tile"
            },
            
            # RIVER TILES - 8x8 pixels
            "RIVER": {
                "x": 315,
                "y": 149,
                "width": 8,
                "height": 8,
                "description": "River tile"
            },
            
            # BUILDING TILES - 8x8 pixels (with 1px separators = 9px grid)
            "CITY": {
                "x": 495,
                "y": 81,  # Neutral row
                "width": 8,
                "height": 8,
                "description": "Neutral city",
                "army_variants": {
                    "RED": {"x": 495, "y": 9},
                    "BLUE": {"x": 495, "y": 27},
                    "YELLOW": {"x": 495, "y": 45},
                    "GREEN": {"x": 495, "y": 63}
                }
            },
            "FACTORY": {
                "x": 504,  # 495 + 9
                "y": 81,
                "width": 8,
                "height": 8,
                "description": "Neutral factory",
                "army_variants": {
                    "RED": {"x": 504, "y": 9},
                    "BLUE": {"x": 504, "y": 27},
                    "YELLOW": {"x": 504, "y": 45},
                    "GREEN": {"x": 504, "y": 63}
                }
            },
            "AIRPORT": {
                "x": 513,  # 504 + 9
                "y": 81,
                "width": 8,
                "height": 8,
                "description": "Neutral airport",
                "army_variants": {
                    "RED": {"x": 513, "y": 9},
                    "BLUE": {"x": 513, "y": 27},
                    "YELLOW": {"x": 513, "y": 45},
                    "GREEN": {"x": 513, "y": 63}
                }
            },
            "PORT": {
                "x": 522,  # 513 + 9
                "y": 81,
                "width": 8,
                "height": 8,
                "description": "Neutral port",
                "army_variants": {
                    "RED": {"x": 522, "y": 9},
                    "BLUE": {"x": 522, "y": 27},
                    "YELLOW": {"x": 522, "y": 45},
                    "GREEN": {"x": 522, "y": 63}
                }
            },
            "HQ": {
                "x": 531,  # 522 + 9
                "y": 9,  # HQs start in RED row
                "width": 8,
                "height": 8,
                "description": "Headquarters",
                "army_variants": {
                    "RED": {"x": 531, "y": 9},
                    "BLUE": {"x": 531, "y": 27},
                    "YELLOW": {"x": 531, "y": 45},
                    "GREEN": {"x": 531, "y": 63}
                }
            },
            
            # SPECIAL LARGE TILES
            "VOLCANO": {
                "x": 360,
                "y": 26,
                "width": 48,
                "height": 48,
                "description": "Volcano (3x3 tiles)"
            }
        }
    }
    
    # Save the mapping
    with open("aw2_mixed_tile_mapping.json", "w") as f:
        json.dump(tile_mapping, f, indent=2)
    
    print("Created aw2_mixed_tile_mapping.json")
    
    # Create a visual verification
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    if os.path.exists(tileset_path):
        tileset = Image.open(tileset_path).convert('RGBA')
        
        # Create verification image
        verify = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
        draw = ImageDraw.Draw(verify)
        draw.text((10, 10), "AW2 TILE MAPPING VERIFICATION", fill=(255, 255, 255))
        draw.text((10, 30), "Showing actual tile sizes and positions", fill=(150, 150, 150))
        
        # Show some key tiles
        examples = [
            # Terrain (16x16)
            ("PLAIN", (255, 255, 150)),
            ("WOOD", (0, 255, 0)),
            ("MOUNTAIN", (150, 150, 150)),
            # Roads (16x16)
            ("ROAD_HORT", (100, 100, 100)),
            # Water (8x8)
            ("SEA", (0, 150, 255)),
            # Buildings (8x8)
            ("CITY", (255, 150, 0)),
            ("FACTORY", (255, 100, 100)),
            # Large
            ("VOLCANO", (255, 100, 0))
        ]
        
        col = 0
        row = 0
        for tile_name, color in examples:
            if tile_name not in tile_mapping["tiles"]:
                continue
                
            tile_info = tile_mapping["tiles"][tile_name]
            x = tile_info["x"]
            y = tile_info["y"]
            w = tile_info["width"]
            h = tile_info["height"]
            
            if x + w <= tileset.width and y + h <= tileset.height:
                # Extract tile
                tile = tileset.crop((x, y, x + w, y + h))
                
                # Position in verify image
                sx = 20 + col * 150
                sy = 60 + row * 150
                
                # Scale appropriately
                scale = 64 / max(w, h)  # Fit in 64x64
                scaled_w = int(w * scale)
                scaled_h = int(h * scale)
                
                tile_scaled = tile.resize((scaled_w, scaled_h), Image.NEAREST)
                verify.paste(tile_scaled, (sx, sy))
                
                # Draw border showing actual size
                draw.rectangle([sx-1, sy-1, sx+scaled_w, sy+scaled_h], outline=color, width=2)
                
                # Labels
                draw.text((sx, sy + scaled_h + 5), tile_name, fill=(255, 255, 255))
                draw.text((sx, sy + scaled_h + 20), f"{w}x{h} → 16x16", fill=color)
                draw.text((sx, sy + scaled_h + 35), f"({x}, {y})", fill=(150, 150, 150))
                
                col += 1
                if col >= 5:
                    col = 0
                    row += 1
        
        verify.save("aw2_tile_mapping_verified.png")
        print("Created aw2_tile_mapping_verified.png")
    
    print("\nKEY FINDINGS:")
    print("- Terrain tiles (plains, woods, mountains): 16x16 pixels")
    print("- Building tiles (city, factory, etc): 8x8 pixels")
    print("- Water/river tiles: 8x8 pixels")
    print("- Special tiles (volcano): 48x48 pixels")
    print("\nAll tiles need to be scaled/padded to 16x16 for game rendering!")

if __name__ == "__main__":
    create_proper_tile_mapping()
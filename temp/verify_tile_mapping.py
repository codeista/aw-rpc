#!/usr/bin/env python3
"""
Verify tile mapping by creating individual tile images for inspection
"""

from PIL import Image, ImageDraw, ImageFont
import json
import os

def verify_tile_mapping():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Load mapping
    with open("aw2_mixed_tile_mapping.json", "r") as f:
        mapping = json.load(f)
    
    # Create verification directory
    os.makedirs("tile_verification", exist_ok=True)
    
    # Create summary report
    report_lines = ["TILE MAPPING VERIFICATION REPORT", "=" * 50, ""]
    
    # Group tiles by category
    categories = {
        "Terrain": [],
        "Roads": [],
        "Pipes": [],
        "Buildings": [],
        "Water/Beach": [],
        "Rivers": [],
        "Special": []
    }
    
    # Categorize tiles
    for tile_name, tile_data in mapping["tiles"].items():
        if tile_name in ["PLAIN", "WOOD", "MOUNTAIN"]:
            categories["Terrain"].append((tile_name, tile_data))
        elif tile_name.startswith("ROAD_"):
            categories["Roads"].append((tile_name, tile_data))
        elif tile_name.startswith("PIPE_"):
            categories["Pipes"].append((tile_name, tile_data))
        elif tile_name in ["CITY", "FACTORY", "AIRPORT", "PORT", "HQ"]:
            categories["Buildings"].append((tile_name, tile_data))
        elif tile_name in ["SEA", "REEF", "SHOAL"] or tile_name.startswith("WATER_"):
            categories["Water/Beach"].append((tile_name, tile_data))
        elif tile_name.startswith("RIVER_"):
            categories["Rivers"].append((tile_name, tile_data))
        else:
            categories["Special"].append((tile_name, tile_data))
    
    # Process each category
    for category_name, tiles in categories.items():
        if not tiles:
            continue
            
        report_lines.append(f"\n{category_name} ({len(tiles)} tiles)")
        report_lines.append("-" * 40)
        
        for tile_name, tile_data in sorted(tiles):
            # Extract tile
            x, y = tile_data["x"], tile_data["y"]
            w, h = tile_data["width"], tile_data["height"]
            
            # Create individual tile image with info
            tile_img = Image.new('RGBA', (200, 150), (40, 40, 40, 255))
            draw = ImageDraw.Draw(tile_img)
            
            # Extract tile from tileset
            if x + w <= tileset.width and y + h <= tileset.height:
                tile = tileset.crop((x, y, x + w, y + h))
                
                # Scale up for visibility
                scale = min(80 / w, 80 / h)
                scaled_w = int(w * scale)
                scaled_h = int(h * scale)
                tile_scaled = tile.resize((scaled_w, scaled_h), Image.NEAREST)
                
                # Center the tile
                paste_x = (200 - scaled_w) // 2
                paste_y = 20
                
                # Draw checkerboard background
                for cy in range(paste_y, paste_y + scaled_h, 8):
                    for cx in range(paste_x, paste_x + scaled_w, 8):
                        if ((cx - paste_x) // 8 + (cy - paste_y) // 8) % 2 == 0:
                            draw.rectangle([cx, cy, cx + 8, cy + 8], fill=(60, 60, 60))
                
                # Paste tile
                tile_img.paste(tile_scaled, (paste_x, paste_y), tile_scaled if tile_scaled.mode == 'RGBA' else None)
                
                # Draw border
                draw.rectangle([paste_x - 1, paste_y - 1, paste_x + scaled_w, paste_y + scaled_h], 
                             outline=(255, 255, 255), width=1)
            else:
                draw.text((100, 50), "OUT OF BOUNDS!", fill=(255, 0, 0), anchor="mm")
            
            # Add text info
            draw.text((100, 110), tile_name, fill=(255, 255, 255), anchor="mm")
            draw.text((100, 125), f"Pos: ({x}, {y})  Size: {w}x{h}", fill=(150, 150, 150), anchor="mm")
            if tile_data.get("animation_frames"):
                draw.text((100, 140), f"{tile_data['animation_frames']} frames", fill=(100, 200, 255), anchor="mm")
            
            # Save individual tile
            filename = f"tile_verification/{tile_name.lower()}.png"
            tile_img.save(filename)
            
            # Add to report
            info = f"{tile_name:<20} ({x:3}, {y:3}) {w:2}x{h:2}"
            if tile_data.get("animation_frames"):
                info += f" [Animated: {tile_data['animation_frames']} frames]"
            if tile_data.get("army_variants"):
                info += " [Has army variants]"
            report_lines.append(info)
            
            # Check if tile is valid
            if x + w > tileset.width or y + h > tileset.height:
                report_lines.append(f"  WARNING: Tile extends beyond tileset bounds!")
    
    # Save report
    with open("tile_verification/VERIFICATION_REPORT.txt", "w") as f:
        f.write("\n".join(report_lines))
    
    # Create HTML viewer
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Tile Verification</title>
    <style>
        body {
            background: #222;
            color: #fff;
            font-family: monospace;
            padding: 20px;
        }
        .category {
            margin: 20px 0;
            border: 1px solid #444;
            padding: 10px;
            background: #333;
        }
        .tiles {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .tile {
            border: 1px solid #555;
            padding: 5px;
            text-align: center;
            background: #2a2a2a;
        }
        .tile img {
            display: block;
            margin: 0 auto;
            image-rendering: pixelated;
        }
        .tile-name {
            color: #3498db;
            font-weight: bold;
            margin-top: 5px;
        }
        h2 {
            color: #3498db;
            margin: 0 0 10px 0;
        }
    </style>
</head>
<body>
    <h1>Tile Mapping Verification</h1>
"""
    
    for category_name, tiles in categories.items():
        if not tiles:
            continue
            
        html_content += f'<div class="category">\n<h2>{category_name} ({len(tiles)} tiles)</h2>\n<div class="tiles">\n'
        
        for tile_name, _ in sorted(tiles):
            filename = f"{tile_name.lower()}.png"
            html_content += f'''<div class="tile">
    <img src="{filename}" alt="{tile_name}">
    <div class="tile-name">{tile_name}</div>
</div>
'''
        
        html_content += '</div>\n</div>\n'
    
    html_content += """
</body>
</html>"""
    
    with open("tile_verification/index.html", "w") as f:
        f.write(html_content)
    
    print(f"Created verification files in tile_verification/")
    print(f"Total tiles verified: {len(mapping['tiles'])}")
    print("\nCategories:")
    for cat, tiles in categories.items():
        if tiles:
            print(f"  {cat}: {len(tiles)} tiles")
    
    return report_lines

if __name__ == "__main__":
    verify_tile_mapping()
#!/usr/bin/env python3
"""
Generate sample images showcasing the new tileset capabilities
"""

from PIL import Image, ImageDraw, ImageFont
import json
import os
import random

def generate_showcase_samples():
    # Load tileset and mapping
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    
    if not os.path.exists(tileset_path):
        print(f"Error: Tileset not found at {tileset_path}")
        return
    
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Load mapping
    with open("aw2_mixed_tile_mapping.json", "r") as f:
        mapping = json.load(f)
    
    print("Generating showcase samples...")
    
    # 1. Create a beautiful title card
    title_card = Image.new('RGBA', (800, 400), (26, 26, 46, 255))
    draw = ImageDraw.Draw(title_card)
    
    # Add gradient effect
    for y in range(400):
        alpha = int(255 * (1 - y / 400))
        draw.rectangle([0, y, 800, y+1], fill=(52, 152, 219, alpha))
    
    # Title text
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    draw.text((400, 100), "ADVANCE WARS 2", fill=(255, 255, 255), anchor="mm", font=font_large)
    draw.text((400, 160), "RGB Tileset System", fill=(52, 152, 219), anchor="mm", font=font_medium)
    draw.text((400, 200), "Mixed Tile Sizes • Full Color • Enhanced Quality", fill=(150, 150, 150), anchor="mm")
    
    # Add some tile decorations
    tile_positions = [(100, 250), (200, 280), (300, 260), (500, 270), (600, 250), (700, 280)]
    tile_names = ['PLAIN', 'WOOD', 'MOUNTAIN', 'CITY', 'FACTORY', 'SEA']
    
    for i, (x, y) in enumerate(tile_positions):
        if i < len(tile_names) and tile_names[i] in mapping['tiles']:
            tile_data = mapping['tiles'][tile_names[i]]
            scale = 3
            tile_img = tileset.crop((tile_data['x'], tile_data['y'], 
                                   tile_data['x'] + tile_data['width'], 
                                   tile_data['y'] + tile_data['height']))
            tile_scaled = tile_img.resize((tile_data['width'] * scale, tile_data['height'] * scale), Image.NEAREST)
            title_card.paste(tile_scaled, (x, y), tile_scaled if tile_scaled.mode == 'RGBA' else None)
    
    title_card.save("showcase_title_card.png")
    print("✓ Created showcase_title_card.png")
    
    # 2. Create a side-by-side comparison
    comparison = Image.new('RGBA', (800, 600), (40, 40, 40, 255))
    comp_draw = ImageDraw.Draw(comparison)
    
    comp_draw.text((400, 30), "Tile Size Comparison", fill=(255, 255, 255), anchor="mm", font=font_medium)
    
    # Show different tile sizes
    examples = [
        ("8×8", "CITY", 100, 100, 4),
        ("16×16", "PLAIN", 300, 100, 4),
        ("48×48", "VOLCANO", 500, 100, 1.5)
    ]
    
    for label, tile_name, x, y, scale in examples:
        if tile_name in mapping['tiles']:
            tile_data = mapping['tiles'][tile_name]
            
            # Draw background
            comp_draw.rectangle([x-5, y-5, x+150, y+200], fill=(0, 0, 0, 128), outline=(52, 152, 219))
            
            # Draw tile
            tile_img = tileset.crop((tile_data['x'], tile_data['y'], 
                                   tile_data['x'] + tile_data['width'], 
                                   tile_data['y'] + tile_data['height']))
            tile_scaled = tile_img.resize((int(tile_data['width'] * scale), 
                                         int(tile_data['height'] * scale)), Image.NEAREST)
            comparison.paste(tile_scaled, (x + 75 - tile_scaled.width//2, y + 20), 
                           tile_scaled if tile_scaled.mode == 'RGBA' else None)
            
            # Labels
            comp_draw.text((x + 75, y + 120), label, fill=(255, 255, 255), anchor="mm")
            comp_draw.text((x + 75, y + 140), tile_name, fill=(52, 152, 219), anchor="mm")
            comp_draw.text((x + 75, y + 160), f"→ 16×16", fill=(150, 150, 150), anchor="mm")
    
    comparison.save("showcase_size_comparison.png")
    print("✓ Created showcase_size_comparison.png")
    
    # 3. Create a mini battle scene
    battle_scene = Image.new('RGBA', (640, 480), (180, 210, 140, 255))  # Plain background
    
    # Create a simple map layout
    map_tiles = [
        # Row 0
        ['MOUNTAIN', 'PLAIN', 'PLAIN', 'PLAIN', 'WOOD', 'WOOD', 'PLAIN', 'PLAIN', 'PLAIN', 'MOUNTAIN'],
        # Row 1
        ['PLAIN', 'PLAIN', 'ROAD_NW', 'ROAD_HORT', 'ROAD_HORT', 'ROAD_HORT', 'ROAD_NE', 'PLAIN', 'PLAIN', 'PLAIN'],
        # Row 2
        ['PLAIN', 'PLAIN', 'ROAD_VERT', 'PLAIN', 'CITY', 'PLAIN', 'ROAD_VERT', 'PLAIN', 'WOOD', 'PLAIN'],
        # Row 3
        ['HQ', 'PLAIN', 'ROAD_VERT', 'PLAIN', 'PLAIN', 'PLAIN', 'ROAD_VERT', 'PLAIN', 'PLAIN', 'HQ'],
        # Row 4
        ['PLAIN', 'FACTORY', 'ROAD_VERT', 'PLAIN', 'PLAIN', 'PLAIN', 'ROAD_VERT', 'FACTORY', 'PLAIN', 'PLAIN'],
        # Row 5
        ['PLAIN', 'PLAIN', 'ROAD_SW', 'ROAD_HORT', 'ROAD_HORT', 'ROAD_HORT', 'ROAD_SE', 'PLAIN', 'PLAIN', 'PLAIN'],
        # Row 6
        ['PLAIN', 'WOOD', 'PLAIN', 'PLAIN', 'AIRPORT', 'PLAIN', 'PLAIN', 'PLAIN', 'WOOD', 'WOOD'],
        # Row 7
        ['SEA', 'SEA', 'SHOAL', 'SHOAL', 'PORT', 'SHOAL', 'SHOAL', 'SEA', 'SEA', 'SEA'],
    ]
    
    tile_size = 64  # Display size
    
    for row_idx, row in enumerate(map_tiles):
        for col_idx, tile_name in enumerate(row):
            x = col_idx * tile_size
            y = row_idx * tile_size
            
            # For buildings, use army variants
            if tile_name in ['HQ', 'FACTORY', 'CITY', 'AIRPORT', 'PORT']:
                army = 'NEUTRAL'
                if tile_name == 'HQ':
                    army = 'RED' if col_idx < 5 else 'BLUE'
                elif tile_name == 'FACTORY':
                    army = 'RED' if col_idx < 5 else 'BLUE'
                elif col_idx < 2 or col_idx > 7:
                    army = 'RED' if col_idx < 5 else 'BLUE'
                
                if army != 'NEUTRAL' and tile_name in mapping['tiles'] and 'army_variants' in mapping['tiles'][tile_name]:
                    # Use army variant
                    tile_data = mapping['tiles'][tile_name]
                    variant = tile_data['army_variants'].get(army, {})
                    if variant:
                        draw_tile(battle_scene, tileset, variant['x'], variant['y'], 
                                tile_data['width'], tile_data['height'], x, y, tile_size)
                        continue
            
            # Draw regular tile
            if tile_name in mapping['tiles']:
                tile_data = mapping['tiles'][tile_name]
                draw_tile(battle_scene, tileset, tile_data['x'], tile_data['y'], 
                        tile_data['width'], tile_data['height'], x, y, tile_size)
    
    battle_scene.save("showcase_battle_scene.png")
    print("✓ Created showcase_battle_scene.png")
    
    # 4. Create a tile catalog page
    catalog = Image.new('RGBA', (1200, 800), (30, 30, 30, 255))
    cat_draw = ImageDraw.Draw(catalog)
    
    cat_draw.text((600, 30), "Complete Tile Catalog", fill=(255, 255, 255), anchor="mm", font=font_large)
    
    # Organize by category
    categories = {
        "Terrain": ['PLAIN', 'WOOD', 'MOUNTAIN', 'ROAD_HORT', 'ROAD_VERT', 'ROAD_NE', 'ROAD_NW', 'ROAD_SE', 'ROAD_SW'],
        "Water": ['SEA', 'SHOAL', 'REEF', 'RIVER'],
        "Buildings": ['CITY', 'FACTORY', 'AIRPORT', 'PORT', 'HQ'],
        "Special": ['VOLCANO']
    }
    
    y_offset = 100
    for category, tiles in categories.items():
        cat_draw.text((50, y_offset), category, fill=(52, 152, 219), font=font_medium)
        
        x_offset = 50
        y_offset += 40
        
        for tile_name in tiles:
            if tile_name in mapping['tiles']:
                tile_data = mapping['tiles'][tile_name]
                
                # Draw tile
                tile_img = tileset.crop((tile_data['x'], tile_data['y'], 
                                       tile_data['x'] + tile_data['width'], 
                                       tile_data['y'] + tile_data['height']))
                
                # Scale to 48x48 display size
                scale = 48 / max(tile_data['width'], tile_data['height'])
                new_w = int(tile_data['width'] * scale)
                new_h = int(tile_data['height'] * scale)
                tile_scaled = tile_img.resize((new_w, new_h), Image.NEAREST)
                
                # Background
                cat_draw.rectangle([x_offset, y_offset, x_offset + 120, y_offset + 80], 
                                 fill=(0, 0, 0, 128), outline=(52, 152, 219, 128))
                
                # Center tile
                tile_x = x_offset + 60 - new_w // 2
                tile_y = y_offset + 10
                catalog.paste(tile_scaled, (tile_x, tile_y), tile_scaled if tile_scaled.mode == 'RGBA' else None)
                
                # Label
                cat_draw.text((x_offset + 60, y_offset + 65), tile_name, 
                            fill=(255, 255, 255), anchor="mm", font=None)
                
                x_offset += 130
                if x_offset > 1000:
                    x_offset = 50
                    y_offset += 90
        
        y_offset += 100
    
    catalog.save("showcase_tile_catalog.png")
    print("✓ Created showcase_tile_catalog.png")
    
    print("\n✅ All showcase samples generated!")
    print("\nOpen create_impressive_showcase.html in a browser to see the interactive showcase!")

def draw_tile(target_img, tileset, tile_x, tile_y, tile_w, tile_h, dest_x, dest_y, dest_size):
    """Helper function to draw a tile"""
    tile = tileset.crop((tile_x, tile_y, tile_x + tile_w, tile_y + tile_h))
    
    # Scale to destination size
    scale = dest_size / max(tile_w, tile_h)
    new_w = int(tile_w * scale)
    new_h = int(tile_h * scale)
    
    # Center in destination
    offset_x = (dest_size - new_w) // 2
    offset_y = (dest_size - new_h) // 2
    
    tile_scaled = tile.resize((new_w, new_h), Image.NEAREST)
    target_img.paste(tile_scaled, (dest_x + offset_x, dest_y + offset_y), 
                    tile_scaled if tile_scaled.mode == 'RGBA' else None)

if __name__ == "__main__":
    generate_showcase_samples()
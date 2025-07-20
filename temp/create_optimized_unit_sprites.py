#!/usr/bin/env python3
"""
Create an optimized 16x16 unit sprite sheet by extracting sprites from the original
aw2_blackhole_units_map_transparent.png and organizing them in a clean grid layout
similar to units_sprite_sheet_v2.png
"""

import json
import os
from PIL import Image
from collections import defaultdict

def load_sprite_config():
    """Load the sprite corrections config to get sprite positions"""
    with open('templates/sprite_corrections_config.json', 'r') as f:
        return json.load(f)

def extract_sprites_from_original():
    """Extract 16x16 sprites from the original sprite sheet"""
    # Load the original sprite sheet
    original_sheet = Image.open('static/img/aw2_blackhole_units_map_transparent.png')
    print(f"Original sheet size: {original_sheet.size}")
    
    # Load sprite configuration
    config = load_sprite_config()
    
    # We'll organize sprites by unit type and army
    sprites = defaultdict(dict)
    
    # Extract sprites for each state from corrections
    corrections = config.get('corrections', {})
    for state in ['idle', 'unavailable']:
        if state in corrections:
            for sprite_key, coords in corrections[state].items():
                # Parse the sprite key (e.g., "INFANTRY_RED_idle_0")
                parts = sprite_key.split('_')
                if len(parts) >= 4:
                    unit_type = parts[0]
                    army = parts[1]
                    
                    # Extract the 16x16 sprite
                    x, y = coords['x'], coords['y']
                    # Ensure coordinates are within bounds
                    if x + 16 <= original_sheet.width and y + 16 <= original_sheet.height:
                        sprite = original_sheet.crop((x, y, x + 16, y + 16))
                    else:
                        print(f"Warning: Sprite {sprite_key} at ({x}, {y}) is out of bounds")
                        continue
                    
                    # Store the sprite
                    if unit_type not in sprites:
                        sprites[unit_type] = {}
                    if army not in sprites[unit_type]:
                        sprites[unit_type][army] = {}
                    sprites[unit_type][army][state] = sprite
    
    return sprites

def create_optimized_sprite_sheet(sprites):
    """Create a new sprite sheet with clean grid layout"""
    # Define the order of units and armies (matching v2 organization)
    unit_order = [
        'INFANTRY', 'MECH', 'RECON', 'TANK', 'MEDIUMTANK', 'NEOTANK', 'MEGATANK',
        'APC', 'ARTILLERY', 'ROCKET', 'ANTIAIR', 'MISSILE', 'PIPERUNNER',
        'FIGHTER', 'BOMBER', 'BCOPTER', 'TCOPTER', 'STEALTH', 'BLACKBOMB',
        'BATTLESHIP', 'CRUISER', 'LANDER', 'SUB', 'CARRIER', 'BLACKBOAT'
    ]
    
    army_order = ['RED', 'BLUE', 'GREEN', 'YELLOW', 'GREY']
    states = ['idle', 'unavailable']
    
    # Calculate dimensions - simplified layout
    # Each row: unit type, columns: army_idle, army_unavailable (no gaps)
    sprites_per_row = len(army_order) * len(states)  # 10 sprites per row
    sprite_size = 16
    padding = 0  # No padding between sprites
    
    # Count valid units
    valid_units = []
    for unit in unit_order:
        if unit in sprites:
            # Check if at least one army has this unit
            has_sprites = False
            for army in army_order:
                if army in sprites[unit] and len(sprites[unit][army]) > 0:
                    has_sprites = True
                    break
            if has_sprites:
                valid_units.append(unit)
    
    rows = len(valid_units)
    
    # Create the new sprite sheet
    sheet_width = sprites_per_row * sprite_size
    sheet_height = rows * sprite_size
    
    new_sheet = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
    
    # Create sprite map for JSON
    sprite_map = {
        "metadata": {
            "version": "1.0",
            "sprite_size": 16,
            "scale": 1,
            "sprites_per_row": sprites_per_row,
            "total_sprites": 0
        },
        "sprites": {}
    }
    
    # Place sprites in the new sheet
    total_sprites = 0
    for row, unit_type in enumerate(valid_units):
        col = 0
        for army in army_order:
            for state_idx, state in enumerate(states):
                if (army in sprites.get(unit_type, {}) and 
                    state in sprites[unit_type][army]):
                    
                    sprite = sprites[unit_type][army][state]
                    x = col * sprite_size
                    y = row * sprite_size
                    
                    # Ensure we don't go out of bounds
                    if x + sprite_size <= sheet_width and y + sprite_size <= sheet_height:
                        # Place the sprite
                        new_sheet.paste(sprite, (x, y))
                        
                        # Add to sprite map
                        sprite_key = f"{unit_type}_{army}_{state}_0"
                        sprite_map["sprites"][sprite_key] = {
                            "x": x,
                            "y": y,
                            "width": sprite_size,
                            "height": sprite_size,
                            "unit_type": unit_type,
                            "army": army,
                            "state": state,
                            "index": 0
                        }
                        total_sprites += 1
                
                col += 1
    
    sprite_map["metadata"]["total_sprites"] = total_sprites
    
    return new_sheet, sprite_map

def main():
    print("Creating optimized 16x16 unit sprite sheet...")
    
    # Extract sprites from original
    print("Extracting sprites from original sheet...")
    sprites = extract_sprites_from_original()
    
    # Debug: Show what we extracted
    print(f"Extracted units: {list(sprites.keys())}")
    for unit in list(sprites.keys())[:3]:  # Show first 3 units
        print(f"  {unit}: armies={list(sprites[unit].keys())}")
    
    # Create optimized sprite sheet
    print("Creating new sprite sheet with clean layout...")
    new_sheet, sprite_map = create_optimized_sprite_sheet(sprites)
    
    # Save the new sprite sheet
    output_path = 'static/img/units_sprite_sheet_16x16.png'
    new_sheet.save(output_path, 'PNG')
    print(f"Saved new sprite sheet to: {output_path}")
    
    # Save the sprite map
    map_path = 'static/img/units_sprite_map_16x16.json'
    with open(map_path, 'w') as f:
        json.dump(sprite_map, f, indent=2)
    print(f"Saved sprite map to: {map_path}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"- Sprite sheet size: {new_sheet.size[0]}x{new_sheet.size[1]} pixels")
    print(f"- Total sprites: {sprite_map['metadata']['total_sprites']}")
    print(f"- Sprite size: 16x16 pixels")

if __name__ == "__main__":
    main()
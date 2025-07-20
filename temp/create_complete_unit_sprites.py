#!/usr/bin/env python3
"""
Create a complete unit sprite sheet that includes both regular units and special units.
This script extracts sprites from the main sheet AND adds the individual special unit files.
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

def load_special_unit_sprites():
    """Load special unit sprites from individual files"""
    special_sprites = defaultdict(dict)
    special_dir = 'static/img/special-units'
    
    # Mapping of file names to unit types and armies
    special_files = {
        # STEALTH sprites
        'osstealth.gif': ('STEALTH', 'RED'),
        'bmstealth.gif': ('STEALTH', 'BLUE'),
        'gestealth.gif': ('STEALTH', 'GREEN'),
        'ycstealth.gif': ('STEALTH', 'YELLOW'),
        'gsstealth.gif': ('STEALTH', 'GREY'),
        
        # BLACKBOMB sprites
        'osblackbomb.gif': ('BLACKBOMB', 'RED'),
        'bmblackbomb.gif': ('BLACKBOMB', 'BLUE'),
        'geblackbomb.gif': ('BLACKBOMB', 'GREEN'),
        'ycblackbomb.gif': ('BLACKBOMB', 'YELLOW'),
        'gsblackbomb.gif': ('BLACKBOMB', 'GREY'),
        
        # MEGATANK sprites
        'osmegatank.gif': ('MEGATANK', 'RED'),
        'bmmegatank.gif': ('MEGATANK', 'BLUE'),
        'gemegatank.gif': ('MEGATANK', 'GREEN'),
        'ycmegatank.gif': ('MEGATANK', 'YELLOW'),
        'gsmegatank.gif': ('MEGATANK', 'GREY'),
        
        # CARRIER sprites
        'oscarrier.gif': ('CARRIER', 'RED'),
        'bmcarrier.gif': ('CARRIER', 'BLUE'),
        'gecarrier.gif': ('CARRIER', 'GREEN'),
        'yccarrier.gif': ('CARRIER', 'YELLOW'),
        'gscarrier.gif': ('CARRIER', 'GREY'),
        
        # BLACKBOAT sprites
        'osblackboat.gif': ('BLACKBOAT', 'RED'),
        'bmblackboat.gif': ('BLACKBOAT', 'BLUE'),
        'geblackboat.gif': ('BLACKBOAT', 'GREEN'),
        'ycblackboat.gif': ('BLACKBOAT', 'YELLOW'),
        'gsblackboat.gif': ('BLACKBOAT', 'GREY'),
        
        # PIPERUNNER sprites
        'ospiperunner.gif': ('PIPERUNNER', 'RED'),
        'bmpiperunner.gif': ('PIPERUNNER', 'BLUE'),
        'gepiperunner.gif': ('PIPERUNNER', 'GREEN'),
        'ycpiperunner.gif': ('PIPERUNNER', 'YELLOW'),
        'gspiperunner.gif': ('PIPERUNNER', 'GREY'),
    }
    
    for filename, (unit_type, army) in special_files.items():
        filepath = os.path.join(special_dir, filename)
        if os.path.exists(filepath):
            try:
                # Load the special sprite
                special_img = Image.open(filepath)
                
                # Convert to RGBA if needed
                if special_img.mode != 'RGBA':
                    special_img = special_img.convert('RGBA')
                
                # For animated GIFs, take the first frame
                if hasattr(special_img, 'is_animated') and special_img.is_animated:
                    special_img.seek(0)  # Go to first frame
                
                # Resize to 16x16 if needed
                if special_img.size != (16, 16):
                    special_img = special_img.resize((16, 16), Image.NEAREST)
                
                # Store the sprite for both idle and unavailable states
                if unit_type not in special_sprites:
                    special_sprites[unit_type] = {}
                if army not in special_sprites[unit_type]:
                    special_sprites[unit_type][army] = {}
                
                # Create idle version
                special_sprites[unit_type][army]['idle'] = special_img.copy()
                
                # Create unavailable version (darker)
                unavailable_sprite = special_img.copy()
                # Apply brightness filter to make it look unavailable
                pixels = unavailable_sprite.load()
                for i in range(unavailable_sprite.width):
                    for j in range(unavailable_sprite.height):
                        r, g, b, a = pixels[i, j]
                        # Reduce brightness and saturation
                        r = int(r * 0.4)
                        g = int(g * 0.4)
                        b = int(b * 0.4)
                        pixels[i, j] = (r, g, b, a)
                
                special_sprites[unit_type][army]['unavailable'] = unavailable_sprite
                
                print(f"Loaded special sprite: {unit_type} {army} from {filename}")
                
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
    
    return special_sprites

def merge_sprite_collections(regular_sprites, special_sprites):
    """Merge regular and special sprites"""
    merged = regular_sprites.copy()
    
    for unit_type, armies in special_sprites.items():
        if unit_type not in merged:
            merged[unit_type] = {}
        
        for army, states in armies.items():
            if army not in merged[unit_type]:
                merged[unit_type][army] = {}
            
            for state, sprite in states.items():
                merged[unit_type][army][state] = sprite
    
    return merged

def create_complete_sprite_sheet(sprites):
    """Create a complete sprite sheet with all units including special ones"""
    # Define the order of units and armies
    unit_order = [
        'INFANTRY', 'MECH', 'RECON', 'TANK', 'MEDIUMTANK', 'NEOTANK', 'MEGATANK',
        'APC', 'ARTILLERY', 'ROCKET', 'ANTIAIR', 'MISSILE', 'PIPERUNNER',
        'FIGHTER', 'BOMBER', 'BCOPTER', 'TCOPTER', 'STEALTH', 'BLACKBOMB',
        'BATTLESHIP', 'CRUISER', 'LANDER', 'SUB', 'CARRIER', 'BLACKBOAT'
    ]
    
    army_order = ['RED', 'BLUE', 'GREEN', 'YELLOW', 'GREY']
    states = ['idle', 'unavailable']
    
    # Calculate dimensions - simplified layout
    sprites_per_row = len(army_order) * len(states)  # 10 sprites per row
    sprite_size = 16
    
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
            "total_sprites": 0,
            "includes_special_units": True
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
    print("Creating complete 16x16 unit sprite sheet with special units...")
    
    # Extract sprites from original sheet
    print("Extracting sprites from original sheet...")
    regular_sprites = extract_sprites_from_original()
    
    # Load special unit sprites
    print("Loading special unit sprites...")
    special_sprites = load_special_unit_sprites()
    
    # Merge collections
    print("Merging sprite collections...")
    all_sprites = merge_sprite_collections(regular_sprites, special_sprites)
    
    # Debug: Show what we have
    print(f"Total unit types: {len(all_sprites)}")
    for unit in ['STEALTH', 'BLACKBOMB', 'MEGATANK']:
        if unit in all_sprites:
            armies = list(all_sprites[unit].keys())
            print(f"  {unit}: armies={armies}")
        else:
            print(f"  {unit}: NOT FOUND")
    
    # Create complete sprite sheet
    print("Creating complete sprite sheet...")
    new_sheet, sprite_map = create_complete_sprite_sheet(all_sprites)
    
    # Save the new sprite sheet
    output_path = 'static/img/units_sprite_sheet_complete.png'
    new_sheet.save(output_path, 'PNG')
    print(f"Saved complete sprite sheet to: {output_path}")
    
    # Save the sprite map
    map_path = 'static/img/units_sprite_map_complete.json'
    with open(map_path, 'w') as f:
        json.dump(sprite_map, f, indent=2)
    print(f"Saved sprite map to: {map_path}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"- Sprite sheet size: {new_sheet.size[0]}x{new_sheet.size[1]} pixels")
    print(f"- Total sprites: {sprite_map['metadata']['total_sprites']}")
    print(f"- Sprite size: 16x16 pixels")
    print(f"- Includes special units: {sprite_map['metadata']['includes_special_units']}")
    
    # Show special units included
    special_units_found = []
    for sprite_key in sprite_map['sprites']:
        unit_type = sprite_key.split('_')[0]
        if unit_type in ['STEALTH', 'BLACKBOMB', 'MEGATANK']:
            if unit_type not in special_units_found:
                special_units_found.append(unit_type)
    
    print(f"- Special units included: {special_units_found}")

if __name__ == "__main__":
    main()
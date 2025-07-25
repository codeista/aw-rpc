#!/usr/bin/env python3
"""
Rebuild UI spritesheet to include fuel and ammo warning icons
"""

import os
from PIL import Image
import json

def rebuild_ui_spritesheet():
    print("=== Rebuilding UI Spritesheet ===\n")
    
    ui_dir = "/home/box/Documents/aw-rpc/static/img/sprites_2x/ui"
    combined_dir = "/home/box/Documents/aw-rpc/static/img/sprites_2x/combined"
    
    # Load existing sprite map
    sprite_map_path = os.path.join(combined_dir, 'ui_spritesheet_2x_map.json')
    with open(sprite_map_path, 'r') as f:
        existing_map = json.load(f)
    
    # Load current spritesheet
    current_sheet_path = os.path.join(combined_dir, 'ui_spritesheet_2x.png')
    current_sheet = Image.open(current_sheet_path)
    
    # Current sheet is 320x64 (enough for 60 HP sprites)
    # We need to add space for warning icons
    # Let's make it 320x96 to add another row
    sprite_size = 16
    spacing = 2
    
    new_width = 320
    new_height = 96  # Add 32 pixels for warning row
    
    # Create new spritesheet
    new_sheet = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
    
    # Copy existing sprites
    new_sheet.paste(current_sheet, (0, 0))
    print(f"✅ Copied existing sprites from {current_sheet.size}")
    
    # Add warning sprites at bottom
    warning_y = 64  # Start after existing sprites
    current_x = 0
    
    # Add fuel warning
    fuel_path = os.path.join(ui_dir, 'fuel_warning_16x16.png')
    if os.path.exists(fuel_path):
        fuel_img = Image.open(fuel_path)
        new_sheet.paste(fuel_img, (current_x, warning_y))
        existing_map['fuel_warning'] = {
            'x': current_x,
            'y': warning_y,
            'w': sprite_size,
            'h': sprite_size
        }
        current_x += sprite_size + spacing
        print("✅ Added fuel_warning sprite")
    
    # Add ammo warning
    ammo_path = os.path.join(ui_dir, 'ammo_warning_16x16.png')
    if os.path.exists(ammo_path):
        ammo_img = Image.open(ammo_path)
        new_sheet.paste(ammo_img, (current_x, warning_y))
        existing_map['ammo_warning'] = {
            'x': current_x,
            'y': warning_y,
            'w': sprite_size,
            'h': sprite_size
        }
        current_x += sprite_size + spacing
        print("✅ Added ammo_warning sprite")
    
    # Add status sprites
    status_sprites = [
        ('status_available', 'status_available_16x16.png'),
        ('status_unavailable', 'hp_status_unavailable_16x16.png')
    ]
    
    for sprite_name, filename in status_sprites:
        sprite_path = os.path.join(ui_dir, filename)
        if os.path.exists(sprite_path):
            sprite_img = Image.open(sprite_path)
            new_sheet.paste(sprite_img, (current_x, warning_y))
            existing_map[sprite_name] = {
                'x': current_x,
                'y': warning_y,
                'w': sprite_size,
                'h': sprite_size
            }
            current_x += sprite_size + spacing
            print(f"✅ Added {sprite_name} sprite")
    
    # Save new spritesheet
    new_sheet.save(current_sheet_path)
    print(f"\n✅ Saved updated spritesheet to: {current_sheet_path}")
    
    # Save updated sprite map
    with open(sprite_map_path, 'w') as f:
        json.dump(existing_map, f, indent=2)
    print(f"✅ Saved updated sprite map to: {sprite_map_path}")
    
    print(f"\n📊 Summary:")
    print(f"- Total sprites: {len(existing_map)}")
    print(f"- HP sprites: {len([k for k in existing_map if k.startswith('hp_')])}")
    print(f"- Warning sprites: {len([k for k in existing_map if 'warning' in k])}")
    print(f"- Status sprites: {len([k for k in existing_map if 'status' in k])}")
    print(f"- New spritesheet size: {new_width}x{new_height}")

if __name__ == "__main__":
    rebuild_ui_spritesheet()
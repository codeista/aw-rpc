#!/usr/bin/env python3
"""
Rebuild UI spritesheet to include ALL sprites from the 5 UI files
"""

import os
from PIL import Image
import json

def rebuild_ui_spritesheet_complete():
    print("=== Rebuilding Complete UI Spritesheet ===\n")
    
    ui_dir = "/home/box/Documents/aw-rpc/static/img/sprites_2x/ui"
    combined_dir = "/home/box/Documents/aw-rpc/static/img/sprites_2x/combined"
    
    # Load the source images
    hp_numbers = Image.open(os.path.join(ui_dir, 'hp_numbers_16x16.png'))
    hp_unavailable = Image.open(os.path.join(ui_dir, 'hp_status_unavailable_16x16.png'))
    status_available = Image.open(os.path.join(ui_dir, 'status_available_16x16.png'))
    ammo_warning = Image.open(os.path.join(ui_dir, 'ammo_warning_16x16.png'))
    fuel_warning = Image.open(os.path.join(ui_dir, 'fuel_warning_16x16.png'))
    
    print(f"Source image sizes:")
    print(f"- hp_numbers: {hp_numbers.size}")
    print(f"- hp_status_unavailable: {hp_unavailable.size}")
    print(f"- status_available: {status_available.size}")
    print(f"- ammo_warning: {ammo_warning.size}")
    print(f"- fuel_warning: {fuel_warning.size}")
    
    # Calculate required size
    # hp_numbers: 10 sprites (160x16)
    # hp_unavailable: 224x80 = 14x5 grid of 16x16 sprites = 70 sprites
    # status_available: 64x80 = 4x5 grid of 16x16 sprites = 20 sprites
    # Plus 2 warning sprites
    # Total: ~102 sprites
    
    sprite_size = 16
    spacing = 2
    sprites_per_row = 20
    
    # Count actual sprites needed
    total_sprites = 10 + 70 + 20 + 2  # 102 sprites
    rows_needed = (total_sprites + sprites_per_row - 1) // sprites_per_row  # 6 rows
    
    width = sprites_per_row * (sprite_size + spacing)
    height = rows_needed * (sprite_size + spacing)
    
    print(f"\nCreating spritesheet: {width}x{height}")
    
    # Create new spritesheet
    spritesheet = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    sprite_map = {}
    
    current_x = 0
    current_y = 0
    sprite_count = 0
    
    # Helper to add sprite
    def add_sprite(name, img, src_x, src_y):
        nonlocal current_x, current_y, sprite_count
        
        # Extract 16x16 sprite
        sprite = img.crop((src_x, src_y, src_x + 16, src_y + 16))
        
        # Place on spritesheet
        spritesheet.paste(sprite, (current_x, current_y))
        
        # Add to map
        sprite_map[name] = {
            'x': current_x,
            'y': current_y,
            'w': sprite_size,
            'h': sprite_size
        }
        
        # Move to next position
        current_x += sprite_size + spacing
        if current_x >= sprites_per_row * (sprite_size + spacing):
            current_x = 0
            current_y += sprite_size + spacing
        
        sprite_count += 1
    
    # 1. Add neutral HP numbers (0-9)
    print("\nAdding neutral HP numbers...")
    for i in range(10):
        add_sprite(f'hp_{i}', hp_numbers, i * 16, 0)
    
    # 2. Add colored HP numbers from hp_status_unavailable
    # This appears to be a 14x5 grid
    print("\nAdding colored HP numbers...")
    armies = ['red', 'blue', 'green', 'yellow', 'grey']
    
    # Assuming the layout is 10 numbers per row, with each army on a row
    for army_idx, army in enumerate(armies):
        for num in range(10):
            # Skip if sprite is empty
            x = num * 16
            y = army_idx * 16
            
            # Check if position is within image
            if x < hp_unavailable.width and y < hp_unavailable.height:
                add_sprite(f'hp_{army}_{num}', hp_unavailable, x, y)
    
    # 3. Add status sprites from status_available
    print("\nAdding status sprites...")
    # This is a 4x5 grid, need to determine what each sprite is
    status_count = 0
    for y in range(5):
        for x in range(4):
            if x * 16 < status_available.width and y * 16 < status_available.height:
                add_sprite(f'status_{status_count}', status_available, x * 16, y * 16)
                status_count += 1
    
    # 4. Add warning sprites
    print("\nAdding warning sprites...")
    add_sprite('fuel_warning', fuel_warning, 0, 0)
    add_sprite('ammo_warning', ammo_warning, 0, 0)
    
    # Save spritesheet
    output_path = os.path.join(combined_dir, 'ui_spritesheet_2x_complete.png')
    spritesheet.save(output_path)
    print(f"\n✅ Saved spritesheet to: {output_path}")
    
    # Save sprite map
    map_path = os.path.join(combined_dir, 'ui_spritesheet_2x_complete_map.json')
    with open(map_path, 'w') as f:
        json.dump(sprite_map, f, indent=2)
    print(f"✅ Saved sprite map to: {map_path}")
    
    print(f"\n📊 Summary:")
    print(f"- Total sprites: {len(sprite_map)}")
    print(f"- Spritesheet size: {width}x{height}")
    print(f"- Sprites added: {sprite_count}")

if __name__ == "__main__":
    rebuild_ui_spritesheet_complete()
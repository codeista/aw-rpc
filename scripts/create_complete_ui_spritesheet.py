#!/usr/bin/env python3
"""
Create a complete UI spritesheet with all 102 sprites properly named and organized
"""

from PIL import Image
import json
import os

def create_complete_ui_spritesheet():
    print("=== Creating Complete UI Spritesheet ===\n")
    
    ui_dir = "/home/box/Documents/aw-rpc/static/img/sprites_2x/ui"
    combined_dir = "/home/box/Documents/aw-rpc/static/img/sprites_2x/combined"
    
    # Load source images
    hp_numbers = Image.open(os.path.join(ui_dir, "hp_numbers_16x16.png"))
    hp_unavailable = Image.open(os.path.join(ui_dir, "hp_status_unavailable_16x16.png"))
    status_available = Image.open(os.path.join(ui_dir, "status_available_16x16.png"))
    fuel_warning = Image.open(os.path.join(ui_dir, "fuel_warning_16x16.png"))
    ammo_warning = Image.open(os.path.join(ui_dir, "ammo_warning_16x16.png"))
    
    # Calculate spritesheet dimensions
    sprite_size = 16
    spacing = 2
    sprites_per_row = 20
    total_sprites = 102
    rows_needed = (total_sprites + sprites_per_row - 1) // sprites_per_row  # 6 rows
    
    width = sprites_per_row * (sprite_size + spacing) - spacing
    height = rows_needed * (sprite_size + spacing) - spacing
    
    print(f"Creating spritesheet: {width}x{height} for {total_sprites} sprites")
    
    # Create new spritesheet
    spritesheet = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    sprite_map = {}
    
    # Helper to calculate position and add sprite
    def add_sprite(name, img, src_x, src_y, sprite_index):
        row = sprite_index // sprites_per_row
        col = sprite_index % sprites_per_row
        
        dest_x = col * (sprite_size + spacing)
        dest_y = row * (sprite_size + spacing)
        
        # Extract sprite
        sprite = img.crop((src_x, src_y, src_x + sprite_size, src_y + sprite_size))
        
        # Place on spritesheet
        spritesheet.paste(sprite, (dest_x, dest_y))
        
        # Add to map
        sprite_map[name] = {
            'x': dest_x,
            'y': dest_y,
            'w': sprite_size,
            'h': sprite_size
        }
        
        return sprite_index + 1
    
    sprite_index = 0
    
    # 1. Add white/neutral HP numbers (10 sprites)
    print("Adding neutral HP sprites...")
    for i in range(9):
        sprite_index = add_sprite(f'hp_{i+1}', hp_numbers, i * 16, 0, sprite_index)
    sprite_index = add_sprite('hp_hidden', hp_numbers, 9 * 16, 0, sprite_index)
    
    # 2. Add colored HP numbers from hp_status_unavailable (70 sprites)
    print("Adding colored HP sprites...")
    armies = ['red', 'blue', 'green', 'yellow', 'grey']
    status_names = ['loaded', 'capturing', 'dive', 'loaded_air']
    
    for army_idx, army in enumerate(armies):
        print(f"  Adding {army} sprites...")
        y_offset = army_idx * 16
        
        # Numbers 1-9
        for i in range(9):
            sprite_index = add_sprite(f'hp_{army}_{i+1}', hp_unavailable, i * 16, y_offset, sprite_index)
        
        # Hidden (?)
        sprite_index = add_sprite(f'hp_{army}_hidden', hp_unavailable, 9 * 16, y_offset, sprite_index)
        
        # Status sprites (4 per army)
        for j, status in enumerate(status_names):
            sprite_index = add_sprite(f'hp_{army}_{status}', hp_unavailable, (10 + j) * 16, y_offset, sprite_index)
    
    # 3. Add available status sprites (20 sprites)
    print("Adding available status sprites...")
    for army_idx, army in enumerate(armies):
        y_offset = army_idx * 16
        for j, status in enumerate(status_names):
            sprite_index = add_sprite(f'status_{army}_{status}', status_available, j * 16, y_offset, sprite_index)
    
    # 4. Add warning sprites (2 sprites)
    print("Adding warning sprites...")
    sprite_index = add_sprite('fuel_warning', fuel_warning, 0, 0, sprite_index)
    sprite_index = add_sprite('ammo_warning', ammo_warning, 0, 0, sprite_index)
    
    # Save spritesheet
    output_path = os.path.join(combined_dir, 'ui_spritesheet_2x_final.png')
    spritesheet.save(output_path)
    print(f"\n✅ Saved spritesheet to: {output_path}")
    
    # Save sprite map
    map_path = os.path.join(combined_dir, 'ui_spritesheet_2x_final_map.json')
    with open(map_path, 'w') as f:
        json.dump(sprite_map, f, indent=2)
    print(f"✅ Saved sprite map to: {map_path}")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"- Total sprites: {len(sprite_map)}")
    print(f"- Neutral HP: {len([k for k in sprite_map if k.startswith('hp_') and '_' not in k[3:]])}")
    print(f"- Colored HP: {len([k for k in sprite_map if k.startswith('hp_') and '_' in k[3:]])}")
    print(f"- Status sprites: {len([k for k in sprite_map if k.startswith('status_')])}")
    print(f"- Warning sprites: {len([k for k in sprite_map if 'warning' in k])}")
    
    # List all sprite names by category
    print("\n📋 Sprite Names:")
    print("\nNeutral HP (10):")
    neutral = sorted([k for k in sprite_map if k.startswith('hp_') and '_' not in k[3:]])
    print(", ".join(neutral))
    
    for army in armies:
        army_sprites = sorted([k for k in sprite_map if f'_{army}_' in k])
        print(f"\n{army.capitalize()} sprites ({len(army_sprites)}):")
        print(", ".join(army_sprites))
    
    print("\nWarning sprites (2):")
    warnings = sorted([k for k in sprite_map if 'warning' in k])
    print(", ".join(warnings))

if __name__ == "__main__":
    create_complete_ui_spritesheet()
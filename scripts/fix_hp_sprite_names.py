#!/usr/bin/env python3
"""
Fix HP sprite names - remove hp_0 and ensure we only have hp_1 through hp_9
"""

import json

def fix_hp_sprite_names():
    print("=== Fixing HP Sprite Names ===\n")
    
    # Load current sprite map
    map_path = "/home/box/Documents/aw-rpc/static/img/sprites_2x/combined/ui_spritesheet_2x_map.json"
    with open(map_path, 'r') as f:
        sprite_map = json.load(f)
    
    # Create new map without hp_0 sprites
    new_map = {}
    removed_count = 0
    
    for name, coords in sprite_map.items():
        if name.endswith('_0') and 'hp' in name:
            # Skip hp_0 sprites
            removed_count += 1
            print(f"Removing: {name}")
        else:
            new_map[name] = coords
    
    # Save updated map
    with open(map_path, 'w') as f:
        json.dump(new_map, f, indent=2)
    
    print(f"\n✅ Removed {removed_count} hp_0 sprites")
    print(f"✅ Remaining sprites: {len(new_map)}")
    
    # Show summary
    hp_sprites = [k for k in new_map if k.startswith('hp_')]
    print(f"\nHP sprite summary:")
    print(f"- Total HP sprites: {len(hp_sprites)}")
    print(f"- Neutral HP: {len([k for k in hp_sprites if '_' not in k[3:]])}")
    print(f"- Colored HP: {len([k for k in hp_sprites if '_' in k[3:]])}")

if __name__ == "__main__":
    fix_hp_sprite_names()
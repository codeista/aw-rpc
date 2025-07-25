#!/usr/bin/env python3
"""
Restore all UI sprites with correct names
"""

import json

def restore_ui_sprites():
    print("=== Restoring UI Sprites with Correct Names ===\n")
    
    # Load current sprite map
    map_path = "/home/box/Documents/aw-rpc/static/img/sprites_2x/combined/ui_spritesheet_2x_map.json"
    with open(map_path, 'r') as f:
        sprite_map = json.load(f)
    
    # Add back the hp_0 sprites (they're digit "0", needed for display)
    hp_0_sprites = {
        "hp_0": {"x": 0, "y": 0, "w": 16, "h": 16},
        "hp_red_0": {"x": 180, "y": 0, "w": 16, "h": 16},
        "hp_blue_0": {"x": 0, "y": 18, "w": 16, "h": 16},
        "hp_green_0": {"x": 180, "y": 18, "w": 16, "h": 16},
        "hp_yellow_0": {"x": 0, "y": 36, "w": 16, "h": 16},
        "hp_grey_0": {"x": 180, "y": 36, "w": 16, "h": 16}
    }
    
    # Merge back the hp_0 sprites
    updated_map = {**sprite_map, **hp_0_sprites}
    
    # The status sprites need better names
    # Based on typical Advance Wars UI, these might be:
    # - Unit status indicators (available/done)
    # - Capture progress indicators
    # - Other UI elements
    
    # For now, let's keep them as status_0 through status_19
    # but add comments about what they might be
    
    print("Restored sprites:")
    for name in sorted(hp_0_sprites.keys()):
        print(f"  ✅ {name}")
    
    # Sort the map for better readability
    sorted_map = dict(sorted(updated_map.items()))
    
    # Save updated map
    with open(map_path, 'w') as f:
        json.dump(sorted_map, f, indent=2)
    
    print(f"\n✅ Total sprites in map: {len(sorted_map)}")
    
    # Summary by category
    hp_neutral = len([k for k in sorted_map if k.startswith('hp_') and '_' not in k[3:]])
    hp_colored = len([k for k in sorted_map if k.startswith('hp_') and '_' in k[3:]])
    status = len([k for k in sorted_map if k.startswith('status_')])
    warnings = len([k for k in sorted_map if 'warning' in k])
    
    print(f"\nSprite categories:")
    print(f"- Neutral HP digits (0-9): {hp_neutral}")
    print(f"- Colored HP digits (5 armies x 10): {hp_colored}")
    print(f"- Status sprites: {status}")
    print(f"- Warning sprites: {warnings}")
    print(f"- Total: {hp_neutral + hp_colored + status + warnings}")

if __name__ == "__main__":
    restore_ui_sprites()
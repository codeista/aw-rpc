#!/usr/bin/env python3
"""
Add entries for individual sprite files to sprite corrections config
"""

import json
from datetime import datetime

# Individual sprite mappings
# Using negative coordinates to indicate these are individual files, not sprite sheet positions
INDIVIDUAL_SPRITES = {
    "GREEN": {
        "STEALTH": {
            "y": 1525,  # Would be after TCOPTER in GREEN army
            "source": "/static/img/stealth.png"
        }
    },
    "YELLOW": {
        "STEALTH": {
            "y": 1525,  # Same relative position
            "source": "/static/img/stealth.png"
        }
    },
    "GREY": {
        "STEALTH": {
            "y": 1525,  # Same relative position
            "source": "/static/img/stealth.png"
        }
    }
}

def add_individual_sprites():
    # Load current config
    with open('templates/sprite_corrections_config.json', 'r') as f:
        config = json.load(f)
    
    # Add special marker for individual sprites
    if 'individual_sprites' not in config:
        config['individual_sprites'] = {}
    
    for army, units in INDIVIDUAL_SPRITES.items():
        for unit_type, sprite_info in units.items():
            # Add to individual sprites section
            for frame in range(3):
                # Idle sprites
                key = f"{unit_type}_{army}_idle_{frame}"
                config['individual_sprites'][key] = {
                    "source": sprite_info['source'],
                    "type": "individual"
                }
                
                # Unavailable sprites (same image for now)
                key = f"{unit_type}_{army}_unavailable_{frame}"
                config['individual_sprites'][key] = {
                    "source": sprite_info['source'],
                    "type": "individual",
                    "filter": "grayscale"  # Note: needs to be implemented
                }
            
            # Also add to regular corrections with special marker (-1 coordinates)
            for frame in range(3):
                # Idle
                key = f"{unit_type}_{army}_idle_{frame}"
                config['corrections']['idle'][key] = {
                    "x": -1,  # Special marker for individual sprite
                    "y": sprite_info['y']
                }
                
                # Unavailable
                key = f"{unit_type}_{army}_unavailable_{frame}"
                if 'unavailable' not in config['corrections']:
                    config['corrections']['unavailable'] = {}
                config['corrections']['unavailable'][key] = {
                    "x": -1,  # Special marker
                    "y": sprite_info['y']
                }
    
    # Update metadata
    config['metadata']['generated'] = datetime.now().isoformat()
    config['metadata']['version'] = "1.1"
    config['metadata']['description'] = "Advance Wars Sprite Corrections with individual sprites"
    
    # Save updated config
    with open('templates/sprite_corrections_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Added individual sprite entries for:")
    for army, units in INDIVIDUAL_SPRITES.items():
        for unit in units:
            print(f"  - {unit} ({army})")

if __name__ == "__main__":
    add_individual_sprites()
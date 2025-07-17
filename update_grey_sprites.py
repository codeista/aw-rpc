#!/usr/bin/env python3
"""
Update GREY army sprite positions to follow standard spacing
"""

import json

# Standard Y positions for GREY army (19px spacing)
GREY_Y_POSITIONS = {
    "INFANTRY": 1240,
    "MECH": 1259,
    "RECON": 1278,
    "TANK": 1297,
    "MEDIUMTANK": 1316,
    "NEOTANK": 1335,
    "APC": 1354,
    "ANTIAIR": 1373,
    "ARTILLERY": 1392,
    "ROCKET": 1411,
    "MISSILE": 1430,
    "FIGHTER": 1449,
    "BOMBER": 1468,
    "BCOPTER": 1487,
    "TCOPTER": 1506,
    "BATTLESHIP": 1525,
    "CRUISER": 1544,
    "LANDER": 1563,
    "SUB": 1582,
    "PIPERUNNER": 1601,
    # These don't exist for GREY but included for completeness
    "MEGATANK": 1335,  # Would be after NEOTANK
    "STEALTH": 1525,   # Would be after TCOPTER
    "BLACKBOMB": 1544, # Would be after STEALTH
    "CARRIER": 1601,   # Would be after SUB
    "BLACKBOAT": 1620  # Would be after CARRIER
}

def update_grey_sprites():
    # Load the current config
    with open('templates/sprite_corrections_config.json', 'r') as f:
        config = json.load(f)
    
    corrections_made = 0
    
    # Update idle sprites
    for sprite_key in list(config['corrections']['idle'].keys()):
        if '_GREY_' in sprite_key:
            unit_type = sprite_key.split('_')[0]
            if unit_type in GREY_Y_POSITIONS:
                old_y = config['corrections']['idle'][sprite_key]['y']
                new_y = GREY_Y_POSITIONS[unit_type]
                if old_y != new_y:
                    config['corrections']['idle'][sprite_key]['y'] = new_y
                    corrections_made += 1
                    print(f"Updated {sprite_key}: Y {old_y} -> {new_y}")
    
    # Update unavailable sprites
    for sprite_key in list(config['corrections']['unavailable'].keys()):
        if '_GREY_' in sprite_key:
            unit_type = sprite_key.split('_')[0]
            if unit_type in GREY_Y_POSITIONS:
                old_y = config['corrections']['unavailable'][sprite_key]['y']
                new_y = GREY_Y_POSITIONS[unit_type]
                if old_y != new_y:
                    config['corrections']['unavailable'][sprite_key]['y'] = new_y
                    corrections_made += 1
                    print(f"Updated {sprite_key}: Y {old_y} -> {new_y}")
    
    # Update metadata
    from datetime import datetime
    config['metadata']['generated'] = datetime.now().isoformat()
    config['metadata']['description'] = "Advance Wars Sprite Corrections - GREY army fixed"
    
    # Save the updated config
    with open('templates/sprite_corrections_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\nTotal corrections made: {corrections_made}")
    print("GREY army sprites updated successfully!")

if __name__ == "__main__":
    update_grey_sprites()
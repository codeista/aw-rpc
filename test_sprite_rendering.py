#!/usr/bin/env python3
"""
Test sprite rendering by checking actual sprite positions
"""

import json
from PIL import Image

# Load sprite maps
with open('static/img/sprites_2x/combined/terrain_tileset_2x_map.json', 'r') as f:
    terrain_map = json.load(f)

print("Testing sprite positions from terrain map:")
print("=" * 50)

# Check a few key sprites
test_sprites = ['PLAIN', 'SEA', 'ROAD_HORT', 'CITY', 'RED_CITY', 'BASE_TOWER_1']

for sprite_name in test_sprites:
    if sprite_name in terrain_map:
        sprite = terrain_map[sprite_name]
        print(f"\n{sprite_name}:")
        print(f"  Position: ({sprite['x']}, {sprite['y']})")
        print(f"  Size: {sprite['w']}x{sprite['h']}")
        print(f"  Center: ({sprite['x'] + sprite['w']//2}, {sprite['y'] + sprite['h']//2})")
    else:
        print(f"\n{sprite_name}: NOT FOUND")

# Check the actual image
print("\nChecking terrain tileset image...")
img = Image.open('static/img/sprites_2x/combined/terrain_tileset_2x.png')
print(f"Image size: {img.size}")
print(f"Image mode: {img.mode}")

# Test extracting a sprite
plain_sprite = terrain_map['PLAIN']
crop_box = (
    plain_sprite['x'],
    plain_sprite['y'],
    plain_sprite['x'] + plain_sprite['w'],
    plain_sprite['y'] + plain_sprite['h']
)
test_crop = img.crop(crop_box)
test_crop.save('/tmp/test_plain_sprite.png')
print(f"\nExtracted PLAIN sprite to /tmp/test_plain_sprite.png")
print(f"Crop box: {crop_box}")
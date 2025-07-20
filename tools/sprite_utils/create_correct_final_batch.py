#!/usr/bin/env python3
"""
Create final batch with correct unit sprites + correct terrain sprites
"""

import os
import zipfile
from pathlib import Path

def create_correct_final_batch():
    """Create final batch with all correct sprites"""
    
    print("=== CREATING CORRECT FINAL SPRITE BATCH ===\n")
    
    # Unit sprites (already correct)
    unit_dir = "temp/complete_sprites_to_upscale"
    unit_sprites = list(Path(unit_dir).glob("unit_*.png"))
    
    # Correct terrain sprites
    terrain_dir = "temp/terrain_grid"
    terrain_sprites = list(Path(terrain_dir).glob("*.png"))
    
    print(f"Found {len(unit_sprites)} unit sprites")
    print(f"Found {len(terrain_sprites)} terrain sprites")
    
    # Filter terrain sprites to most important ones
    important_terrain = []
    for sprite in terrain_sprites:
        name = sprite.stem.lower()
        if any(keyword in name for keyword in ['plain', 'road_hort', 'road_vert', 'road_corner']):
            important_terrain.append(sprite)
    
    print(f"Selected {len(important_terrain)} important terrain sprites")
    
    # Create test batch
    print("\nCreating corrected test batch...")
    with zipfile.ZipFile("temp/CORRECTED_test_batch.zip", 'w') as zf:
        # Add first 15 unit sprites
        for sprite in sorted(unit_sprites)[:15]:
            zf.write(sprite, f"units/{sprite.name}")
        
        # Add important terrain sprites
        for sprite in sorted(important_terrain):
            zf.write(sprite, f"terrain/{sprite.name}")
    
    print(f"✓ Corrected test batch: temp/CORRECTED_test_batch.zip")
    print(f"  - {min(15, len(unit_sprites))} unit sprites")
    print(f"  - {len(important_terrain)} terrain sprites")
    
    # Create full batch
    print("\nCreating corrected full batch...")
    with zipfile.ZipFile("temp/CORRECTED_full_batch.zip", 'w') as zf:
        # Add all unit sprites
        for sprite in sorted(unit_sprites):
            zf.write(sprite, f"units/{sprite.name}")
        
        # Add all terrain sprites (they're all small, so include them all)
        for sprite in sorted(terrain_sprites):
            zf.write(sprite, f"terrain/{sprite.name}")
    
    print(f"✓ Corrected full batch: temp/CORRECTED_full_batch.zip")
    print(f"  - {len(unit_sprites)} unit sprites")
    print(f"  - {len(terrain_sprites)} terrain sprites")
    
    # List what terrain types we have
    print(f"\n=== TERRAIN TYPES INCLUDED ===")
    terrain_types = set()
    for sprite in terrain_sprites:
        # Extract terrain type from filename
        name = sprite.stem
        if '_' in name:
            terrain_type = name.split('_')[0]
        else:
            terrain_type = name
        terrain_types.add(terrain_type)
    
    for terrain_type in sorted(terrain_types):
        print(f"  - {terrain_type}")
    
    total_sprites = len(unit_sprites) + len(terrain_sprites)
    
    print(f"\n✅ READY FOR AI UPSCALING!")
    print(f"Total sprites: {total_sprites}")
    print(f"\nUpload temp/CORRECTED_test_batch.zip to test quality first!")

def main():
    create_correct_final_batch()

if __name__ == "__main__":
    main()
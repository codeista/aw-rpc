#!/usr/bin/env python3
"""
Create final sprite batch with units + working terrain
"""

import os
import zipfile
from pathlib import Path

def create_final_batch():
    """Create final batch with all sprites ready for upscaling"""
    
    print("=== CREATING FINAL SPRITE BATCH ===\n")
    
    # Unit sprites location
    unit_dir = "temp/complete_sprites_to_upscale"
    unit_sprites = list(Path(unit_dir).glob("unit_*.png"))
    
    # Working terrain sprites location  
    terrain_dir = "temp/working_terrain"
    terrain_sprites = list(Path(terrain_dir).glob("*.png"))
    
    print(f"Found {len(unit_sprites)} unit sprites")
    print(f"Found {len(terrain_sprites)} terrain sprites")
    
    # Create test batch (small sample)
    print("\nCreating test batch...")
    with zipfile.ZipFile("temp/FINAL_test_batch.zip", 'w') as zf:
        # Add first 15 unit sprites
        for sprite in sorted(unit_sprites)[:15]:
            zf.write(sprite, f"units/{sprite.name}")
        
        # Add first 5 terrain sprites
        for sprite in sorted(terrain_sprites)[:5]:
            zf.write(sprite, f"terrain/{sprite.name}")
    
    print(f"✓ Test batch: temp/FINAL_test_batch.zip (15 units + 5 terrain)")
    
    # Create full batch
    print("\nCreating full batch...")
    with zipfile.ZipFile("temp/FINAL_full_batch.zip", 'w') as zf:
        # Add all unit sprites
        for sprite in sorted(unit_sprites):
            zf.write(sprite, f"units/{sprite.name}")
        
        # Add all terrain sprites
        for sprite in sorted(terrain_sprites):
            zf.write(sprite, f"terrain/{sprite.name}")
    
    print(f"✓ Full batch: temp/FINAL_full_batch.zip ({len(unit_sprites)} units + {len(terrain_sprites)} terrain)")
    
    # Create batch info
    total_sprites = len(unit_sprites) + len(terrain_sprites)
    
    print(f"\n=== BATCH SUMMARY ===")
    print(f"Total sprites: {total_sprites}")
    print(f"  - Unit sprites: {len(unit_sprites)} (all 16x16)")
    print(f"  - Terrain sprites: {len(terrain_sprites)} (mix of 16x16 and 16x32)")
    
    print(f"\nTerrain types included:")
    for sprite in sorted(terrain_sprites):
        name = sprite.stem  # filename without extension
        print(f"  - {name}")
    
    print(f"\n✅ READY FOR AI UPSCALING!")
    print(f"\nUpload instructions:")
    print(f"1. Upload temp/FINAL_test_batch.zip to waifu2x first")
    print(f"2. Settings: Style=Art, Noise=None, Scale=3x") 
    print(f"3. If quality is good, upload temp/FINAL_full_batch.zip")
    print(f"4. Download results to temp/upscaled_sprites/")

def main():
    create_final_batch()

if __name__ == "__main__":
    main()
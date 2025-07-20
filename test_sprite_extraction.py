#!/usr/bin/env python3
"""
Test sprite extraction functionality
"""

import os
import json
from pathlib import Path

def test_sprite_extraction():
    """Test that sprite extraction worked correctly"""
    
    print("=== SPRITE EXTRACTION TEST SUITE ===\n")
    
    # Test 1: Check extraction scripts exist
    print("1. Checking extraction scripts...")
    scripts = [
        'upscale_sprites.py',
        'create_correct_final_batch.py'
    ]
    
    all_exist = True
    for script in scripts:
        exists = os.path.exists(script)
        status = "✓" if exists else "✗"
        print(f"   {status} {script}")
        if not exists:
            all_exist = False
    
    if not all_exist:
        print("\n❌ Some scripts are missing!")
        return False
    
    # Test 2: Check extracted sprites
    print("\n2. Checking extracted sprites...")
    sprite_dirs = [
        ('Unit sprites', 'temp/complete_sprites_to_upscale', 'unit_*.png'),
        ('Terrain sprites', 'temp/terrain_grid', '*.png'),
    ]
    
    all_good = True
    for name, dir_path, pattern in sprite_dirs:
        if os.path.exists(dir_path):
            files = list(Path(dir_path).glob(pattern))
            count = len(files)
            status = "✓" if count > 0 else "✗"
            print(f"   {status} {name}: {count} files")
            if count == 0:
                all_good = False
        else:
            print(f"   ✗ {name}: directory not found")
            all_good = False
    
    # Test 3: Check batch files
    print("\n3. Checking batch files...")
    batch_files = [
        'temp/CORRECTED_test_batch.zip',
        'temp/CORRECTED_full_batch.zip'
    ]
    
    for batch in batch_files:
        exists = os.path.exists(batch)
        if exists:
            size = os.path.getsize(batch) / 1024  # KB
            status = "✓"
            print(f"   {status} {batch} ({size:.1f} KB)")
        else:
            print(f"   ✗ {batch} not found")
            all_good = False
    
    # Test 4: Check documentation
    print("\n4. Checking documentation...")
    docs = [
        'SPRITE_EXTRACTION_GUIDE.md',
        'temp/extraction_log.json'
    ]
    
    for doc in docs:
        exists = os.path.exists(doc)
        status = "✓" if exists else "✗"
        print(f"   {status} {doc}")
    
    # Test 5: Verify sprite dimensions
    print("\n5. Verifying sprite dimensions...")
    try:
        from PIL import Image
        
        # Check a few unit sprites
        unit_sprites = list(Path('temp/complete_sprites_to_upscale').glob('unit_*.png'))[:5]
        all_16x16 = True
        
        for sprite_path in unit_sprites:
            img = Image.open(sprite_path)
            if img.size != (16, 16):
                print(f"   ✗ {sprite_path.name}: {img.size} (expected 16x16)")
                all_16x16 = False
        
        if all_16x16 and unit_sprites:
            print(f"   ✓ All tested sprites are 16x16")
    except ImportError:
        print("   ⚠️  PIL not available, skipping dimension check")
    
    if all_good:
        print("\n✅ All sprite extraction tests passed!")
        print("\nNext steps:")
        print("1. Upload temp/CORRECTED_test_batch.zip to waifu2x")
        print("2. Use 2x scale, highest noise reduction")
        print("3. Download results when ready")
        return True
    else:
        print("\n❌ Some sprite extraction tests failed!")
        return False

if __name__ == "__main__":
    success = test_sprite_extraction()
    exit(0 if success else 1)
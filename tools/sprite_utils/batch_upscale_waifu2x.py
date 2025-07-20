#!/usr/bin/env python3
"""
Batch upscale sprites using waifu2x web service or local alternatives
"""

import os
import time
import zipfile
from pathlib import Path

def create_sprite_zip(input_dir, output_zip):
    """Create a ZIP of all sprites for batch upload"""
    
    print(f"Creating ZIP file from {input_dir}...")
    
    with zipfile.ZipFile(output_zip, 'w') as zf:
        for sprite in Path(input_dir).glob("*.png"):
            zf.write(sprite, sprite.name)
    
    file_size = os.path.getsize(output_zip) / (1024 * 1024)  # MB
    print(f"Created {output_zip} ({file_size:.1f} MB)")
    
    return output_zip

def prepare_for_batch_upload():
    """Prepare sprites for batch uploading"""
    
    sprite_dir = "temp/sprites_to_upscale"
    
    # Count sprites
    sprites = list(Path(sprite_dir).glob("*.png"))
    print(f"Found {len(sprites)} sprites to upscale")
    
    # Create batches if needed (some services have limits)
    batch_size = 500  # Adjust based on service limits
    
    if len(sprites) > batch_size:
        print(f"\nCreating batches of {batch_size} sprites each...")
        
        for i in range(0, len(sprites), batch_size):
            batch_sprites = sprites[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            # Create batch directory
            batch_dir = f"temp/batch_{batch_num}"
            os.makedirs(batch_dir, exist_ok=True)
            
            # Copy sprites to batch
            for sprite in batch_sprites:
                import shutil
                shutil.copy(sprite, batch_dir)
            
            # Create ZIP for this batch
            zip_name = f"temp/sprites_batch_{batch_num}.zip"
            create_sprite_zip(batch_dir, zip_name)
            
            print(f"Batch {batch_num}: {len(batch_sprites)} sprites")
    else:
        # Single ZIP for all sprites
        create_sprite_zip(sprite_dir, "temp/all_sprites.zip")
    
    print("\n✅ Files ready for upload!")
    print("\nNext steps:")
    print("1. Go to https://waifu2x.booru.pics/")
    print("2. Upload the ZIP file(s) from temp/")
    print("3. Settings: Style=Art, Noise=-1, Scale=3x")
    print("4. Download results to temp/sprites_upscaled_ai/")
    print("5. Run: python upscale_sprites.py --reassemble-only")

def alternative_local_upscale():
    """Alternative: Use ESRGAN locally if available"""
    
    print("\nAlternative: Local ESRGAN upscaling")
    print("\nTo install ESRGAN:")
    print("1. git clone https://github.com/xinntao/Real-ESRGAN.git")
    print("2. cd Real-ESRGAN")
    print("3. pip install -r requirements.txt")
    print("4. Download model: wget https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus_anime_6B.pth")
    
    print("\nThen run:")
    print("python inference_realesrgan.py -n RealESRGAN_x4plus_anime_6B -i ../temp/sprites_to_upscale -o ../temp/sprites_upscaled_ai --scale 3")

def quick_test_batch():
    """Create a small test batch for quality testing"""
    
    print("Creating test batch with 10 sprites...")
    
    test_dir = "temp/test_sprites"
    os.makedirs(test_dir, exist_ok=True)
    
    # Copy first 10 sprites
    sprites = list(Path("temp/sprites_to_upscale").glob("*.png"))[:10]
    
    for sprite in sprites:
        import shutil
        shutil.copy(sprite, test_dir)
    
    create_sprite_zip(test_dir, "temp/test_sprites.zip")
    
    print("\n✅ Test batch created!")
    print("Upload temp/test_sprites.zip to waifu2x to test quality before doing full batch")

def main():
    print("=== Waifu2x Batch Preparation ===\n")
    
    print("Options:")
    print("1. Prepare full batch ZIPs")
    print("2. Create test batch (10 sprites)")
    print("3. Show local alternatives")
    
    # For now, prepare everything
    quick_test_batch()
    print("\n" + "="*50 + "\n")
    prepare_for_batch_upload()
    print("\n" + "="*50 + "\n")
    alternative_local_upscale()

if __name__ == "__main__":
    main()
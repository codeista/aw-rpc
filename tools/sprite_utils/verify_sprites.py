#!/usr/bin/env python3
"""
Verify extracted sprites and create a visual preview
"""

from PIL import Image, ImageDraw
import os
import json
from pathlib import Path

def create_sprite_preview(sprite_dir, num_samples=100):
    """Create a preview image showing extracted sprites"""
    
    # Load sprite mapping
    with open(os.path.join(sprite_dir, "sprite_mapping.json"), "r") as f:
        sprite_info = json.load(f)
    
    print(f"Total sprites extracted: {len(sprite_info)}")
    
    # Create preview grid
    cols = 20
    rows = (min(num_samples, len(sprite_info)) + cols - 1) // cols
    preview_size = 32  # Show sprites at 2x for visibility
    
    preview = Image.new('RGBA', 
        (cols * preview_size + (cols-1) * 2, rows * preview_size + (rows-1) * 2), 
        (64, 64, 64, 255))
    
    # Draw sprites
    for i, info in enumerate(sprite_info[:num_samples]):
        sprite_path = os.path.join(sprite_dir, info["filename"])
        
        if not os.path.exists(sprite_path):
            print(f"Warning: Missing sprite {info['filename']}")
            continue
            
        sprite = Image.open(sprite_path)
        
        # Position in grid
        col = i % cols
        row = i // cols
        x = col * (preview_size + 2)
        y = row * (preview_size + 2)
        
        # Scale sprite for preview
        sprite_scaled = sprite.resize((preview_size, preview_size), Image.NEAREST)
        
        # Draw background square
        draw = ImageDraw.Draw(preview)
        draw.rectangle([x, y, x + preview_size - 1, y + preview_size - 1], 
                      fill=(32, 32, 32, 255))
        
        # Paste sprite
        preview.paste(sprite_scaled, (x, y), sprite_scaled)
    
    preview.save("temp/sprite_preview.png")
    print(f"Preview saved to temp/sprite_preview.png")
    
    return sprite_info

def verify_sprite_integrity(sprite_dir):
    """Check that sprites were extracted correctly"""
    
    issues = []
    
    # Check all sprites exist
    sprites = list(Path(sprite_dir).glob("sprite_*.png"))
    print(f"\nFound {len(sprites)} sprite files")
    
    # Check a sample
    for i, sprite_path in enumerate(sprites[:20]):
        try:
            img = Image.open(sprite_path)
            
            # Check size
            if img.size != (16, 16):
                issues.append(f"{sprite_path.name}: Wrong size {img.size}")
            
            # Check format
            if img.mode != 'RGBA':
                issues.append(f"{sprite_path.name}: Wrong mode {img.mode}")
            
            # Check if completely empty
            if img.getbbox() is None:
                issues.append(f"{sprite_path.name}: Completely transparent")
                
        except Exception as e:
            issues.append(f"{sprite_path.name}: Error - {e}")
    
    if issues:
        print("\nIssues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Sprites look good!")
    
    return len(issues) == 0

def compare_with_original():
    """Compare extracted sprites with original sheet"""
    
    original = Image.open("/home/box/Documents/aw-rpc/static/img/units_sprite_sheet_v2.png")
    print(f"\nOriginal sprite sheet: {original.width}x{original.height}")
    print(f"Expected sprites: {(original.width // 16) * (original.height // 16)}")
    
    # Check specific known sprites
    print("\nChecking known unit positions:")
    
    # Infantry at (0, 0)
    infantry_original = original.crop((0, 0, 16, 16))
    infantry_extracted = Image.open("temp/sprites_to_upscale/sprite_0000.png")
    
    if list(infantry_original.getdata()) == list(infantry_extracted.getdata()):
        print("✅ Infantry sprite matches!")
    else:
        print("❌ Infantry sprite mismatch!")
    
    # Check a few more
    test_positions = [
        (0, 0, "Infantry"),
        (16, 0, "Mech"),
        (32, 0, "Recon"),
        (0, 512, "Different army Infantry")
    ]
    
    for x, y, name in test_positions:
        sprite_num = (y // 16) * (original.width // 16) + (x // 16)
        if sprite_num < 3000:  # We only extracted 3000
            original_sprite = original.crop((x, y, x+16, y+16))
            
            sprite_file = f"temp/sprites_to_upscale/sprite_{sprite_num:04d}.png"
            if os.path.exists(sprite_file):
                extracted = Image.open(sprite_file)
                match = list(original_sprite.getdata()) == list(extracted.getdata())
                print(f"  {name} at ({x},{y}): {'✅' if match else '❌'}")

def main():
    sprite_dir = "temp/sprites_to_upscale"
    
    print("=== Sprite Verification ===\n")
    
    # Create visual preview
    sprite_info = create_sprite_preview(sprite_dir)
    
    # Verify integrity
    print("\n" + "="*50)
    integrity_ok = verify_sprite_integrity(sprite_dir)
    
    # Compare with original
    print("\n" + "="*50)
    compare_with_original()
    
    print("\n" + "="*50)
    print("\nSummary:")
    print(f"- Total sprites: {len(sprite_info)}")
    print(f"- Preview image: temp/sprite_preview.png")
    print(f"- Integrity check: {'✅ Passed' if integrity_ok else '❌ Failed'}")
    print("\nYou can view temp/sprite_preview.png to visually verify the sprites")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Analyze the tileset structure to understand tile sizes
"""

from PIL import Image, ImageDraw

def analyze_tileset():
    """Analyze the transparent tileset structure"""
    
    tileset_path = "/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png"
    img = Image.open(tileset_path)
    
    print(f"Tileset: {tileset_path}")
    print(f"Size: {img.width}x{img.height}")
    print(f"Mode: {img.mode}")
    
    # The tileset is 445x1163
    # Let's check different tile sizes
    for tile_size in [16, 32, 8]:
        print(f"\nChecking {tile_size}x{tile_size} tiles:")
        print(f"  Width tiles: {img.width // tile_size} (remainder: {img.width % tile_size})")
        print(f"  Height tiles: {img.height // tile_size} (remainder: {img.height % tile_size})")
    
    # Create a grid overlay to visualize the structure
    preview = img.convert('RGBA').resize((img.width * 2, img.height * 2), Image.NEAREST)
    draw = ImageDraw.Draw(preview)
    
    # Draw 16x16 grid
    for x in range(0, img.width * 2, 32):  # 16 * 2
        draw.line([(x, 0), (x, img.height * 2)], fill=(255, 0, 0, 128), width=1)
    for y in range(0, img.height * 2, 32):  # 16 * 2
        draw.line([(0, y), (img.width * 2, y)], fill=(255, 0, 0, 128), width=1)
    
    # Save a section with grid
    section = preview.crop((0, 0, 400, 400))
    section.save("temp/tileset_grid_analysis.png")
    
    # Extract actual usable area (might be padded)
    # Try to find the actual content bounds
    bbox = img.getbbox()
    if bbox:
        print(f"\nContent bounding box: {bbox}")
        print(f"Actual content size: {bbox[2]-bbox[0]}x{bbox[3]-bbox[1]}")
    
    # Sample some tiles at different positions
    print("\nSampling tiles at different positions:")
    test_positions = [
        (0, 0, "Top-left"),
        (16, 0, "Second tile"),
        (432, 0, "Near right edge"),
        (0, 1152, "Near bottom")
    ]
    
    for x, y, desc in test_positions:
        if x + 16 <= img.width and y + 16 <= img.height:
            tile = img.crop((x, y, x+16, y+16))
            if tile.getbbox():
                print(f"  {desc} ({x},{y}): Has content")
            else:
                print(f"  {desc} ({x},{y}): Empty")

def check_render_code():
    """Check how the game handles these tilesets"""
    
    print("\n\n=== CHECKING RENDER CODE ===")
    
    with open("/home/box/Documents/aw-rpc/static/js/render_legacy.js", "r") as f:
        content = f.read()
    
    # Look for tileset handling
    if "445" in content:
        print("Found reference to 445 (tileset width)")
    if "1163" in content:
        print("Found reference to 1163 (tileset height)")
    
    # Check for tile size assumptions
    if "TILESIZE" in content:
        print("Found TILESIZE references")

def main():
    analyze_tileset()
    check_render_code()
    
    print("\n\n=== CONCLUSION ===")
    print("The tileset is 445x1163, which means:")
    print("- It's not a perfect 16x16 grid")
    print("- There's 5 pixels of padding on the right (445 = 27*16 + 13)")
    print("- There's 11 pixels of padding on the bottom (1163 = 72*16 + 11)")
    print("\nWe should extract tiles considering this padding!")

if __name__ == "__main__":
    main()
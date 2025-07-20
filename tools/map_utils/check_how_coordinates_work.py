#!/usr/bin/env python3
"""
Check how the coordinate system actually works in the game
"""

from PIL import Image

def check_coordinate_system():
    """Understand how Two.js texture offsets work"""
    
    print("=== UNDERSTANDING TWO.JS COORDINATE SYSTEM ===\n")
    
    # From render.js:
    # spriteTexture.offset = new Two.Vector(x, y);
    # This is a TEXTURE OFFSET, not a position!
    
    # Two.js uses texture offsets to select which part of a sprite sheet to display
    # The offset is relative to the center of the texture
    
    # So when we have:
    # var x = spriteSheetWidth/2 - SPRITESIZE/2;  // 214.5
    # x = x - 8;  // 206.5
    
    # This means: "Show the part of the texture that is 8 pixels to the LEFT of center"
    
    tileset = Image.open("/home/box/Documents/aw-rpc/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png")
    print(f"Tileset size: {tileset.width}x{tileset.height}")
    print(f"Center point: ({tileset.width//2}, {tileset.height//2})")
    
    # Let's verify some tiles exist where the game expects them
    # For PLAIN: offset is (206, 509) from our calculation
    # But this is the OFFSET, not the tile position!
    
    # In Two.js, the actual tile position would be:
    # actual_x = center_x - offset_x = 222 - 206 = 16
    # actual_y = center_y - offset_y = 581 - 509 = 72
    
    print("\nConverting Two.js offsets to actual tile positions:")
    
    test_tiles = [
        ('PLAIN', 206, 509),
        ('MOUNTAIN', 189, 534),
        ('SEA', 138, 479),
        ('ROAD_HORT', 172, 509),
    ]
    
    for name, offset_x, offset_y in test_tiles:
        # Two.js offset means "distance from center of texture"
        # To get actual tile position, we need to think differently
        
        # The offset tells us how far from center to look
        # But Two.js renders from the CENTER of the sprite outward
        
        # So the actual extraction position is:
        actual_x = offset_x - 8  # Adjust for sprite half-width
        actual_y = offset_y - 8  # Adjust for sprite half-height
        
        print(f"\n{name}:")
        print(f"  Two.js offset: ({offset_x}, {offset_y})")
        print(f"  Actual position: ({actual_x}, {actual_y})")
        
        if 0 <= actual_x < tileset.width - 16 and 0 <= actual_y < tileset.height - 16:
            tile = tileset.crop((actual_x, actual_y, actual_x + 16, actual_y + 16))
            if tile.getbbox():
                print(f"  ✓ Tile found at this position!")
                tile.save(f"temp/test_{name}.png")

def main():
    check_coordinate_system()
    
    print("\n\n=== CONCLUSION ===")
    print("The coordinates in render.js are Two.js texture OFFSETS, not positions!")
    print("Two.js uses these offsets to select which part of the sprite sheet to show.")
    print("The actual sprite positions on the sheet are different from these offset values.")

if __name__ == "__main__":
    main()
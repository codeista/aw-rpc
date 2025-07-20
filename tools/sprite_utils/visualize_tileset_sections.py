#!/usr/bin/env python3
"""
Visualize different sections of the tileset to find pipes
"""

from PIL import Image, ImageDraw
import os

def visualize_tileset_sections():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    print(f"Tileset size: {tileset.size}")
    
    # Create multiple visualizations for different sections
    sections = [
        {"name": "section_1_roads", "x": 0, "y": 0, "w": 170, "h": 85},
        {"name": "section_2_next", "x": 85, "y": 0, "w": 170, "h": 85},
        {"name": "section_3_below", "x": 0, "y": 68, "w": 255, "h": 85},
        {"name": "section_4_right", "x": 170, "y": 0, "w": 170, "h": 85},
    ]
    
    for section in sections:
        # Extract section
        x, y, w, h = section["x"], section["y"], section["w"], section["h"]
        if x + w <= tileset.width and y + h <= tileset.height:
            section_img = tileset.crop((x, y, x + w, y + h))
            
            # Scale up 3x for better visibility
            scaled = section_img.resize((w * 3, h * 3), Image.NEAREST)
            
            # Add grid overlay
            draw = ImageDraw.Draw(scaled)
            
            # Draw vertical lines every 17*3 pixels
            for i in range(0, w, 17):
                draw.line([(i * 3, 0), (i * 3, h * 3)], fill=(255, 0, 0, 128), width=1)
            
            # Draw horizontal lines every 17*3 pixels
            for i in range(0, h, 17):
                draw.line([(0, i * 3), (w * 3, i * 3)], fill=(255, 0, 0, 128), width=1)
            
            # Add labels
            draw.text((10, 10), f"Section: {x},{y} to {x+w},{y+h}", fill=(255, 255, 0))
            
            filename = f"tileset_{section['name']}.png"
            scaled.save(filename)
            print(f"Created {filename}")
    
    # Also create a zoomed view of the area with pink/magenta tiles
    print("\nCreating detailed view of pink/magenta tile area...")
    pink_area = tileset.crop((85, 0, 255, 85))
    pink_scaled = pink_area.resize((170 * 4, 85 * 4), Image.NEAREST)
    
    draw = ImageDraw.Draw(pink_scaled)
    # Add coordinate labels
    for row in range(5):
        for col in range(10):
            x = 85 + col * 17
            y = row * 17
            
            # Label position on scaled image
            label_x = (col * 17) * 4 + 2
            label_y = (row * 17) * 4 + 2
            
            draw.text((label_x, label_y), f"{x},{y}", fill=(255, 255, 0), font=None)
    
    pink_scaled.save("pink_tiles_detail.png")
    print("Created pink_tiles_detail.png")

if __name__ == "__main__":
    visualize_tileset_sections()
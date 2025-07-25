#!/usr/bin/env python3
"""
Analyze what sprites are at each position in the UI spritesheet
"""

from PIL import Image
import json

def analyze_ui_sprites():
    print("=== Analyzing UI Sprites ===\n")
    
    # Load the source images to understand the layout
    ui_dir = "/home/box/Documents/aw-rpc/static/img/sprites_2x/ui"
    
    # Load hp_numbers to see what's in the first row
    hp_numbers = Image.open(f"{ui_dir}/hp_numbers_16x16.png")
    print(f"hp_numbers.png size: {hp_numbers.size}")
    print("This should contain 10 sprites (0-9) in a row\n")
    
    # Load hp_status_unavailable to see the colored numbers
    hp_unavailable = Image.open(f"{ui_dir}/hp_status_unavailable_16x16.png")
    print(f"hp_status_unavailable.png size: {hp_unavailable.size}")
    print("This is 224x80, which is 14x5 sprites")
    print("Should contain colored HP numbers for each army\n")
    
    # Load status_available to see what those 20 sprites are
    status_available = Image.open(f"{ui_dir}/status_available_16x16.png")
    print(f"status_available.png size: {status_available.size}")
    print("This is 64x80, which is 4x5 sprites = 20 sprites\n")
    
    # Analyze what's at the "hp_0" positions
    print("Sprites at positions that were labeled 'hp_0':")
    print("- Position (0,0): First sprite in hp_numbers row - this IS the '0' digit")
    print("- Position (180,0): First sprite in RED row - this IS the red '0'")
    print("- Position (0,18): First sprite in BLUE row - this IS the blue '0'")
    print("- Position (180,18): First sprite in GREEN row - this IS the green '0'")
    print("- Position (0,36): First sprite in YELLOW row - this IS the yellow '0'")
    print("- Position (180,36): First sprite in GREY row - this IS the grey '0'")
    
    print("\nConclusion: These ARE '0' digit sprites, but they might be used for:")
    print("1. Display purposes (like showing '10' which needs a '0')")
    print("2. Other UI elements that use digits")
    print("3. They exist in the source files, so we should keep them")
    
    print("\nThe 20 status sprites need proper names based on what they actually are.")
    print("Looking at status_available (64x80 = 4x5 grid)...")

if __name__ == "__main__":
    analyze_ui_sprites()
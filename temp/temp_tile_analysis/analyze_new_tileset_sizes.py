#!/usr/bin/env python3
"""
Analyze the actual sizes of tiles in the new AW2 tileset
by looking at the visual structure.
"""

from PIL import Image
import json

def analyze_tileset():
    """Analyze the new tileset to understand its structure"""
    
    img = Image.open('static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png')
    print(f"Tileset dimensions: {img.width}x{img.height}")
    
    # The tileset has labels, let's analyze common areas
    print("\nAnalyzing tileset structure based on visual inspection:")
    print("This tileset appears to use different scaling than expected.")
    
    # Buildings section analysis
    print("\nBuildings Section Analysis:")
    print("- Buildings might be split into smaller tiles")
    print("- Each building part could be 8x16 or 16x8")
    print("- Full buildings might be assembled from multiple tiles")
    
    # Check if we have an existing mapping
    try:
        with open('static/img/aw2_tileset_corrected_mapping.json', 'r') as f:
            mapping = json.load(f)
            print("\nFound your exported mapping:")
            for name, data in mapping.get('tiles', {}).items():
                print(f"  {name}: {data['width']}x{data['height']} at ({data['x']}, {data['y']})")
    except:
        print("\nNo corrected mapping found yet")
    
    print("\nPossible explanations for 8x16 HQ:")
    print("1. The HQ is split into 4 parts (8x16 each) = 16x32 total")
    print("2. The tileset uses half-size tiles (8x8 base instead of 16x16)")
    print("3. Buildings are meant to be scaled up 2x when rendering")
    
    print("\nRecommendation:")
    print("Map all parts of multi-tile buildings separately, like:")
    print("- hq_red_tl (top-left)")
    print("- hq_red_tr (top-right)")
    print("- hq_red_bl (bottom-left)")
    print("- hq_red_br (bottom-right)")

if __name__ == "__main__":
    analyze_tileset()
#!/usr/bin/env python3
"""
Clean up old tileset files and update references.
Keep only the optimized AW2 RGB tileset as primary.
"""

import os
import json

def cleanup_old_tilesets():
    """Remove old tileset files that are no longer needed"""
    
    old_tilesets = [
        'static/img/Advance_Wars_Dual_Strike_Tileset_Normal.png',
        'static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png',
        'static/img/aw2_blackhole_tileset_normal.png',
        'static/img/aw2_blackhole_tileset_normal_transparent.png',
        # Old optimized versions that are incomplete
        'static/img/optimized_tileset_normal.png',
        'static/img/optimized_tileset_transparent.png',
        'static/img/tileset_optimized.png',  # Keep the mapping but remove old attempts
    ]
    
    # Old sprite sheets we're replacing
    old_sprites = [
        'static/img/aw2_blackhole_units_map.png',
        'static/img/aw2_blackhole_units_map_transparent.png',
        'static/img/units_sprite_sheet_16x16.png',  # Replaced by complete version
        'static/img/units_sprite_sheet_v2.png',
    ]
    
    # Old mapping files
    old_mappings = [
        'static/img/units_sprite_map_16x16.json',
        'static/img/units_sprite_map_v2.json',
        'static/img/optimized_tileset_map.json',
        'static/img/tileset_optimized_map.json',
        'static/img/tileset_usage_guide.json',
    ]
    
    print("Cleaning up old tileset and sprite files...\n")
    
    total_size = 0
    removed_count = 0
    
    # Remove old tilesets
    print("Removing old tilesets:")
    for filepath in old_tilesets:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            total_size += size
            os.remove(filepath)
            removed_count += 1
            print(f"  ✓ Removed {filepath} ({size/1024:.1f}KB)")
        else:
            print(f"  - {filepath} (not found)")
    
    print("\nRemoving old sprite sheets:")
    for filepath in old_sprites:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            total_size += size
            os.remove(filepath)
            removed_count += 1
            print(f"  ✓ Removed {filepath} ({size/1024:.1f}KB)")
        else:
            print(f"  - {filepath} (not found)")
    
    print("\nRemoving old mapping files:")
    for filepath in old_mappings:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            total_size += size
            os.remove(filepath)
            removed_count += 1
            print(f"  ✓ Removed {filepath} ({size/1024:.1f}KB)")
        else:
            print(f"  - {filepath} (not found)")
    
    print(f"\n✅ Cleanup complete!")
    print(f"   Removed {removed_count} files")
    print(f"   Freed {total_size/1024:.1f}KB of space")
    
    # List remaining important files
    print("\n📁 Optimized files in use:")
    important_files = [
        ('Unit sprites', 'static/img/units_sprite_sheet_complete.png'),
        ('Unit mapping', 'static/img/units_sprite_map_complete.json'),
        ('Terrain tileset', 'static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png'),
        ('Terrain mapping', 'static/img/aw2_tileset_labeled_mapping.json'),
    ]
    
    for desc, filepath in important_files:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"  {desc}: {filepath} ({size/1024:.1f}KB)")

def create_migration_guide():
    """Create a guide for migrating to new tilesets"""
    
    guide = {
        "migration_date": "2024-07-18",
        "old_system": {
            "tilesets": [
                "Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png",
                "aw2_blackhole_tileset_normal_transparent.png"
            ],
            "issues": [
                "Large file sizes (75-211KB)",
                "Indexed color mode (limited palette)",
                "Multiple files to manage",
                "Slow loading"
            ]
        },
        "new_system": {
            "tileset": "Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png",
            "mapping": "aw2_tileset_labeled_mapping.json",
            "benefits": [
                "Single 125KB file",
                "Full RGB color",
                "Better quality",
                "Includes all terrain, buildings, roads, etc.",
                "Proper size support (16x16, 32x16, 32x32)",
                "Faster loading"
            ]
        },
        "usage": {
            "default": "The new AW2 RGB tileset is now the default",
            "fallback": "Old tilesets kept as fallback options in dropdown",
            "mapping": "Use aw2_tileset_labeled_mapping.json for tile coordinates"
        }
    }
    
    with open('static/img/TILESET_MIGRATION_GUIDE.json', 'w') as f:
        json.dump(guide, f, indent=2)
    
    print("\n📄 Created migration guide: static/img/TILESET_MIGRATION_GUIDE.json")

def main():
    print("🧹 AW-RPC Tileset Cleanup Tool\n")
    
    # Create migration guide first
    create_migration_guide()
    
    # Ask for confirmation
    response = input("\n⚠️  This will remove old tileset files. Continue? (y/n): ")
    
    if response.lower() == 'y':
        cleanup_old_tilesets()
    else:
        print("Cleanup cancelled.")

if __name__ == "__main__":
    main()
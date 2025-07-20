#!/usr/bin/env python3
"""
Backup old tileset files to a backup directory.
This preserves the old files while cleaning up the main img directory.
"""

import os
import shutil
from datetime import datetime

def backup_old_tilesets():
    """Move old tileset files to backup directory"""
    
    # Create backup directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"static/img/backup_tilesets_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    old_tilesets = [
        'static/img/Advance_Wars_Dual_Strike_Tileset_Normal.png',
        'static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png',
        'static/img/aw2_blackhole_tileset_normal.png',
        'static/img/aw2_blackhole_tileset_normal_transparent.png',
        'static/img/optimized_tileset_normal.png',
        'static/img/optimized_tileset_transparent.png',
        'static/img/tileset_optimized.png',
    ]
    
    old_sprites = [
        'static/img/aw2_blackhole_units_map.png',
        'static/img/aw2_blackhole_units_map_transparent.png',
        'static/img/units_sprite_sheet_16x16.png',
        'static/img/units_sprite_sheet_v2.png',
    ]
    
    old_mappings = [
        'static/img/units_sprite_map_16x16.json',
        'static/img/units_sprite_map_v2.json',
        'static/img/optimized_tileset_map.json',
        'static/img/tileset_optimized_map.json',
        'static/img/tileset_usage_guide.json',
        'static/img/aw2_tileset_mapping.json',
        'static/img/aw2_tileset_variable_mapping.json',
    ]
    
    # Also backup temporary/work files
    temp_files = [
        'static/img/tileset_comparison.png',
        'static/img/aw2_tileset_grid_reference.png',
        'static/img/aw2_tileset_analysis.png',
    ]
    
    print(f"📁 Creating backup directory: {backup_dir}\n")
    
    total_size = 0
    backed_up_count = 0
    
    all_files = [
        ("Old Tilesets", old_tilesets),
        ("Old Sprite Sheets", old_sprites),
        ("Old Mappings", old_mappings),
        ("Temporary Files", temp_files)
    ]
    
    for category, files in all_files:
        print(f"\n{category}:")
        for filepath in files:
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                total_size += size
                filename = os.path.basename(filepath)
                backup_path = os.path.join(backup_dir, filename)
                shutil.move(filepath, backup_path)
                backed_up_count += 1
                print(f"  ✓ Backed up {filename} ({size/1024:.1f}KB)")
            else:
                print(f"  - {filepath} (not found)")
    
    # Create a README in the backup directory
    readme_content = f"""# Tileset Backup - {timestamp}

This directory contains old tileset and sprite files that have been replaced by optimized versions.

## Replaced by:
- **Units**: units_sprite_sheet_complete.png (58KB, 250 sprites)
- **Terrain**: Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png (125KB, RGB)

## Why replaced:
- Old files were larger (up to 362KB for units, 211KB for terrain)
- Indexed color mode had limited quality
- New files are smaller, RGB quality, and load faster

## Restoration:
If needed, these files can be copied back to static/img/
"""
    
    with open(os.path.join(backup_dir, 'README.md'), 'w') as f:
        f.write(readme_content)
    
    print(f"\n✅ Backup complete!")
    print(f"   Backed up {backed_up_count} files")
    print(f"   Total size: {total_size/1024:.1f}KB")
    print(f"   Location: {backup_dir}")
    
    # List remaining optimized files
    print("\n📁 Optimized files now in use:")
    important_files = [
        ('Unit sprites', 'static/img/units_sprite_sheet_complete.png'),
        ('Unit mapping', 'static/img/units_sprite_map_complete.json'),
        ('Terrain tileset', 'static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png'),
        ('Terrain mapping', 'static/img/aw2_tileset_labeled_mapping.json'),
    ]
    
    for desc, filepath in important_files:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"  {desc}: {os.path.basename(filepath)} ({size/1024:.1f}KB)")

def main():
    print("🗄️  AW-RPC Tileset Backup Tool\n")
    print("This will backup old tilesets to a timestamped directory.\n")
    
    backup_old_tilesets()

if __name__ == "__main__":
    main()
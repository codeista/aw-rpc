#!/usr/bin/env python3
"""
Analyze tiles currently used in the game from map_system.py
Compare with our extracted tiles to see what's actually needed
"""

import json
import os
from pathlib import Path

def analyze_map_system():
    """Analyze map_system.py to find all tile types used"""
    print("🔍 Analyzing map_system.py for tile usage...")
    
    # Read map_system.py
    with open("map_system.py", "r") as f:
        content = f.read()
    
    # Find terrain types
    terrain_types = set()
    buildings = set()
    
    # Look for TerrainType references
    if "TerrainType." in content:
        # Extract all TerrainType.XXX references
        import re
        terrain_matches = re.findall(r'TerrainType\.(\w+)', content)
        terrain_types.update(terrain_matches)
    
    # Look for building types
    building_keywords = ['HQ', 'CITY', 'BASE', 'AIRPORT', 'PORT', 'FACTORY', 'SILO', 'COM_TOWER']
    for building in building_keywords:
        if building in content:
            buildings.add(building)
    
    return terrain_types, buildings

def analyze_map_files():
    """Analyze actual map files to see what tiles are used"""
    print("\n📁 Analyzing map files...")
    
    map_dir = Path("maps")
    used_tiles = set()
    
    if map_dir.exists():
        for map_file in map_dir.glob("*.json"):
            print(f"  Checking {map_file.name}...")
            try:
                with open(map_file, 'r') as f:
                    map_data = json.load(f)
                
                # Extract tile types from map data
                if 'tiles' in map_data:
                    for row in map_data['tiles']:
                        for tile in row:
                            if isinstance(tile, dict):
                                if 'terrain' in tile:
                                    used_tiles.add(tile['terrain'])
                                if 'building' in tile:
                                    used_tiles.add(tile['building'])
                            elif isinstance(tile, str):
                                used_tiles.add(tile)
                
                # Also check terrain_grid if present
                if 'terrain_grid' in map_data:
                    for row in map_data['terrain_grid']:
                        for terrain in row:
                            if terrain:
                                used_tiles.add(terrain)
                
                # Check building_grid if present
                if 'building_grid' in map_data:
                    for row in map_data['building_grid']:
                        for building in row:
                            if building:
                                used_tiles.add(building)
                                
            except Exception as e:
                print(f"    Error reading {map_file}: {e}")
    
    return used_tiles

def check_rendering_files():
    """Check render.js and related files for tile references"""
    print("\n🎨 Checking rendering files...")
    
    tile_mappings = {}
    
    # Check for tile mapping files
    static_dir = Path("static")
    if static_dir.exists():
        # Look for tileset mapping JSON files
        for json_file in static_dir.rglob("*tile*.json"):
            if "optimized" not in str(json_file):  # Skip optimized versions
                print(f"  Found mapping: {json_file.name}")
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            # Count tile types
                            for key in data:
                                if isinstance(data[key], dict) and 'terrain' in data[key]:
                                    terrain = data[key]['terrain']
                                    if terrain not in tile_mappings:
                                        tile_mappings[terrain] = 0
                                    tile_mappings[terrain] += 1
                except:
                    pass
    
    # Check render.js for hardcoded tile types
    render_tiles = set()
    render_files = ["render.js", "render_legacy.js", "static/js/render.js"]
    
    for render_file in render_files:
        if os.path.exists(render_file):
            print(f"  Checking {render_file}...")
            with open(render_file, 'r') as f:
                content = f.read()
                
                # Look for tile type references
                import re
                # Common patterns in render files
                tile_patterns = [
                    r"tile[Tt]ype\s*===?\s*['\"](\w+)['\"]",
                    r"terrain\s*===?\s*['\"](\w+)['\"]",
                    r"building\s*===?\s*['\"](\w+)['\"]",
                    r"case\s+['\"](\w+)['\"]:",
                ]
                
                for pattern in tile_patterns:
                    matches = re.findall(pattern, content)
                    render_tiles.update(matches)
    
    return tile_mappings, render_tiles

def analyze_terrain_enum():
    """Check if there's a terrain enum definition"""
    print("\n🏗️ Looking for terrain type definitions...")
    
    terrain_enum = {}
    
    # Check Python files for enum definitions
    for py_file in Path(".").glob("*.py"):
        with open(py_file, 'r') as f:
            content = f.read()
            
        if "TerrainType" in content and "Enum" in content:
            print(f"  Found TerrainType in {py_file}")
            # Extract enum values
            import re
            enum_pattern = r"(\w+)\s*=\s*['\"](\w+)['\"]"
            matches = re.findall(enum_pattern, content)
            for name, value in matches:
                if name.isupper():  # Likely an enum constant
                    terrain_enum[name] = value
    
    return terrain_enum

def compare_with_extracted():
    """Compare game tiles with our extracted tiles"""
    # Skip this for now - focus on game tiles only
    return set()

def main():
    print("🎮 Advance Wars RPC - Tile Usage Analysis")
    print("=" * 50)
    
    # 1. Analyze map_system.py
    terrain_types, buildings = analyze_map_system()
    print(f"\n📝 From map_system.py:")
    print(f"  Terrain types found: {len(terrain_types)}")
    print(f"  Building types found: {len(buildings)}")
    
    # 2. Analyze actual map files
    map_tiles = analyze_map_files()
    print(f"\n🗺️ From map files:")
    print(f"  Unique tiles used: {len(map_tiles)}")
    if map_tiles:
        print("  Tiles:", sorted(map_tiles)[:10], "..." if len(map_tiles) > 10 else "")
    
    # 3. Check rendering files
    tile_mappings, render_tiles = check_rendering_files()
    print(f"\n🎨 From rendering:")
    print(f"  Tile mappings found: {len(tile_mappings)}")
    print(f"  Render tile references: {len(render_tiles)}")
    
    # 4. Look for terrain enum
    terrain_enum = analyze_terrain_enum()
    print(f"\n🏗️ Terrain enum values: {len(terrain_enum)}")
    
    # 5. Compare with extracted
    extracted_tiles = compare_with_extracted()
    print(f"\n✅ Extracted tiles: {len(extracted_tiles)}")
    
    # Compile all used tiles
    all_used = set()
    all_used.update(terrain_types)
    all_used.update(buildings)
    all_used.update(map_tiles)
    all_used.update(render_tiles)
    all_used.update(terrain_enum.keys())
    all_used.update(terrain_enum.values())
    
    # Filter out non-tile entries
    filtered_tiles = {t for t in all_used if t and t.upper() == t or '_' in t}
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    print(f"Total unique tile types referenced: {len(filtered_tiles)}")
    print("\nTile types found:")
    for tile in sorted(filtered_tiles):
        if tile:  # Skip empty strings
            status = "✅" if tile in extracted_tiles else "❌"
            print(f"  {status} {tile}")
    
    # Check for extracted tiles not used in game
    unused_extracted = extracted_tiles - filtered_tiles
    if unused_extracted:
        print(f"\n⚠️ Extracted but possibly unused: {len(unused_extracted)}")
        for tile in sorted(unused_extracted)[:10]:
            print(f"  - {tile}")
        if len(unused_extracted) > 10:
            print(f"  ... and {len(unused_extracted) - 10} more")
    
    # Save results
    results = {
        "game_tiles": sorted(list(filtered_tiles)),
        "extracted_tiles": sorted(list(extracted_tiles)),
        "unused_extracted": sorted(list(unused_extracted)),
        "missing_from_extraction": sorted(list(filtered_tiles - extracted_tiles))
    }
    
    with open("temp/tile_analysis_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to temp/tile_analysis_results.json")

if __name__ == "__main__":
    main()
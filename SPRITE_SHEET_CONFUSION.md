# Sprite Sheet Confusion Documentation

## Current Sprite Sheets in Use (As of 2025-07-20)

### TERRAIN SPRITES
**Currently Used**: `/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png`
- This is the AWDS tileset with proper transparency
- Contains all terrain tiles in a grid layout
- Function: `getSelectedTerrainTileset()` in render_legacy.js

### UNIT SPRITES  
**Currently Used**: `/static/img/units_sprite_sheet_complete.png`
- This is the optimized/complete unit sprite sheet
- Contains all unit sprites organized by type
- Function: `getSelectedUnitSpriteSheet()` in render_legacy.js

## Common Confusion Points

### 1. Multiple Unit Sprite Sheets
There are several unit sprite sheets in the project:
- `units_sprite_sheet_complete.png` - **CURRENTLY USED** (58KB)
- `units_sprite_sheet_v2.png` - Old version, not used (250KB)
- `units_sprite_sheet_16x16.png` - Old version, not used
- `aw2_blackhole_units_map_transparent.png` - Alternative, not active

### 2. Multiple Terrain Tilesets
- `Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png` - **CURRENTLY USED**
- `Advance_Wars_Dual_Strike_Tileset_Normal.png` - Non-transparent version
- `aw2_blackhole_tileset_normal_transparent.png` - Alternative AW2 tileset
- `Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png` - AW2 RGB tileset (problematic)

### 3. Extraction Confusion
When extracting sprites for upscaling:
- **DO NOT** extract from `units_sprite_sheet_v2.png` 
- **DO** extract from `units_sprite_sheet_complete.png` for units
- **DO** extract from `Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png` for terrain

### 4. Coordinate Systems
- The old sprite sheets (v2) used a different coordinate system
- The complete/optimized sheets use the coordinate mappings in:
  - `/static/img/optimized_tileset_map.json` for terrain
  - `/static/img/units_sprite_map_complete.json` for units (was missing, now restored)

## How to Verify Current Usage

1. Check `render_legacy.js`:
```javascript
function getSelectedTerrainTileset() {
    // Returns current terrain tileset
}

function getSelectedUnitSpriteSheet() {
    // Returns current unit sprite sheet
}
```

2. Look for the default returns in these functions - those are what's actually being used.

## For Sprite Extraction/Upscaling

Use these source files and their coordinate maps:
- **Units**: 
  - Source: `/static/img/units_sprite_sheet_complete.png`
  - Coordinates: `/static/img/units_sprite_map_complete.json`
- **Terrain**: 
  - Source: `/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png`
  - Coordinates: `/static/img/optimized_tileset_map.json`

The extraction scripts should reference these files, not the old v2 versions.

## Important Files Summary
- ✅ `units_sprite_sheet_complete.png` - Current unit sprites (16x16, organized in rows)
- ✅ `units_sprite_map_complete.json` - Coordinate map for complete sprite sheet
- ✅ `Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png` - Current terrain tileset
- ✅ `optimized_tileset_map.json` - Coordinate map for terrain tiles
- ❌ `units_sprite_sheet_v2.png` - OLD, DO NOT USE
- ❌ `units_sprite_map_v2.json` - OLD, DO NOT USE
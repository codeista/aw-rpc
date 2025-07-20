# Sprite Rendering Fix Plan

## Current Situation
- **What's Working**: 
  - Terrain tiles are rendering (using AWDS tileset)
  - Game board structure displays correctly (12x10 grid)
  - Click detection is functional
  - API returns correct game data (33 units, 16 buildings)

- **What's Broken**:
  - Unit sprites are not rendering (only some sprites appear)
  - Missing critical sprite sheet files causing 404 errors:
    - `/static/img/units_sprite_sheet_v2.png`
    - `/static/img/awbw_unit_sprites.png` 
    - `/static/img/aw2_blackhole_units_map_transparent.png`

## Root Cause Analysis
1. The optimized sprite renderer (optimized-sprite-renderer.js) is trying to load `units_sprite_sheet_v2.png`
2. This file was deleted/moved but the sprite map JSON still exists
3. The legacy renderer falls back to `aw2_blackhole_units_map_transparent.png` which is also missing
4. All these missing files exist in the backup folder from 2025-07-18

## Fix Options

### Option 1: Restore Missing Sprite Files (Quickest)
- Copy sprite files from backup folder to static/img
- Files to restore:
  - `units_sprite_sheet_v2.png` (101KB)
  - `aw2_blackhole_units_map_transparent.png` (369KB)
- Pros: Quick fix, known working files
- Cons: May have been removed for a reason

### Option 2: Disable Optimized Sprite Renderer
- Similar to how we disabled the tile renderer
- Force use of original sprite loading method
- Would need to check what the fallback sprite source is
- Pros: Consistent with tile renderer approach
- Cons: Larger file sizes, slower loading

### Option 3: Use Alternative Sprite Sheets
- Found existing sprites in special-units folder
- Could redirect to use awbw_unit_sprites.png if it exists elsewhere
- Pros: May be using updated sprites
- Cons: Need to verify sprite mappings match

### Option 4: Create New Optimized Sprites
- Use the scripts in temp/ folder to regenerate
- Files exist: create_optimized_unit_sprites.py
- Pros: Fresh generation, can fix any issues
- Cons: More complex, time consuming

## Recommended Approach
Start with **Option 1** (restore from backup) to get the game working immediately, then investigate why the files were removed and consider Option 2 or 4 for a permanent solution.

## Implementation Steps
1. Copy missing sprite files from backup
2. Verify sprites load correctly
3. Test unit rendering in game
4. Check for any visual issues
5. Document the fix
6. Consider long-term solution
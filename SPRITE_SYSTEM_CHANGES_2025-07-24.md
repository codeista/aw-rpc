# Sprite System Changes - July 24, 2025

## Overview
This document summarizes the sprite system overhaul completed on the `claude-v1` branch.

## Major Changes

### 1. Created Combined Sprite Sheets
Previously, the game was looking for sprite sheets in `/static/img/sprites_2x/combined/` but the directory was empty. We created:

- **terrain_tileset_2x.png** (199 sprites) - Used by minimal_game.js
- **terrain_tileset_2x_final.png** (199 sprites) - Used by game_v2.js  
- **units_spritesheet_2x.png** (250 sprites) - All unit sprites
- **ui_spritesheet_2x.png** - Placeholder UI elements

Each sprite sheet has a corresponding JSON map file with sprite coordinates.

### 2. Fixed Sprite Naming Issues
- Renamed HQ sprites: `HQ_VARIANT_X` → `BASE_TOWER_X` (for X = 0-4)
- Applied to all army colors (RED, BLUE, GREEN, YELLOW, GREY)
- Updated sprite maps to use new names
- Added BASE_TOWER types to tall sprite lists in JavaScript

### 3. Fixed Rendering Issues

#### Tall Sprite Overlap
- Changed rendering order from bottom-to-top to **top-to-bottom**
- This allows tall sprites (like HQs) to properly overlap tiles above them
- Fixed in both minimal_game.js and game_v2.js

#### SEA Tile Selection
- Initially used SEA_0_0 which had issues
- Changed to SEA_1_0, then to SEA_5_0 per user preference
- Fixed artifact in SEA_5 tiles (bottom left corner pixels)

### 4. Sprite Organization
Individual sprites are organized in `/static/img/sprites_2x/`:
- `terrain/` - Basic terrain, roads, water, pipes
- `units/` - All unit sprites by category
- `ui/` - UI elements (mostly placeholders)

Combined sprites with proper spacing (4px) prevent overlap issues.

## Technical Details

### Coordinate System
- Y coordinate marks the BOTTOM of sprites (not top)
- Tall sprites use `full_height` property
- Standard tiles: 32x32, Buildings: up to 64px tall

### Sprite Mapping
- Road T-junctions: `ROAD_T_N` → `NESRoad`, etc.
- Empty silo: `MISSILE_SILO_EMPTY` → `EMPTY_SILO`
- SEA tile: Using SEA_5_0 for basic water

## Files Modified

### JavaScript
- `/static/js/minimal_game.js` - Fixed tall sprite rendering, added BASE_TOWER support
- `/static/js/game_v2.js` - Same fixes for v2 API version

### Documentation
- Updated `CLAUDE.md` with current sprite system details
- Created `SPRITE_SYSTEM_STATUS.md` for ongoing work tracking
- Added `CLAUDE_HOOKS.md` for safety rules (no rm without permission)

## Known Issues Remaining
1. Beach tile orientation (BEACH_W and BEACH_E swapped)
2. Beach/water tiles still use numbered format instead of directional names
3. UI sprites are placeholders - need proper HP graphics

## Testing
The sprite system has been tested and renders correctly:
- All terrain tiles display properly
- Buildings show correct army colors  
- Tall sprites (HQs, mountains, woods) overlap correctly
- Units render with proper sprites

Ready for merge to main branch.
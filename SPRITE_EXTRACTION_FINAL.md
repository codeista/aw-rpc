# Sprite Extraction Documentation

## Overview
This document explains how sprites are extracted from the game's sprite sheets for AI upscaling.

## Sprite Sheets Used

### Unit Sprites
- **File**: `/static/img/units_sprite_sheet_complete.png`
- **Coordinate Map**: `/static/img/units_sprite_map_complete.json`
- **Size**: 16x16 pixels per sprite
- **Total**: 250 unit sprites

### Terrain Sprites  
- **File**: `/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png`
- **Size**: 445x1163 pixels
- **Sprite Sizes**: 
  - Basic terrain: 16x16 pixels
  - Buildings/Trees: 16x32 pixels (double height)

## Terrain Coordinate System

The game uses hardcoded offsets in `render_legacy.js`. The coordinate system works as follows:

1. **Start Position**: 
   ```javascript
   x = spriteSheetWidth/2 - SPRITESIZE/2;  // 222 - 8 = 214
   y = spriteSheetHeight/2 - SPRITESIZE/2; // 581 - 8 = 573
   ```

2. **For each tile type**, offsets are SUBTRACTED from start position
3. **IMPORTANT**: The offset values ARE the actual pixel coordinates in the sprite sheet!

### Examples:
- **PLAIN**: offset (8, 64) → actual pixels at (8, 64)
- **ROAD_HORT**: offset (42, 64) → actual pixels at (42, 64)
- **WOOD**: offset (352, 56) → actual pixels at (352, 48) *
  
\* For double-height sprites, subtract 8 from y offset to get top position

## Tile Types Expected by Game

The game expects these exact tile type names:

### Basic Terrain
- `PLAIN`
- `WOOD` (32px tall)
- `MOUNTAIN` (32px tall)
- `REEF`
- `WATER`

### Roads
- `ROAD_HORT` (horizontal)
- `ROAD_VERT` (vertical)
- `ROAD_NW`, `ROAD_NE`, `ROAD_SE`, `ROAD_SW` (corners)
- `SWNRoad`, `ESWRoad`, `WNERoad`, `NESRoad` (T-junctions)
- `CRoad` (crossroad)

### Buildings (32px tall)
Buildings have separate sprites for each army color:
- `CITY_neutral`, `CITY_RED`, `CITY_BLUE`, `CITY_GREEN`, `CITY_YELLOW`, `CITY_GREY`
- `FACTORY_neutral`, `FACTORY_RED`, etc.
- `AIRPORT_neutral`, `AIRPORT_RED`, etc.
- `PORT_neutral`, `PORT_RED`, etc.
- `HQ_RED`, `HQ_BLUE`, etc. (no neutral HQ)
- `COM_TOWER_neutral`, `COM_TOWER_RED`, etc.
- `LAB_neutral`, `LAB_RED`, etc.

### Special
- `MISSILE_SILO` (has ammo)
- `EMPTY_SILO` (fired)

## Tileset Organization

The AWDS tileset is organized in labeled sections:

1. **"Clear"** (top) - Basic terrain in clear weather
2. **"Animated tiles"** - Water animations (blue section)
3. **"Fog"** - Fog of war versions
4. **"Neutral"** (y=757) - Neutral buildings
5. **Army buildings** (y=803+) - Buildings for each army color:
   - RED (y=803)
   - BLUE (y=838)
   - GREEN (y=873)
   - YELLOW (y=908)
   - GREY (y=943)
6. **"Lights on/off"** - Day/night versions
7. **Units section** (bottom) - Unit sprites

## Extraction Process

### 1. Extract Unit Sprites
```python
# Uses units_sprite_map_complete.json
# Each sprite has exact x,y coordinates
# Example: "INFANTRY_RED_idle_0": {"x": 0, "y": 0, "width": 16, "height": 16}
```

### 2. Extract Terrain Sprites
```python
# Basic terrain (found at top of tileset)
PLAIN: (8, 64, 16, 16)
WOOD: (352, 48, 16, 32)  # Note: y=56 in code, but actual top is 48
MOUNTAIN: (25, 31, 16, 32)  # y=39 in code, actual top is 31

# Buildings (found in labeled rows)
# Neutral at y=757
CITY_neutral: (1, 757, 16, 32)
FACTORY_neutral: (18, 757, 16, 32)
# etc...

# Army buildings start at y=803 with 35px spacing between rows
```

### 3. Rename for Game Compatibility
- Remove variant sprites (PLAIN_var1, etc.)
- Rename road corners: ROAD_CORNER_NE → ROAD_NE
- Keep building army suffixes (CITY_RED, not just CITY)

## Final Output

The extraction creates:
- 250 unit sprites (correctly named)
- ~69 terrain sprites (renamed to match game expectations)
- Total: ~319 sprites ready for AI upscaling

## Scripts Used

1. `temp/extract_terrain_by_sections.py` - Extracts based on tileset sections
2. `temp/rename_sprites_for_game.py` - Renames to match game expectations
3. Final output: `temp/GAME_READY_sprites.zip`
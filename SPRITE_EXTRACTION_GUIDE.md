# Sprite Extraction Guide for AI Upscaling

## Overview
This guide documents the correct sprite locations and extraction process for the Advance Wars RPC game to avoid confusion in future sprite work.

## Sprite Sheets Used

### 1. Unit Sprites
- **File**: `/static/img/units_sprite_sheet_complete.png`
- **Size**: 160x400 pixels
- **Grid**: 10x25 (250 sprites total)
- **Sprite Size**: ALL sprites are 16x16 pixels
- **Organization**: 
  - Columns 0-1: Red/Orange army (idle, used states)
  - Columns 2-3: Blue army
  - Columns 4-5: Green army
  - Columns 6-7: Yellow army  
  - Columns 8-9: Black/Grey army

### 2. Terrain Tiles
- **File**: `/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png`
- **Size**: 445x1163 pixels (NOT perfectly divisible by 16!)
- **Tile Sizes**: 
  - Most terrain: 16x16 pixels
  - Buildings & special terrain: 16x32 pixels (double height)
  
## Important Notes About Terrain Tileset

### Coordinate System Issues
The render_legacy.js uses a CENTER-BASED coordinate system:
```javascript
var x = spriteSheetWidth/2 - SPRITESIZE/2;  // 222.5 - 8 = 214.5
var y = spriteSheetHeight/2 - SPRITESIZE/2; // 581.5 - 8 = 573.5
```

Then it SUBTRACTS offsets from this center point. This causes many tiles to have NEGATIVE coordinates which are out of bounds!

### Double Height Tiles (16x32)
These tiles use `_2xHeight = true` in render.js:
- HQ
- MOUNTAIN
- CITY
- FACTORY
- AIRPORT
- PORT
- BASE_TOWER_0 through BASE_TOWER_4
- LAB
- COM_TOWER
- MISSILE_SILO
- EMPTY_SILO

## Extraction Strategy

### For Unit Sprites (SIMPLE)
1. Extract all 250 sprites as 16x16 from the grid
2. No special handling needed
3. All sprites are the same size

### For Terrain Tiles (COMPLEX)
The terrain tileset has several issues:
1. Uses center-based coordinates that often go negative
2. Not all tiles are accessible with the current coordinate system
3. Mixed tile sizes (16x16 and 16x32)

**RECOMMENDED APPROACH:**
Instead of using the complex coordinate system from render.js, extract tiles systematically:
1. Extract all possible 16x16 tiles from the tileset
2. Identify which tiles are actually buildings (they appear as 16x32)
3. Group related tiles together

## Files Created for Extraction

1. **verify_sprites_simple.py** - Creates verification images of sprite sheets
2. **extract_actual_coordinates.py** - Attempts to use render.js coordinates (many fail)
3. **extract_all_sprites_16x16.py** - Systematic extraction of all tiles

## Upscaling Process

1. **Target Size**: 3x original (16x16 → 48x48, 16x32 → 48x96)
2. **Method**: AI upscaling with waifu2x or similar
3. **Settings**: 
   - Style: Artwork (not Photo)
   - Noise Reduction: None
   - Scale: 3x

## Known Issues

1. **Terrain Tileset Coordinates**: Many tiles referenced in render.js have coordinates outside the tileset bounds due to the center-based system with large negative offsets.

2. **Tileset Size**: The tileset is 445x1163, which means:
   - 13 pixels of padding on the right (445 = 27*16 + 13)
   - 11 pixels of padding on the bottom (1163 = 72*16 + 11)

3. **Missing Sprites**: The game references `units_sprite_sheet_complete.png` but sometimes it's missing and needs to be copied from temp/.

## Recommended Extraction Approach

Given the coordinate issues, the best approach is:

1. **For Units**: Use the complete sprite sheet and extract all 250 sprites
2. **For Terrain**: 
   - Extract tiles systematically in a grid pattern
   - Manually identify buildings and special tiles
   - Don't rely solely on render.js coordinates as many are out of bounds

## Next Steps

1. Extract sprites using a grid-based approach
2. Verify all important game tiles are captured
3. Create batches for AI upscaling
4. Upscale to 3x size
5. Reassemble into new sprite sheets
6. Update game code to use larger sprites
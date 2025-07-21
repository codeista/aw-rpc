# Complete Sprite and Tile Guide

## Current Files in Use (IMPORTANT)

### Unit Sprites
- **File**: `/static/img/units_sprite_sheet_complete.png`
- **Size**: 160x400 pixels (10x25 grid, 250 sprites)
- **Sprite size**: 16x16 pixels each
- **Coordinate map**: `/static/img/units_sprite_map_complete.json`

### Terrain Tiles  
- **File**: `/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png`
- **Size**: 445x1163 pixels
- **Tile sizes**: 16x16 (terrain), 16x32 (buildings)
- **Tile spacing**: 17px (16px tile + 1px separator)

## DO NOT USE These Files
- `units_sprite_sheet_v2.png` - Old version
- `aw2_blackhole_units_map_transparent.png` - Alternative not in use
- Any tileset with "optimized" in the name (corrupted)

## Extraction Details - Complete Reference

### For Units (Simple)
1. All units are on a 10x25 grid
2. Each sprite is exactly 16x16 pixels
3. Extract using grid coordinates: `(col * 16, row * 16, (col+1) * 16, (row+1) * 16)`

### Terrain Tiles (Verified Coordinates)
1. Tiles are at specific positions, NOT on a regular grid
2. Verified terrain tile coordinates:
   - **PLAIN**: (8, 64, 16, 16)
   - **PLAIN_var1**: (25, 64, 16, 16) 
   - **WOOD**: (352, 48, 16, 32) - Double height
   - **MOUNTAIN**: (25, 31, 16, 32) - Double height
   - **REEF**: (195, 145, 16, 16)

### Road Tiles (Verified)
1. Starting position: (42, 13) with 17px spacing
2. Layout: 3×4 grid (12 tiles total)
   - **3×3 grid** forms circle pattern:
     - Corners: NW (42,13), NE (76,13), SW (42,47), SE (76,47)
     - T-junctions: N (59,13), E (76,30), S (59,47), W (42,30)
     - Center: CROSS (59,30)
   - **Bottom row** - Plain roads without markings:
     - HORT_PLAIN (42,64), VERT_PLAIN (59,64), HORT_PLAIN2 (76,64)

### Pipe Tiles (Verified)
1. Starting position: (144, 13) with 17px spacing
2. Grid: 4 rows × 5 columns (15 tiles total)
3. Pattern:
   ```
   Row 0: X - - - -  (SPECIAL)
   Row 1: X X X X X  (CIRCLE_TL, CIRCLE_TR, END_N, HORT, VERT)
   Row 2: X X X X X  (CIRCLE_BL, CIRCLE_BR, END_S, SEAM_WE, SEAM_NS)
   Row 3: X X - X X  (END_W, END_E, skip, BROKEN_WE, BROKEN_NS)
   ```
4. Skip positions: (0,1), (0,2), (0,3), (0,4), (3,2)

### Water Tiles (Verified)
1. Starting position: (8, 94)
2. Structure: Horizontal layout with **3px gaps** between sections
   - **Sea tiles**: x=8, columns 0-11 (12 tiles × 4 rows = 48 total)
   - **Beach tiles**: x=214 (after 3px gap), columns 0-8 (9 tiles × 4 rows = 36 total)
   - **River tiles**: x=369 (after 3px gap), columns 0-3 (4 tiles × 4 rows - 1 blank = 15 total)
3. **Total**: 99 water tiles
4. **Animation**: Each tile has 4 frames vertically; we extract only the first
5. **Note**: River position (3,3) is blank/empty

### Building Tiles (Mostly 16×32 - Verified)
1. **Neutral buildings** at y=757:
   - All buildings are 16×32 (double height)
   - See VERIFIED_TILE_COORDINATES.md for exact coordinates
2. **Army buildings** at different y-coordinates per army:
   - RED: y=803, BLUE: y=836, GREEN: y=869, YELLOW: y=902, GREY: y=935
   - Most buildings are 16×32 (double height)
   - **EXCEPTION**: FACTORY buildings are 16×16 (bottom half only)
   - FACTORY extracted from (x, y+16) coordinates
3. **Fog buildings**: Same coordinates + 372 pixels in Y direction

### Fog Tiles (Verified)
1. **Consistent offset**: All fog tiles are at non-fog position + 372 pixels in Y
2. **First fog tile**: (42, 385) corresponds to first road tile at (42, 13)
3. **Categories extracted**:
   - Fog Roads: 12 tiles (3×4 grid)
   - Fog Pipes: 15 tiles (4×5 grid with same skip pattern)
   - Fog Terrain: 7 tiles
   - Fog Water: 99 tiles (same structure as non-fog)
   - Fog Buildings: At end of neutral building row
4. **Total fog tiles**: 134+ tiles extracted and verified

## Key Patterns and Rules

### Spacing and Gaps
- **Standard tile spacing**: 17px (16px tile + 1px separator)
- **Water section gaps**: 3px between sea/beach and beach/river
- **Fog offset**: Exactly +372 pixels in Y direction

### Grid Structures
- **Roads**: 3 rows × 4 columns
- **Pipes**: 4 rows × 5 columns (not 5×4!)
- **Water**: Single row structure, organized horizontally by type

### Common Extraction Issues (Fixed)
1. **REEF position**: Was incorrectly at (144, 270), fixed to (195, 145)
2. **Spurious tiles**: PORT and RUINS are NOT terrain tiles (PORT is a building, RUINS don't exist)
3. **Grid confusion**: Pipes are 4×5, not 5×4
4. **Water gaps**: 3px gaps, not 1px
5. **Blank tiles**: Position (3,2) in pipes and (3,3) in river are empty

## Upscaling Approach

### CORRECT Method for Pixel Art
1. **Algorithm**: Scale2x, HQ2x, or xBRZ (NOT waifu2x)
2. **No hard thresholding** - Preserve semi-transparent edges
3. **Tile-specific processing**:
   - Terrain: Crisp edges, no smoothing
   - Water: Slight edge smoothing OK
   - Roads/Pipes: Maintain connections
   - Fog buildings: Brightness +20%

### What NOT to Do
- Don't use waifu2x (blurs pixel art)
- Don't apply hard alpha threshold
- Don't use "anime style" upscalers

## PNG Palette Mode Handling
```python
# Correct way to load palette mode tiles
if tile.mode == 'P':
    transparency = tile.info.get('transparency', None)
    tile = tile.convert('RGBA')
    # Apply transparency if needed
```

## File Organization
- Extracted tiles: `temp/terrain_sections/`
- Upscaled tiles: `temp/terrain_upscaled/`
- Showcases: `temp/showcases/`
- Working scripts: Keep in temp/
- Old/experimental: Move to archive/

## Quick Reference Summary
- **Terrain tiles**: 7 basic terrain types
- **Road tiles**: 12 tiles in 3×4 grid
- **Pipe tiles**: 15 tiles in 4×5 grid
- **Water tiles**: 99 total (48 sea + 36 beach + 15 river)
- **Buildings**: All are 16×32 (double height)
- **Fog tiles**: 134+ with consistent +372px Y offset
- **Total unique tiles extracted**: 250+ tiles verified

## Upscaling Status (2025-07-21)

### ✅ Completed Upscaling (2x using Nearest Neighbor)
- **Map Tiles**: 199 tiles upscaled from verified coordinates
  - Location: `/temp/all_tiles_upscaled_2x/`
  - Terrain: 16×16 → 32×32
  - Buildings: 16×32 → 32×64 (except FACTORY: 16×16 → 32×32)
  - Roads/Pipes/Water: 16×16 → 32×32

- **Unit Sprites**: 250 sprites upscaled with proper labels
  - Location: `/temp/units_upscaled_2x_labeled/`
  - All units: 16×16 → 32×32
  - Organized by type: infantry, tanks, vehicles, air, naval, special
  - Label format: `UNITTYPE_ARMY_STATE_INDEX.png`

### Upscaling Method
- Algorithm: Nearest Neighbor (pixel-perfect scaling)
- Preserves sharp pixel art aesthetic
- No smoothing or interpolation artifacts

## Remaining Tasks
- Label water tiles with descriptive names (SEA_NW, BEACH_CORNER_SE, etc.)
- Integrate upscaled assets into game rendering
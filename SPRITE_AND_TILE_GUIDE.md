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
- **Extraction script**: `temp/extract_terrain_by_sections.py`

## DO NOT USE These Files
- `units_sprite_sheet_v2.png` - Old version
- `aw2_blackhole_units_map_transparent.png` - Alternative not in use
- Any tileset with "optimized" in the name (corrupted)

## Extraction Process

### For Units (Simple)
1. All units are on a 10x25 grid
2. Each sprite is exactly 16x16 pixels
3. Extract using grid coordinates: `(col * 16, row * 16, (col+1) * 16, (row+1) * 16)`

### For Terrain (Complex)
1. Use `temp/extract_terrain_by_sections.py` - has all correct coordinates
2. Tiles are at specific positions, NOT on a regular grid
3. Key coordinates documented in the script

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
- Working scripts: Keep in temp/
- Old/experimental: Move to archive/

## Quick Reference
- Total terrain tiles: 69 extracted
- Total unit sprites: 250 in grid
- Buildings are double height (16x32)
- Use NEAREST neighbor when scaling for preview
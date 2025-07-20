# Tile Optimization Issues

## Status: DISABLED

The tile optimization system has been disabled due to palette conversion issues that corrupt terrain tiles.

## What Works
- Building sprites (HQ, Factory, Airport, Port) render correctly in the optimized tileset
- The optimization achieves 86-92% file size reduction
- The tile showcase page at `/tiles` works with legacy renderer

## The Problem
The original tilesets use palette mode ('P' mode in PIL) with indexed colors. When converting to RGBA for extraction and repacking:
1. Terrain tiles (PLAIN, WOOD, MOUNTAIN, SEA, etc.) become corrupted
2. The colors/transparency information is lost or altered
3. Buildings seem to survive the conversion but terrain doesn't

## Technical Details
- Source tilesets are in 'P' mode (palette/indexed color)
- Conversion to RGBA loses palette information
- The extracted tiles have pixels but wrong color data
- Original: `Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png` (76KB, P mode)
- Optimized: `optimized_tileset_transparent.png` (10KB, RGBA mode)

## Current Solution
The optimized tile renderer is disabled in `render_legacy.js`:
```javascript
// Try to load optimized tile renderer - DISABLED due to palette conversion issues
if (false && window.optimizedTileRenderer && !window.optimizedTileRenderer.loaded) {
```

The game uses:
- ✅ Optimized unit sprites (working, 93KB vs 370KB) 
- ✅ Legacy tile rendering (working correctly)

## Future Fix Options
1. **Preserve Palette Mode**: Extract and repack tiles while maintaining palette mode
2. **Better Conversion**: Use a more sophisticated palette-to-RGBA conversion that preserves colors
3. **Manual Color Mapping**: Create a color lookup table for proper conversion
4. **Use Original Format**: Keep tiles in original format and optimize differently

## Files Involved
- `/create_optimized_tileset.py` - Tile extraction and packing script
- `/static/js/optimized-tile-renderer.js` - Optimized renderer (disabled)
- `/static/img/optimized_tileset_*.png` - Corrupted optimized tilesets
- `/templates/tile_sprite_map.json` - Tile coordinate mappings (correct)
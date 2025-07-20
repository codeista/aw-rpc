# Terrain Upscale Fix Plan

## Issues Identified in terrain_upscaled_showcase.png

### 1. **Terrain Tiles (Plains, Woods, Mountains)**
- Lost detail and texture
- Colors appear washed out
- Hard threshold removed subtle shading

### 2. **Water Tiles**
- Shore tiles have harsh edges
- Water animation frames lost smoothness
- Color palette shifted

### 3. **Roads**
- Connection pieces have artifacts
- Diagonal roads lost smooth curves
- Some tiles appear disconnected

### 4. **Pipes**
- Connection pieces have jagged edges
- Colors too saturated
- Lost metallic sheen

### 5. **Fog Buildings**
- Too dark/muddy
- Lost detail in shadows
- Need brightness adjustment

## Proposed Solutions

### A. Tile-Specific Processing
1. **Terrain tiles** - Use nearest-neighbor upscaling to preserve pixel art style
2. **Water tiles** - Apply softer threshold to preserve gradients
3. **Roads/Pipes** - Manual cleanup of connection points
4. **Buildings** - Already look good, minor touch-ups only
5. **Fog buildings** - Brightness/contrast adjustment

### B. Alternative Upscaling Methods
1. **Pixel art scalers** (Scale2x, HQx, xBRZ)
2. **Nearest neighbor + manual enhancement**
3. **Custom processing per tile type**

### C. Quality Control
1. Compare each upscaled tile with original
2. Test in-game rendering
3. Create before/after comparison sheet

## Next Steps
1. Identify most problematic tiles
2. Test alternative upscaling methods
3. Create processing pipeline for each tile type
4. Manual touch-up where needed
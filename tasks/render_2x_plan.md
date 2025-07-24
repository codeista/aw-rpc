# Plan: Modify render.js for 32x32 Tiles

## Overview
Update the game rendering to use 2x upscaled sprites (32x32 tiles instead of 16x16).

## Key Changes Required

### 1. Constants
- `TILESIZE`: 16 → 32
- `SPRITESIZE`: 16 → 32 
- UI sizes: 8 → 16 (HP, fuel, ammo icons were 8x8, now 16x16)

### 2. Sprite Sheet Paths
- Terrain: Use `/static/img/sprites_2x/combined/terrain_tileset_2x.png`
- Units: Use `/static/img/sprites_2x/combined/units_spritesheet_2x.png`
- UI: Use `/static/img/sprites_2x/combined/ui_spritesheet_2x.png`

### 3. Coordinate System Updates
- Canvas size calculations: `board.width * 32` instead of `board.width * 16`
- Mouse coordinate mapping: Divide by 32 instead of 16
- All tile positioning: Multiply by 32 instead of 16

### 4. Sprite Coordinate Lookup
- Replace hardcoded sprite offsets with JSON map lookups
- Load JSON maps: `terrain_tileset_2x_map.json`, `units_spritesheet_2x_map.json`, `ui_spritesheet_2x_map.json`
- Use sprite names to get x,y,w,h from maps

### 5. UI Element Positioning
- HP indicators: Now 16x16 (was 8x8), adjust positioning
- Fuel/ammo warnings: Now 16x16 (was 8x8)
- Load indicators: Now 16x16 (was 8x8)

## Implementation Steps

1. **Create render_2x.js**
   - Copy current render.js
   - Update constants
   - Add JSON map loading

2. **Update drawTerrain()**
   - Use terrain_tileset_2x_map.json for coordinates
   - Remove hardcoded offset calculations
   - Use 32x32 or 32x64 sizes from map

3. **Update drawUnit()**
   - Use units_spritesheet_2x_map.json
   - Keep generateUnitTexture() for HP overlays
   - Adjust UI element positioning

4. **Update Mouse Handling**
   - canvasMove(): Adjust coordinate calculations
   - canvasClick(): Update tile coordinate mapping

5. **Update Context Menus**
   - Adjust positioning for 32px tiles

## Testing Plan
1. Load a game with new renderer
2. Verify terrain renders correctly
3. Check unit sprites and HP indicators
4. Test mouse hover and selection
5. Verify movement/attack overlays

## Risks & Mitigation
- **Risk**: Coordinate mismatch
  - **Mitigation**: Keep old renderer as fallback
- **Risk**: UI element misalignment  
  - **Mitigation**: Test each UI element type
- **Risk**: Performance impact
  - **Mitigation**: Already tested - actually improved!
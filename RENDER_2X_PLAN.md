# 2X Renderer Implementation Plan

## Goal
Create a clean rendering system for 2x upscaled sprites (32x32 tiles) using modern sprite atlas approach with JSON coordinate maps.

## Current Assets
- **Terrain**: `terrain_tileset_2x.png` (512x416) + `terrain_tileset_2x_map.json` (71 sprites)
- **Units**: `units_spritesheet_2x.png` (512x512) + `units_spritesheet_2x_map.json` (250 sprites)
- **UI**: `ui_spritesheet_2x.png` (256x128) + `ui_spritesheet_2x_map.json` (71 sprites)

## Key Differences from Old System
1. **Coordinate System**: 
   - Old: Uses center-based offsets from sprite sheet center (e.g., x = 222.5 - 8, y = 581.5 - 64)
   - New: Uses top-left corner coordinates from JSON maps (e.g., {x: 0, y: 192, w: 32, h: 32})

2. **Sprite Size**:
   - Old: 16x16 tiles, 8x8 UI elements
   - New: 32x32 tiles, 16x16 UI elements

3. **Sprite Loading**:
   - Old: Hardcoded switch statements with 450+ lines of coordinates
   - New: JSON maps with sprite names as keys

## Implementation Steps

### Step 1: Clean Slate
- Start fresh with render_2x.js
- Remove all legacy coordinate calculations
- Remove all hardcoded sprite positions

### Step 2: Core Rendering Functions
1. **initializeRenderer()** - Set up Two.js with proper canvas size
2. **loadSpriteMaps()** - Load all JSON coordinate maps
3. **drawTerrain(tile)** - Draw terrain sprites using JSON coordinates
4. **drawUnit(tile)** - Draw unit sprites with HP/status indicators
5. **drawHighlights()** - Movement/attack range highlights

### Step 3: Sprite Drawing Logic
```javascript
// Example of new approach
function drawSprite(spriteName, x, y, spriteMap, imagePath) {
    const sprite = spriteMap[spriteName];
    if (!sprite) return;
    
    const texture = new Two.Texture(imagePath);
    // Two.js expects center offset, our sprites use top-left
    texture.offset = new Two.Vector(
        -sprite.x - sprite.w/2,  // Negative because Two.js crops from center
        -sprite.y - sprite.h/2
    );
    
    const rect = two.makeRectangle(
        x * 32 + 16,  // Center of tile
        y * 32 + 16,
        sprite.w,
        sprite.h
    );
    rect.fill = texture;
    return rect;
}
```

### Step 4: Key Considerations
1. **Two.js Texture Offset**: Two.js uses center-based cropping, need to convert our top-left coordinates
2. **Double-height buildings**: Buildings are 32x64, need special positioning
3. **UI Elements**: HP numbers, fuel/ammo warnings at 16x16
4. **Performance**: Reuse textures where possible

## Benefits of New System
- Clean, maintainable code
- Easy to add new sprites (just update JSON)
- Consistent coordinate system
- No more hardcoded magic numbers
- Proper 2x scaling throughout
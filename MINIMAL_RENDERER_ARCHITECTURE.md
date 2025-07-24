# Minimal Renderer Architecture

## Overview
The minimal renderer (`minimal_game.js`) is a clean, simplified implementation of the Advance Wars game renderer. It focuses on essential functionality without legacy code complexity.

## Architecture

### 1. Class Structure
```javascript
class Game {
    constructor()    // Initialize canvas, load sprites, setup handlers
    init()          // Async initialization
    loadSprites()   // Load all sprite sheets and maps
    setupSocket()   // WebSocket connection for real-time updates
    setupInput()    // Mouse and keyboard event handlers
    render()        // Main rendering loop
}
```

### 2. Sprite System

#### Sprite Organization
- **Terrain**: `/sprites_2x/combined/terrain_tileset_2x.png`
- **Units**: `/sprites_2x/combined/units_spritesheet_2x.png`
- **UI**: `/sprites_2x/combined/ui_spritesheet_2x.png`

Each sprite sheet has a corresponding JSON map with coordinates:
```json
{
  "SPRITE_NAME": {
    "x": 100,           // Left position in sprite sheet
    "y": 200,           // Bottom position (not top!)
    "w": 32,            // Width
    "h": 32,            // Standard height
    "full_height": 64   // Actual height for tall sprites
  }
}
```

#### Coordinate System
- **Important**: Y coordinate marks the BOTTOM of sprites
- Tall sprites (buildings, mountains) use `full_height` property
- Standard tiles are 32x32, buildings can be up to 64px tall

### 3. Rendering Pipeline

#### Three-Pass Rendering System

**Pass 1: Non-tall terrain**
```javascript
// Draw all basic terrain (roads, plains, water, etc.)
// Skip tall objects to be drawn later
```

**Pass 2: Tall objects (top-to-bottom)**
```javascript
// Draw tall terrain and buildings from top to bottom
// This allows lower tiles to overlap upper tiles correctly
const tallTypes = ['CITY', 'FACTORY', 'AIRPORT', 'PORT', 'HQ', 
                   'BASE_TOWER_0', 'BASE_TOWER_1', 'BASE_TOWER_2', 
                   'BASE_TOWER_3', 'BASE_TOWER_4', 'MOUNTAIN', 'WOOD'];
```

**Pass 3: Units and UI**
```javascript
// Draw movement highlights
// Draw units with HP indicators
// Draw selection box
```

### 4. Sprite Drawing

#### Basic Sprite Drawing
```javascript
drawSprite(type, name, x, y) {
    const sprite = this.sprites[type].data[name];
    
    // For terrain with tall sprites
    if (type === 'terrain' && sprite.full_height) {
        const sourceY = sprite.y - sprite.full_height;  // Top of sprite
        const drawY = y - (sprite.full_height - this.tileSize);
        
        this.ctx.drawImage(
            this.sprites[type].img,
            sprite.x, sourceY, sprite.w, sprite.full_height,
            x, drawY, sprite.w, sprite.full_height
        );
    }
}
```

### 5. Input Handling

#### Click Handling Logic
1. If unit selected → Try move
2. If move fails → Try attack
3. If attack fails → New selection

#### Right-Click Production
- Detects production buildings (FACTORY, AIRPORT, PORT)
- Shows production menu modal
- Creates units via RPC call

### 6. RPC Communication

All game actions use JSON-RPC:
```javascript
async rpc(method, params = {}) {
    const response = await fetch('/api', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            jsonrpc: '2.0',
            method: method,
            params: { token: TOKEN, ...params },
            id: Date.now().toString()
        })
    });
}
```

Methods used:
- `game_board` - Get current game state
- `unit_select` - Select a unit
- `unit_move` - Move selected unit
- `unit_attack_enhanced` - Attack with unit
- `get_production_options` - Get available units to build
- `unit_create` - Create new unit
- `army_end_turn` - End current turn

### 7. Performance Optimizations

1. **Background Optimization**: Uses green fill for plains instead of drawing every tile
2. **Canvas State**: Only updates size when needed
3. **Sprite Caching**: Loads all sprites once at startup
4. **Minimal Redraws**: Only renders when state changes

### 8. Key Fixes Applied

1. **Tall Sprite Rendering**: Proper overlap by rendering top-to-bottom
2. **HQ Support**: Added BASE_TOWER_0-4 recognition
3. **Beach Tile Fix**: Swapped BEACH_N and BEACH_W (temporary fix)
4. **Sprite Spacing**: 4px gaps prevent bleed-over

## File Structure

```
/static/
  /js/
    minimal_game.js      # Main renderer
  /img/sprites_2x/
    /combined/
      terrain_tileset_2x.png      # All terrain sprites
      terrain_tileset_2x_map.json # Terrain coordinates
      units_spritesheet_2x.png    # All unit sprites  
      units_spritesheet_2x_map.json
      ui_spritesheet_2x.png       # UI elements
      ui_spritesheet_2x_map.json
```

## Future Improvements

1. Fix beach tile orientation properly
2. Add animation frame support
3. Implement fog of war rendering
4. Add particle effects
5. Optimize sprite batching
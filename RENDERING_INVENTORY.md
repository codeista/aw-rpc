# Comprehensive Rendering Systems Inventory

## JavaScript Renderer Files

### Active/Main Renderers
1. **`/static/js/render.js`** - ACTIVE
   - Main game renderer using Two.js
   - Uses canvas type rendering
   - Routes: `/game/<token>`
   - Template: `render.html`

2. **`/static/js/render_2x.js`** - ACTIVE (2x scaling version)
   - 2x scaled version of the renderer
   - Uses Two.js
   - Routes: `/game2x/<token>`
   - Template: `render_2x.html`

### Legacy/Alternative Renderers
3. **`/static/js/render_legacy.js`**
   - Legacy renderer with optimized tile renderer disabled
   - Contains fixes from 2025-07-20

4. **`/static/js/render_final.js`**
   - Alternative final version (status unclear)

5. **`/static/js/render_modular.js`**
   - Modularized version (likely experimental)
   - Template: `render_modular.html`

6. **`/static/js/render_2x_clean.js`**
   - Clean version of 2x renderer

### Optimization Systems
7. **`/static/js/optimized-sprite-renderer.js`**
   - Optimized sprite rendering system
   - Used for unit sprites

8. **`/static/js/optimized-tile-renderer.js`**
   - Optimized tile rendering system
   - Currently DISABLED due to palette corruption issues

### Module Systems
9. **`/static/js/modules/renderEngine.js`**
   - Modular render engine component

10. **`/static/js/modules/movementSystem.js`**
    - Movement system with Two.js integration

### Support Files
- `/static/js/two.min.js` - Two.js library
- `/static/js/click-handler.js` - Click handling with Two.js references
- `/static/js/animation-system.js` - Animation system
- `/static/js/animation-integration.js` - Animation integration
- `/static/js/transport_integration.js` - Transport system integration

## HTML Templates

### Active Templates
1. **`/templates/render.html`** - ACTIVE
   - Main game template
   - Used by `/game/<token>` route

2. **`/templates/render_2x.html`** - ACTIVE
   - 2x scaled game template
   - Used by `/game2x/<token>` route

### Backup/Alternative Templates
3. **`/templates/render_backup.html`**
   - Backup of render.html

4. **`/templates/render_modular.html`**
   - Template for modular renderer

### Test Templates
5. **`/test_2x_render.html`**
   - Test file for 2x rendering

6. **`/temp/test_2x_terrain_rendering.html`**
   - Temporary test for terrain rendering

7. **`/templates/test_clean_2x.html`**
   - Clean 2x test template with Two.js

8. **`/static/test_single_tile.html`**
   - Single tile test with Two.js

## Sprite Sheets and Image Assets

### Currently Active Sprite Sheets

#### Terrain Tileset
- **PRIMARY**: `/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png`
  - AWDS tileset with transparency
  - Coordinate map: `/static/img/optimized_tileset_map.json`

#### Unit Sprites
- **PRIMARY**: `/static/img/units_sprite_sheet_complete.png`
  - Complete optimized unit sprite sheet (58KB)
  - Coordinate map: `/static/img/units_sprite_map_complete.json`

### Alternative/Backup Sprite Sheets

#### In `/static/img/backup_tilesets_20250718_142606/`
- Various backup versions of tilesets
- Old unit sprite sheets (v2, 16x16 versions)
- Alternative tileset mappings

#### 2x Scaled Assets in `/static/img/sprites_2x/`
- **Terrain**: Individual 32x32 PNG files for each terrain type
- **Units**: Individual 32x32 PNG files for each unit
- **UI Elements**: Status icons, HP numbers, etc.
- **Combined Sheets**:
  - `terrain_tileset_2x_complete.png` with mapping
  - `units_spritesheet_2x.png` with mapping
  - `ui_spritesheet_2x.png` with mapping

### Special Units
- Located in `/static/img/special-units/`
- Contains GIF animations and PNG sprites for special units

## Two.js Integration

Two.js is used in the following files:
- Main renderers (render.js, render_2x.js)
- Modular components
- Animation systems
- Movement systems
- Click handlers

The library file is at `/static/js/two.min.js`

## Active vs Deprecated Systems

### ACTIVE
1. **Main Game Renderer**
   - Route: `/game/<token>`
   - Files: `render.js` + `render.html`
   - Uses Two.js for canvas rendering

2. **2x Scaled Renderer**
   - Route: `/game2x/<token>`
   - Files: `render_2x.js` + `render_2x.html`
   - Uses Two.js with 2x scaling

3. **Sprite Sheets**
   - Units: `units_sprite_sheet_complete.png`
   - Terrain: `Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png`

### DEPRECATED/DISABLED
1. **Optimized Tile Renderer**
   - Status: DISABLED (palette corruption issues)
   - Would use optimized terrain tiles if enabled

2. **Old Unit Sprite Sheets**
   - `units_sprite_sheet_v2.png` - DO NOT USE
   - `units_sprite_sheet_16x16.png` - DO NOT USE

3. **AW2 RGB Tileset**
   - "Game Boy Advance - Advance Wars 2..." - Problematic, not in use

### EXPERIMENTAL/UNCLEAR
1. **Modular Renderer** (`render_modular.js`)
2. **Final Renderer** (`render_final.js`)
3. **Legacy Renderer** (`render_legacy.js`) - Contains recent fixes

## Key Findings

1. **Two.js is deeply integrated** - Used throughout the rendering system
2. **Multiple renderer versions exist** - Main, 2x, modular, final, legacy
3. **2x scaling system** has both combined sprite sheets and individual files
4. **Optimized tile renderer is disabled** due to palette issues
5. **Clear active vs deprecated distinction** for sprite sheets per SPRITE_SHEET_CONFUSION.md

## Recommendations for Cleanup

1. Consider removing truly deprecated files after verification
2. Consolidate test files to a dedicated test directory
3. Document the purpose of experimental renderers
4. Consider removing old sprite sheet versions from main directories
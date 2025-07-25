## ADVANCE WARS RPC - GAME ENGINE

This is a complete implementation of Advance Wars as a web-based RPC game. Key systems:

### Core Game Rules
- **Turn-based strategy**: Players take turns moving units and capturing properties
- **Unit creation**: Units cannot move on the turn they are created (standard AW rule)
- **One action per turn**: Units can move OR attack, not both in same turn
- **Income**: 1000 funds per property owned, distributed at turn start
- **Victory**: HQ capture, elimination, or property control

### Important Game Mechanics
1. **Transport System**
   - Units move INTO transports to board (not picked up)
   - Unloaded units cannot act same turn
   - APCs auto-resupply adjacent units
   - Black Boats can repair (manual command, 2HP max)

2. **Combat System**
   - Damage based on unit matchups + terrain defense
   - Counter-attacks if defender survives and in range
   - HP affects damage output

3. **Testing**
   - Use `game_create_test` RPC for high starting funds (50k)
   - `game_create` is deprecated, redirects to `game_create_v2`
   - `game_create_v2` is the primary method with player configuration
   - Game mechanics docs in archive/documentation/GAME_MECHANICS.md

### Code Architecture
- `manager.py` - Core game logic
- `transport_system.py` - All transport mechanics
- `app.py` - RPC endpoints and server
- `render.js` - Frontend game rendering

### Tileset System  
- **Current tileset**: AWDS tileset (reverted from AW2 RGB due to rendering issues)
- **Working tileset**: `/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png`
- **Optimized tiles DISABLED**: Palette conversion corrupts terrain tiles (see TILE_OPTIMIZATION_ISSUES.md)

### Sprite System (2025-07-24)
- **Terrain sprites**: Individual 2x sprites in `/static/img/sprites_2x/terrain/`
- **Combined sprite sheets**: `/static/img/sprites_2x/combined/`
  - `terrain_tileset_2x.png` + `terrain_tileset_2x_map.json` (minimal_game.js)
  - `terrain_tileset_2x_final.png` + `terrain_tileset_2x_final_map.json` (game_v2.js)
  - `units_spritesheet_2x.png` + `units_spritesheet_2x_map.json`
  - `ui_spritesheet_2x.png` + `ui_spritesheet_2x_map.json`
- **Sprite naming**: HQ sprites renamed from HQ_VARIANT_X to BASE_TOWER_X
- **Sprite spacing**: 4px between sprites to prevent overlap
- **Coordinate system**: Y marks BOTTOM of sprite (important for tall buildings)

## RECENT SPRITE SYSTEM FIXES (2025-07-24)

### Changes Made
1. **Created Combined Sprite Sheets**
   - Previously game was looking for files in `/sprites_2x/combined/` but directory was empty
   - Combined 199 terrain sprites from individual files with proper spacing
   - Created unit spritesheet with 250 sprites
   - Created placeholder UI spritesheet

2. **Fixed Sprite Naming**
   - Renamed HQ_VARIANT_X → BASE_TOWER_X in sprite maps
   - Applied road mappings (ROAD_T_N → NESRoad, etc.)
   - Fixed MISSILE_SILO_EMPTY → EMPTY_SILO

3. **Known Issues to Fix**
   - Beach/water tile mappings still use numbered format (need directional names)
   - UI sprites are placeholders (need proper HP number graphics)
   - Some sprites may need position adjustments

## RECENT FIXES (2025-07-20)

### UI/UX Fixes Applied
1. **Mouse Hover Jumping** - Fixed null reference errors in canvasMove()
2. **Circular JSON Error** - Fixed JSON.stringify issue with board object
3. **Tile Info Display** - Hover now correctly shows tile information
4. **Production Menu** - API returns correct data structure
5. **Movement System** - Correctly enforces "no move on creation turn" rule

### Selenium Testing Results
- ✅ Canvas renders at correct size (192x176 for 12x10 map)
- ✅ Hover info updates correctly
- ✅ No critical JavaScript errors
- ✅ All game elements visible and positioned correctly
- ✅ Turn/Day/Funds information displays properly

## RECENT RENDERING FIXES (2025-07-20)

### Issues Fixed
1. **JavaScript Syntax Errors**
   - Fixed all `window.window.` typos → `window.` in render_legacy.js
   - Total: 6 instances corrected

2. **Corrupted Optimized Tile Renderer**
   - Disabled with `if (false && window.optimizedTileRenderer...` 
   - Issue: Palette mode (P) to RGBA conversion corrupted terrain tiles
   - Buildings rendered OK but terrain tiles lost color data

3. **Wrong Default Tileset**
   - Changed from problematic AW2 RGB tileset back to AWDS tileset
   - Function: `getSelectedTerrainTileset()` in render_legacy.js

### Current Status
- ✅ Full map displays (was only showing top 5 of 10 rows)
- ✅ Units appear when created
- ✅ No rendering crashes
- ✅ Legacy tile renderer with AWDS tileset
- ✅ Optimized unit sprites still work (93KB vs 370KB)

### Recent Code Fixes (2025-07-25)
1. **API Consolidation** - Reduced 58 API methods to 23 core methods (60% reduction)
   - Transport API: 20→5 methods with auto-loading support
   - Combat API: 7→4 methods using enhanced versions
   - Movement API: 8→4 methods with simplified interface
   - Added 7 new UI features (repair, resupply, capture, etc.)
2. **HP Sprite Display** - Fixed sprite mapping where HP indicators showed wrong icons
   - Reordered sprite coordinates: status icons first, then numbers 1-9
3. **V2 Migration** - Added GameFactory and SpriteMapper for v2 player system
4. **Documentation** - Added API_BEST_PRACTICES.md and API_QUICK_REFERENCE.md

## STANDARD WORKFLOW
1. First think through the problem, read the codebase for relevant files and write a plan to tasks/todo.md. 
2. the plan should have a list of todo items that can be checked off as we go.
3. before you begin working check in with me and I will verify the plan.
4. then begin working on the todo items checking them off as we go.
5. every step of the way give me a high level explanation of the changes made.
6. make every task and code change as simple as possible reusing current methods, system files and configs if relevant.
7. add a review section to the todo.md file with a summary of changes and relevant info.

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

## CRITICAL SAFETY RULES
**NEVER use `rm` or delete files without explicit user permission** (see CLAUDE_HOOKS.md)
- Always ask before deleting ANY file
- Exception: Can clean up files just created if there was an error
- Use backups/renames instead of deletion when possible

## Development Reminders
- Always check current docs for info on game mechanics and API methods
- Please test before committing and pushing
- **Use temp/ folder for temporary analysis files**
- **Clean up test/verification files after use**
- **Current tileset work**: Replacing old center-based coordinate system with new direct coordinates

## Helper Documentation Locations
- Core game logic and rules: `manager.py`
- Transport mechanics: `transport_system.py`
- RPC endpoints: `app.py`
- Frontend rendering: `render.js`
- Tile optimization issues: `TILE_OPTIMIZATION_ISSUES.md`
- Game mechanics details: `archive/documentation/GAME_MECHANICS.md`

## Key Documentation Files
- **[README.md](README.md)** - Project overview, setup instructions, API reference
- **[SPRITE_SHEET_CONFUSION.md](SPRITE_SHEET_CONFUSION.md)** - IMPORTANT: Which sprite sheets are actually used
- **[TESTING.md](TESTING.md)** - Testing documentation
- **[movement-fog.txt](movement-fog.txt)** - Movement and fog of war mechanics

## Sprite System Documentation
- **CRITICAL**: The game uses `units_sprite_sheet_complete.png` for units (NOT v2!)
- **TERRAIN**: Uses `Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png`
- **Unit Coordinates**: `units_sprite_map_complete.json` (was missing from static/img, now restored)
- **Terrain Coordinates**: `optimized_tileset_map.json`
- See SPRITE_SHEET_CONFUSION.md for full details on which files to use

## Testing Documentation
- **Run Tests**: `python3 run_tests.py` - Runs click handler and sprite extraction tests
- **Regression Tests**: `python3 run_regression_tests.py` - Comprehensive mechanics validation
- **Test Interface**: http://localhost:5000/test_interface - Interactive testing UI

## API Documentation
- **API Docs**: http://localhost:5000/api/docs - Categorized API reference
- **API Browser**: http://localhost:5000/api/browse - Interactive RPC testing
- **RPC Methods**: See README.md for complete list of 60+ RPC methods
- RPC endpoints: `app.py`
- Frontend rendering: `render.js`
- **Sprite and tile guide: `SPRITE_AND_TILE_GUIDE.md`** (consolidated guide)
- Game mechanics details: `GAME_MECHANICS.md`

## Key Documentation Files
- **[README.md](README.md)** - Project overview, setup instructions, API reference
- **[SPRITE_AND_TILE_GUIDE.md](SPRITE_AND_TILE_GUIDE.md)** - Complete sprite/tile extraction and upscaling guide
- **[TESTING.md](TESTING.md)** - Testing documentation
- **[movement-fog.txt](movement-fog.txt)** - Movement and fog of war mechanics

## Sprite System
- See **[SPRITE_AND_TILE_GUIDE.md](SPRITE_AND_TILE_GUIDE.md)** for complete details on:
  - Which sprite sheets to use
  - Extraction coordinates and scripts
  - Upscaling approach for pixel art
  - PNG palette mode handling

## 2X Sprite System (CURRENT - 2025-07-24)
- **UNITS**: `sprites_2x/combined/units_spritesheet_2x.png` with `units_spritesheet_2x_map.json`
  - 250 unit sprites from all categories (infantry, vehicles, tanks, air, naval, special)
  - Format: `UNITTYPE_ARMY_state_frame` (e.g., `TANK_RED_idle_0`)
- **TERRAIN**: `sprites_2x/combined/terrain_tileset_2x.png` with `terrain_tileset_2x_map.json`
  - 199 terrain sprites with proper 4px spacing
  - Includes all terrain, buildings, roads, water, pipes
  - HQ sprites renamed: HQ_VARIANT_X → BASE_TOWER_X
  - Tall sprites use 'full_height' property for proper rendering
- **UI ELEMENTS**: `sprites_2x/combined/ui_spritesheet_2x.png` with `ui_spritesheet_2x_map.json`
  - Placeholder HP numbers (needs proper graphics)
  - Format: `hp_N` for normal, `hp_ARMY_N` for team colors

### 2X Sprite Naming Conventions
**IMPORTANT**: The game expects exact sprite names. The 2x system uses these naming rules:
- **Simple terrain**: Direct names like `SEA`, `PLAIN`, `MOUNTAIN`, `REEF`, `WOOD`
- **Roads**: `ROAD_HORT`, `ROAD_VERT`, and corner/junction variants
- **Rivers**: `RIVER_HORT`, `RIVER_VERT`, `RIVER_NW`, `RIVER_NE`, etc.
- **Beaches**: Direction-based like `BEACH_N`, `BEACH_E`, `BEACH_NW`, etc.
- **Buildings**: Army prefix for owned buildings (e.g., `RED_CITY`, `BLUE_FACTORY`)
- **HQ/Base**: Now called `BASE_TOWER_0` through `BASE_TOWER_4` (not HQ_VARIANT)
- **Special**: Some tiles like `EMPTY_SILO` have been renamed from originals

Total renamed sprites: 71 (including SEA variants, river directions, HQ→BASE_TOWER, road directions, etc.)

When verifying sprite coverage, always check against the complete MapType enum in map_system.py (63 types total).

## Important Rendering Notes
- **Sprite Overlap**: Many sprites (buildings, mountains, woods) extend above their base tile
- **Drawing Order**: Render tiles top-to-bottom so lower tiles can overlap upper ones
- **Coordinate System**: Double-height buildings are referenced by their bottom tile
- **Renderer**: Must check 'full_height' property in terrain map for proper overlap rendering

## Testing Documentation
- **Run Tests**: `python3 run_tests.py` - Runs click handler and sprite extraction tests
- **Regression Tests**: `python3 run_regression_tests.py` - Comprehensive mechanics validation
- **Test Interface**: http://localhost:5000/test_interface - Interactive testing UI

## API Documentation
- **API Docs**: http://localhost:5000/api/docs - Categorized API reference
- **API Browser**: http://localhost:5000/api/browse - Interactive RPC testing
- **RPC Methods**: See README.md for complete list of 60+ RPC methods
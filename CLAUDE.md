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
   - Regular `game_create` only gives 5k funds
   - Check GAME_MECHANICS.md for detailed rules

### Code Architecture
- `manager.py` - Core game logic
- `transport_system.py` - All transport mechanics
- `app.py` - RPC endpoints and server
- `render.js` - Frontend game rendering

### Tileset System  
- **Current tileset**: AWDS tileset (reverted from AW2 RGB due to rendering issues)
- **Working tileset**: `/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png`
- **Optimized tiles DISABLED**: Palette conversion corrupts terrain tiles (see TILE_OPTIMIZATION_ISSUES.md)

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

### Known Issues
1. ~~**Logger Error on End Turn**~~ ✅ FIXED - Added null checks in manager.py
2. ~~**Missing sprite files**~~ ✅ FIXED - Restored units_sprite_sheet_v2.png and aw2_blackhole_units_map_transparent.png from backup
3. ~~**Circular JSON Error**~~ ✅ FIXED - Fixed JSON.stringify circular reference in render_legacy.js
4. ~~**Mouse hover null errors**~~ ✅ FIXED - Added proper null checks in canvasMove function

### How to Test Rendering
```bash
# Start server
nohup python app.py > /tmp/game_server.log 2>&1 &

# Run test
python temp/test_rendering_fixes.py
```
Should show:
- ✅ Board Dimensions (12x10, all rows visible)  
- ✅ Unit Creation (units appear)
- ❌ End Turn (logger error, not rendering issue)

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
- Game mechanics details: `GAME_MECHANICS.md`
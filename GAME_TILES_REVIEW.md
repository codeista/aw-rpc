# Game Tiles Review

## Current Tiles Used in Game

Based on analysis of `map_system.py` and `render.js`, here are all the tiles currently implemented in the game:

### 1. Basic Terrain (5 tiles)
- PLAIN
- WOOD
- MOUNTAIN
- SEA
- REEF

### 2. Roads (11 tiles)
- ROAD_HORT (horizontal)
- ROAD_VERT (vertical)
- ROAD_NW, ROAD_NE, ROAD_SE, ROAD_SW (corners)
- SWNRoad, NESRoad, WNERoad, ESWRoad (T-junctions)
- CRoad (cross/center)

### 3. Rivers (10 tiles)
- RIVER_HORT (horizontal)
- RIVER_VERT (vertical)
- RIVER_NW, RIVER_NE, RIVER_SE, RIVER_SW (corners)
- SWNRiver, NESRiver, WNERiver, ESWRiver (T-junctions)

### 4. Beaches (12 tiles)
- BEACH_N, BEACH_E, BEACH_S, BEACH_W (straight edges)
- BEACH_NW, BEACH_NE, BEACH_SE, BEACH_SW (corners)
- BEACH_END_N, BEACH_END_E, BEACH_END_S, BEACH_END_W (end pieces)

### 5. Pipes (10 tiles)
- PIPE_HORT (horizontal)
- PIPE_VERT (vertical)
- PIPE_END_N, PIPE_END_E, PIPE_END_S, PIPE_END_W (end pieces)
- PIPE_END_NW, PIPE_END_NE, PIPE_END_SE, PIPE_END_SW (corner ends)

### 6. Buildings (13 tiles × 6 army variations)
Buildings can be neutral or owned by 5 armies (RED, BLUE, GREEN, YELLOW, GREY):
- BASE_TOWER_0 through BASE_TOWER_4 (HQ variations)
- CITY
- FACTORY
- AIRPORT
- PORT
- COM_TOWER
- LAB
- MISSILE_SILO
- EMPTY_SILO (always neutral)

### 7. Bridges (2 tiles)
- HBridge (horizontal)
- VBridge (vertical)

## Total Tile Count
- **Terrain tiles**: 64 unique types
- **With army variations**: ~138 tiles (13 buildings × 6 states + other tiles)

## Rendering Details from render.js

### Tile Coordinates
The render.js file contains exact pixel coordinates for each tile type in the tileset:
- Uses offset calculations from base coordinates
- Buildings have different Y-offsets per army color
- All tiles are 16×16 pixels (except buildings which are 16×32)

### Special Rendering Rules
1. **Base Layer**: Buildings and mountains render a PLAIN tile underneath
2. **Army Colors**: 
   - RED: Base Y coordinates
   - BLUE: Different Y offset (usually +33-35px from RED)
   - GREEN: Different Y offset (usually +70px from RED)
   - YELLOW: Different Y offset (usually +105px from RED)
   - GREY: Different Y offset (usually +140px from RED)

### Tileset Files
The game supports multiple tilesets:
- `/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png` (default)
- `/static/img/Advance_Wars_Dual_Strike_Tileset_Normal.png`
- `/static/img/aw2_blackhole_tileset_normal_transparent.png`
- `/static/img/aw2_blackhole_tileset_normal.png`

## Units (Not Tiles)
Units are rendered separately and include:
- Infantry: INFANTRY, MECH
- Vehicles: RECON, APC, ANTIAIR, ARTILLERY, MISSILE, ROCKET
- Tanks: TANK, MEDIUMTANK, NEOTANK, MEGATANK
- Air: FIGHTER, BOMBER, BCOPTER, TCOPTER, STEALTH
- Naval: BATTLESHIP, CRUISER, LANDER, SUB, CARRIER, BLACKBOAT
- Special: PIPERUNNER, BLACKBOMB

## Next Steps
1. Compare this list with our extracted tiles to ensure we have everything
2. Verify the exact coordinates match between render.js and our extraction
3. Test integration of upscaled tiles with these exact tile types
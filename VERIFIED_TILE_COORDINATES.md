# Verified Tile Coordinates for AW-RPC

## Tileset Information
- File: `Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png`
- Size: 445×1163 pixels
- Tile size: 16×16 (terrain), 16×32 (buildings)
- Spacing: 17 pixels (16px tile + 1px separator)

## Building Coordinates

### Building X-Coordinates (All Rows)
All rows (armies, neutral, fog) have the same x-coordinate pattern:

| Building | X Coordinate |
|----------|-------------|
| HQ_VARIANT_0 | 1 |
| HQ_VARIANT_1 | 18 |
| HQ_VARIANT_2 | 35 |
| HQ_VARIANT_3 | 52 |
| HQ_VARIANT_4 | 69 |
| CITY | 86 |
| FACTORY | 103 |
| AIRPORT | 120 |
| PORT | 137 |
| COM_TOWER | 154 |
| LAB | 171 |
| MISSILE_SILO | 188 |
| MISSILE_SILO_EMPTY | 205 |

Note: Army rows only have buildings up to LAB. Neutral and Fog rows also have MISSILE_SILO and MISSILE_SILO_EMPTY.

### Army Y Coordinates
| Army | Y Coordinate |
|------|-------------|
| RED | 803 |
| BLUE | 836 |
| GREEN | 869 |
| YELLOW | 902 |
| GREY | 935 |

### Neutral Row (y=757)
Uses the same x-coordinates as all other rows (see table above).

## Terrain Coordinates

| Terrain | Coordinates | Size |
|---------|-------------|------|
| PLAIN | (8, 64) | 16x16 |
| PLAIN_var1 | (25, 64) | 16x16 |
| WOOD | (352, 48) | 16x32 |
| MOUNTAIN | (25, 31) | 16x32 |
| REEF | (195, 145) | 16x16 |

Note: PORT is a building, not terrain. RUINS do not exist as a tile.

## Road Coordinates

Starting position: (42, 13) with 17px spacing

| Road Type | Coordinates |
|-----------|-------------|
| ROAD_NW | (42, 13) |
| ROAD_T_N | (59, 13) |
| ROAD_NE | (76, 13) |
| ROAD_T_W | (42, 30) |
| ROAD_CROSS | (59, 30) |
| ROAD_T_E | (76, 30) |
| ROAD_SW | (42, 47) |
| ROAD_T_S | (59, 47) |
| ROAD_SE | (76, 47) |
| ROAD_HORT_PLAIN | (42, 64) |
| ROAD_VERT_PLAIN | (59, 64) |
| ROAD_HORT_PLAIN2 | (76, 64) |

## Pipe Coordinates

Starting position: (144, 13) with 17px spacing
Grid: 4 rows × 5 columns

| Pipe Type | Coordinates |
|-----------|-------------|
| PIPE_SPECIAL | (144, 13) |
| PIPE_CIRCLE_TL | (144, 30) |
| PIPE_CIRCLE_TR | (161, 30) |
| PIPE_END_N | (178, 30) |
| PIPE_HORT | (195, 30) |
| PIPE_VERT | (212, 30) |
| PIPE_CIRCLE_BL | (144, 47) |
| PIPE_CIRCLE_BR | (161, 47) |
| PIPE_END_S | (178, 47) |
| PIPE_SEAM_WE | (195, 47) |
| PIPE_SEAM_NS | (212, 47) |
| PIPE_END_W | (144, 64) |
| PIPE_END_E | (161, 64) |
| PIPE_BROKEN_WE | (195, 64) |
| PIPE_BROKEN_NS | (212, 64) |

## Water Coordinates

Starting position: (8, 94)

### Sea Tiles
- Start: (8, 94)
- 12 columns × 4 rows = 48 tiles
- 17px spacing horizontally and vertically

### Beach Tiles  
- Start: (214, 94) (after 3px gap from sea)
- 9 columns × 4 rows = 36 tiles
- 17px spacing horizontally and vertically

### River Tiles
- Start: (369, 94) (after 3px gap from beach)
- 4 columns × 4 rows - 1 blank at (3,3) = 15 tiles
- 17px spacing horizontally and vertically

## Fog of War
Fog tiles use a +372 pixel Y offset from their regular counterparts.

### Fog Buildings
Fog buildings are at y=1129 (757 + 372) and use x-coordinates + 2 pixels from the standard positions.
See building x-coordinate table above for base positions.

### Fog Terrain/Roads/Pipes
Use same x-coordinates as regular tiles, but add 372 to y-coordinate.

## Important Notes
1. Most buildings are 16×32 pixels (double height)
2. EXCEPTION: FACTORY buildings for colored armies are 16×16 (bottom half only)
3. Terrain/roads/pipes are 16×16 pixels
4. There's a 1-pixel separator between tiles (17px spacing)
5. Fog buildings have a +2px x-offset from neutral buildings
6. GREY army is at y=935 (not 936)
7. No BLACK army exists - only 5 colors
8. Neutral buildings use white color (not grey)
9. Army FACTORY tiles are extracted from coordinates (x, y+16) with 16×16 size
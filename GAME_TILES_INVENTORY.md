# Game Tiles Inventory

## MapType Enum from map_system.py

### Terrain Types (Basic)
- **PLAIN** = 0
- **WOOD** = 100
- **MOUNTAIN** = 500
- **REEF** = 1001
- **SEA** = 800

### Road Types
- **ROAD_HORT** = 200 (Horizontal)
- **ROAD_VERT** = 201 (Vertical)
- **ROAD_NW** = 202 (Northwest corner)
- **ROAD_NE** = 203 (Northeast corner)
- **ROAD_SE** = 204 (Southeast corner)
- **ROAD_SW** = 205 (Southwest corner)
- **SWNRoad** = 206
- **NESRoad** = 207
- **WNERoad** = 208
- **ESWRoad** = 209
- **CRoad** = 210 (Cross/Center)

### River Types
- **RIVER_HORT** = 300 (Horizontal)
- **RIVER_VERT** = 301 (Vertical)
- **RIVER_NW** = 302
- **RIVER_NE** = 303
- **RIVER_SE** = 304
- **RIVER_SW** = 305
- **SWNRiver** = 306
- **NESRiver** = 307
- **WNERiver** = 308
- **ESWRiver** = 309

### Beach Types
- **BEACH_N** = 400 (North)
- **BEACH_E** = 401 (East)
- **BEACH_S** = 402 (South)
- **BEACH_W** = 403 (West)
- **BEACH_NW** = 404
- **BEACH_NE** = 405
- **BEACH_SE** = 406
- **BEACH_SW** = 407
- **BEACH_END_N** = 408
- **BEACH_END_E** = 409
- **BEACH_END_S** = 410
- **BEACH_END_W** = 411

### Pipe Types
- **PIPE_HORT** = 600 (Horizontal)
- **PIPE_VERT** = 601 (Vertical)
- **PIPE_END_NW** = 602
- **PIPE_END_NE** = 603
- **PIPE_END_SE** = 604
- **PIPE_END_SW** = 605
- **PIPE_END_N** = 606
- **PIPE_END_E** = 607
- **PIPE_END_S** = 608
- **PIPE_END_W** = 609

### Building/Property Types
- **BASE_TOWER_0** = 700
- **BASE_TOWER_1** = 701
- **BASE_TOWER_2** = 702
- **BASE_TOWER_3** = 703
- **BASE_TOWER_4** = 704
- **CITY** = 705
- **FACTORY** = 706
- **AIRPORT** = 707
- **PORT** = 708
- **COM_TOWER** = 709
- **LAB** = 710
- **MISSILE_SILO** = 711
- **EMPTY_SILO** = 712

### Bridge Types
- **HBridge** = 900 (Horizontal Bridge)
- **VBridge** = 901 (Vertical Bridge)

## Summary

### Total Tile Types: 64

### Categories:
- **Basic Terrain**: 5 types
- **Roads**: 11 types
- **Rivers**: 10 types
- **Beaches**: 12 types
- **Pipes**: 10 types
- **Buildings**: 13 types
- **Bridges**: 2 types
- **Water**: 1 type (SEA)

### Special Properties:
- **Capturable Buildings**: CITY, FACTORY, BASE_TOWER_*, COM_TOWER, PORT, AIRPORT, LAB, MISSILE_SILO
- **Ground Repair**: CITY, FACTORY, BASE_TOWER_*
- **Air Repair**: AIRPORT
- **Sea Repair**: PORT

### Army-Specific Buildings:
Buildings can be owned by armies (RED, BLUE, GREEN, YELLOW, GREY) or be neutral. In map definitions, they're specified as:
- `FACTORY:RED` - Red factory
- `CITY:BLUE` - Blue city
- `CITY` - Neutral city
- etc.

### Notes:
1. The enum values appear to group related tiles:
   - 0-99: Basic terrain
   - 100-199: Woods
   - 200-299: Roads
   - 300-399: Rivers
   - 400-499: Beaches
   - 500-599: Mountains
   - 600-699: Pipes
   - 700-799: Buildings
   - 800-899: Water
   - 900-999: Bridges
   - 1000+: Special (REEF)

2. The game uses these MapType values directly in map definitions, often with army prefixes for buildings.

3. Units are NOT part of the MapType enum - they're handled separately as entities on top of the terrain.
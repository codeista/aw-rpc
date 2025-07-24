# Terrain Tileset Creation Plan

## Overview
Create a new terrain tileset from individual 2x sprites following the exact naming conventions from SPRITE_EXTRACTION_FINAL.md and matching the MapType enum in map_system.py. This tileset will only include currently supported sprites (no fog variants).

## Step-by-Step Plan

### 1. Sprite Name Mapping
Based on SPRITE_EXTRACTION_FINAL.md, the game expects these exact names:

#### Basic Terrain (16x16 → 32x32)
- `PLAIN` - from `terrain/PLAIN_0_0.png` or `terrain/PLAIN.png`
- `WOOD` - from `terrain/WOOD.png` (32x64 tall)
- `MOUNTAIN` - from `terrain/MOUNTAIN.png` (32x64 tall)
- `REEF` - from `terrain/REEF.png`
- `WATER` - need to determine which water sprite

#### Roads (32x32)
- `ROAD_HORT` - horizontal road
- `ROAD_VERT` - vertical road
- `ROAD_NW`, `ROAD_NE`, `ROAD_SE`, `ROAD_SW` - corners
- `SWNRoad`, `ESWRoad`, `WNERoad`, `NESRoad` - T-junctions
- `CRoad` - crossroad

#### Buildings (32x64 tall)
**Neutral (white) buildings:**
- `CITY`, `FACTORY`, `AIRPORT`, `PORT`, `COM_TOWER`, `LAB`
- `BASE_TOWER_0`, `BASE_TOWER_1`, `BASE_TOWER_2`, `BASE_TOWER_3`, `BASE_TOWER_4`

**Owned buildings (game uses MAPTYPE:ARMY format):**
- `CITY:RED`, `CITY:BLUE`, `CITY:GREEN`, `CITY:YELLOW`, `CITY:GREY`
- `FACTORY:RED`, `FACTORY:BLUE`, `FACTORY:GREEN`, `FACTORY:YELLOW`, `FACTORY:GREY`
- `AIRPORT:RED`, `AIRPORT:BLUE`, `AIRPORT:GREEN`, `AIRPORT:YELLOW`, `AIRPORT:GREY`
- `PORT:RED`, `PORT:BLUE`, `PORT:GREEN`, `PORT:YELLOW`, `PORT:GREY`
- `COM_TOWER:RED`, `COM_TOWER:BLUE`, `COM_TOWER:GREEN`, `COM_TOWER:YELLOW`, `COM_TOWER:GREY`
- `LAB:RED`, `LAB:BLUE`, `LAB:GREEN`, `LAB:YELLOW`, `LAB:GREY`
- `BASE_TOWER_0:RED`, `BASE_TOWER_0:BLUE`, etc. (for all 5 variants × 5 colors)

#### Special
- `MISSILE_SILO` - with ammo
- `EMPTY_SILO` - fired state

#### Fog Variants (NOT included in this tileset - to be added later)
- Fog variants will be added in a future update
- This tileset will only include the sprites currently defined in MapType enum

### 2. File Mapping Strategy
I need to map from our sprite files to game names:

```
sprites_2x/terrain/terrain/PLAIN_0_0.png → PLAIN
sprites_2x/terrain/terrain/WOOD.png → WOOD
sprites_2x/terrain/buildings_neutral/CITY.png → CITY
sprites_2x/terrain/buildings_red/RED_CITY.png → CITY:RED
sprites_2x/terrain/buildings_blue/BLUE_FACTORY.png → FACTORY:BLUE
sprites_2x/terrain/buildings_neutral/HQ_VARIANT_0.png → BASE_TOWER_0
sprites_2x/terrain/buildings_blue/BLUE_HQ_VARIANT_1.png → BASE_TOWER_1:BLUE
sprites_2x/terrain/roads/ROAD_HORT_PLAIN.png → ROAD_HORT
```

### 3. Sprite Sheet Layout
- **Dimensions**: 640x640 pixels (20 sprites × 10 rows)
- **Row Height**: 64px (to accommodate tall buildings)
- **Sprite Spacing**: 2px between sprites
- **Background**: Dark gray (#202020) to see boundaries

#### Row Organization:
- Row 0: Basic terrain (PLAIN, WATER, REEF, etc.)
- Row 1: Roads and bridges
- Row 2: Natural terrain (MOUNTAIN, WOOD)
- Row 3: Neutral buildings
- Row 4: Red buildings
- Row 5: Blue buildings
- Row 6: Yellow buildings
- Row 7: Green buildings
- Row 8: Grey buildings
- Row 9: Special/overflow

### 4. Coordinate System
Each sprite in the JSON map will have:
```json
{
  "SPRITE_NAME": {
    "x": left_position,
    "y": bottom_position,  // Important: y is bottom of sprite
    "w": width,
    "h": 32,              // Base tile height
    "full_height": actual_height  // 32 or 64
  }
}
```

### 5. Implementation Steps

1. **Backup existing files** (if any exist)
2. **Scan sprite directories** and create name mappings
3. **Verify all required sprites exist**
4. **Create sprite sheet image**
5. **Generate JSON coordinate map**
6. **Save with timestamp for tracking**
7. **Clean up any temp files**

### 6. Error Handling
- Missing sprites will be logged but not stop the process
- Unknown sprite files will be included in an "other" category
- Validation will check that core sprites (PLAIN, WOOD, etc.) exist

### 7. Output Files
- `terrain_tileset_2x.png` - The sprite sheet
- `terrain_tileset_2x_map.json` - Coordinate map
- `terrain_tileset_creation_log.txt` - Log of what was done
- Backups will be timestamped

### 8. Post-Creation Verification
- Check that all expected sprite names are in the map
- Verify image dimensions match expectations
- Test that a sample sprite (like BLUE_HQ_VARIANT_0) extracts correctly

## Questions/Concerns

1. **Water tiles**: The documentation mentions `WATER` but our sprites have many water variations (SEA_0_0, etc.). Which one should map to `WATER`?

2. **Road naming**: We have files like `ROAD_HORT_PLAIN.png` - should this become `ROAD_HORT`?

3. **Building variants**: We have `HQ_VARIANT_0` through `HQ_VARIANT_4` - should these all map to just `HQ_COLOR`?

4. **Missing sprites**: If we don't have a sprite file for something in the documentation (like `SWNRoad`), what should we do?

## Ready to Proceed?
Once you confirm this plan, I will create the script to generate the tileset.
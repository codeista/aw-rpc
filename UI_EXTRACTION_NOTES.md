# UI Elements Extraction Notes

## What We Found and Extracted

### 1. Fuel and Ammo Warning Icons
- **Fuel icon**: Located at (651, 1241) - 8x8 pixels
- **Ammo icon**: Located at (651, 1250) - 8x8 pixels
- Both are warning indicators that appear on units when low

### 2. HP and Status Indicators (100 unique tiles total)

#### Unavailable Status Icons (70 tiles)
- Located starting at (392, 1233)
- 5 armies (red, blue, green, yellow, grey)
- 14 tiles per army (includes HP 1-9, ?, and 4 status icons)
- Each army row separated by 1px white gap (9px total spacing)

#### Available Status Icons (20 tiles)
- Located starting at (520, 1233)
- 5 armies with 4 status icons each
- Only the status icons are army-specific
- The HP numbers are shared (see below)

#### Non-color Specific HP (10 tiles)
- Located at (556, 1233)
- Contains HP digits 1-9 and ?
- These are used for ALL available units regardless of army
- The sprite sheet shows "(same)" text indicating these are reused

### 3. Other UI Elements We Noted But Haven't Extracted Yet
- Red path indicators (movement preview arrows)
- Message boxes (SUPPLY, TRAPPED, etc.)
- Capture progress indicators
- Load indicators for transports
- Unit destroyed animations

## Key Findings

1. **Coordinate System**: All UI elements use 8x8 pixel tiles with 1px spacing (9px grid)

2. **Army Colors**: 
   - Red (Orange Star)
   - Blue (Blue Moon)
   - Green (Green Earth)
   - Yellow (Yellow Comet)
   - Grey (Black Hole)

3. **Status Icon Organization**:
   - Unavailable units: Full set of army-specific icons (status + HP)
   - Available units: Army-specific status icons + shared HP numbers

4. **Reuse Pattern**: The game reuses the non-color HP digits for all available units to save sprite space

## Files Created
- `extract_hp_correct.py` - Extracts all HP/status indicators
- `extract_hp_unique.py` - Extracts only unique tiles (no duplication)
- `extract_correct_warning_icons.py` - Extracts fuel/ammo icons
- `temp/hp_unique_tiles.png` - All unique HP/status tiles
- `static/img/fuel_warning_2x.png` - Fuel icon (needs to be 16x16 not 32x32)
- `static/img/ammo_warning_2x.png` - Ammo icon (needs to be 16x16 not 32x32)

## TODO for Tomorrow
1. Properly upscale UI elements to 16x16 (2x) not 32x32
2. Consider positioning of UI elements with larger 32x32 unit sprites
3. Extract remaining UI elements (path indicators, message boxes, etc.)
4. Create combined sprite sheets for the game to use
5. Update render.js to use the new upscaled assets
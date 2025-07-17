# Sprite Sheet Limitations & Missing Units

## Critical Missing Sprites

The current sprite sheet (`aw2_blackhole_units_map_transparent.png`) is missing sprites for several units:

### Units with Limited Sprites:
- **CARRIER**
- **MEGATANK** 
- **BLACKBOAT**
- **STEALTH**
- **BLACKBOMB**
- **PIPERUNNER**

### Availability by Army:
| Unit | RED | BLUE | GREEN | YELLOW | GREY |
|------|-----|------|-------|--------|------|
| CARRIER | ✓ (idle only) | ✓ (idle only) | ❌ | ❌ | ❌ |
| MEGATANK | ✓ (idle only) | ✓ (idle only) | ❌ | ❌ | ❌ |
| BLACKBOAT | ✓ (idle only) | ✓ (idle only) | ❌ | ❌ | ❌ |
| STEALTH | ✓ | ✓ | ❌ | ❌ | ❌ |
| BLACKBOMB | ✓ | ✓ | ❌ | ❌ | ❌ |
| PIPERUNNER | ✓ (idle only) | ✓ (idle only) | ❌ | ❌ | ❌ |

### Known Issues:
1. **Only first idle sprite (frame 0) available** for RED and BLUE armies
2. **No animation frames** (frames 1, 2) for these units
3. **Unavailable sprites are identical to idle sprites** for RED and BLUE
4. **No sprites at all** for GREEN, YELLOW, and GREY armies
5. **No movement sprites** for any army

## Required Actions

### 1. Import Missing Sprites
Check these locations for additional sprites:
- `/static/img/GEBlack_Bomb.webp`
- `/static/img/blackbomb.png` 
- `/static/img/stealth.png`
- Other sprite sheets in `/static/img/`

### 2. Create Missing Sprites
For units that don't exist in any sprite sheet, you'll need to:
- Create sprites for GREEN, YELLOW, GREY armies
- Generate proper unavailable states (grayed out versions)
- Create animation frames (idle frames 1, 2)
- Design movement sprites

### 3. Temporary Workarounds
Until proper sprites are created:
- Use RED/BLUE sprites as placeholders for other armies
- Duplicate idle frame 0 for frames 1 and 2
- Apply grayscale filter for unavailable states
- Skip movement animations for these units

## Sprite Creation Guidelines

### For Missing Army Colors:
1. Take RED or BLUE sprite as base
2. Recolor using army palette:
   - GREEN: #27ae60 tones
   - YELLOW: #f39c12 tones  
   - GREY: #7f8c8d tones

### For Unavailable States:
1. Take idle sprite
2. Apply grayscale filter
3. Reduce brightness by 40-50%
4. Add slight transparency if needed

### For Animation Frames:
1. Frame 0: Base pose
2. Frame 1: Slight animation (wheels turning, propellers spinning)
3. Frame 2: Return toward base pose

## Affected Game Functionality

Without these sprites:
- Units will show as black boxes or missing
- GREEN, YELLOW, GREY armies can't use these units properly
- No visual feedback for unit availability status
- No movement animations

## Next Steps

1. **Audit existing sprite files** for usable assets
2. **Create sprite completion plan** for missing units
3. **Consider using sprite editing tool** to generate missing sprites
4. **Update sprite_corrections_config.json** to handle duplicates/placeholders
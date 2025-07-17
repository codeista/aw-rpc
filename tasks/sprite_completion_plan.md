# Sprite Completion Plan

## Current Status
- **Total corrections**: 375 (mostly idle states)
- **Movement sprites**: Only 8 (INFANTRY for 4 armies)
- **Unavailable sprites**: 281 entries
- **Missing**: Most movement sprites for all units

## Sprite Organization (8x8 pixels, 1px horizontal spacing)
Based on the sprite sheet layout:
- Each unit has multiple animation frames
- States: idle (3 frames), movement (up to 9 frames), unavailable
- HP indicators: 1-10
- Status icons: ammo, fuel, etc.

## Tasks to Complete

### 1. Movement Sprites (Priority: HIGH)
Need to add movement sprites for all units:
- Ground units: 3x3 grid (8 directions + center)
- Air/Naval units: Often 2x3 or custom layouts
- Each direction has animation frames

### 2. Missing Units
Some units missing from certain armies:
- BLACKBOMB - not all armies have entries
- STEALTH - incomplete coverage
- PIPERUNNER - special pipe-only unit

### 3. HP Indicators
- Numbers 1-10 for unit health display
- Located in specific sprite sheet areas

### 4. Status Icons
- Low ammo indicator
- Low fuel indicator
- Loaded transport indicator

## Sprite Sheet Coordinates Pattern
From analysis:
- RED units: Y=104+ (INFANTRY at 104, MECH at 199, etc.)
- BLUE units: Y=672+ 
- GREEN units: Y=672+ (different X offset)
- YELLOW units: Y=767+
- GREY units: Y=1335+

## Implementation Steps
1. Use advanced_sprite_corrector.html tool
2. Load sprite sheet
3. For each unit type:
   - Find movement sprite grid location
   - Map all 9 positions (8 directions + center)
   - Add animation frames for each direction
4. Export updated JSON config
5. Test in game to verify sprites display correctly
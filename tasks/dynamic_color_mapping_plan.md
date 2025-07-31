# Dynamic Color Mapping Implementation Plan

## Problem
Maps currently hard-code army colors (RED, BLUE, etc.), but players should be able to choose their colors. When Player 1 chooses YELLOW and Player 2 chooses GREEN, the map still assigns properties based on RED/BLUE.

## Current System
1. Maps use `FACTORY:RED` or `FACTORY:0` to indicate ownership
2. Map parser converts legacy colors to player indices (RED→0, BLUE→1, etc.)
3. Players choose colors via `game_create_v2` but map ownership doesn't adapt

## Solution: Player-Index Based Maps

### Step 1: Update Map Format
Instead of:
```
FACTORY:RED,CITY,PLAIN,FACTORY:BLUE
```

Use:
```
FACTORY:0,CITY,PLAIN,FACTORY:1
```

Where 0 = Player 1, 1 = Player 2, etc.

### Step 2: Update Existing Maps
Convert all map templates to use player indices:
- RED → 0 (Player 1)
- BLUE → 1 (Player 2)  
- GREEN → 2 (Player 3)
- YELLOW → 3 (Player 4)
- GREY → 4 (Player 5)
- NEUTRAL → -1 or no suffix

### Step 3: Update Predeployed Units
Change from:
```python
{'army': 'RED', 'type': 'INFANTRY', 'x': 5, 'y': 4}
```

To:
```python
{'player': 0, 'type': 'INFANTRY', 'x': 5, 'y': 4}
```

### Step 4: Update create_predeployed_units()
Modify the function to:
1. Accept player index instead of army name
2. Map player index to their chosen army/sprite color
3. Create units with correct army assignment

### Step 5: Benefits
- Maps work with any color combination
- Players get their chosen colors
- No need to modify maps when players pick different colors
- Cleaner separation of game logic from visual representation

## Implementation Priority
1. Update map parser to prefer player indices
2. Convert test maps to new format
3. Update predeployed unit system
4. Test with various player color combinations
# Color Decoupling Plan

## Overview
Remove hardcoded colors from the codebase to support flexible player colors and more than 2 players.

## Current State Analysis

### 1. Color Systems
- **Two Army Enums**: 
  - `models_v2.py`: String-based ('red', 'blue', 'green', 'yellow', 'grey')
  - `map_system.py`: Integer-based (RED=0, BLUE=1, etc.)
- **Legacy Support**: Special handling for red/blue with dedicated fields

### 2. Hardcoded Locations
- **Maps**: All maps specify armies as "RED,BLUE" 
- **Manager.py**: `red_funds`, `blue_funds`, `total_red_properties`, etc.
- **Sprites**: Named with colors (e.g., `INFANTRY_RED_idle_0`)
- **Frontend**: Direct color string usage in sprite construction

## Proposed Solution

### Phase 1: Core Data Model Changes
1. **Unified Player System**
   ```python
   class Player:
       id: int  # 0, 1, 2, 3...
       name: str
       color: str  # Display color
       sprite_set: str  # Which sprite set to use
   ```

2. **Update Army References**
   - Change from color-based to index-based (army_0, army_1, etc.)
   - Keep color as a display property only

### Phase 2: Map Format Update
1. **New Map Header Format**
   ```
   Old: RED,BLUE
   New: 2  # Number of players
   ```

2. **Property Ownership**
   ```
   Old: CITY:RED
   New: CITY:0  # Player index
   ```

### Phase 3: Sprite Mapping System
1. **Create Sprite Mapping Table**
   ```json
   {
     "player_sprites": {
       "0": "RED",    // Player 0 uses RED sprites
       "1": "BLUE",   // Player 1 uses BLUE sprites
       "2": "GREEN",  // Player 2 uses GREEN sprites
       "3": "YELLOW", // Player 3 uses YELLOW sprites
     }
   }
   ```

2. **Update Sprite Lookup**
   - Instead of `INFANTRY_${color}_idle_0`
   - Use `INFANTRY_${sprite_map[player_id]}_idle_0`

### Phase 4: Game Logic Updates
1. **Replace Color-Specific Fields**
   ```python
   # Old
   red_funds, blue_funds
   
   # New
   player_funds: Dict[int, int]  # {0: 5000, 1: 5000}
   ```

2. **Update All Methods**
   - Change from checking color strings to player indices
   - Update victory conditions to work with any number of players

### Phase 5: Frontend Updates
1. **Dynamic Color Assignment**
   ```javascript
   // Map player ID to sprite color
   const playerSpriteMap = {
     0: 'RED',
     1: 'BLUE', 
     2: 'GREEN',
     3: 'YELLOW'
   };
   ```

2. **Update Sprite Construction**
   ```javascript
   // Old
   const sprite = `${unit.type}_${unit.army}_idle_0`;
   
   // New  
   const sprite = `${unit.type}_${playerSpriteMap[unit.player_id]}_idle_0`;
   ```

## Implementation Order
1. Create player model and sprite mapping system
2. Update map parser to support both old and new formats
3. Modify game logic to use player indices internally
4. Update frontend to use sprite mapping
5. Migrate existing maps to new format
6. Remove legacy color-specific code

## Benefits
- Support for 2+ players
- Flexible color assignment
- Players can choose their preferred color
- Easier to add new sprite sets
- Cleaner separation of game logic and presentation

## Risks & Mitigation
- **Risk**: Breaking existing games
  - **Mitigation**: Support both formats during transition
  
- **Risk**: Complex sprite renaming
  - **Mitigation**: Use mapping table instead of renaming files

- **Risk**: Frontend/backend mismatch
  - **Mitigation**: Careful API versioning
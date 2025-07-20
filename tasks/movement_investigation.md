# Movement System Investigation Results

## 1. Movement Highlighting System ✅ IMPLEMENTED
- **Status**: Fully implemented and functional
- **Location**: `/static/js/render.js` and `/static/js/modules/movementSystem.js`
- **Features**:
  - Shows valid movement tiles when unit is selected
  - Blue/green highlights on accessible tiles
  - Backend calculation via `get_movement_highlights` RPC
  - Considers terrain costs and unit movement points
  - BFS pathfinding algorithm for valid tile calculation

## 2. Path Preview System ❌ NOT IMPLEMENTED
- **Status**: Not implemented
- **Missing Features**:
  - No path arrow sprites (straight, turn, start, end)
  - No hover handlers for path visualization
  - No path calculation on destination hover
  - No manual path adjustment capability
  
### Requirements for Implementation:
1. **Path Arrow Sprites**:
   - Straight arrows (horizontal/vertical)
   - Turn arrows (4 corners)
   - Start/end indicators
   - Different states for fog risk indication

2. **Frontend Changes**:
   - Mouse hover event handler for movement tiles
   - Path calculation from selected unit to hovered tile
   - Dynamic sprite rendering for path visualization
   - Path state management

3. **Path Calculation**:
   - Can reuse existing BFS from movementSystem.js
   - Need to track actual path taken, not just valid tiles
   - Store direction changes for arrow sprite selection

## 3. Fog of War System ❌ NOT IMPLEMENTED
- **Status**: Documented but not implemented
- **Documentation**: Detailed in `/movement-fog.txt`
- **Vision Data**: Configured in `/config.ini` for each unit type

### Fog of War Requirements (from documentation):
1. **Vision System**:
   - Units reveal tiles within vision range
   - Properties provide vision of units on them
   - Shared vision for allied teams
   - Vision ranges: Recon (5), Infantry (2), etc.

2. **Movement Ambush/Trap Mechanics**:
   - Units moving into fog risk being trapped
   - Movement interrupted on enemy contact
   - No further actions allowed that turn

3. **Terrain Interactions**:
   - Woods/Reefs hide ground/sea units unless adjacent
   - Mountains boost Infantry/Mech vision by +3
   - Rain reduces all vision by -1 (min 1)

4. **Rendering Requirements**:
   - Fog overlay on unexplored tiles
   - Partial transparency for previously seen tiles
   - Clear visibility for current vision range
   - Hidden unit indicators

### Implementation Priority:
1. Path preview system - Enhances gameplay usability
2. Fog of War - Major gameplay feature, changes game strategy significantly

Both features would significantly improve the game experience and bring it closer to the original Advance Wars gameplay.
# Map Color System Notes

## Current Issues

### 1. Grey Army Color
- Grey is another army color option (like RED, BLUE, GREEN, YELLOW)
- This is distinct from the darker "unavailable" sprite overlay
- Players can choose GREY as their army color during game setup

### 2. Player Color Selection
- Players choose their colors when setting up a match
- Current system: Properties are hard-coded to specific armies (RED, BLUE, etc.)
- Problem: Map properties don't match player's chosen colors

## Proposed Solutions

### Dynamic Property Color Assignment
Instead of hard-coding army colors in maps, we should:

1. **Store properties as neutral or by player index** (Player 1, Player 2, etc.)
2. **Apply player's chosen color at game creation time**
3. **Benefits**:
   - Maps work with any color combination
   - Players can choose their preferred colors
   - More flexible game setup

### Implementation Approach

#### Option 1: Generate on Request
- Generate map tiles and units dynamically based on player setup
- Properties assigned to "Player 1", "Player 2" etc. in map data
- At game creation: Map Player 1 → chosen color (e.g., GREEN)
- More flexible but requires refactoring map system

#### Option 2: Color Mapping Layer
- Keep existing map format
- Add translation layer: army in map → player's chosen army
- Simpler to implement but less clean

## Example Color Flow

1. **Map Design**: Property marked as "Player 1's City"
2. **Game Setup**: Player 1 chooses YELLOW army
3. **Game Creation**: System converts all "Player 1" properties to YELLOW
4. **In-Game**: City displays with yellow colors

## Technical Considerations

- Need to update `map_system.py` to support player indices
- Modify `game_create_v2` to apply color mappings
- Update sprite system to handle dynamic army colors
- Ensure save/load system preserves player color choices

## Army Colors & Neutral Properties

- **Army Colors**: RED, BLUE, GREEN, YELLOW, GREY
- **Neutral Properties**: Use WHITE sprites (not owned by any army)
- Players can choose from the 5 army colors during game setup
- Neutral properties can be captured by any army

## Questions to Resolve

1. How do we handle pre-deployed units in maps with dynamic colors?
2. Are there other army colors beyond the 5 listed?
3. What happens to existing maps - migration or backwards compatibility?
4. Should map editor support placing "Player 1 units" vs "RED units"?
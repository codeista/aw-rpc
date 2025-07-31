# Player ID System Design

## Current System Issues
- Maps use army colors (RED, BLUE) or local player indices (0, 1, 2)
- This breaks in a multi-user environment where users have unique IDs
- Player indices are only meaningful within a single game

## Better Design: User IDs vs Game Slots

### Option 1: Game Slot System (Recommended)
Keep using **game-local player indices** (0, 1, 2, 3...) but map them to user IDs:

```python
game_state = {
    'game_id': 'abc123',
    'player_slots': {
        0: {'user_id': 'user_12345', 'color': 'YELLOW', 'name': 'Alice'},
        1: {'user_id': 'user_67890', 'color': 'GREEN', 'name': 'Bob'},
        2: {'user_id': 'user_54321', 'color': 'RED', 'name': 'Charlie'},
        # ... up to max players
    }
}
```

**Advantages:**
- Maps remain simple: `FACTORY:0`, `CITY:1`, etc.
- Easy to understand: Player 1, Player 2, etc.
- Maps are reusable across different games
- Turn order is clear (0, 1, 2, 3...)

### Option 2: Direct User IDs (Not Recommended)
Use actual user IDs in maps:

```
FACTORY:user_12345,CITY,PLAIN,FACTORY:user_67890
```

**Disadvantages:**
- Maps become tied to specific users
- Difficult to share/reuse maps
- User IDs could be long/complex
- Turn order becomes complicated

## Recommended Implementation

### 1. Map Format
```
# Header: Number of players
2
# Dimensions
15,10
# Tiles use slot indices
FACTORY:0 CITY PLAIN FACTORY:1
```

### 2. Game Creation
```python
def game_create_v2(token, players):
    # players = [
    #     {'user_id': 'user_12345', 'name': 'Alice', 'color': 'YELLOW'},
    #     {'user_id': 'user_67890', 'name': 'Bob', 'color': 'GREEN'}
    # ]
    
    # Map user IDs to game slots
    player_slots = {}
    for idx, player in enumerate(players):
        player_slots[idx] = player
```

### 3. During Gameplay
- All game logic uses slot indices (0, 1, 2...)
- When displaying to users, lookup: slot → user_id → user info
- When user makes action, lookup: user_id → slot → validate turn

### 4. Benefits
- **Scalability**: Works with any number of users
- **Flexibility**: Users can choose any available color
- **Reusability**: Maps work for any set of players
- **Clarity**: Turn order is always 0→1→2→...

## Example Flow

1. **Matchmaking**: Users Alice, Bob, Charlie want to play
2. **Game Creation**: 
   - Alice → Slot 0 (chooses YELLOW)
   - Bob → Slot 1 (chooses GREEN)  
   - Charlie → Slot 2 (chooses RED)
3. **Map Loading**: Properties marked `:0` go to Alice (YELLOW)
4. **Turn System**: Slot 0 goes first (Alice), then Slot 1 (Bob), etc.
5. **API Calls**: Include user_id, server maps to slot, validates it's their turn

This approach keeps the game engine simple while supporting complex user management!
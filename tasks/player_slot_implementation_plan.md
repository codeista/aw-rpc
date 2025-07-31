# Player Slot System Implementation Plan

## Overview
Convert the game from using hard-coded army colors to a flexible slot-based system where players are assigned to slots (0, 1, 2...) and can choose any color.

## Phase 1: Update Map Format

### Current Format (Color-based)
```
RED,BLUE
15,10
FACTORY:RED CITY PLAIN FACTORY:BLUE
```

### New Format (Slot-based)
```
2
15,10
FACTORY:0 CITY PLAIN FACTORY:1
```

Where:
- First line: Number of player slots
- Properties use slot indices: `:0`, `:1`, `:2`, etc.
- Neutral properties: No suffix

## Phase 2: Update Map Parser

### Changes to map_parser_v2.py
1. The parser already supports player indices! Just need to ensure it's the default
2. Keep backward compatibility for legacy maps
3. Update map saving to always use slot format

## Phase 3: Update Predeployed Units

### Current Format
```python
{'army': 'RED', 'type': 'INFANTRY', 'x': 5, 'y': 4}
```

### New Format
```python
{'player': 0, 'type': 'INFANTRY', 'x': 5, 'y': 4}
```

### Update create_predeployed_units()
- Accept 'player' field (slot index) instead of 'army'
- Map slot to actual army color via game's player configuration

## Phase 4: Update Test Maps

### Convert All Test Maps
1. COMBAT_TEST_MAP
2. TRANSPORT_TEST_MAP
3. MOVEMENT_TEST_MAP
4. Other test maps

### Conversion Rules
- RED → 0
- BLUE → 1
- GREEN → 2
- YELLOW → 3
- GREY → 4
- NEUTRAL → (no suffix)

## Phase 5: Update Game Creation Flow

### game_create_v2 Enhancement
```python
# Players specify their preferences
players = [
    {'user_id': 'user123', 'name': 'Alice', 'color': 'YELLOW'},
    {'user_id': 'user456', 'name': 'Bob', 'color': 'GREEN'}
]

# System maps to slots
slot_mapping = {
    0: {'user_id': 'user123', 'army': Army.YELLOW},
    1: {'user_id': 'user456', 'army': Army.GREEN}
}
```

## Phase 6: Testing

### Test Scenarios
1. 2-player game with non-standard colors (YELLOW vs GREEN)
2. 4-player game with custom color choices
3. Legacy map compatibility
4. Predeployed units with correct ownership

## Implementation Order

1. **Update map parser** - Ensure slot indices are primary format
2. **Convert one test map** - Start with COMBAT_TEST_MAP as proof of concept
3. **Update create_predeployed_units** - Support player slot field
4. **Test the converted map** - Verify it works with custom colors
5. **Convert remaining maps** - Apply changes to all test maps
6. **Update documentation** - Document new map format

## Benefits

1. **Flexibility**: Players choose any color combination
2. **Scalability**: Works with user ID systems
3. **Simplicity**: Maps use simple indices (0,1,2...)
4. **Compatibility**: Legacy maps still work
5. **Reusability**: Same map works for any player set

## Code Changes Summary

### Files to Modify
- `test_map_templates.py` - Convert maps to slot format
- `create_predeployed_units()` - Accept player slot instead of army
- `game_factory.py` - Ensure slot mapping works correctly
- Documentation files - Update map format docs

### Files Already Ready
- `map_parser_v2.py` - Already supports slot indices!
- `player_system.py` - Already handles player-to-army mapping
- `game_create_v2` - Already supports custom player configs
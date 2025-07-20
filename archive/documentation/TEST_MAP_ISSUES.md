# Test Map Creation Issues

## Date: 2025-07-20

## Problem Summary
The test map creation in `get_optimized_test_game()` bypasses normal game mechanics and could cause inconsistent behavior.

## Issues Identified

### 1. Unit Creation Rule Violations
**Normal Game Rules:**
- Units created from factories cannot move on their creation turn
- `Unit.create()` properly sets `can_move = False` and `can_attack = False`

**Test Map Override:**
```python
# From optimized_test_map.py
unit.can_move = True      # VIOLATES RULE - newly created units shouldn't move
unit.can_attack = True    # VIOLATES RULE - newly created units shouldn't attack
unit.can_capture = True   # This is OK
```

### 2. Turn State Initialization
- The test map doesn't go through normal turn initialization
- Day counter shows `null` because the game hasn't gone through proper turn cycles
- Units have movement/attack flags that don't match actual game state

### 3. Direct Property Setting
The test map directly sets unit properties instead of using game manager methods:
```python
# Test map does this:
unit.status.hp = unit_data.get('hp', 100)
unit.can_move = True
unit.can_attack = True

# Should use manager methods that enforce rules
```

## Impact on Testing

### What Still Works:
- Unit placement and board layout
- RPC communication with proper tokens
- UI interactions (clicks, selections, highlights)
- Combat damage calculations

### What May Be Incorrect:
- Turn-based movement restrictions
- Unit creation rules
- Day/turn advancement
- Initial game state consistency

## Recommendations

### For Testing UI Mechanics:
The test map is fine for testing:
- Click handlers
- Selection mechanics  
- Movement highlight display
- Attack highlight display
- RPC token authentication

### For Testing Game Rules:
Consider creating units through proper game flow:
1. Start a normal game
2. Use factories to create units
3. End turns properly to test turn-based mechanics
4. Test that newly created units can't move

### Fix for Test Map:
To make the test map more realistic, change:
```python
# Current (incorrect)
unit.can_move = True
unit.can_attack = True

# Should be (for turn 1 units)
unit.can_move = True   # OK for pre-deployed units
unit.can_attack = True # OK for pre-deployed units

# But for any units created after game start:
unit.can_move = False
unit.can_attack = False
```

## Conclusion
The test map is useful for quickly setting up complex scenarios but bypasses important game rules. For UI testing it's fine, but for testing actual game mechanics, use the normal game flow through factories and proper turn management.
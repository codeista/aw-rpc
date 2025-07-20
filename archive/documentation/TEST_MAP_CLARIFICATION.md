# Test Map Clarification - Pre-deployed Units

## Date: 2025-07-20

## Important Distinction

### Pre-deployed Units (Start of Game)
- **CAN move on first turn** ✅
- **CAN attack on first turn** ✅
- This is standard Advance Wars behavior
- The test map setting `can_move = True` and `can_attack = True` is CORRECT for these units

### Factory-Created Units (During Game)
- **CANNOT move on creation turn** ❌
- **CANNOT attack on creation turn** ❌
- Must wait until next turn to act

## Test Map Analysis - REVISED

The `get_optimized_test_game()` creates pre-deployed units, so:

```python
# This is CORRECT for pre-deployed units:
unit.can_move = True      # ✅ Pre-deployed units can move on turn 1
unit.can_attack = True    # ✅ Pre-deployed units can attack on turn 1
unit.can_capture = True   # ✅ OK
```

## Remaining Issues

### 1. Day Counter Shows Null
- This is likely because the game hasn't been through proper initialization
- Not related to unit movement rules
- The `army_end_turn` fix should help with this

### 2. Turn Advancement
- May need proper game state initialization
- Check if `board.days` or `board.turn_counter` needs to be set

## Conclusion

The test map is actually correct in allowing pre-deployed units to move and attack. The issues we're seeing with:
- Day showing null
- Turn not advancing properly

Are separate initialization issues, not problems with the unit movement flags.

The test map correctly simulates a game that starts with units already on the battlefield, ready for immediate combat.
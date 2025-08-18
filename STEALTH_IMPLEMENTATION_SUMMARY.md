# Stealth System Implementation Summary

## Overview
Successfully implemented a complete stealth/submarine system for Advance Wars RPC, including hide/unhide mechanics, visibility filtering, and ambush mechanics.

## Features Implemented

### 1. Stealth Hide/Unhide Mechanics
- **Units Affected**: STEALTH bomber and SUB (submarine)
- **Hide Requirements**: 
  - Unit must not have moved this turn
  - Unit must not already be hidden
- **Hide Effects**:
  - Unit becomes invisible to enemies (unless adjacent)
  - Unit cannot attack while hidden
  - Hiding ends the unit's turn
- **Unhide Effects**:
  - Unit becomes visible again
  - Unit can attack normally
  - Unhiding does NOT end turn (unit can still move/attack)

### 2. Dynamic Visibility System
- **Visibility Rules**:
  - Own units are always visible to the player
  - Non-hidden enemy units are always visible
  - Hidden enemy units are only visible when adjacent to a friendly unit
  - Visibility is calculated dynamically - hidden units disappear when no longer adjacent
- **Implementation**:
  - `is_unit_visible_to_player()` method checks visibility rules
  - `get_visible_units_for_player()` filters units based on visibility
  - Backend filtering prevents cheating (hidden units not sent to enemy clients)

### 3. Ambush Mechanics
- **Ambush Trigger**: When a unit tries to move through/into a tile with a hidden enemy
- **Ambush Effects**:
  - Movement stops immediately (at tile before the hidden enemy)
  - Moving unit loses all remaining actions (can't attack)
  - Hidden unit is discovered (becomes visible while adjacent)
- **Implementation**: 
  - `check_for_ambush()` method scans movement path
  - `unit_move()` integrates ambush checking

### 4. Fuel Consumption
- **Hidden Unit Fuel Usage**:
  - STEALTH: 8 fuel/turn when hidden (vs 5 normally)
  - SUB: 5 fuel/turn when hidden (vs 1 normally)
- **Fixed**: Updated fuel consumption to use unit's `fuel_use()` method

## Code Changes

### Core Files Modified
1. **manager.py**:
   - Added `unit_hide()` and `unit_unhide()` methods
   - Added visibility filtering methods
   - Added ambush checking to movement
   - Fixed fuel consumption to handle hidden units

2. **core/unit.py**:
   - Added `is_hidden` flag to Unit dataclass
   - Updated `fuel_use()` to handle hidden state

3. **routes/rpc_methods.py**:
   - Modified `game_board_rpc` to accept `viewing_player_id`
   - Integrated visibility filtering

4. **core/api_response.py**:
   - Added `is_hidden` to unit info serialization

## Test Coverage
Created comprehensive test suite with 40+ tests covering:
- Basic hide/unhide functionality
- Visibility filtering from different player perspectives
- Ambush mechanics and movement interruption
- Fuel consumption for hidden units
- Integration with existing systems

## Frontend Integration Guide
The frontend needs to be updated to:
1. Pass `viewing_player_id` when requesting game board
2. Add hide/unhide options to unit context menus
3. Show hidden state visually (e.g., semi-transparent for own hidden units)
4. Handle ambush interruptions during movement

See `frontend_visibility_example.js` for implementation examples.

## Security Considerations
- All visibility filtering happens server-side
- Hidden enemy units are never sent to clients who shouldn't see them
- No client-side state can reveal hidden units
- Ambush detection happens server-side during movement validation
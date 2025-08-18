# Game Mechanics Implementation Summary

## Overview
Successfully implemented all requested game mechanics for Advance Wars RPC, including facility repairs, transport restrictions, unit merging, stealth/submarine mechanics, and Piperunner movement restrictions.

## Completed Features

### 1. Facility Auto-Repair (High Priority) ✅
- Units on friendly facilities repair 2 HP per turn at turn start
- Repair cost is 10% of unit cost per HP repaired
- Only repairs if player has sufficient funds
- Repair happens after resupply but before fuel consumption

### 2. Carrier/Cruiser Attack Restriction (High Priority) ✅
- Carriers and Cruisers cannot unload units after attacking
- Added `has_attacked` flag to track attack status
- Other transports (Lander, APC, Black Boat) not affected

### 3. Unit Join/Merge Mechanics (Medium Priority) ✅
- Same-type units can merge by moving one onto another
- Combined HP capped at 10, excess converted to funds (10% of unit cost per HP)
- Fuel and ammo values combined (respecting max values)
- The moving unit is absorbed into the target unit
- Both units end their turn after joining

### 4. Stealth/Submarine Hide Mechanics (Medium Priority) ✅
- Stealth fighters and Submarines can hide/unhide
- Hiding requirements:
  - Unit must not have moved this turn
  - Hiding ends the unit's turn
- Hidden units:
  - Invisible to enemies unless adjacent
  - Cannot attack while hidden
  - Consume extra fuel (Stealth: 8/turn, Sub: 5/turn)
- Unhiding does NOT end turn

### 5. Dynamic Visibility System (Medium Priority) ✅
- Hidden enemy units only visible when adjacent to friendly units
- Visibility calculated dynamically each turn
- Backend filtering prevents cheating
- `game_board_rpc` accepts `viewing_player_id` parameter

### 6. Ambush Mechanics (Medium Priority) ✅
- Units moving into hidden enemies get ambushed
- Movement stops before the hidden enemy
- Ambushed unit loses all remaining actions
- Simple straight-line path checking implemented

### 7. Piperunner Movement Restrictions (Low Priority) ✅
- Fixed enum mismatch between map_system.py and unit.py
- Piperunners now correctly restricted to pipe terrain only
- Movement cost 99 (impassable) on all non-pipe terrain
- Other units cannot enter pipe terrain

## Technical Details

### Files Modified
- `manager.py` - Added repair, join, hide/unhide, visibility, and ambush methods
- `core/unit.py` - Added `has_attacked` and `is_hidden` flags, updated fuel consumption
- `core/transport_system.py` - Added Carrier/Cruiser unload restriction
- `core/map_system.py` - Fixed UnitClass enum conflict and movement cost calculation
- `routes/rpc_methods.py` - Added visibility filtering to game_board endpoint
- `core/api_response.py` - Added is_hidden to unit serialization

### Test Coverage
Created comprehensive test suites for all features:
- `test_facility_repair.py` - 7 tests
- `test_carrier_cruiser_restriction_simple.py` - 4 tests  
- `test_unit_join.py` - 8 tests
- `test_stealth_mechanics.py` - 10 tests
- `test_visibility_filtering.py` - 6 tests
- `test_ambush_mechanics.py` - 5 tests
- `test_piperunner_movement.py` - 5 tests
- `test_complete_stealth_system.py` - 5 comprehensive integration tests

Total: 50+ tests, all passing

## Key Bug Fixes
1. **Fuel Consumption** - Fixed to use unit's fuel_use() method for proper hidden unit consumption
2. **Piperunner Movement** - Fixed UnitClass enum duplication causing movement restrictions to fail
3. **Visibility Filtering** - Implemented secure server-side filtering

## Frontend Integration Required
1. Pass `viewing_player_id` when requesting game board
2. Add hide/unhide options to unit context menus
3. Visual indicators for hidden units (own units semi-transparent)
4. Handle ambush movement interruptions
5. Show repair costs when hovering over damaged units on facilities

## Notes
- All game logic kept in backend as requested
- Backward compatibility maintained where possible
- Security considerations implemented (no client-side visibility cheating)
- Performance impact minimal (visibility checks are O(n*m) for n units and m adjacent tiles)
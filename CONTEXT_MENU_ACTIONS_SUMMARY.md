# Context Menu Actions Summary

## Available RPC Methods for Context Menu

### Movement & Basic Actions
- ✅ **movement_execute** - Move unit from one position to another
- ✅ **unit_wait** - Mark unit as done for this turn (JUST ADDED)
- ✅ **unit_select** - Select a unit
- ✅ **unit_delete** - Delete a unit (own units only)

### Combat Actions  
- ✅ **combat_attack** - Execute an attack
- ✅ **capture_tile** - Capture a property

### Transport Actions
- ✅ **transport_load** - Load unit into transport
- ✅ **transport_unload** - Unload unit from transport
- ✅ **get_loadable_transports** - Get available transports to load into
- ✅ **get_valid_unload_positions** - Get positions where units can be unloaded
- ✅ **transport_loadable_units** - Get units that can be loaded

### Support Actions
- ✅ **repair_unit** - Repair a unit (Black Boat)
- ✅ **resupply_unit** - Resupply a unit (APC/Black Boat)
- ✅ **action_repair_info** - Get repair information
- ✅ **action_resupply_targets** - Get resupply targets

## Expected Unit State After Actions

### After Movement
- `can_move` = false
- `can_attack` = true (for direct units)
- `can_attack` = false (for indirect units)
- `can_capture` = unchanged

### After Attack
- `can_move` = false
- `can_attack` = false
- `can_capture` = false

### After Wait
- `can_move` = false
- `can_attack` = false  
- `can_capture` = false

### After Capture
- `can_move` = false
- `can_attack` = false
- `can_capture` = false

### After Load/Unload
- Loaded unit: All actions = false
- Unloaded unit: All actions = false
- Transport: `can_move` = false (if moved), other actions based on transport type

### After Repair/Resupply
- Repairing unit: All actions = false
- Repaired/Resupplied unit: No change (passive action)

## Visual Feedback
Units should appear "greyed out" (unavailable sprite) when all actions are false.

## Delete Functionality
The `unit_delete` RPC method allows players to delete their own units:
- **Permission**: Can only delete units belonging to the current player
- **Context Menu**: Available for all owned units (not disabled)
- **Use Cases**: 
  - Clear blocking units to make space
  - Remove damaged units that can't be repaired
  - Strategic sacrifice of units
- **Confirmation**: Frontend shows confirmation dialog before deletion
- **Restrictions**: Cannot delete enemy units or units belonging to other players
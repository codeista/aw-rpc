# Missing Methods Audit - manager_v2.py

## Critical Missing Methods

### 1. Capture System
- ❌ `capture_tile` - Property capture functionality
- ❌ `capture_tile_enhanced` - Enhanced capture with preview
- ❌ `get_capture_preview` - Preview capture progress

### 2. Victory Conditions
- ❌ `check_win_condition` - Check if game has been won

### 3. Movement System
- ❌ `get_movement_preview` - Preview movement paths
- ❌ `unit_can_move_to` - Check if unit can move to position

### 4. Transport System
- ❌ `get_transport_capability` - Get transport capacity info
- ❌ `get_transport_cargo_info` - Get cargo information
- ❌ `is_transport_unit` - Check if unit is a transport

### 5. Production System
- ❌ `produce_unit_at_facility` - Create units at factories

## Methods Found in app.py RPC calls

These methods are called by RPC handlers but may not exist:
- `_calculate_fuel_cost` - Calculate fuel cost for movement
- `can_afford_unit` - Check if player can afford a unit
- `can_transport_load_unload` - Transport loading validation
- `can_transport_move` - Check if transport can move
- `load_transport_unit` - Load unit into transport
- `unload_transport_unit` - Unload unit from transport

## Next Steps

1. Check if these methods exist in other files (transport_system.py, etc.)
2. Implement missing critical methods
3. Add proper error handling for missing methods
4. Update tests to verify actual functionality
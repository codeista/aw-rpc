# API Method Comparison and Cleanup Recommendations

## 1. Unit Move Methods

### `unit_move` (line 2457)
- **Parameters**: `token, x, y, x2, y2`
- **Description**: Basic unit movement with validation
- **Features**:
  - Validates game is active
  - Dynamic coordinate validation using actual board size
  - Checks unit ownership
  - Validates movement path
  - Updates unit position
  - Handles fuel consumption
  - Basic error handling with ValidationError

### `unit_move_enhanced` (line 3462)
- **Parameters**: `token, from_x, from_y, to_x, to_y`
- **Description**: Enhanced movement that can auto-board transports
- **Features**:
  - All basic movement features
  - **ADVANCE WARS STYLE**: Auto-detects friendly transports at destination
  - If destination has friendly transport, automatically tries to board
  - Uses CompleteTransportSystem for transport operations
  - More descriptive parameter names (from_x/to_x vs x/x2)

**Recommendation**: Keep `unit_move_enhanced` as the canonical method. It's a superset of basic movement with better parameter names and transport integration. Consider deprecating `unit_move` or making it an alias.

## 2. Unit Load Methods

### `unit_load` (line 2736)
- **Parameters**: `token, x, y, x2, y2`
- **Description**: Legacy alias for frontend compatibility
- **Implementation**: Calls `load_unit_rpc` with parameter remapping
- **Frontend usage**: Select unit (x,y), then alt-click transport (x2,y2)

### `load_transport_unit` (line 3599)
- **Parameters**: `token, transport_x, transport_y, cargo_x, cargo_y`
- **Description**: Explicit transport loading
- **Implementation**: Calls `mngr.load_transport_unit()` directly
- **Features**: Clear parameter names, direct manager method call

### `load_unit` (line 3913)
- **Parameters**: `token, transport_x, transport_y, cargo_x, cargo_y`
- **Description**: Enhanced loading with CompleteTransportSystem
- **Implementation**: Uses `transport_system.load_unit_enhanced()`
- **Features**: More detailed logging, uses enhanced transport system

**Recommendation**: Keep `load_unit` as the canonical method (uses enhanced system). Keep `unit_load` as a legacy alias for frontend compatibility. Deprecate `load_transport_unit`.

## 3. Unit Unload Methods

### `unit_unload` (line 2766)
- **Parameters**: `token, x, y, x2, y2, index`
- **Description**: Legacy alias for frontend compatibility
- **Implementation**: Calls `unload_unit_rpc` with parameter remapping
- **Frontend usage**: Select transport (x,y), then alt-click destination (x2,y2)
- **Note**: Frontend sends 'index', not 'cargo_index'

### `unload_transport_unit` (line 3645)
- **Parameters**: `token, transport_x, transport_y, unload_x, unload_y, cargo_index`
- **Description**: Explicit transport unloading
- **Implementation**: Calls `mngr.unload_transport_unit()` directly
- **Features**: Clear parameter names, direct manager method call

### `unload_unit` (line 3975)
- **Parameters**: `token, transport_x, transport_y, unload_x, unload_y, cargo_index`
- **Description**: Enhanced unloading with CompleteTransportSystem
- **Implementation**: Uses `transport_system.unload_unit_enhanced()`
- **Features**: More detailed validation and logging

**Recommendation**: Keep `unload_unit` as the canonical method. Keep `unit_unload` as a legacy alias for frontend compatibility. Deprecate `unload_transport_unit`.

## 4. Unit Attack Methods

### `unit_attack` 
- **Status**: Does not exist as a basic method

### `unit_attack_enhanced` (line 4547)
- **Parameters**: `token, attacker_x, attacker_y, defender_x, defender_y`
- **Description**: Enhanced attack with win condition checking
- **Implementation**: Calls `mngr.unit_attack_enhanced()`
- **Features**: 
  - Full combat resolution
  - Win condition checking after combat
  - Game end handling
  - Event logging

**Recommendation**: Keep `unit_attack_enhanced` as the only attack method. Consider creating a simple `unit_attack` alias for consistency.

## Summary of Recommendations

1. **Movement**: Use `unit_move_enhanced` as canonical, deprecate basic `unit_move`
2. **Loading**: Use `load_unit` as canonical, keep `unit_load` for frontend, deprecate `load_transport_unit`
3. **Unloading**: Use `unload_unit` as canonical, keep `unit_unload` for frontend, deprecate `unload_transport_unit`
4. **Attack**: Keep `unit_attack_enhanced`, optionally add `unit_attack` alias

## Frontend Compatibility Notes

The frontend currently expects:
- `unit_load` with (x, y, x2, y2) parameters
- `unit_unload` with (x, y, x2, y2, index) parameters

These legacy aliases should be maintained for frontend compatibility until the frontend is updated to use the enhanced methods with clearer parameter names.
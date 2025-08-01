# RPC Method Name Fixes Needed

## Frontend Methods Using Wrong Names

### 1. ❌ `end_game` - Method doesn't exist
- **Files**: gameActions.js:82
- **Fix**: Remove or implement backend method

### 2. ❌ `unit_attack` - Should be `combat_attack`
- **Files**: 
  - gameActions.js:211, 238
  - combatSystem.js:348, 376, 528
- **Fix**: Replace with `combat_attack`

### 3. ❌ `capture_tile` - Not exposed via jsonrpc
- **Files**: gameActions.js:310
- **Fix**: Use `unit_capture` instead (which exists)

### 4. ❌ `cargo_board_transport` - Not exposed via jsonrpc
- **Files**: 
  - gameActions.js:463
  - transportSystem.js:259
- **Fix**: This is exposed via transport_system_api, need to check if it's accessible

### 5. ❌ `get_attack_targets` - Doesn't exist
- **Files**: combatSystem.js:53, 94, 134
- **Fix**: Should use `combat_targets`

### 6. ❌ `get_movement_highlights` - Doesn't exist
- **Files**: movementSystem.js:38
- **Fix**: Should use `movement_range`

### 7. ❌ `get_unit_valid_moves` - Doesn't exist
- **Files**: movementSystem.js:63
- **Fix**: Should use `movement_range`

### 8. ❌ All `v2.*` methods - Don't exist
- **Files**: game_v2.js (multiple)
- **Fix**: These are for a different version, not applicable to current game

## Already Fixed
- ✅ `unit_attack_enhanced` → `combat_attack` (fixed in game_v2_simple.js)

## Correctly Named Methods
- ✅ `unit_create` - Exists and correct
- ✅ `get_cargo_info` - Exists and correct
- ✅ `cargo_exit_transport` - Exists and correct
- ✅ `unit_wait` - Exists and correct
- ✅ `unit_select` - Exists and correct
- ✅ `movement_execute` - Exists and correct
- ✅ `get_production_options` - Exists and correct
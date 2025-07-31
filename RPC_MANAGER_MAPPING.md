# RPC to Manager Method Mapping

## Core Game Flow
These RPCs enable basic gameplay:

### 1. Game Management
- `game_create` → Creates new game
- `game_create_v2` → Creates game with player config
- `game_create_test` → Creates test game
- `game_board` → `manager.board` (gets game state)
- `game_info` → Gets game metadata
- `game_delete` → Removes game
- `check_turn` → `manager.check_turn()`
- `army_end_turn` → `manager.army_end_turn()`

### 2. Unit Selection & Information
- `unit_select` → `manager.unit_select(x, y)` ✅ IMPLEMENTED
- `tile` → `manager.tile_at(x, y)`
- `troop_info` → Global troop statistics

### 3. Unit Creation
- `unit_create` → `manager.unit_create(army, type, x, y)`
- `produce_unit` → `manager.produce_unit_at_facility(x, y, type)` ✅ IMPLEMENTED

### 4. Movement System
- `unit_move` → `manager.unit_move(x, y, x2, y2)`
- `movement_execute` → Enhanced movement
- `movement_range` → `manager.get_unit_valid_moves(unit)`
- `movement_validate` → `manager.validate_movement_detailed()`
- `movement_preview` → `manager.get_movement_preview()` ✅ IMPLEMENTED
- `unit_valid_moves` → Legacy movement range

### 5. Combat System
- `unit_attack` → `manager.unit_attack(x, y, x2, y2)`
- `unit_attack_enhanced` → `manager.unit_attack_enhanced()`
- `combat_preview` → `manager.get_damage_preview()`
- `combat_targets` → Get valid attack targets
- `damage_estimate` → `manager.damage_estimate()`

### 6. Capture System
- `capture_tile` → `manager.capture_tile(x, y)` ✅ IMPLEMENTED
- `unit_capture` → Alias for capture_tile
- `action_capture` → `manager.capture_tile_enhanced()` ✅ IMPLEMENTED
- `action_capture_preview` → `manager.get_capture_preview()` ✅ IMPLEMENTED

### 7. Transport System
- `unit_load` → `manager.unit_load()` (legacy)
- `cargo_board_transport` → Board transport AW-style
- `load_transport_unit` → `manager.load_transport_unit()` ✅ IMPLEMENTED
- `get_transport_info` → `manager.get_transport_capability()` + cargo info
- `can_transport_move` → `manager.can_transport_move()` ✅ IMPLEMENTED
- `unload_transport_unit` → `manager.unload_transport_unit()` ✅ IMPLEMENTED
- `cargo_exit_transport` → Exit transport AW-style

### 8. Economic System
- `get_army_economy` → `manager.get_army_economy()`
- `get_production_options` → `manager.get_production_options(x, y)`
- `can_afford_unit` → `manager.can_afford_unit(type, army)` ✅ IMPLEMENTED
- `get_unit_costs` → Static unit cost data

### 9. Special Actions
- `repair_unit` → Repair at black boat
- `resupply_unit` → Manual resupply
- `unit_delete` → `manager.unit_remove(x, y)`

### 10. Victory Conditions
- Checked internally by `manager.check_win_condition()` ✅ IMPLEMENTED

## Manager Methods Status

### ✅ Implemented in this session:
1. `unit_select()`
2. `capture_tile()`, `capture_tile_enhanced()`, `get_capture_preview()`
3. `check_win_condition()`, `_check_hq_capture_victory()`
4. `get_movement_preview()`, `unit_can_move_to()`
5. `produce_unit_at_facility()`
6. `can_afford_unit()`
7. Transport wrappers: `is_transport_unit()`, `get_transport_capability()`, etc.
8. `can_transport_load_unload()`

### ❓ Possibly Missing or Broken:
1. Movement validation returning "True" instead of proper response
2. Test map doesn't match test expectations
3. Some transport integration issues

## What a Complete Game Needs

For a player to play a full game, they need these workflows:

1. **Start Game**
   - Create game → See board → Check whose turn

2. **Make Units**
   - Check production options → Check affordability → Create unit

3. **Move Units**
   - Select unit → See movement range → Move to destination
   - OR: Move and load into transport

4. **Combat**
   - Select unit → See attack targets → Preview damage → Attack

5. **Capture**
   - Move infantry/mech to property → Capture → Check progress

6. **End Turn**
   - End turn → Next player acts

7. **Win**
   - Capture HQ or eliminate all enemies → Game ends
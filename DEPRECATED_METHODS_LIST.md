# Deprecated Methods to Remove

## Movement Methods (7)
1. `unit_move` → Use `movement_execute`
2. `unit_move_enhanced` → Use `movement_execute`
3. `unit_valid_moves` → Use `movement_range`
4. `movement_preview` → Use `movement_validate`
5. `validate_movement` → Use `movement_validate`
6. `get_movement_costs` → Use `movement_info`
7. `get_movement_highlights` → Use `movement_range`

## Combat Methods (6)
1. `damage_estimate` → Use `combat_preview`
2. `damage_preview` → Use `combat_preview`
3. `get_attack_targets` → Use `combat_targets`
4. `combat_preview_old` → Use `combat_preview`
5. `unit_attack` → Use `combat_attack`
6. `unit_attack_enhanced` → Use `combat_attack`

## Transport Methods (4)
1. `unit_load` → Use `transport_load`
2. `unit_unload` → Use `transport_unload`
3. `load_unit` → Use `transport_load`
4. `unload_unit` → Use `transport_unload`

## Other Deprecated Elements
1. `game_create` → Redirects to `game_create_v2`
2. `DEPRECATED` comment in game_create_rpc function

## Total: 18 deprecated RPC methods to remove
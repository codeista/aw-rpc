# AW-RPC API Quick Reference

## 🎮 Game Management
```javascript
game_create_v2({token, players, map_name})     // Create new game
game_info({token})                             // Get game state
player_stats({token, player_id?})              // Player statistics
army_end_turn({token})                         // End current turn
check_turn({token})                            // Get current turn
game_active({token})                           // Check if game active
```

## 🚛 Transport (5 methods)
```javascript
transport_info({token, x, y})                  // Get transport/cargo info
transport_loadable_units({token, x, y})        // Find loadable units
transport_load({token, transport_x, transport_y, cargo_x, cargo_y})
transport_unload_positions({token, transport_x, transport_y})
transport_unload({token, transport_x, transport_y, cargo_index, unload_x, unload_y})
```

## ⚔️ Combat (4 methods)
```javascript
combat_preview({token, attacker_x, attacker_y, defender_x, defender_y})
combat_targets({token, unit_x, unit_y})        // Note: unit_x not x
combat_attack({token, attacker_x, attacker_y, defender_x, defender_y})
combat_chart({token})                          // Get damage matchups
```

## 🏃 Movement (4 methods)
```javascript
movement_execute({token, x, y, x2, y2})        // Auto-loads transports!
movement_range({token, x, y})                  // Get valid moves
movement_validate({token, x, y, x2, y2})       // Check specific move
movement_info({token, unit_type?})             // Movement mechanics
```

## 🏭 Units & Production
```javascript
unit_create({token, army, unit_type, x, y})    // Create unit
unit_info({token, x, y})                       // Get unit details
production_options({token, x, y})              // What can be built
unit_costs({token})                            // Get all unit costs
```

## 🏰 Properties & Economy
```javascript
capture_info({token, x, y})                    // Capture progress
capture_status({token})                        // All captures
economy_summary({token})                       // Economic overview
economy_details({token, player_id?})           // Detailed economy
repair_info({token, x, y})                     // Repair costs/status
resupply_status({token, x, y})                 // Resupply info
```

## 🗺️ Map & Tiles
```javascript
game_board({token})                            // Full board state
tile_info({token, x, y})                       // Tile details
map_list()                                     // Available maps
vision_info({token, army})                     // Fog of war
```

## 📊 Game State
```javascript
unit_list({token})                             // All units
property_list({token})                         // All properties
game_history({token})                          // Move history
win_status({token})                            // Victory status
```

## 🔄 Migration Helpers
```javascript
deprecation_status({token})                    // Check deprecated methods
```

---

## Response Pattern
```javascript
// Success
{
    "success": true,
    "result": { /* data */ }      // Some methods nest under 'result'
    // OR direct properties
}

// Error
{
    "success": false,
    "error": "Error message"
}
```

## Common Gotchas
- ❌ `combat_targets` uses `unit_x/unit_y` not `x/y`
- ❌ Attack responses nest data under `result`
- ✅ Movement auto-loads into transports
- ✅ Units can't move on creation turn
- ✅ Check `can_move` and `can_attack` flags
- ✅ Terrain affects loading/unloading

## Deprecated Methods (Don't Use!)
- ❌ `unit_load`, `load_unit` → Use `transport_load`
- ❌ `unit_unload`, `unload_unit` → Use `transport_unload`
- ❌ `unit_attack` → Use `combat_attack`
- ❌ `unit_move` → Use `movement_execute`
- ❌ `damage_preview` → Use `combat_preview`
- ❌ `game_create` → Use `game_create_v2`

---
*Consolidated API v2.0 - 60% fewer methods, 100% functionality*
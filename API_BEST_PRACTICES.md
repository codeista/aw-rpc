# Advance Wars RPC API Best Practices

## Overview

This guide documents the consolidated API structure and best practices for using the Advance Wars RPC system. Following a major consolidation effort, we've reduced the API from 58+ methods to a cleaner, more intuitive set of endpoints.

## API Consolidation Summary

### Before vs After
- **Total Methods**: 58 → 23 core methods (60% reduction)
- **Transport API**: 20 → 5 methods (75% reduction)
- **Combat API**: 7 → 4 methods (43% reduction)
- **Movement API**: 8 → 4 methods (50% reduction)
- **New Features**: 7 UI information methods added

## Core API Categories

### 1. Game Management
```javascript
// Create a new game (v2 with custom players)
game_create_v2({
    token: "unique-game-id",
    players: [
        {name: "Player 1", color: "Red", sprite_color: "RED"},
        {name: "Player 2", color: "Blue", sprite_color: "BLUE"}
    ],
    map_name: "test"  // optional, defaults to "test"
})

// Get comprehensive game information
game_info({token: "game-id"})

// Get player statistics
player_stats({token: "game-id", player_id: 0})  // optional player_id

// Check deprecation status
deprecation_status({token: "game-id"})
```

### 2. Transport System (Consolidated)

The transport system has been dramatically simplified from 20 methods to just 5:

```javascript
// 1. Get transport/cargo information
transport_info({
    token: "game-id",
    x: 5,
    y: 5
})

// 2. Find units that can be loaded or transports with space
transport_loadable_units({
    token: "game-id", 
    x: 5,
    y: 5
})

// 3. Load a unit into a transport
transport_load({
    token: "game-id",
    transport_x: 5,
    transport_y: 5,
    cargo_x: 6,    // Unit to load
    cargo_y: 5
})

// 4. Get valid unload positions
transport_unload_positions({
    token: "game-id",
    transport_x: 5,
    transport_y: 5
})

// 5. Unload a unit from transport
transport_unload({
    token: "game-id",
    transport_x: 5,
    transport_y: 5,
    cargo_index: 0,  // Which cargo to unload
    unload_x: 6,
    unload_y: 5
})
```

#### Transport Best Practices:
- **Auto-loading**: Units automatically load when moving onto friendly transports
- **Manual loading**: Use `transport_load` for adjacent units with movement remaining
- **Terrain matters**: Transports must be on valid terrain to load (not sea/reef)
- **Check first**: Always use `transport_info` before attempting operations

### 3. Combat System (Consolidated)

Combat has been streamlined from 7 methods to 4:

```javascript
// 1. Preview combat before attacking
combat_preview({
    token: "game-id",
    attacker_x: 5,
    attacker_y: 5,
    defender_x: 6,
    defender_y: 5
})
// Returns: damage estimates, counter-attack info, terrain defense

// 2. Find all valid targets
combat_targets({
    token: "game-id",
    unit_x: 5,  // Note: unit_x, not just x
    unit_y: 5
})
// Returns: sorted list of targets with damage estimates

// 3. Execute an attack
combat_attack({
    token: "game-id",
    attacker_x: 5,
    attacker_y: 5,
    defender_x: 6,
    defender_y: 5
})
// Returns: actual damage dealt, HP changes, game state

// 4. Get damage matchup chart
combat_chart({
    token: "game-id"
})
// Returns: complete damage table for all unit matchups
```

#### Combat Best Practices:
- Always use `combat_preview` before attacking to show player expected outcome
- Check `can_counter` flag to warn about counter-attacks
- Verify unit has `can_attack=true` before attempting attack
- Sort targets by damage for better UX

### 4. Movement System (Consolidated)

Movement simplified from 8 methods to 4:

```javascript
// 1. Execute unit movement
movement_execute({
    token: "game-id",
    x: 5,      // From position
    y: 5,
    x2: 8,     // To position
    y2: 5
})
// Auto-loads into transports if applicable

// 2. Get all valid movement positions
movement_range({
    token: "game-id",
    x: 5,
    y: 5
})
// Returns: array of valid positions with movement costs

// 3. Validate specific movement
movement_validate({
    token: "game-id",
    x: 5,
    y: 5,
    x2: 8,
    y2: 5
})
// Returns: whether move is valid and why

// 4. Get movement mechanics info
movement_info({
    token: "game-id",
    unit_type: "TANK"  // optional
})
// Returns: movement costs, terrain restrictions
```

#### Movement Best Practices:
- Use `movement_range` to highlight valid moves
- Always validate before executing movement
- Remember units auto-load into friendly transports
- Check `can_move` flag before attempting movement

### 5. UI Information Methods (New)

These methods provide essential information for rich UI features:

```javascript
// Capture information
capture_info({token: "game-id", x: 5, y: 5})
capture_status({token: "game-id"})

// Economic information  
economy_summary({token: "game-id"})
economy_details({token: "game-id", player_id: 0})

// Repair and resupply
repair_info({token: "game-id", x: 5, y: 5})
resupply_status({token: "game-id", x: 5, y: 5})

// Production capabilities
production_options({token: "game-id", x: 5, y: 5})
```

## Migration Guide

### From Old to New APIs

#### Transport Operations
```javascript
// OLD: Multiple methods for loading
unit_load() / load_unit() / load_transport_unit()

// NEW: Single method
transport_load()

// OLD: Multiple unload methods
unit_unload() / unload_unit() / cargo_exit_transport()

// NEW: Single method
transport_unload()
```

#### Combat Operations
```javascript
// OLD: Multiple preview methods
damage_estimate() / damage_preview() / combat_preview_old()

// NEW: Single comprehensive preview
combat_preview()

// OLD: Multiple attack methods
unit_attack() / unit_attack_enhanced()

// NEW: Single method
combat_attack()
```

#### Movement Operations
```javascript
// OLD: Multiple movement methods
unit_move() / unit_move_enhanced()

// NEW: Single method with auto-load
movement_execute()

// OLD: Various validation methods
validate_movement() / can_transport_move()

// NEW: Single validation
movement_validate()
```

## Response Structures

### Standard Success Response
```json
{
    "success": true,
    "result": {
        // Method-specific data
    }
}
```

### Standard Error Response
```json
{
    "success": false,
    "error": "Descriptive error message"
}
```

### Combat Preview Response
```json
{
    "success": true,
    "attacker": {
        "type": "TANK",
        "hp_current": 100,
        "hp_after": 73,
        "ammo_current": 6,
        "ammo_after": 5
    },
    "defender": {
        "type": "INFANTRY", 
        "hp_current": 100,
        "hp_after": 45,
        "terrain_defense": 2
    },
    "damage": {
        "attacker_damage": 55,
        "attacker_damage_range": {"min": 49, "max": 60},
        "can_counter": true,
        "counter_damage": 27,
        "counter_damage_range": {"min": 24, "max": 29}
    }
}
```

## Best Practices Summary

1. **Use Consolidated Methods**: Avoid deprecated methods marked with [DEPRECATED]
2. **Check Before Acting**: Use preview/validate methods before executing actions
3. **Handle All Response Types**: Check `success` flag and handle errors gracefully
4. **Leverage Auto-Features**: Movement auto-loads transports, no separate call needed
5. **Use V2 for New Games**: `game_create_v2` supports custom players and future features
6. **Cache When Appropriate**: Combat chart and movement info rarely change
7. **Batch Related Calls**: Get all needed info in fewer calls with richer responses

## Common Patterns

### Attack Flow
```javascript
// 1. Get targets
const targets = await rpc('combat_targets', {token, unit_x: 5, unit_y: 5});

// 2. User selects target, show preview
const preview = await rpc('combat_preview', {
    token, 
    attacker_x: 5, 
    attacker_y: 5,
    defender_x: 6,
    defender_y: 5
});

// 3. User confirms, execute attack
const result = await rpc('combat_attack', {
    token,
    attacker_x: 5,
    attacker_y: 5, 
    defender_x: 6,
    defender_y: 5
});
```

### Transport Flow
```javascript
// 1. Check if position has transport
const info = await rpc('transport_info', {token, x: 5, y: 5});

if (info.is_transport && info.current_cargo < info.max_capacity) {
    // 2. Find loadable units
    const loadable = await rpc('transport_loadable_units', {token, x: 5, y: 5});
    
    // 3. Load selected unit
    await rpc('transport_load', {
        token,
        transport_x: 5,
        transport_y: 5,
        cargo_x: 6,
        cargo_y: 5
    });
}
```

## Performance Tips

1. **Minimize Calls**: Use rich responses instead of multiple calls
2. **Cache Static Data**: Combat chart, unit costs rarely change
3. **Batch Updates**: Get game state once after actions
4. **Use Appropriate Methods**: Don't use preview methods for simple checks
5. **Handle Errors Locally**: Validate on client when possible

## Troubleshooting

### Common Issues

1. **"Unit has already moved"**: Check `can_move` flag before movement
2. **"Not your turn"**: Verify `current_turn` matches unit's army
3. **"Invalid position"**: Use validation methods before executing
4. **"Transport full"**: Check capacity with `transport_info` first
5. **"Out of range"**: Use `combat_targets` to get valid targets

### Debug Information

Enable debug logging by checking:
- Server logs at `/logs/awrpc.log`
- Error responses include detailed messages
- Use `game_info` for comprehensive state

## Future Compatibility

The consolidated API is designed for future expansion:
- Team game support through player system
- AI players through v2 architecture  
- New unit types without API changes
- Additional game modes via same endpoints

---

*Last Updated: 2024-01-26*
*API Version: 2.0*
*Consolidation Complete*
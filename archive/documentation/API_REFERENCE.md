# Advance Wars RPC - API Reference

## Overview
This document provides comprehensive documentation for all RPC API methods in the Advance Wars RPC game engine. Methods are organized by functionality and documented with examples.

## Base URL
- **RPC Endpoint**: `http://localhost:5000/api`
- **API Browser**: `http://localhost:5000/api/browse`

## Method Categories

### 🎮 Game Management
Core methods for creating, managing, and accessing game state.

#### `game_create(token: str) -> str`
Creates a new standard game with 5,000 starting funds.
```javascript
rpc('game_create', {token: 'mygame'})
```

#### `game_create_test(token: str, use_optimized: bool = true) -> str`
Creates a test game with 50,000 starting funds and optionally pre-deployed units.
```javascript
rpc('game_create_test', {token: 'testgame', use_optimized: true})
```

#### `game_create_with_setup(token: str, game_setup: dict) -> str`
Creates a game with custom setup parameters.
```javascript
rpc('game_create_with_setup', {
    token: 'customgame',
    game_setup: {funds: 25000, map: 'custom'}
})
```

#### `game_board(token: str) -> dict`
Returns complete game board state including units, tiles, and game status.
```javascript
rpc('game_board', {token: 'mygame'})
```

#### `army_end_turn(token: str) -> dict`
Ends the current army's turn and passes control to the next player.
```javascript
rpc('army_end_turn', {token: 'mygame'})
```

#### `game_delete(token: str) -> str`
Deletes a game and all associated data.
```javascript
rpc('game_delete', {token: 'mygame'})
```

#### `check_turn(token: str) -> dict`
Returns current turn information and game status.
```javascript
rpc('check_turn', {token: 'mygame'})
```

---

### 🪖 Unit Operations
Methods for unit movement, selection, and basic actions.

#### `unit_select(token: str, x: int, y: int) -> dict`
Selects a unit at the specified coordinates.
```javascript
rpc('unit_select', {token: 'mygame', x: 5, y: 3})
```

#### `unit_move(token: str, x: int, y: int, x2: int, y2: int) -> dict`
Moves a unit from (x, y) to (x2, y2).
```javascript
rpc('unit_move', {token: 'mygame', x: 5, y: 3, x2: 6, y2: 3})
```

#### `unit_move_enhanced(token: str, from_x: int, from_y: int, to_x: int, to_y: int) -> dict`
Enhanced movement with automatic transport boarding detection.
```javascript
rpc('unit_move_enhanced', {token: 'mygame', from_x: 5, from_y: 3, to_x: 6, to_y: 3})
```

#### `unit_create(token: str, army: str, unit_type: str, x: int, y: int) -> dict`
Creates a new unit at production facility.
```javascript
rpc('unit_create', {
    token: 'mygame', 
    army: 'RED', 
    unit_type: 'INFANTRY', 
    x: 2, 
    y: 3
})
```

---

### ⚔️ Combat System
Methods for attacking and combat previews.

#### `unit_attack(token: str, x: int, y: int, x2: int, y2: int) -> dict`
Execute an attack from unit at (x, y) to target at (x2, y2).
```javascript
rpc('unit_attack', {token: 'mygame', x: 5, y: 3, x2: 6, y2: 3})
```

#### `combat_preview(token: str, attacker_x: int, attacker_y: int, defender_x: int, defender_y: int) -> dict`
Get detailed combat damage preview before attacking.
```javascript
rpc('combat_preview', {
    token: 'mygame',
    attacker_x: 5, attacker_y: 3,
    defender_x: 6, defender_y: 3
})
```

#### `get_attack_targets(token: str, unit_x: int, unit_y: int) -> dict`
Get all valid attack targets for a unit.
```javascript
rpc('get_attack_targets', {token: 'mygame', unit_x: 5, unit_y: 3})
```

#### `get_damage_chart(token: str) -> dict`
Returns the complete damage chart for reference.
```javascript
rpc('get_damage_chart', {token: 'mygame'})
```

---

### 🚢 Transport System
Methods for loading and unloading units in transports.

#### `load_unit(token: str, transport_x: int, transport_y: int, cargo_x: int, cargo_y: int) -> dict`
Load a cargo unit into a transport.
```javascript
rpc('load_unit', {
    token: 'mygame',
    transport_x: 5, transport_y: 3,
    cargo_x: 4, cargo_y: 3
})
```

#### `unload_unit(token: str, transport_x: int, transport_y: int, unload_x: int, unload_y: int, cargo_index: int = 0) -> dict`
Unload a unit from transport to specified position.
```javascript
rpc('unload_unit', {
    token: 'mygame',
    transport_x: 5, transport_y: 3,
    unload_x: 6, unload_y: 3,
    cargo_index: 0
})
```

#### `get_valid_unload_positions(token: str, x: int, y: int) -> dict`
Get all valid positions where a transport can unload cargo.
```javascript
rpc('get_valid_unload_positions', {token: 'mygame', x: 5, y: 3})
```

#### `get_transport_info(token: str, x: int, y: int) -> dict`
Get detailed information about a transport unit.
```javascript
rpc('get_transport_info', {token: 'mygame', x: 5, y: 3})
```

#### `get_cargo_info(token: str, x: int, y: int) -> dict`
Get detailed cargo information for a transport.
```javascript
rpc('get_cargo_info', {token: 'mygame', x: 5, y: 3})
```

#### `can_load_unit(token: str, transport_x: int, transport_y: int, cargo_x: int, cargo_y: int) -> dict`
Check if a unit can be loaded into a transport.
```javascript
rpc('can_load_unit', {
    token: 'mygame',
    transport_x: 5, transport_y: 3,
    cargo_x: 4, cargo_y: 3
})
```

---

### 🏭 Production System
Methods for unit production and facility management.

#### `produce_unit(token: str, x: int, y: int, unit_type: str) -> dict`
Produce a unit at a production facility.
```javascript
rpc('produce_unit', {
    token: 'mygame',
    x: 2, y: 3,
    unit_type: 'TANK'
})
```

#### `get_production_options(token: str, x: int, y: int) -> dict`
Get all units that can be produced at a facility.
```javascript
rpc('get_production_options', {token: 'mygame', x: 2, y: 3})
```

#### `can_afford_unit(token: str, unit_type: str) -> dict`
Check if current army can afford a specific unit type.
```javascript
rpc('can_afford_unit', {token: 'mygame', unit_type: 'NEOTANK'})
```

#### `get_unit_costs(token: str) -> dict`
Get cost information for all unit types.
```javascript
rpc('get_unit_costs', {token: 'mygame'})
```

---

### 💰 Economy System
Methods for managing funds and economic information.

#### `get_army_economy(token: str) -> dict`
Get complete economic summary for current army.
```javascript
rpc('get_army_economy', {token: 'mygame'})
```

#### `get_army_facilities(token: str) -> dict`
Get all production facilities owned by current army.
```javascript
rpc('get_army_facilities', {token: 'mygame'})
```

---

### 🛠️ Special Actions
Methods for special unit abilities and actions.

#### `capture_tile(token: str, x: int, y: int) -> dict`
Capture a property with an infantry or mech unit.
```javascript
rpc('capture_tile', {token: 'mygame', x: 5, y: 3})
```

#### `repair_unit(token: str, blackboat_x: int, blackboat_y: int, target_x: int, target_y: int, hp_to_repair: int = 1) -> dict`
Use Black Boat to repair adjacent unit (costs funds, max 10 visual HP).
```javascript
rpc('repair_unit', {
    token: 'mygame',
    blackboat_x: 5, blackboat_y: 3,
    target_x: 5, target_y: 4,
    hp_to_repair: 2
})
```

#### `resupply_unit(token: str, resupply_x: int, resupply_y: int, target_x: int, target_y: int, fuel_amount: int = 10, ammo_amount: int = 10) -> dict`
Manual resupply from APC or Black Boat (free).
```javascript
rpc('resupply_unit', {
    token: 'mygame',
    resupply_x: 5, resupply_y: 3,
    target_x: 6, target_y: 3,
    fuel_amount: 20,
    ammo_amount: 5
})
```

---

### 🗺️ Map & Tile Information
Methods for accessing map and tile data.

#### `tile(token: str, x: int, y: int) -> dict`
Get detailed information about a specific tile.
```javascript
rpc('tile', {token: 'mygame', x: 5, y: 3})
```

#### `troop_info(token: str = null) -> dict`
Get unit configuration and reference data.
```javascript
rpc('troop_info', {})
```

---

### 🎯 Movement & Validation
Methods for movement validation and previews.

#### `unit_valid_moves(token: str, x: int, y: int) -> dict`
Get all valid moves for a unit.
```javascript
rpc('unit_valid_moves', {token: 'mygame', x: 5, y: 3})
```

#### `validate_movement(token: str, x: int, y: int, x2: int, y2: int) -> dict`
Validate a specific movement and get detailed information.
```javascript
rpc('validate_movement', {
    token: 'mygame',
    x: 5, y: 3,
    x2: 7, y: 3
})
```

#### `movement_preview(token: str, x: int, y: int, x2: int, y2: int) -> dict`
Get movement preview information.
```javascript
rpc('movement_preview', {
    token: 'mygame',
    x: 5, y: 3,
    x2: 7, y: 3
})
```

#### `get_movement_costs(unit_type: str, token: str) -> dict`
Get movement costs for a unit type across all terrain types.
```javascript
rpc('get_movement_costs', {unit_type: 'INFANTRY', token: 'mygame'})
```

#### `get_movement_highlights(x: int, y: int, token: str) -> dict`
Get valid movement positions for UI highlighting.
```javascript
rpc('get_movement_highlights', {x: 5, y: 3, token: 'mygame'})
```

---

### 💬 Communication
Methods for chat and messaging.

#### `message(token: str, msg: str) -> str`
Send a chat message in the game.
```javascript
rpc('message', {token: 'mygame', msg: 'Good game!'})
```

---

## Legacy Methods (Compatibility)

These methods are maintained for frontend compatibility but are aliases for newer methods:

- `unit_load` → Use `load_unit`
- `unit_unload` → Use `unload_unit`
- `damage_estimate` → Use `combat_preview`
- `damage_preview` → Use `combat_preview`

## Error Handling

All RPC methods return consistent error responses:
```json
{
    "success": false,
    "error": "Error description"
}
```

## Authentication

All methods require a `token` parameter for game identification. Create a game first using `game_create` or `game_create_test`.

## Testing

Use the API browser at `http://localhost:5000/api/browse` to test methods interactively.
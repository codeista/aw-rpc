# Deprecated Method Migration Guide

## Frontend Files Using Deprecated Methods

### Files using `unit_move`:
- `/static/js/minimal_game.js:91`
- `/static/js/modules/gameActions.js:164`
- `/static/js/minimal_game_v2.js:106`
- `/static/js/game_v2_simple.js:204`
- `/static/js/transport_integration.js:129`

### Files using `unit_move_enhanced`:
- `/static/js/transport_integration.js:169`

### Test files using deprecated methods:
- `tests/regression/test_complete_game_mechanics.py` - uses `unit_move`

## Migration Steps

### 1. Update Frontend Calls

#### Replace `unit_move` with `movement_execute`:
```javascript
// OLD:
await this.rpc('unit_move', {
    x: fromX, y: fromY,
    x2: toX, y2: toY
});

// NEW:
await this.rpc('movement_execute', {
    from_x: fromX, from_y: fromY,
    to_x: toX, to_y: toY
});
```

#### Replace `unit_move_enhanced` with `movement_execute`:
```javascript
// OLD:
jsonrpc('unit_move_enhanced', {
    from_x: fromX, from_y: fromY,
    to_x: toX, to_y: toY
});

// NEW: (same parameters!)
jsonrpc('movement_execute', {
    from_x: fromX, from_y: fromY,
    to_x: toX, to_y: toY
});
```

### 2. Update Test Calls

```python
# OLD:
result = self.rpc_call('unit_move', {'x': 0, 'y': 8, 'x2': 1, 'y2': 8})

# NEW:
result = self.rpc_call('movement_execute', {'from_x': 0, 'from_y': 8, 'to_x': 1, 'to_y': 8})
```

### 3. Combat Method Updates

#### Replace `unit_attack` with `combat_attack`:
```javascript
// Parameters stay the same
```

### 4. Transport Method Updates

#### Replace `unit_load` with `transport_load`:
```javascript
// Parameters stay the same
```

## Order of Operations

1. First update all frontend JavaScript files
2. Update test files
3. Test everything works
4. Then remove deprecated methods from app.py
# RPC Method Cleanup Summary

## Removed Duplicate RPC Methods

### 1. `game_create` 
- **Removed**: Old game creation method that used hardcoded RED/BLUE armies
- **Replacement**: Use `game_create_v2` which supports flexible player configuration
- **Location**: Line 2236

### 2. `unit_attack` (duplicate)
- **Removed**: Duplicate definition at line 2799-2896
- **Kept**: The version at line 4706 which is an alias to `unit_attack_enhanced`
- **Reason**: Having two definitions of the same RPC method causes conflicts

### 3. Updated `game_create_test`
- **Changed**: Now uses v2 system internally
- **Features**: 
  - Creates v2 games with high starting funds (50k)
  - Uses GameFactory for proper player management
  - Maintains backward compatibility

## Benefits of Cleanup

1. **Cleaner API**: No more confusion about which method to use
2. **Consistent**: All game creation now flows through v2 system
3. **Maintainable**: Single code path for game creation
4. **Future-proof**: Ready for more than 2 players

## Migration Notes

For any code using the old methods:
- Replace `game_create` with `game_create_v2`
- The `game_create_v2` method accepts optional parameters:
  - `players`: Array of player configurations
  - `map_name`: Name of the map to use

Example:
```javascript
// Old way
rpc('game_create', { token: 'mygame' })

// New way
rpc('game_create_v2', { 
  token: 'mygame',
  map_name: 'test',
  players: [
    { name: 'Player 1', color: 'Red', sprite_color: 'RED' },
    { name: 'Player 2', color: 'Blue', sprite_color: 'BLUE' }
  ]
})
```
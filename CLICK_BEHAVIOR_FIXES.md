# Click Behavior Fixes - 2025-07-26

## Issues Fixed

### 1. Factory Movement Priority (Fixed)
**Problem**: When a unit was selected and player clicked on their own empty factory, the production menu would appear instead of moving the unit there.

**Root Cause**: Click handler checked for production buildings before checking if the tile was a valid movement destination.

**Fix**: Reordered click priorities in `game_v2_simple.js`:
1. Check if tile is a valid movement destination (`can_be_moved_to`)
2. Check if unit has already acted
3. Check if clicking on empty production building (only if NOT a movement target)
4. Try attack if not a movement target

**Result**: Units can now move to empty factories when they're valid movement destinations.

### 2. Attack Menu Reliability (Fixed)
**Problem**: Attack option in context menu was unreliable - sometimes wouldn't show enemies, targets would show as 0, or menu would disappear.

**Root Cause**: `handleAttackFromContextMenu` relied on client-side `can_be_attacked` flags that were cleared whenever the board state was updated by any RPC call.

**Fix**: Updated `handleAttackFromContextMenu` to fetch fresh attack targets from server using `combat_targets` RPC instead of relying on client-side state.

**Result**: Attack menu now reliably shows all valid targets and works consistently.

## Movement Rules Clarification

In Advance Wars, units **cannot** move to tiles occupied by other units, with these exceptions:
1. **Loading into transports** - Infantry/Mech can load into APC/Lander/etc
2. **Joining units** - Units of same type can merge to combine HP

This is working correctly in the current implementation. The issue was only with click priority, not movement validation.

## Testing Instructions

### Test 1: Moving to Empty Factory
1. Create a test game
2. Build a unit near a factory
3. Next turn, select the unit
4. Click on the empty factory - unit should move there
5. Click on empty factory without unit selected - production menu should appear

### Test 2: Attack Menu with Multiple Targets
1. Use combat test scenario
2. Move a unit near multiple enemies
3. Right-click unit → Attack
4. Should fetch and display all valid targets
5. Select target - attack should execute

## Code Changes

### game_v2_simple.js - Click Priority Fix
```javascript
// PRIORITY 1: Check if this tile is highlighted for movement
if (clickedTile && clickedTile.can_be_moved_to) {
    // Movement logic
}

// PRIORITY 2: Check if unit has already moved/acted
// ... 

// PRIORITY 3: Check if clicking on empty production building (ONLY if not a move target)
if (clickedTile && !clickedTile.unit && clickedTile.mapTile && 
    ['FACTORY', 'AIRPORT', 'PORT'].includes(clickedTile.mapTile.type) &&
    !clickedTile.can_be_moved_to) {  // Only show production if NOT a valid move
    // Production menu logic
}
```

### game_v2_simple.js - Attack Menu Fix
```javascript
async handleAttackFromContextMenu(x, y) {
    // Fetch valid attack targets from server to ensure fresh data
    const result = await this.rpc('combat_targets', { unit_x: x, unit_y: y });
    
    if (!result.success || !result.targets || result.targets.length === 0) {
        console.log('No valid attack targets found');
        return;
    }
    
    // Convert and use server response
    const attackTargets = result.targets.map(target => ({
        x: target.x,
        y: target.y,
        unit: target.unit
    }));
    // ... rest of logic
}
```

## Related Files
- `static/js/game_v2_simple.js` - Main game UI logic
- `enhanced_movement_validation.py` - Movement validation (unchanged, working correctly)
- `app.py` - RPC endpoints including `combat_targets`
# Unit Selection Success Criteria

## What Should Happen When Unit Selection Works

### 1. ✅ Board State Update
- `board.selected` should be set to the selected tile object
- Contains x, y coordinates and unit data
- **Current Status**: WORKING ✅
  - Example: `{x: 2, y: 3, unit: {type: 'INFANTRY', ...}}`

### 2. ✅ Movement Highlights 
- Yellow tiles should appear showing valid movement positions
- Number of highlights depends on unit movement range and terrain
- **Current Status**: WORKING ✅
  - Infantry showed 14 movement tiles initially, 28 after second check

### 3. ⚠️ GameState Update
- `gameState.selectedUnit` should reference the selected unit
- `gameState.selectedX` and `selectedY` should be set
- **Current Status**: NOT WORKING ❌
  - gameState.selectedUnit remains null/false

### 4. ✅ Visual Feedback
- Selected unit should be visually highlighted
- Movement range overlay should appear
- **Current Status**: PARTIALLY WORKING ⚠️
  - Movement highlights appear but unit highlight unclear

### 5. ⚠️ Attack Highlights (if applicable)
- Red tiles should show attackable enemies
- Only after movement or for ranged units
- **Current Status**: NEEDS MANUAL TRIGGER ⚠️
  - showAttackTargets() must be called manually

### 6. ✅ RPC Communication
- unit_select RPC should succeed
- Returns unit data from backend
- **Current Status**: WORKING ✅
  - Returns full unit data with stats

## Expected Flow

1. User clicks on unit
2. advanceWarsCanvasClick fires
3. processClick determines it's a unit selection
4. advanceWarsUnitSelect is called with tile
5. RPC call to backend with token, x, y
6. On success:
   - board.selected = tile ✅
   - gameState.selectedUnit = tile ❌
   - showMovementRange() called ✅
   - Movement highlights rendered ✅
   - Attack highlights shown (if needed) ⚠️

## Current Issues

1. **gameState.selectedUnit not being set**
   - Line exists in code but not executing
   - Might be overwritten elsewhere

2. **Attack highlights need manual trigger**
   - Should automatically show after selection
   - Currently requires showAttackTargets() call

3. **Visual unit highlight unclear**
   - Movement tiles show but unit itself may not be visually distinct

## Success Metrics

- [x] board.selected is set
- [x] Movement highlights appear (14+ tiles)
- [ ] gameState.selectedUnit is set
- [ ] Attack highlights appear automatically
- [x] No JavaScript errors
- [x] Selection persists until cleared

## Test Results
- Direct function call: SUCCESS
- Movement highlights: 14 initially, 28 on recheck (working)
- Click through canvas: NEEDS VERIFICATION
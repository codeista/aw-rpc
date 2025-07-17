# UI Issues Summary

## Current Status

### ✅ Working
1. **Mouse controls** - Clicks register properly after removing 200ms throttle
2. **Factory detection** - Correctly identifies production buildings
3. **Unit creation** - Units are created successfully via API
4. **Game mechanics** - Units can move, attack, and play normally
5. **Sprite display** - Works correctly after page refresh

### ❌ Issues to Fix

#### 1. Unit Creation Modal Not Visible
- **Problem**: Modal is set to display:block but doesn't appear on screen
- **Workaround**: Use `createInfantry()`, `createTank()` etc. in console
- **Files**: `render_legacy.js`, `force-factory-fix.js`

#### 2. Sprite Rendering on Creation
- **Problem**: New units show as black box until page refresh
- **Workaround**: Auto-refresh fix applied, or manual refresh
- **Error**: "Unavailable Infantry sprite key: undefined"
- **Files**: Sprite system in `render_legacy.js`

#### 3. Coordinate Alignment
- **Problem**: Clicking on (0,4) registers as (0,3)
- **Impact**: Minor - users can adjust clicks
- **Cause**: Scene offset calculation issue

## Quick Fixes Applied

1. **Direct unit creation**: 
   ```javascript
   createInfantry()  // Creates infantry at RED factory
   createTank()      // Creates tank at RED factory
   ```

2. **Auto-refresh**: Sprites now refresh automatically after unit creation

3. **Factory locations identified**:
   - RED Factory at (0,3)
   - RED Port at (0,0)
   - RED Airport at (0,8)

## Todo Items
- Fix unit sprite rendering on initial creation
- Fix unit creation modal visibility
- Improve coordinate alignment
- Fix Selenium test framework issues
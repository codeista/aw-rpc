# Comprehensive UI/UX Issues Review

## Critical Issues 🔴

### 1. Map Jumping/Glitching on Mouse Hover
- **Symptom**: Map jumps around when hovering mouse after moving infantry
- **Root Cause**: Dynamic scene translation offset calculation issues
- **Code Location**: `tileAt()` function in render_legacy.js
- **Issue**: `window.two?.scene?.translation?.y` may be changing dynamically
- **Status**: Partially fixed null checks, but jumping persists

### 2. Coordinate System Misalignment  
- **Symptom**: Mouse clicks/hovers don't align with visual tiles
- **Root Cause**: Scene offset calculation using dynamic values
- **Code**: `var sceneOffsetY = window.two?.scene?.translation?.y || window.TILESIZE;`
- **Impact**: Makes precise unit selection difficult

## Fixed Issues ✅

### 1. End Turn Logger Crash
- **Fixed**: Added null checks in manager.py
- **Result**: End turn works without errors

### 2. Null Reference Errors in canvasMove
- **Fixed**: Added proper null checks for tile object
- **Result**: No more JavaScript errors on hover

### 3. Missing Sprite Files
- **Fixed**: Restored from backup
- **Result**: All units render correctly

## UI/UX Problems to Address 🟡

### 1. Visual Feedback Issues
- **Movement Range**: Not clearly visible when unit selected
- **Attack Range**: No visual indicators for possible targets
- **Hover State**: Inconsistent cursor changes
- **Selection State**: No clear highlight on selected unit

### 2. Production Menu
- **Issue**: Dropdown visibility unknown (needs browser testing)
- **Expected**: Should show list of 12 units with costs
- **Location**: Factory click interaction

### 3. Transport UI
- **Loading**: No clear visual feedback when unit can board
- **Unloading**: Right-click menu positioning unclear
- **Cargo Display**: No indication of units inside transports

### 4. Turn Indicators
- **Current Turn**: Not prominently displayed
- **Day Counter**: Location unclear
- **Army Funds**: Not visible during gameplay

### 5. Mobile/Touch Support
- **Touch Events**: Basic support exists but untested
- **Drag Handling**: May conflict with map panning
- **Long Press**: Implemented but behavior unclear

## Code Quality Issues 🟠

### 1. Global Variable Dependencies
- `window.two`, `window.board`, `window.draw` used without checks
- Scene translation accessed dynamically
- No consistent coordinate system

### 2. Event Handler Conflicts
- Multiple click handlers (canvas, centralized, transport)
- Touch and mouse events may overlap
- Context menu prevention inconsistent

### 3. Rendering Performance
- Full scene redraws on every update
- No dirty rectangle optimization
- Movement highlights recreated each frame

## Recommended Fixes Priority

### Immediate (High Priority)
1. **Fix map jumping**: Lock scene translation or use fixed offsets
2. **Stabilize coordinate system**: Consistent tile-to-pixel mapping
3. **Add visual selection indicators**: Clear unit/tile highlights

### Short Term (Medium Priority)
1. **Improve movement/attack range display**
2. **Test and fix production menu dropdown**
3. **Add turn/funds display UI**
4. **Implement proper hover tooltips**

### Long Term (Low Priority)
1. **Optimize rendering performance**
2. **Improve mobile/touch experience**
3. **Add animation transitions**
4. **Implement sound effects**

## Testing Checklist

### Browser Testing Needed
- [ ] Production menu dropdown visibility
- [ ] Unit selection highlighting
- [ ] Movement path preview
- [ ] Attack range indicators
- [ ] Transport loading/unloading UI
- [ ] Turn transition animations
- [ ] Victory/defeat screens

### Interaction Testing
- [ ] Click accuracy on all tile types
- [ ] Double-click for capture/wait
- [ ] Right-click for transport menu
- [ ] Alt-click for special actions
- [ ] Keyboard shortcuts
- [ ] Touch gestures on mobile

### Visual Polish
- [ ] Consistent color scheme
- [ ] Clear status indicators
- [ ] Readable text at all zoom levels
- [ ] Smooth transitions
- [ ] Loading states

## Next Steps

1. **Fix the coordinate jumping issue first** - This is breaking basic gameplay
2. **Add proper visual feedback** - Selection, movement, attack ranges
3. **Test all interactions in browser** - Using test game URL
4. **Polish the production menu** - Ensure dropdown works and is styled
5. **Add missing UI elements** - Turn info, funds, etc.
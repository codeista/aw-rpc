# Click Handler System Documentation

## Overview

The Advance Wars RPC game uses a centralized, priority-based click handling system to manage all canvas interactions. This ensures consistent behavior and prevents conflicts between different click actions.

## Architecture

### File Structure
- `/static/js/click-handler.js` - Main click handler implementation
- `/static/js/test-click-handler.js` - Comprehensive test suite
- `/static/js/render_legacy.js` - Integration with legacy renderer

### Priority System

The click handler uses a priority-based system with the following categories (in order of execution):

1. **Modals** - Highest priority for overlay interactions
2. **Modifiers** - Special keyboard modifiers (Ctrl, Alt, Shift)
3. **Contextual** - Context-specific actions (transport unload, attack targets)
4. **Production** - Production building clicks
5. **Selection** - Unit selection
6. **Movement** - Unit movement
7. **Fallback** - Default/cleanup handlers

### Handler Registration

```javascript
registerClickHandler(category, {
    name: 'unique-handler-name',
    priority: 0,  // Lower = higher priority within category
    condition: (tile, event) => {
        // Return true if handler should process this click
        return tile.unit && tile.unit.army === window.board.current_turn;
    },
    handle: (tile, event) => {
        // Process the click
        // Return true to consume event, false to continue
        return true;
    }
});
```

## Built-in Handlers

### Production Buildings
- **Condition**: Factory/Airport/Port owned by current player with no unit
- **Action**: Opens production modal (unitCreate/airunitCreate/seaunitCreate)

### Unit Selection
- **Condition**: Click on unit owned by current player
- **Action**: Selects unit, shows movement/attack ranges

### Movement Execution
- **Condition**: Selected unit, click on valid movement tile
- **Action**: Executes unit movement

### Attack Execution
- **Condition**: Selected unit, click on enemy within attack range
- **Action**: Executes attack

### Alt-Click Transport
- **Condition**: Alt key held during click
- **Action**: Special transport operations (load/unload)

### Clear Selection
- **Condition**: Click on empty tile with no special state
- **Action**: Clears selection and all highlights

## Integration

### Initialization
The click handler automatically initializes after the canvas is created:

```javascript
// Waits 3 seconds after DOM ready to ensure canvas exists
setTimeout(initializeClickHandler, 3000);

// Re-initializes if render_legacy.js is detected
if (window.clickHandler && window.clickHandler.initialize) {
    window.clickHandler.initialize();
}
```

### Canvas Setup
The handler replaces the default canvas onclick:

```javascript
canvas.onclick = function centralizedClickHandler(event) {
    const tile = window.tileAt(event.offsetX, event.offsetY);
    if (tile) {
        processClick(tile, event);
    }
};
```

## Testing

### Automated Tests
Run the comprehensive test suite:

```bash
# Command line
python3 test_click_handling.py

# Browser console
const tester = new ClickHandlerTests();
await tester.runAllTests();
```

### Test Coverage
- Handler initialization
- Empty tile clicks
- Unit selection
- Movement execution
- Production building clicks
- Attack execution
- Alt-click handling
- Priority system

### Manual Testing
1. Open game in browser
2. Click "🧪 Test Clicks" button
3. Check console for test results

## Debugging

### Enable Debug Logging
The click handler includes extensive debug logging:

```javascript
// In processClick function
logger.debug('Click processing started', {
    tile: { x: tile.x, y: tile.y },
    boardLoaded: !!window.board,
    currentTurn: window.board?.current_turn
});
```

### Common Issues

1. **Clicks not registering**
   - Check if canvas has onclick handler
   - Verify window.board and window.tileAt exist
   - Ensure click handler initialized (look for log message)

2. **Wrong handler triggered**
   - Check handler priorities
   - Verify condition functions
   - Look for overlapping conditions

3. **Handler not found**
   - Ensure handler is registered before clicks
   - Check handler name spelling
   - Verify category exists

## Adding Custom Handlers

### Example: Special Building Handler
```javascript
window.clickHandler.register('contextual', {
    name: 'special-building',
    priority: 5,
    condition: (tile, event) => {
        return tile.mapTile?.type === 'SPECIAL_BUILDING' && 
               !tile.unit;
    },
    handle: (tile, event) => {
        console.log('Special building clicked!');
        showSpecialBuildingMenu(tile);
        return true; // Consume the click
    }
});
```

### Best Practices
1. Use descriptive handler names
2. Keep condition checks fast
3. Return true to consume clicks
4. Clean up highlights in handlers
5. Test with existing handlers

## Coordinate System

The click handler accounts for the scene offset:

```javascript
function tileAt(px, py) {
    var sceneOffsetY = window.two?.scene?.translation?.y || window.TILESIZE;
    var adjustedY = py - sceneOffsetY;
    var tileX = Math.floor(px / window.TILESIZE);
    var tileY = Math.floor(adjustedY / window.TILESIZE);
    return getTile(tileX, tileY);
}
```

## Performance

- Handlers execute synchronously in priority order
- First handler to return true stops propagation
- Minimal overhead (~1-2ms per click)
- No throttling needed due to efficient design

## Future Enhancements

1. **Touch Support** - Add touch event handlers
2. **Drag Operations** - Support drag for unit movement
3. **Context Menus** - Right-click context menus
4. **Gesture Support** - Pinch zoom, swipe actions
5. **Accessibility** - Keyboard navigation support
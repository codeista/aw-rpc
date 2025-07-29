# Frontend Design Violations & Fixes

## Critical Issues to Fix

### 1. **Excessive Console Logging (76 instances)**
**Violation**: Debug code in production
**Fix**: Add DEBUG flag

```javascript
// Add at top of file
const DEBUG = false;

// Replace all console.log with:
if (DEBUG) console.log(...);
```

### 2. **Magic Numbers Throughout**
**Violation**: Hard-coded values
**Examples**:
- `this.tileSize = 32`
- `if (tile.x === 0 && tile.y === 4)`
- `modal.style.width = '300px'`

**Fix**: Create constants
```javascript
const CONSTANTS = {
    TILE_SIZE: 32,
    MODAL_WIDTH: 300,
    DEFAULT_FACTORY: {x: 0, y: 4},
    MAX_CARGO: 2,
    CAPTURE_HP: 20
};
```

### 3. **Massive Functions**
**Violation**: Functions doing too much
- `handleSelectedClick()` - Handles movement, attack, loading, unloading
- `render()` - Drawing everything in one function
- `showContextMenu()` - Building entire menu inline

**Fix**: Break into smaller functions
```javascript
// Instead of one giant handleSelectedClick:
async handleUnitMovement(from, to) { }
async handleUnitAttack(attacker, target) { }
async handleTransportLoad(unit, transport) { }
```

### 4. **Repeated Response Parsing**
**Violation**: DRY principle
**Pattern appears 10+ times**:
```javascript
// This pattern repeats:
if (result && result.success) {
    // handle success
} else {
    // handle error
}
```

**Fix**: Create utility function
```javascript
parseRpcResponse(result) {
    if (!result) return { success: false, error: 'No result' };
    if (result.error) return { success: false, error: result.error };
    return { success: true, data: result };
}
```

### 5. **Inline Styles**
**Violation**: Mixing presentation with logic
```javascript
menu.style.position = 'absolute';
menu.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
menu.style.border = '1px solid #3498db';
```

**Fix**: Use CSS classes
```javascript
menu.className = 'context-menu';
```

### 6. **No Error Boundaries**
**Violation**: Inconsistent error handling
- Some async functions have try/catch
- Others let errors propagate
- No user feedback on errors

**Fix**: Centralized error handler
```javascript
async safeRpc(method, params) {
    try {
        const result = await this.rpc(method, params);
        return this.parseRpcResponse(result);
    } catch (error) {
        this.showError(`RPC ${method} failed: ${error.message}`);
        return { success: false, error };
    }
}
```

### 7. **Mixed Responsibilities**
**Violation**: Single Responsibility Principle
- Game class handles: rendering, input, networking, UI, game logic

**Fix**: Separate concerns
```javascript
class GameRenderer { /* drawing only */ }
class InputHandler { /* input only */ }
class NetworkManager { /* RPC only */ }
class UIManager { /* UI updates only */ }
class Game { /* coordinate the above */ }
```

### 8. **Global State Access**
**Violation**: Direct DOM manipulation everywhere
```javascript
document.getElementById('unit-select');
document.getElementById('modal');
document.getElementById('context-menu');
```

**Fix**: Cache references
```javascript
constructor() {
    this.ui = {
        modal: document.getElementById('modal'),
        unitSelect: document.getElementById('unit-select'),
        contextMenu: document.getElementById('context-menu')
    };
}
```

## Priority Fixes

1. **Add DEBUG flag** - Easy win, improves performance
2. **Extract constants** - Improves maintainability
3. **Create response parser** - Reduces code by ~200 lines
4. **Split mega-functions** - Improves readability
5. **Add error handling** - Improves user experience

## Estimated Impact

- **Code reduction**: ~500 lines (25%)
- **Performance**: Faster without console.logs
- **Maintainability**: Much easier to modify
- **Reliability**: Better error handling
- **Testing**: Easier to unit test small functions
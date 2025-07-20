# Debug Files Analysis

## Categories of Debug/Test Files

### 1. Core Utilities (KEEP)
- `logger.js` - Used by render.html and modular system
- `test_helpers.js` - Used for test game creation

### 2. Debug Files in render.html (CAN REMOVE)
These are imported in render.html but appear to be pure debug utilities:
- `click-test.js`
- `test-movement.js`
- `debug-mech.js`
- `render-test.js`
- `debug-rendering.js`
- `debug-unit-0-4.js`
- `debug-tileat.js`

### 3. Standalone Debug Files (CAN REMOVE)
Not imported anywhere:
- `show-map-layout.js`

### 4. Modular System Files (KEEP FOR NOW)
Part of the modular rendering refactor:
- `modules/testing.js` - Part of modular system
- `render_modular.js` - Modular rendering implementation
- `render_final.js` - Another rendering variant

### 5. Integration Files (REVIEW NEEDED)
May be temporary or may be actively used:
- `animation-integration.js`
- `transport_integration.js` 
- `individual-sprite-handler.js`

### 6. Optimization Experiments (KEEP FOR NOW)
Currently imported by render.html:
- `optimized-sprite-renderer.js`
- `optimized-tile-renderer.js`

## Recommendation

### Safe to Remove:
1. Debug files in category 2 (click-test.js, test-movement.js, etc.)
2. show-map-layout.js

### Keep:
1. logger.js and test_helpers.js (core utilities)
2. Modular system files (active refactor)
3. Optimization files (currently in use)

### Need Further Review:
1. Integration files - check if their functionality is properly integrated elsewhere

## Next Steps
1. Remove debug files from render.html imports
2. Delete the standalone debug files
3. Test that the game still works after removal
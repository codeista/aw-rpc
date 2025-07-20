# Rendering Systems Analysis

## Current State: Multiple Overlapping Systems

### 1. Active System: `render_legacy.js`
- **Status**: CURRENTLY IN USE
- **Features**: 
  - Working terrain and unit rendering
  - Center-based coordinate system for sprite offsets
  - Handles double-height tiles (buildings, mountains)
  - Has disabled optimized tile renderer code

### 2. Disabled/Broken Systems

#### `optimized-tile-renderer.js`
- **Status**: DISABLED (corrupts terrain tiles)
- **Issue**: Palette mode conversion loses color data
- **Disabled in render_legacy.js**: `if (false && window.optimizedTileRenderer...`

#### `render.js`
- **Status**: UNKNOWN/UNUSED
- **Purpose**: Appears to be an earlier version

#### `render_modular.js`
- **Status**: HALF-IMPLEMENTED
- **Purpose**: Attempted modular rewrite

#### `render_final.js`
- **Status**: HALF-IMPLEMENTED
- **Purpose**: Another attempted rewrite

### 3. Modular System (`/modules/` directory)
- **Status**: INCOMPLETE
- **Contains**: 
  - renderEngine.js
  - gameState.js
  - movementSystem.js
  - combatSystem.js
  - etc.
- **Issue**: Not integrated, incomplete implementation

## Problems This Causes

1. **Confusion**: Hard to know which system is actually being used
2. **Maintenance**: Changes might be made to wrong files
3. **Dead Code**: Lots of unused code taking up space
4. **Conflicting Approaches**: Different coordinate systems and rendering methods

## Recommendation

### Keep:
- `render_legacy.js` - Currently working system
- `two.min.js` - Required library

### Remove or Archive:
- `optimized-tile-renderer.js` - Broken, causes corruption
- `render.js` - Old/unused
- `render_modular.js` - Incomplete
- `render_final.js` - Incomplete
- `/modules/` directory - Incomplete modular system

### Clean Up render_legacy.js:
- Remove disabled optimized renderer code
- Remove commented out code
- Document the coordinate system clearly

## Steps to Clean Up

1. **Backup everything first**
2. **Remove unused files**
3. **Clean up render_legacy.js**
4. **Add clear documentation**
5. **Test thoroughly**

This will make the codebase much clearer for sprite upscaling work and future maintenance.
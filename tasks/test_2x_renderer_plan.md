# Test 2x Renderer Plan

## Goal
Test that the new canvas-based 2x renderer properly displays units and UI elements

## Current Status
- ✅ 2x terrain sprites created and mapped
- ✅ 2x unit sprites created and mapped  
- ✅ 2x UI sprites created and mapped
- ✅ Canvas-based renderer created (replaced Two.js)
- ✅ Fixed RPC communication (uses JSON-RPC 2.0 to /api)
- ❌ Not tested with actual game

## Test Plan

### 1. Server Setup
- [ ] Ensure server is running
- [ ] Verify /api endpoint works

### 2. Create Test Scenario
- [ ] Create test game with units of different types
- [ ] Include units with different HP levels
- [ ] Include units in different states (moved, available)
- [ ] Include transports with cargo

### 3. Test Rendering
- [ ] Verify terrain renders at 32x32
- [ ] Verify units render at 32x32
- [ ] Verify HP indicators show correctly
- [ ] Verify status icons (loaded, capturing) display
- [ ] Verify movement/attack highlights work

### 4. Test Interactions
- [ ] Click to select unit
- [ ] Hover to show tile info
- [ ] Right-click context menu

### 5. Compare with Original
- [ ] Take screenshots of both renderers
- [ ] Verify feature parity

## Implementation Steps

1. Start server properly
2. Create comprehensive test game
3. Load in 2x renderer
4. Document any issues found
5. Fix issues
6. Repeat until working
# UI Mechanics Fixes Required

## Test Results Summary

### ❌ Failed Features
1. **Movement Highlights** - No yellow tiles shown when unit selected
2. **Attack Highlights** - No red tiles for attack targets
3. **Double-Click Wait** - Unit doesn't end turn on double-click
4. **ESC Key Cancel** - Doesn't clear selection
5. **B Key Transports** - Doesn't show loadable transports

### ⚠️ JavaScript Errors Found
- 13 severe errors detected
- Need to check console logs for details

## According to Documentation

### Expected Behaviors (from CONTROLS_GUIDE.md & UI_REFERENCE_GUIDE.md):

1. **Movement System**:
   - Click unit → Yellow highlights appear for valid moves
   - Click yellow tile → Unit moves
   - Visual: `rgba(255, 248, 220, 0.2)` with `#B8860B` border

2. **Attack System**:
   - Select unit → Red highlights on enemies in range
   - Click red enemy → Attack with damage preview

3. **Keyboard Controls**:
   - **B** → Show green highlights on loadable transports
   - **ESC** → Cancel current action/clear selection
   - **Space** → End turn

4. **Double-Click**:
   - On unit → Make unit wait (end its turn)
   - On capturable property → Start capture

5. **Transport System**:
   - Move onto transport → Auto-board
   - Right-click transport → Unload menu
   - Alt+Click → Show exit positions

## Implementation Status Check

Need to verify these systems exist in the code:
1. Movement highlight rendering
2. Attack highlight rendering  
3. Keyboard event handlers
4. Double-click handlers
5. Transport interaction handlers

## Next Steps

1. Check render_legacy.js for highlight functions
2. Check click-handler.js for interaction handlers
3. Check keyboard-shortcuts.js for key bindings
4. Fix each system based on documentation
5. Re-test with Selenium
# Advance Wars RPC - Issue Tracker

Last Updated: 2025-01-22

## 🔴 Critical Issues

### 1. No User-Facing Error Messages
- **File**: `game_v2_simple.js:422`
- **Impact**: Users see nothing when RPC calls fail
- **Fix Required**: Add error toast/modal system
- **Status**: Open

### 2. Database Transaction Safety
- **File**: `app.py` (multiple locations)
- **Impact**: Failed commits leave DB in bad state
- **Fix Required**: Wrap all commits in try/except with rollback
- **Status**: Open

### 3. Thread Safety for Game State
- **File**: `app.py:18`
- **Impact**: Race conditions with concurrent requests
- **Fix Required**: Add locks for global game dictionary access
- **Status**: Open

### 4. Silent Exception Handling
- **File**: `manager.py:979-980`
- **Impact**: Critical errors hidden with `except: pass`
- **Fix Required**: Add proper logging/error handling
- **Status**: Open

## 🟠 High Priority Issues

### 5. WebSocket Disconnection Not Shown
- **File**: `game_v2_simple.js:60-84`
- **Impact**: Users unaware of connection loss
- **Fix Required**: Add reconnection logic and UI indicator
- **Status**: Open

### 6. No Click Debouncing
- **File**: `game_v2_simple.js:87`
- **Impact**: Rapid clicks cause invalid states
- **Fix Required**: Add 300ms debounce on game actions
- **Status**: Open

### 7. Missing Input Validation
- **File**: Various RPC endpoints
- **Impact**: Invalid coordinates cause crashes
- **Fix Required**: Add bounds checking before array access
- **Status**: Open

### 8. Bare Except Clauses
- **File**: `manager.py:440,454,460`
- **Impact**: Catches SystemExit, KeyboardInterrupt
- **Fix Required**: Use specific exception types
- **Status**: Open

## 🟡 Medium Priority Issues

### 9. Full Board Redraws
- **File**: `game_v2_simple.js:880`
- **Impact**: Poor performance on every update
- **Fix Required**: Implement dirty rectangle system
- **Status**: Open

### 10. Event Listener Memory Leaks
- **File**: `game_v2_simple.js:1461`
- **Impact**: Minor memory leak over time
- **Fix Required**: Clean up listeners on game end
- **Status**: Open

### 11. Concurrent RPC Race Conditions
- **File**: `game_v2_simple.js:413`
- **Impact**: UI can desync from server state
- **Fix Required**: Implement request queue
- **Status**: Open

### 12. Inefficient Board Serialization
- **File**: Throughout codebase
- **Impact**: Performance degrades with large games
- **Fix Required**: Add caching/compression
- **Status**: Open

## 🟢 Low Priority Issues

### 13. Console Logs in Production
- **File**: `game_v2_simple.js` (59 instances)
- **Impact**: Minor performance impact
- **Fix Required**: Add production build process
- **Status**: Open

### 14. Browser Compatibility
- **File**: Multiple uses of `?.` operator
- **Impact**: Breaks on pre-2020 browsers
- **Fix Required**: Add Babel transpilation
- **Status**: Open

### 15. No Loading Indicators
- **File**: Throughout async operations
- **Impact**: Poor UX during operations
- **Fix Required**: Add spinner component
- **Status**: Open

### 16. Token in Global Scope
- **File**: `render_v2.html:787`
- **Impact**: Minor security concern
- **Fix Required**: Move to closure
- **Status**: Open

## 📊 Issue Summary

- **Critical**: 4 issues
- **High**: 4 issues  
- **Medium**: 4 issues
- **Low**: 4 issues
- **Total**: 16 issues

## 🎯 Recommended Fix Order

1. **Phase 1 - Stability** (Critical issues 1-4)
2. **Phase 2 - Reliability** (High issues 5-8)
3. **Phase 3 - Performance** (Medium issues 9-12)
4. **Phase 4 - Polish** (Low issues 13-16)
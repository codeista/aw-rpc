# Code Review - Potential Issues Found

## 1. Memory Leaks

### Issue: Event Listener Not Cleaned Up
**Location**: `game_v2_simple.js:1461`
```javascript
menu.removeEventListener('click', this.attackTargetClickHandler);
```
**Problem**: The `attackTargetClickHandler` is removed but only when a new attack target selection is shown. If the user cancels or navigates away, the event listener may persist.
**Risk**: Low - Minor memory leak in edge cases

### Issue: Timeout Not Always Cleared
**Location**: `game_v2_simple.js:291`
```javascript
previewTimeout = setTimeout(() => {
```
**Problem**: `previewTimeout` is set but only cleared if mouse moves again. If user navigates away or game ends, timeout may still fire.
**Risk**: Low - Timeout is short (150ms)

## 2. Race Conditions

### Issue: Concurrent RPC Calls
**Location**: `game_v2_simple.js:413`
```javascript
// Always update board after RPC call
await this.updateBoard();
```
**Problem**: Every RPC call triggers a board update. If multiple RPCs are in flight (e.g., user clicks rapidly), board state could become inconsistent.
**Risk**: Medium - Could cause UI desync

### Issue: No Debouncing on Click Events
**Location**: `game_v2_simple.js:87`
```javascript
this.canvas.addEventListener('click', async (e) => {
```
**Problem**: Rapid clicks could trigger multiple concurrent operations (moves, attacks) before the first completes.
**Risk**: Medium - Could cause invalid game states

## 3. Error Handling

### Issue: WebSocket Errors Not Handled
**Location**: `game_v2_simple.js:60-84`
```javascript
socket.on('connect_error', (error) => {
    console.error('Connection error:', error.message);
});
```
**Problem**: Connection errors are logged but UI doesn't inform user or attempt reconnection.
**Risk**: High - User won't know if connection is lost

### Issue: RPC Errors Propagated But Not Displayed
**Location**: `game_v2_simple.js:422`
```javascript
console.error('RPC error:', e);
throw e;
```
**Problem**: Errors are re-thrown but never caught at top level. User sees no error message.
**Risk**: High - Silent failures confuse users

## 4. Performance Issues

### Issue: Full Board Render on Every Update
**Location**: `game_v2_simple.js:880`
```javascript
render() {
    if (!this.board || !this.ctx) return;
```
**Problem**: Entire board is redrawn even for minor changes (e.g., hover effects).
**Risk**: Medium - Unnecessary CPU usage, potential lag on slower devices

### Issue: Console Logs in Production
**Location**: Throughout file (59 instances)
**Problem**: Extensive console logging affects performance and exposes internal state.
**Risk**: Low - Minor performance impact

## 5. UI/UX Issues

### Issue: Double-Click and Right-Click Timing Conflict
**Location**: `game_v2_simple.js:191,225`
```javascript
this.canvas.addEventListener('dblclick', async (e) => {
this.canvas.addEventListener('contextmenu', async (e) => {
```
**Problem**: Fast right-click after left-click could trigger unintended double-click capture.
**Risk**: Low - Minor UX annoyance

### Issue: No Loading Indicators
**Location**: Throughout async operations
**Problem**: No visual feedback during RPC calls. User might click multiple times thinking nothing happened.
**Risk**: Medium - Poor UX, potential for duplicate actions

## 6. Security Concerns

### Issue: Token Exposed in Global Scope
**Location**: `render_v2.html:787`
```javascript
const TOKEN = '{{token}}';
```
**Problem**: Game token is in global scope, accessible to any script or browser extension.
**Risk**: Low - Token is game-specific, not user auth

## 7. Browser Compatibility

### Issue: Optional Chaining Not Supported in Older Browsers
**Location**: Multiple instances of `?.` operator
**Problem**: Optional chaining (`?.`) not supported in browsers before 2020.
**Risk**: Low - Most users have modern browsers

## 8. Backend Issues (Python)

### Issue: Bare Except Clauses
**Location**: `manager.py:440,454,460,979`
```python
except:
    print(f"🔥 COMBAT: {attacker.type.name}...")
```
**Problem**: Bare except catches all exceptions including SystemExit and KeyboardInterrupt.
**Risk**: Medium - Could mask critical errors or prevent clean shutdown

### Issue: Exception Silently Ignored
**Location**: `manager.py:979-980`
```python
except:
    pass
```
**Problem**: Exceptions in serialization are completely ignored with no logging.
**Risk**: High - Silent data corruption possible

### Issue: No Database Transaction Rollback
**Location**: `app.py` - Multiple locations with `db.session.commit()`
**Problem**: No try/except blocks around database commits. Failed commits leave session in bad state.
**Risk**: High - Database inconsistency on errors

### Issue: Thread Safety Concerns
**Location**: `app.py:18` imports threading but no locks used
**Problem**: Global game state dictionary accessed without synchronization.
**Risk**: High - Race conditions in concurrent requests

### Issue: Inefficient Board Serialization
**Location**: Throughout codebase
**Problem**: Full board state serialized/deserialized on every request.
**Risk**: Medium - Performance degradation with large games

## 9. Data Validation Issues

### Issue: No Input Sanitization
**Location**: RPC endpoints throughout `app.py`
**Problem**: User input passed directly to game logic without validation.
**Risk**: Low - Type hints provide some protection but not enforced at runtime

### Issue: Missing Bounds Checking
**Location**: Various coordinate-based operations
**Problem**: X,Y coordinates not always validated before array access.
**Risk**: Medium - Could cause IndexError crashes

## Recommendations

1. **Critical (Fix Immediately)**:
   - Add database transaction error handling with rollbacks
   - Implement thread-safe access to shared game state
   - Replace bare except clauses with specific exception types
   - Add user-facing error messages for RPC failures

2. **High Priority**:
   - Implement WebSocket reconnection logic
   - Add loading spinners for async operations
   - Fix silent exception handling (remove `pass`)
   - Add input validation for all RPC endpoints

3. **Medium Priority**:
   - Debounce rapid clicks
   - Implement request queuing to prevent race conditions
   - Optimize rendering (dirty rectangles or layers)
   - Add database connection pooling

4. **Low Priority**:
   - Clean up event listeners on game end
   - Remove console logs for production build
   - Add Babel transpilation for older browser support
   - Implement board state caching/compression
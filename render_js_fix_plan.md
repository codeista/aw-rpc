# render.js Fix Implementation Plan

## Priority 1: Critical Production Issues (Week 1)

### 1. Replace Console Logging System
**Problem**: 121 console.log statements expose information and impact performance
**Solution**:
- Create a Logger class with configurable levels (DEBUG, INFO, WARN, ERROR)
- Replace all console.log with logger.debug() or appropriate level
- Add environment-based log level configuration
- Store logs in memory buffer for debugging

**Implementation**:
```javascript
class Logger {
    constructor(level = 'INFO') {
        this.levels = { DEBUG: 0, INFO: 1, WARN: 2, ERROR: 3 };
        this.currentLevel = this.levels[level];
        this.buffer = [];
    }
    
    log(level, ...args) {
        if (this.levels[level] >= this.currentLevel) {
            const entry = { level, timestamp: Date.now(), message: args };
            this.buffer.push(entry);
            if (window.DEBUG_MODE) console.log(`[${level}]`, ...args);
        }
    }
}
```

### 2. Add Comprehensive Error Handling
**Problem**: Many RPC calls lack proper error handling
**Solution**:
- Wrap all jsonrpc calls with try-catch
- Add .catch() to all Promise-based calls
- Create centralized error handler
- Show user-friendly error messages

**Implementation Steps**:
1. Create errorHandler utility function
2. Audit all 50+ RPC calls
3. Add error handling to each
4. Test error scenarios

### 3. Input Validation Layer
**Problem**: User inputs passed directly to RPC without validation
**Solution**:
- Create validation schemas for each RPC method
- Validate coordinates, unit types, funds
- Sanitize user inputs
- Prevent XSS and injection attacks

**Implementation**:
```javascript
const validators = {
    coordinates: (x, y) => {
        if (!Number.isInteger(x) || !Number.isInteger(y)) return false;
        if (x < 0 || y < 0 || x >= board.width || y >= board.height) return false;
        return true;
    },
    unitType: (type) => VALID_UNIT_TYPES.includes(type),
    funds: (amount) => Number.isInteger(amount) && amount >= 0
};
```

## Priority 2: Architecture & Performance (Week 2)

### 4. Modularize render.js
**Problem**: 5000+ lines in single file
**Solution**: Split into logical modules

**Module Structure**:
```
/static/js/
├── core/
│   ├── logger.js          // Logging system
│   ├── config.js          // Configuration
│   └── utils.js           // Utility functions
├── game/
│   ├── state.js           // Game state management
│   ├── board.js           // Board rendering
│   └── units.js           // Unit rendering
├── systems/
│   ├── movement.js        // Movement system
│   ├── combat.js          // Combat system
│   ├── transport.js       // Transport system
│   └── economy.js         // Economy system
├── ui/
│   ├── controls.js        // UI controls
│   ├── modals.js          // Modal dialogs
│   └── feedback.js        // User feedback
├── network/
│   ├── rpc-client.js      // RPC communication
│   └── socket.js          // Socket.io handling
└── main.js                // Entry point
```

### 5. Fix Race Conditions
**Problem**: Multiple async operations without coordination
**Solution**:
- Use async/await pattern
- Implement operation queue
- Add loading states
- Prevent double-clicks

**Implementation**:
```javascript
class OperationQueue {
    constructor() {
        this.queue = [];
        this.processing = false;
    }
    
    async add(operation) {
        this.queue.push(operation);
        if (!this.processing) {
            await this.process();
        }
    }
    
    async process() {
        this.processing = true;
        while (this.queue.length > 0) {
            const op = this.queue.shift();
            await op();
        }
        this.processing = false;
    }
}
```

## Priority 3: Feature Enhancements (Week 3)

### 6. Cargo Selection UI
**Problem**: Always unloads first unit (index 0)
**Solution**:
- Create cargo selection modal
- Show unit details for each cargo
- Allow selection of specific unit
- Add keyboard shortcuts (1, 2 for cargo selection)

**UI Design**:
```
┌─────────────────────────┐
│ Select Cargo to Unload  │
├─────────────────────────┤
│ [1] Infantry (HP: 10)   │
│ [2] Mech (HP: 8)        │
├─────────────────────────┤
│ [Cancel]    [Unload]    │
└─────────────────────────┘
```

### 7. Keyboard Shortcuts
**Problem**: Limited keyboard support
**Solution**: Add comprehensive shortcuts

**Shortcut Map**:
- `Space` - End turn
- `R` - Refresh board
- `Esc` - Cancel selection
- `1-9` - Quick unit creation
- `W/A/S/D` - Camera pan
- `+/-` - Zoom in/out
- `M` - Toggle move highlights
- `T` - Show transport info
- `?` - Show help

### 8. Animation System
**Problem**: Instant state changes without feedback
**Solution**:
- Add transition animations
- Movement path animation
- Attack animations
- Smooth highlight transitions

## Implementation Order

### Phase 1 (Immediate - Week 1):
1. **Create Logger class** (4 hours)
   - Replace all console.log statements
   - Add environment configuration

2. **Add error handling** (8 hours)
   - Create error handler utility
   - Audit and update all RPC calls
   - Add user-friendly error messages

3. **Input validation** (6 hours)
   - Create validation schemas
   - Add validation to all user inputs
   - Test edge cases

### Phase 2 (Week 2):
4. **Begin modularization** (16 hours)
   - Create module structure
   - Extract logging system
   - Extract RPC client
   - Extract game state

5. **Fix race conditions** (8 hours)
   - Implement operation queue
   - Convert to async/await
   - Add loading states

### Phase 3 (Week 3):
6. **Cargo selection UI** (8 hours)
   - Design and implement modal
   - Hook up to transport system
   - Add keyboard support

7. **Keyboard shortcuts** (4 hours)
   - Implement shortcut manager
   - Add help overlay
   - Test all shortcuts

8. **Basic animations** (8 hours)
   - Movement animations
   - Highlight transitions
   - Attack feedback

## Testing Strategy

### Unit Tests:
- Validation functions
- Logger functionality
- State management
- Error handling

### Integration Tests:
- RPC communication
- Transport operations
- Combat sequences
- Turn management

### Manual Testing:
- Error scenarios
- Race conditions
- UI responsiveness
- Cross-browser compatibility

## Rollback Plan

### Version Control:
- Create feature branches for each phase
- Tag stable versions
- Keep render_backup.js as fallback

### Progressive Enhancement:
- New features behind feature flags
- Gradual rollout
- Monitor error rates

## Success Metrics

### Performance:
- Page load time < 2s
- RPC response time < 200ms
- No console errors in production

### Code Quality:
- No global namespace pollution
- 100% error handling coverage
- Modular architecture
- < 500 lines per module

### User Experience:
- Clear error messages
- Visual feedback for all actions
- Keyboard accessibility
- Smooth animations

## Timeline

**Week 1**: Critical fixes (logging, errors, validation)
**Week 2**: Architecture (modularization, race conditions)
**Week 3**: Features (cargo UI, shortcuts, animations)
**Week 4**: Testing and polish

Total estimated time: 80-100 hours
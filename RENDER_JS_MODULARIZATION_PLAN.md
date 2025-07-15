# Render.js Modularization Implementation Plan

## Overview
Transform the monolithic 5,567-line `render.js` into 12 focused, maintainable modules averaging ~460 lines each.

## Target Architecture

### 1. Core System (3 modules)
- **core.js** (200 lines) - Constants, utilities, basic state
- **network.js** (150 lines) - JSON-RPC, Socket.io, error handling  
- **gameState.js** (300 lines) - State tracking, board management

### 2. User Interface (3 modules)
- **inputHandler.js** (400 lines) - Mouse/touch events, canvas interaction
- **renderEngine.js** (800 lines) - Two.js rendering, sprites, visuals
- **uiSystems.js** (400 lines) - Menus, notifications, modals

### 3. Game Logic (4 modules)
- **gameActions.js** (600 lines) - Unit creation, commands, validation
- **movementSystem.js** (400 lines) - Movement, pathfinding, highlighting
- **combatSystem.js** (300 lines) - Combat preview, execution, targeting
- **transportSystem.js** (350 lines) - Transport units, cargo management

### 4. Support Systems (2 modules)
- **testing.js** (350 lines) - Debug utilities, sprite testing
- **mobileSupport.js** (200 lines) - Touch events, mobile UI

## Implementation Phases

### Phase 1: Foundation (Week 1)
1. **Extract core.js** - Constants, utilities, UUID functions
2. **Extract network.js** - RPC and socket communication
3. **Extract testing.js** - All debug/development code
4. **Set up module loading** - ES6 imports or RequireJS

### Phase 2: Data Layer (Week 2)  
5. **Extract gameState.js** - State management and persistence
6. **Extract uiSystems.js** - UI components and notifications

### Phase 3: Interaction Layer (Week 3)
7. **Extract inputHandler.js** - Event processing and user input
8. **Extract gameActions.js** - Unit actions and game commands

### Phase 4: Complex Systems (Week 4)
9. **Extract renderEngine.js** - Two.js rendering system
10. **Extract movementSystem.js** - Movement logic and pathfinding
11. **Extract combatSystem.js** - Combat mechanics
12. **Extract transportSystem.js** - Transport and cargo logic

### Phase 5: Finalization (Week 5)
13. **Extract mobileSupport.js** - Touch and mobile features
14. **Integration testing** - Comprehensive testing
15. **Performance optimization** - Module loading and caching

## Module Interface Design

### Core Module API
```javascript
// core.js
export const TILESIZE = 16;
export const TRANSPORT_HIGHLIGHT_OPACITY = 0.3;
export function uuidv4() { /* ... */ }
export function isTransportUnitForRender(unit) { /* ... */ }
export const gameState = { selectedUnit: null, movementPhase: false };
```

### Network Module API
```javascript
// network.js
export function jsonrpc(method, params) { /* Returns Promise */ }
export function initializeSocket(token) { /* ... */ }
export class ErrorHandler { /* ... */ }
```

### Game State Module API
```javascript
// gameState.js
export function updateBoard(boardData) { /* ... */ }
export function preserveMovementHighlights() { /* ... */ }
export function getCurrentGameState() { /* ... */ }
```

## Dependencies Management

### Dependency Graph
```
core.js (no dependencies)
├── network.js (depends on: core)
├── gameState.js (depends on: core, network)
├── inputHandler.js (depends on: core, gameState)
├── gameActions.js (depends on: core, network, gameState)
├── renderEngine.js (depends on: core, gameState)
├── movementSystem.js (depends on: core, gameState, renderEngine)
├── combatSystem.js (depends on: core, gameActions, uiSystems)
├── transportSystem.js (depends on: core, gameActions, movementSystem)
├── uiSystems.js (depends on: core, renderEngine)
├── testing.js (depends on: core, renderEngine)
└── mobileSupport.js (depends on: core, inputHandler)
```

## Benefits

### Immediate Benefits
- **Maintainability**: 12 focused files vs 1 massive file
- **Collaboration**: Multiple developers can work simultaneously
- **Testing**: Individual modules can be unit tested
- **Debugging**: Easier to isolate issues

### Long-term Benefits
- **Performance**: Lazy loading of non-critical modules
- **Scalability**: New features as separate modules
- **Reusability**: Modules can be reused across projects
- **Code Quality**: Better separation of concerns

## Risk Mitigation

### Technical Risks
- **Global State**: Gradually convert to module-based state
- **Circular Dependencies**: Careful dependency design
- **Event System**: Implement proper inter-module communication

### Process Risks
- **Incremental Migration**: One module at a time
- **Comprehensive Testing**: Test after each module extraction
- **Rollback Plan**: Keep original render.js until migration complete

## Success Metrics
- ✅ All 12 modules under 1000 lines each
- ✅ No functionality lost during migration
- ✅ Test suite passes with 95%+ success rate
- ✅ Page load time improves or stays same
- ✅ Code maintainability score improves significantly

## Next Actions
1. **Review and approve this plan**
2. **Set up development branch** for modularization work
3. **Create module template structure**
4. **Begin Phase 1 implementation**
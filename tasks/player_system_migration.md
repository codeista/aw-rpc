# Player System Migration Plan

## Overview
Complete migration from Army enum (RED/BLUE) system to player-based system.

## Current State Analysis

### Files Using Army Enum (12 files identified)
1. **Core Systems**
   - `map_system.py` - Army enum definition, Map format uses "RED,BLUE"
   - `unit.py` - Unit.create() expects Army enum
   - `manager.py` - Heavy Army enum usage for turns
   - `gameboard.py` - turn_order, current_turn use Army

2. **V2 Systems (Hybrid)**
   - `game_factory.py` - Converts between systems
   - `game_board_v2.py` - Compatibility layer
   - `api_v2.py` - Mixed usage
   - `manager_v2.py` - Inherits from manager.py

3. **Routes/API**
   - `app.py` - Uses Army strings
   - `routes/unified_test_route.py` - Mixed player/army
   - `routes/rpc_methods.py` - Army parameters

4. **Tests**
   - Multiple test files use Army.RED/BLUE

## Migration Steps

### Phase 1: Foundation Changes
- [ ] Create new MapV2 format that uses player IDs
- [ ] Update Unit class to use player_id instead of army
- [ ] Create migration utilities for save games

### Phase 2: Core Updates  
- [ ] Update GameBoard to use player-based turns
- [ ] Modify manager.py core methods
- [ ] Update all unit creation calls

### Phase 3: API/Frontend
- [ ] Update RPC methods to use player_id
- [ ] Fix frontend sprite lookups
- [ ] Update game state responses

### Phase 4: Test System
- [ ] Fix test map definitions
- [ ] Update test unit creation
- [ ] Fix all test assertions

### Phase 5: Cleanup
- [ ] Remove Army enum usage (except sprite mapping)
- [ ] Remove compatibility layers
- [ ] Update documentation

## Implementation Order
1. Start with Unit system (smallest change)
2. Update Map system
3. Fix GameBoard 
4. Update managers
5. Fix tests to validate
6. Update API/frontend
7. Final cleanup

## Files to Update (Priority Order)

### High Priority (Core Systems)
1. `unit.py` - Add player_id field, update create()
2. `map_system.py` - New map format
3. `gameboard.py` - Player-based turns
4. `manager.py` - Core game logic

### Medium Priority (API/Routes)
5. `app.py` - API endpoints
6. `routes/unified_test_route.py` - Test creation
7. `routes/rpc_methods.py` - RPC methods

### Low Priority (Tests/Cleanup)
8. Test files - Update all tests
9. Remove compatibility code
10. Documentation updates
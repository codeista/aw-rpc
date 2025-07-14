# Redundant Code Cleanup Notes

## Completed
- ✅ Removed duplicate `/test_combat` route (was defined twice)
- ✅ Converted DEBUG print statements to app_logger in app.py
- ✅ Removed `/sprite_test` route (replaced by `/sprites` showcase)

## High Priority Tasks
1. **Move test files from root to proper location**
   - These files clutter the root directory and should be organized
   - Action: Move to `/tests/unit/` or `/tests/integration/` as appropriate

## Medium Priority Tasks
1. **Remove remaining DEBUG print statements**
   - Files with DEBUG prints: `optimized_test_map.py`, `routes/transport_rpc.py`, various test files
   - Action: Convert to proper logging or remove if not needed

2. **Clean up test file duplicates**
   - `test_simple_transport.py` duplicates `/tests/unit/test_transport_simple.py`
   - Action: Verify which version is newer/better and remove duplicate

## Low Priority Tasks
1. **Consolidate test game creation routes**
   - Current: 10 different routes for creating test games
   - Proposed: Single route like `/test?type=combat&players=3`
   - Benefits: Easier maintenance, less code duplication

2. **Unify test API endpoints**
   - Current: 7 different endpoints for running tests
   - Proposed: Single `/api/tests` endpoint with parameters
   - Benefits: Cleaner API, easier to document

3. **Remove unused resources**
   - Empty `/tests/debug/` directory
   - `sprite_test` map in map_system.py (verify if still needed)

## Detailed File Lists

### Test Files in Root Directory
These should be moved to `/tests/unit/` or `/tests/integration/`:
- `test_simple_transport.py` → Duplicate of `/tests/unit/test_transport_simple.py` (DELETE)
- `test_blackboat_movement.py` → `/tests/unit/`
- `test_game_improvements.py` → `/tests/integration/`
- `test_blackboat_repair_complete.py` → `/tests/unit/`
- `test_complete_repair_refuel.py` → `/tests/unit/`
- `test_repair_refuel_proper.py` → `/tests/unit/` (or merge with test_complete_repair_refuel.py)

### Test Game Creation Routes
All in `app.py` - consider consolidating:
1. `/test` - Basic test game (lines ~900)
2. `/test_comprehensive` - All features test (lines ~940)
3. `/test_movement` - Movement focus (lines ~950)
4. `/test_combat` - Combat scenarios (lines ~967)
5. `/test_optimized` - Quick all-features (lines ~1340)
6. `/test_transport` - Transport testing (lines ~1400)
7. `/test_capture` - Capture mechanics (lines ~1440)
8. `/test_triangle` - 3-player game (lines ~1480)
9. `/test_cross` - 4-player game (lines ~1520)
10. `/test_pentagon` - 5-player game (lines ~1560)

### Test API Endpoints
All need consolidation:
- `/api/test_create_custom_game` - Custom game creation
- `/api/test_connection` - WebSocket test
- `/api/test-status` - Test runner status
- `/api/run-tests` - Run all tests
- `/api/run-test-category/<category>` - Run specific category
- `/api/quick-test` - Quick test runner
- `/run_test` - Legacy test runner

### Files with DEBUG Prints
Need conversion to proper logging:
- `optimized_test_map.py` - 6 DEBUG prints
- `routes/transport_rpc.py` - 7 DEBUG prints
- `tests/unit/test_combat_system.py` - Multiple DEBUG sections

## Implementation Plan

### Phase 1: Quick Wins (Do First)
1. Delete `test_simple_transport.py` (it's a duplicate)
2. Remove empty `/tests/debug/` directory
3. Move remaining test files to proper directories

### Phase 2: Code Quality
1. Convert all DEBUG prints to logging
2. Review and merge similar test files
3. Add proper test documentation

### Phase 3: Architecture (Later)
1. Design unified test game creation system
2. Create single parameterized test route
3. Consolidate API endpoints
4. Create proper test harness

## Benefits of Cleanup
- Cleaner root directory
- Easier to find and run tests
- Less code duplication
- Better maintainability
- Clearer project structure
- Easier onboarding for new developers
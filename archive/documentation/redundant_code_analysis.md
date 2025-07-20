# Redundant Code Analysis Report

## Summary
I've analyzed the codebase for redundant test routes, test files, and duplicate functionality. Here's what I found:

## 1. Duplicate Test Routes in app.py

### Critical Duplication
- **`/test_combat` route appears TWICE**:
  - Line 967: `create_combat_test()` - Creates a simple combat scenario
  - Line 1400: `create_combat_focused_game()` - Creates a different combat scenario
  - This will cause routing conflicts!

### Overlapping Test Game Creation Routes
Multiple routes create similar test games:
- `/test` - Terrain-focused test game with predeployed units
- `/test_comprehensive` - Comprehensive test with all unit types
- `/test_movement` - Movement testing scenario
- `/test_combat` (x2) - Combat testing scenarios
- `/test_optimized` - Complete mechanics test
- `/test_transport` - Transport and cargo mechanics
- `/test_capture` - Property capture mechanics
- `/test_triangle`, `/test_cross`, `/test_pentagon` - Multi-player maps

## 2. Test Files Outside Tests Directory
Found 6 test files in the root directory that should be in `/tests/`:
- `test_simple_transport.py` - Duplicates `/tests/unit/test_transport_simple.py`
- `test_blackboat_movement.py`
- `test_game_improvements.py`
- `test_blackboat_repair_complete.py`
- `test_complete_repair_refuel.py`
- `test_repair_refuel_proper.py`

## 3. Debug Code Throughout Codebase

### DEBUG Print Statements Found
- **optimized_test_map.py**: Lines 222-237 (6 DEBUG prints)
- **app.py**: Lines 1347, 1351, 1356, 1526, 1564, 1602 (6 DEBUG prints)
- **routes/transport_rpc.py**: Lines 132-160 (7 DEBUG prints)
- **tests/unit/test_combat_system.py**: Multiple DEBUG prints throughout

## 4. Multiple Debug Routes
- `/debug/methods` (line 834) - Enhanced debug endpoint
- `/debug` (line 867) - Basic debug info
- `/debug_detailed/<token>` (line 1652) - Detailed game debug
- `/test_scripts/<token>` (line 1808) - Test script runner

## 5. Redundant Test API Endpoints
Multiple API endpoints for testing with overlapping functionality:
- `/api/test_create_custom_game` - Creates custom test game
- `/api/test_connection` - Basic connection test
- `/api/test-status` - Status check
- `/api/run-tests` - Main test runner
- `/api/run-test-category/<category>` - Category-specific test runner
- `/api/quick-test` - Quick test runner
- `/run_test` (line 4590) - Another test runner

## 6. Test Utility Functions
Multiple functions that create similar test games:
- `get_predeployed_test_game()`
- `get_comprehensive_test_game()`
- `get_optimized_test_game()`
- `create_quick_combat_scenario()`

## 7. Unused Resources
- `/tests/debug/` directory is empty
- `sprite_test_map.json` - May be obsolete

## Recommendations

### High Priority
1. **Remove duplicate `/test_combat` route** - This causes routing conflicts
2. **Remove or convert DEBUG print statements** to proper logging

### Medium Priority
3. **Consolidate test files** - Move root-level test files to `/tests/` directory
4. **Unify test game creation** - Create one parameterized route instead of many
5. **Consolidate test API endpoints** - One main test runner with parameters

### Low Priority
6. **Clean up debug routes** - Keep one comprehensive debug route
7. **Remove empty directories** and unused test maps

## Impact Assessment
- **Routing conflicts**: The duplicate `/test_combat` route will cause unpredictable behavior
- **Code maintainability**: Multiple similar test routes make updates difficult
- **Performance**: DEBUG prints in production code impact performance
- **Organization**: Test files scattered in root directory reduce discoverability
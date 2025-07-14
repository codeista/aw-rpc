# Redundant Code Cleanup Notes

## Completed
- ✅ Removed duplicate `/test_combat` route (was defined twice)
- ✅ Converted DEBUG print statements to app_logger in app.py
- ✅ Removed `/sprite_test` route (replaced by `/sprites` showcase)

## Pending Cleanup

### Test Files in Root (Move to /tests/)
- `test_simple_transport.py` (duplicates `/tests/unit/test_transport_simple.py`)
- `test_blackboat_movement.py`
- `test_game_improvements.py`
- `test_blackboat_repair_complete.py`
- `test_complete_repair_refuel.py`
- `test_repair_refuel_proper.py`

### Test Game Routes (Consider consolidating)
Current routes that create test games:
1. `/test` - Basic test game
2. `/test_comprehensive` - Comprehensive test
3. `/test_movement` - Movement testing
4. `/test_combat` - Combat testing
5. `/test_optimized` - Optimized for all features
6. `/test_transport` - Transport mechanics
7. `/test_capture` - Capture mechanics
8. `/test_triangle` - 3-player game
9. `/test_cross` - 4-player game
10. `/test_pentagon` - 5-player game

Consider: Single parameterized route like `/test?mode=combat&players=3`

### Test API Endpoints (Consider unifying)
- `/api/test_create_custom_game`
- `/api/test_connection`
- `/api/test-status`
- `/api/run-tests`
- `/api/run-test-category/<category>`
- `/api/quick-test`
- `/run_test`

Consider: Single endpoint with parameters

### Other Cleanup
- Empty `/tests/debug/` directory
- `sprite_test` map in map_system.py (if no longer needed)
- Remaining DEBUG prints in:
  - `optimized_test_map.py`
  - `routes/transport_rpc.py`
  - Test files

## Notes
- Many test routes have overlapping functionality
- Test files in root should follow project structure
- Debug logging should use proper logging framework
- Consider creating a single test harness with configuration options
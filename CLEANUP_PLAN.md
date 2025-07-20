# Cleanup Plan - Debug and Test Files

## Files to Keep (Essential)

### Test Infrastructure
- `run_tests.py` - Main test runner
- `run_all_tests.py` - Comprehensive test runner
- `run_regression_tests.py` - Regression test runner
- `test_click_handling.py` - Click handler tests ✅ NEW
- `test_sprite_extraction.py` - Sprite extraction tests ✅ NEW
- `test_runner.html` - Browser-based test interface

### Static JS (Essential)
- `/static/js/click-handler.js` - Centralized click handler ✅
- `/static/js/test-click-handler.js` - Click handler test suite ✅

## Files to Remove (Debug/Temporary)

### Root Directory Debug Files
- `check_test_map.py` - One-time map check
- `debug_board_structure.py` - Debug script
- `debug_two_js_offsets.py` - Debug script for coordinates
- `test_canvas_scale_fix.py` - Debug for scaling issue
- `test_canvas_setup.py` - Debug for canvas setup
- `test_day_counter_fix.py` - Fixed issue, no longer needed
- `test_end_turn_fix.py` - Fixed issue
- `test_factory_click.py` - Fixed issue
- `test_factory_debug.py` - Debug script
- `test_factory_with_offset.py` - Debug script
- `test_game_flow.py` - Debug script
- `test_movement_after_turn.py` - Debug script
- `test_movement_debug.py` - Debug script
- `test_production_fix.py` - Fixed issue
- `test_production_menu.py` - Fixed issue
- `test_proper_scaling.py` - Debug for scaling
- `test_rendering_state.py` - Debug script
- `test_sprite_fix.py` - Fixed issue
- `test_sprite_size.py` - Debug script
- `test_terrain_in_game.py` - Debug script
- `test_ui_bugs.py` - Debug script
- `test_ui_comprehensive.py` - Debug script
- `test_ui_fixes.py` - Debug script
- `test_ui_selenium.py` - Debug script
- `test_unit_movement.py` - Debug script

### Temp Directory (All can be removed)
All files in `/temp/` that start with `test_` or `debug_`:
- Various HTML test pages
- Python test scripts
- JS debug scripts
- Click test scripts

### Sprite Extraction Helpers (Can remove after upscaling)
- `upscale_sprites.py` - Keep until upscaling complete
- `extract_terrain_direct.py` - Can remove
- `create_correct_final_batch.py` - Keep until upscaling complete
- `create_optimized_tileset.py` - Can remove

## Files to Review

### Templates
- `templates/test_interface.html` - Keep (official test interface)
- `templates/tile_optimization_test.html` - Review if still needed

### Documentation to Keep
- All `.md` files documenting features and fixes
- `CLICK_HANDLER_DOCUMENTATION.md` ✅ NEW
- `TESTING.md` - Updated with new tests

## Clean Command Sequence

```bash
# 1. Remove root debug/test files
rm -f check_test_map.py debug_board_structure.py debug_two_js_offsets.py
rm -f test_canvas_*.py test_day_counter_fix.py test_end_turn_fix.py
rm -f test_factory_*.py test_game_flow.py test_movement_*.py
rm -f test_production_*.py test_proper_scaling.py test_rendering_state.py
rm -f test_sprite_fix.py test_sprite_size.py test_terrain_in_game.py
rm -f test_ui_*.py test_unit_movement.py

# 2. Clean temp directory test files
rm -f temp/test_*.py temp/test_*.html temp/test_*.js
rm -f temp/debug_*.py temp/debug_*.html temp/debug_*.js
rm -f temp/*_test.py temp/*_test.html temp/*_test.js
rm -f temp/*_debug.py temp/*_debug.html temp/*_debug.js

# 3. Remove one-time extraction scripts
rm -f extract_terrain_direct.py create_optimized_tileset.py

# 4. Clean up any .pyc files
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
```

## Testing After Cleanup

After cleanup, verify:
1. Run `python3 run_tests.py` - Should still work
2. Run `python3 test_click_handling.py` - Should pass
3. Check game still loads and clicks work
4. Check test interface at `/test_interface` still works
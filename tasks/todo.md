# Update Sprite Sheet and Clean Up Debug Files

## Plan

### Phase 1: Identify Debug Files for Removal
- [ ] List all debug/test files in static/js/ that can be removed
- [ ] Verify they are not imported/used by core files
- [ ] Group them by category (debug, test, fix, temporary)

### Phase 2: Update Sprite Rendering
- [ ] Update render_legacy.js to use the new units_sprite_sheet.png
- [ ] Replace hardcoded sprite offsets with data from units_sprite_map.json
- [ ] Update sprite size from 16x16 to 32x32 (the new sprites are 2x scale)
- [ ] Test that unit rendering still works correctly

### Phase 3: Clean Up Files
- [ ] Remove identified debug files
- [ ] Clean up any references to removed files
- [ ] Verify the game still works after cleanup

### Phase 4: Additional Cleanup
- [ ] Identify other potential cleanup opportunities
- [ ] Remove unused sprite analysis/mapping scripts
- [ ] Clean up old calibration files

## Movement System Investigation (Completed)

### Findings:
1. **Movement Highlighting** ✅ - Fully implemented
   - Located in render.js and movementSystem.js
   - Shows valid movement tiles with blue/green highlights
   
2. **Path Preview System** ❌ - Not implemented
   - No arrow sprites for path visualization
   - No hover-based path preview
   - Would need sprites, hover handlers, and path rendering
   
3. **Fog of War** ❌ - Not implemented
   - Documented in movement-fog.txt
   - Vision stats configured in config.ini
   - No actual fog rendering or vision calculation

### Next Steps for Movement Features:
- [ ] Implement path preview system with arrow sprites
- [ ] Add fog of war rendering and vision calculation
- [ ] Integrate movement ambush/trap mechanics

## UI Testing Framework (Completed)

### Created Test Suites:
1. **Movement Highlighting Tests** ✅
   - Tests movement highlight appearance/clearing
   - Validates movement range calculations
   - Tests terrain and occupation restrictions
   
2. **Unit Rendering Tests** ✅
   - Tests sprite rendering for all unit types
   - Validates availability states (idle/unavailable)
   - Tests HP display and transport rendering
   
3. **Game Interaction Tests** ✅
   - Tests selection and movement mechanics
   - Validates attack targeting
   - Tests property capture and transport loading

### Test Infrastructure:
- Created `base_test.py` with common test utilities
- Created `run_ui_component_tests.py` for easy test execution
- Documented in `UI_TESTING_GUIDE.md`

### Running Tests:
```bash
# Run all UI component tests
python tests/ui/run_ui_component_tests.py

# Run specific components
python tests/ui/run_ui_component_tests.py movement
python tests/ui/run_ui_component_tests.py rendering
python tests/ui/run_ui_component_tests.py interactions
```

## Notes
- The new sprite sheet uses 32x32 sprites (2x scale) instead of 16x16
- Sprite mapping is now in JSON format for easier maintenance
- Need to be careful not to remove core functionality files
- Movement investigation findings documented in tasks/movement_investigation.md
- UI tests require server running on localhost:5000
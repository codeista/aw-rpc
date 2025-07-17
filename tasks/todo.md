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

## Notes
- The new sprite sheet uses 32x32 sprites (2x scale) instead of 16x16
- Sprite mapping is now in JSON format for easier maintenance
- Need to be careful not to remove core functionality files
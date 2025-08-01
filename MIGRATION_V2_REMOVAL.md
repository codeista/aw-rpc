# V2 Naming Removal Migration Guide

## Date: 2025-08-01

This document describes the migration from V2-named files and classes to clean naming conventions.

## Summary of Changes

### 1. Backend File Renames
- `game_board_v2.py` → `gameboard.py`
- `manager_v2.py` → `manager.py`

### 2. Class Renames
- `GameBoardV2` → `GameBoard`
- All references updated throughout codebase

### 3. Frontend File Renames
- `static/js/game_v2_simple.js` → `static/js/game.js`
- `templates/render_v2.html` → `templates/render.html`

### 4. Archived Legacy Files
Moved to `archive/legacy/`:
- `gameboard.py` → `archive/legacy/gameboard_army_based.py` (old army-based board)
- `templates/render.html` → `archive/legacy/render_minimal.html` (old minimal renderer)
- `static/js/game_v2.js` → `archive/legacy/game_v2_prototype.js` (prototype with non-existent APIs)
- `templates/game_v2.html` → `archive/legacy/game_v2_prototype.html`

### 5. Import Updates
All Python files updated to use new imports:
```python
# Old imports
from manager_v2 import GameManager
from game_board_v2 import GameBoardV2
from gameboard import GameBoard, GameTile  # Old army-based

# New imports
from manager import GameManager
from gameboard import GameBoard, GameTile  # Now player-based
```

### 6. RPC Method Fixes
Fixed misnamed RPC methods in frontend:
- `unit_attack_enhanced` → `combat_attack`
- `unit_attack` → `combat_attack`
- `get_attack_targets` → `combat_targets`
- `get_movement_highlights` → `movement_range`
- `get_unit_valid_moves` → `movement_range`
- `capture_tile` → `unit_capture`
- Implemented missing `end_game` RPC method

## Why This Migration?

1. **Cleaner Codebase**: Removed confusing V2 suffixes
2. **Single Implementation**: The player-based system (formerly V2) is now the main implementation
3. **Better Maintainability**: No more confusion about which version to use
4. **Consistency**: All naming follows standard conventions

## Breaking Changes

If you have external code that imports these modules, update your imports:
- Change `from manager_v2 import` to `from manager import`
- Change `from game_board_v2 import` to `from gameboard import`
- Change `GameBoardV2` to `GameBoard` in type annotations

## Testing

After migration:
1. Run all unit tests: `python3 run_regression_tests.py`
2. Test game creation and gameplay
3. Verify all RPC endpoints work
4. Check that player slot system functions correctly

## Notes

- The old army-based GameBoard is archived but available if needed
- The player-based system (formerly V2) supports flexible player configurations
- All games now use the slot-based map system where players are identified by index (0, 1, 2...)
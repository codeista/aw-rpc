# Codebase Cleanup Plan

## Current Issues

### 1. V2 Naming Confusion
- Files with `_v2` suffix that should be primary:
  - `manager_v2.py` → `manager.py` (after backing up old one)
  - `game_board_v2.py` → `game_board_extended.py` (or merge with gameboard.py)
  - `models_v2.py` → `player_models.py`
  - `map_parser_v2.py` → `map_parser_extended.py`
  - `api_v2.py` → Can be removed if unused

### 2. Deprecated RPC Methods (42 total!)
- Movement: `unit_move`, `unit_move_enhanced`, `unit_valid_moves`, `movement_info`
- Combat: `unit_attack`, `unit_attack_enhanced`, `damage_estimate`, `get_damage_preview`
- Transport: `unit_load`, `unit_unload`
- And many more...

### 3. Duplicate Functionality
- Two manager classes (GameManager in manager.py and manager_v2.py)
- Multiple movement validation systems
- Duplicate transport handling
- Two board classes (GameBoard and GameBoardV2)

### 4. Legacy Code
- Old manager.py with 3000+ lines
- Duplicate transport systems
- Old combat calculation methods

## Cleanup Steps

### Phase 1: Analyze Dependencies
1. Check which files import the v2 modules
2. Determine which RPC methods are actually used
3. Map out the dependency tree

### Phase 2: Rename Core Files
1. Backup old manager.py → manager_legacy.py
2. Rename manager_v2.py → manager.py
3. Update all imports
4. Rename other v2 files appropriately

### Phase 3: Remove Deprecated Methods
1. Mark deprecated methods with proper deprecation warnings
2. Update any code still using them
3. Remove after verification

### Phase 4: Consolidate Functionality
1. Merge GameBoard and GameBoardV2
2. Consolidate transport systems
3. Unify combat calculations

### Phase 5: Clean Documentation
1. Update all references to v2
2. Remove mentions of deprecated methods
3. Update API documentation

## Benefits
- Clearer codebase structure
- No confusion about which files to use
- Reduced code duplication
- Easier maintenance
- Better performance (less code to load)

## Risk Mitigation
- Create backups before major changes
- Test after each phase
- Keep legacy code available for reference
- Document all changes
# Changelog

## [2025-07-31] - Movement Highlights & Game Persistence Fixes

### Fixed
- **Movement highlights disappearing** - Fixed multiple issues causing highlights to vanish:
  - Socket updates now preserve highlight states when receiving board updates
  - `updateBoard()` method saves and restores highlights when fetching fresh data
  - RPC calls only update board for state-changing methods, not queries
  - Removed unnecessary board updates after query methods like `movement_range`
  
- **Game resetting on page refresh** - Fixed database persistence issues:
  - Identified all 4021 games in database were legacy format
  - Created cleanup script to remove legacy games
  - Fixed SQLAlchemy instantiation error in `game_save()` function
  - Games now properly persist in v2 format
  
- **Combat test game creation** - Fixed test game setup:
  - Fixed GameFactory API usage in optimized_test_map.py
  - Corrected parameter order in unit_create calls
  - Added unit movement flag reset for test scenarios
  - Combat test games now create properly with moveable units

### Added
- `cleanup_legacy_games.py` - Script to remove legacy format games from database

### Changed
- Movement highlights opacity set to 40% for better visibility
- Removed debug console.log statements from production code

## [2025-07-30] - V2 Player System Migration & Performance

### Added
- Performance documentation (PERFORMANCE.md) with benchmark results
- Backward compatibility methods for legacy tests:
  - `unit_load()` method in manager_v2.py
  - `unit_wait()` method in manager_v2.py

### Changed
- Migrated fully to player-based game system (v2)
- Updated all tests to use GameFactory.create_game_with_players()
- Moved old files to archive/ directory structure:
  - archive/temp_debug/ - Debug scripts and test files
  - archive/old_code/ - Deprecated code and backups
  - archive/documentation/ - Old planning documents

### Fixed
- Fixed GameManager initialization requiring player_manager parameter
- Fixed unit type enum names throughout codebase:
  - ROCKETS → ROCKET
  - MISSILES → MISSILE
  - ANTI_AIR → ANTIAIR
  - BATTLE_COPTER → BCOPTER
  - TRANSPORT_COPTER → TCOPTER
  - BLACK_BOAT → BLACKBOAT
- Fixed fuel consumption tracking (fuel_required now properly set)
- Fixed direct units can now attack after movement
- Fixed indirect units cannot counter-attack (includes BATTLESHIP, CARRIER, PIPERUNNER)
- Fixed UI test failures (canvas ID and window object references)
- Added attack validations:
  - Friendly fire prevention
  - Range validation
  - Target type validation

### Performance
- Game Creation: 12.31ms average (100% success)
- Combat Preview: 3.17ms average (100% success)
- Board Retrieval: 15.71ms average (100% success)
- All operations under 50ms (fast category)

### Testing
- All 57 regression tests passing (100% success rate)
- Fixed test coordinates to stay within 12x10 board bounds

### Removed
- Removed manager.py (replaced by manager_v2.py)

## [2025-07-27] - UI Improvements & API Consolidation

### Added
- COM_TOWER damage bonus system (+10% per tower, max +40%)
- Unavailable unit sprite display for units with no actions
- Context menu auto-close after wait action

### Changed
- API Consolidation - Reduced 58 methods to 23 core methods:
  - Transport API: 20→5 methods
  - Combat API: 7→4 methods
  - Movement API: 8→4 methods

### Fixed
- Fixed can_capture flag (only infantry/mech can capture)
- Fixed battleship attempting to capture properties

## [2025-07-24] - Sprite System Overhaul

### Added
- Combined sprite sheets in sprites_2x/combined/
- 199 terrain sprites with proper spacing
- 250 unit sprites from all categories
- Placeholder UI sprites

### Fixed
- HQ sprites renamed from HQ_VARIANT_X to BASE_TOWER_X
- Road sprite mappings (ROAD_T_N → NESRoad, etc.)
- MISSILE_SILO_EMPTY → EMPTY_SILO naming

## [2025-07-20] - UI/UX & Rendering Fixes

### Fixed
- Mouse hover jumping (null reference errors)
- Circular JSON error with board object
- JavaScript syntax errors (window.window. → window.)
- Corrupted optimized tile renderer
- Wrong default tileset (reverted to AWDS)
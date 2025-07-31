# Current State Analysis

## What Actually Exists

### Core Files
- `manager_v2.py` - This IS the main manager (no old manager.py exists)
- `game_board_v2.py` - Extended game board
- `models_v2.py` - Player-based models
- `map_parser_v2.py` - Extended map parser
- `api_v2.py` - Appears to be unused

### The Confusion
- Everything has "v2" in the name but there's no "v1" anymore
- RPC method `game_create_v2` is the primary creation method
- Comments say "DEPRECATED: use v2" but v2 IS the current version
- Legacy methods redirect to v2 methods

## What Should Be Done

### 1. Simple Renaming (Low Risk)
- Keep the files as-is but update documentation
- Remove "v2" from user-facing elements:
  - `game_create_v2` → `game_create` (keep v2 as alias)
  - Update UI/frontend references
  - Update documentation

### 2. File Renaming (Medium Risk)
- `manager_v2.py` → `game_manager.py`
- `game_board_v2.py` → `game_board_extended.py`
- `models_v2.py` → `player_models.py`
- `map_parser_v2.py` → `map_parser_extended.py`
- Update all imports

### 3. Remove Deprecated Methods
- 20 deprecated RPC methods that just redirect
- These add confusion and bloat

## Current Dependencies
- 30+ files import from manager_v2
- GameFactory uses manager_v2 and game_board_v2
- All new code uses the v2 system

## Recommendation
Start with #1 (update user-facing elements) and #3 (remove deprecated methods) as these are low risk. File renaming can wait for a larger refactor.
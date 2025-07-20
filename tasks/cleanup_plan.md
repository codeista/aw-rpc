# Documentation and File Cleanup Plan

## Current State
- 132 Python scripts in temp/
- Multiple overlapping documentation files about sprites/tiles
- Outdated test scripts and experiments
- Conflicting information across different docs

## Files to Keep (Essential)

### Core Documentation
- `CLAUDE.md` - Main project instructions
- `SPRITE_SHEET_CONFUSION.md` - Critical info on which sprite sheets to use
- `README.md` - Project overview
- `GAME_MECHANICS.md` - Game rules

### Latest Sprite/Tile Knowledge
- `temp/TILESET_EXTRACTION_KNOWLEDGE.md` - Current coordinate system
- `temp/SPRITE_UPSCALING_FINDINGS.md` - Latest upscaling learnings
- `temp/extract_terrain_by_sections.py` - Working extraction script

### Essential Scripts
- Working test scripts in `tests/`
- Core game files (manager.py, app.py, etc.)
- Frontend files in `static/`

## Files to Remove/Archive

### Outdated Documentation
- Old sprite plans that have been superseded
- Test result files from debugging
- Temporary analysis files

### Redundant Scripts in temp/
- Multiple versions of extraction scripts (keep only the working one)
- One-off test scripts
- Debug/analysis scripts that served their purpose

### Old Upscaling Attempts
- Waifu2x processed files (since we're switching to Scale2x)
- Test batches that didn't work

## Consolidation Plan

### 1. Sprite/Tile Documentation
Consolidate into one clear document:
- `SPRITE_AND_TILE_GUIDE.md` containing:
  - Which files to use (from SPRITE_SHEET_CONFUSION.md)
  - Extraction coordinates (from TILESET_EXTRACTION_KNOWLEDGE.md)
  - Upscaling approach (from SPRITE_UPSCALING_FINDINGS.md)

### 2. Archive Old Work
Create `archive/old_sprite_work/`:
- Move superseded scripts
- Move old documentation
- Keep for reference but out of main flow

### 3. Clean temp/ folder
Keep only:
- Current working scripts
- Extracted sprites pending processing
- Active upscaling work

## Questions Before Proceeding
1. Should we archive or completely delete old work?
2. Any specific files you want to keep?
3. OK to consolidate the sprite docs into one file?
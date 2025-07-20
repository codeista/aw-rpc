# Terrain Upscaling Fix Plan

## Current Situation
- Upscaled terrain tiles using waifu2x (anime-style upscaler)
- Hard threshold applied removing all semi-transparent pixels
- Result: Lost detail, harsh edges, poor quality for pixel art

## Issues Found (from analysis)
1. **All 18 tested tiles have "hard_threshold" issue**
   - Plains, woods, mountains lost texture
   - Water/shore tiles have harsh edges
   - Roads/pipes lost smooth connections
   - Fog buildings too dark

2. **Waifu2x not suitable for pixel art**
   - Designed for anime/photos, not pixel art
   - Blurs pixel boundaries
   - Creates artifacts on low-res sprites

## Proposed Solution

### Phase 1: Assess Current State
- [ ] Locate original 16x16 terrain tiles (source files)
- [ ] Identify which tiles are most critical to fix
- [ ] Determine if we need to re-extract from tileset

### Phase 2: Choose Better Upscaling Method
- [ ] Test Scale2x algorithm (pixel art specific)
- [ ] Test HQ2x or xBRZ as alternatives
- [ ] Compare nearest-neighbor + manual touch-up
- [ ] Pick best method for each tile type

### Phase 3: Implement Tile-Specific Processing
- [ ] **Terrain tiles** (plains, woods, mountains)
  - Use Scale2x to preserve pixel structure
  - Keep crisp edges and texture detail
  
- [ ] **Water tiles**
  - Scale2x + slight edge smoothing
  - Preserve animation frame consistency
  
- [ ] **Roads/Pipes**
  - Scale2x with no smoothing
  - Manual cleanup of connection points
  
- [ ] **Buildings**
  - Most are already good
  - Minor touch-ups only
  
- [ ] **Fog buildings**
  - Brightness correction (+20%)
  - Enhance contrast

### Phase 4: Quality Control
- [ ] Create comparison sheet (original vs old upscale vs new upscale)
- [ ] Test in-game rendering
- [ ] Get feedback before full processing

### Phase 5: Full Processing
- [ ] Process all terrain tiles with approved method
- [ ] Create new showcase image
- [ ] Update game to use new tiles

## Questions for User
1. Do we have the original 16x16 tiles extracted somewhere?
2. Should we prioritize certain tiles first (e.g., most common terrain)?
3. Is Scale2x acceptable or do you prefer another algorithm?
4. Should we keep any of the current upscaled tiles that look good?

## Next Steps
- Wait for user approval on this plan
- Locate source files
- Begin with test batch of priority tiles
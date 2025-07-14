# Update GAME_FLOW_AND_INTERACTIONS.md Documentation

## TODO List

- [ ] Add Auto-Wait Feature documentation
  - Document automatic unit wait behavior when no actions available after moving
  - Add to "User Interactions by Type" section

- [ ] Update Client-Side Flag Updates section
  - Document can_move, can_attack, can_capture flag updates after actions
  - Add to "Unit States" visual states section

- [ ] Document clearAllHighlights Function
  - Add comprehensive highlight clearing behavior
  - Update "Visual Effects and Highlights" section

- [ ] Update Sprite States Logic
  - Document that sprite states only check can_move || can_attack (not can_capture)
  - Update "Unit States" in special visual states

- [ ] Add Debug Functions Documentation
  - Document simulateGameFlow and testSpriteStates functions
  - Create new "Debug Tools" section

- [ ] Document Async Handling Updates
  - Update showPostMoveActionMenu async behavior
  - Add to "Interaction Flow Examples" section

- [ ] Add Sprite Showcase Route
  - Document /sprites route for sprite showcase page
  - Add to "Game Start" or create new "Development Tools" section

- [ ] Update Unit Selection Priority
  - Document fixed unit selection priority on production buildings
  - Add to "Mouse Controls" left click behavior

- [ ] Document BLUE Unit Sprite Fix
  - Document fix for BLUE unit black sprite timing issue
  - Add to "Special Visual States" section

- [ ] Update Zoom Controls Documentation
  - Document localStorage persistence for zoom
  - Update existing "Zoom" keyboard controls section

## Review Summary
- The GAME_FLOW_AND_INTERACTIONS.md file needs updates in multiple sections
- Most changes are enhancements to existing features
- Need to add new sections for debug tools and development routes
# TODO - Advance Wars RPC

## ✅ Completed
- [x] Fix production bug after latest changes
- [x] Fix unit_create_rpc to return proper error messages
- [x] Fix production options to work with occupied facilities
- [x] Fix test result display logic
- [x] Fix turn management in production tests
- [x] Debug why newly created units can't move
- [x] Fix unit movement collisions in tests
- [x] All production tests passing (6/6)

## 🔄 In Progress

## 📋 TODO - Testing & Verification
1. [ ] Run full regression test suite to ensure no other systems broken
2. [ ] Run combat system tests
3. [ ] Run transport system tests
4. [ ] Run movement system tests
5. [ ] Run victory condition tests
6. [ ] Run economic system tests
7. [ ] Test the actual game UI to verify production works correctly

## 🚀 TODO - Features & Improvements
1. [ ] Add CO (Commanding Officer) system
   - [ ] CO abilities and powers
   - [ ] CO-specific unit bonuses
   - [ ] CO power meters
2. [ ] Implement Fog of War
   - [ ] Vision mechanics
   - [ ] Unit hiding
   - [ ] Recon units revealing tiles
3. [ ] Add weather effects
   - [ ] Rain (reduced movement)
   - [ ] Snow (increased fuel consumption)
   - [ ] Clear weather
4. [ ] Implement proper save/load system
5. [ ] Add replay system
6. [ ] Implement ranked/competitive modes

## 🐛 TODO - Known Issues
1. [ ] SUB cost mismatch (showing 24000 instead of 20000)
2. [ ] Some sprites may need position adjustments
3. [ ] UI sprites are placeholders (need proper HP number graphics)
4. [ ] Beach/water tile mappings still use numbered format

## 🧹 TODO - Code Quality
1. [ ] Clean up temporary debug files
2. [ ] Remove redundant API methods (already reduced from 58 to 23)
3. [ ] Add comprehensive API documentation
4. [ ] Add unit tests for new modifier system
5. [ ] Refactor movement validation to be more efficient

## 📊 TODO - Performance
1. [ ] Optimize sprite rendering for large maps
2. [ ] Implement sprite caching
3. [ ] Optimize pathfinding algorithms
4. [ ] Add performance monitoring

## Review Section
### Changes Made
- Fixed production system error handling
- Fixed test coordinate mismatches  
- Fixed unit movement collision handling
- Improved API error responses
- All production tests now passing

### Notes
- Production system working correctly with proper facility blocking
- COM_TOWER damage bonus system implemented
- Unit availability display fixed
- Test suite significantly improved
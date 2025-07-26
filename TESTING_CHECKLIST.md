# Testing Checklist for AW-RPC

## Pre-Commit Testing Requirements
**NEVER commit code without completing this checklist!**

### 🔴 MANDATORY Before Every Commit

- [ ] Server is running without errors
- [ ] No JavaScript console errors (check F12 in browser)
- [ ] Feature being changed works as expected
- [ ] Regression tests pass: `python3 run_regression_tests.py`
- [ ] Visual inspection shows no UI glitches

### 🎮 Feature-Specific Testing

#### Combat System Changes
1. **Create Combat Test Game**
   - Open http://localhost:5000/test_interface
   - Select "Combat Test" from dropdown
   - Click "🚀 Launch Test Game"

2. **Test Combat Flow**
   - [ ] Select a tank unit
   - [ ] Action prompt shows "Select destination or action"
   - [ ] Move tank next to enemy
   - [ ] Action prompt updates to "Select target to attack"
   - [ ] Attack range highlights appear (red tiles)
   - [ ] Hover over enemy - combat preview shows
   - [ ] Right-click moved unit - "Attack" appears in menu
   - [ ] Click Attack - executes properly
   - [ ] Unit becomes "done" after attack

3. **Test Edge Cases**
   - [ ] Indirect units cannot attack after moving
   - [ ] Direct units CAN attack after moving
   - [ ] Combat preview shows for all enemies when hovering
   - [ ] Out-of-range enemies show "Out of range" in preview

#### Movement System Changes
1. **Create Movement Test Game**
   - Use test interface with "Movement Test"

2. **Test Movement**
   - [ ] Movement range highlights correctly
   - [ ] Can move to highlighted tiles
   - [ ] Cannot move to unhighlighted tiles
   - [ ] Terrain affects movement cost properly
   - [ ] Cannot move through enemy units
   - [ ] Can move through (not stop on) friendly units

#### UI/UX Changes
1. **Test Visual Elements**
   - [ ] All panels display correctly
   - [ ] Sprites render without corruption
   - [ ] Highlights show correct colors
   - [ ] Text is readable and aligned
   - [ ] Responsive design works

2. **Test Interactions**
   - [ ] Click handling works correctly
   - [ ] Right-click context menu appears
   - [ ] Hover effects work smoothly
   - [ ] No flickering or jumping

### 📊 Performance Testing
- [ ] Game runs smoothly (no lag)
- [ ] Memory usage is reasonable
- [ ] No performance degradation over time

### 🔄 Integration Testing
1. **Full Game Flow**
   - [ ] Can create game
   - [ ] Can create units
   - [ ] Can move and attack
   - [ ] Turn switching works
   - [ ] Victory conditions trigger
   - [ ] No data corruption

### 🐛 Bug Prevention
1. **Common Issues to Check**
   - [ ] No null reference errors
   - [ ] API calls handle errors gracefully
   - [ ] Edge cases don't crash game
   - [ ] State updates correctly

### 📝 Testing Documentation
After testing, document:
1. What was tested
2. Any issues found
3. How issues were resolved
4. Confirmation that retesting passed

## Quick Test Commands

```bash
# Run regression tests
python3 run_regression_tests.py

# Run unit tests
python3 -m pytest tests/unit/

# Check server logs
tail -f server.log

# Run specific test file
python3 tests/unit/test_combat_system.py
```

## Test Game URLs
- Test Interface: http://localhost:5000/test_interface
- API Browser: http://localhost:5000/api/browse
- Sprite Test: http://localhost:5000/sprite_test

## When to Test What

| Change Type | Required Tests |
|------------|----------------|
| Combat Logic | Combat flow, regression tests |
| Movement | Movement test, pathfinding |
| UI Changes | Visual inspection, interaction tests |
| API Changes | API tests, integration tests |
| Sprites | Sprite test page, visual check |

## Golden Rule
**If you're not sure if something needs testing - TEST IT!**
Better to spend 5 minutes testing than to break the game.
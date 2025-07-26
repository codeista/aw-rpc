# UI Interaction Review - Advance Wars RPC

## Current Implementation Status

### 1. Click Actions

#### Left Click (Primary Action)
```javascript
this.canvas.addEventListener('click', async (e) => {
```

**Current Flow:**
1. **No selection** → Select unit at clicked position
2. **Unit selected** → 
   - Click same tile → Deselect
   - Click movement tile → Move unit
   - Click elsewhere → Try to select new unit

**Issues Identified:**
- No clear feedback when clicking invalid tiles
- Attack flow requires right-click menu (not intuitive)
- Movement validation happens server-side only

#### Right Click (Context Menu)
```javascript
this.canvas.addEventListener('contextmenu', async (e) => {
```

**Current Implementation:**
- Shows context menu with actions: Wait, Capture, Attack, Load, Unload, Repair, Cancel
- Dynamically enables/disables options based on unit state
- Attack option leads to target selection for multiple targets

**Issues:**
- Attack option visibility is inconsistent
- Menu positioning can go off-screen
- No keyboard navigation support

#### Double Click
```javascript
this.canvas.addEventListener('dblclick', async (e) => {
```
- Used for quick capture action
- Limited use case

### 2. Mouse Hover Effects

#### Combat Preview
- Shows damage preview when hovering over enemy units
- 150ms delay before showing
- Only works with selected unit

**Issues:**
- Sometimes doesn't appear
- Timeout clearing was problematic (fixed)

#### Tile Information
- Shows coordinates and terrain type
- Shows unit info including HP, fuel, ammo
- Updates in real-time

### 3. Context Menu System

#### Dynamic Menu Items
- **Wait**: Always available for units that haven't acted
- **Capture**: Only on capturable properties
- **Attack**: Checks for adjacent enemies (direct) or any enemies (indirect)
- **Load**: Checks for adjacent transports
- **Unload**: For transports with cargo
- **Repair**: For APCs/Black Boats

#### Attack Flow
1. Click Attack in context menu
2. If one target → Attack immediately
3. If multiple targets → Show target selection submenu
4. Click target → Execute attack

**Current Issues:**
- Attack targets were being cleared by board updates (fixed by fetching from server)
- Complex state management for menu transitions

### 4. UI Panels

#### Unit Info Panel
- Shows selected unit details
- Updates on selection

#### Movement Info Panel  
- Shows movement costs and restrictions
- Only visible during movement

#### Combat Preview Panel
- Shows attack/counter damage predictions
- Appears on hover with delay

#### Action Prompt
- Shows contextual hints ("Select destination", "Select target", etc.)
- Updates based on game state

### 5. Keyboard Shortcuts
- **Space**: End turn
- **Escape**: Cancel/Deselect
- **Tab**: Cycle through units
- **H**: Toggle help panel

## Test Coverage Analysis

### What We Have Tests For:
1. **Regression Tests** (run_regression_tests.py)
   - Game creation and management
   - Unit movement validation
   - Combat calculations
   - Transport operations
   - Economic system
   - Special actions

2. **Unit Tests**
   - Attack/defense ranges
   - Combat damage calculations
   - Movement validation

### What We DON'T Have Tests For:
1. **UI Click Interactions**
   - Click-to-select behavior
   - Click-to-move validation
   - Context menu appearance/options
   - Attack target selection flow

2. **Mouse Events**
   - Hover preview timing
   - Combat preview accuracy
   - Tooltip information

3. **UI State Management**
   - Panel visibility
   - Menu transitions
   - Action prompt updates

4. **Edge Cases**
   - Clicking off-board
   - Rapid clicking
   - Menu positioning at screen edges
   - Concurrent actions

## Known Issues

### Critical:
1. **Attack Flow Confusion** - Users don't know they need to right-click for attack
2. **Inconsistent Attack Option** - Sometimes doesn't appear in context menu
3. **No Visual Attack Range** - Can't see who you can attack before clicking

### Medium:
1. **Movement Preview** - No preview of where unit can move before committing
2. **Action Feedback** - Limited feedback for invalid actions
3. **Menu Navigation** - No keyboard support for context menu

### Minor:
1. **Double-click Capture** - Not discoverable
2. **Help Panel** - Could be more prominent
3. **Turn Indicator** - Could be clearer whose turn it is

## Recommendations

### Immediate Fixes Needed:
1. **Add attack range highlighting** when unit is selected
2. **Show movement range** before moving
3. **Add visual feedback** for invalid clicks
4. **Improve action prompts** to guide users

### UI Flow Improvements:
1. **Single-click attack** - Click enemy to attack (skip menu if only option)
2. **Drag-to-move** - Drag unit to destination
3. **Preview on hover** - Show what will happen before clicking
4. **Better tutorials** - In-game hints for new players

### Testing Improvements:
1. **Selenium tests** for click interactions
2. **Jest tests** for UI state management  
3. **Manual test checklist** for UI flows
4. **User testing sessions** to identify pain points

## Test Scenarios Needed

### Click Action Tests:
```
1. Select unit → Click empty space → Unit deselected
2. Select unit → Click enemy → Attack menu/preview shown
3. Select unit → Click valid move → Unit moves
4. Select unit → Click invalid move → Error feedback
5. Right-click unit → Context menu appears with correct options
6. Click Attack → One target → Immediate attack
7. Click Attack → Multiple targets → Target selection shown
8. Click outside menu → Menu closes
```

### State Management Tests:
```
1. Select unit → Move → Can still attack
2. Select unit → Attack → Cannot move/attack again  
3. End turn → All units reset
4. Load game → UI state restored correctly
```

### Edge Case Tests:
```
1. Spam click during animation
2. Click while RPC in progress
3. Right-click at screen edge
4. Switch tabs during action
```
# Advance Wars RPC - Controls Guide

## Mouse Controls

### Left Click
- **Click on unit**: Select the unit (shows movement and attack range)
- **Click on highlighted tile**: Move selected unit to that tile
- **Click on enemy in red highlight**: Attack that enemy
- **Click on empty tile**: Deselect current unit

### Double Click
- **On your unit**: Make the unit wait (ends its turn)
- **On Infantry/Mech on capturable property**: Capture the property
- **On factory/airport/port**: Open production menu (if implemented)

### Right Click
- **On Black Boat/APC**: Opens context menu for repair/resupply
- **On loaded transport**: Shows unload options

### Special Click Combinations
- **Ctrl + Click**: Load unit into transport (if adjacent)
- **Alt + Click**: Unload unit from transport

## Action Menu

After moving a unit, an action menu will appear with these options:
- **⚔️ Attack**: Select an enemy to attack (if any in range)
- **🏴 Capture**: Capture the property (Infantry/Mech only on cities/bases)
- **⏸️ Wait**: End the unit's turn without doing anything else
- **❌ Cancel**: Cancel the move (if supported)

## Keyboard Controls

### Navigation
- **Arrow Keys**: Pan the map (if implemented)
- **WASD**: Alternative pan controls

### Zoom
- **+/=**: Zoom in
- **-**: Zoom out
- **0**: Reset zoom to 100%

### Actions
- **Space**: End turn
- **Escape**: Cancel current action
- **Enter**: Confirm action

## Mobile/Touch Controls

### Touch Gestures
- **Tap**: Same as left click (select, move, attack)
- **Long Press**: Same as right click (context menus)
- **Drag**: Pan the map
- **Pinch**: Zoom in/out

## Tips for Infantry/Mech Units

1. **To Capture**: 
   - Move Infantry/Mech onto a capturable property (city, factory, etc.)
   - Either:
     - Double-click the unit, OR
     - Wait for action menu and select "🏴 Capture"
   - Capturing takes multiple turns (reduces property HP by 10 each turn)

2. **To Wait**:
   - After moving or if you don't want to move:
     - Double-click the unit, OR
     - Select "⏸️ Wait" from action menu
   - This ends the unit's turn

3. **Visual Indicators**:
   - Available units: Full color
   - Units that have acted: Grayed out
   - Can still move/act: Check if unit has color

## Console Commands (for debugging)

Open browser console (F12) and run:
- `testSpriteStates()` - Check which units can still act
- `simulateGameFlow()` - Simulate a move/attack sequence
- `clearAllHighlights()` - Clear all highlights if stuck

## Common Issues

1. **Unit won't capture**: Make sure it's Infantry or Mech and on a capturable property
2. **No action menu**: The menu appears after moving, not when first selecting
3. **Unit still shows available after acting**: This is a known server bug - the client-side fix should gray them out
4. **Double-click not working**: Make sure to double-click quickly on the unit itself
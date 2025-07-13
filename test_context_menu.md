# Context Menu Test Instructions

## Testing the Black Boat Repair Context Menu

1. **Create a test game** with Black Boat and damaged units:
   - Go to http://localhost:5000/test
   - Create units using the game interface

2. **Set up test scenario**:
   - Create a BLACKBOAT on a port tile
   - Create an INFANTRY unit adjacent to the Black Boat
   - Create an enemy unit to damage the infantry
   - Attack the infantry to reduce its HP

3. **Test the context menu**:
   - Select the Black Boat (left-click)
   - Right-click on the damaged infantry
   - A context menu should appear with "🔧 Repair Unit (2 HP)"
   - Click the repair option
   - You should see a notification with the repair result

## Expected Behavior

- Context menu only appears when:
  - A Black Boat is selected
  - Right-clicking on an adjacent friendly unit
  - The target unit has less than 100 HP
  
- Repair action will:
  - Repair up to 2 HP
  - Cost 10% of unit cost per HP
  - Show success/error notification
  - Update the game board

## Implementation Details

### Frontend (render.html)
- Added context menu HTML div
- Added showUnitContextMenu function
- Added contextMenuAction function
- Added notification system

### Frontend (render.js)
- Added handleUnitRightClick function
- Updated unitSelect to track selected unit
- Right-click event handler calls handleUnitRightClick

### Backend (app.py)
- repair_unit RPC endpoint already implemented
- Handles validation and fund deduction

## Troubleshooting

If the context menu doesn't appear:
1. Check browser console for errors
2. Ensure Black Boat is properly selected first
3. Verify target unit is adjacent and damaged
4. Check that both units are on the same team
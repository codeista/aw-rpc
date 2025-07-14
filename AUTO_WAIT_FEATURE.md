# Auto-Wait Feature Implementation

## Overview
Units now automatically wait after moving if they have no valid actions available, streamlining gameplay and reducing unnecessary clicks.

## How It Works

When a unit moves to a new position, the system checks for available actions:

### Checked Actions:
1. **Attack** - Are there enemy units in range?
2. **Capture** - Is Infantry/Mech on a capturable property?
3. **Load** - Are there adjacent friendly transports with space?
4. **Launch** - For missiles, are there targets in range?
5. **Join** - Can join with damaged units of same type?
6. **Supply** - For APC/Black Boat, are there adjacent units needing fuel/ammo?
7. **Repair** - For Black Boat, are there adjacent damaged units?

### Auto-Wait Behavior:
- If **NO** actions are available → Unit automatically waits
- If **ANY** action is available → Action menu appears

## Benefits
- Faster gameplay - no need to manually wait when there's nothing to do
- Reduces misclicks and forgotten units
- Makes the game flow more intuitive

## Implementation Details

The logic is in `showPostMoveActionMenu()`:
```javascript
// If no actions available, auto-wait
if (!hasAttackTargets && !canCapture && !canLoadTransport && 
    !canLaunchMissile && !canJoin && !canSupply && !canRepair) {
    console.log('🤖 No actions available - auto-waiting unit');
    unitWait(tile);
    endUnitTurn();
    return;
}
```

## Helper Functions Added:
- `checkCanLoadTransport()` - Checks for adjacent transports
- `checkCanJoinUnit()` - Checks if unit can join with damaged same-type units
- `checkHasAdjacentUnitsToSupply()` - For APC/Black Boat supply ability
- `checkHasAdjacentUnitsToRepair()` - For Black Boat repair ability
- `getMaxFuel()` / `getMaxAmmo()` - Unit stat lookups

## Console Output
When auto-wait triggers, you'll see:
```
📋 Checking post-move actions...
🤖 No actions available - auto-waiting unit
```

## Manual Override
Players can still access all actions through:
- **Action Menu** - Appears when actions are available
- **Right-Click** - Context menu for supply/repair
- **Double-Click** - Quick wait/capture

## Future Improvements
- Add setting to disable auto-wait if players prefer manual control
- Implement actual join functionality (currently shows in menu but not implemented)
- Add visual indicator when auto-wait occurs
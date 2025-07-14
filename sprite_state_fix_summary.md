# Sprite State Fix Summary

## Problem
Units were not showing as unavailable (grayed out) after performing actions because the server wasn't properly updating the `can_move`, `can_attack`, and `can_capture` flags.

## Solution
Implemented client-side flag updates to manually set these flags to false after units perform actions.

## Changes Made

### 1. Attack Handler Updates
- Modified `executeAttack()` function to set all flags to false after attack (render.js:2341-2345)
- Updated promise-based attack handler to also set flags (render.js:3249-3253)

### 2. Movement Handler Updates  
- Updated `advanceWarsMove()` to set `can_move` to false after moving (render.js:3183-3185)
- Note: `can_attack` may still be true after moving if unit hasn't attacked yet

### 3. Wait Action Updates
- Modified `unitWait()` to set all flags to false when unit waits (render.js:579-593, 3740-3754)

### 4. End Unit Turn Updates
- Enhanced `endUnitTurn()` to manually update flags before clearing selection (render.js:3293-3297)

### 5. Testing Functions Added
- `testSpriteStates()` - Shows current state of all units for debugging
- Enhanced `simulateGameFlow()` - Simulates user interactions for testing

## How It Works

1. **Sprite State Logic**: Units show as "idle" (available) when any of `can_move`, `can_attack`, or `can_capture` is true. They show as "unavailable" (grayed out) when all are false.

2. **Client-Side Updates**: Since the server doesn't properly update these flags, we manually set them to false on the client side after each action.

3. **Visual Update**: After changing flags, we call `update()` to refresh the display with new sprite states.

## Testing

1. Open browser console and run `testSpriteStates()` to see current unit states
2. Move a unit and check its state again - `can_move` should be false
3. Attack with a unit - all flags should become false  
4. Use `simulateGameFlow()` to automatically test the flow

## Known Limitations

- This is a client-side workaround for a server bug
- State will reset if page is refreshed since server still has wrong data
- Proper fix would be to update server to correctly manage these flags

## Console Commands

- `testSpriteStates()` - Check unit availability states
- `simulateGameFlow()` - Simulate move/attack sequence
- `clearAllHighlights()` - Manually clear all highlights
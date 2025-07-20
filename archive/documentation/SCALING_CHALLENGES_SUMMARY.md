# Scaling Challenges Summary - Advance Wars RPC

## Date: 2025-07-20

## The Core Problem
The game renders at 192x176 pixels (12x10 tiles @ 16px each), which is too small for modern screens. Every scaling attempt creates new issues.

## Why Scaling Keeps Failing

### 1. CSS Transform Scale
**What happens:** `transform: scale(3)` makes canvas appear 3x larger
**Problem:** Browser events still report original coordinates
**Result:** Clicks register in wrong tiles

### 2. TILESIZE Scaling  
**What happens:** Changed TILESIZE from 16 to 48
**Problem:** 
- Canvas scales to 576x528 ✅
- But sprites stay at 16x16 ❌
- Tiny sprites on large tiles
- Would need to scale ALL rendering code

### 3. Multiple Coordinate Systems
The game has several interconnected systems:
- Tile coordinates (0-11 x 0-9)
- Pixel coordinates (TILESIZE-based)
- Sprite rendering (16x16 fixed)
- Scene offset (Y+16 pixels)
- Click event coordinates

Changing any one system breaks the others.

## Why It's So Complex

1. **Sprite Sheets:** All sprites are designed for 16x16 tiles
2. **Hardcoded Values:** Many places assume 16px tiles
3. **Two.js Rendering:** Sprites, tiles, and UI all tied to TILESIZE
4. **Event Handling:** Click math assumes specific pixel sizes

## Current State
- Game works at original 192x176 size
- Clicks work correctly (after token fixes)
- Too small but functional

## Possible Solutions

### 1. Complete Rendering Overhaul
- Scale EVERYTHING: tiles, sprites, offsets, click math
- Massive undertaking, high risk of bugs

### 2. Browser Zoom
- Let users zoom browser to 300%
- Simple but not ideal UX

### 3. New Assets
- Create 48x48 sprites and tiles
- Clean solution but requires art work

### 4. Canvas Stretching (CSS)
- Use `width: 576px; height: 528px` on canvas element
- But this still breaks click coordinates

## Recommendation
The game is functional at its current size. Given the complexity of scaling and the recurring issues it causes, it may be better to:
1. Focus on gameplay features
2. Let users zoom their browser if needed
3. Consider a proper scaling solution as a major future update

The recurring click issues all stem from attempts to make the game larger. At original size, clicks work correctly.
# Proper Scaling Solution for Advance Wars RPC

## Problem History
- Game renders too small (192x176 pixels)
- CSS transform scale breaks click coordinates
- This is a recurring issue we've faced before

## Why CSS Transform Fails
1. `transform: scale(3)` makes canvas appear 3x larger
2. BUT browser still reports original coordinates in events
3. `offsetX/offsetY` don't account for CSS transforms
4. Results in clicks registering in wrong tiles

## Better Solutions

### Option 1: Scale at Canvas Creation (RECOMMENDED)
```javascript
// Instead of:
var params = { 
    width: board.width * window.TILESIZE, 
    height: board.height * window.TILESIZE + extraHeight 
};

// Use:
const RENDER_SCALE = 3;
window.TILESIZE = 16 * RENDER_SCALE; // 48px tiles
var params = { 
    width: board.width * window.TILESIZE, 
    height: board.height * window.TILESIZE + extraHeight 
};
```

### Option 2: Larger Tile Assets
- Use 48x48 pixel tiles instead of 16x16
- No coordinate math changes needed
- But requires new sprite sheets

### Option 3: Canvas Pixel Ratio
```javascript
const scale = 3;
canvas.width = board.width * 16 * scale;
canvas.height = board.height * 16 * scale;
ctx.scale(scale, scale);
```

## Why Option 1 is Best
- Simple: Just change TILESIZE
- No coordinate translation needed
- Clicks work naturally
- Sprites scale with nearest-neighbor

## Implementation Plan
1. Change TILESIZE from 16 to 48 (3x scale)
2. Adjust scene offset accordingly
3. Test that clicks work without any scale math
4. Verify sprites still look crisp

This avoids the CSS transform pitfall entirely!
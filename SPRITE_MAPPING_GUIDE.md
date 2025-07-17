# Sprite Mapping Quick Reference Guide

## Current Status
- **Idle sprites**: Mostly complete (375 entries)
- **Movement sprites**: Only INFANTRY has some (8 entries)
- **Unavailable sprites**: Many complete (281 entries)

## How to Use the Sprite Showcase

1. **Open the showcase**: http://localhost:5000/sprites
2. **Check missing sprites**: Click "Check Missing Sprites" button
3. **Use browser console** for advanced commands:

### Console Commands

```javascript
// Check what's missing
checkMissingSprites()

// Find next unit to map
findNextUnmapped()

// Generate mapping for a unit (after finding coordinates)
generateUnitMapping('TANK', 'RED', baseX, baseY)

// Export all mappings to clipboard
exportMappings()
```

## Sprite Layout Pattern

### Standard Ground Unit Layout (per army row):
```
[Idle 0] [Idle 1] [Idle 2] ... [Movement Grid] ... [Unavailable 0] [Unavailable 1] [Unavailable 2]
```

### Spacing:
- **Unit sprites**: 16x16 pixels (idle/unavailable states)
- **Status indicators**: 8x8 pixels (HP, fuel, load/unload, submerged)
- **Between sprites**: 1px horizontal gap
- **Frame spacing**: 17px (16px sprite + 1px gap)

### Army Y-Offsets (approximate):
- **RED**: Y = 104+
- **BLUE**: Y = 672+  
- **GREEN**: Y = 672+ (X offset ~195)
- **YELLOW**: Y = 767+
- **GREY**: Y = 1335+

### Unit Spacing:
- Each unit type is ~19px below the previous

## Movement Sprite Patterns

### Ground Units (3x3 grid):
```
[NW] [N ] [NE]
[W ] [C ] [E ]  
[SW] [S ] [SE]
```
- 4 animation frames per direction
- Total: 36 sprites (9 directions × 4 frames)

### Air/Naval Units:
- Usually 2x3 or similar reduced grid
- 2-3 animation frames per direction

## Mapping Process

1. **Find the unit row** on sprite sheet
2. **Identify idle sprites** (3 in a row)
3. **Note the base X,Y coordinates**
4. **Generate mapping**: `generateUnitMapping('UNIT', 'ARMY', x, y)`
5. **Copy the output** (auto-copied to clipboard)
6. **Add to sprite_corrections_config.json**

## Tips

- Red squares in showcase = missing sprites
- Use browser zoom to see sprites better
- Movement sprites are usually to the right of idle sprites
- Unavailable sprites are often grayed-out versions

## Priority Order

1. Complete all idle sprites first (for basic display)
2. Add unavailable sprites (for turn management)  
3. Add movement sprites last (for animations)
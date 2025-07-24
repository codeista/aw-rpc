# Hardcoded Colors Summary

This document summarizes where colors are hardcoded throughout the AW-RPC codebase.

## 1. Python Core Game Logic

### models_v2.py - Army Enum Definition
```python
class Army(Enum):
    RED = 'red'
    BLUE = 'blue'
    GREEN = 'green'
    YELLOW = 'yellow'
    GREY = 'grey'
    NEUTRAL = 'neutral'
    FOG = 'fog'
```

### map_system.py - Army Enum (Integer-based)
```python
class Army(Enum):
    RED = 0
    BLUE = 1
    GREEN = 2
    YELLOW = 3
    GREY = 4
```

### manager.py - Legacy Support for RED/BLUE
The manager has special handling for RED and BLUE armies for backward compatibility:
- Lines 239-249: Property ownership tracking (total_red_properties, total_blue_properties)
- Lines 254-268: Fund management (red_funds, blue_funds)
- Lines 296-311: Troop counting (total_red_troops, total_blue_troops)
- Lines 402-405: Initial fund setup
- Lines 947-950: Unit production

This creates a dual system where RED/BLUE have both legacy fields AND the flexible army_funds system.

## 2. Map Definitions

### map_system.py - Hardcoded Army Names in Maps
All predefined maps use color names directly:
- Line 459: `RED,BLUE` for test map
- Line 472: `RED,BLUE` for scorpion map
- Line 489: `RED,BLUE,GREEN` for triangle map
- Line 505: `RED,BLUE,GREEN,YELLOW` for cross map
- Line 521: `RED,BLUE,GREEN,YELLOW,GREY` for pentagon map
- Lines 541-602: Various victory test maps using GREEN/YELLOW combinations

Map format requires army names in the header (e.g., "RED,BLUE") and uses format like "CITY:RED" for owned properties.

## 3. JavaScript/Frontend

### game_v2.js - Color Mapping System
- Line 15: `this.playerColors = {}` - Maps player_id to color string
- Line 73: Color assignment from player data
- Line 428: Building sprites use color prefix: `${color}_${spriteName}`
- Line 439: Unit sprites use color in name: `${unit.type}_${color}_${state}_0`

### Static Player Creation
- Line 47-48: Default players created with hardcoded colors:
  ```javascript
  { name: 'Player 1', color: 'red' },
  { name: 'Player 2', color: 'blue' }
  ```

## 4. Sprite Naming Convention

### Sprite File Names
All unit and building sprites follow the pattern:
- Units: `{UNIT_TYPE}_{COLOR}_{STATE}_{FRAME}`
  - Example: `INFANTRY_RED_idle_0`, `TANK_BLUE_unavailable_0`
- Buildings: `{COLOR}_{BUILDING_TYPE}`
  - Example: `RED_FACTORY`, `BLUE_BASE_TOWER_0`

### sprite_corrections_config.json
Contains hundreds of sprite coordinate mappings using color-based naming:
- `INFANTRY_RED_idle_0`, `INFANTRY_RED_idle_1`, etc.
- `TANK_BLUE_idle_0`, `TANK_BLUE_unavailable_0`, etc.

## 5. RPC/API Layer

### routes/rpc_methods.py
- Line 70: Player creation uses `player.get('color', 'RED')` defaulting to RED
- Army assignment from player color string

## 6. Test Files
Many test files reference specific colors:
- Unit placement with specific armies (e.g., `"army": "RED"`)
- Victory condition tests for specific color combinations
- Map creation with hardcoded army lists

## Key Issues with Current System

1. **Dual Army Systems**: Two different Army enums (string-based in models_v2.py, integer-based in map_system.py)

2. **Legacy Support**: RED/BLUE have special fields (red_funds, blue_funds) while other colors only use army_funds dictionary

3. **Sprite Dependency**: All sprites are named with specific colors, making color changes require sprite renaming

4. **Map Format**: Maps hardcode army colors in their definition, tying map data to specific colors

5. **Frontend Coupling**: JavaScript expects color strings and builds sprite names from them

## Recommendations for Decoupling Colors

1. **Use Army IDs**: Replace color names with army IDs (ARMY_1, ARMY_2, etc.) internally
2. **Color Configuration**: Add a color theme/configuration system that maps army IDs to display colors
3. **Sprite Abstraction**: Load sprites by army ID and state, with color mapping handled by configuration
4. **Map Format Update**: Use army IDs in maps instead of color names
5. **Unified Army System**: Consolidate the two Army enum systems into one
6. **Remove Legacy Fields**: Migrate away from red_funds/blue_funds to only use army_funds dictionary
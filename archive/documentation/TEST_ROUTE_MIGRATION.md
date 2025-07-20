# Test Route Migration Guide

## Overview

All test game creation routes have been consolidated into a single parameterized endpoint: `/test_game`

## Migration Map

| Old Route | New Route | Notes |
|-----------|-----------|-------|
| `/test` | `/test_game` or `/test_game?type=basic` | Basic test game |
| `/test_comprehensive` | `/test_game?type=comprehensive` | All features with units |
| `/test_movement` | `/test_game?type=movement` | Movement-focused units |
| `/test_combat` | `/test_game?type=combat` | Combat scenario units |
| `/test_optimized` | `/test_game?type=optimized` | Quick all-features |
| `/test_transport` | `/test_game?type=transport` | Transport operations |
| `/test_capture` | `/test_game?type=capture` | Capture mechanics |
| `/test_triangle` | `/test_game?type=triangle` | 3-player game |
| `/test_cross` | `/test_game?type=cross` | 4-player game |
| `/test_pentagon` | `/test_game?type=pentagon` | 5-player game |

## Additional Test Types

New test types available through the unified route:

- `/test_game?type=scorpion` - Scorpion Operation map
- `/test_game?type=green_yellow` - Green vs Yellow victory test
- `/test_game?type=islands` - Island battle scenario
- `/test_game?type=mountains` - Mountain warfare
- `/test_game?type=hq_rush` - HQ rush scenario
- `/test_game?type=multi_army` - 4-color test
- `/test_game?type=elimination` - Small elimination test

## Query Parameters

- `type` - Type of test game (see list above)
- `map` - Override the default map for any test type
- `units` - Force unit deployment (true/false)
- `players` - (Future) Override number of players

## Examples

```bash
# Basic test game
/test_game

# Combat test with pre-deployed units
/test_game?type=combat

# Basic game on Scorpion map
/test_game?type=basic&map=scorpion

# Transport test forcing unit deployment
/test_game?type=transport&units=true

# Custom combination
/test_game?type=basic&map=pentagon&units=true
```

## API Endpoint

List all available test types and maps:
```
GET /test_game/list
```

Returns:
```json
{
  "types": {
    "basic": { "map": "test", "description": "..." },
    ...
  },
  "maps": ["test", "scorpion", "triangle", ...],
  "usage": { ... }
}
```

## Benefits

1. **Single endpoint** - Easier to remember and use
2. **Parameterized** - Flexible configuration
3. **Discoverable** - List endpoint shows all options
4. **Extensible** - Easy to add new test types
5. **Less code** - Reduces duplication

## Implementation Status

- ✅ Unified route created
- ⏳ Old routes still active (for backward compatibility)
- 🔜 Remove old routes after transition period
- 🔜 Update test interface to use new route
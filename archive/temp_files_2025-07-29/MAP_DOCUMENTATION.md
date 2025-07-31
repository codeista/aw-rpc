# Test Map Documentation

## Available Test Maps

### 1. comprehensive_test.txt (16x12)
**Purpose**: Test ALL game features in one map

**Features**:
- 2 COM_TOWERs (neutral) - For damage bonus testing
- 2 LABs (neutral) - For special mechanics
- 2 MISSILE_SILOs (neutral) - For one-time attacks
- 10 River tiles - For movement restrictions
- 2 Pipe tiles - For piperunner testing
- 4 Factories (2 per player)
- 2 Airports (1 per player)
- 2 Ports (1 per player)
- 2 HQs (BASE_TOWER_1, 1 per player)
- Various terrain: Mountains, Woods, Roads, Beaches, Sea, Reefs

**Test Scenarios**:
- COM_TOWER capture and damage stacking
- LAB functionality testing
- MISSILE_SILO usage
- River crossing limitations
- Pipe network navigation
- All production facility types
- Mixed terrain combat
- Naval operations

### 2. combat_test.txt (10x10)
**Purpose**: Focused combat and tactical testing

**Features**:
- 2 Factories (1 per player)
- 2 Airports (1 per player)
- 2 Ports (1 per player)
- 2 HQs (1 per player)
- 2 COM_TOWERs (neutral, center)
- 1 MISSILE_SILO (neutral, bottom center)
- Mountains for defensive positions
- Woods for cover
- Sea area for naval combat
- Beaches for amphibious operations

**Test Scenarios**:
- Direct vs indirect combat
- Terrain defense bonuses
- COM_TOWER control battles
- Naval combat
- Air superiority
- Choke point tactics

### 3. transport_test.txt (12x8)
**Purpose**: Transport mechanics and logistics

**Features**:
- 2 Ports (1 per player) - Naval transport
- 2 Factories (1 per player) - Ground units
- 2 Airports (1 per player) - Air transport
- 2 HQs (1 per player)
- Extensive road network
- Beach areas for landing
- Mountains and woods for terrain variety
- Sea with reefs

**Test Scenarios**:
- Lander beach operations
- APC unit transport on roads
- T-Copter transport over terrain
- Loading/unloading mechanics
- Transport capacity limits
- Multi-modal transportation

### 4. small_test.txt (8x6)
**Purpose**: Quick basic testing

**Features**:
- 2 Factories
- 2 HQs
- 2 Cities
- Basic terrain

### 5. cross_test.txt (8x8)
**Purpose**: 4-player game testing

**Features**:
- 4 Factories (1 per corner)
- 4 HQs (1 per player)
- Central city cluster
- Symmetrical layout

### 6. triangle_test.txt (9x7)
**Purpose**: 3-player game testing

**Features**:
- 3 Factories
- 3 HQs
- Triangular symmetry

## Default Test Map

The standard test game (created via `game_create_test`) uses a default map with:
- Size: 12x10
- 4 Factories (2 RED, 2 BLUE)
- 2 Airports (1 per player)
- 2 Ports (1 per player)
- 2 HQs (1 per player)
- 9 neutral Cities
- Various terrain including sea, mountains, woods, roads

## Map Format (V2)

Maps use the V2 format with player count:
```
[player_count]
[width],[height]
[tile data rows...]
```

Tile ownership uses player indices (0-based):
- `:0` = Player 0 (RED)
- `:1` = Player 1 (BLUE)
- No suffix = Neutral

## Creating Custom Test Maps

1. Start with player count (e.g., `2` for 2-player game)
2. Specify dimensions (e.g., `12,8`)
3. Add tile rows with proper spacing
4. Use correct tile names from MapType enum
5. Mark ownership with `:N` suffix where N is player index

## Testing with Custom Maps

```python
# Via RPC
result = rpc_call("game_create_v2", {
    "token": "mytest",
    "map_name": "comprehensive_test"
})

# Via GameFactory
manager, token = GameFactory.create_game_with_map('comprehensive_test', players)
```
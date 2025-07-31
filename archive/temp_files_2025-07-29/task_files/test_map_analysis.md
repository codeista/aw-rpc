# Test Map Analysis and Requirements

## Current Test Map Analysis

### Main Test Map (12x10)
**Has:**
- 2 HQs (BASE_TOWER_1) - one per team
- 4 Factories (2 RED, 2 BLUE)
- 2 Airports (1 RED, 1 BLUE) 
- 2 Ports (1 RED, 1 BLUE)
- 9 neutral Cities
- Various terrain: Plains, Woods, Mountains, Sea, Reefs, Roads, Beaches

**Missing:**
- COM_TOWER (for damage bonus testing)
- LAB (for income/special mechanics)
- MISSILE_SILO (for special attacks)
- Rivers (for movement testing)
- Pipes (for piperunner movement)
- Bridges (for naval/ground interaction)

### Small Test Maps
- **small_test.txt (8x6)**: Basic with 2 factories, 2 HQs, 2 cities, some woods
- **cross_test.txt (8x8)**: 4-player setup with 4 factories, 4 HQs, neutral cities
- **triangle_test.txt (9x7)**: 3-player setup with 3 factories, 3 HQs

## Missing Test Coverage

### 1. Special Buildings
- [ ] COM_TOWER - Need to test damage bonus stacking
- [ ] LAB - Need to test special mechanics
- [ ] MISSILE_SILO - Need to test one-time use attack

### 2. Special Terrain
- [ ] Rivers - Test movement restrictions
- [ ] Bridges - Test multi-layer movement
- [ ] Pipes & Pipe Seams - Test piperunner movement
- [ ] Different pipe configurations (corners, ends, broken)

### 3. Combat Scenarios
- [ ] Indirect unit positioning (Artillery, Rockets, Missiles)
- [ ] Naval combat areas
- [ ] Air unit interception zones
- [ ] Choke points for tactical testing

### 4. Transport Testing
- [ ] Beach areas for Lander loading/unloading
- [ ] Open sea for naval transport
- [ ] Roads near factories for APC loading
- [ ] Mixed terrain for T-Copter operations

### 5. Economic Testing
- [ ] High property density areas
- [ ] Property clusters for capture strategy
- [ ] Isolated properties for expansion testing

## Proposed Test Maps

### 1. comprehensive_test.txt (16x12)
```
Purpose: Test ALL game features in one map
- All building types (Factory, Airport, Port, HQ, City, COM_TOWER, LAB, MISSILE_SILO)
- All terrain types (Plain, Wood, Mountain, Road, River, Bridge, Sea, Reef, Beach, Pipe)
- Multiple choke points and tactical positions
- Balanced for 2-4 players
```

### 2. combat_test.txt (10x10)
```
Purpose: Focused combat testing
- Open areas for direct combat
- Forests/mountains for defensive positions
- Long sight lines for indirect units
- Naval combat zone
- Air superiority testing area
```

### 3. transport_test.txt (12x8)
```
Purpose: Transport mechanics
- Beaches for lander operations
- Roads connecting all facilities
- Mixed terrain for copter transport
- Islands requiring naval/air transport
```

### 4. special_features.txt (10x10)
```
Purpose: Special mechanics testing
- Multiple COM_TOWERs for damage stacking
- MISSILE_SILOs in strategic positions
- LABs for special mechanics
- Pipe network for piperunner testing
```

### 5. economy_test.txt (14x10)
```
Purpose: Economic warfare testing
- High property density
- Property chains for capture routes
- Isolated high-value targets
- Resource denial positions
```

## Test Map Requirements

### Essential Elements for Complete Testing
1. **Buildings** (minimum per map)
   - 2+ HQs (different variants)
   - 2+ Factories
   - 2+ Airports 
   - 2+ Ports
   - 4+ Cities
   - 1+ COM_TOWER
   - 1+ LAB
   - 1+ MISSILE_SILO

2. **Terrain Variety**
   - Open plains for movement
   - Defensive terrain (woods/mountains)
   - Water bodies for naval units
   - Beaches for amphibious operations
   - Roads for rapid movement
   - Rivers for movement restriction
   - Pipes for special unit movement

3. **Tactical Features**
   - Choke points
   - High ground positions
   - Naval passages
   - Air corridors
   - Property clusters
   - Isolated objectives

4. **Balance Considerations**
   - Symmetrical or balanced asymmetric layout
   - Equal access to resources
   - Multiple viable strategies
   - No dominant positions

## Implementation Priority
1. **High Priority**: comprehensive_test.txt - Covers all features
2. **Medium Priority**: combat_test.txt, transport_test.txt
3. **Low Priority**: special_features.txt, economy_test.txt

## Next Steps
1. Create comprehensive_test.txt map file
2. Update game_create_test to support map selection
3. Create unit tests for each map scenario
4. Document expected behaviors for each test map
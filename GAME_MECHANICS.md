# Advance Wars RPC - Game Mechanics Guide

## Core Game Rules

### Turn Structure
1. **Turn Start**
   - Income is added (1000 per property)
   - Units are activated (can_move, can_attack, can_capture = True)
   - Fuel is consumed for air/sea units
   - Auto-resupply triggers for APCs, Cruisers, and Carriers
   - Units on repair facilities heal 20 HP

2. **During Turn**
   - Units can perform ONE action: move, attack, capture, or wait
   - After moving, a unit can still attack if it hasn't acted
   - After any action, the unit is done for the turn

3. **Turn End**
   - All unit flags reset
   - Control passes to next player

### Unit Creation
- Units are created at production facilities:
  - **Factory**: Ground units (Infantry, Tanks, Artillery, etc.)
  - **Airport**: Air units (Fighters, Bombers, Helicopters, etc.)
  - **Port**: Naval units (Battleships, Submarines, Landers, etc.)
- **Created units CANNOT move on their first turn** (can_move = False)
- Must have sufficient funds before creation

### Movement System
- Each unit has a movement range based on unit type
- Terrain affects movement cost:
  - Roads: 1 movement point
  - Plains: 1 point (2 for treads)
  - Forests: 2 points (3 for wheels)
  - Mountains: Infantry only, 2 points
- Fuel is consumed with each move
- Cannot move through enemy units
- Can move through (but not stop on) friendly units

### Combat System
- Damage is calculated based on:
  - Base damage from damage table
  - Attacker's HP (damaged units do less damage)
  - Defender's terrain defense bonus
  - Random luck factor (0-9%)
- Counter-attacks occur if:
  - Defender survives
  - Attacker is within defender's range
  - Uses defender's reduced HP for damage calculation

### Transport Mechanics

#### Loading Rules
- Cargo units move INTO transports (not picked up)
- Transport must have space available
- Some transports have terrain restrictions:
  - Lander: Only at beaches/ports
  - APC: Only on land terrain
  - Others: No restrictions

#### Unloading Rules  
- Transport selects adjacent empty tile
- Unloaded unit CANNOT act that turn
- Transport CANNOT move after unloading

#### Transport Types
1. **APC**
   - Capacity: 1 Infantry/Mech
   - Special: Auto-resupplies ALL adjacent units at turn start
   - Loading: Land terrain only

2. **T-Copter (Transport Copter)**
   - Capacity: 1 Infantry/Mech
   - Air transport, no terrain restrictions

3. **Lander**
   - Capacity: 2 ground units
   - Loading: Beaches and ports only
   - Can carry tanks, artillery, etc.

4. **Black Boat**
   - Capacity: 2 Infantry/Mech
   - Loading: Beaches and ports only
   - Special: Can manually repair adjacent units (2 HP max, costs 10% per HP)

5. **Cruiser**
   - Capacity: 2 helicopters
   - Special: Auto-resupplies carried units at turn start

6. **Carrier**
   - Capacity: 2 planes
   - Special: Auto-resupplies carried units at turn start

### Property System
- Properties provide 1000 funds per turn
- Infantry/Mech can capture properties:
  - Takes multiple turns (HP/10 capture points per turn)
  - Must start fresh if interrupted
  - Cannot capture while in transport
- HQ capture = instant victory

### Victory Conditions
1. **HQ Capture**: Capture enemy headquarters
2. **Elimination**: Destroy all enemy units
3. **Property Control**: Control majority of properties when turn limit reached
4. **Turn Limit**: Highest score when max turns reached

### Special Mechanics

#### Fuel System
- All units have limited fuel
- Movement consumes fuel (1 per tile for most units)
- Air units consume fuel each turn (even stationary)
- Units crash/sink when fuel reaches 0
- Resupply at cities/bases or from APC

#### Repair System
- Automatic repair at friendly facilities (20 HP/turn)
- Costs 10% of unit cost per HP
- Black Boat manual repair (adjacent units, 2 HP max)

#### Fog of War (Not Yet Implemented)
- Units have vision range
- Forests/reefs hide units
- Recon units have extended vision

## Testing Tips

### Creating Test Games
```javascript
// Regular game (5000 starting funds)
rpc('game_create', {token: 'mygame'})

// Test game (50000 starting funds)
rpc('game_create_test', {token: 'testgame'})
```

### Common Test Scenarios
1. **Transport Testing**
   - Create transport at appropriate facility
   - End turn to enable movement
   - Move cargo unit into transport
   - Move transport and unload

2. **Combat Testing**
   - Create units in range
   - Select attacker
   - Click defender
   - Check damage preview

3. **Black Boat Repair**
   - Create Black Boat at port
   - Create damaged friendly unit adjacent
   - Select Black Boat
   - Right-click damaged unit
   - Choose repair from context menu

## RPC Reference

See README.md for complete RPC method documentation.
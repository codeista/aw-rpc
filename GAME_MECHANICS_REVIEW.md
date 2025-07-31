# ADVANCE WARS RPC - GAME MECHANICS REVIEW
## Security-Fixes Branch Analysis

This document provides a comprehensive review of all game mechanics in the Advance Wars RPC implementation, detailing how players interact with each system and what happens next.

---

## 1. TURN SYSTEM

### How It Works:
- **Turn Order**: Players take turns in sequence (managed by `turn_order` in GameBoardV2)
- **Current Player**: Tracked via `current_player` index in turn order
- **Army Assignment**: Each player controls one army (RED, BLUE, GREEN, YELLOW)

### Player Interactions:
- `army_end_turn()` - End current turn and advance to next player
- All units of ending player become inactive
- All units of new player become active
- Income is distributed at turn start

### What Happens Next:
1. Turn-end effects applied (currently minimal)
2. Turn advances to next player in order
3. All new player's units activated
4. Income calculated and distributed (1000 per property)
5. Auto-resupply occurs for units on/near resupply points

---

## 2. UNIT CREATION SYSTEM

### How It Works:
- **Production Facilities**: FACTORY (ground), AIRPORT (air), PORT (naval)
- **Unit Costs**: Defined in ProductionSystem.UNIT_COSTS
- **Creation Rule**: New units cannot act on creation turn

### Player Interactions:
- `get_production_options(x, y, army)` - View available units and costs
- `produce_unit(x, y, unit_type)` - Create new unit at facility
- Must have sufficient funds
- Facility must be unoccupied

### What Happens Next:
1. Funds deducted from player
2. Unit created at facility location
3. Unit marked as inactive (can_move=false, can_attack=false)
4. Player statistics updated (troop count)

---

## 3. MOVEMENT SYSTEM

### How It Works:
- **Movement Points**: Each unit has movement range (e.g., Infantry=3, Tank=6)
- **Terrain Costs**: Different terrains cost different movement points
- **Fuel Consumption**: Movement consumes fuel based on distance
- **Direct vs Indirect**: Direct units can attack after moving, indirect cannot

### Player Interactions:
- `unit_move(x, y, x2, y2)` - Move unit from (x,y) to (x2,y2)
- `get_unit_valid_moves(unit)` - Get all valid destinations
- `get_movement_preview(x, y, x2, y2)` - Preview fuel cost

### What Happens Next:
1. Path validated using Dijkstra's algorithm
2. Fuel consumed based on actual path cost
3. Unit moved to destination
4. Unit marked as can_move=false
5. If indirect unit: also marked can_attack=false
6. If direct unit: can still attack

---

## 4. COMBAT SYSTEM

### How It Works:
- **Damage Formula**: Base damage * (attacker_hp/10) * terrain_defense * modifiers
- **Counter-attacks**: Defender strikes back if survives and in range
- **Terrain Defense**: Reduces incoming damage (e.g., Mountains=40% reduction)
- **COM_TOWER Bonus**: +10% attack per owned COM_TOWER (max +40%)

### Player Interactions:
- `unit_attack_enhanced(attacker_x, attacker_y, defender_x, defender_y)` - Execute attack
- `get_damage_preview(ax, ay, dx, dy)` - Preview damage before attacking
- Must be in range (min-max range per unit type)
- Cannot attack friendly units

### What Happens Next:
1. Damage calculated with all modifiers
2. Defender HP reduced
3. If defender survives and can counter: counter-damage applied
4. Units with HP ≤ 0 removed from board
5. Attacker marked as inactive
6. Victory conditions checked

---

## 5. CAPTURE SYSTEM

### How It Works:
- **Eligible Units**: Only INFANTRY and MECH can capture
- **Capture Power**: HP/10 rounded up (e.g., 100HP = 10 capture power)
- **Capture HP**: Properties have 20 capture HP
- **HQ Victory**: Capturing enemy HQ wins the game

### Player Interactions:
- `capture_tile(x, y)` - Initiate/continue capture
- `capture_tile_enhanced(x, y)` - Enhanced version with feedback
- `get_capture_preview(x, y)` - Check capture progress
- Unit must be on capturable property

### What Happens Next:
1. Capture power applied to property
2. If capture HP reaches 0: ownership changes
3. Income statistics updated
4. COM_TOWER modifiers recalculated if applicable
5. If HQ captured: game ends immediately
6. Capturing unit marked as inactive

---

## 6. TRANSPORT SYSTEM

### How It Works:
- **Loading**: Units move INTO transports (not picked up)
- **Capacity**: APC/T-Copter(1), Lander/BlackBoat/Cruiser/Carrier(2)
- **Restrictions**: Type-specific (e.g., Cruiser carries only helicopters)
- **Unload Rule**: Unloaded units cannot act same turn

### Player Interactions:
- `load_transport_unit(transport_x, transport_y, cargo_x, cargo_y)` - Load unit
- `unload_transport_unit(transport_x, transport_y, unload_x, unload_y, index)` - Unload
- `get_transport_cargo_info(unit)` - View loaded units
- Loading happens by moving cargo to transport position

### What Happens Next:
1. **On Load**: Cargo removed from map, stored in transport
2. **On Unload**: Cargo placed at destination, marked inactive
3. Transport marked as having acted (cannot move after unload)
4. Auto-resupply for some transports (Cruiser/Carrier at turn start)

---

## 7. PROPERTY & ECONOMY SYSTEM

### How It Works:
- **Income**: 1000 funds per property owned
- **Distribution**: At start of player's turn
- **Property Types**: CITY, FACTORY, AIRPORT, PORT, COM_TOWER, HQ
- **Starting Funds**: Minimum 10,000 or 3x starting income

### Player Interactions:
- Properties change hands via capture
- COM_TOWERs provide attack bonuses when owned
- Production facilities enable unit creation

### What Happens Next:
1. Income calculated: property_count × 1000
2. Funds added to player's treasury
3. Player can spend on unit production/repairs
4. COM_TOWER ownership updates damage modifiers

---

## 8. SPECIAL ABILITIES

### Repair (Black Boat Only)
- **Interaction**: `repair_unit_rpc(blackboat_x, blackboat_y, target_x, target_y, hp)`
- **Cost**: 10% of unit cost per HP repaired
- **Limit**: Max 2 HP per turn, cannot exceed 10 visual HP
- **Bonus**: Also resupplies fuel/ammo for free

### Auto-Resupply
- **APCs**: Resupply adjacent friendly units at turn start
- **Properties**: Units ON properties auto-resupply at turn start
- **Cruiser/Carrier**: Auto-resupply loaded aircraft at turn start
- **Effect**: Restores fuel and ammo to maximum

### What Happens Next:
1. **Repair**: HP restored, funds deducted, fuel/ammo refilled
2. **Resupply**: Fuel and ammo set to maximum values
3. Black Boat marked as having acted after repair

---

## 9. VICTORY CONDITIONS

### Three Ways to Win:
1. **HQ Capture**: Capture enemy headquarters
2. **Elimination**: Destroy all enemy units
3. **Property Control**: Control majority of properties (if enabled)

### What Happens Next:
- `game_active` set to false
- Winner recorded in `board.winner`
- Victory type stored in `board.victory_type`
- Game cannot continue after victory

---

## 10. UNIT STATE MANAGEMENT

### Unit Action Flags:
- **can_move**: Can unit move this turn?
- **can_attack**: Can unit attack this turn?
- **can_capture**: Can unit capture? (Infantry/Mech only)

### State Transitions:
1. **Turn Start**: All flags set to true for active player's units
2. **After Move**: can_move = false, indirect units also lose can_attack
3. **After Attack**: All flags set to false
4. **After Capture**: All flags set to false
5. **After Wait**: All flags set to false
6. **Unloaded Units**: All flags set to false

---

## 11. MODIFIER SYSTEM

### Current Modifiers:
- **COM_TOWER**: +10% attack damage per tower (cumulative)
- **Terrain Defense**: Reduces incoming damage by percentage
- **HP-based Damage**: Damage scales with attacker's HP

### Future Expansion:
- CO Powers (not yet implemented)
- Weather effects (not yet implemented)
- Special abilities (not yet implemented)

---

## KEY GAME FLOW

1. **Turn Start**:
   - Income distributed
   - Units activated
   - Auto-resupply occurs

2. **During Turn**:
   - Move units
   - Attack enemies
   - Capture properties
   - Produce new units
   - Load/unload transports

3. **Turn End**:
   - All units deactivated
   - Turn advances to next player
   - Victory conditions checked

---

## RECENT SECURITY FIXES (Branch: security-fixes)

The security-fixes branch includes:
1. Movement highlight persistence fixes
2. Game state persistence improvements
3. Production deployment security updates
4. Enhanced validation for all player actions
5. Improved error handling and logging

These fixes ensure game state remains consistent and secure across all player interactions.
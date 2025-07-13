# Common Test Patterns and Solutions

## Quick Reference

### Always Remember
1. Units created this turn CANNOT move
2. Turn order matters - use `ensure_correct_turn()`
3. Use `game_create_test` for 50000 starting funds
4. Visual HP = ceil(actual_hp / 10)

## Pattern Library

### Pattern 1: Create and Enable Unit
```python
# WRONG - Unit can't move same turn
unit = create_unit(game_id, "TANK", 5, 5, "RED")
move_unit(game_id, 5, 5, 7, 5)  # FAILS!

# CORRECT - End turns to enable movement
unit = create_unit(game_id, "TANK", 5, 5, "RED")
end_turn(game_id)  # End RED turn
end_turn(game_id)  # End BLUE turn, back to RED
move_unit(game_id, 5, 5, 7, 5)  # SUCCESS!
```

### Pattern 2: Ensure Correct Turn
```python
# WRONG - Assuming it's RED's turn
attack_unit(game_id, red_x, red_y, blue_x, blue_y)  # May fail!

# CORRECT - Ensure it's RED's turn first
while get_current_turn(game_id) != "RED":
    end_turn(game_id)
attack_unit(game_id, red_x, red_y, blue_x, blue_y)
```

### Pattern 3: Damage Unit for Testing
```python
# Create unit to damage
infantry = create_unit(game_id, "INFANTRY", 5, 5, "RED")
end_turn(game_id)
end_turn(game_id)

# Create enemy attacker
ensure_turn(game_id, "BLUE")
tank = create_unit(game_id, "TANK", 6, 5, "BLUE")
end_turn(game_id)
end_turn(game_id)

# Attack to damage
ensure_turn(game_id, "BLUE")
attack_unit(game_id, 6, 5, 5, 5)  # Tank attacks Infantry

# Now Infantry is damaged for repair testing
ensure_turn(game_id, "RED")
```

### Pattern 4: Test Transport Loading
```python
# Create transport first (it needs to exist)
apc = create_unit(game_id, "APC", 5, 5, "RED")
end_turn(game_id)
end_turn(game_id)

# Create cargo unit
infantry = create_unit(game_id, "INFANTRY", 4, 5, "RED")
end_turn(game_id)
end_turn(game_id)

# Load by moving cargo INTO transport
ensure_turn(game_id, "RED")
move_unit(game_id, 4, 5, 5, 5)  # Infantry moves into APC
```

### Pattern 5: Test Facility Production
```python
# Factories are at specific coordinates
# RED: (0,4), (1,4)
# BLUE: (9,4), (8,4)

# Create at RED factory
ensure_turn(game_id, "RED")
create_unit(game_id, "TANK", 0, 4, "RED")

# Create at BLUE factory  
ensure_turn(game_id, "BLUE")
create_unit(game_id, "TANK", 9, 4, "BLUE")
```

## Common Pitfalls

### Pitfall 1: HP Confusion
```python
# WRONG - Checking for literal 10 HP
if unit.hp >= 10:
    print("Unit at max HP")

# CORRECT - HP is 0-100, visual is 1-10
if unit.hp >= 100:
    print("Unit at max HP")
    
visual_hp = math.ceil(unit.hp / 10)
if visual_hp >= 10:
    print("Unit at max visual HP")

# Black Boat repair limit
if unit.hp > 90:
    print("Black Boat cannot repair (but can resupply)")
```

### Pitfall 2: Transport Movement
```python
# WRONG - Moving transport after load/unload
load_unit(transport, cargo)
move_unit(transport, x, y)  # FAILS - transport can't move after load

# CORRECT - Move first, then load/unload
move_unit(transport, x, y)
load_unit(transport, cargo)  # OK
```

### Pitfall 3: Attack Range
```python
# WRONG - Not checking attack range
attack_unit(artillery, target)  # May fail if out of range

# CORRECT - Check unit ranges
# Artillery: 2-3 range
# Tank: 1 range (adjacent only)
# Battleship: 2-6 range
distance = abs(x1-x2) + abs(y1-y2)
if min_range <= distance <= max_range:
    attack_unit(attacker, target)
```

### Pitfall 4: Repair Limits
```python
# WRONG - Trying to repair beyond limits
repair_unit(blackboat, target, hp=10)  # Max is 2 per action

# CORRECT - Respect repair limits
# Black Boat: 1-2 HP per action, can't repair units >90 HP
# Facilities: 20 HP per turn
if target.hp <= 90:
    repair_unit(blackboat, target, hp=2)
else:
    # Can still resupply even at full HP
    resupply_unit(blackboat, target)
```

## Debugging Tips

### 1. Check Game State
```python
def debug_game_state(game_id):
    board = rpc_call("game_board", {"token": game_id})
    print(f"Current turn: {board['current_turn']}")
    print(f"Day: {board['days']}")
    print(f"RED funds: {board['red_funds']}")
    print(f"BLUE funds: {board['blue_funds']}")
```

### 2. Find Units on Board
```python
def find_units(game_id):
    board = rpc_call("game_board", {"token": game_id})
    for y, row in enumerate(board['tiles']):
        for x, tile in enumerate(row):
            if tile.get('unit'):
                unit = tile['unit']
                print(f"{unit['army']} {unit['type']} at ({x},{y}) - {unit['hp']}HP")
```

### 3. Verify Unit Status
```python
def check_unit_status(game_id, x, y):
    board = rpc_call("game_board", {"token": game_id})
    tile = board['tiles'][y][x]
    if tile.get('unit'):
        unit = tile['unit']
        print(f"Unit: {unit['type']}")
        print(f"HP: {unit['hp']} (Visual: {math.ceil(unit['hp']/10)})")
        print(f"Can move: {unit.get('can_move', False)}")
        print(f"Can attack: {unit.get('can_attack', False)}")
```

## Test Data Reference

### Unit Costs
- Infantry: 1000
- Tank: 7000
- Black Boat: 7500
- APC: 5000
- Battleship: 28000

### Movement Ranges
- Infantry: 3
- Tank: 6
- Recon: 8
- APC: 6
- Black Boat: 7

### Starting Positions
- RED HQ: (0,0)
- BLUE HQ: (9,9)
- RED Factories: (0,4), (1,4)
- BLUE Factories: (9,4), (8,4)

### Repair Rates
- Facilities: 20 HP/turn
- Black Boat: 1-2 HP/action (manual)
- APC: Full resupply (auto)
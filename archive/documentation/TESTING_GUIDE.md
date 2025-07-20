# Advance Wars RPC Testing Guide

## Overview

This guide explains how to write and run tests for the Advance Wars RPC game engine. Tests are critical for ensuring game mechanics work correctly and preventing regressions.

## Test Structure

### 1. RPC Test Pattern

All RPC tests should follow this basic structure:

```python
#!/usr/bin/env python3
"""
Test description - what feature/mechanic is being tested
"""

import requests
import json
import time
import random
import string

def rpc_call(method: str, params: dict = None) -> dict:
    """Make RPC call to the server"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    }
    
    response = requests.post("http://localhost:5000/api", json=payload)
    if response.status_code != 200:
        return {"error": f"HTTP {response.status_code}: {response.text}"}
    
    try:
        result = response.json()
        if "error" in result:
            return {"error": result["error"]}
        return result.get("result", {})
    except Exception as e:
        return {"error": f"JSON decode error: {str(e)}"}
```

### 2. Game Creation Pattern

Always create test games with sufficient funds:

```python
def create_test_game() -> str:
    """Create a test game with high starting funds"""
    print("🎮 Creating test game...")
    
    game_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    # Use game_create_test for high funds (50000)
    result = rpc_call("game_create_test", {"token": game_id})
    if "error" in result:
        print(f"❌ Failed to create game: {result['error']}")
        return None
    
    print(f"✅ Created test game: {game_id}")
    return game_id
```

### 3. Turn Management

CRITICAL: Always manage turns properly to avoid "Not your turn" errors:

```python
def ensure_correct_turn(game_id: str, expected_army: str = "RED") -> bool:
    """Ensure it's the correct army's turn"""
    board = rpc_call("game_board", {"token": game_id})
    if "error" in board:
        return False
    
    current_turn = board.get("current_turn", "")
    
    # Keep ending turns until we get to the expected army
    attempts = 0
    while current_turn != expected_army and attempts < 4:
        rpc_call("army_end_turn", {"token": game_id})
        board = rpc_call("game_board", {"token": game_id})
        current_turn = board.get("current_turn", "")
        attempts += 1
    
    return current_turn == expected_army
```

### 4. Unit Creation Pattern

Units cannot move on the turn they're created:

```python
def create_unit_and_enable(game_id: str, unit_type: str, x: int, y: int, army: str) -> dict:
    """Create a unit and enable it for movement"""
    
    # Create unit
    result = rpc_call("unit_create", {
        "token": game_id,
        "army": army,
        "unit_type": unit_type,
        "x": x,
        "y": y
    })
    
    if "error" in result:
        return result
    
    # End turn twice to enable movement
    rpc_call("army_end_turn", {"token": game_id})
    rpc_call("army_end_turn", {"token": game_id})
    
    return result
```

## Common Test Scenarios

### 1. Combat Testing

```python
def test_combat_damage():
    """Test damage calculations between units"""
    game_id = create_test_game()
    
    # Create attacker
    create_unit_and_enable(game_id, "TANK", 5, 5, "RED")
    
    # Create defender  
    ensure_correct_turn(game_id, "BLUE")
    create_unit_and_enable(game_id, "INFANTRY", 6, 5, "BLUE")
    
    # Attack
    ensure_correct_turn(game_id, "RED")
    result = rpc_call("unit_attack", {
        "token": game_id,
        "x": 5, "y": 5,  # Attacker
        "x2": 6, "y2": 5  # Defender
    })
    
    # Verify damage dealt
    assert result.get("success") == True
    print(f"✅ Combat successful: {result}")
```

### 2. Movement Testing

```python
def test_unit_movement():
    """Test unit movement and fuel consumption"""
    game_id = create_test_game()
    
    # Create and enable unit
    create_unit_and_enable(game_id, "RECON", 0, 0, "RED")
    
    # Get valid moves
    moves = rpc_call("get_valid_moves", {
        "token": game_id,
        "x": 0,
        "y": 0
    })
    
    # Move unit
    result = rpc_call("unit_move", {
        "token": game_id,
        "x": 0, "y": 0,
        "x2": 3, "y2": 0
    })
    
    assert result.get("success") == True
```

### 3. Transport Testing

```python
def test_transport_load():
    """Test loading units into transports"""
    game_id = create_test_game()
    
    # Create transport
    create_unit_and_enable(game_id, "APC", 5, 5, "RED")
    
    # Create cargo unit
    create_unit_and_enable(game_id, "INFANTRY", 4, 5, "RED")
    
    # Load unit
    ensure_correct_turn(game_id, "RED")
    result = rpc_call("cargo_board_transport", {
        "token": game_id,
        "cargo_x": 4, "cargo_y": 5,
        "transport_x": 5, "transport_y": 5
    })
    
    assert result.get("success") == True
```

### 4. Repair/Resupply Testing

```python
def test_black_boat_repair():
    """Test Black Boat repair functionality"""
    game_id = create_test_game()
    
    # Create Black Boat
    create_unit_and_enable(game_id, "BLACKBOAT", 0, 0, "RED")
    
    # Create damaged unit
    infantry = create_unit_and_enable(game_id, "INFANTRY", 1, 0, "RED")
    
    # Damage the infantry (create enemy to attack it)
    ensure_correct_turn(game_id, "BLUE") 
    create_unit_and_enable(game_id, "TANK", 2, 0, "BLUE")
    
    # Attack to damage
    ensure_correct_turn(game_id, "BLUE")
    rpc_call("unit_attack", {
        "token": game_id,
        "x": 2, "y": 0,
        "x2": 1, "y2": 0
    })
    
    # Repair with Black Boat
    ensure_correct_turn(game_id, "RED")
    result = rpc_call("repair_unit", {
        "token": game_id,
        "blackboat_x": 0, "blackboat_y": 0,
        "target_x": 1, "target_y": 0,
        "hp_to_repair": 2
    })
    
    assert result.get("success") == True
```

## HP System Notes

### Visual HP vs Actual HP

The game uses a dual HP system:
- **Actual HP**: 0-100 (internal)
- **Visual HP**: 1-10 (displayed)
- Conversion: `visual_hp = ceil(actual_hp / 10)`

### Important HP Rules

1. **Damage Calculations use Visual HP**
   ```python
   # In damage formula:
   attacker_visual_hp = math.ceil(attacker.status.hp / 10)
   # This affects damage output
   ```

2. **HP Caps**
   - Max HP: 100 (not 10!)
   - Min HP: 0 (units die at 0)
   - Repair facilities: +20 HP per turn (max 100)
   - Black Boat: +1-2 HP per action (repairs only up to 90 actual HP / 10 visual HP)
   - Black Boat: Always resupplies fuel/ammo even if unit has full HP

3. **Common HP Mistakes**
   - Don't change internal HP to 10 - breaks damage calculations
   - Don't allow negative HP - use `max(0, hp - damage)`
   - Don't allow HP > 100 - use `min(100, hp + heal)`
   - Black Boat can't repair units with >90 HP but CAN resupply them

## Test Organization

### File Structure
```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_combat_system.py
│   ├── test_movement_system.py
│   └── test_transport_system.py
├── integration/             # Integration tests for full features
│   ├── test_victory_conditions.py
│   └── test_economic_system.py
└── manual/                  # Manual test scripts
    ├── test_repair_refuel_proper.py
    └── test_multiplayer_sync.py
```

### Test Naming Conventions

- Test files: `test_<feature>_<scope>.py`
- Test functions: `test_<specific_behavior>()`
- Scenario setup: `setup_<scenario_name>()`
- Validation: `validate_<condition>()`

## Running Tests

### Command Line
```bash
# Run specific test
python3 test_repair_refuel_proper.py

# Run all unit tests
python3 -m pytest tests/unit/

# Run with verbose output
python3 -m pytest -v tests/
```

### Web Interface
1. Visit `http://localhost:5000/test_interface`
2. Click test category buttons
3. Monitor real-time results

## Common Issues and Solutions

### 1. "Not your turn" Errors
**Problem**: Trying to perform actions when it's not the unit's army's turn
**Solution**: Always use `ensure_correct_turn()` before actions

### 2. "Unit cannot move this turn"
**Problem**: Units created this turn cannot move
**Solution**: End turn twice after creating units

### 3. "Insufficient funds"
**Problem**: Not enough funds to create units
**Solution**: Use `game_create_test` for 50000 starting funds

### 4. "No unit at position"
**Problem**: Unit coordinates are wrong or unit was destroyed
**Solution**: Check board state with `game_board` RPC

### 5. HP Display Issues
**Problem**: Unit shows wrong HP in UI
**Solution**: Remember visual HP = ceil(actual_hp / 10)

## Test Best Practices

1. **Always validate preconditions**
   ```python
   # Check server is running
   try:
       response = requests.get("http://localhost:5000", timeout=5)
   except:
       print("❌ Server not accessible")
       return False
   ```

2. **Use descriptive test output**
   ```python
   print("🧪 Testing repair functionality...")
   print(f"   ✅ Unit repaired: {old_hp} → {new_hp} HP")
   print(f"   ❌ Repair failed: {error_msg}")
   ```

3. **Clean up test state**
   ```python
   # Return game ID for manual testing
   print(f"URL: http://localhost:5000/game/{game_id}")
   ```

4. **Test both success and failure cases**
   ```python
   # Test valid repair
   assert repair_result["success"] == True
   
   # Test invalid repair (full HP)
   assert repair_full_hp["error"] == "Target is already at full health"
   ```

5. **Document expected behavior**
   ```python
   """
   Test Black Boat repair mechanics:
   - Can repair adjacent friendly units
   - Repairs 1-2 HP per action
   - Cannot repair units above 10 visual HP (91-100 actual)
   - Costs 10% of unit value per HP
   """
   ```

## Example Complete Test

See `test_repair_refuel_proper.py` for a complete example that includes:
- Comprehensive setup scenarios
- Multiple test categories
- Proper error handling
- Manual testing instructions
- Results summary

## Contributing New Tests

When adding new tests:
1. Follow the patterns in this guide
2. Test both positive and negative cases
3. Include setup and teardown
4. Add manual testing instructions
5. Document any special requirements
6. Update this guide if you discover new patterns
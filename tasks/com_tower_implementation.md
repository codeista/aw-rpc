# COM_TOWER Damage Bonus Implementation Plan

## Overview
Implement the COM_TOWER damage bonus mechanic where each COM_TOWER owned by an army provides +10% attack power to all units of that army.

## Game Mechanics
- Each COM_TOWER owned provides +10% attack bonus
- Bonus is cumulative (2 towers = +20%, 3 towers = +30%, etc.)
- Maximum bonus in standard AW is typically +40% (4 towers)
- Bonus applies to ALL units of the owning army
- COM_TOWERs start as neutral and must be captured

## Implementation Steps

### 1. Add COM_TOWER Counting Method
Create a method in `manager.py` to count COM_TOWERs owned by each army:
```python
def count_com_towers(self, army: Army) -> int:
    """Count number of COM_TOWERs owned by specified army"""
    count = 0
    for row in self.board.grid:
        for tile in row:
            if tile.mapTile.type == MapType.COM_TOWER and tile.mapTile.army == army:
                count += 1
    return count
```

### 2. Modify Damage Calculation
Update `enhanced_attack_damage` in `unit.py` to include COM_TOWER bonus:
```python
# AV: Attacker's attack value (default 100, modified by COs and COM_TOWERs)
attack_value = UNIT_ATTACK_VALUES.get(self.type, 100)

# Add COM_TOWER bonus (+10% per tower)
if hasattr(self, 'board_manager') and self.board_manager:
    com_towers = self.board_manager.count_com_towers(self.army)
    com_tower_bonus = com_towers * 10  # +10% per tower
    attack_value = attack_value * (100 + com_tower_bonus) / 100
```

### 3. Update Combat Preview
Modify `get_damage_preview` in `manager.py` to pass board manager reference:
- Ensure units have access to board manager for COM_TOWER counting
- Update preview calculations to show boosted damage

### 4. UI Updates
Update `game_v2_simple.js` to display COM_TOWER bonus:
- Show tower count in UI
- Indicate when damage is boosted
- Update combat preview tooltip

### 5. Testing
Create comprehensive tests:
- Unit test for COM_TOWER counting
- Combat test with 0, 1, 2, 3, 4 towers
- Capture/loss of COM_TOWER updates bonus
- Regression test for all armies

## File Changes Required

1. **manager.py**
   - Add `count_com_towers()` method
   - Pass board manager reference to units

2. **unit.py**
   - Modify `enhanced_attack_damage()` to include COM_TOWER bonus
   - Add board_manager reference handling

3. **combat_system.py**
   - Ensure board manager is available during combat

4. **app.py**
   - Update combat_preview RPC to include COM_TOWER info

5. **game_v2_simple.js**
   - Display COM_TOWER count for each army
   - Show bonus in combat preview

6. **tests/**
   - New test file: `test_com_tower_bonus.py`
   - Update regression tests

## Expected Behavior

### Example Scenario:
- RED owns 2 COM_TOWERs (+20% attack)
- RED TANK (base 55 damage vs INFANTRY)
- With bonus: 55 * 1.20 = 66 damage

### Edge Cases:
- Neutral COM_TOWERs provide no bonus
- Capturing enemy COM_TOWER immediately transfers bonus
- Maximum practical bonus is +40% (4 towers)

## Success Criteria
1. COM_TOWER bonus correctly applies to all unit attacks
2. Bonus updates immediately when towers are captured/lost
3. Combat preview shows accurate damage with bonus
4. All tests pass
5. No performance degradation
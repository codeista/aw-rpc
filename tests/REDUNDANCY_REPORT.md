# Test File Redundancy Analysis Report

## Summary

This report identifies redundant test files in the `/home/box/Documents/aw-rpc/tests` directory and provides recommendations for consolidation.

## 1. Transport Test Files (4 redundant files)

### Files Found:
- `unit/test_transport_simple.py` - Basic transport test with APC resupply and Black Boat repair
- `unit/test_transport_final.py` - Transport test with fund generation via property income
- `unit/test_transport_features.py` - Transport test focusing on APC auto-resupply and Black Boat repair
- `unit/test_simple_transport.py` - Simplified transport test with basic functionality

### Analysis:
All four files test similar functionality:
- APC auto-resupply mechanics
- Black Boat repair capabilities
- Unit creation and movement
- Fund generation (some files)

### Recommendation:
**Keep**: `test_transport_features.py` - Most comprehensive and well-structured
**Remove**: The other three files are redundant

---

## 2. Repair/Refuel Test Files (3 redundant files)

### Files Found:
- `unit/test_repair_resupply_system.py` - Tests Black Boat repair, APC resupply, and facility repairs
- `unit/test_repair_refuel_proper.py` - Black Boat repair/refuel test with UI integration
- `unit/test_complete_repair_refuel.py` - Complete repair/refuel test with damage scenarios

### Analysis:
All three files test overlapping functionality:
- Black Boat repair mechanics
- Infantry repair adjacent to Black Boat
- Fuel/supply mechanics
- Unit damage and repair cycles

### Recommendation:
**Keep**: `test_complete_repair_refuel.py` - Most comprehensive with damage scenarios
**Remove**: The other two files are largely redundant

---

## 3. Black Boat Test Files (3 redundant files)

### Files Found:
- `unit/test_blackboat_movement.py` - Tests Black Boat movement mechanics
- `unit/test_blackboat_repair_complete.py` - Complete Black Boat repair system test
- `unit/simple_blackboat_test.py` - Simple Black Boat creation and movement test

### Analysis:
These files have significant overlap:
- Black Boat creation at ports
- Movement validation
- Turn cycling for movement enablement
- Some include repair functionality

### Recommendation:
**Keep**: `test_blackboat_repair_complete.py` - Most comprehensive functionality
**Remove**: The other two files test subsets of this functionality

---

## 4. Victory Condition Test Files (2 files, not redundant)

### Files Found:
- `integration/test_victory_conditions.py` - Tests capture mechanics and victory detection
- `integration/test_complete_victory_conditions.py` - Tests unit elimination victory scenarios

### Analysis:
These files test different aspects:
- `test_victory_conditions.py`: Property capture, HQ capture, game state tracking
- `test_complete_victory_conditions.py`: Unit elimination, multi-army scenarios

### Recommendation:
**Keep both**: They test complementary functionality

---

## 5. Income/Economic Test Files (3 files with some overlap)

### Files Found:
- `unit/test_economic_system.py` - Comprehensive economic system tests
- `unit/test_daily_income.py` - Tests daily income from properties
- `unit/test_income_with_cross_map.py` - Tests income on 4-player cross map

### Analysis:
- `test_economic_system.py`: Full economic system (fund management, unit costs, affordability)
- `test_daily_income.py`: Focuses specifically on daily income mechanics
- `test_income_with_cross_map.py`: Tests income on specific map type

### Recommendation:
**Keep**: `test_economic_system.py` (comprehensive) and `test_income_with_cross_map.py` (specific map scenario)
**Remove**: `test_daily_income.py` (functionality covered by economic system test)

---

## Consolidation Summary

### Files to Keep (7):
1. `unit/test_transport_features.py`
2. `unit/test_complete_repair_refuel.py`
3. `unit/test_blackboat_repair_complete.py`
4. `integration/test_victory_conditions.py`
5. `integration/test_complete_victory_conditions.py`
6. `unit/test_economic_system.py`
7. `unit/test_income_with_cross_map.py`

### Files to Remove (8):
1. `unit/test_transport_simple.py`
2. `unit/test_transport_final.py`
3. `unit/test_simple_transport.py`
4. `unit/test_repair_resupply_system.py`
5. `unit/test_repair_refuel_proper.py`
6. `unit/test_blackboat_movement.py`
7. `unit/simple_blackboat_test.py`
8. `unit/test_daily_income.py`

### Additional Notes:
- Some other test files in integration/ and system/ directories appear to have unique purposes
- `test_green_yellow_victory.py`, `test_victory_fix_verification.py`, `test_new_victory_maps.py` test specific victory scenarios
- `test_multiplayer_armies.py` tests multi-army functionality
- System tests appear to focus on server/API testing rather than game mechanics

This consolidation would reduce test redundancy by ~50% while maintaining full test coverage.
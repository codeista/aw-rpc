# Test Failure Summary

Based on running the test suite, here are the failing tests grouped by category:

## 1. Unit Tests (11 failures in test_attack_defense_ranges.py)

All tests in `tests/unit/test_attack_defense_ranges.py` are failing due to a missing `player_manager` argument in the GameManager constructor:

- `test_all_indirect_units_cannot_counter`
- `test_artillery_maximum_range`
- `test_artillery_minimum_range`
- `test_attack_after_movement`
- `test_battleship_cannot_counter_at_any_range`
- `test_carrier_missile_range`
- `test_counter_attack_with_reduced_hp`
- `test_direct_unit_ranges`
- `test_direct_units_can_counter`
- `test_missile_anti_air_only`
- `test_no_friendly_fire`

**Root Cause**: `TypeError: GameManager.__init__() missing 1 required positional argument: 'player_manager'`

## 2. Integration Tests (19 failures)

### Complex Scenarios (13 failures in test_complex_scenarios.py)
Most failures are due to missing `unit_load` method:
- `test_transport_chain_loading` - AttributeError: 'GameManager' object has no attribute 'unit_load'
- `test_transport_unload_and_action`
- `test_naval_transport_with_ground_units`
- `test_chain_combat_scenario`
- `test_indirect_combat_with_fog_of_war`
- `test_combat_with_terrain_advantage`
- `test_hq_capture_victory`
- `test_elimination_victory`
- `test_unit_fuel_exhaustion`
- `test_blocked_factory_production`
- `test_invalid_transport_combinations`
- `test_repair_beyond_max_hp`
- `test_simultaneous_capture_attempts`

### Other Integration Test Failures
- `test_unit_deselects_when_no_actions` (test_unit_deselection.py)
- `test_unit_stays_selected_for_capture` (test_unit_deselection.py)
- `test_unit_stays_selected_with_enemy_nearby` (test_unit_deselection.py)
- `test_all_user_interactions_documented` (test_user_interactions_coverage.py) - 500 error on game_create_test
- `test_rpc_methods_coverage` (test_user_interactions_coverage.py) - 500 error on game_create_test
- `test_army_turn_cycle` (test_multiplayer_armies.py)

## 3. System Tests (2 failures)

- `test_movement_fuel_consumption` (test_unittest.py) - Fuel not being consumed on movement (99 == 99)
- `test_fuel_consumption_mechanics` (test_unittest.py) - Similar fuel consumption issue

## 4. Transport Unit Tests (3 errors)

- `test_apc_auto_resupply` (test_transport_features.py)
- `test_cruiser_carrier_resupply` (test_transport_features.py)
- `test_blackboat_repair` (test_transport_features.py)

## Summary

**Total Failing Tests**: ~35 tests across different categories

**Main Issues**:
1. Missing `player_manager` parameter in GameManager initialization
2. Missing `unit_load` method in GameManager
3. Fuel consumption not working correctly
4. game_create_test endpoint returning 500 errors

**Note**: The regression tests (test_complete_with_recent.py) are passing, which suggests the core game mechanics through the RPC interface are working, but the unit/integration tests that directly instantiate GameManager objects are failing due to API changes.
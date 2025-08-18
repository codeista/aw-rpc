# Facility Repair Mechanics Implementation

## Task Overview
Implement automatic facility repair mechanics at turn start - airports repair air units, factories repair land units, ports repair naval units.

## Requirements
1. Repair happens at turn start automatically
2. Repair up to 2 HP per turn max
3. Cost is 10% of unit value per HP repaired
4. Only repair units on matching facility types

## Implementation Plan

### Todo Items

- [ ] 1. Analyze current turn start effects in `_apply_turn_start_effects`
- [ ] 2. Add facility repair logic after existing auto-resupply
- [ ] 3. Map unit classes to facility types (AIR->AIRPORT, SEA/LANDER->PORT, others->FACTORY)
- [ ] 4. Calculate repair costs (10% of unit cost per HP)
- [ ] 5. Implement repair logic with HP cap of 2 per turn
- [ ] 6. Deduct repair costs from player funds
- [ ] 7. Add logging for repair actions
- [ ] 8. Create/update tests for facility repair functionality
- [ ] 9. Test integration with existing turn mechanics

### Technical Details

#### Facility-Unit Mapping:
- **AIRPORT**: Repairs AIR units (FIGHTER, BOMBER, STEALTH, BCOPTER, TCOPTER, BLACKBOMB)
- **PORT**: Repairs SEA and LANDER units (BATTLESHIP, CRUISER, SUB, CARRIER, BLACKBOAT, LANDER)  
- **FACTORY**: Repairs land units (all others - INFANTRY, MECH, RECON, TANK, etc.)

#### Current Turn Start Flow:
1. Auto-resupply from APCs and bases (fuel/ammo)
2. Fuel consumption for air/naval units
3. Income distribution

#### Proposed Addition:
4. **Facility repair** (NEW) - after resupply, before fuel consumption

#### Cost Calculation:
- Base cost = UNIT_COSTS[unit_type] * 0.1 per HP
- Max 2 HP repaired per turn
- Deduct from player funds

### Files to Modify:
- `manager.py` - Add repair logic to `_apply_turn_start_effects`
- Create tests in `tests/unit/test_facility_repair.py`

### Integration Points:
- Uses existing `ProductionSystem.UNIT_COSTS` for cost calculation
- Uses existing `_update_player_funds` for cost deduction
- Follows existing resupply pattern in `_apply_auto_resupply`

## Review Section
*Will be filled in as tasks are completed*
# Repair & Refuel Test Guide

## Overview

The `test_repair_refuel_proper.py` test suite provides comprehensive testing of Black Boat repair and APC auto-resupply functionality. This test validates both the RPC endpoints and the actual game mechanics.

## Test Coverage

### 🔧 Repair Testing
- **Black Boat Creation**: Creates Black Boat at port position
- **RPC Validation**: Tests repair_unit endpoint with various validation scenarios
- **Repair Functionality**: Tests actual HP repair with proper cost calculation (up to 2 HP per action, max 10 HP total)
- **UI Integration**: Verifies game board state and unit positioning

### ⛽ Refuel Testing  
- **APC Auto-Resupply**: Tests APC automatic refuel of adjacent units at turn start
- **Fuel Level Monitoring**: Checks fuel before and after resupply operations
- **Unit Compatibility**: Validates APC resupplies ALL unit types (Infantry, Tanks, etc.)
- **Turn Management**: Ensures auto-resupply triggers correctly during turn cycling

## Running the Tests

### Command Line
```bash
python3 test_repair_refuel_proper.py
```

### Web Interface
1. Visit `http://localhost:5000/test_interface`
2. Click the "🔧 Repair & Refuel" button
3. Monitor real-time test results

### Manual Testing
After automated tests complete, visit the generated game URL for manual validation:
- Test Black Boat right-click repair context menu
- Verify APC auto-resupply by ending turns
- Check fuel levels in unit information panels

## Test Scenarios

### Repair Test Scenario
1. **Setup Phase**
   - Creates Black Boat at port (0,0)
   - Creates Infantry adjacent at (1,0)
   - Creates enemy unit to damage Infantry
   
2. **Validation Phase**
   - Tests invalid coordinates
   - Tests non-existent units
   - Tests invalid game tokens
   
3. **Functionality Phase**
   - Attempts repair via RPC
   - Validates cost calculation
   - Confirms HP restoration

### Refuel Test Scenario
1. **Setup Phase**
   - Creates APC at factory (0,4)
   - Creates Infantry adjacent at (1,4)
   - Establishes proper positioning
   
2. **Consumption Phase**
   - Units move to consume fuel
   - Records initial fuel levels
   
3. **Resupply Phase**
   - Triggers turn end to activate auto-resupply
   - Measures fuel levels after resupply
   - Validates fuel restoration

## Expected Results

### Success Indicators
- ✅ **RPC Validation**: All endpoint validations pass
- ✅ **Repair Functionality**: Repair system works correctly
- ✅ **Refuel Functionality**: Auto-resupply activates properly  
- ✅ **UI Integration**: Game board loads and displays correctly

### Common Issues
- **Turn Management**: "Not your turn" errors indicate turn state problems
- **Unit Creation**: Insufficient funds or invalid positions
- **Board Loading**: Empty tiles array suggests game state issues

## Game Mechanics Validated

### Black Boat Repair
- Only repairs units of same team
- Maximum 2 HP repair per action
- Costs 10% of unit value per HP
- Requires adjacency to target unit
- Only works on Black Boat's turn

### APC Auto-Resupply  
- Triggers automatically at turn start
- Affects ALL adjacent friendly units
- Restores fuel to maximum capacity
- Works with any unit type (Infantry, Tanks, Aircraft, etc.)
- No cost for auto-resupply

## Integration Points

### RPC Endpoints Tested
- `repair_unit`: Manual Black Boat repair
- `game_create_test`: High-funds test game creation
- `unit_create`: Unit placement and validation
- `army_end_turn`: Turn management and auto-resupply triggers
- `game_board`: Board state verification

### UI Components Tested
- Context menu display for repair actions
- Unit selection and highlighting
- Game board rendering and updates
- Real-time game state synchronization

## Maintenance Notes

### Updating Tests
- Modify unit positions in `setup_repair_scenario()` 
- Adjust fuel consumption patterns for different unit types
- Update validation scenarios for new RPC endpoints

### Adding New Scenarios
- Follow existing pattern: setup → validation → functionality
- Use `game_create_test` for sufficient starting funds
- Always include both automated and manual testing instructions

## Related Documentation

- `README.md`: Overall test suite information
- `GAME_MECHANICS.md`: Core game rule testing scenarios
- `templates/test_interface.html`: Web interface integration
- `app.py`: RPC endpoint implementations
- `manager.py`: Core game logic for repair/refuel systems

## Troubleshooting

### Test Failures
1. **Server Connection**: Ensure Flask server running on localhost:5000
2. **Turn State**: Check army_end_turn calls for proper turn management  
3. **Unit Positioning**: Verify coordinates are valid for the test map
4. **Funds**: Use game_create_test for sufficient starting funds

### Manual Verification
If automated tests fail, use the generated game URL to manually verify:
- Units are created in expected positions
- Right-click context menus appear correctly
- Repair actions work via UI
- Auto-resupply triggers on turn end
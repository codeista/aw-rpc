# Advance Wars RPC - Testing Documentation

## Test Suite Overview

The Advance Wars RPC game has a comprehensive test suite covering unit tests, integration tests, and regression tests.

### Test Structure

```
tests/
├── unit/           # Individual component tests
├── integration/    # System interaction tests
├── regression/     # Full game mechanics validation
├── system/         # Complete system tests
├── ui/            # Selenium-based UI tests
└── debug/         # Test utilities and helpers
```

## Running Tests

### Quick Start

```bash
# Activate virtual environment first
source flask-env/bin/activate

# Run all tests
python3 run_tests.py

# Run regression tests only
python3 run_regression_tests.py

# Run specific test file
python3 tests/unit/test_combat_system.py
python3 tests/unit/test_combat_system_fixed.py

# Run integration tests
python3 tests/integration/test_unit_deselection.py

# Run click handler tests (in root directory)
python3 test_click_handling.py

# Access web-based test interface
# Start server first, then navigate to:
# http://localhost:5000/test_interface
```

### Prerequisites

1. **Activate the virtual environment:**
```bash
source flask-env/bin/activate
```

2. **Start the game server:**
```bash
# Must be in flask-env to have all dependencies
nohup python3 app.py > server.log 2>&1 &
```

3. **Verify server is running:**
```bash
curl http://localhost:5000
```

**Note:** The flask-env virtual environment contains all required dependencies including Flask, flask-cors, and other packages. Always activate it before running the app or tests.

## Test Results Summary (Last Updated: 2025-07-24)

### ✅ Passing Tests

**Unit Tests (11/12 passing):**
- `test_combat_system.py` - All combat mechanics
- `test_combat_system_fixed.py` - Fixed combat test with win condition check
- `test_movement_system.py` - Unit movement validation
- `test_transport_features.py` - Transport load/unload/resupply
- `test_economic_system.py` - Income and funds management
- `test_income_with_cross_map.py` - Multi-army income
- `test_ui_mobile_features.py` - UI endpoints and mobile support
- `test_blackboat_repair_complete.py` - Black boat repair feature
- `test_complete_repair_refuel.py` - Repair/refuel systems
- `test_victory_conditions.py` - All victory conditions

**Integration Tests:**
- `test_multiplayer_armies.py` - 4-player army support
- `test_game_improvements.py` - Game creation methods
- `test_unit_deselection.py` - Unit auto-deselection behavior
- `test_complete_victory_conditions.py` - 3/4 victory scenarios

**Regression Tests:**
- All 28 core game mechanics tests passing
- 100% success rate on established functionality

**UI/Frontend Tests:**
- `test_click_handling.py` - Priority-based click processing (in root directory)
- Interactive browser-based test suite
- Test runner interface at `/test_interface`

### ❌ Known Issues

1. **test_production_system.py** (1/6 tests pass)
   - Production options API needs update
   - Unit creation validation too strict

2. **test_complex_scenarios.py**
   - HQ tile naming issue (looking for "HQ" instead of BASE_TOWER_*)
   - Some unit creation conflicts on occupied tiles

3. **test_core_integration.py**
   - API compatibility issues with newer test format
   - Import path problems

## Important Test Notes

### HQ Tiles
- HQ tiles are named `BASE_TOWER_0` through `BASE_TOWER_4`, not "HQ"
- Use `tile.mapTile.is_hq()` method to check for HQ tiles
- Each army color has its own BASE_TOWER variant

### Test Game Creation
```javascript
// Regular game (5000 starting funds)
rpc('game_create', {token: 'mygame'})

// Test game (50000 starting funds) - use for expensive units
rpc('game_create_test', {token: 'testgame'})
```

### Common Test Patterns

1. **Enable Unit Movement**
```python
# Units cannot move on creation turn
self.manager.end_turn()  # End turn to enable movement
```

2. **Check Unit at Position**
```python
tile = self.manager.tile_at(x, y)
if tile.unit:
    print(f"Unit: {tile.unit.type.name}")
```

3. **Verify Transport Loading**
```python
# Move unit INTO transport (not picked up)
self.manager.unit_move(unit_x, unit_y, transport_x, transport_y)
```

## Click Handler Testing

The centralized click handler system has comprehensive tests covering all interaction types:

### Browser-Based Tests
- Run via the "🧪 Test Clicks" button in the game UI
- Or access `test_runner.html` for dedicated test interface
- Tests run in actual browser environment with mocked game state

### Test Coverage
1. **Handler Initialization** - Verifies click handler is properly loaded
2. **Empty Tile Clicks** - Clears selection when clicking empty tiles
3. **Unit Selection** - Selects units and shows movement/attack options
4. **Movement Execution** - Handles movement to valid tiles
5. **Production Buildings** - Opens production modal for factories/airports/ports
6. **Attack Execution** - Processes attacks on enemy units
7. **Alt-Click Transport** - Special handling for transport operations
8. **Priority System** - Ensures handlers execute in correct order

### Running Click Tests
```bash
# Command line
python3 test_click_handling.py

# In-game
Click "🧪 Test Clicks" button in game UI

# Browser console
const tester = new ClickHandlerTests();
tester.runAllTests();
```

## Test Coverage

- **Combat System**: 100% coverage
- **Movement System**: 100% coverage  
- **Transport System**: 100% coverage
- **Economic System**: 100% coverage
- **Victory Conditions**: 100% coverage
- **Click Handler**: 100% coverage ✨ NEW
- **UI/Frontend**: Enhanced coverage with automated tests

## Manual Testing Checklist

When making changes, manually verify:

- [ ] Units move correctly and fuel is consumed
- [ ] Combat damage calculations match expected values
- [ ] Transports can load/unload units properly
- [ ] Income is distributed correctly at turn start
- [ ] Victory conditions trigger appropriately
- [ ] UI updates reflect game state changes
- [ ] Context menus work for special actions

## Continuous Integration

The test suite is designed to run in CI/CD pipelines:

```bash
# Activate virtual environment
source flask-env/bin/activate

# Start server in background
nohup python3 app.py > server.log 2>&1 &
sleep 5  # Wait for server to start

# Run tests
python3 run_all_tests.py
TEST_RESULT=$?

# Kill server
pkill -f "python3 app.py"

# Exit codes
# 0 = All tests passed
# 1 = Some tests failed
exit $TEST_RESULT
```

## Adding New Tests

1. Create test file in appropriate directory
2. Import test base classes and utilities
3. Follow existing test patterns
4. Add to test runner configuration
5. Document any special setup requirements

Example test structure:
```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from gameboard import GameBoard
from manager import GameManager
# ... other imports

def test_my_feature():
    config = Config()
    board = GameBoard.create(map_name='test_map')
    manager = GameManager(config, board)
    
    # Test implementation
    assert condition, "Error message"
    
    print("✅ My Feature Test PASSED")
```

## Debugging Failed Tests

1. **Ensure flask-env is activated:**
   ```bash
   source flask-env/bin/activate
   which python3  # Should show flask-env path
   ```

2. **Check server logs:**
   ```bash
   tail -f server.log
   ```

3. **Common issues:**
   - Missing dependencies: Install in flask-env
   - Server not running: Check `ps aux | grep app.py`
   - Port conflicts: Ensure port 5000 is free

4. **Debug tips:**
   - Enable debug mode in tests
   - Print intermediate values
   - Verify map has required features (HQs, properties)
   - Check for race conditions in async operations

## Performance Benchmarks

Current test suite performance:
- Unit tests: ~30 seconds
- Integration tests: ~45 seconds  
- Regression tests: ~3 minutes
- Full suite: ~5 minutes

Target: Keep full suite under 10 minutes
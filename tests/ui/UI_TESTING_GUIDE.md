# UI Testing Guide

## Overview

This guide covers the UI testing framework for Advance Wars RPC. The tests use Selenium WebDriver to automate browser interactions and verify the game's visual components work correctly.

## Test Categories

### 1. Movement Highlighting Tests (`test_movement_highlighting.py`)
- Verifies movement highlights appear when units are selected
- Tests highlight clearing on deselection
- Validates movement range calculations
- Checks terrain restrictions on movement
- Tests occupied tile exclusion

### 2. Unit Rendering Tests (`test_unit_rendering.py`)
- Validates correct sprite rendering for all unit types
- Tests unit availability states (idle vs unavailable)
- Verifies HP display functionality
- Tests transport cargo rendering
- Validates multi-army color rendering
- Tests sprite scaling and updates

### 3. Game Interaction Tests (`test_game_interactions.py`)
- Tests unit selection mechanics
- Validates movement execution flow
- Tests attack targeting system
- Verifies property capture interactions
- Tests transport loading mechanics
- Validates turn management

## Running Tests

### Quick Start
```bash
# Run all UI component tests
python tests/ui/run_ui_component_tests.py

# Run specific component tests
python tests/ui/run_ui_component_tests.py movement
python tests/ui/run_ui_component_tests.py rendering
python tests/ui/run_ui_component_tests.py interactions

# Run with verbose output
python tests/ui/run_ui_component_tests.py -v

# List available test suites
python tests/ui/run_ui_component_tests.py --list
```

### Prerequisites
1. Game server must be running on `localhost:5000`
2. Required dependencies: `selenium`, `pytest`, `pytest-html`
3. Chrome browser and ChromeDriver installed

### Using the Main UI Test Runner
```bash
# Run all UI tests (includes component tests)
python tests/ui/run_ui_tests.py

# Run specific test file
python tests/ui/run_ui_tests.py --test test_movement_highlighting.py

# Run tests matching pattern
python tests/ui/run_ui_tests.py --test test_movement_highlights_appear
```

## Test Structure

### Base Test Class (`base_test.py`)
All UI tests inherit from `BaseUITest` which provides:

- **Setup/Teardown**: Browser initialization and cleanup
- **RPC Methods**: Execute game commands via RPC
- **Navigation**: Load games and wait for initialization
- **Interactions**: Click, hover, drag operations on tiles
- **State Queries**: Get units, tiles, highlights, game state
- **Utilities**: Screenshots, JS execution, error checking

### Key Helper Methods

```python
# Create a test game
game_id = self.create_test_game(funds=50000)

# Navigate to game
self.navigate_to_game(game_id)

# Click on tiles
self.click_tile(x, y)
self.double_click_tile(x, y)
self.right_click_tile(x, y)

# Get game state
unit = self.get_unit_at(x, y)
tile = self.get_tile_at(x, y)
selected = self.get_selected_unit()

# Wait for highlights
highlights = self.wait_for_movement_highlights()
attack_highlights = self.wait_for_attack_highlights()

# Execute RPC commands
self.execute_rpc('unit_create', {'army': 'RED', 'unit_type': 'TANK', 'x': 5, 'y': 5})

# Take screenshots
self.take_screenshot("test_state")
```

## Writing New Tests

### Test Template
```python
from .base_test import BaseUITest

class TestNewFeature(BaseUITest):
    def test_feature_behavior(self):
        """Test description"""
        # Setup
        game_id = self.create_test_game()
        self.navigate_to_game(game_id)
        
        # Create test scenario
        self.execute_rpc('unit_create', {...})
        
        # Perform actions
        self.click_tile(x, y)
        
        # Verify results
        assert condition, "Error message"
        
        # Visual verification
        self.take_screenshot("feature_state")
```

### Best Practices

1. **Test Independence**: Each test should create its own game state
2. **Clear Assertions**: Use descriptive assertion messages
3. **Visual Verification**: Take screenshots at key points
4. **Wait for Updates**: Use appropriate delays for UI updates
5. **Clean State**: Don't rely on previous test state

## Debugging Tests

### Screenshots
- Automatically saved to `tests/ui/screenshots/`
- Named with test name and timestamp
- Taken on test failure automatically

### JavaScript Errors
- Console errors are checked after each test
- Use `self.check_js_errors()` to verify no JS errors

### Interactive Debugging
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use pytest debugging
pytest tests/ui/test_file.py -s --pdb
```

## Test Reports

HTML reports are generated in `tests/ui/reports/` containing:
- Test results summary
- Detailed failure information
- Test duration metrics
- Screenshots on failure

## Continuous Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run UI Tests
  run: |
    python app.py &  # Start server
    sleep 5
    python tests/ui/run_ui_component_tests.py
```

## Troubleshooting

### Common Issues

1. **Server Not Running**
   ```bash
   source flask-env/bin/activate
   python app.py
   ```

2. **ChromeDriver Issues**
   - Ensure ChromeDriver matches Chrome version
   - Install: `pip install webdriver-manager`

3. **Timeout Errors**
   - Increase wait times in base_test.py
   - Check server performance

4. **Element Not Found**
   - Verify game loaded with `wait_for_game_load()`
   - Check element IDs haven't changed

## Performance Considerations

- Tests create new games for isolation (slower but reliable)
- Use `--parallel` flag for concurrent execution
- Disable animations with `disable_animations()`
- Reuse game state within test methods when possible
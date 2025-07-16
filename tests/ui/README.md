# UI Testing Suite for Advance Wars RPC

This directory contains comprehensive Selenium-based UI tests for the AW-RPC game, focusing on visual verification of highlighting, movement, and attack mechanics.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r tests/ui/requirements.txt
   ```

2. **Ensure server is running:**
   ```bash
   source flask-env/bin/activate
   python3 app.py
   ```

3. **Run all UI tests:**
   ```bash
   python3 tests/ui/run_ui_tests.py
   ```

## 🧪 Test Suites

### 1. **Highlighting Mechanics** (`test_highlighting_system.py`)
- Movement range highlights appear when selecting units
- Attack range highlights show valid targets
- Transport highlights for loading/unloading
- Highlight persistence and clearing behavior

### 2. **Movement System** (`test_movement_system.py`)
- Units move to clicked highlighted tiles
- Movement animation completion
- Pathfinding around obstacles
- Fuel consumption tracking
- Transport movement with cargo

### 3. **Attack System** (`test_attack_system.py`)
- Direct attacks on adjacent enemies
- Indirect attacks at range
- Damage preview display
- Combat animations
- HP reduction and unit destruction
- Counter-attack mechanics

### 4. **Complex Scenarios** (`test_complex_scenarios.py`)
- Multi-step operations (load → move → unload → attack)
- Property capture over multiple turns
- Coordinated attacks with multiple units
- Edge cases and stress testing

## 📋 Running Specific Tests

### Run a specific test suite:
```bash
python3 tests/ui/run_ui_tests.py --suite highlighting
python3 tests/ui/run_ui_tests.py --suite movement
python3 tests/ui/run_ui_tests.py --suite attack
python3 tests/ui/run_ui_tests.py --suite complex
```

### Run a specific test:
```bash
python3 tests/ui/run_ui_tests.py --test test_movement_highlights_appear
```

### List all available tests:
```bash
python3 tests/ui/run_ui_tests.py --list
```

### Run tests in parallel:
```bash
python3 tests/ui/run_ui_tests.py --parallel
```

## 🔧 Test Infrastructure

### Base Test Class (`test_base_selenium.py`)
- WebDriver setup and teardown
- Canvas click coordinate calculations
- Game state extraction via JavaScript
- Screenshot capture utilities
- Common helper methods

### Helper Utilities (`selenium_helpers.py`)
- **ColorDetector**: Detect highlight colors in screenshots
- **CoordinateHelper**: Convert between tile and canvas coordinates
- **GameStateValidator**: Validate game state changes
- **VisualDebugger**: Create debug images and comparisons
- **TestDataHelper**: Set up specific test scenarios

## 📸 Visual Verification

The tests use image analysis to verify visual elements:

1. **Highlight Detection**: Uses color ranges to detect yellow movement highlights, red attack highlights, etc.
2. **Screenshot Comparison**: Before/after screenshots to verify state changes
3. **Animation Capture**: Frame capture during animations

Screenshots are saved to `tests/ui/screenshots/` for debugging.

## 📊 Test Reports

HTML test reports are generated in `tests/ui/reports/` with:
- Test execution summary
- Pass/fail status for each test
- Failure screenshots
- Execution time metrics

## 🔍 Debugging Failed Tests

1. **Check screenshots**: Look in `tests/ui/screenshots/` for failure captures
2. **Run specific test**: Use `--test` flag to run individual failing test
3. **Enable verbose mode**: Add `-v` flag for detailed output
4. **Check browser console**: Tests verify no JavaScript errors occurred

## ⚙️ Configuration

### Browser Options
Tests run in Chrome by default. To run headless:
```python
# In test_base_selenium.py, uncomment:
options.add_argument('--headless')
```

### Timeouts
Adjust timeouts in `BaseSeleniumTest`:
- `WAIT_TIMEOUT`: WebDriver wait timeout (default: 10s)
- Animation waits: Adjust `wait_for_animation()` calls

### Test Game Setup
Tests use `game_create_test` with optimized map for consistent scenarios.

## 🎯 Test Coverage

### Visual Elements Tested:
- ✅ Movement highlight appearance and clearing
- ✅ Attack highlight range validation
- ✅ Transport loading/unloading indicators
- ✅ Unit movement animations
- ✅ Combat damage feedback
- ✅ Multi-turn operations

### Interactions Tested:
- ✅ Click, double-click, right-click
- ✅ Ctrl+Click for loading
- ✅ Alt+Click for unloading
- ✅ Keyboard shortcuts
- ✅ Rapid clicking handling
- ✅ Browser zoom levels

## 🚦 Continuous Integration

To run in CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Start game server
  run: |
    source flask-env/bin/activate
    nohup python3 app.py &
    sleep 5

- name: Run UI tests
  run: |
    python3 tests/ui/run_ui_tests.py --parallel
```

## 📝 Adding New Tests

1. Create test class inheriting from `BaseSeleniumTest`
2. Use helper methods for common operations
3. Capture screenshots at key points
4. Verify both visual and state changes
5. Handle test data setup and teardown

Example:
```python
class TestNewFeature(BaseSeleniumTest):
    def test_feature_behavior(self):
        # Setup
        units = self.get_unit_positions('RED')
        
        # Action
        self.click_tile(units[0]['x'], units[0]['y'])
        
        # Verify
        assert self.wait_for_highlights('movement')
        
        # Screenshot
        self.take_screenshot('feature_test')
```

## 🐛 Known Issues

- Chrome WebDriver must be installed and in PATH
- Tests require display (use Xvfb for headless servers)
- Some animations may need timing adjustments
- Color detection ranges may need tuning for different monitors

## 🤝 Contributing

When adding new UI tests:
1. Follow existing test patterns
2. Add visual verification where possible
3. Include edge cases
4. Document expected behavior
5. Ensure tests are reliable and not flaky
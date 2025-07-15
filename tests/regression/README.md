# Automated Regression Test Suite

## Overview
Comprehensive automated test suite that validates all core game mechanics using RPC API calls to ensure nothing breaks as the codebase evolves.

## Quick Start
```bash
# Run from project root
python3 run_regression_tests.py

# Or use integrated test runner
python3 tests/run_tests.py
# Choose option 3: Automated Regression Tests
```

## Test Coverage

### 🎮 Game Management (4 tests)
- ✅ Game creation with optimized test map
- ✅ Game board access and validation
- ✅ Game active status verification
- ✅ Turn checking functionality

### 🪖 Unit Operations (4 tests)
- ✅ Unit creation at production facilities
- ✅ Unit selection and state management
- ✅ Unit movement with turn cycling
- ✅ Movement validation and range checking

### ⚔️ Combat System (3 tests)
- ✅ Combat damage preview calculations
- ✅ Attack target identification
- ✅ Damage chart access and validation

### 🚢 Transport System (6 tests)
- ✅ APC transport creation
- ✅ Infantry cargo unit creation
- ✅ Unit loading into transports
- ✅ Transport information retrieval
- ✅ Valid unload position calculation
- ✅ Unit unloading from transports

### 🏰 Capture Mechanics (5 tests)
- ✅ Infantry creation for property capture
- ✅ Movement to capturable properties
- ✅ Tile information validation
- ✅ Capture attempt execution
- ✅ Capture system functionality verification

### 💰 Economic System (4 tests)
- ✅ Army economy information retrieval
- ✅ Unit cost data access
- ✅ Unit affordability checking
- ✅ Production options validation

### 🛠️ Special Actions (2 tests)
- ✅ Black Boat unit creation
- ✅ Troop configuration information access

## Test Results
- **Total Tests**: 28 individual validations
- **Success Rate**: 100.0%
- **Execution Time**: ~3 minutes
- **Coverage**: All core game mechanics

## Implementation Details

### Test Strategy
- **RPC-based testing**: Uses actual API endpoints rather than internal methods
- **Follows AW rules**: Respects turn cycling, unit movement restrictions, etc.
- **Robust error handling**: Graceful failure with detailed error reporting
- **Self-contained**: Creates and cleans up test games automatically

### Test Patterns Used
```python
# Standard pattern for unit operations
1. Create unit at production facility
2. End turns to enable movement (AW rule: new units can't move)
3. Execute operation (move, attack, capture, etc.)
4. Validate results using RPC calls
```

### Error Handling
- **Server availability check**: 30-second timeout before starting tests
- **RPC call validation**: Detailed error reporting for failed API calls
- **Expected key validation**: Ensures response contains required data
- **Exception handling**: Graceful handling of test crashes

## Files

### Main Test Suite
- `/tests/regression/test_complete_game_mechanics.py` - Main test implementation
- `/run_regression_tests.py` - Standalone test runner
- `/tests/run_tests.py` - Integrated test runner (option 3)

### Supporting Files
- `/tests/regression/README.md` - This documentation
- `/API_REFERENCE.md` - Complete RPC API documentation

## Benefits

1. **Prevents Regressions**: Automatically catches when code changes break existing functionality
2. **Fast Feedback**: Complete validation in under 3 minutes
3. **CI/CD Ready**: Returns proper exit codes (0=success, 1=failure)
4. **Developer Friendly**: Clear success/failure reporting with specific error messages
5. **Comprehensive Coverage**: Tests all major game mechanics end-to-end

## Usage Examples

### Command Line
```bash
# Basic execution
python3 run_regression_tests.py

# Check exit code
python3 run_regression_tests.py && echo "All tests passed" || echo "Tests failed"
```

### CI/CD Integration
```yaml
# Example GitHub Actions step
- name: Run Regression Tests
  run: |
    python3 app.py &
    sleep 10  # Wait for server startup
    python3 run_regression_tests.py
```

### Development Workflow
1. Make code changes
2. Run regression tests: `python3 run_regression_tests.py`
3. If tests fail, fix issues before committing
4. If tests pass, changes are safe to deploy

## Maintenance

### Adding New Tests
1. Add test method to appropriate category in `test_complete_game_mechanics.py`
2. Follow existing patterns for RPC calls and validation
3. Update this README with new test count

### Updating for New Features
1. Add new test category if needed
2. Implement tests for new RPC methods
3. Ensure tests follow established patterns

### Troubleshooting
- **Server not running**: Tests will detect and report this automatically
- **Tests timing out**: Check server performance and adjust timeout if needed
- **API changes**: Update test RPC calls to match new API signatures

This regression test suite ensures the Advance Wars RPC game engine continues working correctly as the codebase evolves, providing confidence for future development.
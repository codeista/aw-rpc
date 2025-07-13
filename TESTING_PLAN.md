# Testing Plan for Modular AW-RPC

## Phase 0 & 1 Testing (Modular Structure)

### 1. Syntax Validation ✓ (Can do now)
```bash
# Test all route files compile correctly
python3 -m py_compile routes/*.py
python3 -m py_compile app_modular.py
python3 -m py_compile tests/unit/*.py
python3 -m py_compile tests/integration/*.py
python3 -m py_compile tests/system/*.py
```

### 2. Import Testing (Need virtual env)
```bash
# Activate environment
. flask-env/bin/activate

# Test modular app imports
python3 -c "import app_modular; print('Modular app imports OK')"

# Test route imports
python3 -c "from routes import game_bp, admin_bp, test_bp; print('All blueprints OK')"
```

### 3. Functional Testing (Need virtual env)
```bash
# Start modular server
python3 app_modular.py

# Test endpoints:
# - http://localhost:5000/ (game creation)
# - http://localhost:5000/debug (admin functions)  
# - http://localhost:5000/logs (log viewer)
# - http://localhost:5000/test (test games)
```

### 4. RPC Method Testing (Need virtual env)
```bash
# Run organized tests
python3 tests/run_tests.py

# Run specific test categories
python3 -m pytest tests/unit/
python3 -m pytest tests/integration/  
python3 -m pytest tests/system/
```

## Comparison Testing

### Before vs After Comparison
```bash
# Original app
python3 app.py

# Modular app  
python3 app_modular.py

# Both should:
# - Start on port 5000
# - Serve same functionality
# - Have same RPC methods
# - Pass same tests
```

## What to Test

### ✅ Route Organization
- [ ] All HTTP routes work (/, /debug, /logs, /test*)
- [ ] All RPC methods registered (game_board, unit_move, etc.)
- [ ] No duplicate method errors
- [ ] Blueprint registration successful

### ✅ Game Functionality  
- [ ] Game creation works
- [ ] Unit movement works
- [ ] Combat system works
- [ ] Transport system works
- [ ] Turn ending works
- [ ] Victory conditions work

### ✅ Test Organization
- [ ] All tests in tests/ directory
- [ ] Tests run from new locations
- [ ] Test runner works (tests/run_tests.py)
- [ ] No missing test files

## Recommendation

**Do testing now:** We should validate syntax and basic structure
**Do full testing after:** Once you confirm the modular app starts correctly in your virtual env

The modular structure is a major refactor (4363 → 400 lines), so testing is crucial before proceeding to Phase 2 (UI improvements).
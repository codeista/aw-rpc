# QA Test Suite Improvement Plan

## Executive Summary
Critical bugs escaped QA due to:
1. **No persistence testing** - Games disappearing after server restart
2. **No lifecycle testing** - Unit states not resetting properly  
3. **Disabled critical tests** - Data serialization test skipped
4. **Test redundancy** - 8 duplicate test files diluting coverage
5. **Silent failures** - getattr() defaults masking missing fields

## Critical Gaps to Address

### 1. Server Lifecycle Testing (HIGHEST PRIORITY)
**Current Gap**: No tests verify game state survives server restart
**Impact**: Games disappear when server reloads
**Solution**: Create `test_server_persistence.py`
```python
def test_game_persistence_across_restart():
    # Create game and add units
    # Stop server
    # Start server
    # Load game and verify state intact
```

### 2. Turn State Management Testing
**Current Gap**: Turn reset only tested in isolation, not full cycles
**Impact**: Units stuck as "done" after turn cycles
**Solution**: Add to regression tests
```python
def test_unit_state_through_multiple_turns():
    # Create unit (should be done)
    # Cycle through all players twice
    # Verify unit can act again
```

### 3. Fix Disabled Tests
**Current Gap**: `test_data_serialization` skipped due to "Serialization issue"
**Impact**: JSON parsing errors not caught
**Solution**: Fix the underlying serialization issue and re-enable test

### 4. Consolidate Redundant Tests
**Current Gap**: 8 redundant test files (see REDUNDANCY_REPORT.md)
**Impact**: Maintenance overhead, gaps between test boundaries
**Solution**: 
- Keep 7 comprehensive files
- Remove 8 redundant files
- Ensure no coverage gaps during consolidation

### 5. Add Field Validation Tests
**Current Gap**: Missing fields silently defaulted by getattr()
**Impact**: Missing `action_taken` field not detected
**Solution**: Create strict field validation tests
```python
def test_unit_status_fields():
    # Create unit
    # Verify ALL expected fields exist
    # No getattr defaults allowed
```

## Implementation Priority

### Phase 1: Critical Fixes (Immediate)
1. ✅ Already fixed: Added `action_taken` field to UnitStatus
2. ✅ Already fixed: Database persistence for new games
3. ⏳ Create server persistence test
4. ⏳ Fix disabled serialization test

### Phase 2: Coverage Expansion (This Week)
1. Add multi-turn state tests
2. Add field validation tests
3. Add error propagation tests
4. Test all error conditions explicitly

### Phase 3: Test Consolidation (Next Week)
1. Remove 8 redundant test files
2. Merge overlapping coverage
3. Create test coverage report
4. Document test requirements

## New Test Categories Needed

### 1. Persistence Tests (`test_persistence.py`)
- Game survives server restart
- Unit states persist correctly
- Player funds persist
- Capture progress persists

### 2. Lifecycle Tests (`test_lifecycle.py`)
- Multi-turn state management
- Long game sessions
- Memory cleanup
- State transitions

### 3. Field Validation Tests (`test_field_validation.py`)
- All dataclass fields present
- No silent defaults
- Type checking
- Required vs optional fields

### 4. Error Handling Tests (`test_error_handling.py`)
- Invalid RPC parameters
- Out of bounds coordinates
- Insufficient funds
- Invalid game states

## Testing Best Practices

### 1. No Silent Failures
```python
# BAD - Silent default
hp = getattr(unit, 'hp', 100)

# GOOD - Explicit check
if not hasattr(unit, 'hp'):
    raise ValueError("Unit missing hp field")
```

### 2. Test Full Lifecycles
```python
# BAD - Single operation
create_unit()
assert unit.done

# GOOD - Full lifecycle
create_unit()
assert unit.done
cycle_turns()
assert not unit.done
move_unit()
assert unit.done
```

### 3. Test Persistence
```python
# BAD - In-memory only
game = create_game()
assert game.exists()

# GOOD - With persistence
game = create_game()
restart_server()
game = load_game()
assert game.exists()
```

## Success Metrics

1. **Zero silent failures** - All errors explicitly caught
2. **100% field coverage** - Every dataclass field tested
3. **Full lifecycle testing** - Creation → Usage → Persistence → Reload
4. **No redundant tests** - Single source of truth for each feature
5. **Server restart safe** - All games persist across restarts

## Estimated Timeline

- **Week 1**: Fix critical gaps (persistence, turn state)
- **Week 2**: Add new test categories
- **Week 3**: Consolidate redundant tests
- **Week 4**: Full regression validation

## Expected Outcomes

After implementing this plan:
- No games lost on server restart
- No units stuck in wrong state
- All field errors caught immediately
- 50% reduction in test files
- 100% increase in effective coverage
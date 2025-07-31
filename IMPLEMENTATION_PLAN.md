# Implementation Plan - Fix Missing Methods and Test Framework

## Overview
The V2 refactoring split functionality across multiple systems but left many methods unimplemented. The test framework has been masking these failures by only checking JSON-RPC format, not actual functionality.

## Root Causes
1. **Incomplete V2 Migration**: Methods were removed from manager but not reimplemented
2. **Flawed Test Design**: Tests check for RPC format success, not actual method execution
3. **Silent Error Handling**: Exceptions are caught and returned as "successful" RPC responses
4. **Separation Without Integration**: Systems were separated but not properly integrated

## Phase 1: Fix Critical Game Methods (HIGH PRIORITY)

### 1.1 Capture System
```python
# Add to manager_v2.py
def capture_tile(self, x: int, y: int) -> None:
    """Capture a property with infantry/mech unit"""
    # Implementation needed

def capture_tile_enhanced(self, x: int, y: int) -> Dict:
    """Enhanced capture with preview and validation"""
    # Implementation needed

def get_capture_preview(self, x: int, y: int) -> Dict:
    """Preview capture progress"""
    # Implementation needed
```

### 1.2 Victory Conditions
```python
# Add to manager_v2.py
def check_win_condition(self) -> Optional[Dict]:
    """Check if game has been won"""
    # Check HQ capture
    # Check unit elimination
    # Check turn limit
    # Implementation needed
```

### 1.3 Movement System
```python
# Add to manager_v2.py
def get_movement_preview(self, x: int, y: int, x2: int, y2: int) -> Dict:
    """Preview movement path and fuel cost"""
    # Implementation needed

def unit_can_move_to(self, unit: Unit, x: int, y: int) -> bool:
    """Check if unit can reach destination"""
    # Implementation needed
```

## Phase 2: Fix System Integration

### 2.1 Transport System Integration
- Transport methods exist in `transport_system.py` but manager doesn't expose them
- Add wrapper methods in manager_v2.py:

```python
def is_transport_unit(self, unit: Unit) -> bool:
    """Check if unit is a transport"""
    return self.transport_system.is_transport_unit(unit)

def get_transport_capability(self, unit: Unit) -> Optional[Dict]:
    """Get transport capacity info"""
    return self.transport_system.get_transport_capability(unit)

def load_transport_unit(self, transport_x: int, transport_y: int, 
                       cargo_x: int, cargo_y: int) -> Dict:
    """Load unit into transport"""
    # Delegate to transport_system
```

### 2.2 Production System
```python
def produce_unit_at_facility(self, x: int, y: int, unit_type: str) -> Unit:
    """Create unit at production facility"""
    # Validate facility
    # Check funds
    # Create unit
    # Implementation needed
```

## Phase 3: Fix Test Framework

### 3.1 Update assert_success Method
```python
def assert_success(self, result: Dict, test_name: str, expected_keys: List[str] = None) -> bool:
    """Assert that RPC call was successful"""
    # Check for top-level error
    if 'error' in result:
        self.record_test(test_name, False, f"RPC error: {result['error']}")
        return False
    
    # Check for result
    if 'result' not in result:
        self.record_test(test_name, False, "No result in response")
        return False
    
    # NEW: Check for error inside result
    result_data = result['result']
    if isinstance(result_data, dict) and 'error' in result_data:
        self.record_test(test_name, False, f"Method error: {result_data['error']}")
        return False
    
    # NEW: Check for success flag
    if isinstance(result_data, dict) and 'success' in result_data and not result_data['success']:
        self.record_test(test_name, False, f"Method failed: {result_data.get('error', 'Unknown error')}")
        return False
    
    # Rest of validation...
```

### 3.2 Add State Verification Tests
```python
def test_unit_selection_state(self):
    """Test that selection actually updates board state"""
    # Create unit
    # Select unit
    # Verify board.selected is set
    # Deselect
    # Verify board.selected is None
    
def test_capture_actually_works(self):
    """Test that capture reduces HP and changes ownership"""
    # Create infantry on enemy city
    # Get initial capture_hp
    # Execute capture
    # Verify capture_hp decreased
    # Continue until captured
    # Verify ownership changed
```

## Phase 4: Implementation Order

### Week 1: Critical Game Functions
1. ✅ Unit selection (DONE)
2. Capture system (capture_tile, capture_tile_enhanced)
3. Victory conditions (check_win_condition)
4. Basic movement preview

### Week 2: System Integration
1. Transport system wrappers
2. Production system integration
3. Combat preview fixes
4. Movement validation

### Week 3: Test Framework
1. Fix assert_success to detect actual failures
2. Add state verification tests
3. Create integration tests that verify game state
4. Update all existing tests

## Phase 5: Error Handling

### 5.1 RPC Layer
- Add specific error codes for missing methods
- Return proper JSON-RPC errors (not wrapped in result)
- Log all missing method calls

### 5.2 Manager Layer
- Raise NotImplementedError for missing methods
- Add method existence checks
- Proper validation before delegating to systems

## Success Criteria
1. All RPC methods have corresponding manager implementations
2. Tests verify actual functionality, not just RPC format
3. No silent failures - errors are properly reported
4. All game features work as expected
5. Clear separation of concerns with proper integration

## Immediate Actions
1. Implement capture_tile method (most critical for gameplay)
2. Fix test framework to detect real failures
3. Run updated tests to identify all broken features
4. Systematically implement missing methods
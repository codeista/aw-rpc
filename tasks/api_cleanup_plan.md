# API Method Cleanup Plan

## Current Situation

We have multiple versions of similar RPC methods that create confusion:

### 1. Movement Methods
- `unit_move(x, y, x2, y2)` - Basic movement
- `unit_move_enhanced(from_x, from_y, to_x, to_y)` - Auto-handles transport boarding

**Problem**: Two methods, different parameter names, overlapping functionality

### 2. Attack Methods  
- `unit_attack` - Referenced in frontend but DOESN'T EXIST in app.py!
- `unit_attack_enhanced(attacker_x, attacker_y, defender_x, defender_y)` - Only actual implementation

**Problem**: Frontend expects `unit_attack` but only `unit_attack_enhanced` exists

### 3. Load Methods (3 versions!)
- `unit_load(x, y, x2, y2)` - Legacy alias, confusing params (x2,y2 is transport location)
- `load_transport_unit(x, y, transport_x, transport_y)` - Direct manager call
- `load_unit(unit_x, unit_y, transport_x, transport_y)` - Enhanced version

**Problem**: Three methods doing the same thing with different parameter names

### 4. Unload Methods (3 versions!)
- `unit_unload(x, y, x2, y2)` - Legacy alias (x,y is transport, x2,y2 is destination)
- `unload_transport_unit(x, y, unload_x, unload_y, unit_index)` - Direct manager call
- `unload_unit(transport_x, transport_y, target_x, target_y, unit_index)` - Enhanced version

**Problem**: Three methods, confusing parameter names in legacy version

## Recommended Actions

### Phase 1: Immediate Fixes (No Breaking Changes)

1. **Add missing `unit_attack` method**
   ```python
   @jsonrpc.method('unit_attack')
   def unit_attack_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
       """Legacy alias for unit_attack_enhanced - maintains frontend compatibility"""
       return unit_attack_enhanced_rpc(token, x, y, x2, y2)
   ```

2. **Update minimal_game.js to use consistent methods**
   - Change `unit_attack_enhanced` to `unit_attack` for consistency
   - Keep using `unit_move` (not enhanced) for simplicity

3. **Add deprecation notices in docstrings**
   - Mark `load_transport_unit` and `unload_transport_unit` as deprecated
   - Mark parameter confusion in `unit_load` and `unit_unload` docstrings

### Phase 2: Documentation Update

1. **Update README.md API section** to show:
   - Preferred methods: `unit_move`, `unit_attack`, `load_unit`, `unload_unit`
   - Mark enhanced versions as "advanced usage"
   - Explain parameter naming clearly

2. **Add API migration guide** explaining:
   - Which methods to use for new code
   - Parameter name mappings
   - Why duplicates exist (legacy compatibility)

### Phase 3: Future Cleanup (Breaking Changes)

1. **Standardize parameter names**:
   - Always use `x, y, target_x, target_y` (not x2, y2)
   - For attacks: `attacker_x, attacker_y, defender_x, defender_y`
   - For transports: `unit_x, unit_y, transport_x, transport_y`

2. **Remove redundant methods**:
   - Remove `load_transport_unit` and `unload_transport_unit`
   - Make `unit_move_enhanced` the default `unit_move`
   - Update all frontends to use consistent parameter names

## Benefits

1. **Less Confusion**: Clear which methods to use
2. **Better Documentation**: Explains the "why" behind duplicates
3. **Gradual Migration**: No immediate breaking changes
4. **Future Proof**: Clear path to cleaner API
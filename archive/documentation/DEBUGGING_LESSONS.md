# AW-RPC Debugging Lessons Learned

## Issue Resolution Summary (2025-01-16)

### Primary Issue: Duplicate Map Display
**Problem**: User reported seeing "a duplicate map grid to the left" causing coordinate offset issues
**Root Cause**: HTML template was loading both legacy render system AND modular render system simultaneously
**Solution**: Disabled modular render system in `templates/render.html` (lines 883-914)
**Files Changed**: 
- `/templates/render.html` - Commented out modular system loader

### Testing Methodology Lessons

#### ❌ **WRONG Approach - Don't Repeat These Mistakes:**

1. **Creating Empty Test Games**
   - `curl http://localhost:5000/test_game` creates games with 0 troops
   - Requires manual unit creation + turn cycling before testing combat
   - Wastes time on setup instead of testing core mechanics

2. **Testing Newly Created Units**
   - Fresh units have `can_move = false` on creation turn (authentic AW rule)
   - Need to end turn before they can act
   - Creates false negative test results

3. **Using Wrong API Endpoints**
   - JSON-RPC endpoint is `/api` not `/jsonrpc` 
   - Always check `app_core.py` line 14: `jsonrpc = JSONRPC(app, '/api')`

4. **Coordinate Offset Workarounds**
   - Adding coordinate offsets (-96px X, -80px Y) masks real problems
   - Fix root cause (duplicate rendering) instead of compensating

#### ✅ **CORRECT Approach - Follow These Patterns:**

1. **Use Pre-Deployed Test Games**
   ```bash
   curl http://localhost:5000/test_optimized
   # Creates game with 32+ units ready to act immediately
   ```

2. **Verify Game State First**
   ```bash
   # Check troop count
   curl -X POST http://localhost:5000/api -d '{"method": "game_board", "params": {"token": "TOKEN"}}'
   # Look for: "army_troops": {"BLUE": X, "RED": Y} where X,Y > 0
   ```

3. **Test Combat with Valid Units**
   ```bash
   # 1. Get attack targets first
   curl -X POST http://localhost:5000/api -d '{"method": "get_attack_targets", "params": {"token": "TOKEN", "unit_x": X, "unit_y": Y}}'
   
   # 2. Then execute attack
   curl -X POST http://localhost:5000/api -d '{"method": "unit_attack", "params": {"token": "TOKEN", "x": X, "y": Y, "x2": X2, "y2": Y2}}'
   ```

### Game Mechanics Understanding

#### Advance Wars Rules Clarification:
- **Direct Units** (Battleship, Tank, Infantry): CAN move AND attack same turn
- **Indirect Units** (Artillery, Rockets): CANNOT move and attack same turn  
- **New Units**: Cannot move on creation turn (authentic AW rule)
- **After Action**: Units get `can_move = false, can_attack = false, can_capture = false`

#### API Endpoint Reference:
- **Game Creation**: `/test_optimized` (pre-deployed) vs `/test_game` (empty)
- **JSON-RPC**: `/api` (not `/jsonrpc`)
- **API Browser**: `http://localhost:5000/api/browse/`
- **Board State**: `game_board` method
- **Attack Targets**: `get_attack_targets` method  
- **Combat**: `unit_attack` method

### Architecture Issues Found

#### Multiple Render Systems Conflict:
```html
<!-- templates/render.html was loading BOTH: -->
<script src="/static/js/render_legacy.js"></script>          <!-- Line 854 -->
<!-- AND -->
<script type="module">
  import moduleLoader from '/static/js/modules/moduleLoader.js';  <!-- Line 887 -->
</script>
```

**Fix**: Keep only one render system active. Legacy system works reliably.

#### File Locations for Canvas Creation:
- `render_legacy.js:435` - Main canvas creation
- `render.js:389` - Alternate canvas creation  
- `render_modular.js:84` - Modular canvas creation
- `render_final.js:105` - Final version canvas creation

**Lesson**: Only ONE should be active to prevent visual duplication.

### Testing Environment Setup

#### Flask Server Management:
```bash
# Correct way to start server in background:
source flask-env/bin/activate && nohup python app.py > server.log 2>&1 &

# Check if running:
curl -s http://localhost:5000/test_optimized -w "%{http_code}" -o /dev/null
# Should return: 302 (redirect)
```

#### Python JSON Parsing:
```bash
# For complex JSON analysis, use Python instead of jq:
python3 -c "
import json
with open('board.json') as f:
    data = json.load(f)
for tile in data['result']['grid']:
    if tile.get('unit'):
        print(f'{tile[\"unit\"][\"army\"]} {tile[\"unit\"][\"type\"]} at ({tile[\"x\"]}, {tile[\"y\"]})')
"
```

### Coordinate System Notes

#### Scene Translation Handling:
- Two.js uses scene translation offset (usually 16px Y-axis)
- `tileAt()` function correctly accounts for this in `render_legacy.js:1037-1056`
- Don't add manual coordinate offsets - fix root rendering issues instead

#### Valid Test Coordinates (test_optimized map):
- RED units start around (1-4, 1-8)  
- BLUE units start around (6-10, 1-8)
- 12x10 grid total (0-11 X, 0-9 Y)

### Success Verification Patterns

#### Combat Test Success Indicators:
1. Attack returns attacking unit with `can_attack: false`
2. Target tile shows `"unit": null` (if destroyed) or reduced HP
3. No error codes in response
4. Board state updates correctly

#### Movement Test Success Indicators:
1. Unit appears at new coordinates
2. Original tile shows `"unit": null`
3. Unit has updated movement flags
4. No coordinate offset required

### Documentation References
- **Game Rules**: `/GAME_MECHANICS.md` 
- **API Methods**: `/README.md` lines 22-27
- **Controls**: `/README.md` lines 28-50
- **API Browser**: `http://localhost:5000/api/browse/`

---

## Quick Reference Checklist

Before debugging game mechanics:
- [ ] Use `test_optimized` not `test_game`
- [ ] Verify `army_troops > 0` in board state
- [ ] Check `/api` endpoint not `/jsonrpc`
- [ ] Confirm only one render system is active
- [ ] Test with units that have `can_attack: true`
- [ ] Use `get_attack_targets` before `unit_attack`

**Remember**: Fix root causes, don't add workarounds!
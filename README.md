# Advance Wars RPC Game Engine

A fully functional Advance Wars implementation with authentic combat mechanics, transport systems, and multiplayer support. All core game systems are complete and fully tested.

## Quick Start

### Setup
```bash
# Create virtual environment
python3 -m venv flask-env

# Activate environment
. flask-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the game
python3 app.py
```

### Access Points
- **Play Game**: http://localhost:5000/test_game (NEW: Unified test system)
- **API Browser**: http://localhost:5000/api/browse
- **Test Interface**: http://localhost:5000/test_interface
- **Create Custom Game**: http://localhost:5000/{game_id}

## Game Controls

### Mouse Controls
- **Click**: Select unit / Move to empty tile / Attack enemy unit
- **Double-click**: Capture property / End unit's turn
- **Right-click**: Context menu (repair/resupply)
- **Ctrl+Click**: Load unit into transport
- **Alt+Click**: Unload unit from transport

### Keyboard Shortcuts (NEW!)
- **Space/E**: End turn
- **ESC**: Cancel action / Deselect
- **Enter**: Confirm / Wait unit
- **W**: Wait selected unit
- **A**: Attack mode
- **M**: Move mode
- **C**: Capture property
- **L**: Load unit into transport
- **U**: Unload unit from transport
- **Tab**: Cycle through units
- **H**: Show help overlay
- **+/-/0**: Zoom controls
- **R**: Refresh board

### Transport Controls
- **Loading**: Move cargo unit onto transport tile (automatic) or press L
- **Unloading**: Select transport → Click adjacent tile → Select cargo or press U
- **Note**: Unloaded units cannot act the same turn (authentic AW rule)

## Game Features

### ✅ Combat System (100% Complete)
- Authentic damage calculations with official AW formulas
- Terrain defense modifiers (Plains 0%, Woods 20%, Cities 30%, etc.)
- Counter-attack mechanics
- HP-based damage reduction
- Unit type advantages/disadvantages

### ✅ Movement System (100% Complete)
- Dijkstra pathfinding with terrain costs
- Movement range visualization
- Fuel consumption tracking
- Valid move validation
- Movement preview

### ✅ Transport System (100% Complete)
- **APC**: Infantry/Mech transport with auto-resupply capability
- **T-Copter**: Air transport for Infantry/Mech
- **Lander**: Naval transport for ground units (2 slots)
- **Black Boat**: Infantry/Mech transport with repair capability (up to 10 visual HP / 90 actual HP max)
- **Cruiser**: Helicopter transport with resupply
- **Carrier**: Fighter/Bomber transport (2 slots)

### ✅ Economic System (100% Complete)
- Daily income from properties (1000 per property)
- Unit production costs
- Fund management
- Property capture income

### ✅ Victory Conditions (100% Complete)
- HQ capture victory
- Total elimination victory
- Turn limit victory
- Property control victory

## Test Results

All systems fully tested and operational:
- **Combat System**: 4/4 test categories passing
- **Movement System**: 6/6 test categories passing
- **Transport System**: 8/8 test categories passing
- **Repair & Refuel System**: 4/4 test categories passing
- **Economic System**: 6/6 test categories passing
- **Victory Conditions**: 5/5 test categories passing

**Total: 33/33 test categories (100%)**

## Running Tests

```bash
# Run all unit tests
python3 tests/unit/test_combat_system.py
python3 tests/unit/test_movement_system.py
python3 tests/unit/test_transport_final.py
python3 test_repair_refuel_proper.py
python3 tests/unit/test_economic_system.py

# Run integration tests
python3 tests/integration/test_victory_conditions.py

# Run via web interface
# Visit http://localhost:5000/test_interface for interactive testing
```

## Architecture

### Frontend
- **render.js**: Game rendering with Two.js
- **Socket.IO**: Real-time multiplayer updates
- **RPC Client**: JSON-RPC communication

### Backend
- **app.py**: Flask server with RPC endpoints
- **manager.py**: Core game logic
- **transport_system.py**: Transport mechanics
- **combat_system.py**: Combat calculations
- **map_system.py**: Map loading and terrain

### Database
- **SQLite**: Game state persistence
- **Models**: Game, Unit, Tile, Army tables

## Current Development Status

### Working Features
- ✅ All unit types (25 total)
- ✅ All terrain types with proper effects
- ✅ Complete transport load/unload system
- ✅ Property capture mechanics
- ✅ Turn management
- ✅ Combat with counter-attacks
- ✅ Victory detection
- ✅ Save/load game state

### Recently Completed
- [x] APC/Cruiser/Carrier auto-resupply at turn start
- [x] Black Boat manual repair command (up to 2 HP per action, max 10 visual HP / 90 actual HP)
- [x] Comprehensive repair and refuel testing suite
- [x] Test interface integration for repair/refuel tests

### In Progress
- [ ] COM_TOWER damage bonus (+10% per tower)

### Future Features
- [ ] Commanding Officer (CO) system with powers
- [ ] Weather effects and Fog of War
- [ ] User account system
- [ ] Ranked multiplayer
- [ ] Replay system
- [ ] Additional game modes

## API Documentation

### Key RPC Methods
```javascript
// Game Management
rpc('game_create', {token})              // Regular game (5000 starting funds)
rpc('game_create_test', {token})         // Test game (50000 starting funds)
rpc('army_end_turn', {token})
rpc('game_board', {token})

// Movement
rpc('unit_move', {token, x, y, x2, y2})
rpc('get_valid_moves', {token, x, y})

// Combat
rpc('unit_attack', {token, x, y, x2, y2})
rpc('get_damage_preview', {token, x, y, x2, y2})

// Transport
rpc('cargo_board_transport', {token, cargo_x, cargo_y, transport_x, transport_y})
rpc('cargo_exit_transport', {token, transport_x, transport_y, exit_x, exit_y, cargo_index})

// Production
rpc('unit_create', {token, army, unit_type, x, y})
rpc('get_production_options', {token, x, y})

// Repair & Resupply (Black Boat - up to 2 HP per action, max 10 visual HP)
rpc('repair_unit', {token, blackboat_x, blackboat_y, target_x, target_y, hp_to_repair})

// Manual Resupply (Black Boat/APC - FREE)
rpc('resupply_unit', {token, resupply_x, resupply_y, target_x, target_y, fuel_amount, ammo_amount})
```

## Contributing

This project implements authentic Advance Wars mechanics. When contributing:
1. Ensure changes match official AW behavior
2. Add tests for new features
3. Update documentation
4. Follow existing code patterns

## License

This is a fan project for educational purposes. Advance Wars is a trademark of Nintendo/Intelligent Systems.
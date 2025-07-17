# Advance Wars RPC Game Engine

A fully functional Advance Wars implementation with authentic combat mechanics, transport systems, and multiplayer support. All core game systems are complete and fully tested.

## Quick Start

### Setup
```bash
# Create virtual environment
python3 -m venv flask-env

# Activate environment
source flask-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the game
python3 app.py
```

**Note:** Always use `flask-env` virtual environment for running the game and tests.

### Access Points
- **Play Game**: http://localhost:5000/test_game (NEW: Unified test system)
- **API Documentation**: http://localhost:5000/api/docs (NEW: Categorized API reference)
- **API Browser**: http://localhost:5000/api/browse (Interactive RPC testing)
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

## Technical Architecture

### Coordinate System
The game uses a unified coordinate system (`coordinate-system.js`) that automatically handles:
- Different map sizes (12x10, 20x15, etc.)
- Canvas scaling and zooming
- Container resizing
- Sprite overlap compensation
- Dynamic board updates when switching maps

### Game Features

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
- **Combat System**: 4/4 test categories passing ✅
- **Movement System**: 6/6 test categories passing ✅
- **Transport System**: 3/3 test categories passing ✅ (Updated test)
- **Repair & Refuel System**: 4/4 test categories passing ✅
- **Economic System**: 6/6 test categories passing ✅
- **Victory Conditions**: 5/5 test categories passing ✅

**Total: 13/13 test suites (100% success rate)**

### Recent Updates (July 2025)
- Fixed Flask blueprint registration for test interface
- Implemented unified coordinate system for dynamic map sizes
- Resolved canvas click accuracy issues across all zoom levels
- Cleaned up 31 debugging files, reducing codebase complexity

## Running Tests

### Automated Regression Tests (Recommended)
```bash
# Quick regression test runner (comprehensive mechanics validation)
python3 run_regression_tests.py

# Or use the full test runner with options
python3 tests/run_tests.py
# Choose option 3: Automated Regression Tests
```

### Manual Unit Tests
```bash
# Run individual unit tests
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

### Regression Test Suite Features
- **🤖 Fully Automated**: No manual intervention required
- **⚡ Fast Execution**: Complete validation in ~3 minutes
- **🎯 Comprehensive Coverage**: All core game mechanics tested
- **📊 Detailed Reporting**: Success/failure rates with specific error details
- **🔄 CI/CD Ready**: Returns proper exit codes for automated systems

## Architecture

### Sprite System
See [SPRITE_STATUS.md](SPRITE_STATUS.md) for current sprite mapping progress and limitations.

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

### 🔗 **Enhanced API Browser** (NEW!)
- **Categorized Methods**: http://localhost:5000/api/docs - Beautiful categorized API reference
- **Interactive Testing**: http://localhost:5000/api/browse - Live RPC method testing
- **60+ Methods** organized into 9 logical categories
- **Complete Documentation** with examples and parameter descriptions

### API Categories
- **🎮 Game Management** - Core game lifecycle operations
- **🪖 Unit Operations** - Unit creation, movement, and actions  
- **⚔️ Combat System** - Attack mechanics and damage calculations
- **🚢 Transport System** - Cargo loading and transport operations
- **🗺️ Map & Tile Information** - Terrain and tile data access
- **🏰 Special Actions** - Property capture and special abilities
- **🏭 Production & Economic** - Unit production and financial operations
- **📋 Information & Reference** - Configuration and reference data
- **💬 Communication** - Chat and messaging features

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
rpc('combat_preview', {token, attacker_x, attacker_y, defender_x, defender_y})

// Transport
rpc('load_unit', {token, transport_x, transport_y, cargo_x, cargo_y})
rpc('unload_unit', {token, transport_x, transport_y, unload_x, unload_y, cargo_index})

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
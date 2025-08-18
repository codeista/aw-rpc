# Advance Wars RPC

A web-based implementation of Advance Wars with authentic game mechanics, multiplayer support, and a complete RPC API.

## Quick Start

```bash
# Create and activate virtual environment
python3 -m venv flask-env
source flask-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python3 app.py
# Or use the helper script: ./start_server.sh

# Play the game
# Visit http://localhost:5000
```

## Game Features

### ✅ Complete Game Systems
- **25 unit types** with authentic stats and mechanics
- **Combat system** with damage calculations, terrain defense, and counter-attacks
- **Transport system** for loading/unloading units (APC, Lander, Carrier, etc.)
- **Economic system** with property income and unit production
- **Victory conditions**: HQ capture, elimination, property control
- **Multiplayer support** with real-time updates via Socket.IO

### 🎮 Game Controls

**Mouse:**
- Click: Select unit / Move / Attack
- Right-click: Context menu
- Ctrl+Click: Load into transport
- Alt+Click: Unload from transport

**Keyboard:**
- Space/E: End turn
- W: Wait unit
- C: Capture property
- Tab: Cycle units
- ESC: Cancel/Deselect

## API Reference

The game provides a complete JSON-RPC API for all game operations.

### Key Endpoints

```javascript
// Game Management
rpc('game_create_v2', {token, players, map_name})
rpc('game_create_test', {token})  // Test game with 50k funds
rpc('game_board', {token})
rpc('army_end_turn', {token})

// Unit Operations
rpc('unit_create', {token, player_id, unit_type, x, y})
rpc('unit_move', {token, x, y, x2, y2})
rpc('unit_attack', {token, x, y, x2, y2})

// Transport Operations
rpc('load_unit', {token, transport_x, transport_y, cargo_x, cargo_y})
rpc('unload_unit', {token, transport_x, transport_y, unload_x, unload_y, cargo_index})
```

**Full API Documentation:**
- Interactive browser: http://localhost:5000/api/browse
- Categorized reference: http://localhost:5000/api/docs

## Map System

Maps use a flexible slot-based system where players choose their colors at game start.

### Map Format
```
<number_of_players>
<width>,<height>
<tile> <tile> <tile>...
```

### Example (2-player map)
```
2
10,8
FACTORY:0 CITY PLAIN WOOD PLAIN CITY FACTORY:1
HQ:0 CITY:0 PLAIN SEA PLAIN CITY:1 HQ:1
```

Properties owned by player slots (0, 1, 2...) instead of fixed colors.

## Testing

```bash
# Run all regression tests (recommended)
python3 tests/run_regression_tests.py

# Run specific test suites
python3 tests/unit/test_combat_system.py
python3 tests/unit/test_transport_features.py

# Interactive testing
# Visit http://localhost:5000/test_interface
```

## Project Structure

```
aw-rpc/
├── app.py              # Flask server & RPC endpoints
├── manager.py          # Core game logic
├── config.ini          # Unit configurations
├── core/               # Core game modules
│   ├── unit.py         # Unit definitions
│   ├── map_system.py   # Map & terrain logic
│   ├── combat_system.py # Combat calculations
│   └── transport_system.py # Transport mechanics
├── static/             # Frontend assets
│   ├── js/             # Game client code
│   └── img/            # Sprites & tilesets
├── templates/          # HTML templates
├── tests/              # Test suites
└── docs/               # Additional documentation
```

## Performance

- Average API response time: **6.68ms**
- All operations complete in under 50ms
- 98%+ test coverage with automated regression suite

## Contributing

When contributing, please:
1. Ensure changes match authentic Advance Wars behavior
2. Add tests for new features
3. Update relevant documentation
4. Follow existing code patterns

## License

This is a fan project for educational purposes. Advance Wars is a trademark of Nintendo/Intelligent Systems.
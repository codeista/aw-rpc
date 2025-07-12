# Advance Wars RPC Game Engine

A fully functional Advance Wars implementation with authentic combat mechanics, transport systems, and multiplayer support.

## Quick Start

### Install venv
```bash
python3.9 -m venv flask-env
```

### Start environment
```bash
. flask-env/bin/activate
```

### Install requirements
```bash
pip install -r requirements.txt
```

### Run locally
```bash
python3 app.py
```

### Run tests
```bash
python test_unittest.py
```

## Game Access

- **API Browser**: http://localhost:5000/api/browse
- **Start/View Game**: http://localhost:5000/(game)
- **Test Interface**: http://localhost:5000/test

## Controls & Gameplay

### Basic Controls
- **Click**: Select unit / Move to empty tile / Attack enemy unit
- **Double-click**: Capture property / Wait (end unit's turn)
- **Ctrl+Click**: Load unit into transport
- **Alt+Click**: Show unload options / Unload from transport
- **ESC**: Cancel transport actions / Clear highlights

### Unit Management
- **Selection**: Click on your units to select them
- **Movement**: Click on highlighted tiles to move selected unit
- **Attack**: Click on enemy units within range to attack
- **Capture**: Double-click on properties with Infantry/Mech to capture

### Transport System (Authentic Advance Wars Style)
#### Loading Units
1. Select a cargo unit (Infantry, Mech, etc.)
2. **Ctrl+Click** on a friendly transport (APC, Lander, etc.)
3. Unit automatically loads if compatible and space available

#### Unloading Units
1. **Alt+Click** on a loaded transport
2. Blue tiles appear showing valid exit positions
3. **Alt+Click** on any blue tile to deploy unit there
4. Unloaded units cannot act the same turn (authentic AW rule)

#### Transport Types & Compatibility
- **APC**: Carries Infantry, Mech (Land transport)
- **Lander**: Carries land units across water
- **T-Copter**: Air transport for Infantry, Mech
- **Cruiser**: Naval transport for air units
- **Carrier**: Carries 2 air units

### Combat System
#### Damage Calculation (Authentic Formula)
```
Base Damage = (Attacker ATK × Attacker HP / 10) × Weapon Power / 100
Final Damage = Base × Random(90-99) / 100 × Terrain Defense
```

#### Features
- **Authentic damage tables**: Based on official Advance Wars values
- **Counter-attacks**: Defending units counter if in range and alive
- **Terrain defense**: Roads (0%), Forests (20%), Cities (30%), etc.
- **HP-based damage**: Damaged units deal proportionally less damage
- **Weapon selection**: Units automatically choose optimal weapon

## Testing Features

### Test Interface (`/test`)
- **Unit Matchup Testing**: Verify damage calculations across unit types
- **Combat System Testing**: Test damage previews and battle outcomes
- **Transport System Testing**: Validate loading/unloading mechanics

### Available Test Games
- **Basic Test**: `/test` - Standard test map with predeployed units
- **Terrain Test**: Custom maps for testing different terrain types
- **Combat Test**: Scenarios for validating combat mechanics

## Technical Features

### RPC Methods
The game supports extensive RPC methods for:
- Unit movement and combat
- Transport operations (load/unload)
- Property capture and production
- Turn management
- Damage calculations and previews

### Key RPC Endpoints
- `unit_move`: Move units with enhanced validation
- `unit_attack`: Execute combat with authentic damage
- `cargo_board_transport`: Load units into transports
- `cargo_exit_transport`: Unload units from transports
- `get_damage_preview`: Preview combat outcomes
- `unit_create`: Produce units from factories/airports/ports

### Database & State Management
- **SQLite**: Game state persistence
- **Socket.IO**: Real-time multiplayer updates
- **Session management**: Multiple concurrent games
- **Auto-save**: Game state automatically preserved


## Implementation Status

### ✅ Completed Features
- **Authentic Combat System**: Full damage calculation with weapon tables
- **Transport System**: Complete load/unload mechanics for all transport types
- **Unit Matchup Testing**: Comprehensive damage validation across unit types
- **Counter-attack Logic**: Prevents destroyed units from counter-attacking
- **Visual Indicators**: Authentic AW load icons and highlight system
- **Movement Validation**: Enhanced pathfinding and movement rules
- **Property Capture**: Factory, Airport, Port, and City capture mechanics
- **Turn Management**: Proper turn cycling and unit state management

### 🚧 Current TODO
- Create flow diagram to visualize game flow
- Create user/player system to join games
- Add COM_TOWER damage bonus (+10% per tower)
- Implement all terrain tiles from tileset
- CO (Commanding Officer) system and powers

### 🎯 Future Enhancements
- **Resupply System**: On-demand resupply via context menu for APC/Blackboat
- **Multiple Cargo**: Support for multiple units in larger transports
- **Unit Joining**: Mouse selection to join damaged units together
- **Weather System**: Including fog of war mechanics
- **Stealth Mechanics**: For submarines and stealth units
- **Fuel Consumption**: Proper fuel usage for hidden/submerged units

## Architecture

### Frontend (`static/js/`)
- **render.js**: Main game rendering and Two.js canvas management
- **transport_integration.js**: Complete transport system integration
- **comprehensive_game_testing.js**: Testing suite for game mechanics

### Backend (`*.py`)
- **app.py**: Main Flask application with RPC endpoints
- **manager.py**: Core game logic and state management
- **transport_system.py**: Complete transport mechanics implementation
- **combat_system.py**: Authentic damage calculation system
- **unit.py**: Unit definitions and behavior
- **gameboard.py**: Board state and tile management

### Key Systems
1. **Combat**: Authentic AW damage formulas with terrain effects
2. **Transport**: Full load/unload with visual feedback
3. **Movement**: Dijkstra pathfinding with terrain costs
4. **Production**: Factory/Airport/Port unit creation
5. **Capture**: Property ownership and income generation

## Contributing

The codebase follows authentic Advance Wars mechanics and includes comprehensive testing systems. All transport and combat features match official game behavior.

### Testing
- Use `/test` interface for unit testing
- Check browser console for debug information
- Server logs available in `logs/` directory
- Unit tests in `test_unittest.py`

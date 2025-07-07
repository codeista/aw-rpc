# app_integration_test_map.py - Easy integration for test maps

"""
Instructions to integrate test maps with predeployed units into your existing app.py:

1. Save the test_map_predeployed.py file to your project directory
2. Add the imports and routes below to your app.py
3. Access test games at: http://localhost:5000/test or http://localhost:5000/test_comprehensive
"""

# ADD THESE IMPORTS to the top of your app.py (after existing imports)
from test_map_predeployed import get_predeployed_test_game, get_comprehensive_test_game

# ADD THESE ROUTES to your app.py (after existing routes)

@app.route('/test')
def create_test_game_with_units():
    """Create a 7x7 test game with predeployed units for immediate testing"""
    token = secrets.token_urlsafe(6)
    
    try:
        # Create game with predeployed units
        game_manager = get_predeployed_test_game(token)
        games[token] = game_manager
        
        # Log game creation
        app_logger.info(f"Created test game with predeployed units: {token}")
        
        # Redirect to the game
        return redirect(f'/{token}')
    
    except Exception as e:
        app_logger.error(f"Failed to create test game: {e}")
        return f"Error creating test game: {e}", 500

@app.route('/test_comprehensive')  
def create_comprehensive_test_game():
    """Create a 10x10 test game with comprehensive unit deployment"""
    token = secrets.token_urlsafe(6)
    
    try:
        # Create comprehensive test game
        game_manager = get_comprehensive_test_game(token)
        games[token] = game_manager
        
        app_logger.info(f"Created comprehensive test game: {token}")
        return redirect(f'/{token}')
    
    except Exception as e:
        app_logger.error(f"Failed to create comprehensive test game: {e}")
        return f"Error creating comprehensive test game: {e}", 500

# MODIFY YOUR EXISTING get_game() function to support test maps
# Replace your existing get_game function with this enhanced version:

def get_game(token: str, use_test_map: bool = False):
    """
    Enhanced game creation with optional test map support
    """
    # Check if game already exists
    if token in games:
        return games[token]
    
    # Try to load from database first
    try:
        game = Game.query.filter_by(token=token).first()
        if game and game.board_state:
            # Your existing deserialization code here...
            # [Keep your existing deserialization logic]
            pass
    except Exception as e:
        app_logger.error(f"Failed to deserialize game {token}: {str(e)}")
    
    app_logger.info(f"Creating new game: {token}")
    
    # Choose map type based on parameter
    if use_test_map:
        # Create with test map (predeployed units)
        try:
            game_manager = get_predeployed_test_game(token)
            return game_manager
        except Exception as e:
            app_logger.error(f"Failed to create test map, falling back to default: {e}")
    
    # Default map creation (your existing code)
    try:
        default_map = map_repository.get_map('test')
        if not default_map:
            default_map = map_repository.get_map('scorpion')  
    except:
        from map_system import Map
        default_map = Map()
    
    board = GameBoard.create(default_map)
    mngr = GameManager(config_game, board)
    
    if ENHANCED_LOGGING:
        game_event_logger.log_game_created(token, len(board.turn_order))
    
    return mngr

# OPTIONAL: Add a toggle to your existing random game creation
# Modify your existing @app.route('/') if you want random games to sometimes use test maps

@app.route('/debug')
def debug_info():
    """Debug endpoint to see current game status"""
    active_games = []
    for token, game in games.items():
        board = game.board
        active_games.append({
            'token': token,
            'size': f"{board.width}x{board.height}",
            'current_turn': board.current_turn.name,
            'red_units': board.total_red_troops,
            'blue_units': board.total_blue_troops,
            'red_funds': board.red_funds,
            'blue_funds': board.blue_funds,
            'days': board.days
        })
    
    return {
        'active_games': active_games,
        'total_games': len(games)
    }

# TESTING ENDPOINTS for specific scenarios
@app.route('/test_combat')
def test_combat_scenario():
    """Create a game specifically designed for combat testing"""
    token = secrets.token_urlsafe(6)
    
    # Create basic test game
    game_manager = get_predeployed_test_game(token)
    
    # Modify to have units adjacent for immediate combat
    board = game_manager.board
    
    # Clear a section and place opposing units next to each other
    # Find center of board
    center_x, center_y = board.width // 2, board.height // 2
    
    # Clear center area
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            x, y = center_x + dx, center_y + dy
            if 0 <= x < board.width and 0 <= y < board.height:
                tile_index = y * board.width + x
                board.grid[tile_index].unit = None
    
    # Place combat units
    from unit import Unit, UnitType
    
    # RED tank
    red_tank = Unit.create(Army.RED, UnitType.TANK)
    tile_index = center_y * board.width + (center_x - 1)
    board.grid[tile_index].unit = red_tank
    
    # BLUE tank (adjacent)
    blue_tank = Unit.create(Army.BLUE, UnitType.TANK)
    tile_index = center_y * board.width + (center_x + 1)
    board.grid[tile_index].unit = blue_tank
    
    games[token] = game_manager
    app_logger.info(f"Created combat test game: {token}")
    return redirect(f'/{token}')

@app.route('/test_movement')  
def test_movement_scenario():
    """Create a game specifically for movement testing"""
    token = secrets.token_urlsafe(6)
    
    game_manager = get_predeployed_test_game(token)
    board = game_manager.board
    
    # Clear most of the board for open movement
    for tile in board.grid:
        if tile.unit and tile.unit.army == Army.BLUE:
            tile.unit = None  # Remove BLUE units for easier testing
    
    # Place a few RED units in strategic positions
    from unit import Unit, UnitType
    
    test_units = [
        {'type': UnitType.INFANTRY, 'x': 1, 'y': 1},
        {'type': UnitType.RECON, 'x': 3, 'y': 3},
        {'type': UnitType.TANK, 'x': 5, 'y': 5}
    ]
    
    for unit_data in test_units:
        # Clear the tile first
        tile_index = unit_data['y'] * board.width + unit_data['x']
        board.grid[tile_index].unit = None
        
        # Place new unit
        unit = Unit.create(Army.RED, unit_data['type'])
        board.grid[tile_index].unit = unit
    
    games[token] = game_manager
    app_logger.info(f"Created movement test game: {token}")
    return redirect(f'/{token}')

# QUICK SETUP INSTRUCTIONS
"""
To quickly set up test maps:

1. Copy test_map_predeployed.py to your project folder
2. Add the imports and routes above to your app.py
3. Start your server: python app.py
4. Visit these URLs:

   http://localhost:5000/test           - Basic 7x7 map with predeployed units
   http://localhost:5000/test_comprehensive - 10x10 map with many unit types
   http://localhost:5000/test_combat    - Units positioned for immediate combat
   http://localhost:5000/test_movement  - Open map for movement testing
   http://localhost:5000/debug          - View all active games

Your tests should immediately show:
✅ RED and BLUE units on the board
✅ Balanced funds (15,000 each for basic, 25,000 for comprehensive)
✅ Units ready to move, attack, and capture
✅ No more "No units found" errors
"""

# EXAMPLE TEST COMMANDS to run in browser console:
"""
// After visiting /test, open browser console and run:

// Check initial state
rpc('game_board', {}, console.log);

// Test movement (move RED infantry from (0,1) to (0,2))
rpc('unit_move', {x: 0, y: 1, x2: 0, y2: 2}, console.log);

// Test attack (have RED unit attack BLUE unit)
rpc('unit_attack', {x: 2, y: 2, x2: 4, y: 2}, console.log);

// End turn
rpc('army_end_turn', {}, console.log);

// Create new unit at factory
rpc('unit_create', {army: 'RED', unit_type: 'INFANTRY', x: 0, y: 0}, console.log);
"""
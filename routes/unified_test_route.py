"""
Unified test game creation route - consolidates all test game creation into one parameterized endpoint
"""

from flask import Blueprint, request, redirect, url_for, jsonify
import time
from manager import GameManager
from gameboard import GameBoard
from config import Config
from map_system import map_repository
import logging

app_logger = logging.getLogger('aw-rpc')

unified_test_bp = Blueprint('unified_test', __name__)

# Test configurations
TEST_CONFIGS = {
    'basic': {
        'map': 'test',
        'description': 'Basic test game with standard map'
    },
    'comprehensive': {
        'map': 'test',
        'description': 'All features test with pre-deployed units',
        'add_units': True
    },
    'movement': {
        'map': 'test', 
        'description': 'Movement system test',
        'add_units': True,
        'unit_focus': 'movement'
    },
    'combat': {
        'map': 'test',
        'description': 'Combat scenarios test',
        'add_units': True,
        'unit_focus': 'combat'
    },
    'optimized': {
        'map': 'test',
        'description': 'Quick all-features test',
        'add_units': True
    },
    'transport': {
        'map': 'test',
        'description': 'Basic transport operations test',
        'add_units': True,
        'unit_focus': 'transport'
    },
    'transport_comprehensive': {
        'map': 'transport_test',
        'description': 'Comprehensive transport mechanics test',
        'add_units': True,
        'unit_focus': 'transport_comprehensive'
    },
    'capture': {
        'map': 'test',
        'description': 'Capture mechanics test',
        'add_units': True,
        'unit_focus': 'capture'
    },
    'triangle': {
        'map': 'triangle',
        'description': '3-player Triangle Arena'
    },
    'cross': {
        'map': 'cross',
        'description': '4-player Cross Battle'
    },
    'pentagon': {
        'map': 'pentagon',
        'description': '5-player Pentagon Chaos'
    },
    'scorpion': {
        'map': 'scorpion',
        'description': 'Scorpion Operation scenario'
    },
    'green_yellow': {
        'map': 'green_yellow_arena',
        'description': 'Green vs Yellow victory test'
    },
    'islands': {
        'map': 'green_blue_islands',
        'description': 'Green vs Blue island battle'
    },
    'mountains': {
        'map': 'yellow_grey_mountains',
        'description': 'Yellow vs Grey mountain war'
    },
    'hq_rush': {
        'map': 'green_yellow_hq_rush',
        'description': 'Green vs Yellow HQ rush'
    },
    'multi_army': {
        'map': 'multi_army_test',
        'description': '4-color multi-army test'
    },
    'elimination': {
        'map': 'elimination_test',
        'description': 'Small elimination test'
    },
    'naval': {
        'map': 'naval_test',
        'description': 'Naval units comprehensive test',
        'add_units': True,
        'unit_focus': 'naval'
    },
    'air': {
        'map': 'air_test',
        'description': 'Air units comprehensive test',
        'add_units': True,
        'unit_focus': 'air'
    },
    'land': {
        'map': 'land_test',
        'description': 'Land units comprehensive test',
        'add_units': True,
        'unit_focus': 'land'
    }
}

@unified_test_bp.route('/test_game')
def unified_test_game():
    """
    Unified test game creation endpoint.
    
    Query parameters:
    - type: Type of test game (default: 'basic')
    - players: Override number of players (optional)
    - map: Override map choice (optional)
    - units: Whether to add pre-deployed units (optional)
    
    Examples:
    - /test_game - Basic test game
    - /test_game?type=combat - Combat test with units
    - /test_game?type=triangle - 3-player triangle map
    - /test_game?type=basic&map=scorpion - Basic game on Scorpion map
    - /test_game?type=transport&units=true - Transport test with units
    """
    
    # Get parameters
    test_type = request.args.get('type', 'basic')
    custom_map = request.args.get('map')
    force_units = request.args.get('units', '').lower() == 'true'
    
    # Validate test type
    if test_type not in TEST_CONFIGS:
        return jsonify({'error': f'Unknown test type: {test_type}', 
                       'available': list(TEST_CONFIGS.keys())}), 400
    
    config = TEST_CONFIGS[test_type]
    
    # Override map if specified
    map_name = custom_map or config['map']
    
    # Check if map exists
    game_map = map_repository.get_map(map_name)
    if not game_map:
        return jsonify({'error': f'Map not found: {map_name}',
                       'available': map_repository.list_maps()}), 400
    
    # Generate unique token
    token = f"test_{test_type}_{int(time.time())}"
    
    # Create game
    try:
        # Create config and board first
        config_game = Config()
        config_game.current_turn = 'RED'
        config_game.current_day = 1
        config_game.max_days = 30
        
        board = GameBoard.create(game_map)
        game = GameManager(config_game, board)
        
        # Import games dict from main app (avoid circular import)
        from app import games
        games[token] = game
        
        # Add units if configured or forced
        if config.get('add_units', False) or force_units:
            unit_focus = config.get('unit_focus')
            _add_test_units(game, unit_focus)
        
        app_logger.info(f"Created test game: {token} (type={test_type}, map={map_name})")
        
        # Redirect to game
        return redirect(url_for('render', token=token))
        
    except Exception as e:
        app_logger.error(f"Failed to create test game: {e}")
        return jsonify({'error': str(e)}), 500


def _add_test_units(game: GameManager, focus: str = None):
    """Legacy unit addition for old GameManager - use _add_test_units_v2 instead"""
    """Add pre-deployed units based on focus area."""
    
    if focus == 'movement':
        # Add movement-focused units
        units = [
            {"type": "INFANTRY", "player": 0, "x": 1, "y": 4},
            {"type": "MECH", "player": 0, "x": 2, "y": 5},
            {"type": "RECON", "player": 1, "x": 6, "y": 5},
            {"type": "TANK", "player": 1, "x": 7, "y": 6},
            {"type": "FIGHTER", "player": 0, "x": 1, "y": 7},
            {"type": "TCOPTER", "player": 1, "x": 8, "y": 8},
        ]
    elif focus == 'combat':
        # Add combat-focused units
        units = [
            {"type": "TANK", "player": 0, "x": 3, "y": 5},
            {"type": "TANK", "player": 1, "x": 5, "y": 5},
            {"type": "ARTILLERY", "player": 0, "x": 3, "y": 7},
            {"type": "ROCKET", "player": 1, "x": 6, "y": 7},
            {"type": "FIGHTER", "player": 0, "x": 1, "y": 8},
            {"type": "FIGHTER", "player": 1, "x": 8, "y": 8},
            {"type": "BATTLESHIP", "player": 0, "x": 3, "y": 0},
            {"type": "CRUISER", "player": 1, "x": 5, "y": 0},
        ]
    elif focus == 'transport':
        # Add basic transport-focused units
        units = [
            {"type": "INFANTRY", "player": 0, "x": 1, "y": 4},
            {"type": "MECH", "player": 0, "x": 2, "y": 4},
            {"type": "APC", "player": 0, "x": 3, "y": 4},
            {"type": "LANDER", "player": 1, "x": 7, "y": 1},
            {"type": "TCOPTER", "player": 1, "x": 8, "y": 7},
            {"type": "BLACKBOAT", "player": 0, "x": 2, "y": 2},
        ]
    elif focus == 'transport_comprehensive':
        # Comprehensive transport test with all transport types and loadable units
        units = [
            # Ground transports and their cargo
            {"type": "APC", "player": 0, "x": 0, "y": 4},
            {"type": "INFANTRY", "player": 0, "x": 1, "y": 4},
            {"type": "MECH", "player": 0, "x": 2, "y": 4},
            
            # Air transports and cargo
            {"type": "TCOPTER", "player": 0, "x": 0, "y": 7},
            {"type": "INFANTRY", "player": 0, "x": 1, "y": 7},
            {"type": "MECH", "player": 0, "x": 2, "y": 7},
            
            # Naval transports
            {"type": "LANDER", "player": 0, "x": 0, "y": 1},
            {"type": "BLACKBOAT", "player": 0, "x": 1, "y": 2},
            {"type": "CRUISER", "player": 0, "x": 2, "y": 1},
            {"type": "CARRIER", "player": 0, "x": 3, "y": 2},
            
            # Units that can be loaded on lander
            {"type": "TANK", "player": 0, "x": 0, "y": 3},
            {"type": "RECON", "player": 0, "x": 1, "y": 3},
            {"type": "ARTILLERY", "player": 0, "x": 2, "y": 3},
            
            # Air units for carrier/cruiser
            {"type": "FIGHTER", "player": 0, "x": 3, "y": 0},
            {"type": "BOMBER", "player": 0, "x": 4, "y": 0},
            {"type": "BCOPTER", "player": 0, "x": 3, "y": 1},
            
            # BLUE team transports
            {"type": "APC", "player": 1, "x": 9, "y": 4},
            {"type": "TCOPTER", "player": 1, "x": 9, "y": 7},
            {"type": "LANDER", "player": 1, "x": 9, "y": 1},
            {"type": "BLACKBOAT", "player": 1, "x": 8, "y": 2},
            {"type": "CRUISER", "player": 1, "x": 7, "y": 1},
            {"type": "CARRIER", "player": 1, "x": 6, "y": 2},
            
            # BLUE loadable units
            {"type": "INFANTRY", "player": 1, "x": 8, "y": 4},
            {"type": "MECH", "player": 1, "x": 7, "y": 4},
            {"type": "TANK", "player": 1, "x": 9, "y": 3},
            {"type": "FIGHTER", "player": 1, "x": 6, "y": 0},
            {"type": "BCOPTER", "player": 1, "x": 7, "y": 0},
        ]
    elif focus == 'capture':
        # Add units near capturable properties
        units = [
            {"type": "INFANTRY", "player": 0, "x": 3, "y": 3},  # Near city
            {"type": "MECH", "player": 1, "x": 8, "y": 4},     # Near factory
            {"type": "INFANTRY", "player": 0, "x": 7, "y": 8},  # Near airport
            {"type": "MECH", "player": 1, "x": 0, "y": 0},     # Near port
        ]
    elif focus == 'naval':
        # Comprehensive naval units test
        units = [
            # Player 1 (RED) naval units on left side
            {"type": "BATTLESHIP", "player": 0, "x": 0, "y": 1},
            {"type": "CRUISER", "player": 0, "x": 1, "y": 0},
            {"type": "SUB", "player": 0, "x": 2, "y": 1},
            {"type": "LANDER", "player": 0, "x": 0, "y": 2},
            {"type": "CARRIER", "player": 0, "x": 1, "y": 3},
            {"type": "BLACKBOAT", "player": 0, "x": 2, "y": 2},
            
            # Player 2 (BLUE) naval units on right side with proper spacing
            {"type": "BATTLESHIP", "player": 1, "x": 9, "y": 1},  # Range 2-6
            {"type": "CRUISER", "player": 1, "x": 8, "y": 0},
            {"type": "SUB", "player": 1, "x": 7, "y": 1},
            {"type": "LANDER", "player": 1, "x": 9, "y": 2},
            {"type": "CARRIER", "player": 1, "x": 8, "y": 3},
            {"type": "BLACKBOAT", "player": 1, "x": 7, "y": 2},
            
            # Add some air units for carrier testing
            {"type": "FIGHTER", "player": 0, "x": 1, "y": 4},
            {"type": "BOMBER", "player": 1, "x": 8, "y": 4},
            
            # Add infantry for transport testing
            {"type": "INFANTRY", "player": 0, "x": 0, "y": 4},
            {"type": "MECH", "player": 1, "x": 9, "y": 4},
        ]
    elif focus == 'air':
        # Comprehensive air units test
        units = [
            # Player 1 (RED) air units
            {"type": "FIGHTER", "player": 0, "x": 1, "y": 7},
            {"type": "BOMBER", "player": 0, "x": 2, "y": 8},
            {"type": "BCOPTER", "player": 0, "x": 0, "y": 8},
            {"type": "TCOPTER", "player": 0, "x": 1, "y": 9},
            {"type": "STEALTH", "player": 0, "x": 2, "y": 7},
            {"type": "BLACKBOMB", "player": 0, "x": 0, "y": 9},
            
            # Player 2 (BLUE) air units
            {"type": "FIGHTER", "player": 1, "x": 8, "y": 7},
            {"type": "BOMBER", "player": 1, "x": 7, "y": 8},
            {"type": "BCOPTER", "player": 1, "x": 9, "y": 8},
            {"type": "TCOPTER", "player": 1, "x": 8, "y": 9},
            {"type": "STEALTH", "player": 1, "x": 7, "y": 7},
            {"type": "BLACKBOMB", "player": 1, "x": 9, "y": 9},
            
            # Add ground units for air-to-ground testing
            {"type": "TANK", "player": 0, "x": 3, "y": 5},
            {"type": "ANTIAIR", "player": 1, "x": 6, "y": 5},
            {"type": "MISSILE", "player": 0, "x": 4, "y": 6},
            {"type": "MISSILE", "player": 1, "x": 5, "y": 6},
        ]
    elif focus == 'land':
        # Comprehensive land units test
        units = [
            # Player 1 (RED) land units
            {"type": "INFANTRY", "player": 0, "x": 1, "y": 4},
            {"type": "MECH", "player": 0, "x": 2, "y": 4},
            {"type": "RECON", "player": 0, "x": 0, "y": 5},
            {"type": "TANK", "player": 0, "x": 1, "y": 5},
            {"type": "MEDIUMTANK", "player": 0, "x": 2, "y": 5},
            {"type": "NEOTANK", "player": 0, "x": 0, "y": 6},
            {"type": "MEGATANK", "player": 0, "x": 1, "y": 6},
            {"type": "ANTIAIR", "player": 0, "x": 2, "y": 6},
            {"type": "ARTILLERY", "player": 0, "x": 0, "y": 7},
            {"type": "ROCKET", "player": 0, "x": 1, "y": 7},
            {"type": "MISSILE", "player": 0, "x": 2, "y": 7},
            {"type": "APC", "player": 0, "x": 0, "y": 8},
            {"type": "PIPERUNNER", "player": 0, "x": 1, "y": 8},
            
            # Player 2 (BLUE) land units
            {"type": "INFANTRY", "player": 1, "x": 8, "y": 4},
            {"type": "MECH", "player": 1, "x": 7, "y": 4},
            {"type": "RECON", "player": 1, "x": 9, "y": 5},
            {"type": "TANK", "player": 1, "x": 8, "y": 5},
            {"type": "MEDIUMTANK", "player": 1, "x": 7, "y": 5},
            {"type": "NEOTANK", "player": 1, "x": 9, "y": 6},
            {"type": "MEGATANK", "player": 1, "x": 8, "y": 6},
            {"type": "ANTIAIR", "player": 1, "x": 7, "y": 6},
            {"type": "ARTILLERY", "player": 1, "x": 9, "y": 7},
            {"type": "ROCKET", "player": 1, "x": 8, "y": 7},
            {"type": "MISSILE", "player": 1, "x": 7, "y": 7},
            {"type": "APC", "player": 1, "x": 9, "y": 8},
            {"type": "PIPERUNNER", "player": 1, "x": 8, "y": 8},
        ]
    elif focus == 'transport_comprehensive':
        # Same as transport_comprehensive from the main function
        units = [
            # Ground transports and their cargo
            {"type": "APC", "player": 0, "x": 0, "y": 4},
            {"type": "INFANTRY", "player": 0, "x": 1, "y": 4},
            {"type": "MECH", "player": 0, "x": 2, "y": 4},
            
            # Air transports and cargo
            {"type": "TCOPTER", "player": 0, "x": 0, "y": 7},
            {"type": "INFANTRY", "player": 0, "x": 1, "y": 7},
            {"type": "MECH", "player": 0, "x": 2, "y": 7},
            
            # Naval transports
            {"type": "LANDER", "player": 0, "x": 0, "y": 1},
            {"type": "BLACKBOAT", "player": 0, "x": 1, "y": 2},
            {"type": "CRUISER", "player": 0, "x": 2, "y": 1},
            {"type": "CARRIER", "player": 0, "x": 3, "y": 2},
            
            # Units that can be loaded on lander
            {"type": "TANK", "player": 0, "x": 0, "y": 3},
            {"type": "RECON", "player": 0, "x": 1, "y": 3},
            {"type": "ARTILLERY", "player": 0, "x": 2, "y": 3},
            
            # Air units for carrier/cruiser
            {"type": "FIGHTER", "player": 0, "x": 3, "y": 0},
            {"type": "BOMBER", "player": 0, "x": 4, "y": 0},
            {"type": "BCOPTER", "player": 0, "x": 3, "y": 1},
            
            # BLUE team transports
            {"type": "APC", "player": 1, "x": 9, "y": 4},
            {"type": "TCOPTER", "player": 1, "x": 9, "y": 7},
            {"type": "LANDER", "player": 1, "x": 9, "y": 1},
            {"type": "BLACKBOAT", "player": 1, "x": 8, "y": 2},
            {"type": "CRUISER", "player": 1, "x": 7, "y": 1},
            {"type": "CARRIER", "player": 1, "x": 6, "y": 2},
            
            # BLUE loadable units
            {"type": "INFANTRY", "player": 1, "x": 8, "y": 4},
            {"type": "MECH", "player": 1, "x": 7, "y": 4},
            {"type": "TANK", "player": 1, "x": 9, "y": 3},
            {"type": "FIGHTER", "player": 1, "x": 6, "y": 0},
            {"type": "BCOPTER", "player": 1, "x": 7, "y": 0},
        ]
    else:
        # Default comprehensive unit set
        units = [
            # Naval units
            {"type": "BATTLESHIP", "player": 0, "x": 3, "y": 0},
            {"type": "CRUISER", "player": 1, "x": 5, "y": 0},
            {"type": "SUB", "player": 0, "x": 1, "y": 1},
            {"type": "LANDER", "player": 1, "x": 7, "y": 1},
            
            # Ground units
            {"type": "INFANTRY", "player": 0, "x": 1, "y": 4},
            {"type": "MECH", "player": 1, "x": 7, "y": 4},
            {"type": "TANK", "player": 0, "x": 3, "y": 5},
            {"type": "RECON", "player": 1, "x": 6, "y": 5},
            {"type": "ARTILLERY", "player": 0, "x": 3, "y": 9},
            {"type": "ROCKET", "player": 1, "x": 6, "y": 9},
            
            # Air units
            {"type": "FIGHTER", "player": 0, "x": 1, "y": 7},
            {"type": "BOMBER", "player": 0, "x": 1, "y": 8},
            {"type": "FIGHTER", "player": 1, "x": 8, "y": 8},
            
            # Special units
            {"type": "BLACKBOAT", "player": 0, "x": 2, "y": 2},
            {"type": "APC", "player": 1, "x": 8, "y": 6},
        ]
    
    # Create units
    for unit_data in units:
        try:
            # Convert player number to army name
            army_name = "RED" if unit_data["player"] == 0 else "BLUE"
            game.unit_create(
                army=army_name,
                unit_type=unit_data["type"],
                x=unit_data["x"],
                y=unit_data["y"]
            )
            
            # For player 1 units on day 1, set them as active so they can be tested immediately
            if unit_data["player"] == 1 and game.board.days == 0:
                tile = game.board.grid[unit_data["y"] * game.board.width + unit_data["x"]]
                if tile and tile.unit:
                    tile.unit.can_move = True
                    tile.unit.can_attack = True
                    tile.unit.can_capture = tile.unit.type_can_capture()
                    tile.unit.has_moved_this_turn = False
                    app_logger.info(f"Setting player 1 {unit_data['type']} as active for day 1 testing")
                    
        except Exception as e:
            app_logger.warning(f"Failed to create {unit_data['type']}: {e}")


def _add_test_units_v2(game, focus: str = None):
    """Add pre-deployed units for v2 GameManager with direct unit placement"""
    from unit import Unit, UnitType
    from config import Config
    
    app_logger.info(f"_add_test_units_v2 called with focus: {focus}")
    
    # Same unit configurations as before but with direct placement
    if focus == 'naval':
        units = [
            # Player 1 (RED) naval units on left side
            {"type": "BATTLESHIP", "player": 0, "x": 0, "y": 1},
            {"type": "CRUISER", "player": 0, "x": 1, "y": 0},
            {"type": "SUB", "player": 0, "x": 2, "y": 1},
            {"type": "LANDER", "player": 0, "x": 0, "y": 2},
            {"type": "CARRIER", "player": 0, "x": 1, "y": 3},
            {"type": "BLACKBOAT", "player": 0, "x": 2, "y": 2},
            
            # Player 2 (BLUE) naval units on right side
            {"type": "BATTLESHIP", "player": 1, "x": 9, "y": 1},
            {"type": "CRUISER", "player": 1, "x": 8, "y": 0},
            {"type": "SUB", "player": 1, "x": 7, "y": 1},
            {"type": "LANDER", "player": 1, "x": 9, "y": 2},
            {"type": "CARRIER", "player": 1, "x": 8, "y": 3},
            {"type": "BLACKBOAT", "player": 1, "x": 7, "y": 2},
            
            # Add some air units for carrier testing
            {"type": "FIGHTER", "player": 0, "x": 1, "y": 4},
            {"type": "BOMBER", "player": 1, "x": 8, "y": 4},
            
            # Add infantry for transport testing
            {"type": "INFANTRY", "player": 0, "x": 0, "y": 4},
            {"type": "MECH", "player": 1, "x": 9, "y": 4},
        ]
    elif focus == 'air':
        units = [
            # Player 1 air units
            {"type": "FIGHTER", "player": 0, "x": 1, "y": 7},
            {"type": "BOMBER", "player": 0, "x": 2, "y": 8},
            {"type": "BCOPTER", "player": 0, "x": 0, "y": 8},
            {"type": "TCOPTER", "player": 0, "x": 1, "y": 9},
            
            # Player 2 air units
            {"type": "FIGHTER", "player": 1, "x": 8, "y": 7},
            {"type": "BOMBER", "player": 1, "x": 7, "y": 8},
            {"type": "BCOPTER", "player": 1, "x": 9, "y": 8},
            {"type": "TCOPTER", "player": 1, "x": 8, "y": 9},
            
            # Add ground units for air-to-ground testing
            {"type": "TANK", "player": 0, "x": 3, "y": 5},
            {"type": "ANTIAIR", "player": 1, "x": 6, "y": 5},
        ]
    elif focus == 'land':
        units = [
            # Player 1 land units
            {"type": "INFANTRY", "player": 0, "x": 1, "y": 4},
            {"type": "MECH", "player": 0, "x": 2, "y": 4},
            {"type": "RECON", "player": 0, "x": 0, "y": 5},
            {"type": "TANK", "player": 0, "x": 1, "y": 5},
            {"type": "MEDIUMTANK", "player": 0, "x": 2, "y": 5},
            {"type": "ANTIAIR", "player": 0, "x": 2, "y": 6},
            {"type": "ARTILLERY", "player": 0, "x": 0, "y": 7},
            {"type": "ROCKET", "player": 0, "x": 1, "y": 7},
            {"type": "APC", "player": 0, "x": 0, "y": 8},
            
            # Player 2 land units
            {"type": "INFANTRY", "player": 1, "x": 8, "y": 4},
            {"type": "MECH", "player": 1, "x": 7, "y": 4},
            {"type": "RECON", "player": 1, "x": 9, "y": 5},
            {"type": "TANK", "player": 1, "x": 8, "y": 5},
            {"type": "MEDIUMTANK", "player": 1, "x": 7, "y": 5},
            {"type": "ANTIAIR", "player": 1, "x": 7, "y": 6},
            {"type": "ARTILLERY", "player": 1, "x": 9, "y": 7},
            {"type": "ROCKET", "player": 1, "x": 8, "y": 7},
            {"type": "APC", "player": 1, "x": 9, "y": 8},
        ]
    elif focus == 'movement':
        # Add movement-focused units
        units = [
            {"type": "INFANTRY", "player": 0, "x": 1, "y": 4},
            {"type": "MECH", "player": 0, "x": 2, "y": 5},
            {"type": "RECON", "player": 0, "x": 0, "y": 5},
            {"type": "TANK", "player": 0, "x": 1, "y": 6},
            {"type": "FIGHTER", "player": 0, "x": 1, "y": 7},
            {"type": "TCOPTER", "player": 0, "x": 0, "y": 8},
            # Player 2 units
            {"type": "RECON", "player": 1, "x": 6, "y": 5},
            {"type": "TANK", "player": 1, "x": 7, "y": 6},
            {"type": "FIGHTER", "player": 1, "x": 8, "y": 7},
            {"type": "TCOPTER", "player": 1, "x": 8, "y": 8},
        ]
    elif focus == 'combat':
        # Add combat-focused units
        units = [
            {"type": "TANK", "player": 0, "x": 3, "y": 5},
            {"type": "ARTILLERY", "player": 0, "x": 3, "y": 7},
            {"type": "FIGHTER", "player": 0, "x": 1, "y": 8},
            {"type": "BATTLESHIP", "player": 0, "x": 3, "y": 0},
            # Player 2 units - positioned for combat
            {"type": "TANK", "player": 1, "x": 5, "y": 5},
            {"type": "ROCKET", "player": 1, "x": 6, "y": 7},
            {"type": "FIGHTER", "player": 1, "x": 8, "y": 8},
            {"type": "CRUISER", "player": 1, "x": 5, "y": 0},
        ]
    elif focus == 'transport':
        # Add transport-focused units
        units = [
            # Ground transports and cargo
            {"type": "APC", "player": 0, "x": 0, "y": 4},
            {"type": "INFANTRY", "player": 0, "x": 1, "y": 4},
            {"type": "MECH", "player": 0, "x": 2, "y": 4},
            # Air transports
            {"type": "TCOPTER", "player": 0, "x": 0, "y": 7},
            {"type": "INFANTRY", "player": 0, "x": 1, "y": 7},
            # Naval transports
            {"type": "LANDER", "player": 0, "x": 0, "y": 1},
            {"type": "BLACKBOAT", "player": 0, "x": 1, "y": 2},
            {"type": "CRUISER", "player": 0, "x": 2, "y": 1},
            {"type": "CARRIER", "player": 0, "x": 3, "y": 2},
            # Cargo for naval
            {"type": "TANK", "player": 0, "x": 0, "y": 3},
            {"type": "FIGHTER", "player": 0, "x": 3, "y": 0},
            {"type": "BCOPTER", "player": 0, "x": 3, "y": 1},
        ]
    else:
        # Default units
        units = [
            {"type": "INFANTRY", "player": 0, "x": 1, "y": 4},
            {"type": "TANK", "player": 0, "x": 3, "y": 5},
            {"type": "INFANTRY", "player": 1, "x": 8, "y": 4},
            {"type": "TANK", "player": 1, "x": 6, "y": 5},
        ]
    
    # Get config for unit stats
    config = Config()
    
    # Create and place units directly on the board
    for unit_data in units:
        try:
            unit_type = UnitType[unit_data["type"]]
            unit_config = config.units[unit_type.name]
            
            # For v2 games, we need to map player ID to Army enum
            # Player 0 = RED, Player 1 = BLUE for test games
            from map_system import Army
            army = Army.RED if unit_data["player"] == 0 else Army.BLUE
            
            # Create unit with proper army
            unit = Unit.create(
                army=army,
                unit_type=unit_type,
                unit_config=unit_config
            )
            
            # For player 1 units on day 1, set them as active so they can be tested immediately
            if unit_data["player"] == 1 and game.board.days == 0:
                unit.can_move = True
                unit.can_attack = True
                unit.can_capture = unit.type_can_capture()
                unit.has_moved_this_turn = False
                app_logger.info(f"Setting player 1 {unit_type.name} as active for day 1 testing")
            
            # Place unit on board
            tile_index = unit_data["y"] * game.board.width + unit_data["x"]
            if 0 <= tile_index < len(game.board.grid):
                game.board.grid[tile_index].unit = unit
                app_logger.info(f"Placed {unit_type.name} at ({unit_data['x']}, {unit_data['y']})")
            
        except Exception as e:
            app_logger.warning(f"Failed to create {unit_data['type']}: {e}")


@unified_test_bp.route('/test_game/list')
def list_test_types():
    """List available test game types and their configurations."""
    return jsonify({
        'types': TEST_CONFIGS,
        'maps': map_repository.list_maps(),
        'usage': {
            'basic': '/test_game',
            'with_type': '/test_game?type=combat',
            'custom_map': '/test_game?type=basic&map=scorpion',
            'force_units': '/test_game?type=basic&units=true'
        }
    })
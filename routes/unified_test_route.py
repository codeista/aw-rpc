"""
Unified test game creation route - consolidates all test game creation into one parameterized endpoint
"""

from flask import Blueprint, request, redirect, url_for, jsonify
import time
from app_core import games
from manager import GameManager
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
        'description': 'Transport operations test',
        'add_units': True,
        'unit_focus': 'transport'
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
        game = GameManager(token)
        game.setup(game_map)
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
    """Add pre-deployed units based on focus area."""
    
    if focus == 'movement':
        # Add movement-focused units
        units = [
            {"type": "INFANTRY", "army": "RED", "x": 1, "y": 4},
            {"type": "MECH", "army": "RED", "x": 2, "y": 5},
            {"type": "RECON", "army": "BLUE", "x": 6, "y": 5},
            {"type": "TANK", "army": "BLUE", "x": 7, "y": 6},
            {"type": "FIGHTER", "army": "RED", "x": 1, "y": 7},
            {"type": "TCOPTER", "army": "BLUE", "x": 8, "y": 8},
        ]
    elif focus == 'combat':
        # Add combat-focused units
        units = [
            {"type": "TANK", "army": "RED", "x": 3, "y": 5},
            {"type": "TANK", "army": "BLUE", "x": 5, "y": 5},
            {"type": "ARTILLERY", "army": "RED", "x": 3, "y": 7},
            {"type": "ROCKET", "army": "BLUE", "x": 6, "y": 7},
            {"type": "FIGHTER", "army": "RED", "x": 1, "y": 8},
            {"type": "FIGHTER", "army": "BLUE", "x": 8, "y": 8},
            {"type": "BATTLESHIP", "army": "RED", "x": 3, "y": 0},
            {"type": "CRUISER", "army": "BLUE", "x": 5, "y": 0},
        ]
    elif focus == 'transport':
        # Add transport-focused units
        units = [
            {"type": "INFANTRY", "army": "RED", "x": 1, "y": 4},
            {"type": "MECH", "army": "RED", "x": 2, "y": 4},
            {"type": "APC", "army": "RED", "x": 3, "y": 4},
            {"type": "LANDER", "army": "BLUE", "x": 7, "y": 1},
            {"type": "TCOPTER", "army": "BLUE", "x": 8, "y": 7},
            {"type": "BLACKBOAT", "army": "RED", "x": 2, "y": 2},
        ]
    elif focus == 'capture':
        # Add units near capturable properties
        units = [
            {"type": "INFANTRY", "army": "RED", "x": 3, "y": 3},  # Near city
            {"type": "MECH", "army": "BLUE", "x": 8, "y": 4},     # Near factory
            {"type": "INFANTRY", "army": "RED", "x": 7, "y": 8},  # Near airport
            {"type": "MECH", "army": "BLUE", "x": 0, "y": 0},     # Near port
        ]
    else:
        # Default comprehensive unit set
        units = [
            # Naval units
            {"type": "BATTLESHIP", "army": "RED", "x": 3, "y": 0},
            {"type": "CRUISER", "army": "BLUE", "x": 5, "y": 0},
            {"type": "SUB", "army": "RED", "x": 1, "y": 1},
            {"type": "LANDER", "army": "BLUE", "x": 7, "y": 1},
            
            # Ground units
            {"type": "INFANTRY", "army": "RED", "x": 1, "y": 4},
            {"type": "MECH", "army": "BLUE", "x": 7, "y": 4},
            {"type": "TANK", "army": "RED", "x": 3, "y": 5},
            {"type": "RECON", "army": "BLUE", "x": 6, "y": 5},
            {"type": "ARTILLERY", "army": "RED", "x": 3, "y": 9},
            {"type": "ROCKET", "army": "BLUE", "x": 6, "y": 9},
            
            # Air units
            {"type": "FIGHTER", "army": "RED", "x": 1, "y": 7},
            {"type": "BOMBER", "army": "RED", "x": 1, "y": 8},
            {"type": "FIGHTER", "army": "BLUE", "x": 8, "y": 8},
            
            # Special units
            {"type": "BLACKBOAT", "army": "RED", "x": 2, "y": 2},
            {"type": "APC", "army": "BLUE", "x": 8, "y": 6},
        ]
    
    # Create units
    for unit_data in units:
        try:
            game.create_unit(
                army=unit_data["army"],
                unit_type=unit_data["type"],
                x=unit_data["x"],
                y=unit_data["y"]
            )
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
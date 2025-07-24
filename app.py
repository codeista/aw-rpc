#!/usr/bin/python3

'''[This is a RPC game engine for Advance wars with enhanced logging - Built on current version]'''

import os
os.environ['TYPEGUARD_DISABLE'] = '1'
import logging
import datetime
import secrets
from functools import wraps
import time
import json
import traceback
import math

import subprocess
import threading

from flask_cors import CORS
from flask import redirect, render_template, abort, request
from flask_socketio import Namespace, join_room, leave_room
import jsons

from tests.debug.optimized_test_map import (
    get_optimized_test_game, 
    create_quick_combat_scenario,
    verify_optimized_map
)
import secrets

from manager import GameManager
from gameboard import GameBoard
from game_factory import GameFactory
from manager_v2 import GameManagerV2
from game_board_v2 import GameBoardV2
from player_system import PlayerManager
from config import Config
from app_core import (
    app, jsonrpc, db, socketio,
    game_management_api, unit_operations_api, combat_system_api,
    transport_system_api, map_tile_api, special_actions_api,
    production_economic_api, information_api, communication_api
)
from models import Game
from map_system import map_repository, Map, Army
from enhanced_combat_system import EnhancedCombatSystem, CombatPreview, EnhancedCombatResult
from transport_system import CompleteTransportSystem, TransportResult
from tests.integration.test_map_predeployed import get_predeployed_test_game, get_comprehensive_test_game
from routes.unified_test_route import unified_test_bp
from routes.unified_test_api import unified_test_api_bp
import api_docs_route  # Import the custom API documentation

# Import the new clean API v2
from api_v2 import GameAPIv2

# Import our fixed logging system
try:
    from logging_config import setup_application_logging, GameEventLogger, PerformanceLogger
    app_logger, game_logger = setup_application_logging()
    game_event_logger = GameEventLogger()
    perf_logger = PerformanceLogger()
    ENHANCED_LOGGING = True
except ImportError:
    # Fallback to your existing logging if new system not available
    app_logger = logging.getLogger(__name__)
    logging.basicConfig(filename='app.log', level=logging.INFO)
    
    game_logger = logging.getLogger('game_events')
    game_logger.setLevel(logging.INFO)
    event_handler = logging.FileHandler('game_events.log')
    event_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    event_handler.setFormatter(event_formatter)
    if not game_logger.handlers:
        game_logger.addHandler(event_handler)
    
    ENHANCED_LOGGING = False

# Initialize the new clean API v2
api_v2 = GameAPIv2(app, jsonrpc)
app_logger.info("Clean API v2 initialized with 8 core methods")

# Blueprint registration disabled - routes implemented directly in app.py
# This avoids Flask's "can't register after first request" error in debug mode
# The test_game route is now implemented directly in this file

from error_handling import (
    setup_error_handlers, setup_logging, validate_rpc_params,
    validate_token, validate_coordinates, validate_army, 
    validate_unit_type, safe_rpc_call, log_game_event, AWRPCError,
    ValidationError, GameStateError, UnitError, MovementError
)

# Enhanced logging decorators
def log_rpc_performance(func):
    """Decorator to log RPC call performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        method_name = func.__name__.replace('_rpc', '')
        
        try:
            app_logger.info(f"RPC_START {method_name} args={args}")
            result = func(*args, **kwargs)
            
            duration_ms = (time.time() - start_time) * 1000
            if ENHANCED_LOGGING:
                perf_logger.log_rpc_call(method_name, duration_ms, True, len(args) + len(kwargs))
            app_logger.info(f"RPC_SUCCESS {method_name} duration={duration_ms:.2f}ms")
            
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            if ENHANCED_LOGGING:
                perf_logger.log_rpc_call(method_name, duration_ms, False, len(args) + len(kwargs))
            app_logger.error(f"RPC_ERROR {method_name} duration={duration_ms:.2f}ms error={str(e)}")
            
            # Log game-specific error if token is provided
            if args and len(args) > 0:
                token = args[0] if isinstance(args[0], str) else "unknown"
                if ENHANCED_LOGGING:
                    game_event_logger.log_error(token, method_name, str(e))
            
            raise
    return wrapper

def log_game_event(event_type, token, details):
    """Enhanced game event logging"""
    if ENHANCED_LOGGING:
        # Use structured logging if available
        if event_type == 'UNIT_CREATED':
            game_event_logger.log_unit_created(token, details.get('army', ''), details.get('unit_type', ''), 
                                             details.get('x', 0), details.get('y', 0), details.get('cost', 0))
        elif event_type == 'UNIT_MOVED':
            game_event_logger.log_unit_moved(token, details.get('army', ''), details.get('unit_type', ''),
                                           details.get('from_pos', (0, 0)), details.get('to_pos', (0, 0)), 
                                           details.get('fuel_used', 0))
        elif event_type == 'PROPERTY_CAPTURED':
            game_event_logger.log_property_captured(token, details.get('army', ''), details.get('property_type', ''),
                                                   details.get('position', (0, 0)))
        else:
            game_logger.info(f"{event_type} | {token} | {json.dumps(details)}")
    else:
        # Fallback to original logging
        game_logger.info(f"{event_type} | {token} | {json.dumps(details)}")

# Map system - use your existing flexible approach
try:
    from map_system import Map, MapType, Army, MapTile
    
    # Create a working map inline
    MAP_DATA = '''RED,BLUE
FACTORY:RED,PLAIN*5,FACTORY:BLUE
PLAIN*7
PLAIN*2,CITY,PLAIN,CITY,PLAIN*2
PLAIN*7
FACTORY:BLUE,PLAIN*5,FACTORY:RED'''
    
    default_map = Map.parse(MAP_DATA)
    app_logger.info("Using map_system for map data")

except ImportError:
    # Use your existing fallback system
    app_logger.warning("Using minimal map system - map_system not available")
    
    class Army:
        RED = 'RED'
        BLUE = 'BLUE'
    
    class MapType:
        PLAIN = 'PLAIN'
        FACTORY = 'FACTORY'
        CITY = 'CITY'
    
    class MapTile:
        def __init__(self, tile_type, army=None):
            self.type = tile_type
            self.army = army
    
    class Map:
        def __init__(self):
            self.width = 7
            self.height = 5
            self.tiles = []
            self.turn_order = [Army.RED, Army.BLUE]
            
            # Create simple 7x5 map
            for y in range(self.height):
                for x in range(self.width):
                    if y == 0 and x == 0:
                        tile = MapTile(MapType.FACTORY, Army.RED)
                    elif y == 0 and x == 6:
                        tile = MapTile(MapType.FACTORY, Army.BLUE)
                    elif y == 4 and x == 0:
                        tile = MapTile(MapType.FACTORY, Army.BLUE)
                    elif y == 4 and x == 6:
                        tile = MapTile(MapType.FACTORY, Army.RED)
                    elif (y == 2 and x == 2) or (y == 2 and x == 4):
                        tile = MapTile(MapType.CITY)
                    else:
                        tile = MapTile(MapType.PLAIN)
                    self.tiles.append(tile)
    
    default_map = Map()

config_game = Config()

#
# Helper functions (Enhanced)
#

def setup_logging(level):
    '''Setup logging.'''
    app_logger.setLevel(level)

def game_load(token):
    '''Loads the game token specified with FIXED deserialization'''
    app_logger.info(f"Loading game: {token}")
    
        # CHECK IN-MEMORY GAMES FIRST
    if token in games:
        app_logger.info(f"Game found in memory: {token}")
        return games[token]
    
    game = Game.from_token(db.session, token)
    if game:
        app_logger.info(f"Game found in database: {token}")
        
        try:
            # CRITICAL FIX: Better handling of board data format
            board_data = game.board
            
            # Convert to dict if it's a string
            if isinstance(board_data, str):
                import json
                board_dict = json.loads(board_data)
                app_logger.debug(f"Parsed JSON string to dict")
            else:
                # It's already a dict (most common case)
                board_dict = board_data
                app_logger.debug(f"Board data is already a dict")
            
            # RECONSTRUCT UNITS: Fix any dict units in the grid
            units_reconstructed = 0
            if 'grid' in board_dict:
                for i, tile_data in enumerate(board_dict['grid']):
                    if isinstance(tile_data, dict) and 'unit' in tile_data and tile_data['unit'] is not None:
                        unit_data = tile_data['unit']
                        
                        # If unit is a dict, reconstruct it
                        if isinstance(unit_data, dict):
                            # Reconstructing unit at grid index {i}
                            try:
                                reconstructed_unit = reconstruct_unit_from_dict(unit_data)
                                tile_data['unit'] = reconstructed_unit
                                units_reconstructed += 1
                                # Successfully reconstructed unit {units_reconstructed}
                            except Exception as unit_error:
                                app_logger.warning(f"Failed to reconstruct unit at index {i}: {unit_error}")
                                # Set unit to None instead of leaving a broken dict
                                tile_data['unit'] = None
            
            app_logger.debug(f"Reconstructed {units_reconstructed} units total")
            
            # Now try to deserialize with jsons - pass the dict directly, not as JSON
            try:
                board = jsons.loads(board_dict, GameBoard)
                app_logger.debug(f"jsons.loads succeeded")
            except Exception as jsons_error:
                app_logger.debug(f"jsons.loads failed: {jsons_error}")
                # Try alternative approach - create GameBoard manually
                board = create_board_from_dict(board_dict)
            
            mngr = GameManager(config_game, board)
            mngr.app_logger = app_logger  # Set logger for income processing
            return mngr
            
        except Exception as e:
            app_logger.error(f"Failed to deserialize game {token}: {str(e)}")
            app_logger.error(f"Error type: {type(e).__name__}")
            app_logger.error(f"Creating new game instead")
            # Fall through to create new game
    
    app_logger.info(f"Creating new game: {token}")   
    # If no game found or deserialization failed, create a new one with default map 
    try:
        default_map = map_repository.get_map('test')
        if not default_map:
            default_map = map_repository.get_map('scorpion')  
    except:
        # Fallback if map system isn't working
        from map_system import Map
        default_map = Map()
    
    board = GameBoard.create(default_map)
    mngr = GameManager(config_game, board)
    mngr.app_logger = app_logger  # Set logger for income processing
    
    # Log game creation
    if ENHANCED_LOGGING:
        game_event_logger.log_game_created(token, len(board.turn_order))
    
    return mngr

def create_board_from_dict(board_dict):
    """
    Fallback method to create GameBoard from dict if jsons.loads fails
    """
    try:
        from gameboard import GameBoard
        from map_system import Army
        
        # Extract basic board properties
        width = board_dict.get('width', 7)
        height = board_dict.get('height', 7)
        
        # Create a new board with the same dimensions
        try:
            default_map = map_repository.get_map('test')
        except:
            from map_system import Map
            default_map = Map()
        
        board = GameBoard.create(default_map)
        
        # CRITICAL FIX: Properly restore turn order and current turn
        if 'turn_order' in board_dict:
            # Convert turn order strings back to Army enums
            turn_order = []
            for army_data in board_dict['turn_order']:
                if isinstance(army_data, str):
                    turn_order.append(Army[army_data])
                elif hasattr(army_data, 'name'):
                    turn_order.append(Army[army_data.name])
                else:
                    turn_order.append(army_data)
            board.turn_order = turn_order
            app_logger.debug(f"Restored turn_order: {[army.name for army in turn_order]}")
        
        if 'current_turn' in board_dict:
            current_turn_data = board_dict['current_turn']
            if isinstance(current_turn_data, str):
                board.current_turn = Army[current_turn_data]
            elif hasattr(current_turn_data, 'name'):
                board.current_turn = Army[current_turn_data.name]
            else:
                board.current_turn = current_turn_data
            app_logger.debug(f"Restored current_turn: {board.current_turn.name}")
        
        # Copy other important properties
        if 'days' in board_dict:
            board.days = board_dict['days']
        if 'game_active' in board_dict:
            board.game_active = board_dict['game_active']
        if 'red_funds' in board_dict:
            board.red_funds = board_dict['red_funds']
        if 'blue_funds' in board_dict:
            board.blue_funds = board_dict['blue_funds']
        
        # Copy army statistics
        if 'total_red_troops' in board_dict:
            board.total_red_troops = board_dict['total_red_troops']
        if 'total_blue_troops' in board_dict:
            board.total_blue_troops = board_dict['total_blue_troops']
        if 'total_red_properties' in board_dict:
            board.total_red_properties = board_dict['total_red_properties']
        if 'total_blue_properties' in board_dict:
            board.total_blue_properties = board_dict['total_blue_properties']
        
        # Copy the reconstructed grid
        if 'grid' in board_dict and len(board_dict['grid']) == len(board.grid):
            for i, tile_data in enumerate(board_dict['grid']):
                if isinstance(tile_data, dict) and 'unit' in tile_data:
                    board.grid[i].unit = tile_data['unit']  # Units should already be reconstructed
        
        app_logger.debug(f"Created board from dict manually with proper turn system")
        return board
        
    except Exception as e:
        app_logger.error(f"Manual board creation failed: {e}")
        app_logger.debug(f"Board dict keys: {list(board_dict.keys()) if isinstance(board_dict, dict) else 'Not a dict'}")
        
        # Final fallback - create completely new board but try to preserve basic state
        try:
            from map_system import Map
            default_map = Map()
            board = GameBoard.create(default_map)
            
            # At least try to preserve the game state
            if isinstance(board_dict, dict):
                if 'days' in board_dict:
                    board.days = board_dict['days']
                if 'game_active' in board_dict:
                    board.game_active = board_dict['game_active']
                if 'red_funds' in board_dict:
                    board.red_funds = board_dict['red_funds']
                if 'blue_funds' in board_dict:
                    board.blue_funds = board_dict['blue_funds']
            
            app_logger.warning(f"Using minimal fallback board")
            return board
        except Exception as e2:
            app_logger.error(f"Even minimal fallback failed: {e2}")
            # Absolute last resort
            from map_system import Map
            return GameBoard.create(Map())

def reconstruct_unit_from_dict(unit_dict: dict):
    """
    CRITICAL FIX: Reconstruct Unit object from dictionary using proper Unit.create method
    """
    try:
        from unit import Unit, UnitType, UnitConfig, UnitClass
        from map_system import Army
        
        # Extract basic data from the serialized dict
        unit_type_name = unit_dict.get('type', 'INFANTRY')
        army_name = unit_dict.get('army', 'RED')
        unit_id = unit_dict.get('id', 'reconstructed')
        status_data = unit_dict.get('status', {})
        
        # Convert string names to enums if needed
        if isinstance(unit_type_name, str):
            unit_type = UnitType[unit_type_name]
        elif hasattr(unit_type_name, 'name'):  # It's already an enum
            unit_type = UnitType[unit_type_name.name]
        else:
            unit_type = unit_type_name
            
        if isinstance(army_name, str):
            army = Army[army_name]
        elif hasattr(army_name, 'name'):  # It's already an enum
            army = Army[army_name.name]
        else:
            army = army_name
        
        # Create UnitConfig (status) from the saved data
        if isinstance(status_data, dict):
            # If status is serialized as dict, reconstruct UnitConfig
            unit_config = UnitConfig(
                cls=UnitClass[status_data.get('cls', 'FOOT')] if isinstance(status_data.get('cls'), str) else status_data.get('cls', UnitClass.FOOT),
                cost=status_data.get('cost', 1000),
                move=status_data.get('move', 3),
                rangemin=status_data.get('rangemin', 1),
                rangemax=status_data.get('rangemax', 1),
                fuel=status_data.get('fuel', 99),
                vision=status_data.get('vision', 2),
                hp=status_data.get('hp', 100),
                ammo=status_data.get('ammo', 99),
                cargo=status_data.get('cargo', [])
            )
        else:
            # If status is already a UnitConfig object, use it
            unit_config = status_data
        
        # Create the Unit object with all required parameters
        unit = Unit(
            army=army,
            type=unit_type,
            status=unit_config,  # This was the missing required parameter!
            id=unit_id,
            can_move=unit_dict.get('can_move', True),
            can_attack=unit_dict.get('can_attack', True), 
            can_capture=unit_dict.get('can_capture', True)
        )
        
        # Successfully reconstructed {unit_type_name} unit with proper status
        return unit
        
    except Exception as e:
        # Enhanced fallback with proper UnitConfig
        app_logger.warning(f"Failed to reconstruct unit from dict: {e}")
        app_logger.debug(f"Unit dict keys: {list(unit_dict.keys()) if isinstance(unit_dict, dict) else 'Not a dict'}")
        
        try:
            # Create a fallback unit with basic UnitConfig
            from unit import Unit, UnitType, UnitConfig, UnitClass
            from map_system import Army
            
            fallback_config = UnitConfig(
                cls=UnitClass.FOOT,
                cost=1000,
                move=3,
                rangemin=1,
                rangemax=1,
                fuel=99,
                vision=2,
                hp=100,
                ammo=99,
                cargo=[]
            )
            
            return Unit(
                army=Army.RED,
                type=UnitType.INFANTRY,
                status=fallback_config,  # Proper UnitConfig
                id='fallback',
                can_move=True,
                can_attack=True,
                can_capture=True
            )
        except Exception as e2:
            app_logger.error(f"Even fallback failed: {e2}")
            raise e2

def game_save(mngr, token):
    '''Saves the current game state'''
    app_logger.info(f"Saving game: {token}")
    
    start_time = time.time()
    try:
        game = Game.from_token(db.session, token)
        if not game:
            game = Game(mngr.board, token)
            app_logger.info(f"Created new game record: {token}")
        else:
            game.update = datetime.datetime.now()
            game.board = jsons.dumps(mngr.board)
            app_logger.debug(f"Updated existing game: {token}")
        
        db.session.add(game)
        db.session.commit()
        
        # Also save to in-memory games dict for immediate access
        games[token] = mngr
        
        duration_ms = (time.time() - start_time) * 1000
        if ENHANCED_LOGGING:
            perf_logger.log_database_operation("game_save", duration_ms, True)
        app_logger.info(f"Game saved successfully: {token} in {duration_ms:.2f}ms")
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        if ENHANCED_LOGGING:
            perf_logger.log_database_operation("game_save", duration_ms, False)
        app_logger.error(f"Failed to save game {token}: {str(e)}")
        raise

def game_delete(token):
    '''Deletes the game token specified.'''
    app_logger.info(f"Deleting game: {token}")
    
    game = Game.from_token(db.session, token)
    if game:
        db.session.delete(game)
        db.session.commit()
        if ENHANCED_LOGGING:
            game_event_logger.log_game_deleted(token)
        app_logger.info(f"Game deleted: {token}")
    else:
        app_logger.warning(f"Attempted to delete non-existent game: {token}")

def game_create(token):
    '''Creates a new game with token specified'''
    app_logger.info(f"Creating game: {token}")
    
    mngr = game_load(token)
    game = Game(mngr.board, token)
    db.session.add(game)
    db.session.commit()
    
    if ENHANCED_LOGGING:
        game_event_logger.log_game_created(token, len(mngr.board.turn_order))
    app_logger.info(f"Game created successfully: {token}")

# =============================================================================
# 🎮 GAME MANAGEMENT RPC METHODS
# =============================================================================

@game_management_api.method('game_create_with_setup')
@log_rpc_performance
def game_create_with_setup(token: str, game_setup: dict) -> str:
    """Create a new game with custom setup parameters
    
    Args:
        token: Unique game identifier
        game_setup: Custom game configuration (funds, map, etc.)
        
    Returns:
        str: Success status message
        
    Example:
        rpc('game_create_with_setup', {
            token: 'customgame',
            game_setup: {funds: 25000, map: 'custom'}
        })
    """
    app_logger.info(f"Creating game with setup: {token}")
    
    from map_system import MapTile
    
    # Get the selected map
    map_id = game_setup['map_id']
    selected_map = map_repository.get_map(map_id)
    
    if not selected_map:
        raise ValueError(f"Map not found: {map_id}")
    
    # Create custom turn order based on player selections
    custom_turn_order = []
    players = game_setup['players']
    
    for player in players:
        army_color = player['color']
        try:
            army_enum = Army[army_color]
            custom_turn_order.append(army_enum)
        except KeyError:
            raise ValueError(f"Invalid army color: {army_color}")
    
    # Create army mapping: original map armies -> selected armies
    original_armies = selected_map.turn_order
    army_mapping = {}
    
    # Map original armies to selected armies based on position
    for i, original_army in enumerate(original_armies):
        if i < len(custom_turn_order):
            army_mapping[original_army] = custom_turn_order[i]
            app_logger.info(f"Army mapping: {original_army.name} -> {custom_turn_order[i].name}")
    
    # Convert tiles to use the new army assignments
    converted_tiles = []
    for tile in selected_map.tiles:
        new_tile = MapTile(type=tile.type, army=tile.army)
        
        # Convert army ownership if this tile has an army
        if tile.army and tile.army in army_mapping:
            new_tile.army = army_mapping[tile.army]
            
        converted_tiles.append(new_tile)
    
    # Create a modified map with custom turn order and converted properties
    custom_map = Map(
        width=selected_map.width,
        height=selected_map.height,
        tiles=converted_tiles,           # Use converted tiles
        turn_order=custom_turn_order,     # Use custom turn order
        name=selected_map.name,
        description=f"Custom game: {selected_map.description}"
    )
    
    # Create GameManager with custom map
    config_game = Config()
    board = GameBoard.create(custom_map)
    mngr = GameManager(config_game, board)
    mngr.app_logger = app_logger  # Set logger for income processing
    
    # Store game setup data in the manager
    mngr._game_setup = game_setup
    
    # Add to games dictionary
    games[token] = mngr
    
    # Create database entry
    game = Game(mngr.board, token)
    db.session.add(game)
    db.session.commit()
    
    if ENHANCED_LOGGING:
        game_event_logger.log_game_created(token, len(mngr.board.turn_order))
    
    app_logger.info(f"Game created with custom setup: {token}, map: {map_id}, turn_order: {[army.name for army in custom_turn_order]}")
    return "ok"

def handle_rpc_error(func_name, token, ex):
    '''Enhanced error handling for RPC methods'''
    error_msg = str(ex)
    app_logger.error(f'RPC Error in {func_name}: {error_msg}')
    app_logger.error(traceback.format_exc())
    
    if ENHANCED_LOGGING and token:
        game_event_logger.log_error(token, func_name, error_msg)
    
    return {"error": error_msg, "success": False}

def check_victory_conditions(mngr, token):
    """Check if game should end due to victory conditions"""
    # Count remaining units by army (dynamic for all armies in turn order)
    army_units = {}
    
    # Initialize count for all armies in the game
    for army in mngr.board.turn_order:
        army_units[army.name] = 0
    
    # Count units for each army
    for tile in mngr.board.grid:
        if tile.unit:
            army_name = tile.unit.army.name
            if army_name in army_units:
                army_units[army_name] += 1
    
    # Log all army unit counts
    unit_counts = ", ".join([f"{army}={count}" for army, count in army_units.items()])
    app_logger.info(f'Victory check: {unit_counts}')
    
    # Check for elimination victory - find armies with 0 units
    armies_with_units = [army for army, count in army_units.items() if count > 0]
    
    # Game ends when only one army has units remaining
    if len(armies_with_units) == 1:
        winner = armies_with_units[0]
        mngr.board.game_active = False
        mngr.board.winner = winner
        mngr.board.victory_type = 'ELIMINATION'
        app_logger.info(f'GAME ENDED: {winner} wins by elimination')
        return {'victory': True, 'winner': winner, 'type': 'ELIMINATION'}
    elif len(armies_with_units) == 0:
        # Edge case: all armies eliminated simultaneously (draw)
        mngr.board.game_active = False
        mngr.board.winner = 'DRAW'
        mngr.board.victory_type = 'ELIMINATION'
        app_logger.info('GAME ENDED: Draw - all armies eliminated')
        return {'victory': True, 'winner': 'DRAW', 'type': 'ELIMINATION'}
    
    # Check for HQ capture victory (if implemented)
    # ... additional victory conditions
    
    return {'victory': False}

#
# REST Routes (Enhanced)
#

@app.route('/')
def index():
    app_logger.info("Landing page accessed")
    return render_template('index.html')

@app.route('/api/maps', methods=['GET'])
def get_available_maps():
    """API endpoint to get available maps"""
    try:
        maps = map_repository.list_maps()
        map_data = []
        
        for map_id in maps:
            map_obj = map_repository.get_map(map_id)
            if map_obj:
                # Handle turn_order safely
                armies = []
                if hasattr(map_obj, 'turn_order') and map_obj.turn_order:
                    armies = [army.name for army in map_obj.turn_order]
                elif hasattr(map_obj, 'armies') and map_obj.armies:
                    armies = [army.name for army in map_obj.armies]
                
                map_data.append({
                    'id': map_id,
                    'name': map_obj.name,
                    'width': map_obj.width,
                    'height': map_obj.height,
                    'armies': armies,
                    'turn_order': armies  # Add turn_order field for backward compatibility
                })
        
        return {'success': True, 'maps': map_data}
    except Exception as e:
        app_logger.error(f"Error getting maps: {str(e)}")
        return {'success': False, 'error': str(e)}

@app.route('/api/create_game', methods=['POST'])
def create_game_api():
    """API endpoint for creating a new game with setup parameters"""
    try:
        data = request.get_json()
        
        # Generate game token
        token = secrets.token_urlsafe(4)
        
        # Validate required fields
        required_fields = ['map', 'playerCount', 'turnLimit', 'players']
        for field in required_fields:
            if field not in data:
                return {'success': False, 'error': f'Missing required field: {field}'}
        
        # Validate player setup
        players = data['players']
        if len(players) != data['playerCount']:
            return {'success': False, 'error': 'Player count mismatch'}
        
        # Check for duplicate colors
        colors = [p['color'] for p in players if p['color']]
        if len(colors) != len(set(colors)):
            return {'success': False, 'error': 'Duplicate army colors selected'}
        
        # Check all players have CO and color
        for i, player in enumerate(players):
            if not player.get('co'):
                return {'success': False, 'error': f'Player {i+1} must select a CO'}
            if not player.get('color'):
                return {'success': False, 'error': f'Player {i+1} must select an army color'}
        
        # Store game setup data (we'll extend this later)
        game_setup = {
            'token': token,
            'map_id': data['map'],
            'player_count': data['playerCount'],
            'turn_limit': data['turnLimit'],
            'game_mode': data.get('gameMode', 'standard'),
            'players': players
        }
        
        # Create the game with the selected map
        game_create_with_setup(token, game_setup)
        
        app_logger.info(f"Game created with setup: {token}, map: {data['map']}, players: {data['playerCount']}")
        
        return {'success': True, 'token': token}
        
    except Exception as e:
        app_logger.error(f"Error creating game: {str(e)}")
        return {'success': False, 'error': str(e)}

@app.route('/game/v2/<game_id>')
def game_v2(game_id: str):
    """New clean v2 game interface"""
    return render_template('game_v2.html', game_id=game_id)

@app.route('/game/v2')
def game_v2_new():
    """Create new v2 game"""
    return render_template('game_v2.html')

@app.route('/game/<token>')
def game(token: str):
    app_logger.info(f"Game page accessed: {token}")
    return render_template('render_minimal.html', token=token)

@app.route('/game2x/<token>')
def game_2x(token: str):
    app_logger.info(f"Game 2x page accessed: {token}")
    return render_template('render_2x.html', token=token)

@app.route('/templates/<path:filename>')
def serve_template_files(filename):
    """Serve files from templates directory for sprite corrections"""
    from flask import send_from_directory
    return send_from_directory('templates', filename)

@app.route('/logs')
def view_logs():
    """Enhanced log viewer"""
    try:
        logs = []
        
        # Try to read from enhanced logs first
        if os.path.exists('logs/game_events.log'):
            with open('logs/game_events.log', 'r') as f:
                lines = f.readlines()
            logs.extend([('GAME', line.strip()) for line in lines[-25:]])
        
        # Fallback to original logs
        if os.path.exists('game_events.log'):
            with open('game_events.log', 'r') as f:
                lines = f.readlines()
            logs.extend([('EVENT', line.strip()) for line in lines[-25:]])
        
        if not logs:
            return '<h2>No logs found</h2><p>Logs will appear here once the application starts generating events.</p>'
        
        # Format logs nicely
        formatted_logs = []
        for log_type, line in logs[-50:]:  # Show last 50 entries
            formatted_logs.append(f'<div class="{log_type.lower()}">[{log_type}] {line}</div>')
        
        return f'''
        <html>
        <head>
            <title>AW-RPC Logs</title>
            <style>
                body {{ font-family: monospace; margin: 20px; }}
                .game {{ color: blue; }}
                .event {{ color: green; }}
                .error {{ color: red; }}
                div {{ margin: 2px 0; }}
            </style>
        </head>
        <body>
            <h2>AW-RPC Recent Logs</h2>
            <div>{''.join(formatted_logs)}</div>
            <br><a href="/">Back to Game</a>
        </body>
        </html>
        '''
    except Exception as e:
        app_logger.error(f"Error viewing logs: {e}")
        return f'<h2>Error reading logs</h2><p>{str(e)}</p>'

@app.route('/debug/methods')
def debug_methods():
    '''Enhanced debug endpoint'''
    try:
        methods_info = {
            'enhanced_logging': ENHANCED_LOGGING,
            'map_system': 'map_repository' in globals(),
            'total_methods': 0,
            'registered_methods': []
        }
        
        # Add map system details if available
        if 'map_repository' in globals():
            try:
                methods_info['map_system_details'] = {
                    'available_maps': map_repository.list_maps(),
                    'map_count': len(map_repository.list_maps()),
                    'test_map_available': map_repository.get_map('test') is not None
                }
            except Exception as e:
                methods_info['map_system_error'] = str(e)
        
        if hasattr(jsonrpc, 'jsonrpc_site'):
            site = jsonrpc.jsonrpc_site
            if hasattr(site, 'view_funcs'):
                methods = list(site.view_funcs.keys())
                methods_info['registered_methods'] = methods
                methods_info['total_methods'] = len(methods)
        
        return methods_info
    except Exception as e:
        return {'error': str(e)}

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
    
@app.route('/test')
def create_terrain_test_game():
    """Create terrain-focused test game with predeployed units"""
    token = secrets.token_urlsafe(6)
    try:
        game_manager = get_predeployed_test_game(token)
        games[token] = game_manager
        app_logger.info(f"Created terrain test game: {token}")
        return redirect(f'/game/{token}')
    except Exception as e:
        app_logger.error(f"Failed to create terrain test game: {e}")
        return f"Error creating test game: {e}", 500

@app.route('/test_comprehensive')  
def create_comprehensive_test():
    """Create comprehensive test game with all unit types"""
    token = secrets.token_urlsafe(6)
    try:
        game_manager = get_comprehensive_test_game(token)
        games[token] = game_manager
        app_logger.info(f"Created comprehensive test game: {token}")
        return redirect(f'/game/{token}')
    except Exception as e:
        app_logger.error(f"Failed to create comprehensive test game: {e}")
        return f"Error creating comprehensive test game: {e}", 500

@app.route('/test_movement')  
def test_movement_scenario():
    """Create a game specifically for movement testing"""
    token = secrets.token_urlsafe(6)
    
    try:
        game_manager = get_predeployed_test_game(token)
        board = game_manager.board

        from unit import Unit, UnitType
        from config import Config
        from map_system import Army  # ← This was missing!
        
        # Clear most BLUE units for easier testing
        for tile in board.grid:
            if tile.unit and tile.unit.army == Army.BLUE:
                tile.unit = None
        
        # Place a few RED units in strategic positions for movement testing
        from unit import Unit, UnitType
        from config import Config
        from map_system import Army
        
        config_game = Config()
        
        test_units = [
            {'type': UnitType.INFANTRY, 'x': 1, 'y': 1},
            {'type': UnitType.RECON, 'x': 3, 'y': 3},
            {'type': UnitType.TANK, 'x': 5, 'y': 5}
        ]
        
        for unit_data in test_units:
            # Clear the tile first
            tile_index = unit_data['y'] * board.width + unit_data['x']
            if tile_index < len(board.grid):
                board.grid[tile_index].unit = None
                
                # Get proper unit config and create unit
                unit_config = config_game.units[unit_data['type'].name]
                unit = Unit.create(Army.RED, unit_data['type'], unit_config)
                unit.can_move = True
                unit.can_attack = True
                board.grid[tile_index].unit = unit
        
        games[token] = game_manager
        app_logger.info(f"Created movement test game: {token}")
        return redirect(f'/game/{token}')
        
    except Exception as e:
        app_logger.error(f"Failed to create movement test game: {e}")
        return f"Error creating movement test game: {e}", 500

@app.route('/test_combat')
def create_combat_test():
    """Create a game with units positioned for immediate combat"""
    token = secrets.token_urlsafe(6)
    
    try:
        from unit import Unit, UnitType
        from config import Config
        from map_system import Army
        
        game_manager = get_predeployed_test_game(token)
        board = game_manager.board
        
        # Set up combat scenario
        center_x, center_y = board.width // 2, board.height // 2
        
        # Clear center area and place opposing units
        config_game = Config()
        
        # RED tank
        red_tank_config = config_game.units[UnitType.TANK.name]
        red_tank = Unit.create(Army.RED, UnitType.TANK, red_tank_config)
        tile_index = center_y * board.width + (center_x - 1)
        board.grid[tile_index].unit = red_tank
        
        # BLUE tank (adjacent)
        blue_tank_config = config_game.units[UnitType.TANK.name]
        blue_tank = Unit.create(Army.BLUE, UnitType.TANK, blue_tank_config)
        tile_index = center_y * board.width + (center_x + 1)
        board.grid[tile_index].unit = blue_tank
        
        games[token] = game_manager
        app_logger.info(f"Created combat test game: {token}")
        return redirect(f'/game/{token}')
        
    except Exception as e:
        app_logger.error(f"Failed to create combat test game: {e}")
        return f"Error creating combat test game: {e}", 500

@app.route('/test_info')
def test_info():
    """Show information about available test games"""
    return '''
    <html>
    <head><title>AW-RPC Test Games</title></head>
    <body>
        <h1>🎮 Available Test Games</h1>
        <p><a href="/test">🏔️ Terrain Test Game</a></p>
        <p><a href="/test_comprehensive">🌍 Comprehensive Test</a></p>
        <p><a href="/test_combat">⚔️ Combat Test Game</a></p>
        <p><a href="/test_movement">🏃 Movement Test Game</a></p>
        <p><a href="/test_interface">🧪 Complete Testing Interface</a></p>
        <p><a href="/">🎲 New Game Setup</a></p>
    </body>
    </html>
    '''

@app.route('/test_interface')
def test_interface():
    """Complete testing interface with all testing tools"""
    app_logger.info("Test interface accessed")
    return render_template('test_interface.html')


@app.route('/test_game')
def test_game():
    """Direct implementation of unified test game creation (replaces blueprint route)"""
    # Get query parameters
    test_type = request.args.get('type', 'basic')
    custom_map = request.args.get('map')
    force_units = request.args.get('units', '').lower() == 'true'
    
    # Generate token
    token = secrets.token_urlsafe(8)
    
    try:
        # Create game based on type
        if test_type == 'comprehensive' or (test_type == 'basic' and force_units):
            mngr = get_comprehensive_test_game(token)
        elif test_type == 'movement':
            # Use optimized test for movement
            from tests.debug.optimized_test_map import get_optimized_test_game
            mngr = get_optimized_test_game(token)
        else:
            # Basic test game
            mngr = get_predeployed_test_game(token)
        
        if mngr:
            games[token] = mngr
            app_logger.info(f"Created test game '{token}' with type '{test_type}'")
            return redirect(f'/game/{token}')
        else:
            return "Failed to create test game", 500
            
    except Exception as e:
        app_logger.error(f"Test game creation failed: {e}")
        return f"Error creating test game: {str(e)}", 500

@app.route('/sprites')
def sprite_showcase():
    """Sprite showcase page to view all unit sprites"""
    app_logger.info("Sprite showcase accessed")
    return render_template('sprite_showcase.html')


@app.route('/tile_optimization_test')
def tile_optimization_test():
    """Tile optimization comparison page"""
    app_logger.info("Tile optimization test accessed")
    return render_template('tile_optimization_test.html')


@app.route('/tiles')
def tile_showcase():
    """Tile showcase page to view all map tiles"""
    app_logger.info("Tile showcase accessed")
    return render_template('tile_showcase.html')


@app.route('/api/test_create_custom_game', methods=['POST'])
def test_create_custom_game():
    """API endpoint for test interface to create custom games"""
    try:
        app_logger.info("Test interface: Custom game creation request received")
        
        data = request.get_json()
        app_logger.info(f"Test interface: Request data: {data}")
        
        # Default test setup if no data provided
        if not data:
            data = {
                'map': 'test',
                'playerCount': 2,
                'turnLimit': 50,
                'gameMode': 'standard',
                'players': [
                    {'slot': 1, 'co': 'andy', 'color': 'RED', 'name': 'Player 1'},
                    {'slot': 2, 'co': 'max', 'color': 'BLUE', 'name': 'Player 2'}
                ]
            }
        
        # Generate test token
        token = f"test_{secrets.token_urlsafe(4)}"
        app_logger.info(f"Test interface: Generated token: {token}")
        
        # Create game setup
        game_setup = {
            'token': token,
            'map_id': data['map'],
            'player_count': data['playerCount'],
            'turn_limit': data['turnLimit'],
            'game_mode': data.get('gameMode', 'standard'),
            'players': data['players']
        }
        
        # Create the game
        app_logger.info(f"Test interface: Creating game with setup: {game_setup}")
        game_create_with_setup(token, game_setup)
        
        app_logger.info(f"Test interface: Successfully created game: {token}")
        
        return {
            'success': True, 
            'token': token,
            'game_url': f'/game/{token}',
            'setup': game_setup
        }
        
    except Exception as e:
        app_logger.error(f"Test interface: Error creating test game: {str(e)}")
        import traceback
        app_logger.error(f"Test interface: Full traceback: {traceback.format_exc()}")
        return {'success': False, 'error': str(e)}

@app.route('/api/test_connection', methods=['GET'])
def test_connection():
    """Simple test endpoint to verify server connectivity"""
    return {'success': True, 'message': 'Server is reachable', 'timestamp': datetime.datetime.now().isoformat()}

@app.route('/api/server_logs', methods=['GET'])
def get_server_logs():
    """Get recent server logs for test interface synchronization"""
    try:
        lines = request.args.get('lines', 50, type=int)  # Default to 50 lines
        log_type = request.args.get('type', 'app')  # app, game, or errors
        
        log_files = {
            'app': 'logs/awrpc_app.log',
            'game': 'logs/game_events.log', 
            'errors': 'logs/awrpc_errors.log'
        }
        
        log_file = log_files.get(log_type, 'logs/awrpc_app.log')
        
        if not os.path.exists(log_file):
            return {'success': False, 'error': f'Log file {log_file} not found'}
        
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
        return {
            'success': True,
            'logs': [line.strip() for line in recent_lines],
            'total_lines': len(all_lines),
            'showing_lines': len(recent_lines),
            'log_type': log_type,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        app_logger.error(f"Error reading server logs: {str(e)}")
        return {'success': False, 'error': str(e)}

@app.route('/api/test-status')
def test_status():
    """Get current test framework status"""
    try:
        return json.dumps({
            'status': 'ready',
            'totalTests': 35,
            'framework': 'Enhanced Testing Suite v2.0',
            'categories': {
                'movement': 12,
                'transport': 10, 
                'capture': 8,
                'basic': 5
            },
            'lastRun': None
        })
    except Exception as e:
        return json.dumps({'error': str(e)})

# Replace your @app.route('/api/run-tests') function with this improved version:

@app.route('/api/run-tests')
def run_tests():
    """Run the complete unittest suite"""
    try:
        print("🧪 Running complete test suite...")
        
        result = subprocess.run([
            'python', '-m', 'unittest', 'test_unittest.py', '-v'
        ], capture_output=True, text=True, timeout=120)
        
        # Parse unittest output more carefully
        output_lines = result.stdout.split('\n')
        
        # Count test results
        passed_tests = 0
        failed_tests = 0
        total_tests = 0
        test_details = []
        
        # Look for test result lines
        for line in output_lines:
            if ' ... ok' in line:
                passed_tests += 1
                test_name = line.split(' (')[0].strip()
                test_details.append({'name': test_name, 'status': 'PASS'})
            elif ' ... FAIL' in line or ' ... ERROR' in line:
                failed_tests += 1
                test_name = line.split(' (')[0].strip()
                test_details.append({'name': test_name, 'status': 'FAIL'})
        
        total_tests = passed_tests + failed_tests
        
        # Look for final summary line like "Ran 35 tests in 3.930s"
        for line in output_lines:
            if line.startswith('Ran ') and ' tests in ' in line:
                import re
                match = re.search(r'Ran (\d+) tests', line)
                if match:
                    total_tests = int(match.group(1))
                    print(f"📊 Found summary: {total_tests} total tests")
                break
        
        # If we found the summary but no individual results, assume all passed if OK
        if total_tests > 0 and passed_tests == 0 and failed_tests == 0:
            if result.returncode == 0 and 'OK' in result.stdout:
                passed_tests = total_tests
                failed_tests = 0
                print(f"✅ All {total_tests} tests passed (based on OK status)")
            else:
                failed_tests = total_tests
                passed_tests = 0
                print(f"❌ All {total_tests} tests failed (based on error status)")
        
        # Fallback: if we still have no test count, use your known count
        if total_tests == 0:
            total_tests = 35
            if result.returncode == 0:
                passed_tests = 35
                failed_tests = 0
            else:
                passed_tests = 0
                failed_tests = 35
            print(f"📊 Using fallback: {total_tests} tests, return code: {result.returncode}")
        
        success_rate = round((passed_tests / total_tests * 100), 1) if total_tests > 0 else 0
        
        response_data = {
            'success': result.returncode == 0,
            'totalTests': total_tests,
            'passedTests': passed_tests,
            'failedTests': failed_tests,
            'successRate': success_rate,
            'output': result.stdout[:2000],  # First 2000 chars
            'errors': result.stderr[:1000] if result.stderr else None,
            'testDetails': test_details[:10],  # First 10 test details
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✅ Test API response: {passed_tests}/{total_tests} passed ({success_rate}%)")
        return json.dumps(response_data)
        
    except subprocess.TimeoutExpired:
        return json.dumps({
            'error': 'Tests timed out after 120 seconds',
            'success': False,
            'totalTests': 35,
            'passedTests': 0,
            'failedTests': 35
        })
    except Exception as e:
        print(f"❌ Test API error: {e}")
        return json.dumps({
            'error': str(e),
            'success': False,
            'totalTests': 35,
            'passedTests': 0,
            'failedTests': 35
        })

@app.route('/api/run-test-category/<category>')
def run_test_category(category):
    """Run tests for a specific category"""
    try:
        category_mapping = {
            'basic': 'Test_RPC_unit_create',
            'movement': 'Test_Enhanced_Movement_System',
            'transport': 'Test_Enhanced_Transport_System', 
            'capture': 'Test_Enhanced_Capture_System'
        }
        
        if category not in category_mapping:
            return json.dumps({'error': f'Unknown category: {category}'})
        
        test_class = category_mapping[category]
        
        print(f"🧪 Running {category} tests...")
        
        result = subprocess.run([
            'python', '-m', 'unittest', f'test_unittest.{test_class}', '-v'
        ], capture_output=True, text=True, timeout=60)
        
        # Parse results
        passed = result.stdout.count('... ok')
        failed = result.stdout.count('... FAIL') + result.stdout.count('... ERROR')
        total = passed + failed
        
        response_data = {
            'success': result.returncode == 0,
            'category': category,
            'totalTests': total,
            'passedTests': passed,
            'failedTests': failed,
            'output': result.stdout,
            'errors': result.stderr if result.stderr else None,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✅ {category} tests: {passed}/{total} passed")
        return json.dumps(response_data)
        
    except Exception as e:
        print(f"❌ Category test error: {e}")
        return json.dumps({
            'error': str(e),
            'success': False,
            'category': category
        })

@app.route('/api/quick-test')
def quick_test():
    """Run a quick validation test"""
    try:
        print("⚡ Running quick validation...")
        
        # Run just one basic test
        result = subprocess.run([
            'python', '-m', 'unittest', 'test_unittest.Test_RPC_unit_create.test_unit_create', '-v'
        ], capture_output=True, text=True, timeout=30)
        
        success = result.returncode == 0
        
        response_data = {
            'success': success,
            'testName': 'Quick Unit Creation Test',
            'output': result.stdout,
            'errors': result.stderr if result.stderr else None,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"⚡ Quick test: {'PASSED' if success else 'FAILED'}")
        return json.dumps(response_data)
        
    except Exception as e:
        print(f"❌ Quick test error: {e}")
        return json.dumps({
            'error': str(e),
            'success': False
        })

# === ADD THESE ROUTES TO YOUR app.py ===

@app.route('/test_optimized')
def create_optimized_test_game():
    """Create the ultimate test game with all mechanics ready"""
    token = secrets.token_urlsafe(6)
    
    try:
        # Import everything we need explicitly
        from config import Config
        from manager import GameManager
        from tests.debug.optimized_test_map import create_optimized_test_map
        
        # Create configuration
        config_game = Config()
        app_logger.debug(f"Config created: {type(config_game)}")
        
        # Create the optimized board
        board = create_optimized_test_map()
        app_logger.debug(f"Board created: {type(board)}")
        
        # Create game manager with proper parameters
        game_manager = GameManager(config_game, board)
        game_manager.app_logger = app_logger  # Set logger for income processing
        app_logger.debug(f"GameManager created: {type(game_manager)}")
        
        # Set game properties
        game_manager.board.game_active = True
        game_manager.board.current_turn = Army.RED
        
        # Store in games dict
        games[token] = game_manager
        
        app_logger.info(f"Created optimized test game: {token}")
        
        # Log what's available for testing
        app_logger.info("🎮 OPTIMIZED TEST GAME CREATED!")
        app_logger.info("   ⚔️ Combat: Units positioned for immediate attacks")
        app_logger.info("   🚢 Transport: Loaded transports ready to unload")
        app_logger.info("   🏰 Capture: Infantry next to neutral cities")
        app_logger.info("   💰 Economy: 50,000 funds each army")
        app_logger.info("   🎯 All unit types: Naval, air, land units deployed")
        
        return redirect(f'/game/{token}')
    
    except Exception as e:
        # Enhanced error reporting
        import traceback
        error_details = traceback.format_exc()
        app_logger.error(f"Failed to create optimized test game: {e}")
        app_logger.error(f"Full traceback: {error_details}")
        
        # Return detailed error page
        return f"""
        <h2>❌ Error Creating Optimized Test Game</h2>
        <p><strong>Error:</strong> {e}</p>
        <p><strong>Error Type:</strong> {type(e).__name__}</p>
        <h3>Debug Information:</h3>
        <pre>{error_details}</pre>
        <h3>Troubleshooting:</h3>
        <ul>
            <li><a href="/test_verify">Test Map Verification</a></li>
            <li><a href="/debug">View Active Games</a></li>
            <li>Check server console for detailed logs</li>
        </ul>
        <p><a href="/">Back to Home</a></p>
        """, 500


@app.route('/test_transport')
def create_transport_test_game():
    """Create game focused on transport and cargo mechanics"""
    token = secrets.token_urlsafe(6)
    
    try:
        # Create optimized game and modify for transport focus
        game_manager = get_optimized_test_game(token)
        board = game_manager.board
        
        # Clear some units to focus on transports
        transport_focus_tiles = []
        for tile in board.grid:
            if tile.unit and hasattr(tile.unit, 'cargo') and len(tile.unit.cargo) > 0:
                transport_focus_tiles.append(tile)
        
        games[token] = game_manager
        app_logger.info(f"Created transport test game: {token}")
        
        print("🚢 TRANSPORT TEST GAME CREATED!")
        print(f"   📦 {len(transport_focus_tiles)} loaded transports ready")
        print("   🏖️ Beach landing zones available")
        print("   🚁 Naval and land transport options")
        print("   📋 Test: Load/unload, transport movement, cargo protection")
        
        return redirect(f'/game/{token}')
    
    except Exception as e:
        app_logger.error(f"Failed to create transport test game: {e}")
        return f"Error creating transport test game: {e}", 500

@app.route('/test_capture')
def create_capture_test_game():
    """Create game focused on property capture mechanics"""
    token = secrets.token_urlsafe(6)
    
    try:
        # Create optimized game
        game_manager = get_optimized_test_game(token)
        board = game_manager.board
        
        # Count capture opportunities
        capture_opportunities = 0
        neutral_buildings = 0
        
        for tile in board.grid:
            if tile.mapTile.is_capturable():
                if not tile.mapTile.army:  # Neutral
                    neutral_buildings += 1
                
                # Check for nearby infantry
                for check_tile in board.grid:
                    if (check_tile.unit and 
                        check_tile.unit.type in [UnitType.INFANTRY, UnitType.MECH] and
                        abs(check_tile.x - tile.x) + abs(check_tile.y - tile.y) <= 1):
                        capture_opportunities += 1
                        break
        
        games[token] = game_manager
        app_logger.info(f"Created capture test game: {token}")
        
        print("🏰 CAPTURE TEST GAME CREATED!")
        print(f"   📊 {capture_opportunities} immediate capture opportunities")
        print(f"   🏛️ {neutral_buildings} neutral buildings available")
        print("   👥 Infantry positioned next to key buildings")
        print("   📋 Test: Capture mechanics, income generation, property control")
        
        return redirect(f'/{token}')
    
    except Exception as e:
        app_logger.error(f"Failed to create capture test game: {e}")
        return f"Error creating capture test game: {e}", 500

@app.route('/test_triangle')
def create_triangle_map_game():
    """Create 3-player triangle map game"""
    token = secrets.token_urlsafe(6)
    
    try:
        from manager import GameManager
        from config import Config
        from map_system import map_repository
        
        # Load configuration and triangle map
        config_game = Config()
        triangle_map = map_repository.get_map('triangle')
        
        if not triangle_map:
            return "Triangle map not found", 500
        
        # Create GameBoard from Map
        from gameboard import GameBoard
        board = GameBoard.create(triangle_map)
        
        app_logger.debug(f"Triangle: Map {triangle_map.name}, size {triangle_map.width}x{triangle_map.height}, armies: {[a.name for a in triangle_map.turn_order]}")
        
        # Create game manager
        game_manager = GameManager(config_game, board)
        game_manager.app_logger = app_logger  # Set logger for income processing
        board.game_active = True
        board.current_turn = Army.RED
        
        games[token] = game_manager
        app_logger.info(f"Created triangle map game: {token}")
        
        return redirect(f'/game/{token}')
    
    except Exception as e:
        app_logger.error(f"Failed to create triangle map game: {e}")
        return f"Error creating triangle map game: {e}", 500

@app.route('/test_cross')
def create_cross_map_game():
    """Create 4-player cross map game"""
    token = secrets.token_urlsafe(6)
    
    try:
        from manager import GameManager
        from config import Config
        from map_system import map_repository
        
        # Load configuration and cross map
        config_game = Config()
        cross_map = map_repository.get_map('cross')
        
        if not cross_map:
            return "Cross map not found", 500
        
        # Create GameBoard from Map
        from gameboard import GameBoard
        board = GameBoard.create(cross_map)
        
        app_logger.debug(f"Cross: Map {cross_map.name}, size {cross_map.width}x{cross_map.height}, armies: {[a.name for a in cross_map.turn_order]}")
        
        # Create game manager
        game_manager = GameManager(config_game, board)
        game_manager.app_logger = app_logger  # Set logger for income processing
        board.game_active = True
        board.current_turn = Army.RED
        
        games[token] = game_manager
        app_logger.info(f"Created cross map game: {token}")
        
        return redirect(f'/game/{token}')
    
    except Exception as e:
        app_logger.error(f"Failed to create cross map game: {e}")
        return f"Error creating cross map game: {e}", 500

@app.route('/test_pentagon')
def create_pentagon_map_game():
    """Create 5-player pentagon map game"""
    token = secrets.token_urlsafe(6)
    
    try:
        from manager import GameManager
        from config import Config
        from map_system import map_repository
        
        # Load configuration and pentagon map
        config_game = Config()
        pentagon_map = map_repository.get_map('pentagon')
        
        if not pentagon_map:
            return "Pentagon map not found", 500
        
        # Create GameBoard from Map
        from gameboard import GameBoard
        board = GameBoard.create(pentagon_map)
        
        app_logger.debug(f"Pentagon: Map {pentagon_map.name}, size {pentagon_map.width}x{pentagon_map.height}, armies: {[a.name for a in pentagon_map.turn_order]}")
        
        # Create game manager
        game_manager = GameManager(config_game, board)
        game_manager.app_logger = app_logger  # Set logger for income processing
        board.game_active = True
        board.current_turn = Army.RED
        
        games[token] = game_manager
        app_logger.info(f"Created pentagon map game: {token}")
        
        return redirect(f'/game/{token}')
    
    except Exception as e:
        app_logger.error(f"Failed to create pentagon map game: {e}")
        return f"Error creating pentagon map game: {e}", 500

@app.route('/test_verify')
def verify_test_maps():
    """Verify that all test maps are working correctly"""
    try:
        verify_optimized_map()
        
        return """
        <h2>🔍 Test Map Verification Complete</h2>
        <p>✅ All test maps verified and ready for use</p>
        <h3>Available Test Games:</h3>
        <ul>
            <li><a href="/test_optimized">🎮 Complete Mechanics Test</a> - All features in one map</li>
            <li><a href="/test_combat">⚔️ Combat Focused Test</a> - Quick combat scenarios</li>
            <li><a href="/test_transport">🚢 Transport Test</a> - Cargo and transport mechanics</li>
            <li><a href="/test_capture">🏰 Capture Test</a> - Property capture scenarios</li>
        </ul>
        <h3>Testing Features Available:</h3>
        <ul>
            <li>✅ Units positioned for immediate combat</li>
            <li>✅ Loaded transports (naval and land)</li>
            <li>✅ Infantry next to capturable buildings</li>
            <li>✅ All unit types represented</li>
            <li>✅ Multiple terrain types</li>
            <li>✅ Balanced economies (50k funds each)</li>
        </ul>
        <p><a href="/debug">View All Active Games</a></p>
        """
    
    except Exception as e:
        return f"<h2>❌ Test Map Verification Failed</h2><p>Error: {e}</p>"
    
# === ENHANCED GAME DEBUGGING ===

@app.route('/debug_detailed/<token>')
def debug_game_detailed(token):
    """Provide detailed debugging info for a specific game"""
    if token not in games:
        return f"Game {token} not found", 404
    
    game_manager = games[token]
    board = game_manager.board
    
    # Analyze the game state
    unit_analysis = {}
    combat_pairs = []
    capture_opportunities = []
    loaded_transports = []
    
    for tile in board.grid:
        if tile.unit:
            army = tile.unit.army.name
            unit_type = tile.unit.type.name
            
            if army not in unit_analysis:
                unit_analysis[army] = {}
            unit_analysis[army][unit_type] = unit_analysis[army].get(unit_type, 0) + 1
            
            # Check for loaded transports
            if hasattr(tile.unit, 'cargo') and len(tile.unit.cargo) > 0:
                loaded_transports.append({
                    'type': unit_type,
                    'position': f"({tile.x},{tile.y})",
                    'cargo_count': len(tile.unit.cargo),
                    'cargo_types': [cargo.type.name for cargo in tile.unit.cargo]
                })
            
            # Check for capture opportunities
            if tile.unit.type in [UnitType.INFANTRY, UnitType.MECH]:
                for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                    check_x, check_y = tile.x + dx, tile.y + dy
                    if 0 <= check_x < board.width and 0 <= check_y < board.height:
                        check_tile = board.grid[check_y * board.width + check_x]
                        if check_tile.mapTile.is_capturable():
                            building_owner = check_tile.mapTile.army.name if check_tile.mapTile.army else "Neutral"
                            capture_opportunities.append({
                                'unit': f"{unit_type} at ({tile.x},{tile.y})",
                                'target': f"{check_tile.mapTile.type} at ({check_x},{check_y})",
                                'current_owner': building_owner
                            })
            
            # Check for adjacent combat opportunities
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                check_x, check_y = tile.x + dx, tile.y + dy
                if 0 <= check_x < board.width and 0 <= check_y < board.height:
                    check_tile = board.grid[check_y * board.width + check_x]
                    if (check_tile.unit and 
                        check_tile.unit.army != tile.unit.army):
                        combat_pairs.append({
                            'attacker': f"{tile.unit.army.name} {unit_type} at ({tile.x},{tile.y})",
                            'defender': f"{check_tile.unit.army.name} {check_tile.unit.type.name} at ({check_x},{check_y})"
                        })
    
    html_response = f"""
    <html>
    <head><title>Debug: Game {token}</title></head>
    <body>
        <h1>🔍 Detailed Game Analysis: {token}</h1>
        
        <h2>📊 Game State</h2>
        <ul>
            <li><strong>Current Turn:</strong> {board.current_turn.name}</li>
            <li><strong>Day:</strong> {board.days}</li>
            <li><strong>Game Active:</strong> {board.game_active}</li>
            <li><strong>Board Size:</strong> {board.width}x{board.height}</li>
        </ul>
        
        <h2>💰 Economy</h2>
        <ul>
            <li><strong>RED Funds:</strong> ${board.red_funds:,}</li>
            <li><strong>BLUE Funds:</strong> ${board.blue_funds:,}</li>
            <li><strong>RED Properties:</strong> {board.total_red_properties}</li>
            <li><strong>BLUE Properties:</strong> {board.total_blue_properties}</li>
        </ul>
        
        <h2>🪖 Unit Deployment</h2>"""
    
    for army, units in unit_analysis.items():
        html_response += f"<h3>{army} Army ({sum(units.values())} total units)</h3><ul>"
        for unit_type, count in sorted(units.items()):
            html_response += f"<li>{unit_type}: {count}</li>"
        html_response += "</ul>"
    
    html_response += f"""
        <h2>⚔️ Combat Opportunities ({len(combat_pairs)})</h2>
        <ul>"""
    
    for pair in combat_pairs[:10]:  # Show first 10
        html_response += f"<li>{pair['attacker']} vs {pair['defender']}</li>"
    
    if len(combat_pairs) > 10:
        html_response += f"<li><em>... and {len(combat_pairs) - 10} more</em></li>"
    
    html_response += f"""
        </ul>
        
        <h2>🏰 Capture Opportunities ({len(capture_opportunities)})</h2>
        <ul>"""
    
    for opp in capture_opportunities[:10]:  # Show first 10
        html_response += f"<li>{opp['unit']} can capture {opp['target']} (currently {opp['current_owner']})</li>"
    
    if len(capture_opportunities) > 10:
        html_response += f"<li><em>... and {len(capture_opportunities) - 10} more</em></li>"
    
    html_response += f"""
        </ul>
        
        <h2>🚢 Loaded Transports ({len(loaded_transports)})</h2>
        <ul>"""
    
    for transport in loaded_transports:
        html_response += f"<li>{transport['type']} at {transport['position']} carrying {transport['cargo_count']} units: {', '.join(transport['cargo_types'])}</li>"
    
    html_response += f"""
        </ul>
        
        <h2>🎮 Quick Actions</h2>
        <ul>
            <li><a href="/{token}">🎯 Play Game</a></li>
            <li><a href="/debug">📋 All Games</a></li>
            <li><a href="/test_optimized">🔄 Create New Optimized Test</a></li>
        </ul>
        
        <h2>🧪 Browser Console Tests</h2>
        <p>Open the game and run these in browser console:</p>
        <pre>
// Test combat
rpc('unit_attack', {{x: 4, y: 5, x2: 6, y2: 5}}, console.log);

// Test movement  
rpc('unit_move', {{x: 2, y: 3, x2: 3, y2: 3}}, console.log);

// Test capture
rpc('unit_capture', {{x: 2, y: 3}}, console.log);

// Test transport unload
rpc('unit_unload', {{x: 3, y: 1, x2: 4, y2: 2, cargo_index: 0}}, console.log);

// Check game state
rpc('game_board', {{}}, console.log);
        </pre>
    </body>
    </html>
    """
    
    return html_response

# === JAVASCRIPT TESTING HELPERS ===

@app.route('/test_scripts/<token>')
def get_test_scripts(token):
    """Provide JavaScript testing scripts for browser console"""
    if token not in games:
        return f"Game {token} not found", 404
    
    game_manager = games[token]
    board = game_manager.board
    
    # Find specific units for targeted testing
    red_units = []
    blue_units = []
    transports = []
    infantry_near_buildings = []
    
    for tile in board.grid:
        if tile.unit:
            unit_info = {
                'type': tile.unit.type.name,
                'x': tile.x,
                'y': tile.y,
                'hp': tile.unit.status.hp,
                'army': tile.unit.army.name
            }
            
            if tile.unit.army.name == 'RED':
                red_units.append(unit_info)
            else:
                blue_units.append(unit_info)
            
            # Check for transports with cargo
            if hasattr(tile.unit, 'cargo') and len(tile.unit.cargo) > 0:
                unit_info['cargo'] = [cargo.type.name for cargo in tile.unit.cargo]
                transports.append(unit_info)
            
            # Check for infantry near buildings
            if tile.unit.type in [UnitType.INFANTRY, UnitType.MECH]:
                for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                    check_x, check_y = tile.x + dx, tile.y + dy
                    if 0 <= check_x < board.width and 0 <= check_y < board.height:
                        check_tile = board.grid[check_y * board.width + check_x]
                        if check_tile.mapTile.is_capturable():
                            unit_info['target_building'] = {
                                'type': check_tile.mapTile.type,
                                'x': check_x,
                                'y': check_y,
                                'owner': check_tile.mapTile.army.name if check_tile.mapTile.army else 'Neutral'
                            }
                            infantry_near_buildings.append(unit_info)
                            break

    javascript_tests = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Scripts for Game {token}</title>
    <style>
        body {{ font-family: monospace; margin: 20px; }}
        .test-section {{ margin: 20px 0; padding: 15px; border: 1px solid #ccc; }}
        pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; }}
        .copy-btn {{ margin: 5px; padding: 5px 10px; cursor: pointer; }}
    </style>
</head>
<body>
    <h1>🧪 Test Scripts for Game {token}</h1>
    <p><a href="/{token}" target="_blank">🎮 Open Game in New Tab</a></p>
    
    <div class="test-section">
        <h2>⚔️ Combat Tests</h2>
        <p>Copy and paste these into the game's browser console:</p>"""
    
    # Generate combat test scripts
    if len(red_units) > 0 and len(blue_units) > 0:
        red_unit = red_units[0]
        blue_unit = blue_units[0]
        javascript_tests += f"""
        <pre>
// Test attack with {red_unit['type']} vs {blue_unit['type']}
rpc('unit_attack', {{
    x: {red_unit['x']}, y: {red_unit['y']}, 
    x2: {blue_unit['x']}, y2: {blue_unit['y']}
}}, console.log);
        </pre>"""
    
    javascript_tests += """
    </div>
    
    <div class="test-section">
        <h2>🚶 Movement Tests</h2>"""
    
    if len(red_units) > 0:
        unit = red_units[0]
        new_x = min(unit['x'] + 1, board.width - 1)
        new_y = unit['y']
        javascript_tests += f"""
        <pre>
// Test movement with {unit['type']}
rpc('unit_move', {{
    x: {unit['x']}, y: {unit['y']}, 
    x2: {new_x}, y2: {new_y}
}}, console.log);
        </pre>"""
    
    javascript_tests += """
    </div>
    
    <div class="test-section">
        <h2>🏰 Capture Tests</h2>"""
    
    for unit in infantry_near_buildings[:3]:  # Show first 3
        javascript_tests += f"""
        <pre>
// {unit['type']} capture {unit['target_building']['type']} (currently {unit['target_building']['owner']})
// First move to the building:
rpc('unit_move', {{
    x: {unit['x']}, y: {unit['y']}, 
    x2: {unit['target_building']['x']}, y2: {unit['target_building']['y']}
}}, console.log);

// Then capture (after move completes):
setTimeout(() => {{
    rpc('unit_capture', {{x: {unit['target_building']['x']}, y: {unit['target_building']['y']}}}, console.log);
}}, 1000);
        </pre>"""
    
    javascript_tests += """
    </div>
    
    <div class="test-section">
        <h2>🚢 Transport Tests</h2>"""
    
    for transport in transports[:2]:  # Show first 2
        unload_x = min(transport['x'] + 1, board.width - 1)
        unload_y = transport['y']
        javascript_tests += f"""
        <pre>
// {transport['type']} unload {transport['cargo'][0]} 
rpc('unit_unload', {{
    x: {transport['x']}, y: {transport['y']}, 
    x2: {unload_x}, y2: {unload_y}, 
    cargo_index: 0
}}, console.log);
        </pre>"""
    
    javascript_tests += f"""
    </div>
    
    <div class="test-section">
        <h2>🎮 General Game Tests</h2>
        <pre>
// Check current game state
rpc('game_board', {{}}, console.log);

// Check current turn
rpc('check_turn', {{}}, console.log);

// End turn
rpc('army_end_turn', {{}}, console.log);

// Get tile info
rpc('tile', {{x: 5, y: 5}}, console.log);

// Create new unit (at factory)
rpc('unit_create', {{
    army: '{board.current_turn.name}', 
    unit_type: 'INFANTRY', 
    x: 0, y: 0
}}, console.log);
        </pre>
    </div>
    
    <div class="test-section">
        <h2>📊 Available Units for Testing</h2>
        <h3>RED Army Units:</h3>
        <ul>"""
    
    for unit in red_units:
        javascript_tests += f"<li>{unit['type']} at ({unit['x']},{unit['y']}) - HP: {unit['hp']}</li>"
    
    javascript_tests += """
        </ul>
        <h3>BLUE Army Units:</h3>
        <ul>"""
    
    for unit in blue_units:
        javascript_tests += f"<li>{unit['type']} at ({unit['x']},{unit['y']}) - HP: {unit['hp']}</li>"
    
    javascript_tests += f"""
        </ul>
    </div>
    
    <script>
        // Helper function to copy text to clipboard
        function copyToClipboard(text) {{
            navigator.clipboard.writeText(text).then(() => {{
                alert('Copied to clipboard!');
            }});
        }}
        
        // Add copy buttons to all pre elements
        document.querySelectorAll('pre').forEach(pre => {{
            const button = document.createElement('button');
            button.textContent = 'Copy';
            button.className = 'copy-btn';
            button.onclick = () => copyToClipboard(pre.textContent);
            pre.parentNode.insertBefore(button, pre);
        }});
    </script>
</body>
</html>
    """
    
    return javascript_tests

#
# Websocket (Enhanced)
#

ws_games = {}
games = {}

def ws_board_update(token):
    app_logger.debug(f"Broadcasting board update: {token}")
    socketio.emit('update', 'room', room=token)

def ws_msg(token, msg):
    app_logger.debug(f"Broadcasting message to {token}: {msg}")
    socketio.emit('message', msg, room=token)

class SocketIoNamespace(Namespace):
    def on_error(self, e):
        app_logger.error(f"SocketIO error: {e}")

    def on_connect(self):
        app_logger.info(f'SocketIO connect - sid: {request.sid}')

    def on_game(self, token):
        app_logger.info(f'SocketIO game join - sid: {request.sid}, token: {token}')
        join_room(token)
        ws_games[request.sid] = token

    def on_disconnect(self):
        app_logger.info(f'SocketIO disconnect - sid: {request.sid}')
        if request.sid in ws_games:
            leave_room(ws_games[request.sid])
            del ws_games[request.sid]

socketio.on_namespace(SocketIoNamespace('/'))

# =============================================================================
# 📋 INFORMATION & REFERENCE RPC METHODS  
# =============================================================================

@information_api.method('troop_info')
@log_rpc_performance
def troop_info(token: str = None) -> dict:
    """Get unit configuration and reference data
    
    Returns comprehensive unit information including costs, movement ranges,
    attack ranges, HP, fuel capacity, and other unit statistics.
    
    Args:
        token: Optional game identifier (not required for reference data)
        
    Returns:
        dict: Complete unit configuration data for all unit types
        
    Example:
        rpc('troop_info', {})
    """
    app_logger.info('troop_info requested')
    return jsons.dump(config_game.units)

# =============================================================================
# 💬 COMMUNICATION RPC METHODS
# =============================================================================

@communication_api.method('message')
@log_rpc_performance
def message(token: str, msg: str) -> str:
    """Send a chat message in the game
    
    Args:
        token: Game identifier
        msg: Message text to send
        
    Returns:
        str: Success confirmation
        
    Example:
        rpc('message', {token: 'mygame', msg: 'Good game!'})
    """
    app_logger.info(f'Chat message from {token}: {msg[:50]}...')
    ws_msg(token, msg)
    return 'ok'

@jsonrpc.method('game_delete')
@log_rpc_performance
def game_delete_rpc(token: str) -> str:
    '''rpc delete game'''
    try:
        game_delete(token)
        return 'ok'
    except Exception as ex:
        return handle_rpc_error('game_delete', token, ex)

@jsonrpc.method('game_create')
@log_rpc_performance
def game_create_rpc(token: str) -> str:
    '''rpc-create game'''
    try:
        game_create(token)
        return 'ok'
    except Exception as ex:
        return handle_rpc_error('game_create', token, ex)

@jsonrpc.method('game_create_test')
@log_rpc_performance
def game_create_test_rpc(token: str, use_optimized: bool = True) -> str:
    '''Create a test game with optimized map and settings'''
    try:
        if use_optimized:
            # Use the optimized test map with 50k starting funds
            mngr = get_optimized_test_game(token)
            game = Game(mngr.board, token)
            db.session.add(game)
            db.session.commit()
            
            games[token] = mngr
            
            if ENHANCED_LOGGING:
                game_event_logger.log_game_created(token, len(mngr.board.turn_order))
            
            app_logger.info(f"Test game created with optimized map: {token}")
            return 'ok'
        else:
            # Use regular test creation
            game_create(token)
            return 'ok'
    except Exception as ex:
        app_logger.error(f'game_create_test failed for {token}: {str(ex)}')
        raise ex  # Let Flask-JSONRPC handle the error properly

@jsonrpc.method('game_create_v2')
@log_rpc_performance
def game_create_v2_rpc(token: str, players: list = None, map_name: str = 'test') -> dict:
    '''Create a game with custom player configuration
    
    Args:
        token: Unique game identifier
        players: List of player configs, each with:
            - name: Player display name
            - color: Display color (any string)
            - sprite_color: Which sprite set to use (RED, BLUE, GREEN, YELLOW, GREY)
        map_name: Map to use (default: 'test')
        
    Returns:
        dict: Game info including token and player configuration
        
    Example:
        players = [
            {"name": "Alice", "color": "Purple", "sprite_color": "RED"},
            {"name": "Bob", "color": "Orange", "sprite_color": "BLUE"}
        ]
    '''
    try:
        # Create game with custom players or default 2-player
        if players:
            manager, _ = GameFactory.create_game_with_players(map_name, players)
        else:
            manager, _ = GameFactory.create_standard_game(map_name)
            
        # Store in games dict
        games[token] = manager
        
        # Save to database
        game = Game(manager.board, token)
        db.session.add(game)
        db.session.commit()
        
        if ENHANCED_LOGGING:
            game_event_logger.log_game_created(token, manager.player_manager.get_player_count())
            
        app_logger.info(f"Game v2 created: {token} with {manager.player_manager.get_player_count()} players")
        
        # Return game info
        return {
            'token': token,
            'players': manager.player_manager.to_dict()['players'],
            'sprite_mapping': manager.player_manager.to_dict()['sprite_mapping'],
            'map': map_name
        }
        
    except Exception as ex:
        return handle_rpc_error('game_create_v2', token, ex)

@jsonrpc.method('game_board')
@log_rpc_performance
def game_board_rpc(token: str) -> dict:
    '''rpc return game board'''
    app_logger.debug(f'Game board requested: {token}')
    try:
        mngr = game_load(token)
        
        # CRITICAL FIX: Ensure we return a dict, not a string
        board_data = jsons.dump(mngr.board)
        
        # If jsons.dump returns a string, parse it back to dict
        if isinstance(board_data, str):
            import json
            board_data = json.loads(board_data)
            
        # Add player info if this is a v2 game
        if isinstance(mngr, GameManagerV2):
            board_data['players'] = mngr.player_manager.to_dict()['players']
            board_data['sprite_mapping'] = mngr.player_manager.to_dict()['sprite_mapping']
            board_data['player_funds'] = mngr.board_v2.player_funds
            board_data['player_properties'] = mngr.board_v2.player_properties
            board_data['player_troops'] = mngr.board_v2.player_troops
            board_data['current_player'] = mngr.board_v2.current_player
        
        return board_data  # Now guaranteed to be a dict
        
    except Exception as ex:
        app_logger.error(f'game_board failed for {token}: {str(ex)}')
        # Return dict for consistency with return type annotation
        return {
            "error": True,
            "error_code": "GAME_BOARD_ERROR", 
            "message": str(ex),
            "details": {"token": token}
        }

@jsonrpc.method('army_end_turn')
@log_rpc_performance
def army_end_turn_rpc(token: str) -> dict:
    '''rpc end current turn'''
    try:
        mngr = game_load(token)
        current_army = mngr.check_turn()
        winner = mngr.check_win_condition()
        mngr.army_end_turn()
        game_save(mngr, token)
        ws_board_update(token)
        
        new_turn = mngr.check_turn()
        
        # Enhanced logging
        turn_number = getattr(mngr.board, 'days', 1)
        funds = getattr(mngr.board, f'{current_army.name.lower()}_funds', 0)
        
        if ENHANCED_LOGGING:
            game_event_logger.log_turn_ended(token, current_army.name, turn_number, funds)
        
        app_logger.info(f'Turn ended: {current_army.name} -> {new_turn.name} (Day {turn_number})')
        
        return {'current_turn': new_turn.name, 'status': 'success', 'day': turn_number}
    except Exception as ex:
        app_logger.error(f'army_end_turn error: {ex}')
        return handle_rpc_error('army_end_turn', token, ex)

# =============================================================================
# 🗺️ MAP & TILE INFORMATION RPC METHODS
# =============================================================================

@map_tile_api.method('tile')
@log_rpc_performance
def tile_rpc(token: str, x: int, y: int) -> dict:
    """Get detailed information about a specific tile
    
    Returns complete tile data including terrain type, ownership,
    any unit present, and capture status.
    
    Args:
        token: Game identifier
        x: X coordinate of tile
        y: Y coordinate of tile
        
    Returns:
        dict: Complete tile information including mapTile and unit data
        
    Example:
        rpc('tile', {token: 'mygame', x: 5, y: 3})
    """
    app_logger.debug(f'Tile requested: {token} at ({x},{y})')
    try:
        mngr = game_load(token)
        
        # Enhanced validation
        if x < 0 or y < 0 or x >= mngr.board.width or y >= mngr.board.height:
            raise Exception(f'coordinate out of range: x={x}, y={y}, max=({mngr.board.width-1},{mngr.board.height-1})')
        
        tile = mngr.tile_get(x, y)
        
        # Add terrain defense stars before serialization
        from map_system import TERRAIN_DEFENSE
        defense_stars = 0
        if tile.mapTile:
            defense_stars = TERRAIN_DEFENSE.get(tile.mapTile.type, 0)
        
        result = jsons.dump(tile)
        
        # Ensure defense_stars is in the result
        if isinstance(result, dict):
            result['defense_stars'] = defense_stars
        else:
            # If jsons.dump returned something else, create a proper dict
            result = {
                'x': tile.x,
                'y': tile.y,
                'mapTile': jsons.dump(tile.mapTile) if tile.mapTile else None,
                'unit': jsons.dump(tile.unit) if tile.unit else None,
                'capture_hp': tile.capture_hp,
                'can_be_moved_to': tile.can_be_moved_to,
                'can_be_attacked': tile.can_be_attacked,
                'defense_stars': defense_stars
            }
        
        return result
    except Exception as ex:
        app_logger.error(f'tile_rpc failed for {token} at ({x},{y}): {str(ex)}')
        return handle_rpc_error('tile', token, ex)

# =============================================================================
# 🏰 SPECIAL ACTIONS RPC METHODS
# =============================================================================

@special_actions_api.method('capture_tile')
@log_rpc_performance
def capture_tile_rpc(token: str, x: int, y: int) -> dict:
    """Capture a property with an infantry or mech unit
    
    Attempts to capture a property at the specified coordinates.
    Capture progress depends on unit HP (HP/10 capture points per turn).
    
    Args:
        token: Game identifier
        x: X coordinate of property to capture
        y: Y coordinate of property to capture
        
    Returns:
        dict: Capture result including progress and completion status
        
    Example:
        rpc('capture_tile', {token: 'mygame', x: 5, y: 3})
    """
    try:
        mngr = game_load(token)
        
        # Get info before capture
        tile = mngr.tile_get(x, y)
        old_hp = tile.capture_hp
        unit_info = f"{tile.unit.army.name}:{tile.unit.type.name}" if tile.unit else "none"
        property_type = tile.mapTile.type.name if hasattr(tile.mapTile.type, 'name') else str(tile.mapTile.type)
        
        mngr.capture_tile(x, y)
        
        # Enhanced logging
        new_tile = mngr.tile_get(x, y)
        if new_tile.capture_hp <= 0:
            log_game_event('PROPERTY_CAPTURED', token, {
                'position': {'x': x, 'y': y},
                'unit': unit_info,
                'property_type': property_type,
                'army': tile.unit.army.name if tile.unit else 'unknown'
            })
            app_logger.info(f'Property captured: {token} - {unit_info} captured {property_type} at ({x},{y})')
        else:
            app_logger.info(f'Capture progress: {token} - {unit_info} at ({x},{y}) HP: {old_hp} -> {new_tile.capture_hp}')
        
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x, y))
    except Exception as ex:
        app_logger.error(f'capture_tile failed for {token} at ({x},{y}): {str(ex)}')
        return handle_rpc_error('capture_tile', token, ex)

# =============================================================================
# 🪖 UNIT OPERATIONS RPC METHODS
# =============================================================================

@unit_operations_api.method('unit_create')
@log_rpc_performance
def unit_create_rpc(token: str, army: str, unit_type: str, x: int, y: int) -> dict:
    """Create a new unit at a production facility
    
    Creates a unit at the specified coordinates if there is a valid production
    facility and sufficient funds. New units cannot move on their creation turn.
    
    Args:
        token: Game identifier
        army: Army color ('RED' or 'BLUE')
        unit_type: Type of unit to create (e.g., 'INFANTRY', 'TANK', 'BATTLESHIP')
        x: X coordinate of production facility
        y: Y coordinate of production facility
        
    Returns:
        dict: Created unit information and tile state
        
    Example:
        rpc('unit_create', {
            token: 'mygame', 
            army: 'RED', 
            unit_type: 'INFANTRY', 
            x: 2, 
            y: 3
        })
    """
    
    # Import validation functions at the top
    from error_handling import validate_army, validate_unit_type, validate_coordinates, ValidationError
    
    try:
        # CHECK GAME ACTIVE FIRST
        mngr = game_load(token)
        if not mngr.board.game_active:
            return {
                "error": True,
                "error_code": "GAME_ENDED",
                "message": f"Cannot create units - game has ended! {getattr(mngr.board, 'winner', 'Unknown')} wins!",
                "details": {"winner": getattr(mngr.board, 'winner', 'Unknown')}
            }
        
        # Validate inputs
        army = validate_army(army)
        unit_type = validate_unit_type(unit_type)
        validate_coordinates(x, y, 50, 50)
        
        # Load game and create unit
        mngr = game_load(token)
        unit = mngr.unit_create(army, unit_type, x, y)
        
        # Log successful creation
        if ENHANCED_LOGGING:
            game_event_logger.log_unit_created(token, army, unit_type, x, y)
        
        # Save and return
        game_save(mngr, token)
        ws_board_update(token)
        
        return jsons.dump(mngr.tile_get(x, y))
        
    except ValidationError as e:
        # Return error as a dict instead of raising
        app_logger.error(f"Validation error in unit_create: {e.message}")
        return {
            "error": True,
            "error_code": "VALIDATION_ERROR",
            "message": e.message,
            "details": getattr(e, 'details', {})
        }
        
    except Exception as e:
        app_logger.error(f"unit_create failed for {token}: {army}:{unit_type} at ({x},{y}): {str(e)}")
        return {
            "error": True,
            "error_code": "INTERNAL_ERROR", 
            "message": "Internal server error",
            "details": {}
        }

@jsonrpc.method('unit_move')
@log_rpc_performance
def unit_move_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    """Move unit with enhanced validation and error handling"""
    try:
        # CHECK GAME ACTIVE FIRST (ADD THIS)
        mngr = game_load(token)
        if not mngr.board.game_active:
            return {
                "error": True,
                "error_code": "GAME_ENDED",
                "message": f"Cannot create units - game has ended! {getattr(mngr.board, 'winner', 'Unknown')} wins!",
                "details": {"winner": getattr(mngr.board, 'winner', 'Unknown')}
            }
            
        from error_handling import ValidationError
        
        # Load game first to get actual board dimensions
        mngr = game_load(token)
        
        # Dynamic coordinate validation using actual board size
        board_width = mngr.board.width
        board_height = mngr.board.height
        
        # Validate coordinates against actual board
        if not (0 <= x < board_width and 0 <= y < board_height):
            raise ValidationError(
                f"Source coordinates ({x}, {y}) are out of bounds. Board size: {board_width}x{board_height}",
                details={"position": {"x": x, "y": y}, "board_size": {"width": board_width, "height": board_height}}
            )
        
        if not (0 <= x2 < board_width and 0 <= y2 < board_height):
            raise ValidationError(
                f"Destination coordinates ({x2}, {y2}) are out of bounds. Board size: {board_width}x{board_height}",
                details={"position": {"x": x2, "y": y2}, "board_size": {"width": board_width, "height": board_height}}
            )
        
        # Get unit info before move
        unit = mngr.unit_at(x, y)
        if unit:
            army = unit.army.name
            unit_type = unit.type.name
            fuel_before = unit.status.fuel
        else:
            army = "unknown"
            unit_type = "unknown"  
            fuel_before = 0
        
        # Execute move
        mngr.unit_move(x, y, x2, y2)
        
        # Calculate fuel used
        unit_after = mngr.unit_at(x2, y2)
        fuel_used = fuel_before - (unit_after.status.fuel if unit_after else 0)
        
        # Enhanced logging
        log_game_event('UNIT_MOVED', token, {
            'army': army,
            'unit_type': unit_type,
            'from_pos': (x, y),
            'to_pos': (x2, y2),
            'fuel_used': fuel_used,
            'board_size': f"{board_width}x{board_height}"
        })
        
        app_logger.info(f'Unit moved: {token} - {army}:{unit_type} from ({x},{y}) to ({x2},{y2}) fuel_used={fuel_used} on {board_width}x{board_height} board')
        
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x2, y2))
        
    except ValidationError as e:
        app_logger.error(f"Validation error in unit_move: {e.message}")
        return {
            "error": True,
            "error_code": "VALIDATION_ERROR",
            "message": e.message,
            "details": getattr(e, 'details', {})
        }
        
    except Exception as e:
        app_logger.error(f'unit_move failed for {token}: ({x},{y}) -> ({x2},{y2}): {str(e)}')
        return {
            "error": True,
            "error_code": "MOVEMENT_ERROR",
            "message": "Movement failed",
            "details": {"from": {"x": x, "y": y}, "to": {"x": x2, "y": y2}}
        }

@jsonrpc.method('unit_select')
@log_rpc_performance
def unit_select_rpc(token: str, x: int, y: int) -> dict:
    """Select unit with enhanced validation and error handling"""
    try:
        # CHECK GAME ACTIVE FIRST (ADD THIS)
        mngr = game_load(token)
        if not mngr.board.game_active:
            return {
                "error": True,
                "error_code": "GAME_ENDED",
                "message": f"Cannot create units - game has ended! {getattr(mngr.board, 'winner', 'Unknown')} wins!",
                "details": {"winner": getattr(mngr.board, 'winner', 'Unknown')}
            }
            
        from error_handling import ValidationError
        
        # Load game first to get actual board dimensions
        mngr = game_load(token)
        
        # Dynamic coordinate validation using actual board size
        board_width = mngr.board.width
        board_height = mngr.board.height
        
        # Validate coordinates
        if not (0 <= x < board_width and 0 <= y < board_height):
            raise ValidationError(
                f"Selection coordinates ({x}, {y}) are out of bounds. Board size: {board_width}x{board_height}",
                details={"position": {"x": x, "y": y}, "board_size": {"width": board_width, "height": board_height}}
            )
        
        # Get tile and unit info for logging
        tile = mngr.tile_at(x, y)
        unit = mngr.unit_at(x, y)
        
        # Determine what's being selected
        if unit:
            unit_info = f"{unit.army.name}:{unit.type.name}"
            selection_type = "unit"
        elif tile.mapTile.type.name in ['FACTORY', 'AIRPORT', 'PORT'] if hasattr(tile.mapTile.type, 'name') else False:
            unit_info = f"{tile.mapTile.type.name}"
            selection_type = "property"
        else:
            unit_info = "empty tile"
            selection_type = "empty"
        
        # Try to execute selection - handle the manager's limitations gracefully
        try:
            mngr.unit_select(x, y)
            success = True
            app_logger.debug(f'{selection_type.title()} selected: {token} - {unit_info} at ({x},{y})')
        except Exception as selection_error:
            # If manager.unit_select fails, that's okay for empty tiles/properties
            # Just log it and continue
            if "No unit at" in str(selection_error):
                app_logger.debug(f'Selected {selection_type}: {token} - {unit_info} at ({x},{y}) (no unit selection needed)')
                success = True
            else:
                # Re-raise if it's a different error
                raise selection_error
        
        # Save game state
        game_save(mngr, token)
        ws_board_update(token)
        
        # Return appropriate information
        if unit:
            return jsons.dump(unit)
        else:
            # Return tile info for properties/empty tiles
            return jsons.dump(mngr.tile_get(x, y))
        
    except ValidationError as e:
        app_logger.error(f"Validation error in unit_select: {e.message}")
        return {
            "error": True,
            "error_code": "VALIDATION_ERROR",
            "message": e.message,
            "details": getattr(e, 'details', {})
        }
        
    except Exception as e:
        app_logger.error(f'unit_select failed for {token} at ({x},{y}): {str(e)}')
        return {
            "error": True,
            "error_code": "SELECTION_ERROR",
            "message": "Selection failed",
            "details": {"position": {"x": x, "y": y}}
        }

# =============================================================================
# ⚔️ COMBAT SYSTEM RPC METHODS
# =============================================================================

@combat_system_api.method('unit_attack')
@log_rpc_performance
def unit_attack_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    """Execute an attack from one unit to another
    
    Performs combat between attacking unit at (x,y) and defending unit at (x2,y2).
    Includes damage calculation, counter-attacks, and automatic victory detection.
    
    Args:
        token: Game identifier
        x: X coordinate of attacking unit
        y: Y coordinate of attacking unit
        x2: X coordinate of target unit
        y2: Y coordinate of target unit
        
    Returns:
        dict: Combat result including damage dealt, victory status
        
    Example:
        rpc('unit_attack', {token: 'mygame', x: 5, y: 3, x2: 6, y2: 3})
    """
    try:
        from error_handling import ValidationError
        
        # Load game first to get actual board dimensions
        mngr = game_load(token)
        
        # Dynamic coordinate validation using actual board size
        board_width = mngr.board.width
        board_height = mngr.board.height
        
        # Validate source coordinates
        if not (0 <= x < board_width and 0 <= y < board_height):
            raise ValidationError(
                f"Attacker coordinates ({x}, {y}) are out of bounds. Board size: {board_width}x{board_height}",
                details={"attacker_pos": {"x": x, "y": y}, "board_size": {"width": board_width, "height": board_height}}
            )
        
        # Validate target coordinates
        if not (0 <= x2 < board_width and 0 <= y2 < board_height):
            raise ValidationError(
                f"Target coordinates ({x2}, {y2}) are out of bounds. Board size: {board_width}x{board_height}",
                details={"target_pos": {"x": x2, "y": y2}, "board_size": {"width": board_width, "height": board_height}}
            )
        
        # Execute the attack
        result = mngr.unit_attack(x, y, x2, y2)
        
        # Check victory BEFORE saving (MOVED UP)
        victory_result = check_victory_conditions(mngr, token)
        
        if victory_result['victory']:
            # SET BOARD STATE HERE (where it gets saved)
            mngr.board.game_active = False
            mngr.board.winner = victory_result['winner']
            mngr.board.victory_type = victory_result['type']
            app_logger.info(f"SETTING VICTORY STATE: {victory_result['winner']} wins!")
        
        # Save game state and update clients (AFTER setting victory state)
        game_save(mngr, token)
        ws_board_update(token)
        
        if victory_result['victory']:
            app_logger.info(f"GAME OVER: {victory_result['winner']} wins!")
            return {
                **jsons.dump(result),
                'game_over': True,
                'winner': victory_result['winner'],
                'victory_type': victory_result['type']
            }
        
        # Normal return if no victory
        return jsons.dump(result)
        
    except ValidationError as e:
        # Return error as a dict instead of raising
        app_logger.error(f"Validation error in unit_attack: {e.message}")
        return {
            "error": True,
            "error_code": "VALIDATION_ERROR",
            "message": e.message,
            "details": getattr(e, 'details', {})
        }
        
    except Exception as e:
        app_logger.error(f'unit_attack failed for {token}: ({x},{y}) -> ({x2},{y2}): {str(e)}')
        return {
            "error": True,
            "error_code": "COMBAT_ERROR",
            "message": "Attack failed",
            "details": {"attacker_pos": {"x": x, "y": y}, "target_pos": {"x": x2, "y": y2}}
        }

# Add this to your app.py file to fix the APC loading error
# This creates an alias for the frontend's expected method name

@jsonrpc.method('unit_load')
@log_rpc_performance
def unit_load_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    """
    LEGACY ALIAS: Load a unit into transport
    Frontend logic: Select unit, then alt-click transport
    x,y = selected unit position (cargo)
    x2,y2 = alt-clicked transport position
    
    This is the method your frontend is calling based on the debug logs:
    rpc:: unit_load Object { x: 1, y: 3, x2: 2, y2: 3, token: "655z_K2c" }
    """
    try:
        # Add debug logging to track the call
        app_logger.info(f"UNIT_LOAD: Frontend called with cargo=({x},{y}), transport=({x2},{y2})")
        
        # Correct parameter mapping:
        # x,y = cargo position (selected unit)
        # x2,y2 = transport position (alt-clicked)
        result = load_unit_rpc(token, transport_x=x2, transport_y=y2, cargo_x=x, cargo_y=y)
        
        app_logger.info(f"UNIT_LOAD: Backend result = {result}")
        return result
        
    except Exception as e:
        app_logger.error(f"Unit load (legacy) failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}
       
# Add this to your app.py file to fix the APC unloading

@jsonrpc.method('unit_unload')
@log_rpc_performance
def unit_unload_rpc(token: str, x: int, y: int, x2: int, y2: int, index: int = 0) -> dict:
    """
    LEGACY ALIAS: Unload a unit from transport
    Frontend logic: Select transport, then alt-click destination
    x,y = selected transport position
    x2,y2 = alt-clicked unload destination position
    index = cargo index (frontend sends 'index', not 'cargo_index')
    """
    try:
        # Parameter mapping:
        # x,y = transport position (selected transport)
        # x2,y2 = unload destination (alt-clicked tile)
        # index = cargo_index (frontend parameter name)
        return unload_unit_rpc(token, 
                             transport_x=x, transport_y=y,
                             unload_x=x2, unload_y=y2, 
                             cargo_index=index)
        
    except Exception as e:
        app_logger.error(f"Unit unload (legacy) failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

# Add this simple alias to your app.py file
@jsonrpc.method('get_unload_positions_internal')
@log_rpc_performance
def get_unload_positions_rpc(token: str, transport_x: int, transport_y: int) -> dict:
    """Get valid unload positions for transport cargo (internal method)"""
    try:
        mngr = game_load(token)
        
        # Validate coordinates
        if not (0 <= transport_x < mngr.board.width and 0 <= transport_y < mngr.board.height):
            return {"success": False, "error": "Invalid coordinates"}
        
        # Get transport
        transport = mngr.unit_at(transport_x, transport_y)
        if not transport:
            return {"success": False, "error": "No unit found"}
        
        # Check turn ownership
        if transport.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        # Get valid exit positions
        transport_system = CompleteTransportSystem(mngr)
        valid_positions = transport_system.get_valid_exit_positions(transport_x, transport_y)
        
        return {
            "success": True,
            "valid_positions": [{"x": x, "y": y} for x, y in valid_positions],
            "transport_info": transport_system.get_cargo_info(transport)
        }
        
    except Exception as e:
        app_logger.error(f"Get unload positions failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('get_unload_positions')
@log_rpc_performance  
def get_unload_positions_frontend_alias(token: str, x: int, y: int) -> dict:
    """
    FRONTEND ALIAS: Get valid unload positions
    Frontend calls with x,y, maps to backend transport_x, transport_y
    Also fixes cargo_list vs cargo_units naming mismatch
    """
    try:
        # Call existing backend method with correct parameter names
        result = get_unload_positions_rpc(token, transport_x=x, transport_y=y)
        
        # Fix frontend naming expectation: cargo_units -> cargo_list
        if result.get('success') and 'transport_info' in result:
            transport_info = result['transport_info']
            if 'cargo_units' in transport_info:
                transport_info['cargo_list'] = transport_info['cargo_units']
        
        return result
        
    except Exception as e:
        app_logger.error(f"Get unload positions (frontend alias) failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('damage_estimate')
@log_rpc_performance
def damage_estimate_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    '''rpc estimates the damage for attacker and defender'''
    try:
        mngr = game_load(token)
        attacker_hp, defender_hp = mngr.damage_estimate(x, y, x2, y2)
        
        app_logger.debug(f'Damage estimate: {token} - ({x},{y}) vs ({x2},{y2}) = attacker:{attacker_hp}, defender:{defender_hp}')
        
        return {
            "attacker_hp_after": attacker_hp,
            "defender_hp_after": defender_hp,
            "success": True
        }
    except Exception as ex:
        app_logger.error(f'damage_estimate failed for {token}: ({x},{y}) vs ({x2},{y2}): {str(ex)}')
        return handle_rpc_error('damage_estimate', token, ex)

@jsonrpc.method('check_turn')
@log_rpc_performance
def check_turn_rpc(token: str) -> dict:
    '''rpc check current turn'''
    try:
        mngr = game_load(token)
        turn = mngr.check_turn()
        app_logger.debug(f'Turn check: {token} - {turn.name}')
        return {'current_turn': turn.name, 'success': True}
    except Exception as ex:
        app_logger.error(f'check_turn failed for {token}: {str(ex)}')
        return handle_rpc_error('check_turn', token, ex)

# Enhanced damage preview RPC method)
@jsonrpc.method('damage_preview')
@log_rpc_performance
def damage_preview_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    """Get damage preview before executing attack"""
    try:
        mngr = game_load(token)
        
        # Validate coordinates
        board_width = mngr.board.width
        board_height = mngr.board.height
        
        if not (0 <= x < board_width and 0 <= y < board_height):
            return {
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": f"Attacker coordinates ({x}, {y}) out of bounds"
            }
        
        if not (0 <= x2 < board_width and 0 <= y2 < board_height):
            return {
                "success": False,
                "error_code": "VALIDATION_ERROR", 
                "message": f"Target coordinates ({x2}, {y2}) out of bounds"
            }
        
        preview = mngr.get_damage_preview(x, y, x2, y2)
        
        if "error" in preview:
            return {
                "success": False,
                "error_code": "PREVIEW_ERROR",
                "message": preview["error"]
            }
        
        return {
            "success": True,
            "preview": preview,
            "attacker_position": {"x": x, "y": y},
            "defender_position": {"x": x2, "y": y2}
        }
        
    except Exception as e:
        app_logger.error(f"Damage preview failed for {token}: ({x},{y}) vs ({x2},{y2}): {str(e)}")
        return {
            "success": False,
            "error_code": "PREVIEW_ERROR",
            "message": f"Could not calculate damage preview: {str(e)}"
        }

# Enhanced movement RPC methods
@jsonrpc.method('movement_preview')
def movement_preview_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    """Get movement preview information"""
    mngr = game_load(token)
    return mngr.get_movement_preview(x, y, x2, y2)

@jsonrpc.method('unit_valid_moves')
def unit_valid_moves_rpc(token: str, x: int, y: int) -> dict:
    """Get all valid moves for a unit"""
    mngr = game_load(token)
    unit = mngr._validate_unit_exists(x, y)
    valid_moves = mngr.get_unit_valid_moves(unit)
    return {
        'valid_moves': valid_moves,
        'count': len(valid_moves)
    }

@jsonrpc.method('validate_movement')
def validate_movement_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    """Validate movement and get detailed information"""
    mngr = game_load(token)
    result = mngr.validate_movement_detailed(x, y, x2, y2)
    return {
        'valid': result.valid,
        'reason': result.reason,
        'MOVEMENT_COST': result.MOVEMENT_COST,
        'fuel_required': result.fuel_required,
        'path_found': result.path_found,
        'blocked_by': result.blocked_by
    }

# =============================================================================
# 🏭 PRODUCTION & ECONOMIC SYSTEM RPC METHODS
# =============================================================================

@production_economic_api.method('produce_unit')
@log_rpc_performance
def produce_unit_rpc(token: str, x: int, y: int, unit_type: str) -> dict:
    """Produce a unit at a production facility
    
    Creates a new unit at the specified facility coordinates if there is
    sufficient funds and the facility can produce the requested unit type.
    
    Args:
        token: Game identifier
        x: X coordinate of production facility
        y: Y coordinate of production facility
        unit_type: Type of unit to produce
        
    Returns:
        dict: Production result and new unit information
        
    Example:
        rpc('produce_unit', {token: 'mygame', x: 2, y: 3, unit_type: 'TANK'})
    """
    try:
        mngr = game_load(token)
        
        # Validate coordinates
        board_width = mngr.board.width
        board_height = mngr.board.height
        
        if not (0 <= x < board_width and 0 <= y < board_height):
            return {
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": f"Coordinates ({x}, {y}) out of bounds"
            }
        
        # Get current army
        current_army = mngr.board.current_turn
        
        # Attempt production
        result = mngr.produce_unit_at_facility(x, y, unit_type, current_army)
        
        if result.success:
            # Save game state
            game_save(mngr, token)
            ws_board_update(token)
            
            # Enhanced logging
            if ENHANCED_LOGGING:
                app_logger.info(f'Unit produced: {token} - {current_army.name} created {unit_type} at ({x},{y}) for {result.cost}')
            
            return {
                "success": True,
                "unit_created": {
                    "type": unit_type,
                    "position": {"x": x, "y": y},
                    "army": current_army.name,
                    "cost": result.cost,
                    "remaining_funds": result.remaining_funds
                }
            }
        else:
            return {
                "success": False,
                "error_code": "PRODUCTION_ERROR",
                "message": result.error_message,
                "remaining_funds": result.remaining_funds
            }
        
    except Exception as e:
        app_logger.error(f"Unit production failed for {token} at ({x},{y}): {str(e)}")
        return {
            "success": False,
            "error_code": "PRODUCTION_ERROR",
            "message": f"Production failed: {str(e)}"
        }

@jsonrpc.method('get_production_options')
@log_rpc_performance
def get_production_options_rpc(token: str, x: int, y: int) -> dict:
    """Get available units that can be produced at a facility"""
    try:
        mngr = game_load(token)
        
        # Validate coordinates
        board_width = mngr.board.width
        board_height = mngr.board.height
        
        if not (0 <= x < board_width and 0 <= y < board_height):
            return {
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": f"Coordinates ({x}, {y}) out of bounds"
            }
        
        # Get current army
        current_army = mngr.board.current_turn
        
        # Get production options
        options = mngr.get_production_options(x, y, current_army)
        
        if "error" in options:
            return {
                "success": False,
                "error_code": "FACILITY_ERROR",
                "message": options["error"]
            }
        
        return {
            "success": True,
            "facility": {
                "position": {"x": x, "y": y},
                "type": options["facility_type"],
                "army": current_army.name
            },
            "production_options": options
        }
        
    except Exception as e:
        app_logger.error(f"Get production options failed for {token} at ({x},{y}): {str(e)}")
        return {
            "success": False,
            "error_code": "FACILITY_ERROR",
            "message": f"Could not get production options: {str(e)}"
        }

@jsonrpc.method('get_army_economy')
@log_rpc_performance
def get_army_economy_rpc(token: str) -> dict:
    """Get complete economic summary for current army"""
    try:
        mngr = game_load(token)
        current_army = mngr.board.current_turn
        
        economy = mngr.get_army_economy(current_army)
        
        return {
            "success": True,
            "economy": economy
        }
        
    except Exception as e:
        app_logger.error(f"Get army economy failed for {token}: {str(e)}")
        return {
            "success": False,
            "error_code": "ECONOMY_ERROR",
            "message": f"Could not get economy info: {str(e)}"
        }

@jsonrpc.method('get_army_facilities')
@log_rpc_performance
def get_army_facilities_rpc(token: str) -> dict:
    """Get all production facilities owned by current army"""
    try:
        mngr = game_load(token)
        current_army = mngr.board.current_turn
        
        facilities = mngr.get_army_facilities(current_army)
        
        return {
            "success": True,
            "army": current_army.name,
            "facilities": facilities,
            "facility_count": len(facilities)
        }
        
    except Exception as e:
        app_logger.error(f"Get army facilities failed for {token}: {str(e)}")
        return {
            "success": False,
            "error_code": "FACILITY_ERROR",
            "message": f"Could not get facilities: {str(e)}"
        }

@jsonrpc.method('can_afford_unit')
@log_rpc_performance
def can_afford_unit_rpc(token: str, unit_type: str) -> dict:
    """Check if current army can afford a specific unit type"""
    try:
        mngr = game_load(token)
        current_army = mngr.board.current_turn
        
        can_afford = mngr.can_afford_unit(unit_type, current_army)
        current_funds = mngr._get_army_funds(current_army)
        
        # Get unit cost for reference
        from production_system import ProductionSystem
        from unit import UnitType
        
        try:
            unit_type_enum = UnitType[unit_type.upper()]
            production_system = ProductionSystem(mngr)
            unit_cost = production_system.UNIT_COSTS.get(unit_type_enum, 1000)
        except KeyError:
            return {
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": f"Invalid unit type: {unit_type}"
            }
        
        return {
            "success": True,
            "can_afford": can_afford,
            "unit_type": unit_type,
            "unit_cost": unit_cost,
            "current_funds": current_funds,
            "army": current_army.name
        }
        
    except Exception as e:
        app_logger.error(f"Can afford unit check failed for {token}: {str(e)}")
        return {
            "success": False,
            "error_code": "AFFORDABILITY_ERROR",
            "message": f"Could not check affordability: {str(e)}"
        }

@jsonrpc.method('get_unit_costs')
@log_rpc_performance
def get_unit_costs_rpc(token: str) -> dict:
    
    """Get all unit costs for reference"""
    try:
        from production_system import ProductionSystem
        from unit import UnitType
        
        # Get unit costs from production system
        production_system = ProductionSystem(None)  # Manager not needed for costs
        unit_costs = {}
        
        for unit_type in UnitType:
            cost = production_system.UNIT_COSTS.get(unit_type, 1000)
            unit_costs[unit_type.name] = cost
        
        return {
            "success": True,
            "unit_costs": unit_costs
        }
        
    except Exception as e:
        app_logger.error(f"Get unit costs failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        } 
# =============================================================================
# 🚢 TRANSPORT SYSTEM RPC METHODS
# =============================================================================

@transport_system_api.method('cargo_board_transport')
@log_rpc_performance
def cargo_board_transport_rpc(token: str, cargo_x: int, cargo_y: int, 
                             transport_x: int, transport_y: int) -> dict:
    """
    ADVANCE WARS STYLE: Cargo unit moves into transport
    This is called when a cargo unit wants to board a transport
    """
    try:
        mngr = game_load(token)
        
        # Validate game state
        if not mngr.board.game_active:
            return {"success": False, "error": "Game has ended"}
        
        # Validate coordinates
        coords = [cargo_x, cargo_y, transport_x, transport_y]
        if not all(0 <= coord < mngr.board.width or 0 <= coord < mngr.board.height for coord in coords):
            return {"success": False, "error": "Invalid coordinates"}
        
        # Get units
        cargo = mngr.unit_at(cargo_x, cargo_y)
        transport = mngr.unit_at(transport_x, transport_y)
        
        if not cargo:
            return {"success": False, "error": "No cargo unit found"}
        if not transport:
            return {"success": False, "error": "No transport unit found"}
        
        # Check turn ownership
        if cargo.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        # Execute boarding
        transport_system = CompleteTransportSystem(mngr)
        result = transport_system.cargo_move_into_transport(
            cargo, transport, cargo_x, cargo_y, transport_x, transport_y
        )
        
        if result.success:
            # Log the action
            log_game_event('CARGO_BOARDED_TRANSPORT', token, {
                'cargo': f"{cargo.army.name} {cargo.type.name}",
                'transport': f"{transport.army.name} {transport.type.name}",
                'from_position': f"({cargo_x}, {cargo_y})",
                'to_position': f"({transport_x}, {transport_y})",
                'cargo_index': result.cargo_index
            })
            
            app_logger.info(f"Cargo boarded: {token} - {cargo.type.name} boarded {transport.type.name}")
            
            # Save game state
            game_save(mngr, token)
            ws_board_update(token)
        
        return {
            "success": result.success,
            "message": result.message,
            "cargo_index": result.cargo_index,
            "transport_info": transport_system.get_cargo_info(transport)
        }
        
    except Exception as e:
        app_logger.error(f"Cargo board failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('cargo_exit_transport')
@log_rpc_performance
def cargo_exit_transport_rpc(token: str, transport_x: int, transport_y: int,
                            exit_x: int, exit_y: int, cargo_index: int = 0) -> dict:
    """
    ADVANCE WARS STYLE: Cargo unit exits transport to specific position
    This is called when a cargo unit wants to exit a transport
    """
    try:
        mngr = game_load(token)
        
        # Validate game state
        if not mngr.board.game_active:
            return {"success": False, "error": "Game has ended"}
        
        # Validate coordinates
        coords = [transport_x, transport_y, exit_x, exit_y]
        if not all(0 <= coord < mngr.board.width or 0 <= coord < mngr.board.height for coord in coords):
            return {"success": False, "error": "Invalid coordinates"}
        
        # Get transport
        transport = mngr.unit_at(transport_x, transport_y)
        if not transport:
            return {"success": False, "error": "No transport unit found"}
        
        # Check turn ownership
        if transport.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        # Execute exit
        transport_system = CompleteTransportSystem(mngr)
        result = transport_system.cargo_exit_transport(
            transport, cargo_index, transport_x, transport_y, exit_x, exit_y
        )
        
        if result.success:
            # Log the action
            log_game_event('CARGO_EXITED_TRANSPORT', token, {
                'transport': f"{transport.army.name} {transport.type.name}",
                'position': f"({transport_x}, {transport_y})",
                'exit_position': f"({exit_x}, {exit_y})",
                'cargo_index': cargo_index
            })
            
            app_logger.info(f"Cargo exited: {token} - from {transport.type.name} to ({exit_x}, {exit_y})")
            
            # Save game state
            game_save(mngr, token)
            ws_board_update(token)
        
        return {
            "success": result.success,
            "message": result.message,
            "exit_position": result.unloaded_position,
            "transport_info": transport_system.get_cargo_info(transport)
        }
        
    except Exception as e:
        app_logger.error(f"Cargo exit failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('get_loadable_transports')
@log_rpc_performance
def get_loadable_transports_rpc(token: str, cargo_x: int, cargo_y: int) -> dict:
    """
    ADVANCE WARS STYLE: Get transports that this cargo unit can board
    Called when a cargo unit is selected to show boarding options
    """
    try:
        mngr = game_load(token)
        
        # Validate coordinates
        if not (0 <= cargo_x < mngr.board.width and 0 <= cargo_y < mngr.board.height):
            return {"success": False, "error": "Invalid coordinates"}
        
        # Get cargo unit
        cargo = mngr.unit_at(cargo_x, cargo_y)
        if not cargo:
            return {"success": False, "error": "No unit found"}
        
        # Check turn ownership
        if cargo.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        # Get loadable transports
        transport_system = CompleteTransportSystem(mngr)
        loadable_transports = transport_system.get_loadable_transports_near(cargo_x, cargo_y)
        
        return {
            "success": True,
            "loadable_transports": loadable_transports,
            "count": len(loadable_transports),
            "cargo_type": cargo.type.name if hasattr(cargo.type, 'name') else str(cargo.type)
        }
        
    except Exception as e:
        app_logger.error(f"Get loadable transports failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('get_exit_positions')
@log_rpc_performance
def get_exit_positions_rpc(token: str, transport_x: int, transport_y: int) -> dict:
    """
    ADVANCE WARS STYLE: Get valid exit positions for transport cargo
    Called when a transport is selected to show exit options
    """
    try:
        mngr = game_load(token)
        
        # Validate coordinates
        if not (0 <= transport_x < mngr.board.width and 0 <= transport_y < mngr.board.height):
            return {"success": False, "error": "Invalid coordinates"}
        
        # Get transport
        transport = mngr.unit_at(transport_x, transport_y)
        if not transport:
            return {"success": False, "error": "No unit found"}
        
        # Check turn ownership
        if transport.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        # Get valid exit positions
        transport_system = CompleteTransportSystem(mngr)
        valid_positions = transport_system.get_valid_exit_positions(transport_x, transport_y)
        
        return {
            "success": True,
            "valid_positions": [{"x": x, "y": y} for x, y in valid_positions],
            "transport_info": transport_system.get_cargo_info(transport)
        }
        
    except Exception as e:
        app_logger.error(f"Get exit positions failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('can_cargo_exit_transport')
@log_rpc_performance
def can_cargo_exit_transport_rpc(token: str, transport_x: int, transport_y: int,
                                exit_x: int, exit_y: int, cargo_index: int = 0) -> dict:
    """
    ADVANCE WARS STYLE: Check if cargo can exit to specific position
    Used for validation before attempting to exit
    """
    try:
        mngr = game_load(token)
        
        # Validate coordinates
        coords = [transport_x, transport_y, exit_x, exit_y]
        if not all(0 <= coord < mngr.board.width or 0 <= coord < mngr.board.height for coord in coords):
            return {"success": False, "error": "Invalid coordinates"}
        
        # Get transport
        transport = mngr.unit_at(transport_x, transport_y)
        if not transport:
            return {"success": False, "error": "No transport unit found"}
        
        # Check turn ownership
        if transport.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        # Check if exit is possible
        transport_system = CompleteTransportSystem(mngr)
        can_exit, message = transport_system.can_cargo_exit_transport(
            transport, cargo_index, transport_x, transport_y, exit_x, exit_y
        )
        
        return {
            "success": True,
            "can_exit": can_exit,
            "message": message,
            "transport_info": transport_system.get_cargo_info(transport)
        }
        
    except Exception as e:
        app_logger.error(f"Can cargo exit failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

# =============================================================================
# ENHANCED UNIT MOVEMENT WITH TRANSPORT INTEGRATION
# =============================================================================

@jsonrpc.method('unit_move_enhanced')
@log_rpc_performance 
def unit_move_enhanced_rpc(token: str, from_x: int, from_y: int, to_x: int, to_y: int) -> dict:
    """
    ADVANCE WARS STYLE: Enhanced unit movement that can handle transport boarding
    This automatically detects if the destination contains a friendly transport
    """
    try:
        mngr = game_load(token)
        
        # Validate game state
        if not mngr.board.game_active:
            return {"success": False, "error": "Game has ended"}
        
        # Validate coordinates
        coords = [from_x, from_y, to_x, to_y]
        if not all(0 <= coord < mngr.board.width or 0 <= coord < mngr.board.height for coord in coords):
            return {"success": False, "error": "Invalid coordinates"}
        
        # Get moving unit
        moving_unit = mngr.unit_at(from_x, from_y)
        if not moving_unit:
            return {"success": False, "error": "No unit to move"}
        
        # Check turn ownership
        if moving_unit.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        # Check destination
        destination_unit = mngr.unit_at(to_x, to_y)
        
        # ADVANCE WARS STYLE: If destination has a friendly transport, try to board
        if destination_unit:
            transport_system = CompleteTransportSystem(mngr)
            
            # Check if destination unit is a friendly transport
            if (destination_unit.army == moving_unit.army and 
                transport_system.is_transport_unit(destination_unit)):
                
                # Attempt to board the transport
                can_board, message = transport_system.can_cargo_move_into_transport(
                    moving_unit, destination_unit, from_x, from_y, to_x, to_y
                )
                
                if can_board:
                    # Execute boarding
                    result = transport_system.cargo_move_into_transport(
                        moving_unit, destination_unit, from_x, from_y, to_x, to_y
                    )
                    
                    if result.success:
                        # Log the action
                        log_game_event('AUTO_CARGO_BOARDED', token, {
                            'cargo': f"{moving_unit.army.name} {moving_unit.type.name}",
                            'transport': f"{destination_unit.army.name} {destination_unit.type.name}",
                            'from_position': f"({from_x}, {from_y})",
                            'to_position': f"({to_x}, {to_y})"
                        })
                        
                        # Save and update
                        game_save(mngr, token)
                        ws_board_update(token)
                        
                        return {
                            "success": True,
                            "action": "boarded_transport",
                            "message": result.message,
                            "transport_info": transport_system.get_cargo_info(destination_unit)
                        }
                    else:
                        return {"success": False, "error": result.message}
                else:
                    return {"success": False, "error": message}
            else:
                return {"success": False, "error": "Destination tile is occupied"}
        
        # Normal movement - destination is empty
        try:
            moved_unit = mngr.unit_move(from_x, from_y, to_x, to_y)
            
            # Log the action
            log_game_event('UNIT_MOVED', token, {
                'unit': f"{moved_unit.army.name} {moved_unit.type.name}",
                'from_position': f"({from_x}, {from_y})",
                'to_position': f"({to_x}, {to_y})"
            })
            
            # Save and update
            game_save(mngr, token)
            ws_board_update(token)
            
            return {
                "success": True,
                "action": "moved",
                "message": f"Unit moved to ({to_x}, {to_y})",
                "unit_info": {
                    "type": moved_unit.type.name if hasattr(moved_unit.type, 'name') else str(moved_unit.type),
                    "hp": moved_unit.status.hp,
                    "fuel": moved_unit.status.fuel
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    except Exception as e:
        app_logger.error(f"Enhanced unit move failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('can_transport_move')
@log_rpc_performance
def can_transport_move_rpc(token: str, x: int, y: int) -> dict:
    """Check if transport can still move this turn"""
    try:
        mngr = game_load(token)
        unit = mngr.unit_at(x, y)
        
        if not unit:
            return {"success": False, "error": "No unit found"}
        
        if not mngr.is_transport_unit(unit):
            return {"success": False, "error": "Unit is not a transport"}
        
        can_move = mngr.can_transport_move(unit)
        has_moved = getattr(unit.status, 'has_moved_this_turn', False)
        
        return {
            "success": True,
            "can_move": can_move,
            "has_moved_this_turn": has_moved,
            "unit_type": unit.type.name if hasattr(unit.type, 'name') else str(unit.type)
        }
        
    except Exception as e:
        app_logger.error(f"Can transport move check failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('load_transport_unit')
@log_rpc_performance
def load_transport_unit_rpc(token: str, transport_x: int, transport_y: int, 
                           cargo_x: int, cargo_y: int) -> dict:
    """Load unit into transport"""
    try:
        mngr = game_load(token)
        
        if not mngr.board.game_active:
            return {"success": False, "error": "Game has ended"}
        
        # Get units
        transport = mngr.unit_at(transport_x, transport_y)
        cargo = mngr.unit_at(cargo_x, cargo_y)
        
        if not transport:
            return {"success": False, "error": "No transport unit found"}
        if not cargo:
            return {"success": False, "error": "No cargo unit found"}
        
        # Check turn ownership
        if transport.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        # Execute loading
        result = mngr.load_transport_unit(transport, cargo, transport_x, transport_y, cargo_x, cargo_y)
        
        if result.success:
            # Log the action
            app_logger.info(f"Unit loaded: {token} - {cargo.type.name} into {transport.type.name}")
            
            # Save game state
            game_save(mngr, token)
            ws_board_update(token)
        
        return {
            "success": result.success,
            "message": result.message,
            "cargo_index": result.cargo_index,
            "transport_info": mngr.get_transport_cargo_info(transport)
        }
        
    except Exception as e:
        app_logger.error(f"Load transport unit failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('unload_transport_unit')
@log_rpc_performance
def unload_transport_unit_rpc(token: str, transport_x: int, transport_y: int, 
                             unload_x: int, unload_y: int, cargo_index: int = 0) -> dict:
    """Unload unit from transport"""
    try:
        mngr = game_load(token)
        
        if not mngr.board.game_active:
            return {"success": False, "error": "Game has ended"}
        
        # Get transport
        transport = mngr.unit_at(transport_x, transport_y)
        if not transport:
            return {"success": False, "error": "No transport unit found"}
        
        # Check turn ownership
        if transport.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        # Execute unloading
        result = mngr.unload_transport_unit(transport, cargo_index, transport_x, transport_y, unload_x, unload_y)
        
        if result.success:
            # Log the action
            app_logger.info(f"Unit unloaded: {token} - from {transport.type.name} to ({unload_x}, {unload_y})")
            
            # Save game state
            game_save(mngr, token)
            ws_board_update(token)
        
        return {
            "success": result.success,
            "message": result.message,
            "unloaded_position": result.unloaded_position,
            "transport_info": mngr.get_transport_cargo_info(transport)
        }
        
    except Exception as e:
        app_logger.error(f"Unload transport unit failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('get_transport_info')
@log_rpc_performance
def get_transport_info_rpc(token: str, x: int, y: int) -> dict:
    """Get detailed transport information"""
    try:
        mngr = game_load(token)
        unit = mngr.unit_at(x, y)
        
        if not unit:
            return {"success": False, "error": "No unit found"}
        
        if not mngr.is_transport_unit(unit):
            return {"success": False, "error": "Unit is not a transport"}
        
        # Get transport capabilities
        capability = mngr.get_transport_capability(unit)
        cargo_info = mngr.get_transport_cargo_info(unit)
        
        # Get movement status
        can_move = mngr.can_transport_move(unit)
        can_load_unload = mngr.can_transport_load_unload(unit)
        
        return {
            "success": True,
            "unit_type": unit.type.name if hasattr(unit.type, 'name') else str(unit.type),
            "max_capacity": capability.max_capacity if capability else 0,
            "compatible_units": capability.compatible_units if capability else [],
            "loading_terrain": capability.loading_terrain if capability else None,
            "can_resupply": capability.can_resupply if capability else False,
            "can_repair": capability.can_repair if capability else False,
            "cargo_info": cargo_info,
            "movement_status": {
                "can_move": can_move,
                "can_load_unload": can_load_unload,
                "has_moved_this_turn": getattr(unit.status, 'has_moved_this_turn', False)
            }
        }
        
    except Exception as e:
        app_logger.error(f"Get transport info failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('get_valid_unload_positions')
@log_rpc_performance
def get_valid_unload_positions_rpc(token: str, x: int, y: int) -> dict:
    """Get valid positions where transport can unload cargo"""
    try:
        mngr = game_load(token)
        transport = mngr.unit_at(x, y)
        
        if not transport:
            return {"success": False, "error": "No unit found"}
        
        if not mngr.is_transport_unit(transport):
            return {"success": False, "error": "Unit is not a transport"}
        
        # Get valid unload positions
        valid_positions = mngr.transport_system.get_valid_unload_positions(x, y)
        
        return {
            "success": True,
            "valid_positions": [{"x": pos[0], "y": pos[1]} for pos in valid_positions],
            "transport_info": mngr.get_transport_cargo_info(transport)
        }
        
    except Exception as e:
        app_logger.error(f"Get valid unload positions failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}


# =============================================================================
# TRANSPORT UTILITY METHODS
# =============================================================================

@jsonrpc.method('get_transport_summary')
@log_rpc_performance
def get_transport_summary_rpc(token: str) -> dict:
    """Get summary of all transports and their cargo for current army"""
    try:
        mngr = game_load(token)
        current_army = mngr.board.current_turn
        
        transport_system = CompleteTransportSystem(mngr)
        transports = []
        
        for tile in mngr.board.grid:
            if (tile.unit and tile.unit.army == current_army and 
                transport_system.is_transport_unit(tile.unit)):
                
                transport_info = transport_system.get_cargo_info(tile.unit)
                transport_info.update({
                    "x": tile.x,
                    "y": tile.y,
                    "can_move": tile.unit.can_move,
                    "hp": tile.unit.status.hp,
                    "fuel": tile.unit.status.fuel
                })
                transports.append(transport_info)
        
        return {
            "success": True,
            "transports": transports,
            "count": len(transports),
            "army": current_army.name if hasattr(current_army, 'name') else str(current_army)
        }
        
    except Exception as e:
        app_logger.error(f"Get transport summary failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}


@jsonrpc.method('get_cargo_info')
@log_rpc_performance
def get_cargo_info_rpc(token: str, x: int, y: int) -> dict:
    """Get detailed cargo information for a unit"""
    try:
        mngr = game_load(token)
        
        # Validate coordinates
        if not (0 <= x < mngr.board.width and 0 <= y < mngr.board.height):
            return {"success": False, "error": "Invalid coordinates"}
        
        # Get unit
        unit = mngr.unit_at(x, y)
        if not unit:
            return {"success": False, "error": "No unit found"}
        
        # Check turn
        if unit.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        # Get cargo info
        transport_system = CompleteTransportSystem(mngr)
        cargo_info = transport_system.get_cargo_info(unit)
        
        # Get compatible types safely (only if unit is actually a transport)
        compatible_types = []
        if cargo_info.get("is_transport", False):
            try:
                compatible_types = transport_system.get_compatible_cargo_types(unit)
            except (AttributeError, TypeError) as e:
                app_logger.warning(f"Could not get compatible types for unit: {str(e)}")
                compatible_types = []
        
        return {
            "success": True,
            "cargo_info": cargo_info,
            "compatible_types": compatible_types
        }
        
    except Exception as e:
        app_logger.error(f"Get cargo info failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('get_loadable_units')
@log_rpc_performance
def get_loadable_units_rpc(token: str, x: int, y: int) -> dict:
    """Get all units that can be loaded into this transport"""
    try:
        mngr = game_load(token)
        
        # Validate coordinates
        if not (0 <= x < mngr.board.width and 0 <= y < mngr.board.height):
            return {"success": False, "error": "Invalid coordinates"}
        
        # Get transport
        transport = mngr.unit_at(x, y)
        if not transport:
            return {"success": False, "error": "No unit found"}
        
        # Check turn
        if transport.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        transport_system = CompleteTransportSystem(mngr)
        
        # Check if it's a transport unit
        if not transport_system.is_transport_unit(transport):
            return {
                "success": True,
                "loadable_units": [],
                "message": "Unit is not a transport"
            }
        
        loadable_units = []
        
        # Check all adjacent tiles
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # N, S, E, W
        
        for dx, dy in directions:
            cargo_x = x + dx
            cargo_y = y + dy
            
            # Check if position is on board
            if not (0 <= cargo_x < mngr.board.width and 0 <= cargo_y < mngr.board.height):
                continue
            
            # Check if there's a unit there
            cargo_unit = mngr.unit_at(cargo_x, cargo_y)
            if not cargo_unit:
                continue
            
            # Check if it can be loaded
            can_load, message = transport_system.can_load_unit(
                transport, cargo_unit, x, y, cargo_x, cargo_y
            )
            
            if can_load:
                loadable_units.append({
                    "x": cargo_x,
                    "y": cargo_y,
                    "unit_type": cargo_unit.type.name if hasattr(cargo_unit.type, 'name') else str(cargo_unit.type),
                    "army": cargo_unit.army.name if hasattr(cargo_unit.army, 'name') else str(cargo_unit.army),
                    "hp": cargo_unit.status.hp
                })
        
        return {
            "success": True,
            "loadable_units": loadable_units,
            "transport_info": transport_system.get_cargo_info(transport)
        }
        
    except Exception as e:
        app_logger.error(f"Get loadable units failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('load_unit')
@log_rpc_performance
def load_unit_rpc(token: str, transport_x: int, transport_y: int, 
                 cargo_x: int, cargo_y: int) -> dict:
    """Load a unit into transport"""
    try:
        mngr = game_load(token)
        
        # Validate game state
        if not mngr.board.game_active:
            return {"success": False, "error": "Game has ended"}
        
        # Validate coordinates
        coords = [transport_x, transport_y, cargo_x, cargo_y]
        if not all(0 <= coord < mngr.board.width or 0 <= coord < mngr.board.height for coord in coords):
            return {"success": False, "error": "Invalid coordinates"}
        
        # Get units
        transport = mngr.unit_at(transport_x, transport_y)
        cargo = mngr.unit_at(cargo_x, cargo_y)
        
        if not transport:
            return {"success": False, "error": "No transport unit found"}
        if not cargo:
            return {"success": False, "error": "No cargo unit found"}
        
        # Check turn
        if transport.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        # Execute loading
        transport_system = CompleteTransportSystem(mngr)
        result = transport_system.load_unit_enhanced(
            transport, cargo, transport_x, transport_y, cargo_x, cargo_y
        )
        
        if result.success:
            # Log the action
            log_game_event('UNIT_LOADED', token, {
                'transport': f"{transport.army.name} {transport.type.name}",
                'cargo': f"{cargo.army.name} {cargo.type.name}",
                'position': f"({transport_x}, {transport_y})",
                'cargo_index': result.cargo_index
            })
            
            app_logger.info(f"Unit loaded: {token} - {cargo.type.name} into {transport.type.name} at ({transport_x}, {transport_y})")
            
            # Save game state
            game_save(mngr, token)
            ws_board_update(token)
        
        return {
            "success": result.success,
            "message": result.message,
            "cargo_index": result.cargo_index,
            "transport_info": transport_system.get_cargo_info(transport)
        }
        
    except Exception as e:
        app_logger.error(f"Load unit failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('unload_unit')
@log_rpc_performance
def unload_unit_rpc(token: str, transport_x: int, transport_y: int, 
                   unload_x: int, unload_y: int, cargo_index: int = 0) -> dict:
    """Unload a unit from transport"""
    try:
        mngr = game_load(token)
        
        # Validate game state
        if not mngr.board.game_active:
            return {"success": False, "error": "Game has ended"}
        
        # Validate coordinates
        coords = [transport_x, transport_y, unload_x, unload_y]
        if not all(0 <= coord < mngr.board.width or 0 <= coord < mngr.board.height for coord in coords):
            return {"success": False, "error": "Invalid coordinates"}
        
        # Get transport
        transport = mngr.unit_at(transport_x, transport_y)
        if not transport:
            return {"success": False, "error": "No transport unit found"}
        
        # Check turn
        if transport.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        # Execute unloading
        transport_system = CompleteTransportSystem(mngr)
        result = transport_system.unload_unit_enhanced(
            transport, cargo_index, transport_x, transport_y, unload_x, unload_y
        )
        
        if result.success:
            # Log the action
            log_game_event('UNIT_UNLOADED', token, {
                'transport': f"{transport.army.name} {transport.type.name}",
                'position': f"({transport_x}, {transport_y})",
                'unload_position': f"({unload_x}, {unload_y})",
                'cargo_index': cargo_index
            })
            
            app_logger.info(f"Unit unloaded: {token} - from {transport.type.name} at ({transport_x}, {transport_y}) to ({unload_x}, {unload_y})")
            
            # Save game state
            game_save(mngr, token)
            ws_board_update(token)
        
        return {
            "success": result.success,
            "message": result.message,
            "unloaded_position": result.unloaded_position,
            "transport_info": transport_system.get_cargo_info(transport)
        }
        
    except Exception as e:
        app_logger.error(f"Unload unit failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('get_transport_units')
@log_rpc_performance
def get_transport_units_rpc(token: str) -> dict:
    """Get all transport units for the current army"""
    try:
        mngr = game_load(token)
        current_army = mngr.board.current_turn
        
        transport_system = CompleteTransportSystem(mngr)
        transport_units = []
        
        # Find all transport units for current army
        for tile in mngr.board.grid:
            if tile.unit and tile.unit.army == current_army:
                if transport_system.is_transport_unit(tile.unit):
                    cargo_info = transport_system.get_cargo_info(tile.unit)
                    transport_units.append({
                        "x": tile.x,
                        "y": tile.y,
                        "unit_type": tile.unit.type.name if hasattr(tile.unit.type, 'name') else str(tile.unit.type),
                        "cargo_info": cargo_info
                    })
        
        return {
            "success": True,
            "transport_units": transport_units,
            "count": len(transport_units),
            "army": current_army.name if hasattr(current_army, 'name') else str(current_army)
        }
        
    except Exception as e:
        app_logger.error(f"Get transport units failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('can_load_unit')
@log_rpc_performance
def can_load_unit_rpc(token: str, transport_x: int, transport_y: int, 
                     cargo_x: int, cargo_y: int) -> dict:
    """Check if a unit can be loaded into transport"""
    try:
        mngr = game_load(token)
        
        # Validate coordinates
        coords = [transport_x, transport_y, cargo_x, cargo_y]
        if not all(0 <= coord < mngr.board.width or 0 <= coord < mngr.board.height for coord in coords):
            return {"success": False, "error": "Invalid coordinates"}
        
        # Get units
        transport = mngr.unit_at(transport_x, transport_y)
        cargo = mngr.unit_at(cargo_x, cargo_y)
        
        if not transport:
            return {"success": False, "error": "No transport unit found"}
        if not cargo:
            return {"success": False, "error": "No cargo unit found"}
        
        # Check turn
        if transport.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        # Use transport system
        transport_system = CompleteTransportSystem(mngr)
        can_load, message = transport_system.can_load_unit(
            transport, cargo, transport_x, transport_y, cargo_x, cargo_y
        )
        
        return {
            "success": True,
            "can_load": can_load,
            "message": message,
            "transport_info": transport_system.get_cargo_info(transport)
        }
        
    except Exception as e:
        app_logger.error(f"Can load unit failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('can_unload_unit')
@log_rpc_performance
def can_unload_unit_rpc(token: str, transport_x: int, transport_y: int,
                       unload_x: int, unload_y: int, cargo_index: int = 0) -> dict:
    """Check if a unit can be unloaded at a specific position"""
    try:
        mngr = game_load(token)
        
        # Validate coordinates
        coords = [transport_x, transport_y, unload_x, unload_y]
        if not all(0 <= coord < mngr.board.width or 0 <= coord < mngr.board.height for coord in coords):
            return {"success": False, "error": "Invalid coordinates"}
        
        # Get transport
        transport = mngr.unit_at(transport_x, transport_y)
        if not transport:
            return {"success": False, "error": "No transport unit found"}
        
        # Check turn
        if transport.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        # Check if can unload
        transport_system = CompleteTransportSystem(mngr)
        can_unload, message = transport_system.can_unload_unit(
            transport, cargo_index, transport_x, transport_y, unload_x, unload_y
        )
        
        return {
            "success": True,
            "can_unload": can_unload,
            "message": message,
            "transport_info": transport_system.get_cargo_info(transport)
        }
        
    except Exception as e:
        app_logger.error(f"Can unload unit failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('repair_unit')
@log_rpc_performance
def repair_unit_rpc(token: str, blackboat_x: int, blackboat_y: int, 
                    target_x: int, target_y: int, hp_to_repair: int = 1) -> dict:
    """
    Black Boat manual repair command
    Repairs adjacent unit up to 2 HP (max 10 HP total) AND resupplies fuel/ammo (costs 10% of unit cost per HP)
    """
    try:
        mngr = game_load(token)
        
        # Validate coordinates
        coords = [blackboat_x, blackboat_y, target_x, target_y]
        if not all(0 <= coord < mngr.board.width or 0 <= coord < mngr.board.height for coord in coords):
            return {"success": False, "error": "Invalid coordinates"}
        
        # Get units
        blackboat = mngr.unit_at(blackboat_x, blackboat_y)
        target = mngr.unit_at(target_x, target_y)
        
        if not blackboat:
            return {"success": False, "error": "No unit at Black Boat position"}
        if not target:
            return {"success": False, "error": "No unit at target position"}
        
        # Verify it's a Black Boat (could be BLACK_BOAT or BLACKBOAT)
        unit_type = blackboat.type.name if hasattr(blackboat.type, 'name') else str(blackboat.type)
        if unit_type not in ['BLACK_BOAT', 'BLACKBOAT']:
            return {"success": False, "error": f"Unit at ({blackboat_x}, {blackboat_y}) is not a Black Boat (found: {unit_type})"}
        
        # Check turn ownership
        if blackboat.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        # Check target is friendly
        if target.army != blackboat.army:
            return {"success": False, "error": "Can only repair friendly units"}
        
        # Check adjacency (Manhattan distance = 1)
        distance = abs(blackboat_x - target_x) + abs(blackboat_y - target_y)
        if distance != 1:
            return {"success": False, "error": "Target must be adjacent to Black Boat"}
        
        # Black Boat can only repair units up to 10 visual HP (91-100 actual HP)
        # But can still resupply units at full HP
        can_repair_hp = target.status.hp <= 90
        
        # Validate hp_to_repair (1-2 HP max)
        hp_to_repair = max(1, min(2, hp_to_repair))
        
        # Calculate actual HP to repair
        if can_repair_hp:
            actual_hp_to_repair = min(hp_to_repair, 100 - target.status.hp)
        else:
            actual_hp_to_repair = 0
        
        # Calculate cost (10% of unit cost per HP repaired)
        repair_cost = 0
        if actual_hp_to_repair > 0:
            unit_cost = mngr.config.units[target.type.name].cost
            repair_cost = int(unit_cost * 0.1 * actual_hp_to_repair)
            
            # Check funds
            current_funds = mngr._get_army_funds(blackboat.army)
            if current_funds < repair_cost:
                return {
                    "success": False, 
                    "error": f"Insufficient funds. Need {repair_cost}, have {current_funds}"
                }
        
        # Perform repair (if applicable)
        old_hp = target.status.hp
        if actual_hp_to_repair > 0:
            target.status.hp = min(100, target.status.hp + actual_hp_to_repair)
        new_hp = target.status.hp
        
        # ALSO RESUPPLY fuel and ammo (Black Boat repair includes resupply)
        old_fuel = target.status.fuel
        old_ammo = getattr(target.status, 'ammo', None)
        
        # Get max values for this unit type
        max_fuel = mngr.config.units[target.type.name].fuel
        max_ammo = mngr.config.units[target.type.name].ammo if hasattr(mngr.config.units[target.type.name], 'ammo') else None
        
        # Resupply to maximum
        target.status.fuel = max_fuel
        fuel_resupplied = max_fuel - old_fuel
        
        ammo_resupplied = 0
        new_ammo = old_ammo
        if max_ammo is not None and hasattr(target.status, 'ammo'):
            target.status.ammo = max_ammo
            ammo_resupplied = max_ammo - (old_ammo or 0)
            new_ammo = max_ammo
        
        # Deduct funds (only for repair, resupply is FREE)
        if blackboat.army == Army.RED:
            mngr.board.red_funds -= repair_cost
        elif blackboat.army == Army.BLUE:
            mngr.board.blue_funds -= repair_cost
        elif hasattr(mngr.board, 'army_funds') and blackboat.army in mngr.board.army_funds:
            mngr.board.army_funds[blackboat.army] -= repair_cost
        
        # Save changes
        game_save(mngr, token)
        
        # Log event
        if ENHANCED_LOGGING:
            game_logger.info(f"REPAIR_AND_RESUPPLY: {token} - Black Boat at ({blackboat_x},{blackboat_y}) repaired {target.type.name} at ({target_x},{target_y}) for {actual_hp_to_repair} HP + resupplied fuel/ammo (cost: {repair_cost})")
        
        app_logger.info(f"Unit repaired & resupplied: {token} - Black Boat at ({blackboat_x},{blackboat_y}) repaired {target.type} at ({target_x},{target_y}) for {actual_hp_to_repair} HP + fuel/ammo (cost: {repair_cost})")
        
        # Notify via websocket
        update_msg = {
            "type": "unit_repaired_and_resupplied",
            "blackboat_position": {"x": blackboat_x, "y": blackboat_y},
            "target_position": {"x": target_x, "y": target_y},
            "hp_repaired": actual_hp_to_repair,
            "new_hp": new_hp,
            "fuel_resupplied": fuel_resupplied,
            "ammo_resupplied": ammo_resupplied,
            "repair_cost": repair_cost,
            "remaining_funds": mngr._get_army_funds(blackboat.army)
        }
        ws_board_update(token)
        
        return {
            "success": True,
            "message": f"Repaired {actual_hp_to_repair} HP + resupplied fuel/ammo for {repair_cost} funds" if actual_hp_to_repair > 0 else "Resupplied fuel/ammo (FREE)",
            "hp_repaired": actual_hp_to_repair,
            "old_hp": old_hp,
            "new_hp": new_hp,
            "fuel_resupplied": fuel_resupplied,
            "ammo_resupplied": ammo_resupplied,
            "new_fuel": target.status.fuel,
            "new_ammo": new_ammo,
            "repair_cost": repair_cost,
            "remaining_funds": mngr._get_army_funds(blackboat.army)
        }
        
    except Exception as e:
        app_logger.error(f"Repair unit failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('resupply_unit')
@log_rpc_performance
def resupply_unit_rpc(token: str, resupply_x: int, resupply_y: int, 
                      target_x: int, target_y: int, fuel_amount: int = 10, ammo_amount: int = 10) -> dict:
    """
    Manual resupply command for Black Boats and APCs
    Resupplies adjacent unit with fuel and ammo (FREE - no cost)
    """
    try:
        mngr = game_load(token)
        
        # Validate coordinates
        coords = [resupply_x, resupply_y, target_x, target_y]
        if not all(0 <= coord < mngr.board.width or 0 <= coord < mngr.board.height for coord in coords):
            return {"success": False, "error": "Invalid coordinates"}
        
        # Get units
        resupply_unit = mngr.unit_at(resupply_x, resupply_y)
        target = mngr.unit_at(target_x, target_y)
        
        if not resupply_unit:
            return {"success": False, "error": "No unit at resupply position"}
        if not target:
            return {"success": False, "error": "No unit at target position"}
        
        # Verify it's a resupply unit (Black Boat or APC)
        unit_type = resupply_unit.type.name if hasattr(resupply_unit.type, 'name') else str(resupply_unit.type)
        if unit_type not in ['BLACK_BOAT', 'BLACKBOAT', 'APC']:
            return {"success": False, "error": f"Unit at ({resupply_x}, {resupply_y}) cannot resupply (found: {unit_type}). Only Black Boats and APCs can manually resupply."}
        
        # Check turn ownership
        if resupply_unit.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        # Check target is friendly
        if target.army != resupply_unit.army:
            return {"success": False, "error": "Can only resupply friendly units"}
        
        # Check adjacency (Manhattan distance = 1)
        distance = abs(resupply_x - target_x) + abs(resupply_y - target_y)
        if distance != 1:
            return {"success": False, "error": "Target must be adjacent to resupply unit"}
        
        # Get target's max fuel/ammo and current fuel/ammo
        target_max_fuel = mngr.config.units[target.type].fuel
        target_max_ammo = mngr.config.units[target.type].ammo if hasattr(mngr.config.units[target.type], 'ammo') else 0
        
        current_fuel = target.fuel if hasattr(target, 'fuel') else target.status.fuel
        current_ammo = target.ammo if hasattr(target, 'ammo') else (target.status.ammo if hasattr(target.status, 'ammo') else 0)
        
        # Check if target needs resupply
        fuel_needed = target_max_fuel - current_fuel
        ammo_needed = target_max_ammo - current_ammo if target_max_ammo > 0 else 0
        
        if fuel_needed <= 0 and ammo_needed <= 0:
            return {"success": False, "error": "Target is already fully supplied"}
        
        # Calculate actual amounts to resupply (can't exceed max)
        actual_fuel_to_resupply = min(fuel_amount, fuel_needed) if fuel_needed > 0 else 0
        actual_ammo_to_resupply = min(ammo_amount, ammo_needed) if ammo_needed > 0 else 0
        
        # Resupply is free (no cost like APC auto-resupply)
        
        # Perform resupply
        old_fuel = current_fuel
        old_ammo = current_ammo
        
        # Resupply fuel
        if actual_fuel_to_resupply > 0:
            if hasattr(target, 'fuel'):
                target.fuel = min(target_max_fuel, target.fuel + actual_fuel_to_resupply)
                new_fuel = target.fuel
            else:
                target.status.fuel = min(target_max_fuel, target.status.fuel + actual_fuel_to_resupply)
                new_fuel = target.status.fuel
        else:
            new_fuel = current_fuel
        
        # Resupply ammo
        if actual_ammo_to_resupply > 0:
            if hasattr(target, 'ammo'):
                target.ammo = min(target_max_ammo, target.ammo + actual_ammo_to_resupply)
                new_ammo = target.ammo
            else:
                if hasattr(target.status, 'ammo'):
                    target.status.ammo = min(target_max_ammo, target.status.ammo + actual_ammo_to_resupply)
                    new_ammo = target.status.ammo
                else:
                    new_ammo = current_ammo
        else:
            new_ammo = current_ammo
        
        # Save changes
        game_save(mngr, token)
        
        # Log event
        if ENHANCED_LOGGING:
            game_event_logger.log_event(
                game_id=token,
                event_type="RESUPPLY",
                details={
                    "resupply_position": [resupply_x, resupply_y],
                    "resupply_type": unit_type,
                    "target_position": [target_x, target_y],
                    "target_type": target.type.name if hasattr(target.type, 'name') else str(target.type),
                    "fuel_resupplied": actual_fuel_to_resupply,
                    "ammo_resupplied": actual_ammo_to_resupply,
                    "old_fuel": old_fuel,
                    "new_fuel": new_fuel,
                    "old_ammo": old_ammo,
                    "new_ammo": new_ammo
                }
            )
        
        app_logger.info(f"Unit resupplied: {token} - {unit_type} at ({resupply_x},{resupply_y}) resupplied {target.type} at ({target_x},{target_y}) - Fuel: {actual_fuel_to_resupply}, Ammo: {actual_ammo_to_resupply} (FREE)")
        
        # Notify via websocket
        update_msg = {
            "type": "unit_resupplied",
            "resupply_position": {"x": resupply_x, "y": resupply_y},
            "resupply_type": unit_type,
            "target_position": {"x": target_x, "y": target_y},
            "fuel_resupplied": actual_fuel_to_resupply,
            "ammo_resupplied": actual_ammo_to_resupply,
            "new_fuel": new_fuel,
            "new_ammo": new_ammo
        }
        ws_board_update(token)
        
        return {
            "success": True,
            "message": f"Resupplied {actual_fuel_to_resupply} fuel and {actual_ammo_to_resupply} ammo (FREE)",
            "fuel_resupplied": actual_fuel_to_resupply,
            "ammo_resupplied": actual_ammo_to_resupply,
            "old_fuel": old_fuel,
            "new_fuel": new_fuel,
            "old_ammo": old_ammo,
            "new_ammo": new_ammo,
            "max_fuel": target_max_fuel,
            "max_ammo": target_max_ammo,
            "resupply_unit_type": unit_type
        }
        
    except Exception as e:
        app_logger.error(f"Resupply unit failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

# =============================================================================
# PHASE 2A: ENHANCED COMBAT RPC METHODS
# =============================================================================

@jsonrpc.method('get_attack_targets')
@log_rpc_performance
def get_attack_targets_rpc(token: str, unit_x: int, unit_y: int) -> dict:
    """Get all valid attack targets for a unit (simplified version)"""
    try:
        mngr = game_load(token)
        
        unit = mngr.unit_at(unit_x, unit_y)
        if not unit:
            return {"success": False, "error": "No unit at specified position"}
        
        if unit.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your unit"}
        
        targets = []
        
        # Simple target finding - check all positions on the board
        for x in range(mngr.board.width):
            for y in range(mngr.board.height):
                target_unit = mngr.unit_at(x, y)
                if target_unit and target_unit.army != unit.army:
                    distance = abs(unit_x - x) + abs(unit_y - y)
                    
                    # Check basic range
                    if unit.status.rangemin <= distance <= unit.status.rangemax:
                        targets.append({
                            "x": x,
                            "y": y,
                            "unit_type": target_unit.type.name if hasattr(target_unit.type, 'name') else str(target_unit.type),
                            "army": target_unit.army.name if hasattr(target_unit.army, 'name') else str(target_unit.army),
                            "hp": target_unit.status.hp,
                            "distance": distance
                        })
        
        return {
            "success": True,
            "targets": targets,
            "unit_range": f"{unit.status.rangemin}-{unit.status.rangemax}",
            "is_indirect": False  # Simplified for now
        }
        
    except Exception as e:
        app_logger.error(f"Get attack targets failed: {token} - {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@jsonrpc.method('combat_preview')
@log_rpc_performance
def combat_preview_rpc(token: str, attacker_x: int, attacker_y: int, 
                      defender_x: int, defender_y: int) -> dict:
    """Get combat preview using existing damage calculation"""
    try:
        mngr = game_load(token)
        
        # Validate inputs
        if not (0 <= attacker_x < mngr.board.width and 0 <= attacker_y < mngr.board.height):
            return {"success": False, "error": f"Invalid attacker position: ({attacker_x}, {attacker_y})"}
        
        if not (0 <= defender_x < mngr.board.width and 0 <= defender_y < mngr.board.height):
            return {"success": False, "error": f"Invalid defender position: ({defender_x}, {defender_y})"}
        
        attacker = mngr.unit_at(attacker_x, attacker_y)
        defender = mngr.unit_at(defender_x, defender_y)
        
        if not attacker:
            return {"success": False, "error": "No unit at attacker position"}
        if not defender:
            return {"success": False, "error": "No unit at defender position"}
        
        if attacker.army != mngr.board.current_turn:
            return {"success": False, "error": "Not your turn to attack with this unit"}
        
        if attacker.army == defender.army:
            return {"success": False, "error": "Cannot attack friendly units"}
        
        # Use existing damage preview from manager
        preview = mngr.get_damage_preview(attacker_x, attacker_y, defender_x, defender_y)
        
        if "error" in preview:
            return {"success": False, "error": preview["error"]}
        
        app_logger.info(f"Combat preview: {token} - {attacker.army.name}:{attacker.type.name} vs {defender.army.name}:{defender.type.name}")
        
        return {
            "success": True,
            "attacker_damage": preview.get("attacker_damage", 0),
            "counter_damage": preview.get("counter_damage", 0),
            "can_counter": preview.get("can_counter", False),
            "attacker_hp_after": preview.get("attacker_hp_after", attacker.status.hp),
            "defender_hp_after": preview.get("defender_hp_after", defender.status.hp),
            "attacker_destroyed": preview.get("attacker_destroyed", False),
            "defender_destroyed": preview.get("defender_destroyed", False),
            "terrain_bonus": 0,  # We'll add this later
            "damage_range": f"{preview.get('attacker_damage', 0)}-{preview.get('attacker_damage', 0) + 9}",
            "ammo_warning": False  # We'll add this later
        }
        
    except Exception as e:
        app_logger.error(f"Combat preview failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('unit_attack')
@log_rpc_performance
def unit_attack_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    """
    Standard unit attack method - maintains frontend compatibility
    
    Args:
        token: Game token
        x, y: Attacker coordinates  
        x2, y2: Defender coordinates
        
    Note: This is an alias for unit_attack_enhanced with legacy parameter names
    """
    return unit_attack_enhanced_rpc(token, x, y, x2, y2)

@jsonrpc.method('unit_attack_enhanced')
@log_rpc_performance  
def unit_attack_enhanced_rpc(token: str, attacker_x: int, attacker_y: int,
                            defender_x: int, defender_y: int) -> dict:
    """Enhanced unit attack - uses existing attack system for now"""
    try:
        mngr = game_load(token)
        
        # Use existing attack system
        result = mngr.unit_attack_enhanced(attacker_x, attacker_y, defender_x, defender_y)
        
        # Check for win condition after combat
        winner = mngr.check_win_condition()
        if winner:
            mngr.board.game_active = False
            mngr.board.winner = winner
            app_logger.info(f"Game ended: {winner.name} wins after combat in {token}")
            
            # Log game end event
            log_game_event('GAME_ENDED', token, {
                'winner': winner.name,
                'reason': 'All enemy units destroyed',
                'final_day': mngr.board.days
            })
                
        # Save game state
        game_save(mngr, token)
        ws_board_update(token)
        
        return {
            "success": True,
            "combat_result": {
                "attacker_damage": result.attacker_damage_dealt,
                "defender_damage": result.defender_damage_dealt,
                "attacker_hp_before": result.attacker_hp_before,
                "attacker_hp_after": result.attacker_hp_after,
                "defender_hp_before": result.defender_hp_before,
                "defender_hp_after": result.defender_hp_after,
                "attacker_destroyed": result.attacker_destroyed,
                "defender_destroyed": result.defender_destroyed,
                "counter_attack_occurred": result.counter_attack_occurred,
                "terrain_bonus": 0,
                "luck_attacker": 0,
                "luck_defender": 0
            }
        }
        
    except Exception as e:
        app_logger.error(f"Enhanced combat failed: {token} - {str(e)}")
        return {"success": False, "error": str(e)}

@jsonrpc.method('get_damage_chart')
@log_rpc_performance  
def get_damage_chart_rpc(token: str) -> dict:
    """Get the complete damage chart for reference"""
    try:
        from unit import DAMAGE_TABLE, UnitType
        
        # Convert damage table to readable format
        damage_chart = {}
        
        for attacker_type in UnitType:
            damage_chart[attacker_type.name] = {}
            for defender_type in UnitType:
                try:
                    damage = DAMAGE_TABLE[attacker_type][defender_type.value]
                    damage_chart[attacker_type.name][defender_type.name] = damage
                except (KeyError, IndexError):
                    damage_chart[attacker_type.name][defender_type.name] = 0
        
        return {
            "success": True,
            "damage_chart": damage_chart
        }
        
    except Exception as e:
        app_logger.error(f"Get damage chart failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@jsonrpc.method('get_movement_costs')
def get_movement_costs(unit_type: str, token: str) -> dict:
    """Get movement costs for a unit type across all terrain types"""
    try:
        mngr = game_load(token)
        
        # Get movement costs from map_system
        from map_system import get_movement_cost_for_unit_on_terrain
        
        terrain_costs = {}
        terrain_types = [
            'PLAIN', 'WOOD', 'MOUNTAIN', 'ROAD_HORT', 'ROAD_VERT', 
            'ROAD_NW', 'ROAD_NE', 'ROAD_SE', 'ROAD_SW', 'CITY', 
            'FACTORY', 'AIRPORT', 'PORT', 'RIVER_HORT', 'RIVER_VERT',
            'BEACH_N', 'BEACH_E', 'BEACH_S', 'BEACH_W', 'SEA', 'REEF'
            # Add all your terrain types here
        ]
        
        for terrain in terrain_types:
            try:
                cost = get_movement_cost_for_unit_on_terrain(unit_type, terrain)
                terrain_costs[terrain] = cost
            except:
                terrain_costs[terrain] = 99  # Impassable
        
        return {
            "success": True,
            "unit_type": unit_type,
            "terrain_costs": terrain_costs
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@jsonrpc.method('get_movement_highlights')
def get_movement_highlights(token: str, x: int, y: int) -> dict:
    """Get valid movement positions for highlighting using the same logic as actual movement"""
    try:
        # Load the game
        mngr = game_load(token)
        
        # Validate coordinates
        if not (0 <= x < mngr.board.width and 0 <= y < mngr.board.height):
            return {
                "success": False,
                "error": f"Invalid coordinates ({x}, {y})"
            }
        
        # Get the unit at the position
        unit = mngr.unit_at(x, y)
        if not unit:
            return {
                "success": False,
                "error": "No unit at position"
            }
        
        # Get valid moves using the proper method
        valid_moves = []
        
        # Use the manager's get_unit_valid_moves method which uses EnhancedMovementValidator
        if hasattr(mngr, 'get_unit_valid_moves'):
            valid_positions = mngr.get_unit_valid_moves(unit)
            valid_moves = [{"x": pos[0], "y": pos[1]} for pos in valid_positions]
        else:
            # Fallback to checking every position
            for target_x in range(mngr.board.width):
                for target_y in range(mngr.board.height):
                    # Skip the unit's current position
                    if target_x == x and target_y == y:
                        continue
                    
                    try:
                        # Check if unit can move to this position
                        if hasattr(mngr, 'unit_can_move_to'):
                            can_move = mngr.unit_can_move_to(unit, target_x, target_y)
                        else:
                            # This should not happen anymore
                            can_move = False
                        
                        if can_move:
                            valid_moves.append({
                                "x": target_x,
                                "y": target_y
                            })
                            
                    except Exception as move_error:
                        # Skip this position if validation fails
                        app_logger.debug(f"Movement validation failed for ({target_x}, {target_y}): {move_error}")
                        continue
        
        app_logger.debug(f"Found {len(valid_moves)} valid moves for unit at ({x}, {y})")
        
        return {
            "success": True,
            "moves": valid_moves,
            "unit_type": unit.type.name if hasattr(unit, 'type') and hasattr(unit.type, 'name') else str(unit.type)
        }
        
    except Exception as e:
        app_logger.error(f"Error in get_movement_highlights: {str(e)}")
        return {
            "success": False,
            "error": f"Server error: {str(e)}"
        }
        
@app.route('/run_test', methods=['POST'])
def run_test():
    """Execute a test script and return results"""
    try:
        data = request.get_json()
        script_name = data.get('script')
        
        if not script_name:
            return "No script specified", 400
        
        # Security check - only allow specific test scripts
        allowed_scripts = [
            'test_combat_system.py',
            'test_economic_system.py', 
            'test_movement_system.py',
            'test_victory_conditions.py',
            'test_transport_final.py',
            'test_repair_refuel_proper.py',
            'updated_test_phase1.py',
            'test_multiplayer_armies.py'
        ]
        
        if script_name not in allowed_scripts:
            return f"Script {script_name} not allowed", 403
        
        # Map script names to their new locations in tests/ directory
        script_locations = {
            'test_combat_system.py': 'tests/unit/test_combat_system.py',
            'test_economic_system.py': 'tests/unit/test_economic_system.py',
            'test_movement_system.py': 'tests/unit/test_movement_system.py',
            'test_victory_conditions.py': 'tests/unit/test_victory_conditions.py',
            'test_transport_final.py': 'tests/unit/test_transport_features.py',
            'test_repair_refuel_proper.py': 'tests/unit/test_complete_repair_refuel.py',
            'updated_test_phase1.py': 'tests/system/updated_test_phase1.py',
            'test_multiplayer_armies.py': 'tests/integration/test_multiplayer_armies.py'
        }
        
        # Get the correct path for the moved test file
        relative_script_path = script_locations.get(script_name)
        if not relative_script_path:
            return f"Script {script_name} location not mapped", 404
            
        script_path = f"/home/box/Documents/aw-rpc/{relative_script_path}"
        
        if not os.path.exists(script_path):
            return f"Script {script_name} not found at {relative_script_path}", 404
        
        try:
            result = subprocess.run(
                ['python3', script_path],
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
                cwd='/home/box/Documents/aw-rpc'
            )
            
            output = f"Exit Code: {result.returncode}\n\n"
            
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n\n"
            
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            
            return output
            
        except subprocess.TimeoutExpired:
            return "Test script timeout (60 seconds)", 408
        except Exception as e:
            return f"Error executing script: {str(e)}", 500
        
    except Exception as e:
        app_logger.error(f"Error in run_test endpoint: {e}")
        return f"Internal server error: {str(e)}", 500

if __name__ == '__main__':
    app_logger.info("=== AW-RPC Application Starting ===")
    
    # Setup logging level from environment
    log_level_name = os.environ.get('LOG_LEVEL', 'INFO').upper()
    if hasattr(logging, log_level_name):
        log_level = getattr(logging, log_level_name)
        setup_logging(log_level)
    
    # Create tables
    with app.app_context():
        app_logger.info("Creating database tables...")
        db.create_all()
        db.session.commit()
        app_logger.info("Database tables created successfully")
    
    # Bind to PORT if defined, otherwise default to 5000
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    app_logger.info(f"Enhanced logging: {ENHANCED_LOGGING}")
    
    # Check map system availability
    map_system_available = 'map_repository' in globals()
    app_logger.info(f"Map system available: {map_system_available}")
    
    if map_system_available:
        try:
            # Test map repository functionality
            available_maps = map_repository.list_maps()
            app_logger.info(f"Available maps: {available_maps}")
            
            # Test getting a specific map
            test_map = map_repository.get_map('test')
            if test_map:
                app_logger.info(f"Test map loaded: {test_map.name} ({test_map.width}x{test_map.height})")
            else:
                app_logger.warning("Test map not found in repository")
                
        except Exception as e:
            app_logger.error(f"Error testing map system: {e}")
    else:
        app_logger.error("Map system not available - check imports")
    
    app_logger.info(f"Starting server on {host}:{port} (debug={debug})")
    app_logger.info("=== AW-RPC Application Ready ===")
    
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
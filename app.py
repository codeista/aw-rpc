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

from flask import redirect, render_template, abort, request
from flask_socketio import Namespace, join_room, leave_room
import jsons

from manager import GameManager
from gameboard import GameBoard
from config import Config
from app_core import app, jsonrpc, db, socketio
from models import Game
from map_system import map_repository, Map
from enhanced_combat_system import EnhancedCombatSystem, CombatPreview, EnhancedCombatResult
from transport_system import TransportSystem
from test_map_predeployed import get_predeployed_test_game, get_comprehensive_test_game

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
                print(f"SERIALIZATION_FIX: Parsed JSON string to dict")
            else:
                # It's already a dict (most common case)
                board_dict = board_data
                print(f"SERIALIZATION_FIX: Board data is already a dict")
            
            # RECONSTRUCT UNITS: Fix any dict units in the grid
            units_reconstructed = 0
            if 'grid' in board_dict:
                for i, tile_data in enumerate(board_dict['grid']):
                    if isinstance(tile_data, dict) and 'unit' in tile_data and tile_data['unit'] is not None:
                        unit_data = tile_data['unit']
                        
                        # If unit is a dict, reconstruct it
                        if isinstance(unit_data, dict):
                            print(f"SERIALIZATION_FIX: Reconstructing unit at grid index {i}")
                            try:
                                reconstructed_unit = reconstruct_unit_from_dict(unit_data)
                                tile_data['unit'] = reconstructed_unit
                                units_reconstructed += 1
                                print(f"SERIALIZATION_FIX: Successfully reconstructed unit {units_reconstructed}")
                            except Exception as unit_error:
                                print(f"SERIALIZATION_FIX: Failed to reconstruct unit at index {i}: {unit_error}")
                                # Set unit to None instead of leaving a broken dict
                                tile_data['unit'] = None
            
            print(f"SERIALIZATION_FIX: Reconstructed {units_reconstructed} units total")
            
            # Now try to deserialize with jsons - pass the dict directly, not as JSON
            try:
                board = jsons.loads(board_dict, GameBoard)
                print(f"SERIALIZATION_FIX: jsons.loads succeeded")
            except Exception as jsons_error:
                print(f"SERIALIZATION_FIX: jsons.loads failed: {jsons_error}")
                # Try alternative approach - create GameBoard manually
                board = create_board_from_dict(board_dict)
            
            mngr = GameManager(config_game, board)
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
            print(f"SERIALIZATION_FIX: Restored turn_order: {[army.name for army in turn_order]}")
        
        if 'current_turn' in board_dict:
            current_turn_data = board_dict['current_turn']
            if isinstance(current_turn_data, str):
                board.current_turn = Army[current_turn_data]
            elif hasattr(current_turn_data, 'name'):
                board.current_turn = Army[current_turn_data.name]
            else:
                board.current_turn = current_turn_data
            print(f"SERIALIZATION_FIX: Restored current_turn: {board.current_turn.name}")
        
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
        
        print(f"SERIALIZATION_FIX: Created board from dict manually with proper turn system")
        return board
        
    except Exception as e:
        print(f"SERIALIZATION_FIX: Manual board creation failed: {e}")
        print(f"SERIALIZATION_FIX: Board dict keys: {list(board_dict.keys()) if isinstance(board_dict, dict) else 'Not a dict'}")
        
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
            
            print(f"SERIALIZATION_FIX: Using minimal fallback board")
            return board
        except Exception as e2:
            print(f"SERIALIZATION_FIX: Even minimal fallback failed: {e2}")
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
        
        print(f"SERIALIZATION_FIX: Successfully reconstructed {unit_type_name} unit with proper status")
        return unit
        
    except Exception as e:
        # Enhanced fallback with proper UnitConfig
        print(f"SERIALIZATION_FIX: Failed to reconstruct unit from dict: {e}")
        print(f"SERIALIZATION_FIX: Unit dict keys: {list(unit_dict.keys()) if isinstance(unit_dict, dict) else 'Not a dict'}")
        
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
            print(f"SERIALIZATION_FIX: Even fallback failed: {e2}")
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
    # Count remaining units by army
    red_units = 0
    blue_units = 0
    
    for tile in mngr.board.grid:
        if tile.unit:
            if tile.unit.army.name == 'RED':
                red_units += 1
            elif tile.unit.army.name == 'BLUE':
                blue_units += 1
    
    app_logger.info(f'Victory check: RED={red_units}, BLUE={blue_units}')
    
    # Check for elimination victory
    if red_units == 0:
        # SET GAME INACTIVE + SAVE WINNER
        mngr.board.game_active = False
        mngr.board.winner = 'BLUE'
        mngr.board.victory_type = 'ELIMINATION'
        app_logger.info('GAME ENDED: BLUE wins by elimination')
        return {'victory': True, 'winner': 'BLUE', 'type': 'ELIMINATION'}
    elif blue_units == 0:
        # SET GAME INACTIVE + SAVE WINNER  
        mngr.board.game_active = False
        mngr.board.winner = 'RED'
        mngr.board.victory_type = 'ELIMINATION'
        app_logger.info('GAME ENDED: RED wins by elimination')
        return {'victory': True, 'winner': 'RED', 'type': 'ELIMINATION'}
    
    # Check for HQ capture victory (if implemented)
    # ... additional victory conditions
    
    return {'victory': False}

#
# REST Routes (Enhanced)
#

@app.route('/')
def index():
    new_token = secrets.token_urlsafe(4)
    app_logger.info(f"Index accessed, redirecting to new game: {new_token}")
    return redirect('/game/' + new_token)

@app.route('/game/<token>')
def game(token: str):
    app_logger.info(f"Game page accessed: {token}")
    return render_template('render.html', token=token)

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
            'map_system': 'map_system' in globals(),
            'total_methods': 0,
            'registered_methods': []
        }
        
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
        <p><a href="/">🎲 Random Game</a></p>
    </body>
    </html>
    '''

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

#
# JSONRPC Methods (Enhanced with logging)
#

@jsonrpc.method('troop_info')
@log_rpc_performance
def troop_info(token: str = None) -> dict:
    '''Returns the unit config info'''
    app_logger.info('troop_info requested')
    return jsons.dump(config_game.units)

@jsonrpc.method('message')
@log_rpc_performance
def message(token: str, msg: str) -> str:
    '''rpc chat'''
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

@jsonrpc.method('tile')
@log_rpc_performance
def tile_rpc(token: str, x: int, y: int) -> dict:
    '''rpc return tile at coordinates'''
    app_logger.debug(f'Tile requested: {token} at ({x},{y})')
    try:
        mngr = game_load(token)
        
        # Enhanced validation
        if x < 0 or y < 0 or x >= mngr.board.width or y >= mngr.board.height:
            raise Exception(f'coordinate out of range: x={x}, y={y}, max=({mngr.board.width-1},{mngr.board.height-1})')
        
        return jsons.dump(mngr.tile_get(x, y))
    except Exception as ex:
        app_logger.error(f'tile_rpc failed for {token} at ({x},{y}): {str(ex)}')
        return handle_rpc_error('tile', token, ex)

@jsonrpc.method('capture_tile')
@log_rpc_performance
def capture_tile_rpc(token: str, x: int, y: int) -> dict:
    '''rpc capture tile'''
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

@jsonrpc.method('unit_create')
@log_rpc_performance
def unit_create_rpc(token: str, army: str, unit_type: str, x: int, y: int) -> dict:
    """Create a unit with enhanced error handling and validation"""
    
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
            
        # Import validation functions
        from error_handling import validate_army, validate_unit_type, validate_coordinates, ValidationError
        
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

@jsonrpc.method('unit_attack')
@log_rpc_performance
def unit_attack_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    """Attack with enhanced validation and error handling + victory detection"""
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
    """
    try:
        # Correct parameter mapping:
        # x,y = cargo position (selected unit)
        # x2,y2 = transport position (alt-clicked)
        return load_unit_rpc(token, transport_x=x2, transport_y=y2, cargo_x=x, cargo_y=y)
        
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
        transport_system = TransportSystem(mngr)
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

@jsonrpc.method('produce_unit')
@log_rpc_performance
def produce_unit_rpc(token: str, x: int, y: int, unit_type: str) -> dict:
    """Produce a unit at a facility"""
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
# TRANSPORT SYSTEM RPC METHODS -
# =============================================================================

@jsonrpc.method('cargo_board_transport')
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
        transport_system = TransportSystem(mngr)
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
        transport_system = TransportSystem(mngr)
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
        transport_system = TransportSystem(mngr)
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
        transport_system = TransportSystem(mngr)
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
        transport_system = TransportSystem(mngr)
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
            transport_system = TransportSystem(mngr)
            
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
        
        transport_system = TransportSystem(mngr)
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
        transport_system = TransportSystem(mngr)
        cargo_info = transport_system.get_cargo_info(unit)
        
        return {
            "success": True,
            "cargo_info": cargo_info,
            "compatible_types": transport_system.get_compatible_cargo_types(unit) if cargo_info["is_transport"] else []
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
        
        transport_system = TransportSystem(mngr)
        
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
        transport_system = TransportSystem(mngr)
        result = transport_system.load_unit(
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
        transport_system = TransportSystem(mngr)
        result = transport_system.unload_unit(
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
        
        transport_system = TransportSystem(mngr)
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
        transport_system = TransportSystem(mngr)
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
        transport_system = TransportSystem(mngr)
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
def get_movement_costs(unit_type: str, token: str):
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
def get_movement_highlights(x: int, y: int, token: str) -> dict:
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
        
        # Get valid moves
        valid_moves = []
        
        # Check every position on the board
        for target_x in range(mngr.board.width):
            for target_y in range(mngr.board.height):
                # Skip the unit's current position
                if target_x == x and target_y == y:
                    continue
                
                try:
                    # Check if unit can move to this position
                    # Use whatever validation method exists in your manager
                    if hasattr(mngr, 'unit_can_move_to'):
                        can_move = mngr.unit_can_move_to(unit, target_x, target_y)
                    elif hasattr(mngr, 'can_unit_move_to'):
                        can_move = mngr.can_unit_move_to(unit, target_x, target_y)
                    else:
                        # Fallback - check if tile is empty and accessible
                        target_tile = mngr.tile_at(target_x, target_y)
                        can_move = (target_tile is not None and 
                                   mngr.unit_at(target_x, target_y) is None)
                    
                    if can_move:
                        valid_moves.append({
                            "x": target_x,
                            "y": target_y,
                            "cost": 1  # Default cost for now
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
    app_logger.info(f"Map system available: {'map_system' in globals()}")
    app_logger.info(f"Starting server on {host}:{port} (debug={debug})")
    app_logger.info("=== AW-RPC Application Ready ===")
    
    socketio.run(app, host=host, port=port, debug=debug)
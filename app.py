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
    '''Loads the game token specified'''
    app_logger.info(f"Loading game: {token}")
    
    game = Game.from_token(db.session, token)
    if game:
        app_logger.info(f"Game found in database: {token}")
        mngr = GameManager(config_game, jsons.loads(game.board, GameBoard))
        return mngr
    
    app_logger.info(f"Creating new game: {token}")   
    # If no game found, create a new one with default map 
    default_map = map_repository.get_map('test')
    if not default_map:
        default_map = map_repository.get_map('scorpion')  
    board = GameBoard.create(default_map)
    mngr = GameManager(config_game, board)
    
    # Log game creation
    if ENHANCED_LOGGING:
        game_event_logger.log_game_created(token, len(board.turn_order))
    
    return mngr

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

#
# Websocket (Enhanced)
#

ws_games = {}

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

# @jsonrpc.method('game_board')
# @log_rpc_performance
# def game_board_rpc(token: str) -> dict:
#     '''rpc return game board'''
#     app_logger.debug(f'Game board requested: {token}')
#     try:
#         mngr = game_load(token)
#         return jsons.dump(mngr.board)
#     except Exception as ex:
#         return handle_rpc_error('game_board', token, ex)

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
    """Attack with enhanced validation and error handling"""
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
        
        # Get unit info before attack
        attacker = mngr.unit_at(x, y)
        defender = mngr.unit_at(x2, y2)
        
        # Validate attacker exists
        if not attacker:
            raise ValidationError(
                f"No attacking unit found at position ({x}, {y})",
                details={"attacker_pos": {"x": x, "y": y}}
            )
        
        # Validate defender exists
        if not defender:
            raise ValidationError(
                f"No target unit found at position ({x2}, {y2})",
                details={"target_pos": {"x": x2, "y": y2}}
            )
        
        # Get unit info for logging
        attacker_info = f"{attacker.army.name}:{attacker.type.name}"
        defender_info = f"{defender.army.name}:{defender.type.name}"
        defender_hp_before = defender.status.hp
        
        # Execute attack
        mngr.unit_attack(x, y, x2, y2)
        
        # Calculate damage dealt
        defender_after = mngr.unit_at(x2, y2)
        damage_dealt = defender_hp_before - (defender_after.status.hp if defender_after else 0)
        
        # Enhanced logging
        if ENHANCED_LOGGING:
            game_event_logger.log_unit_attack(
                token, attacker.army.name, attacker.type.name, (x, y),
                defender.army.name, defender.type.name, (x2, y2), damage_dealt
            )
        
        app_logger.info(f'Unit attack: {token} - {attacker_info}@({x},{y}) attacked {defender_info}@({x2},{y2}) damage={damage_dealt}')
        
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x2, y2))
        
    except ValidationError as e:
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

@jsonrpc.method('unit_attack_enhanced')
@log_rpc_performance
def unit_attack_enhanced_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    """Enhanced unit attack with full combat system"""
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
        
        # Get unit info for logging
        attacker = mngr.unit_at(x, y)
        defender = mngr.unit_at(x2, y2)
        
        if not attacker:
            return {
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": f"No attacking unit at ({x}, {y})"
            }
        
        if not defender:
            return {
                "success": False,
                "error_code": "VALIDATION_ERROR", 
                "message": f"No target unit at ({x2}, {y2})"
            }
        
        # Store combat info for logging
        attacker_info = f"{attacker.army.name}:{attacker.type.name}"
        defender_info = f"{defender.army.name}:{defender.type.name}"
        
        # Execute enhanced combat
        combat_result = mngr.unit_attack_enhanced(x, y, x2, y2)
        
        # Enhanced logging
        if ENHANCED_LOGGING:
            app_logger.info(f'Enhanced combat: {token} - {attacker_info} attacked {defender_info} at ({x2},{y2})')
            app_logger.info(f'Combat result: Attacker dealt {combat_result.attacker_damage_dealt}, Defender dealt {combat_result.defender_damage_dealt}')
        
        # Save game state
        game_save(mngr, token)
        ws_board_update(token)
        
        # Return detailed combat result
        return {
            "success": True,
            "combat_result": {
                "attacker_damage_dealt": combat_result.attacker_damage_dealt,
                "defender_damage_dealt": combat_result.defender_damage_dealt,
                "attacker_hp_before": combat_result.attacker_hp_before,
                "attacker_hp_after": combat_result.attacker_hp_after,
                "defender_hp_before": combat_result.defender_hp_before,
                "defender_hp_after": combat_result.defender_hp_after,
                "defender_destroyed": combat_result.defender_destroyed,
                "attacker_destroyed": combat_result.attacker_destroyed,
                "counter_attack_occurred": combat_result.counter_attack_occurred
            },
            "attacker_position": {"x": x, "y": y},
            "defender_position": {"x": x2, "y": y2}
        }
        
    except Exception as e:
        app_logger.error(f"Enhanced attack failed for {token}: ({x},{y}) vs ({x2},{y2}): {str(e)}")
        return {
            "success": False,
            "error_code": "COMBAT_ERROR",
            "message": f"Combat operation failed: {str(e)}"
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
        mngr = game_load(token)
        
        from production_system import ProductionSystem
        
        production_system = ProductionSystem(mngr)
        
        # Convert costs to readable format
        costs = {}
        for unit_type, cost in production_system.UNIT_COSTS.items():
            costs[unit_type.name] = cost
        
        return {
            "success": True,
            "unit_costs": costs
        }
        
    except Exception as e:
        app_logger.error(f"Get unit costs failed for {token}: {str(e)}")
        return {
            "success": False,
            "error_code": "COSTS_ERROR",
            "message": f"Could not get unit costs: {str(e)}"
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
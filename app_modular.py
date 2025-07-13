#!/usr/bin/python3

'''[Modular AW-RPC game engine with organized route structure]'''

import os
os.environ['TYPEGUARD_DISABLE'] = '1'
import logging
import datetime
import secrets
from functools import wraps
import time
import json
import traceback

import subprocess
import threading

from flask import redirect, render_template, abort, request
from flask_socketio import Namespace, join_room, leave_room
import jsons

from optimized_test_map import (
    get_optimized_test_game, 
    create_quick_combat_scenario,
    verify_optimized_map
)

from manager import GameManager
from gameboard import GameBoard
from config import Config
from app_core import app, jsonrpc, db, socketio
from models import Game
from map_system import map_repository, Map, Army
from enhanced_combat_system import EnhancedCombatSystem, CombatPreview, EnhancedCombatResult
from transport_system import CompleteTransportSystem, TransportResult
from tests.integration.test_map_predeployed import get_predeployed_test_game, get_comprehensive_test_game

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

# Import shared utilities
from game_utils import games, game_load

# Core game management functions are now in game_utils.py

def create_board_from_dict(board_dict):
    """Fallback method to create GameBoard from dict if jsons.loads fails"""
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
    """CRITICAL FIX: Reconstruct Unit object from dictionary using proper Unit.create method"""
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
        else:
            unit_type = unit_type_name
            
        if isinstance(army_name, str):
            army = Army[army_name]
        else:
            army = army_name
        
        # Create the unit using proper Unit.create method
        unit = Unit.create(unit_type, army, unit_id)
        
        # Restore status if available
        if status_data:
            if 'health' in status_data:
                unit.status.health = status_data['health']
            if 'fuel' in status_data:
                unit.status.fuel = status_data['fuel']
            if 'ammo' in status_data:
                unit.status.ammo = status_data['ammo']
            if 'moved' in status_data:
                unit.status.moved = status_data['moved']
        
        app_logger.debug(f"Reconstructed unit: {unit_type.name} {army.name} with health {unit.status.health}")
        return unit
        
    except Exception as e:
        app_logger.error(f"Failed to reconstruct unit from dict: {e}")
        app_logger.debug(f"Unit dict: {unit_dict}")
        raise

config_game = Config()

# Register all modular routes
from routes.game_routes import game_bp
from routes.admin_routes import admin_bp  
from routes.test_routes import test_bp

# Register blueprints
app.register_blueprint(game_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(test_bp)

# Import all RPC methods (this registers them with jsonrpc)
from routes.rpc_methods import *
from routes.transport_rpc import *
from routes.combat_rpc import *

# Setup error handling and logging
setup_error_handlers(app)
setup_logging()

# CORS removed - handle if needed in app_core

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='AW-RPC Game Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    host = args.host
    port = args.port
    debug = args.debug
    
    app_logger.info("=== AW-RPC Application Starting ===")
    app_logger.info(f"Enhanced logging: {ENHANCED_LOGGING}")
    
    # Test map system
    if map_repository:
        try:
            available_maps = map_repository.list_maps()
            app_logger.info(f"Available maps: {available_maps}")
            
            test_map = map_repository.get_map('test')
            if test_map:
                app_logger.info(f"Test map loaded: {test_map.name} ({test_map.width}x{test_map.height})")
            else:
                app_logger.warning("Test map not found in repository")
                
        except Exception as e:
            app_logger.error(f"Error testing map system: {e}")
    else:
        app_logger.error("Map system not available - check imports")
    
    app_logger.info(f"Starting modular server on {host}:{port} (debug={debug})")
    app_logger.info("=== AW-RPC Modular Application Ready ===")
    
    socketio.run(app, host=host, port=port, debug=debug)
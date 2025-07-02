#!/usr/bin/python3

"""RPC game engine for Advance Wars clone with Flask and SocketIO."""

import os
import logging
import datetime
import secrets
from typing import Dict, Optional, Tuple, Any

from flask import redirect, render_template, abort, request
from flask_socketio import Namespace, join_room, leave_room
import jsons

from manager import GameManager
from gameboard import GameBoard
from config import Config
from app_core import app, jsonrpc, db, socketio
from models import Game
from map_system import Map, map_repository

from error_handling import (
    setup_error_handlers, setup_logging, validate_rpc_params,
    validate_token, validate_coordinates, validate_army, validate_unit_type,
    safe_rpc_call, log_game_event, AWRPCError, ValidationError, 
    GameStateError, UnitError, MovementError, CombatError, TurnError, NotFoundError
)


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='app.log', 
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

config_game = Config()
setup_error_handlers(app)
game_logger = setup_logging()


#
# Constants
#

# TODO: Implement secondary weapon damage table
SECONDARY_WEAPON_DAMAGE = {
    'INFANTRY': {'INFANTRY': 55, 'MECH': 45, 'RECON': 12},
    'MECH': {'INFANTRY': 65, 'MECH': 55, 'RECON': 18},
    'TANK': {'INFANTRY': 75, 'MECH': 70, 'RECON': 85},
    # Add more units and their secondary weapon damage
}

# TODO: COM_TOWER damage modifiers
COM_TOWER_MODIFIERS = {
    'attack_bonus': 1.1,  # 10% attack bonus per tower
    'defense_bonus': 1.1,  # 10% defense bonus per tower
}

# Weather effects (nice to have)
WEATHER_EFFECTS = {
    'CLEAR': {'movement': 1.0, 'vision': 1.0},
    'RAIN': {'movement': 0.8, 'vision': 0.7},
    'SNOW': {'movement': 0.6, 'vision': 0.5},
    'FOG': {'movement': 1.0, 'vision': 0.3},
}

#
# Helper functions
#

def setup_logging(level: int) -> None:
    """Setup logging with specified level."""
    logger.setLevel(level)
    
def game_load(token):
    '''Loads the game token specified'''
    game = Game.from_token(db.session, token)
    if game:
        mngr = GameManager(config_game, jsons.loads(game.board, GameBoard))
        return mngr
    
    # Get default map from repository
    try:
        default_map = map_repository.get_map('test')
        if not default_map:
            default_map = map_repository.get_map('scorpion')
        
        if default_map:
            board = GameBoard.create(default_map)
            mngr = GameManager(config_game, board)
            return mngr
            
    except Exception as e:
        print(f"Error loading map: {e}")
    
    # Fallback - create a simple test map
    from map_system import Map, MapType, Army, MapTile
    
    # Create a 3x3 map manually
    tiles = []
    for i in range(9):
        if i == 4:  # Center tile
            tiles.append(MapTile(MapType.CITY))
        else:
            tiles.append(MapTile(MapType.PLAIN))
    
    fallback_map = Map(
        width=3, 
        height=3, 
        tiles=tiles, 
        turn_order=[Army.RED, Army.BLUE],
        name="Fallback Map"
    )
    
    board = GameBoard.create(fallback_map)
    mngr = GameManager(config_game, board)
    return mngr


def game_save(mngr: GameManager, token: str) -> bool:
    """Save the current game state."""
    try:
        game = Game.from_token(db.session, token)
        if not game:
            game = Game(mngr.board, token)
        else:
            game.update = datetime.datetime.now()
            game.board = jsons.dumps(mngr.board)
        
        db.session.add(game)
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error saving game {token}: {e}")
        return False


def game_delete(token: str) -> bool:
    """Delete the game with specified token."""
    try:
        game = Game.from_token(db.session, token)
        if game:
            db.session.delete(game)
            db.session.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting game {token}: {e}")
        return False


def game_create(token: str) -> bool:
    """Create a new game with specified token."""
    try:
        mngr = game_load(token)
        game = Game(mngr.board, token)
        db.session.add(game)
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error creating game {token}: {e}")
        return False


def calculate_damage_with_towers(attacker_damage: int, defender_damage: int, 
                               attacker_towers: int, defender_towers: int) -> Tuple[int, int]:
    """Calculate damage including COM_TOWER bonuses."""
    # Apply COM_TOWER attack bonuses
    attacker_modifier = COM_TOWER_MODIFIERS['attack_bonus'] ** attacker_towers
    defender_modifier = COM_TOWER_MODIFIERS['attack_bonus'] ** defender_towers
    
    # Apply COM_TOWER defense bonuses
    attacker_defense = COM_TOWER_MODIFIERS['defense_bonus'] ** attacker_towers
    defender_defense = COM_TOWER_MODIFIERS['defense_bonus'] ** defender_towers
    
    # Calculate final damage
    final_attacker_damage = int(attacker_damage * attacker_modifier / defender_defense)
    final_defender_damage = int(defender_damage * defender_modifier / attacker_defense)
    
    return final_attacker_damage, final_defender_damage


def get_secondary_weapon_damage(attacker_type: str, defender_type: str) -> int:
    """Get secondary weapon damage for unit types."""
    return SECONDARY_WEAPON_DAMAGE.get(attacker_type, {}).get(defender_type, 0)


def handle_rpc_error(func_name: str, token: str, error: Exception) -> None:
    """Centralized error handling for RPC methods."""
    logger.error(f"Error in {func_name} for token {token}: {error}")
    

#
# REST Routes
#

@app.route('/')
def index():
    """Redirect to new game with random token."""
    return redirect('/game/' + secrets.token_urlsafe(4))


@app.route('/game/<token>')
def game(token: str):
    """Render game page with specified token."""
    return render_template('render.html', token=token)


@app.route('/api/browse-api')
def api_browse():
    """API documentation endpoint."""
    # TODO: Add proper API documentation
    return render_template('api_docs.html')


#
# WebSocket handling
#

ws_games: Dict[str, str] = {}


def ws_board_update(token: str) -> None:
    """Send board update to all clients in game room."""
    socketio.emit('update', 'room', room=token)


def ws_msg(token: str, msg: str) -> None:
    """Send message to all clients in game room."""
    socketio.emit('message', msg, room=token)


class SocketIoNamespace(Namespace):
    """WebSocket namespace for game communication."""
    
    def on_error(self, e):
        logger.error(f"SocketIO error: {e}")

    def on_connect(self):
        logger.info(f'SocketIO connect - sid: {request.sid}')

    def on_game(self, token):
        logger.info(f'SocketIO game join - sid: {request.sid}, token: {token}')
        join_room(token)
        ws_games[request.sid] = token

    def on_disconnect(self):
        logger.info(f'SocketIO disconnect - sid: {request.sid}')
        if request.sid in ws_games:
            leave_room(ws_games[request.sid])
            del ws_games[request.sid]


socketio.on_namespace(SocketIoNamespace('/'))

#
# JSON-RPC Methods
#

@jsonrpc.method('troop_info')
def troop_info() -> dict:
    """Return unit configuration information."""
    logger.info('troop_info called')
    return jsons.dump(config_game.units)


@jsonrpc.method('message')
def message(token: str, msg: str) -> str:
    """Send chat message to game room."""
    logger.info(f'message - token: {token}')
    ws_msg(token, msg)
    return 'ok'


@jsonrpc.method('game_delete')
def game_delete_rpc(token: str) -> str:
    """Delete specified game."""
    logger.info(f'game_delete - token: {token}')
    success = game_delete(token)
    return 'ok' if success else 'error'


@jsonrpc.method('game_create')
def game_create_rpc(token: str) -> str:
    """Create new game with specified token."""
    logger.info(f'game_create - token: {token}')
    success = game_create(token)
    return 'ok' if success else 'error'


@jsonrpc.method('game_board')
def game_board_rpc(token: str) -> dict:
    """Return current game board state."""
    logger.info(f'game_board - token: {token}')
    try:
        mngr = game_load(token)
        return jsons.dump(mngr.board)
    except Exception as e:
        handle_rpc_error('game_board', token, e)
        return abort(400, str(e))


@jsonrpc.method('army_end_turn')
def army_end_turn_rpc(token: str) -> str:
    """End current army's turn."""
    logger.info(f'army_end_turn - token: {token}')
    try:
        mngr = game_load(token)
        mngr.army_end_turn()
        game_save(mngr, token)
        ws_board_update(token)
        turn = mngr.check_turn()
        logger.info(f'Turn ended - new turn: {turn.name}')
        return jsons.dump(turn)
    except Exception as e:
        handle_rpc_error('army_end_turn', token, e)
        return abort(400, str(e))


@jsonrpc.method('end_game')
def end_game_rpc(token: str) -> str:
    """End the game and declare winner."""
    logger.info(f'end_game - token: {token}')
    try:
        mngr = game_load(token)
        mngr.end_game()
        game_save(mngr, token)
        ws_board_update(token)
        turn = mngr.check_turn()
        result = f'{turn.name} is the winner!'
        logger.info(result)
        return jsons.dump(result)
    except Exception as e:
        handle_rpc_error('end_game', token, e)
        return abort(400, str(e))


@jsonrpc.method('tile')
def tile_rpc(token: str, x: int, y: int) -> dict:
    """Return tile at specified coordinates."""
    logger.info(f'tile - token: {token}, coords: ({x},{y})')
    try:
        mngr = game_load(token)
        return jsons.dump(mngr.tile_get(x, y))
    except Exception as e:
        handle_rpc_error('tile', token, e)
        return abort(400, str(e))


@jsonrpc.method('capture_tile')
def capture_tile_rpc(token: str, x: int, y: int) -> dict:
    '''rpc capture tile with enhanced validation'''
    logger.info(f'capture_tile token={token}, x={x}, y={y}')
    
    try:
        # Validate inputs
        validate_token(token)
        
        mngr = game_load(token)
        
        # Validate coordinates
        validate_coordinates(x, y, mngr.board.width, mngr.board.height)
        
        # Perform capture
        tile = mngr.capture_tile(x, y)
        game_save(mngr, token)
        ws_board_update(token)
        
        # Log successful capture
        log_game_event(game_logger, "PROPERTY_CAPTURED", {
            "token": token,
            "position": {"x": x, "y": y},
            "property_type": tile.mapTile.type.name,
            "army": tile.mapTile.army.name if tile.mapTile.army else "Neutral",
            "capture_hp_remaining": tile.capture_hp
        })
        
        return jsons.dump(mngr.tile_get(x, y))
        
    except (ValidationError, GameStateError, UnitError, TurnError, AWRPCError) as e:
        logger.error(f"Capture error: {str(e)}")
        return {
            "error": True,
            "error_code": getattr(e, 'error_code', 'CAPTURE_ERROR'),
            "message": str(e),
            "details": getattr(e, 'details', {})
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in capture_tile: {str(e)}")
        return {
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": f"Failed to capture property: {str(e)}",
            "details": {}
        }
        

@jsonrpc.method('unit_wait')
def unit_wait_rpc(token: str, x: int, y: int) -> dict:
    """Set unit to wait state."""
    logger.info(f'unit_wait - token: {token}, coords: ({x},{y})')
    try:
        mngr = game_load(token)
        mngr.unit_wait(x, y)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.unit_at(x, y))
    except Exception as e:
        handle_rpc_error('unit_wait', token, e)
        return abort(400, str(e))


@jsonrpc.method('unit_select')
def unit_select_rpc(token: str, x: int, y: int) -> dict:
    """Select unit at specified coordinates."""
    logger.info(f'unit_select - token: {token}, coords: ({x},{y})')
    try:
        mngr = game_load(token)
        mngr.unit_select(x, y)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.unit_at(x, y))
    except Exception as e:
        handle_rpc_error('unit_select', token, e)
        return abort(400, str(e))

@jsonrpc.method('unit_move')
def unit_move_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    '''rpc move unit from / to coordinates with enhanced validation'''
    logger.info(f'unit_move token={token}, x={x}, y={y}, x2={x2}, y2={y2}')
    
    try:
        # Validate inputs
        validate_token(token)
        
        mngr = game_load(token)
        
        # Validate all coordinates
        validate_coordinates(x, y, mngr.board.width, mngr.board.height)
        validate_coordinates(x2, y2, mngr.board.width, mngr.board.height)
        
        # Perform the move
        mngr.unit_move(x, y, x2, y2)
        game_save(mngr, token)
        ws_board_update(token)
        
        # Log successful move
        log_game_event(game_logger, "UNIT_MOVED", {
            "token": token,
            "from": {"x": x, "y": y},
            "to": {"x": x2, "y": y2}
        })
        
        return jsons.dump(mngr.tile_get(x2, y2))
        
    except (ValidationError, GameStateError, UnitError, MovementError, TurnError, AWRPCError) as e:
        logger.error(f"Movement error: {str(e)}")
        return {
            "error": True,
            "error_code": getattr(e, 'error_code', 'MOVEMENT_ERROR'),
            "message": str(e),
            "details": getattr(e, 'details', {})
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in unit_move: {str(e)}")
        return {
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": f"Failed to move unit: {str(e)}",
            "details": {}
        }
    
@jsonrpc.method('unit_move2')
def unit_move2_rpc(token: str, unit_id: str, x: int, y: int) -> dict:
    """Move unit by ID to specified coordinates."""
    logger.info(f'unit_move2 - token: {token}, unit_id: {unit_id}, to: ({x},{y})')
    try:
        mngr = game_load(token)
        mngr.unit_move2(unit_id, x, y)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x, y))
    except Exception as e:
        handle_rpc_error('unit_move2', token, e)
        return abort(400, str(e))

@jsonrpc.method('unit_create')
def unit_create_rpc(token: str, army: str, unit_type: str, x: int, y: int) -> dict:
    '''rpc create a unit at the coordinates given'''
    logger.info(f'unit_create token={token}, army={army}, unit_type={unit_type}, x={x}, y={y}')
    
    try:
        # Validate inputs
        validate_token(token)
        validate_army(army)
        validate_unit_type(unit_type)
        
        mngr = game_load(token)
        
        # Validate coordinates
        validate_coordinates(x, y, mngr.board.width, mngr.board.height)
        
        # Create the unit
        mngr.unit_create(army, unit_type, x, y)
        game_save(mngr, token)
        ws_board_update(token)
        
        return jsons.dump(mngr.tile_get(x, y))
        
    except (ValidationError, GameStateError, UnitError, MovementError, AWRPCError) as e:
        # Return error as JSON response
        logger.error(f"Validation error in unit_create: {str(e)}")
        return {
            "error": True,
            "error_code": getattr(e, 'error_code', 'VALIDATION_ERROR'),
            "message": str(e),
            "details": getattr(e, 'details', {})
        }
        
    except Exception as e:
        # Convert other exceptions
        logger.error(f"Unexpected error in unit_create: {str(e)}")
        return {
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": f"Failed to create unit: {str(e)}",
            "details": {}
        }

@jsonrpc.method('damage_estimate')
def damage_estimate_rpc(token: str, x: int, y: int, x2: int, y2: int) -> list:
    """Estimate damage for attacker and defender."""
    logger.info(f'damage_estimate - token: {token}, attacker: ({x},{y}), defender: ({x2},{y2})')
    try:
        mngr = game_load(token)
        damage_tuple = mngr.damage_estimate(x, y, x2, y2)
        
        # TODO: Apply COM_TOWER modifiers
        # attacker_towers = mngr.count_com_towers(mngr.unit_at(x, y).army)
        # defender_towers = mngr.count_com_towers(mngr.unit_at(x2, y2).army)
        # damage_tuple = calculate_damage_with_towers(*damage_tuple, attacker_towers, defender_towers)
        
        return jsons.dump(damage_tuple)
    except Exception as e:
        handle_rpc_error('damage_estimate', token, e)
        return abort(400, str(e))


@jsonrpc.method('unit_attack')
def unit_attack_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    """Attack unit at target coordinates."""
    logger.info(f'unit_attack - token: {token}, attacker: ({x},{y}), target: ({x2},{y2})')
    try:
        mngr = game_load(token)
        mngr.unit_attack(x, y, x2, y2)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x2, y2))
    except Exception as e:
        handle_rpc_error('unit_attack', token, e)
        return abort(400, str(e))


@jsonrpc.method('unit_delete')
def unit_delete_rpc(token: str, x: int, y: int) -> dict:
    """Delete unit at specified coordinates."""
    logger.info(f'unit_delete - token: {token}, coords: ({x},{y})')
    try:
        mngr = game_load(token)
        mngr.unit_delete(x, y)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x, y))
    except Exception as e:
        handle_rpc_error('unit_delete', token, e)
        return abort(400, str(e))


@jsonrpc.method('check_turn')
def check_turn_rpc(token: str) -> str:
    """Check current army turn."""
    logger.info(f'check_turn - token: {token}')
    try:
        mngr = game_load(token)
        turn = mngr.check_turn()
        return jsons.dump(turn)
    except Exception as e:
        handle_rpc_error('check_turn', token, e)
        return abort(400, str(e))


@jsonrpc.method('unit_join')
def unit_join_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    """Join unit from source to destination coordinates."""
    logger.info(f'unit_join - token: {token}, from: ({x},{y}), to: ({x2},{y2})')
    try:
        mngr = game_load(token)
        mngr.unit_join(x, y, x2, y2)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x2, y2))
    except Exception as e:
        handle_rpc_error('unit_join', token, e)
        return abort(400, str(e))


@jsonrpc.method('unit_load')
def unit_load_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    """Load unit into transport."""
    logger.info(f'unit_load - token: {token}, unit: ({x},{y}), transport: ({x2},{y2})')
    try:
        mngr = game_load(token)
        mngr.unit_load(x, y, x2, y2)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x2, y2))
    except Exception as e:
        handle_rpc_error('unit_load', token, e)
        return abort(400, str(e))


@jsonrpc.method('unit_unload')
def unit_unload_rpc(token: str, x: int, y: int, x2: int, y2: int, index: int) -> dict:
    """Unload unit from transport."""
    logger.info(f'unit_unload - token: {token}, transport: ({x},{y}), destination: ({x2},{y2}), index: {index}')
    try:
        mngr = game_load(token)
        mngr.unit_unload(x, y, x2, y2, index)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x2, y2))
    except Exception as e:
        handle_rpc_error('unit_unload', token, e)
        return abort(400, str(e))


@jsonrpc.method('launch_missile')
def launch_missile_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    """Launch missile from source to target coordinates."""
    logger.info(f'launch_missile - token: {token}, from: ({x},{y}), to: ({x2},{y2})')
    try:
        mngr = game_load(token)
        mngr.launch_missile(x, y, x2, y2)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x, y))
    except Exception as e:
        handle_rpc_error('launch_missile', token, e)
        return abort(400, str(e))


@jsonrpc.method('unit_resupply')
def unit_resupply_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    """Resupply unit at target coordinates."""
    logger.info(f'unit_resupply - token: {token}, supplier: ({x},{y}), target: ({x2},{y2})')
    try:
        mngr = game_load(token)
        mngr.unit_resupply(x, y, x2, y2)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x2, y2))
    except Exception as e:
        handle_rpc_error('unit_resupply', token, e)
        return abort(400, str(e))


# TODO: Implement CO powers
@jsonrpc.method('activate_co_power')
def activate_co_power_rpc(token: str, army: str, power_type: str) -> str:
    """Activate CO power for specified army."""
    logger.info(f'activate_co_power - token: {token}, army: {army}, power: {power_type}')
    try:
        mngr = game_load(token)
        # TODO: Implement CO power logic
        # mngr.activate_co_power(army, power_type)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump('CO power activated')
    except Exception as e:
        handle_rpc_error('activate_co_power', token, e)
        return abort(400, str(e))


# TODO: Implement weather system
@jsonrpc.method('set_weather')
def set_weather_rpc(token: str, weather_type: str) -> str:
    """Set weather conditions for the game."""
    logger.info(f'set_weather - token: {token}, weather: {weather_type}')
    try:
        mngr = game_load(token)
        # TODO: Implement weather system
        # mngr.set_weather(weather_type)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(f'Weather set to {weather_type}')
    except Exception as e:
        handle_rpc_error('set_weather', token, e)
        return abort(400, str(e))


if __name__ == '__main__':
    setup_logging(logging.DEBUG)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        db.session.commit()
    
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    logger.info(f'Starting server on port: {port}')
    
    # Run the application
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
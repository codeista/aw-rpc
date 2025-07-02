#!/usr/bin/python3

'''[This is a RPC game engine for Advance wars - WORKING VERSION]'''

import os
import logging
import datetime
import secrets

from flask import redirect, render_template, abort, request
from flask_socketio import Namespace, join_room, leave_room
import jsons

from manager import GameManager
from gameboard import GameBoard
from config import Config
from app_core import app, jsonrpc, db, socketio
from models import Game

# Simple map import - just use what works
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

except ImportError:
    # If map_system doesn't exist, create minimal compatibility
    print("Warning: Using minimal map system")
    
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

logger = logging.getLogger(__name__)
logging.basicConfig(filename='app.log', level=logging.INFO)

config_game = Config()

#
# Helper functions
#

def setup_logging(level):
    '''Setup logging.'''
    logger.setLevel(level)

def game_load(token):
    '''Loads the game token specified'''
    game = Game.from_token(db.session, token)
    if game:
        mngr = GameManager(config_game, jsons.loads(game.board, GameBoard))
        return mngr
    board = GameBoard.create(default_map)  # Use our default_map
    mngr = GameManager(config_game, board)
    return mngr

def game_save(mngr, token):
    '''Saves the current game state'''
    game = Game.from_token(db.session, token)
    if not game:
        game = Game(mngr.board, token)
    else:
        game.update = datetime.datetime.now()
        game.board = jsons.dumps(mngr.board)
    db.session.add(game)
    db.session.commit()

def game_delete(token):
    '''Deletes the game token specified.'''
    game = Game.from_token(db.session, token)
    if game:
        db.session.delete(game)
        db.session.commit()

def game_create(token):
    '''Creates a new game with token specified'''
    mngr = game_load(token)
    game = Game(mngr.board, token)
    db.session.add(game)
    db.session.commit()

#
# REST
#

@app.route('/')
def index():
    return redirect('/game/' + secrets.token_urlsafe(4))

@app.route('/game/<token>')
def game(token: str):
    return render_template('render.html', token=token)

#
# Websocket
#

ws_games = {}

def ws_board_update(token):
    socketio.emit('update', 'room', room=token)

def ws_msg(token, msg):
    socketio.emit('message', msg, room=token)

class SocketIoNamespace(Namespace):
    def on_error(self, e):
        logger.error(e)

    def on_connect(self):
        logger.info('socketio - connect sid: %s' % request.sid)

    def on_game(self, token):
        logger.info('socketio - game sid: %s, token: %s' % (request.sid, token))
        join_room(token)
        ws_games[request.sid] = token

    def on_disconnect(self):
        logger.info('socketio - disconnect sid: %s' % request.sid)
        if request.sid in ws_games:
            leave_room(ws_games[request.sid])
            del ws_games[request.sid]

socketio.on_namespace(SocketIoNamespace('/'))

#
# JSONRPC Methods
#

@jsonrpc.method('troop_info')
def troop_info() -> dict:
    '''Returns the unit config info'''
    logger.info('troop_info')
    return jsons.dump(config_game.units)

@jsonrpc.method('message')
def message(token: str, msg: str) -> str:
    '''rpc chat'''
    logger.info('msg')
    ws_msg(token, msg)
    return 'ok'

@jsonrpc.method('game_delete')
def game_delete_rpc(token: str) -> str:
    '''rpc delete game'''
    logger.info(f'game_delete token={token}')
    game_delete(token)
    return 'ok'

@jsonrpc.method('game_create')
def game_create_rpc(token: str) -> str:
    '''rpc-create game'''
    logger.info(f'game_create token={token}')
    game_create(token)
    return 'ok'

@jsonrpc.method('game_board')
def game_board_rpc(token: str) -> dict:
    '''rpc return game board'''
    logger.info(f'game_board token={token}')
    mngr = game_load(token)
    return jsons.dump(mngr.board)

@jsonrpc.method('army_end_turn')
def army_end_turn_rpc(token: str) -> str:
    '''rpc end current turn'''
    mngr = game_load(token)
    try:
        mngr.army_end_turn()
        game_save(mngr, token)
        ws_board_update(token)
        turn = mngr.check_turn()
        logger.info(f'army_end_turn={turn.name}')
        return jsons.dump(turn)
    except Exception as ex:
        logger.error(f'army_end_turn error: {ex}')
        raise Exception( str(ex))

@jsonrpc.method('tile')
def tile_rpc(token: str, x: int, y: int) -> dict:
    '''rpc return tile at coordinates'''
    logger.info(f'tile token={token}, x={x}, y={y}')
    mngr = game_load(token)
    try:
        if x < 0 or y < 0 or x >= mngr.board.width or y >= mngr.board.height:
            raise Exception( f'coordinate out of range: x={x}, y={y}')
        return jsons.dump(mngr.tile_get(x, y))
    except Exception as ex:
        logger.error(f'tile error: {ex}')
        raise Exception( str(ex))

@jsonrpc.method('unit_create')
def unit_create_rpc(token: str, army: str, unit_type: str, x: int, y: int) -> dict:
    '''rpc create a unit at the coordinates given'''
    logger.info(f'unit_create token={token}, army={army}, unit_type={unit_type}, x={x}, y={y}')
    mngr = game_load(token)
    try:
        # Basic validation
        army = army.upper()
        unit_type = unit_type.upper()
        
        valid_armies = ['RED', 'BLUE', 'GREEN', 'YELLOW', 'GREY']
        if army not in valid_armies:
            raise Exception( f'invalid army: {army}')
        
        # Validate unit_type parameter
        unit_type = unit_type.upper()
        try:
            from unit import UnitType
            UnitType[unit_type]
        except KeyError:
            valid_types = ', '.join([ut.name for ut in UnitType])
            raise Exception(f'invalid unit_type parameter: {unit_type}. Valid types: {valid_types}')
        
        # Check coordinates
        if x < 0 or y < 0 or x >= mngr.board.width or y >= mngr.board.height:
            raise Exception( f'coordinates out of range')
        
        mngr.unit_create(army, unit_type, x, y)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x, y))
    except Exception as ex:
        logger.error(f'unit_create error: {ex}')
        raise Exception( str(ex))

@jsonrpc.method('unit_move')
def unit_move_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    '''rpc move unit'''
    logger.info(f'unit_move token={token}, x={x}, y={y}, x2={x2}, y2={y2}')
    mngr = game_load(token)
    try:
        mngr.unit_move(x, y, x2, y2)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x2, y2))
    except Exception as ex:
        logger.error(f'unit_move error: {ex}')
        raise Exception( str(ex))

@jsonrpc.method('army_end_turn')
def army_end_turn_rpc(token: str) -> str:
    '''rpc end turn'''
    mngr = game_load(token)
    try:
        mngr.army_end_turn()
        game_save(mngr, token)
        ws_board_update(token)
        turn = mngr.check_turn()
        return jsons.dump(turn)
    except Exception as ex:
        raise Exception( str(ex))

@jsonrpc.method('check_turn')
def check_turn_rpc(token: str) -> str:
    '''rpc check current turn'''
    mngr = game_load(token)
    try:
        turn = mngr.check_turn()
        return jsons.dump(turn)
    except Exception as ex:
        raise Exception( str(ex))

# Add other essential RPC methods as needed...

if __name__ == '__main__':
    setup_logging(logging.DEBUG)
    # create tables
    with app.app_context():
        db.create_all()
        db.session.commit()
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    logging.info(f'binding to port: {port}')
    socketio.run(app, host='0.0.0.0', port=port, debug=True)

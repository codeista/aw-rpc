#!/usr/bin/python3

'''[This is a RPC game engine for Advance wars]'''

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
from mapping import Map, MAP1

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
    board = GameBoard.create(Map.parse(MAP1))
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
# JSONRPC
#


@jsonrpc.method('troop_info')
def troop_info() -> dict:
    '''Returns the unit config info
    :return: [Unit configs]'''
    logger.info('troop_info')
    return jsons.dump(config_game.units)


@jsonrpc.method('message')
def message(token: str, msg: str) -> str:
    '''rpc chat.
    :return: [ok]
    '''
    logger.info('msg')
    ws_msg(token, msg)
    return 'ok'


@jsonrpc.method('game_delete')
def game_delete_rpc(token: str) -> str:
    '''rpc delete game.
    :return: [ok]
    '''
    logger.info(f'game_delete token={token}')
    game_delete(token)
    return 'ok'


@jsonrpc.method('game_create')
def game_create_rpc(token: str) -> str:
    '''rpc-create game.
    :return: [ok]
    '''
    logger.info(f'game_create token={token}')
    game_create(token)
    return 'ok'


@jsonrpc.method('game_board')
def game_board_rpc(token: str) -> dict:
    '''rpc return game board.
    :return: [gameboard]
    '''
    logger.info(f'game_board token={token}')
    mngr = game_load(token)
    return jsons.dump(mngr.board)


@jsonrpc.method('army_end_turn')
def army_end_turn_rpc(token: str) -> str:
    '''rpc end current turn.
    :return: [ok]
    '''
    mngr = game_load(token)
    try:
        mngr.army_end_turn()
        game_save(mngr, token)
        ws_board_update(token)
        turn = mngr.check_turn()
        logger.info(f'army_end_turn={turn.name}')
        return jsons.dump(turn)
    except Exception as ex:
        return abort(400, ex)
        


@jsonrpc.method('end_game')
def end_game_rpc(token: str) -> str:
    '''rpc end game.
    :return: [ok]
    '''
    logger.info(f'end game token={token}')
    mngr = game_load(token)
    try:
        mngr.end_game()
        game_save(mngr, token)
        ws_board_update(token)
        turn = mngr.check_turn()
        text = turn.name + ' is the winner!'
        logger.info(f'{turn.name} is the winner')
        return jsons.dump(text)
    except Exception as ex:
        return abort(400, ex)


# return the game tile for the coord(x, y)
@jsonrpc.method('tile')
def tile_rpc(token: str, x: int, y: int) -> dict:
    '''rpc return tile at coordinates
    :return: [tile at coordinates given]
    '''
    logger.info(f'tile token={token}, x={x}, y={y}')
    mngr = game_load(token)
    try:
        return jsons.dump(mngr.tile_get(x, y))
    except Exception as ex:
        return abort(400, ex)


@jsonrpc.method('capture_tile')
def capture_tile_rpc(token: str, x: int, y: int) -> dict:
    '''rpc capture tile
    :return: [tile at coordinates given]
    '''
    logger.info(f'capture_city token={token}, x={x}, y={y}')
    mngr = game_load(token)
    try:
        mngr.capture_tile(x, y)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x, y))
    except Exception as ex:
        return abort(400, ex)


@jsonrpc.method('unit_wait')
def unit_wait_rpc(token: str, x: int, y: int) -> dict:
    '''rpc unit wait
    :return: [tile at coordinates given]
    '''
    logger.info(f'unit wait token={token}, x={x}, y={y}')
    mngr = game_load(token)
    try:
        mngr.unit_wait(x, y)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.unit_at(x, y))
    except Exception as ex:
        return abort(400, ex)


@jsonrpc.method('unit_select')
def unit_select_rpc(token: str, x: int, y: int) -> dict:
    '''rpc select unit at coordinate.
    :return: [gameboard]
    '''
    logger.info(f'unit_select token={token}, x={x}, y={y}')
    mngr = game_load(token)
    try:
        unit = mngr.unit_select(x, y)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.unit_at(x, y))
    except Exception as ex:
        return abort(400, ex)


@jsonrpc.method('unit_move')
def unit_move_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    '''rpc move unit from / to coordinates
    :return: [tile at destination coordinates]
    '''
    logger.info(f'unit_move token={token}, x={x}, y={y}, x2={x2}, y2={y2}')
    mngr = game_load(token)
    try:
        mngr.unit_move(x, y, x2, y2)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x2, y2))
    except Exception as ex:
        return abort(400, ex)


@jsonrpc.method('unit_move2')
def unit_move2_rpc(token: str, id: str, x: int, y: int) -> dict:
    '''rpc move unit for given ID to the coordinates.
    :return: [tile at coordinates]
    '''
    logger.info(f'unit_move2 token={token}, id={id}, x={x}, y={y}')
    mngr = game_load(token)
    try:
        mngr.unit_move2(id, x, y)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x, y))
    except Exception as ex:
        return abort(400, ex)


@jsonrpc.method('unit_create')
def unit_create_rpc(token: str, army: str, unit_type: str, x: int, y: int) -> dict:
    '''rpc create a unit at the coordinates given
    :return: [tile at coordinates]
    '''
    logger.info(f'unit_create token={token}, army={army}, x={x}, y={y}')
    mngr = game_load(token)
    try:
        mngr.unit_create(army, unit_type, x, y)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x, y))
    except Exception as ex:
        return abort(400, ex)


# need to return both attacker and defender
@jsonrpc.method('damage_estimate')
def damage_estimate_rpc(token: str, x: int, y: int, x2: int, y2: int) -> list:
    '''rpc estimates the damage for attacker and defender.
    :return: [tuple (attacker hp, defender hp) ]
    '''
    logger.info(f'damage_estimate token={token}, x={x}, y={y}, x2={x2}, y2={y2}')
    mngr = game_load(token)
    try:
        tup = mngr.damage_estimate(x, y, x2, y2)
        return jsons.dump(tup)
    except Exception as ex:
        return abort(400, ex)


# need to return both attacker and defender
@jsonrpc.method('unit_attack')
def unit_attack_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    '''rpc attacks the unit from x,y to x2,y2
    :return: [tile at given coordinate]
    '''
    logger.info(f'unit_attack token={token}, x={x}, y={y}, x2={x2}, y2={y2}')
    mngr = game_load(token)
    try:
        mngr.unit_attack(x, y, x2, y2)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x2, y2))
    except Exception as ex:
        return abort(400, ex)


@jsonrpc.method('unit_delete')
def unit_delete_rpc(token: str, x: int, y: int) -> dict:
    '''rpc deletes unit at given coordinate.
    :return: [tile at coordinates]
    '''
    logger.info(f'unit_delete token={token}, x={x}, y={y}')
    mngr = game_load(token)
    try:
        mngr.unit_delete(x, y)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x, y))
    except Exception as ex:
        return abort(400, ex)


@jsonrpc.method('check_turn')
def check_turn_rpc(token: str) -> str:
    '''rpc checks the current army turn.
    :return: [The current turn]
    '''
    logger.info(f'check turn token={token}')
    mngr = game_load(token)
    try:
        turn = mngr.check_turn()
        return jsons.dump(turn)
    except Exception as ex:
        return abort(400, ex)


@jsonrpc.method('unit_join')
def unit_join_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    '''rpc joins the unit from x,y to x2,y2.
    :return: [Tile at x2,y2]
    '''
    logger.info(f'unit_join token={token}, x={x}, y={y}, x2={x2}, y2={y2}')
    mngr = game_load(token)
    try:
        mngr.unit_join(x, y, x2, y2)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x2, y2))
    except Exception as ex:
        return abort(400, ex)


@jsonrpc.method('unit_load')
def unit_load_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    '''rpc loads the unit from x,y to x2,y2.
    :return: [Tile at x2,y2]
    '''
    logger.info(f'unit_load token={token}, x={x}, y={y}, x2={x2}, y2={y2}')
    mngr = game_load(token)
    try:
        mngr.unit_load(x, y, x2, y2)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x2, y2))
    except Exception as ex:
        return abort(400, ex)


@jsonrpc.method('unit_unload')
def unit_unload_rpc(token: str, x: int, y: int, x2: int, y2: int, index: int) -> dict:
    '''rpc umloads the unit from x,y to x2,y2.
    :return: [Tile at x2,y2]
    '''
    logger.info(
        f'unit_unload token={token}, x={x}, y={y}, x2={x2}, y2={y2}, index={index}')
    mngr = game_load(token)
    try:
        mngr.unit_unload(x, y, x2, y2, index)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x2, y2))
    except Exception as ex:
        return abort(400, ex)


@jsonrpc.method('launch_missile')
def launch_missile_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    '''launches missile from x,y to x2,y2.
    :return: [tile at destination coordinate]
    '''
    logger.info(
        f'launch missile token={token}, x={x}, y={y}, x2={x2}, y2={y2}')
    mngr = game_load(token)
    try:
        mngr.launch_missile(x, y, x2, y2)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x, y))
    except Exception as ex:
        return abort(400, ex)


@jsonrpc.method('unit_resupply')
def unit_resupply_rpc(token: str, x: int, y: int, x2: int, y2: int) -> dict:
    '''rpc resupply unit from x,y to x2,y2.
    :return: [tile at destination coordinates]
    '''
    logger.info(f'resupply token={token}, x={x}, y={y}, x2={x2}, y2={y2}')
    mngr = game_load(token)
    try:
        mngr.unit_resupply(x, y, x2, y2)
        game_save(mngr, token)
        ws_board_update(token)
        return jsons.dump(mngr.tile_get(x2, y2))
    except Exception as ex:
        return abort(400, ex)


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

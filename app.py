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
from models import Game, Player
from mapping import Map, MAP1
from army import Army
from cos import Co

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
    game = Game.from_token(db.session, token)
    if game:
        return game.token
    mngr = game_load(token)
    game = Game(mngr.board, token)
    db.session.add(game)
    db.session.commit()
    logger.info(f'game_created token={token}')
    return game.token


def player_create(colour, co):
    '''Creates a player for the game'''
    colour = colour.upper()
    co = co.upper()
    try:
        Army[colour]
    except KeyError:
        raise Exception('Invalid colour parameter RED/BLUE')
    try:
        Co[co]
    except KeyError:
        raise Exception('Invalid co parameter MAX/ANDY/JESS/GRIMM/ADDER')
    player = Player(colour, co)
    db.session.add(player)
    db.session.commit()
    return player

def player_load(id):
    '''Loads a player from the player id'''
    try:
        player = Player.from_id(db.session, id)
        if player:
            return player
        else:
            abort(404, description='Player doesnt exist')
    except Exception as ex:
        return abort(404, ex)

def p_1(token):
    game = Game.from_token(db.session, token)
    if game and game.player_one:
        player = game.players[0]
        return f'{player.colour} {player.co}'
    else:
        return 'Join Game'

def p_2(token):
    game = Game.from_token(db.session, token)
    if game and game.player_two:
        player = game.players[1]
        return f'{player.colour} {player.co}'
    else:
        return 'Join game'

#
# REST
#


@app.route('/')
def index():
    return redirect('/game/' + secrets.token_urlsafe(4))


@app.route('/game/<token>')
def game(token: str):
    return render_template('render.html', token=token, p1=p_1(token), p2=p_2(token))

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
        logger.debug('socketio - connect sid: %s' % request.sid)

    def on_game(self, token):
        logger.info('socketio - game sid: %s, token: %s' % (request.sid, token))
        join_room(token)
        ws_games[request.sid] = token

    def on_disconnect(self):
        logger.debug('socketio - disconnect sid: %s' % request.sid)
        if request.sid in ws_games:
            leave_room(ws_games[request.sid])
            del ws_games[request.sid]


socketio.on_namespace(SocketIoNamespace('/'))

#
# JSONRPC
#


@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

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
    :return: [game token]
    '''
    return jsons.dump(game_create(token))

@jsonrpc.method('player_create')
def player_create_rpc(colour: str, co: str) -> int:
    '''rpc-create player.
    :return: [player.id]
    '''
    player = player_create(colour, co)
    logger.info(f'player_create colour:{player.colour}, co:{player.co}, id:{player.id}')
    return player.id

@jsonrpc.method('player_info')
def player_info(id: int) -> str:
    '''rpc return player info by ID.
    :return: [player one]
    '''
    player = player_load(id)
    logger.info(f'player token={player.token}, colour:{player.colour}, co:{player.co}, id:{player.id}')
    return f'ID: {player.id} : {player.co} : {player.colour} token={player.token}'

@jsonrpc.method('join_game')
def join_game(token: str, pos: int, id: int) -> str:
    '''rpc-join game.
    :return: [ok]
    '''
    try:
        game = Game.from_token(db.session, token)
        player = Player.from_id(db.session, id)
        if game == None:
            abort(404, description="game not found")
        elif player == None:
            abort('player not found')
        elif pos == 1:
            if game.player_one:
                abort(404, description="Player one taken")
            elif player.token:
                abort(404, description="Player already joined game")
            else:
                game.player_one = player.id
                game.players.append(player)
                player.token = game.token
        elif pos == 2:
            if game.player_two:
                abort(404, description="Player two taken")
            elif player.token:
                abort(404, description="Player already joined game")
            else:
                game.player_two = player.id
                game.players.append(player)
                player.token = game.token
        mngr = game_load(token)
        game_save(mngr, token)
        logger.info(f'rpc Joined game={token}, pos:{pos}, id:{id}')
        message(token, f'rpc Joined game={token}, pos:{pos}, id:{id}')
        return 'ok'
    except Exception as ex:
        return abort(400, ex)

@jsonrpc.method('game_p1_p2')
def game_p1_p2(token: str) -> str:
    '''rpc-players info.
    :return: [player one id, player two id]
    '''
    try:
        game = Game.from_token(db.session, token)
        if game is None:
            abort(404, description="game not found")
        logger.info(f'player info game={game.token}, p1 id:{game.player_one}, p2 id:{game.player_two}, players:{game.players}')
        return jsons.dump(p_1(token) + " " + p_2(token))
    except Exception as ex:
        return abort(400, ex)

@jsonrpc.method('game_board')
def game_board(token: str) -> dict:
    '''rpc return game board.
    :return: [gameboard]
    '''
    mngr = game_load(token)
    return jsons.dump(mngr.board)

@jsonrpc.method('army_end_turn')
def army_end_turn(token: str) -> str:
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
def end_game(token: str) -> str:
    '''rpc end game.
    :return: [ok]
    '''
    logger.info(f'end game token={token}')
    mngr = game_load(token)
    if mngr.board.game_active == False:
        text = 'game is not active'
    else:
        try:
            mngr.end_game()
            game_save(mngr, token)
            ws_board_update(token)
            text = 'Game ended'
        except Exception as ex:
            return abort(400, ex)
    logger.info(text)
    ws_msg(token, text)
    return jsons.dump(text)

@jsonrpc.method('start_game')
def start_game(token: str) -> str:
    '''rpc start game.
    :return: [ok]
    '''
    game = Game.from_token(db.session, token)
    if game == None:
        abort(404, description="game not found")
    elif game.player_one and game.player_two:
        mngr = game_load(token)
        try:
            mngr.start_game()
            game_save(mngr, token)
            ws_board_update(token)
            logger.info(f'started game {game.token}')
            ws_msg(token, f'started game {game.token}')
            return 'ok'
        except Exception as ex:
            return abort(400, ex)
    else:
        ws_msg(token, 'join players to start')
        abort(404, description="players not found")


# return the game tile for the coord(x, y)
@jsonrpc.method('tile')
def tile(token: str, x: int, y: int) -> dict:
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
def capture_tile(token: str, x: int, y: int) -> dict:
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
def unit_wait(token: str, x: int, y: int) -> dict:
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
def unit_select(token: str, x: int, y: int) -> dict:
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
def unit_move(token: str, x: int, y: int, x2: int, y2: int) -> dict:
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
def unit_move2(token: str, id: str, x: int, y: int) -> dict:
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


@jsonrpc.method('unit_create_rpc')
def unit_create_rpc(token: str, army: str, unit_type: str, x: int, y: int) -> dict:
    '''rpc create a unit at the coordinates given
    :return: [tile at coordinates]
    '''
    mngr = game_load(token)
    try:
        unit = mngr.unit_create(army, unit_type, x, y)
        game_save(mngr, token)
        ws_board_update(token)
        logger.info(f'unit_create token={token}, army={army}, x={x}, y={y}')
        return jsons.dump(unit)
    except Exception as ex:
        return abort(400, ex)


# need to return both attacker and defender
@jsonrpc.method('damage_estimate')
def damage_estimate(token: str, x: int, y: int, x2: int, y2: int) -> list:
    '''rpc estimates the damage for attacker and defender.
    :return: [tuple (attacker hp, defender hp) ]
    '''
    if Game.from_token(db.session, token) == None:
        return ["Game does not exist"]
    mngr = game_load(token)
    try:
        tup = mngr.damage_estimate(x, y, x2, y2)
        logger.info(f'damage_estimate token={token}, x={x}, y={y}, x2={x2}, y2={y2}')
        return jsons.dump(tup)
    except Exception as ex:
        return abort(400, ex)


# need to return both attacker and defender
@jsonrpc.method('unit_attack')
def unit_attack(token: str, x: int, y: int, x2: int, y2: int) -> str:
    '''rpc attacks the unit from x,y to x2,y2
    :return: [tile at given coordinate]
    '''
    if Game.from_token(db.session, token) == None:
        return "Game does not exist"
    mngr = game_load(token)
    try:
        mngr.unit_attack(x, y, x2, y2)
        game_save(mngr, token)
        ws_board_update(token)
        logger.info(f'unit_attack token={token}, x={x}, y={y}, x2={x2}, y2={y2}')
        return 'OK'
    except Exception as ex:
        return abort(400, ex)


@jsonrpc.method('unit_delete')
def unit_delete(token: str, x: int, y: int) -> str:
    '''rpc deletes unit at given coordinate.
    :return: [tile at coordinates]
    '''
    if Game.from_token(db.session, token) == None:
        return "Game does not exist"
    mngr = game_load(token)
    if mngr.unit_at(x, y) == None:
        return "Unit does not exist"
    mngr.unit_delete(x, y)
    logger.info(f'unit_delete token={token}, x={x}, y={y}')
    game_save(mngr, token)
    ws_board_update(token)
    return "unit deleted"



@jsonrpc.method('check_turn')
def check_turn(token: str) -> str:
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
def unit_join(token: str, x: int, y: int, x2: int, y2: int) -> dict:
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
def unit_load(token: str, x: int, y: int, x2: int, y2: int) -> dict:
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
def unit_unload(token: str, x: int, y: int, x2: int, y2: int, index: int) -> dict:
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
def launch_missile(token: str, x: int, y: int, x2: int, y2: int) -> dict:
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
def unit_resupply(token: str, x: int, y: int, x2: int, y2: int) -> dict:
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
    db.create_all()
    db.session.commit()
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    logging.info(f'binding to port: {port}')
    socketio.run(app, host='0.0.0.0', port=port, debug=True)

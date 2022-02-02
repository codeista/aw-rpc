'''[This module defines and creates the gameboard ]'''

from dataclasses import dataclass, field
from typing import List
from unit import Army, Unit
from mapping import MapTile, Map

import configparser
config = configparser.ConfigParser()
config.read('config.ini')


@dataclass
class GameTile():
    x: int
    y: int
    unit: Unit = None
    mapTile: MapTile = None
    can_be_moved_to: bool = False
    can_be_attacked: bool = False
    capture_hp: int = 20


@dataclass
class GameBoard():
    width: int
    height: int
    grid: List[GameTile] = field(default_factory=list)
    selected: GameTile = None
    turn_order: List[Army] = field(default_factory=list)
    current_turn: Army = None
    game_active: bool = True
    total_red_troops: int = 0
    total_red_properties: int = 0
    red_funds: int = 0
    total_blue_troops: int = 0
    total_blue_properties: int = 0
    blue_funds: int = 0
    days: int = 0

    @classmethod
    def create(cls, map: Map):
        board = GameBoard(map.width, map.height)
        for i in range(map.width * map.height):
            x = i % map.width
            y = int(i / map.width)
            tile = GameTile(x, y, mapTile=map.tiles[i])
            board.grid.append(tile)
            board.turn_order = map.turn_order
            board.current_turn = map.turn_order[0]
            board.total_red_troops = 0
            board.total_red_properties = 0
            board.red_funds = 0
            board.total_blue_troops = 0
            board.total_blue_properties = 0
            board.blue_funds = 0
            board.days = 0
        # add funds from properties for first turn
        for i in board.grid:
            if i.mapTile.army and i.mapTile.army.name == "RED":
                board.red_funds += int(config['FUNDS']['income'])
        return board

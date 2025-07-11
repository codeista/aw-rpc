'''[This module defines and creates the gameboard ]'''

from dataclasses import dataclass, field
from typing import List, Dict
from unit import Army, Unit
from map_system import MapTile, Map

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
    
    # Flexible fund tracking for all armies
    army_funds: Dict[Army, int] = field(default_factory=dict)
    army_properties: Dict[Army, int] = field(default_factory=dict)
    army_troops: Dict[Army, int] = field(default_factory=dict)

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
            if i.mapTile.army:
                if i.mapTile.army.name == "RED":
                    board.red_funds += int(config['FUNDS']['income'])
                    board.total_red_properties += 1
                elif i.mapTile.army.name == "BLUE":
                    board.blue_funds += int(config['FUNDS']['income'])
                    board.total_blue_properties += 1
        
        # Give all armies a starting amount of funds to prevent insufficient funds error
        # This ensures all armies can perform basic actions even without properties
        starting_funds = int(config['FUNDS']['income']) * 10  # 10,000 starting funds
        
        # Initialize flexible fund tracking for all armies
        for army in board.turn_order:
            board.army_funds[army] = starting_funds
            board.army_properties[army] = 0
            board.army_troops[army] = 0
            
            # Also maintain backward compatibility with hardcoded RED/BLUE system
            if army.name == "RED":
                board.red_funds = max(board.red_funds, starting_funds)
            elif army.name == "BLUE":
                board.blue_funds = max(board.blue_funds, starting_funds)
        return board

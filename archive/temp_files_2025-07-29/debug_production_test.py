#!/usr/bin/env python3
"""Debug production test issues"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from manager_v2 import GameManager
from config import Config
from map_system import Map, MapType, Army
from unit import UnitType
from production_system import ProductionSystem

# Create test map with all facility types
map_data = """RED,BLUE
FACTORY:RED,AIRPORT:RED,PORT:RED,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN
PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN
PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN
PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN
"""

board = Map.parse(map_data)
board.funds = {Army.RED: 50000, Army.BLUE: 50000}

manager = GameManager(Config(), board)
ps = ProductionSystem(manager)

# Test each facility
facilities = [(0, 0, "FACTORY"), (1, 0, "AIRPORT"), (2, 0, "PORT")]

for x, y, name in facilities:
    print(f"\n=== Testing {name} at ({x}, {y}) ===")
    
    # Check tile
    tile = manager.tile_at(x, y)
    print(f"Tile type: {tile.mapTile.type}")
    print(f"Tile army: {tile.mapTile.army}")
    
    # Get production options
    options = ps.get_producible_units(x, y, Army.RED)
    print(f"Production options: {options}")
    
    if "error" in options:
        print(f"ERROR: {options['error']}")
    elif "units" in options:
        print(f"Number of units available: {len(options['units'])}")
        if options['units']:
            print(f"First unit: {options['units'][0]}")
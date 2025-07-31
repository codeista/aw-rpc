#!/usr/bin/env python3
"""Debug the actual server errors"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from manager_v2 import GameManager
from config import Config
from map_system import Map
from unit import UnitType, Army

# Create a test game directly
config = Config()

# Create simple map
map_data = """RED,BLUE
FACTORY:RED,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,FACTORY:BLUE
PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN
PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN
PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN
"""

board = Map.parse(map_data)
board.funds = {Army.RED: 50000, Army.BLUE: 50000}

manager = GameManager(config, board)

print("Testing unit creation directly...")

# Create INFANTRY - should work
try:
    unit = manager.unit_create(Army.RED, "INFANTRY", 0, 0)
    print(f"✅ INFANTRY created successfully")
except Exception as e:
    print(f"❌ INFANTRY failed: {type(e).__name__}: {e}")

# Create TANK on same spot - should fail
try:
    unit = manager.unit_create(Army.RED, "TANK", 0, 0)
    print(f"❌ TANK should have failed (factory occupied)")
except Exception as e:
    print(f"✅ TANK correctly failed: {type(e).__name__}: {e}")

# End turns to enable movement
manager.board.current_turn = Army.BLUE
manager.board.days += 1
manager.board.current_turn = Army.RED

# Try to move INFANTRY
try:
    result = manager.unit_move(0, 0, 1, 0)
    if result:
        print(f"✅ INFANTRY moved successfully")
    else:
        print(f"❌ INFANTRY move returned False")
except Exception as e:
    print(f"❌ INFANTRY move failed: {type(e).__name__}: {e}")

# Try to create RECON - should fail with insufficient funds
manager.board.funds[Army.RED] = 3000  # Not enough for RECON (4000)
try:
    unit = manager.unit_create(Army.RED, "RECON", 0, 0)
    print(f"❌ RECON should have failed (insufficient funds)")
except Exception as e:
    print(f"✅ RECON correctly failed: {type(e).__name__}: {e}")

# Test production options
print("\nTesting production options...")
try:
    from production_system import ProductionSystem
    ps = ProductionSystem(manager)
    options = ps.get_producible_units(0, 0, Army.RED)
    print(f"Production options result: {options}")
except Exception as e:
    print(f"❌ Production options failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
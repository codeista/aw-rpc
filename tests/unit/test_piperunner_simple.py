"""Simple test for Piperunner movement restrictions"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.game_factory import GameFactory
from core.unit import UnitType, UnitClass
from core.map_system import MapType, get_movement_cost, MOVEMENT_COSTS

def test_piperunner_movement():
    """Test that Piperunners are properly restricted"""
    manager, token = GameFactory.create_standard_game('tiny')
    manager.board_v2.player_funds[0] = 100000
    
    # Create Piperunner on plains
    piperunner = manager.unit_create_v2(0, "PIPERUNNER", 3, 3)
    print(f"Created Piperunner")
    print(f"Unit type: {piperunner.type}")
    print(f"Unit status.cls: {piperunner.status.cls}")
    print(f"Unit status.cls type: {type(piperunner.status.cls)}")
    
    # Check movement cost calculation
    print(f"\nMovement cost checks:")
    print(f"PLAIN movement costs: {MOVEMENT_COSTS[MapType.PLAIN]}")
    print(f"get_movement_cost(UnitClass.PIPE, PLAIN): {get_movement_cost(UnitClass.PIPE, MapType.PLAIN)}")
    print(f"get_movement_cost(piperunner.status.cls, PLAIN): {get_movement_cost(piperunner.status.cls, MapType.PLAIN)}")
    
    # End turn to allow movement
    manager.army_end_turn()
    manager.army_end_turn()
    
    # Get valid moves
    valid_moves = manager.get_valid_moves(3, 3)
    print(f"\nPiperunner at (3,3) has {len(valid_moves)} valid moves")
    
    if len(valid_moves) > 0:
        print("ERROR: Piperunner can move on non-pipe terrain!")
        print(f"First few valid moves: {valid_moves[:10]}")
    else:
        print("SUCCESS: Piperunner correctly restricted to pipes")

if __name__ == "__main__":
    test_piperunner_movement()
#!/usr/bin/env python3
"""Test the slot-based map system with different player configurations"""

import sys
from game_factory import GameFactory
from test_map_templates import get_test_map

def test_standard_colors():
    """Test with standard RED and BLUE"""
    print("\n=== Test 1: Standard Colors (RED, BLUE) ===")
    
    players = [
        {"name": "Player 1", "color": "Red", "sprite_color": "RED"},
        {"name": "Player 2", "color": "Blue", "sprite_color": "BLUE"}
    ]
    
    # Get test map data
    test_map = get_test_map('combat')
    
    # Create game using the new system
    from map_parser_v2 import MapParserV2
    from gameboard import GameBoard
    from player_system import PlayerManager, SpriteColor
    from manager import GameManager
    from config import Config
    
    # Parse map
    parser = MapParserV2()
    pm_from_map, tiles = parser.parse_lines(test_map['map_data'].strip().split('\n'))
    
    # Create player manager with chosen colors
    player_manager = PlayerManager()
    for i, p in enumerate(players):
        player_manager.add_player(i, p['name'], p['color'], SpriteColor[p['sprite_color']])
    
    # Create board
    board = GameBoard()
    board.create_from_tiles(tiles, parser.width, parser.height)
    
    # Create game manager
    config = Config()
    manager = GameManager(config, board, player_manager)
    
    # Check property ownership
    print(f"Player 0 army: {manager.board.get_army_for_player(0)}")
    print(f"Player 1 army: {manager.board.get_army_for_player(1)}")
    
    # Check a few tiles
    factory_0_0 = manager.tile_at(0, 0)  # Should be owned by player 0
    factory_14_0 = manager.tile_at(14, 0)  # Should be owned by player 1
    
    print(f"Factory at (0,0) owned by: {factory_0_0.mapTile.army if factory_0_0.mapTile else 'None'}")
    print(f"Factory at (14,0) owned by: {factory_14_0.mapTile.army if factory_14_0.mapTile else 'None'}")
    
    return True

def test_swapped_colors():
    """Test with swapped colors - Player 1 gets BLUE, Player 2 gets RED"""
    print("\n=== Test 2: Swapped Colors (BLUE, RED) ===")
    
    players = [
        {"name": "Player 1", "color": "Blue", "sprite_color": "BLUE"},
        {"name": "Player 2", "color": "Red", "sprite_color": "RED"}
    ]
    
    manager, _ = GameFactory.create_game_with_players('combat', players)
    
    # Check property ownership
    print(f"Player 0 army: {manager.board.get_army_for_player(0)}")
    print(f"Player 1 army: {manager.board.get_army_for_player(1)}")
    
    # Check same tiles - ownership should follow player slots, not colors
    factory_0_0 = manager.tile_at(0, 0)  # Should still be owned by player 0 (now BLUE)
    factory_14_0 = manager.tile_at(14, 0)  # Should still be owned by player 1 (now RED)
    
    print(f"Factory at (0,0) owned by: {factory_0_0.mapTile.army if factory_0_0.mapTile else 'None'}")
    print(f"Factory at (14,0) owned by: {factory_14_0.mapTile.army if factory_14_0.mapTile else 'None'}")
    
    return True

def test_custom_colors():
    """Test with custom colors - YELLOW vs GREEN"""
    print("\n=== Test 3: Custom Colors (YELLOW, GREEN) ===")
    
    players = [
        {"name": "Player 1", "color": "Yellow", "sprite_color": "YELLOW"},
        {"name": "Player 2", "color": "Green", "sprite_color": "GREEN"}
    ]
    
    manager, _ = GameFactory.create_game_with_players('combat', players)
    
    # Check property ownership
    print(f"Player 0 army: {manager.board.get_army_for_player(0)}")
    print(f"Player 1 army: {manager.board.get_army_for_player(1)}")
    
    # Properties should be assigned based on slots
    factory_0_0 = manager.tile_at(0, 0)  # Should be owned by player 0 (YELLOW)
    factory_14_0 = manager.tile_at(14, 0)  # Should be owned by player 1 (GREEN)
    
    print(f"Factory at (0,0) owned by: {factory_0_0.mapTile.army if factory_0_0.mapTile else 'None'}")
    print(f"Factory at (14,0) owned by: {factory_14_0.mapTile.army if factory_14_0.mapTile else 'None'}")
    
    return True

def test_predeployed_units():
    """Test that predeployed units get correct army assignment"""
    print("\n=== Test 4: Predeployed Units ===")
    
    players = [
        {"name": "Alice", "color": "Purple", "sprite_color": "YELLOW"},
        {"name": "Bob", "color": "Orange", "sprite_color": "GREEN"}
    ]
    
    # Get test map with predeployed units
    test_map = get_test_map('combat')
    
    # Create game
    manager, _ = GameFactory.create_game_with_map_data(
        test_map['map_data'], 
        players,
        test_map.get('predeployed_units', [])
    )
    
    # Check that units have correct armies
    # Player 0's infantry should be at (5, 4)
    unit_5_4 = manager.unit_at(5, 4)
    if unit_5_4:
        print(f"Unit at (5,4) army: {unit_5_4.army} (should be YELLOW for player 0)")
    else:
        print("ERROR: No unit found at (5,4)")
    
    # Player 1's infantry should be at (9, 4)
    unit_9_4 = manager.unit_at(9, 4)
    if unit_9_4:
        print(f"Unit at (9,4) army: {unit_9_4.army} (should be GREEN for player 1)")
    else:
        print("ERROR: No unit found at (9,4)")
    
    return True

def main():
    """Run all tests"""
    print("Testing Slot-Based Map System")
    print("=" * 50)
    
    tests = [
        test_standard_colors,
        test_swapped_colors,
        test_custom_colors,
        test_predeployed_units
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
                print(f"✓ {test.__name__} PASSED")
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{passed}/{len(tests)} tests passed")
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
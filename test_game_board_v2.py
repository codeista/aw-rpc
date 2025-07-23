#!/usr/bin/env python3
"""
Test GameBoardV2 backward compatibility
"""
from game_board_v2 import GameBoardV2
from player_system import PlayerManager, SpriteColor
from map_system import Army

def test_backward_compatibility():
    """Test that legacy fields still work"""
    print("Testing GameBoardV2 Backward Compatibility...")
    
    # Create standard 2-player game
    pm = PlayerManager.create_default_2_player()
    board = GameBoardV2()
    board.initialize_from_player_manager(pm)
    
    # Test legacy property access
    board.red_funds = 5000
    board.blue_funds = 6000
    
    assert board.red_funds == 5000
    assert board.blue_funds == 6000
    assert board.player_funds[0] == 5000  # Player 0 is RED
    assert board.player_funds[1] == 6000  # Player 1 is BLUE
    print("✓ Legacy fund properties work")
    
    # Test property counts
    board.update_player_properties(0, 5)  # RED player
    board.update_player_properties(1, 3)  # BLUE player
    
    assert board.total_red_properties == 5
    assert board.total_blue_properties == 3
    print("✓ Legacy property counts work")
    
    # Test troop counts
    board.update_player_troops(0, 10)
    board.update_player_troops(1, 8)
    
    assert board.total_red_troops == 10
    assert board.total_blue_troops == 8
    print("✓ Legacy troop counts work")
    
    # Test army mapping
    assert board.get_army_for_player(0) == Army.RED
    assert board.get_army_for_player(1) == Army.BLUE
    assert board.get_player_for_army(Army.RED) == 0
    assert board.get_player_for_army(Army.BLUE) == 1
    print("✓ Army/player mapping works")
    
    # Test current turn
    assert board.current_turn == Army.RED
    board.current_player = 1
    assert board.current_turn == Army.BLUE
    print("✓ Current turn mapping works")
    
    # Test serialization includes legacy fields
    data = board.to_dict()
    assert data['red_funds'] == 5000
    assert data['blue_funds'] == 6000
    assert data['total_red_properties'] == 5
    assert data['total_blue_properties'] == 3
    print("✓ Serialization includes legacy fields")
    
    print("Backward Compatibility: All tests passed!\n")

def test_multi_player():
    """Test with more than 2 players"""
    print("Testing Multi-Player Support...")
    
    # Create 4-player game
    pm = PlayerManager.create_default_4_player()
    board = GameBoardV2()
    board.initialize_from_player_manager(pm)
    
    # Set funds for all players
    board.update_player_funds(0, 5000)  # RED
    board.update_player_funds(1, 5000)  # BLUE
    board.update_player_funds(2, 5000)  # GREEN
    board.update_player_funds(3, 5000)  # YELLOW
    
    assert board.player_funds[0] == 5000
    assert board.player_funds[1] == 5000
    assert board.player_funds[2] == 5000
    assert board.player_funds[3] == 5000
    print("✓ 4-player funds work")
    
    # Test turn order
    assert board.turn_order == [0, 1, 2, 3]
    assert board.get_next_player() == 1
    board.current_player = 3
    assert board.get_next_player() == 0  # Wraps around
    print("✓ Turn order works for 4 players")
    
    # Test army mapping for all players
    assert board.get_army_for_player(2) == Army.GREEN
    assert board.get_army_for_player(3) == Army.YELLOW
    print("✓ Army mapping works for all players")
    
    print("Multi-Player Support: All tests passed!\n")

def test_custom_colors():
    """Test with custom player colors"""
    print("Testing Custom Player Colors...")
    
    # Create game with custom colors
    pm = PlayerManager()
    pm.add_player(0, "Alice", "Purple", SpriteColor.RED)
    pm.add_player(1, "Bob", "Orange", SpriteColor.BLUE)
    pm.add_player(2, "Charlie", "Pink", SpriteColor.GREEN)
    
    board = GameBoardV2()
    board.initialize_from_player_manager(pm)
    
    # Players use standard sprite colors internally
    assert board.get_army_for_player(0) == Army.RED
    assert board.get_army_for_player(1) == Army.BLUE
    assert board.get_army_for_player(2) == Army.GREEN
    
    # But player manager knows their display colors
    assert pm.get_player(0).color == "Purple"
    assert pm.get_player(1).color == "Orange"
    assert pm.get_player(2).color == "Pink"
    
    print("✓ Custom colors work with standard sprites")
    print("Custom Player Colors: All tests passed!\n")

def main():
    """Run all tests"""
    print("=== GameBoardV2 Tests ===\n")
    
    test_backward_compatibility()
    test_multi_player()
    test_custom_colors()
    
    print("=== All Tests Passed! ===")
    print("\nGameBoardV2 successfully:")
    print("- Maintains backward compatibility with legacy code")
    print("- Supports any number of players")
    print("- Allows custom player colors")
    print("- Maps players to existing sprite sets")

if __name__ == "__main__":
    main()
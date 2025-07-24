#!/usr/bin/env python3
"""
Test color decoupling with actual game integration
"""
from game_factory import GameFactory
from map_system import Army
from unit import UnitType
from player_system import SpriteColor

def test_standard_game():
    """Test standard 2-player game"""
    print("Testing Standard 2-Player Game...")
    
    # Create standard game
    manager, token = GameFactory.create_standard_game("small_test")
    
    # Verify player setup
    assert manager.player_manager.get_player_count() == 2
    assert manager.board_v2.player_funds[0] > 0  # Player 0 has funds
    assert manager.board_v2.player_funds[1] > 0  # Player 1 has funds
    
    # Get initial troop count
    initial_troops = manager.board_v2.player_troops.get(0, 0)
    
    # Test unit creation
    unit = manager.unit_create("RED", "INFANTRY", 2, 2)
    assert unit is not None
    assert manager.board_v2.player_troops[0] == initial_troops + 1  # Player 0 has 1 more troop
    
    print("✓ Standard game works")
    print(f"  Player 0 funds: {manager.board_v2.player_funds[0]}")
    print(f"  Player 1 funds: {manager.board_v2.player_funds[1]}")
    print()

def test_custom_colors():
    """Test game with custom player colors"""
    print("Testing Custom Color Game...")
    
    # Create game with custom players
    players = [
        {"name": "Fire Nation", "color": "Orange", "sprite_color": "RED"},
        {"name": "Water Tribe", "color": "Cyan", "sprite_color": "BLUE"},
        {"name": "Earth Kingdom", "color": "Brown", "sprite_color": "GREEN"}
    ]
    
    manager, token = GameFactory.create_game_with_players("triangle_test", players)
    
    # Verify player setup
    assert manager.player_manager.get_player_count() == 3
    
    player0 = manager.player_manager.get_player(0)
    assert player0.name == "Fire Nation"
    assert player0.color == "Orange"
    assert player0.sprite_color == SpriteColor.RED
    
    # Test that sprite mapping works
    assert manager.board_v2.get_army_for_player(0) == Army.RED
    assert manager.board_v2.get_army_for_player(1) == Army.BLUE
    assert manager.board_v2.get_army_for_player(2) == Army.GREEN
    
    print("✓ Custom colors work")
    for i in range(3):
        player = manager.player_manager.get_player(i)
        print(f"  Player {i}: {player.name} ({player.color}) using {player.sprite_color.value} sprites")
    print()

def test_turn_progression():
    """Test turn progression with multiple players"""
    print("Testing Turn Progression...")
    
    # Create 4-player game
    manager, token = GameFactory.create_4_player_game("cross_test")
    
    # Verify initial state
    assert manager.board_v2.current_player == 0
    assert manager.board.current_turn == Army.RED
    
    # Progress turns
    turns = []
    initial_day = manager.board.days
    for i in range(8):  # Two full rounds
        current = manager.board_v2.current_player
        turns.append(current)
        manager._advance_to_next_army()
    
    # Verify turn order
    assert turns == [0, 1, 2, 3, 0, 1, 2, 3]
    # Days increment when wrapping from player 3 to 0
    # Initial: day 1, after 4 turns: day 2, after 8 turns: day 3
    assert manager.board.days == initial_day + 2  # Completed 2 rounds
    
    print("✓ Turn progression works")
    print(f"  Turn sequence: {turns}")
    print(f"  Days after 2 rounds: {manager.board.days}")
    print()

def test_backward_compatibility():
    """Test backward compatibility with legacy code"""
    print("Testing Backward Compatibility...")
    
    # Create game
    manager, token = GameFactory.create_standard_game("small_test")
    
    # Test legacy property access
    manager.board_v2.red_funds = 5000
    assert manager.board_v2.player_funds[0] == 5000
    assert manager.board_v2.red_funds == 5000
    
    manager.board_v2.blue_funds = 6000
    assert manager.board_v2.player_funds[1] == 6000
    assert manager.board_v2.blue_funds == 6000
    
    # Test legacy methods
    red_funds = manager._get_army_funds(Army.RED)
    blue_funds = manager._get_army_funds(Army.BLUE)
    assert red_funds == 5000
    assert blue_funds == 6000
    
    print("✓ Backward compatibility maintained")
    print(f"  Legacy red_funds: {manager.board_v2.red_funds}")
    print(f"  Legacy blue_funds: {manager.board_v2.blue_funds}")
    print()

def test_economic_system():
    """Test that the economic system works with players"""
    print("Testing Economic System...")
    
    # Create game
    manager, token = GameFactory.create_standard_game("small_test")
    
    # Get initial funds
    initial_p0 = manager.board_v2.player_funds[0]
    initial_p1 = manager.board_v2.player_funds[1]
    
    # Update funds
    manager._update_army_funds(Army.RED, 1000)
    manager._update_army_funds(Army.BLUE, -500)
    
    # Verify updates
    assert manager.board_v2.player_funds[0] == initial_p0 + 1000
    assert manager.board_v2.player_funds[1] == initial_p1 - 500
    
    print("✓ Economic system works")
    print(f"  Player 0: {initial_p0} -> {manager.board_v2.player_funds[0]}")
    print(f"  Player 1: {initial_p1} -> {manager.board_v2.player_funds[1]}")
    print()

def test_game_state_serialization():
    """Test that game state includes player information"""
    print("Testing Game State Serialization...")
    
    # Create custom game
    players = [
        {"name": "Alice", "color": "Purple", "sprite_color": "RED"},
        {"name": "Bob", "color": "Orange", "sprite_color": "BLUE"}
    ]
    
    manager, token = GameFactory.create_game_with_players("small_test", players)
    
    # Get game state
    state = manager.to_dict()
    
    # Verify player info is included
    assert 'players' in state
    assert 'sprite_mapping' in state
    assert 'player_funds' in state
    
    # Check player data
    assert state['players']['0']['name'] == "Alice"
    assert state['players']['0']['color'] == "Purple"
    assert state['sprite_mapping']['0'] == "RED"
    
    print("✓ Game state serialization includes player data")
    print(f"  Players in state: {list(state['players'].keys())}")
    print(f"  Sprite mapping: {state['sprite_mapping']}")
    print()

def main():
    """Run all tests"""
    print("=== Color Decoupling Game Integration Tests ===\n")
    
    # Create test maps if they don't exist
    create_test_maps()
    
    # Run tests
    test_standard_game()
    test_custom_colors()
    test_turn_progression()
    test_backward_compatibility()
    test_economic_system()
    test_game_state_serialization()
    
    print("=== All Tests Passed! ===")
    print("\nThe color decoupling system is working correctly with:")
    print("- Custom player names and colors")
    print("- Flexible sprite mapping")
    print("- Full backward compatibility")
    print("- Proper turn management")
    print("- Economic system integration")

def create_test_maps():
    """Create simple test maps"""
    import os
    
    # Small test map (2 players)
    small_test = """2
8,6
PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN
PLAIN FACTORY:0 PLAIN CITY:0 CITY:1 PLAIN FACTORY:1 PLAIN
PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN
PLAIN BASE_TOWER_0:0 PLAIN PLAIN PLAIN PLAIN BASE_TOWER_0:1 PLAIN
PLAIN PLAIN PLAIN WOOD WOOD PLAIN PLAIN PLAIN
PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN"""
    
    # Triangle test map (3 players)
    triangle_test = """3
9,7
PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN
FACTORY:0 PLAIN BASE_TOWER_0:0 PLAIN PLAIN PLAIN BASE_TOWER_0:1 PLAIN FACTORY:1
PLAIN PLAIN PLAIN PLAIN CITY PLAIN PLAIN PLAIN PLAIN
PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN
PLAIN PLAIN PLAIN BASE_TOWER_0:2 PLAIN PLAIN PLAIN PLAIN PLAIN
PLAIN PLAIN FACTORY:2 PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN
PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN"""
    
    # Cross test map (4 players)
    cross_test = """4
8,8
FACTORY:0 PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN FACTORY:1
PLAIN BASE_TOWER_0:0 PLAIN PLAIN PLAIN PLAIN BASE_TOWER_0:1 PLAIN
PLAIN PLAIN PLAIN CITY CITY PLAIN PLAIN PLAIN
PLAIN PLAIN CITY PLAIN PLAIN CITY PLAIN PLAIN
PLAIN PLAIN CITY PLAIN PLAIN CITY PLAIN PLAIN
PLAIN PLAIN PLAIN CITY CITY PLAIN PLAIN PLAIN
PLAIN BASE_TOWER_0:3 PLAIN PLAIN PLAIN PLAIN BASE_TOWER_0:2 PLAIN
FACTORY:3 PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN FACTORY:2"""
    
    # Create maps directory if needed
    os.makedirs('maps_v2', exist_ok=True)
    
    # Write test maps
    with open('maps_v2/small_test.txt', 'w') as f:
        f.write(small_test)
    with open('maps_v2/triangle_test.txt', 'w') as f:
        f.write(triangle_test)
    with open('maps_v2/cross_test.txt', 'w') as f:
        f.write(cross_test)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Simple test of color decoupling components
"""
from player_system import PlayerManager, SpriteColor
from game_board_v2 import GameBoardV2
from map_parser_v2 import MapParserV2
from map_system import Army

def test_components():
    """Test individual components work together"""
    print("Testing Color Decoupling Components...\n")
    
    # Test 1: Player Manager
    print("1. Testing PlayerManager...")
    pm = PlayerManager()
    pm.add_player(0, "Fire Nation", "Orange", SpriteColor.RED)
    pm.add_player(1, "Water Tribe", "Cyan", SpriteColor.BLUE)
    pm.add_player(2, "Earth Kingdom", "Brown", SpriteColor.GREEN)
    
    assert pm.get_player_count() == 3
    assert pm.get_sprite_color(0) == "RED"
    assert pm.get_player(1).color == "Cyan"
    print("✓ PlayerManager works with custom colors")
    
    # Test 2: GameBoardV2
    print("\n2. Testing GameBoardV2...")
    board = GameBoardV2()
    board.initialize_from_player_manager(pm)
    
    # Test player mapping
    assert board.get_army_for_player(0) == Army.RED
    assert board.get_army_for_player(1) == Army.BLUE
    assert board.get_army_for_player(2) == Army.GREEN
    
    # Test fund management
    board.update_player_funds(0, 5000)
    board.update_player_funds(1, 6000)
    board.update_player_funds(2, 4000)
    
    assert board.player_funds[0] == 5000
    assert board.player_funds[1] == 6000
    assert board.player_funds[2] == 4000
    
    # Test backward compatibility
    assert board.red_funds == 5000
    assert board.blue_funds == 6000
    
    print("✓ GameBoardV2 maps players to armies correctly")
    print("✓ Backward compatibility maintained")
    
    # Test 3: Map Parser
    print("\n3. Testing Map Parser...")
    
    # New format map
    new_map = """3
5,3
PLAIN FACTORY:0 PLAIN FACTORY:1 PLAIN
PLAIN BASE_TOWER_0:0 PLAIN BASE_TOWER_0:1 PLAIN
PLAIN FACTORY:2 PLAIN BASE_TOWER_0:2 PLAIN"""
    
    parser = MapParserV2()
    pm_from_map, tiles = parser.parse_lines(new_map.strip().split('\n'))
    
    assert pm_from_map.get_player_count() == 3
    # Check that tiles were parsed correctly
    from map_system import MapType
    assert tiles[0][1][0] == MapType.FACTORY  # Factory type
    assert tiles[0][1][1] == 0  # Owned by player 0
    assert tiles[1][3][0] == MapType.BASE_TOWER_0  # HQ type
    assert tiles[1][3][1] == 1  # Owned by player 1
    
    print("✓ Map parser handles player indices")
    
    # Legacy format map
    legacy_map = """RED,BLUE,GREEN
5,3
PLAIN FACTORY:RED PLAIN FACTORY:BLUE PLAIN
PLAIN BASE_TOWER_0:RED PLAIN BASE_TOWER_0:BLUE PLAIN
PLAIN FACTORY:GREEN PLAIN BASE_TOWER_0:GREEN PLAIN"""
    
    pm_legacy, tiles_legacy = parser.parse_lines(legacy_map.strip().split('\n'))
    
    # Should convert to same result
    assert tiles_legacy[0][1][1] == 0  # RED -> player 0
    assert tiles_legacy[0][3][1] == 1  # BLUE -> player 1
    assert tiles_legacy[2][1][1] == 2  # GREEN -> player 2
    
    print("✓ Map parser handles legacy format")
    
    # Test 4: Integration
    print("\n4. Testing Integration...")
    
    # Create board from parsed map
    board2 = GameBoardV2()
    board2.width = 5
    board2.height = 3
    board2.initialize_from_player_manager(pm_from_map)
    
    # Simulate turn progression
    assert board2.current_player == 0
    board2.current_player = board2.get_next_player()
    assert board2.current_player == 1
    board2.current_player = board2.get_next_player()
    assert board2.current_player == 2
    board2.current_player = board2.get_next_player()
    assert board2.current_player == 0  # Wraps around
    
    print("✓ Turn order works with multiple players")
    
    # Test 5: Serialization
    print("\n5. Testing Serialization...")
    
    state = board.to_dict()
    assert 'player_funds' in state
    assert 'current_player' in state
    assert state['player_funds'] == {0: 5000, 1: 6000, 2: 4000}
    
    # Legacy fields should be included
    assert state['red_funds'] == 5000
    assert state['blue_funds'] == 6000
    
    print("✓ Serialization includes both new and legacy fields")
    
    print("\n=== All Component Tests Passed! ===")
    print("\nSummary:")
    print("- PlayerManager supports custom colors")
    print("- GameBoardV2 provides player<->army mapping")
    print("- Map parser handles both formats")
    print("- Turn progression works for any player count")
    print("- Full backward compatibility maintained")

if __name__ == "__main__":
    test_components()
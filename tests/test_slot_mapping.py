#!/usr/bin/env python3
"""Simple test to verify slot mapping works correctly"""

from map_parser_v2 import MapParserV2
from player_system import PlayerManager, SpriteColor
from map_system import Army

# Simple test map with player 0 and player 1 properties
test_map = """2
3,3
FACTORY:0 PLAIN FACTORY:1
PLAIN CITY PLAIN
CITY:0 PLAIN CITY:1"""

def test_slot_to_army_mapping():
    """Test that player slots map to correct armies"""
    
    # Test 1: Standard mapping (Player 0 = RED, Player 1 = BLUE)
    print("Test 1: Standard Colors")
    parser = MapParserV2()
    pm, tiles = parser.parse_lines(test_map.strip().split('\n'))
    
    # Player manager has default colors
    print(f"Player 0 sprite color: {pm.get_player(0).sprite_color}")
    print(f"Player 1 sprite color: {pm.get_player(1).sprite_color}")
    
    # Test 2: Custom colors (Player 0 = YELLOW, Player 1 = GREEN)
    print("\nTest 2: Custom Colors")
    custom_pm = PlayerManager()
    custom_pm.add_player(0, "Alice", "Yellow", SpriteColor.YELLOW)
    custom_pm.add_player(1, "Bob", "Green", SpriteColor.GREEN)
    
    print(f"Player 0 sprite color: {custom_pm.get_player(0).sprite_color}")
    print(f"Player 1 sprite color: {custom_pm.get_player(1).sprite_color}")
    
    # Test 3: Map sprite colors to armies
    print("\nTest 3: Sprite to Army Mapping")
    sprite_to_army = {
        SpriteColor.RED: Army.RED,
        SpriteColor.BLUE: Army.BLUE,
        SpriteColor.GREEN: Army.GREEN,
        SpriteColor.YELLOW: Army.YELLOW,
        SpriteColor.GREY: Army.GREY
    }
    
    print(f"Player 0 (YELLOW) -> Army: {sprite_to_army[custom_pm.get_player(0).sprite_color]}")
    print(f"Player 1 (GREEN) -> Army: {sprite_to_army[custom_pm.get_player(1).sprite_color]}")

if __name__ == "__main__":
    test_slot_to_army_mapping()
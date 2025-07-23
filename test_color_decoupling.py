#!/usr/bin/env python3
"""
Test the color decoupling system
"""
from player_system import PlayerManager, SpriteColor
from map_parser_v2 import MapParserV2
from map_system import MapType
import os

def test_player_system():
    """Test the player system"""
    print("Testing Player System...")
    
    # Test default 2-player setup
    pm = PlayerManager.create_default_2_player()
    assert pm.get_player_count() == 2
    assert pm.get_sprite_color(0) == "RED"
    assert pm.get_sprite_color(1) == "BLUE"
    print("✓ Default 2-player setup works")
    
    # Test 4-player setup
    pm4 = PlayerManager.create_default_4_player()
    assert pm4.get_player_count() == 4
    assert pm4.get_sprite_color(2) == "GREEN"
    assert pm4.get_sprite_color(3) == "YELLOW"
    print("✓ Default 4-player setup works")
    
    # Test custom player
    pm_custom = PlayerManager()
    pm_custom.add_player(0, "Alice", "Purple", SpriteColor.RED)
    pm_custom.add_player(1, "Bob", "Orange", SpriteColor.BLUE)
    
    player = pm_custom.get_player(0)
    assert player.name == "Alice"
    assert player.color == "Purple"
    assert player.sprite_color == SpriteColor.RED
    print("✓ Custom player colors work")
    
    # Test serialization
    data = pm_custom.to_dict()
    pm_loaded = PlayerManager.from_dict(data)
    assert pm_loaded.get_player_count() == 2
    assert pm_loaded.get_sprite_color(0) == "RED"
    print("✓ Serialization works")
    
    print("Player System: All tests passed!\n")

def test_map_parser():
    """Test the map parser"""
    print("Testing Map Parser...")
    
    # Create a test legacy map
    legacy_map = """RED,BLUE
5,3
PLAIN PLAIN FACTORY:RED PLAIN PLAIN
PLAIN MOUNTAIN PLAIN MOUNTAIN PLAIN
PLAIN PLAIN FACTORY:BLUE PLAIN PLAIN"""
    
    # Parse legacy format
    parser = MapParserV2()
    pm, tiles = parser.parse_lines(legacy_map.strip().split('\n'))
    
    assert pm.get_player_count() == 2
    assert pm.get_sprite_color(0) == "RED"
    assert pm.get_sprite_color(1) == "BLUE"
    assert tiles[0][2] == (MapType.FACTORY, 0)  # RED factory -> player 0
    assert tiles[2][2] == (MapType.FACTORY, 1)  # BLUE factory -> player 1
    print("✓ Legacy format parsing works")
    
    # Create a test new format map
    new_map = """2
5,3
PLAIN PLAIN FACTORY:0 PLAIN PLAIN
PLAIN MOUNTAIN PLAIN MOUNTAIN PLAIN
PLAIN PLAIN FACTORY:1 PLAIN PLAIN"""
    
    # Parse new format
    parser2 = MapParserV2()
    pm2, tiles2 = parser2.parse_lines(new_map.strip().split('\n'))
    
    assert pm2.get_player_count() == 2
    assert tiles2[0][2] == (MapType.FACTORY, 0)
    assert tiles2[2][2] == (MapType.FACTORY, 1)
    print("✓ New format parsing works")
    
    # Test 4-player map
    four_player_map = """4
5,3
CITY:0 PLAIN CITY:1 PLAIN CITY:2
PLAIN MOUNTAIN PLAIN MOUNTAIN PLAIN
PLAIN CITY:3 PLAIN BASE_TOWER_0:0 PLAIN"""
    
    parser3 = MapParserV2()
    pm3, tiles3 = parser3.parse_lines(four_player_map.strip().split('\n'))
    
    assert pm3.get_player_count() == 4
    assert tiles3[0][0] == (MapType.CITY, 0)
    assert tiles3[0][4] == (MapType.CITY, 2)
    assert tiles3[2][1] == (MapType.CITY, 3)
    print("✓ 4-player map parsing works")
    
    print("Map Parser: All tests passed!\n")

def test_map_conversion():
    """Test converting legacy maps to new format"""
    print("Testing Map Conversion...")
    
    # Create a legacy map file
    legacy_content = """# Test map
RED,BLUE
8,6
PLAIN PLAIN PLAIN CITY:RED PLAIN PLAIN PLAIN PLAIN
PLAIN MOUNTAIN PLAIN PLAIN PLAIN PLAIN MOUNTAIN PLAIN
FACTORY:RED PLAIN WOOD PLAIN PLAIN WOOD PLAIN FACTORY:BLUE
PLAIN PLAIN PLAIN BASE_TOWER_0:RED BASE_TOWER_0:BLUE PLAIN PLAIN PLAIN
PLAIN MOUNTAIN PLAIN PLAIN PLAIN PLAIN MOUNTAIN PLAIN
PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN"""
    
    # Write legacy map
    with open('temp_legacy_map.txt', 'w') as f:
        f.write(legacy_content)
    
    # Convert to new format
    MapParserV2.convert_legacy_to_new('temp_legacy_map.txt', 'temp_new_map.txt')
    
    # Read converted map
    with open('temp_new_map.txt', 'r') as f:
        new_content = f.read()
    
    # Verify conversion
    assert new_content.startswith('2\n')  # 2 players
    assert 'CITY:0' in new_content  # RED -> 0
    assert 'FACTORY:1' in new_content  # BLUE -> 1
    assert 'BASE_TOWER_0:0' in new_content
    assert 'BASE_TOWER_0:1' in new_content
    
    # Parse both and compare
    parser_legacy = MapParserV2()
    pm_legacy, tiles_legacy = parser_legacy.parse_file('temp_legacy_map.txt')
    
    parser_new = MapParserV2()
    pm_new, tiles_new = parser_new.parse_file('temp_new_map.txt')
    
    # Compare tiles
    for y in range(6):
        for x in range(8):
            assert tiles_legacy[y][x] == tiles_new[y][x], f"Mismatch at ({x},{y})"
    
    print("✓ Map conversion works correctly")
    
    # Cleanup
    os.remove('temp_legacy_map.txt')
    os.remove('temp_new_map.txt')
    
    print("Map Conversion: All tests passed!\n")

def main():
    """Run all tests"""
    print("=== Color Decoupling System Tests ===\n")
    
    test_player_system()
    test_map_parser()
    test_map_conversion()
    
    print("=== All Tests Passed! ===")
    print("\nNext steps:")
    print("1. Update game manager to use PlayerManager")
    print("2. Modify sprite lookup in frontend")
    print("3. Convert existing maps to new format")
    print("4. Update API to support flexible colors")

if __name__ == "__main__":
    main()
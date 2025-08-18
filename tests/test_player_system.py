#!/usr/bin/env python3
"""
Test the new player-based system components
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.unit import Unit, UnitType
from core.map_system import MapV2, MapTileV2, MapType
from config import Config

def test_unit_with_player():
    """Test creating units with player IDs"""
    print("Testing Unit with player_id...")
    
    config = Config()
    unit_config = config.units["TANK"]
    
    # Test new create_with_player method
    unit = Unit.create_with_player(
        player_id=0,
        unit_type=UnitType.TANK, 
        unit_config=unit_config
    )
    
    assert unit.player_id == 0
    assert unit.army.name == 0  # Backward compatibility
    assert unit.type == UnitType.TANK
    print("✅ Unit created with player_id")
    
    # Test with player 2
    unit2 = Unit.create_with_player(
        player_id=2,
        unit_type=UnitType.INFANTRY,
        unit_config=config.units["INFANTRY"]
    )
    
    assert unit2.player_id == 2
    assert unit2.army.name == "GREEN"  # Maps to GREEN
    print("✅ Player ID mapping works correctly")


def test_map_v2():
    """Test new map format with player IDs"""
    print("\nTesting MapV2...")
    
    # Create a simple 2-player map
    map_data = """2
PLAIN,PLAIN,CITY:0,PLAIN,CITY:1
PLAIN,WOOD,PLAIN,WOOD,PLAIN
SEA,SEA,PLAIN,SEA,SEA
PLAIN,FACTORY:0,PLAIN,FACTORY:1,PLAIN
BASE_TOWER_0:0,PLAIN,PLAIN,PLAIN,BASE_TOWER_1:1
"""
    
    map_v2 = MapV2.parse(map_data, "Test Map")
    
    assert map_v2.player_count == 2
    assert map_v2.width == 5
    assert map_v2.height == 5
    assert len(map_v2.tiles) == 25
    print("✅ MapV2 parsed correctly")
    
    # Check specific tiles
    # Top row city for player 0
    city_tile = map_v2.get_tile(2, 0)
    assert city_tile.type == MapType.CITY
    assert city_tile.player_id == 0
    
    # Bottom row HQ for player 1
    hq_tile = map_v2.get_tile(4, 4)
    assert hq_tile.type == MapType.BASE_TOWER_1
    assert hq_tile.player_id == 1
    assert hq_tile.is_hq()
    print("✅ Tile ownership works correctly")
    
    # Test neutral tiles
    plain_tile = map_v2.get_tile(0, 0)
    assert plain_tile.type == MapType.PLAIN
    assert plain_tile.player_id is None
    print("✅ Neutral tiles work correctly")


def test_map_conversion():
    """Test converting legacy maps to new format"""
    print("\nTesting legacy map conversion...")
    
    from map_system import Map, MapTile, Army
    
    # Create a legacy map
    legacy_data = """RED,BLUE
PLAIN,CITY:RED,PLAIN,CITY:BLUE,PLAIN
WOOD,PLAIN,PLAIN,PLAIN,WOOD  
BASE_TOWER_0:RED,PLAIN,PLAIN,PLAIN,BASE_TOWER_1:BLUE
"""
    
    legacy_map = Map.parse(legacy_data, "Legacy Map")
    
    # Convert to MapV2
    map_v2 = MapV2.from_legacy_map(legacy_map)
    
    assert map_v2.player_count == 2
    assert map_v2.width == 5
    assert map_v2.height == 3
    
    # Check conversions
    # RED city -> player 0
    city_tile = map_v2.get_tile(1, 0)
    assert city_tile.type == MapType.CITY
    assert city_tile.player_id == 0
    
    # BLUE HQ -> player 1
    hq_tile = map_v2.get_tile(4, 2)
    assert hq_tile.type == MapType.BASE_TOWER_1
    assert hq_tile.player_id == 1
    
    print("✅ Legacy map conversion works")


def main():
    """Run all tests"""
    print("🧪 Testing Player System Components")
    print("=" * 50)
    
    try:
        test_unit_with_player()
        test_map_v2()
        test_map_conversion()
        
        print("\n✅ All tests passed!")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
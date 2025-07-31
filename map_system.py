"""
Map System - Simplified to use only slot-based maps from files
"""
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import os


class UnitClass(Enum):
    FOOT = 'FOOT'
    BOOTS = 'BOOTS'
    TYRES = 'TYRES'
    TREADS = 'TREADS'
    AIR = 'AIR'
    SEA = 'SEA'
    LANDER = 'LANDER'
    PIPE = 'PIPE'


class MapType(Enum):
    # Terrain types
    PLAIN = 1
    MOUNTAIN = 2
    WOOD = 3
    RIVER_HORT = 100
    RIVER_VERT = 101
    RIVER_NW = 102
    RIVER_NE = 103
    RIVER_SE = 104
    RIVER_SW = 105
    ROAD_HORT = 200
    ROAD_VERT = 201
    ROAD_NW = 202
    ROAD_NE = 203
    ROAD_SE = 204
    ROAD_SW = 205
    BRIDGE_HORT = 300
    BRIDGE_VERT = 301
    SEA = 400
    REEF = 401
    BEACH_N = 500
    BEACH_S = 501
    BEACH_E = 502
    BEACH_W = 503
    BEACH_NE = 504
    BEACH_NW = 505
    BEACH_SE = 506
    BEACH_SW = 507
    PIPE_HORT = 600
    PIPE_VERT = 601
    PIPE_N = 602
    PIPE_S = 603
    PIPE_E = 604
    PIPE_W = 605
    PIPE_NE = 606
    PIPE_NW = 607
    PIPE_SE = 608
    PIPE_SW = 609
    BROKEN_PIPE_HORT = 650
    BROKEN_PIPE_VERT = 651
    BROKEN_PIPE_N = 652
    BROKEN_PIPE_S = 653
    BROKEN_PIPE_E = 654
    BROKEN_PIPE_W = 655
    BASE_TOWER_0 = 700
    BASE_TOWER_1 = 701
    BASE_TOWER_2 = 702
    BASE_TOWER_3 = 703
    BASE_TOWER_4 = 704
    CITY = 705
    FACTORY = 706
    AIRPORT = 707
    PORT = 708
    COM_TOWER = 709
    EMPTY_SILO = 710
    MISSILE_SILO = 711


class Army(Enum):
    RED = 'RED'
    BLUE = 'BLUE'
    GREEN = 'GREEN'
    YELLOW = 'YELLOW'
    GREY = 'GREY'
    
    @property
    def is_neutral(self):
        return self == Army.GREY


@dataclass
class MapTile:
    """Individual map tile"""
    type: MapType
    army: Optional[Army] = None
    
    def is_property(self) -> bool:
        """Check if tile is a capturable property"""
        return self.type in {
            MapType.CITY, MapType.FACTORY, MapType.AIRPORT,
            MapType.PORT, MapType.COM_TOWER,
            MapType.BASE_TOWER_0, MapType.BASE_TOWER_1,
            MapType.BASE_TOWER_2, MapType.BASE_TOWER_3,
            MapType.BASE_TOWER_4
        }
    
    def is_production_facility(self) -> bool:
        """Check if tile can produce units"""
        return self.type in {MapType.FACTORY, MapType.AIRPORT, MapType.PORT}
    
    def is_hq(self) -> bool:
        """Check if tile is a headquarters"""
        return self.type in {
            MapType.BASE_TOWER_0, MapType.BASE_TOWER_1,
            MapType.BASE_TOWER_2, MapType.BASE_TOWER_3,
            MapType.BASE_TOWER_4
        }
    
    def is_capturable(self) -> bool:
        """Check if tile can be captured"""
        return self.type in {
            MapType.CITY, MapType.FACTORY, MapType.AIRPORT,
            MapType.PORT, MapType.COM_TOWER,
            MapType.BASE_TOWER_0, MapType.BASE_TOWER_1,
            MapType.BASE_TOWER_2, MapType.BASE_TOWER_3
        }


@dataclass 
class Map:
    """Map data structure"""
    width: int
    height: int
    tiles: List[MapTile]
    turn_order: List[Army]
    name: str = "Unknown Map"
    
    def tile_at(self, x: int, y: int) -> Optional[MapTile]:
        """Get tile at coordinates"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y * self.width + x]
        return None


class MapRepository:
    """Repository for loading maps from files"""
    
    def __init__(self):
        self._maps: Dict[str, Map] = {}
        self.maps_directory = "maps"
        self._load_maps()
        
    def _load_maps(self):
        """Load all maps from the maps directory"""
        # Load the default test map from test_map_templates if no maps exist
        try:
            from test_map_templates import get_test_map
            
            # Get combat test map as default
            test_map_data = get_test_map('combat')
            if test_map_data:
                from map_parser_v2 import MapParserV2
                parser = MapParserV2()
                pm, tiles = parser.parse_lines(test_map_data['map_data'].strip().split('\n'))
                
                # Convert to Map format
                map_tiles = []
                turn_order = []
                
                for y in range(parser.height):
                    for x in range(parser.width):
                        tile_type, owner = tiles[y][x]
                        map_tile = MapTile(tile_type)
                        
                        if owner is not None:
                            # Map player slot to army based on standard colors
                            army_map = {0: Army.RED, 1: Army.BLUE, 2: Army.GREEN, 3: Army.YELLOW, 4: Army.GREY}
                            if owner in army_map:
                                map_tile.army = army_map[owner]
                                if map_tile.army not in turn_order:
                                    turn_order.append(map_tile.army)
                                    
                        map_tiles.append(map_tile)
                
                self._maps['test'] = Map(
                    width=parser.width,
                    height=parser.height,
                    tiles=map_tiles,
                    turn_order=turn_order if turn_order else [Army.RED, Army.BLUE],
                    name="Test Combat Map"
                )
        except Exception as e:
            print(f"Failed to load default test map: {e}")
            
        # Load maps from files if directory exists
        if os.path.exists(self.maps_directory):
            for filename in os.listdir(self.maps_directory):
                if filename.endswith('.txt'):
                    map_name = filename[:-4]  # Remove .txt extension
                    try:
                        self._load_map_from_file(map_name, os.path.join(self.maps_directory, filename))
                    except Exception as e:
                        print(f"Failed to load map {filename}: {e}")
                        
    def _load_map_from_file(self, map_name: str, filepath: str):
        """Load a single map from file"""
        from map_parser_v2 import MapParserV2
        
        parser = MapParserV2()
        pm, tiles = parser.parse_file(filepath)
        
        # Convert to Map format
        map_tiles = []
        turn_order = []
        
        for y in range(parser.height):
            for x in range(parser.width):
                tile_type, owner = tiles[y][x]
                map_tile = MapTile(tile_type)
                
                if owner is not None:
                    # Map player slot to army
                    army_map = {0: Army.RED, 1: Army.BLUE, 2: Army.GREEN, 3: Army.YELLOW, 4: Army.GREY}
                    if owner in army_map:
                        map_tile.army = army_map[owner]
                        if map_tile.army not in turn_order:
                            turn_order.append(map_tile.army)
                            
                map_tiles.append(map_tile)
        
        self._maps[map_name] = Map(
            width=parser.width,
            height=parser.height,
            tiles=map_tiles,
            turn_order=turn_order,
            name=map_name.replace('_', ' ').title()
        )
        
    def get_map(self, name: str) -> Optional[Map]:
        """Get map by name"""
        return self._maps.get(name)
        
    def list_maps(self) -> List[str]:
        """List available map names"""
        return sorted(self._maps.keys())


# Global map repository instance
map_repository = MapRepository()


# Terrain defense values
TERRAIN_DEFENSE_STARS = {
    MapType.PLAIN: 1,
    MapType.WOOD: 2,
    MapType.MOUNTAIN: 4,
    MapType.CITY: 3,
    MapType.FACTORY: 3,
    MapType.AIRPORT: 3,
    MapType.PORT: 3,
    MapType.BASE_TOWER_0: 4,
    MapType.BASE_TOWER_1: 4,
    MapType.BASE_TOWER_2: 4,
    MapType.BASE_TOWER_3: 4,
    MapType.BASE_TOWER_4: 4,
    MapType.COM_TOWER: 3,
    MapType.SEA: 0,
    MapType.REEF: 1,
    MapType.ROAD_HORT: 0,
    MapType.ROAD_VERT: 0,
    MapType.ROAD_NW: 0,
    MapType.ROAD_NE: 0,
    MapType.ROAD_SE: 0,
    MapType.ROAD_SW: 0,
    MapType.BRIDGE_HORT: 0,
    MapType.BRIDGE_VERT: 0,
}


# Movement costs by unit class and terrain
# Format: [FOOT, BOOTS, TYRES, TREADS, AIR, SEA, LANDER, PIPE]
INF = 99  # Impassable terrain

MOVEMENT_COSTS = {
    MapType.PLAIN: [1, 1, 2, 1, 1, INF, 1, INF],
    MapType.WOOD: [1, 1, 3, 2, 1, INF, 1, INF],
    MapType.MOUNTAIN: [2, 1, INF, INF, 1, INF, 1, INF],
    MapType.CITY: [1, 1, 1, 1, 1, INF, 1, INF],
    MapType.FACTORY: [1, 1, 1, 1, 1, INF, 1, INF],
    MapType.AIRPORT: [1, 1, 1, 1, 1, INF, 1, INF],
    MapType.PORT: [1, 1, 1, 1, 1, INF, 1, INF],
    MapType.BASE_TOWER_0: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.BASE_TOWER_1: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.BASE_TOWER_2: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.BASE_TOWER_3: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.BASE_TOWER_4: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.COM_TOWER: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.ROAD_HORT: [1, 1, 1, 1, 1, INF, 1, INF],
    MapType.ROAD_VERT: [1, 1, 1, 1, 1, INF, 1, INF],
    MapType.ROAD_NW: [1, 1, 1, 1, 1, INF, 1, INF],
    MapType.ROAD_NE: [1, 1, 1, 1, 1, INF, 1, INF],
    MapType.ROAD_SE: [1, 1, 1, 1, 1, INF, 1, INF],
    MapType.ROAD_SW: [1, 1, 1, 1, 1, INF, 1, INF],
    MapType.SEA: [INF, INF, INF, INF, 1, 1, 1, INF],
    MapType.REEF: [INF, INF, INF, INF, 1, 2, 2, INF],
    MapType.BRIDGE_HORT: [1, 1, 1, 1, 1, 1, 1, INF],
    MapType.BRIDGE_VERT: [1, 1, 1, 1, 1, 1, 1, INF],
}


def get_movement_cost(unit_class: UnitClass, terrain: MapType) -> int:
    """Get movement cost for unit class on terrain"""
    class_map = {
        UnitClass.FOOT: 0,
        UnitClass.BOOTS: 1,
        UnitClass.TYRES: 2,
        UnitClass.TREADS: 3,
        UnitClass.AIR: 4,
        UnitClass.SEA: 5,
        UnitClass.LANDER: 6,
        UnitClass.PIPE: 7
    }
    
    costs = MOVEMENT_COSTS.get(terrain, [INF] * 8)
    idx = class_map.get(unit_class, 0)
    return costs[idx]
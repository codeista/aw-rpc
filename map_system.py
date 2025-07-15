"""
Consolidated map system for AW-RPC game.
Contains all map-related functionality including types, data, and utilities.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class Army(Enum):
    """Army colors/factions."""
    RED = 0
    BLUE = 1
    GREEN = 2
    YELLOW = 3
    GREY = 4


class MapType(Enum):
    """All terrain types in the game."""
    PLAIN = 0
    WOOD = 100
    ROAD_HORT = 200
    ROAD_VERT = 201
    ROAD_NW = 202
    ROAD_NE = 203
    ROAD_SE = 204
    ROAD_SW = 205
    SWNRoad = 206
    NESRoad = 207
    WNERoad = 208
    ESWRoad = 209
    CRoad = 210
    RIVER_HORT = 300
    RIVER_VERT = 301
    RIVER_NW = 302
    RIVER_NE = 303
    RIVER_SE = 304
    RIVER_SW = 305
    SWNRiver = 306
    NESRiver = 307
    WNERiver = 308
    ESWRiver = 309
    BEACH_N = 400
    BEACH_E = 401
    BEACH_S = 402
    BEACH_W = 403
    BEACH_NW = 404
    BEACH_NE = 405
    BEACH_SE = 406
    BEACH_SW = 407
    BEACH_END_N = 408
    BEACH_END_E = 409
    BEACH_END_S = 410
    BEACH_END_W = 411
    MOUNTAIN = 500
    PIPE_HORT = 600
    PIPE_VERT = 601
    PIPE_END_NW = 602
    PIPE_END_NE = 603
    PIPE_END_SE = 604
    PIPE_END_SW = 605
    PIPE_END_N = 606
    PIPE_END_E = 607
    PIPE_END_S = 608
    PIPE_END_W = 609
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
    LAB = 710
    MISSILE_SILO = 711
    EMPTY_SILO = 712
    SEA = 800
    HBridge = 900
    VBridge = 901
    REEF = 1001


@dataclass
class MapTile:
    """Individual map tile with terrain and ownership."""
    type: MapType
    army: Optional[Army] = None

    def ground_repairs(self) -> bool:
        """Returns true if terrain repairs ground units."""
        return self.type in {
            MapType.CITY, MapType.FACTORY,
            MapType.BASE_TOWER_0, MapType.BASE_TOWER_1,
            MapType.BASE_TOWER_2, MapType.BASE_TOWER_3,
            MapType.BASE_TOWER_4
        }

    def air_repairs(self) -> bool:
        """Returns true if terrain repairs air units."""
        return self.type in {MapType.AIRPORT}

    def sea_repairs(self) -> bool:
        """Returns true if terrain repairs sea units."""
        return self.type in {MapType.PORT}

    def is_capturable(self) -> bool:
        """Returns true if terrain can be captured."""
        return self.type in {
            MapType.CITY, MapType.FACTORY,
            MapType.BASE_TOWER_0, MapType.BASE_TOWER_1,
            MapType.BASE_TOWER_2, MapType.BASE_TOWER_3,
            MapType.COM_TOWER, MapType.PORT, MapType.AIRPORT,
            MapType.LAB, MapType.MISSILE_SILO
        }

    def is_hq(self) -> bool:
        """Returns true if terrain is a HQ."""
        return self.type in {
            MapType.BASE_TOWER_0, MapType.BASE_TOWER_1,
            MapType.BASE_TOWER_2, MapType.BASE_TOWER_3
        }


@dataclass
class Map:
    """Complete map with dimensions, tiles, and turn order."""
    width: int
    height: int
    tiles: List[MapTile]
    turn_order: List[Army]
    name: str = "Unnamed Map"
    description: str = ""

    @classmethod
    def parse(cls, map_data: str, name: str = "Parsed Map") -> 'Map':
        """
        Parse map from string format.
        
        Expected format:
        First line: comma-separated army names (e.g., "RED,BLUE")
        Following lines: comma-separated terrain types with optional army ownership
        
        Args:
            map_data: String representation of the map
            name: Name for the map
            
        Returns:
            Parsed Map object
            
        Raises:
            ValueError: If map format is invalid
        """
        width = 0
        height = 0
        turn_order = []
        tiles = []
        row_count = 0
        
        for line in map_data.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if row_count == 0:
                # First line contains turn order
                for army_name in line.split(','):
                    army_name = army_name.strip()
                    try:
                        turn_order.append(Army[army_name])
                    except KeyError:
                        raise ValueError(f"Invalid army name: {army_name}")
            else:
                # Map data lines
                col_count = 0
                for cell in line.split(','):
                    cell = cell.strip()
                    tile_type = None
                    multiplier = 1
                    army = None
                    
                    # Parse cell format: TYPE*multiplier or TYPE:ARMY
                    if '*' in cell:
                        type_str, mult_str = cell.split('*', 1)
                        multiplier = int(mult_str)
                    elif ':' in cell:
                        type_str, army_str = cell.split(':', 1)
                        army = Army[army_str.strip()]
                    else:
                        type_str = cell
                    
                    try:
                        tile_type = MapType[type_str.strip()]
                    except KeyError:
                        raise ValueError(f"Invalid terrain type: {type_str}")
                    
                    # Add tiles with multiplier
                    for _ in range(multiplier):
                        tile = MapTile(tile_type, army)
                        tiles.append(tile)
                        col_count += 1
                
                if row_count == 1:
                    width = col_count
                elif width != col_count:
                    raise ValueError(f"Row {row_count} has {col_count} columns, expected {width}")
                height += 1
            
            row_count += 1
        
        return cls(width, height, tiles, turn_order, name)

    def get_tile(self, x: int, y: int) -> Optional[MapTile]:
        """Get tile at coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[x + y * self.width]
        return None

    def set_tile(self, x: int, y: int, tile: MapTile) -> bool:
        """Set tile at coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[x + y * self.width] = tile
            return True
        return False

    def to_string(self) -> str:
        """Convert map back to string format."""
        lines = []
        
        # Turn order line
        turn_names = [army.name for army in self.turn_order]
        lines.append(','.join(turn_names))
        
        # Map data lines
        for y in range(self.height):
            row = []
            for x in range(self.width):
                tile = self.get_tile(x, y)
                if tile:
                    cell = tile.type.name
                    if tile.army:
                        cell += f":{tile.army.name}"
                    row.append(cell)
            lines.append(','.join(row))
        
        return '\n'.join(lines)


# Terrain defense values (originally terrain_star in mapping.py)
TERRAIN_DEFENSE = {
    MapType.PLAIN: 1,
    MapType.WOOD: 2,
    MapType.ROAD_HORT: 0,
    MapType.ROAD_VERT: 0,
    MapType.ROAD_NW: 0,
    MapType.ROAD_NE: 0,
    MapType.ROAD_SE: 0,
    MapType.ROAD_SW: 0,
    MapType.CRoad: 0,
    MapType.SWNRoad: 0,
    MapType.ESWRoad: 0,
    MapType.WNERoad: 0,
    MapType.NESRoad: 0,
    MapType.ESWRiver: 0,
    MapType.SWNRiver: 0,
    MapType.WNERiver: 0,
    MapType.NESRiver: 0,
    MapType.RIVER_HORT: 0,
    MapType.RIVER_VERT: 0,
    MapType.RIVER_NW: 0,
    MapType.RIVER_NE: 0,
    MapType.RIVER_SE: 0,
    MapType.RIVER_SW: 0,
    MapType.BEACH_N: 0,
    MapType.BEACH_E: 0,
    MapType.BEACH_S: 0,
    MapType.BEACH_W: 0,
    MapType.BEACH_NW: 0,
    MapType.BEACH_NE: 0,
    MapType.BEACH_SE: 0,
    MapType.BEACH_SW: 0,
    MapType.BEACH_END_N: 0,
    MapType.BEACH_END_E: 0,
    MapType.BEACH_END_S: 0,
    MapType.BEACH_END_W: 0,
    MapType.MOUNTAIN: 4,
    MapType.BASE_TOWER_0: 4,
    MapType.BASE_TOWER_1: 4,
    MapType.BASE_TOWER_2: 4,
    MapType.BASE_TOWER_3: 4,
    MapType.BASE_TOWER_4: 4,
    MapType.CITY: 3,
    MapType.FACTORY: 3,
    MapType.AIRPORT: 3,
    MapType.PORT: 3,
    MapType.COM_TOWER: 3,
    MapType.LAB: 3,
    MapType.MISSILE_SILO: 3,
    MapType.EMPTY_SILO: 3,
    MapType.SEA: 0,
    MapType.PIPE_HORT: 0,
    MapType.PIPE_VERT: 0,
    MapType.PIPE_END_NW: 0,
    MapType.PIPE_END_NE: 0,
    MapType.PIPE_END_SE: 0,
    MapType.PIPE_END_SW: 0,
    MapType.PIPE_END_N: 0,
    MapType.PIPE_END_E: 0,
    MapType.PIPE_END_S: 0,
    MapType.PIPE_END_W: 0,
    MapType.REEF: 1,
    MapType.HBridge: 0,
    MapType.VBridge: 0,
}

INF = 99999999

# Movement costs per unit class
# Format: {terrain_type: [BOOTS, TREADS, TYRES, SEA, AIR, LANDER, FOOT, PIPE]}
MOVEMENT_COST = {
    MapType.PLAIN: [1, 1, 2, INF, 1, INF, 1, INF],
    MapType.WOOD: [1, 2, 3, INF, 1, INF, 1, INF],
    MapType.ROAD_HORT: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.CRoad: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.ROAD_VERT: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.ROAD_NW: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.ROAD_NE: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.ROAD_SE: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.ROAD_SW: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.SWNRoad: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.ESWRoad: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.WNERoad: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.NESRoad: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.ESWRiver: [1, INF, INF, INF, 1, INF, 2, INF],
    MapType.SWNRiver: [1, INF, INF, INF, 1, INF, 2, INF],
    MapType.NESRiver: [1, INF, INF, INF, 1, INF, 2, INF],
    MapType.WNERiver: [1, INF, INF, INF, 1, INF, 2, INF],
    MapType.RIVER_HORT: [1, INF, INF, INF, 1, INF, 2, INF],
    MapType.RIVER_VERT: [1, INF, INF, INF, 1, INF, 2, INF],
    MapType.RIVER_NW: [1, INF, INF, INF, 1, INF, 2, INF],
    MapType.RIVER_NE: [1, INF, INF, INF, 1, INF, 2, INF],
    MapType.RIVER_SE: [1, INF, INF, INF, 1, INF, 2, INF],
    MapType.RIVER_SW: [1, INF, INF, INF, 1, INF, 2, INF],
    MapType.BEACH_N: [1, 1, 1, INF, 1, 1, 1, INF],
    MapType.BEACH_E: [1, 1, 1, INF, 1, 1, 1, INF],
    MapType.BEACH_S: [1, 1, 1, INF, 1, 1, 1, INF],
    MapType.BEACH_W: [1, 1, 1, INF, 1, 1, 1, INF],
    MapType.BEACH_NW: [1, 1, 1, INF, 1, 1, 1, INF],
    MapType.BEACH_NE: [1, 1, 1, INF, 1, 1, 1, INF],
    MapType.BEACH_SE: [1, 1, 1, INF, 1, 1, 1, INF],
    MapType.BEACH_SW: [1, 1, 1, INF, 1, 1, 1, INF],
    MapType.BEACH_END_N: [1, 1, 1, INF, 1, 1, 1, INF],
    MapType.BEACH_END_E: [1, 1, 1, INF, 1, 1, 1, INF],
    MapType.BEACH_END_S: [1, 1, 1, INF, 1, 1, 1, INF],
    MapType.BEACH_END_W: [1, 1, 1, INF, 1, 1, 1, INF],
    MapType.MOUNTAIN: [1, INF, INF, INF, 1, INF, 2, INF],
    MapType.BASE_TOWER_0: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.BASE_TOWER_1: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.BASE_TOWER_2: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.BASE_TOWER_3: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.BASE_TOWER_4: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.CITY: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.FACTORY: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.AIRPORT: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.PORT: [1, 1, 1, 1, 1, 1, 1, INF],
    MapType.COM_TOWER: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.LAB: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.MISSILE_SILO: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.EMPTY_SILO: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.SEA: [INF, INF, INF, 1, 1, 1, INF, INF],
    MapType.PIPE_HORT: [INF, INF, INF, INF, INF, INF, INF, 1],
    MapType.PIPE_VERT: [INF, INF, INF, INF, INF, INF, INF, 1],
    MapType.PIPE_END_NW: [INF, INF, INF, INF, INF, INF, INF, 1],
    MapType.PIPE_END_NE: [INF, INF, INF, INF, INF, INF, INF, 1],
    MapType.PIPE_END_SE: [INF, INF, INF, INF, INF, INF, INF, 1],
    MapType.PIPE_END_SW: [INF, INF, INF, INF, INF, INF, INF, 1],
    MapType.PIPE_END_N: [INF, INF, INF, INF, INF, INF, INF, 1],
    MapType.PIPE_END_E: [INF, INF, INF, INF, INF, INF, INF, 1],
    MapType.PIPE_END_S: [INF, INF, INF, INF, INF, INF, INF, 1],
    MapType.PIPE_END_W: [INF, INF, INF, INF, INF, INF, INF, 1],
    MapType.REEF: [INF, INF, INF, 2, 1, INF, INF, INF],
    MapType.HBridge: [1, 1, 1, INF, 1, INF, 1, INF],
    MapType.VBridge: [1, 1, 1, INF, 1, INF, 1, INF],
}


# Unit class name to index mapping for MOVEMENT_COST lookups
UNIT_CLASS_TO_INDEX = {
    'BOOTS': 0,
    'TREADS': 1, 
    'TYRES': 2,
    'SEA': 3,
    'AIR': 4,
    'LANDER': 5,
    'FOOT': 6,
    'PIPE': 7
}


def get_movement_cost_for_unit_on_terrain(unit_type: str, terrain_type: str) -> int:
    """
    Get movement cost for a specific unit type on a specific terrain type.
    
    Args:
        unit_type: Unit type name (e.g., 'INFANTRY', 'TANK', 'BATTLESHIP')
        terrain_type: Terrain type name (e.g., 'PLAIN', 'WOOD', 'SEA')
        
    Returns:
        Movement cost as integer (99999999 means impassable)
        
    Raises:
        ValueError: If unit_type or terrain_type is invalid
    """
    from config import Config
    
    # Load unit configuration to get movement class
    try:
        config = Config()
        unit_config = config.units.get(unit_type)
        if not unit_config:
            raise ValueError(f"Unknown unit type: {unit_type}")
        
        unit_class = unit_config.get('cls', '').upper()
        if unit_class not in UNIT_CLASS_TO_INDEX:
            raise ValueError(f"Unknown unit class: {unit_class} for unit {unit_type}")
        
        class_index = UNIT_CLASS_TO_INDEX[unit_class]
        
    except Exception as e:
        raise ValueError(f"Error getting unit class for {unit_type}: {e}")
    
    # Convert terrain type string to MapType enum
    try:
        terrain_enum = MapType[terrain_type.upper()]
    except KeyError:
        raise ValueError(f"Unknown terrain type: {terrain_type}")
    
    # Look up movement cost
    if terrain_enum not in MOVEMENT_COST:
        raise ValueError(f"No movement cost data for terrain: {terrain_type}")
    
    cost = MOVEMENT_COST[terrain_enum][class_index]
    return cost


class MapRepository:
    """Repository for managing predefined maps."""
    
    def __init__(self):
        self._maps: Dict[str, Map] = {}
        self._load_default_maps()
    
    def _load_default_maps(self):
        """Load all default maps."""
        # Default test map
        self._maps['test'] = Map.parse('''RED,BLUE
PORT:RED,SEA,SEA,SEA,REEF,SEA,SEA,SEA,PORT:BLUE,PLAIN,MOUNTAIN,CITY
SEA,SEA,SEA,SEA,SEA,SEA,SEA,SEA,SEA,PLAIN,WOOD,PLAIN
SEA,SEA,REEF,SEA,SEA,SEA,REEF,SEA,SEA,ROAD_HORT,ROAD_HORT,ROAD_HORT
BEACH_W,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_E,ROAD_VERT,FACTORY:BLUE,ROAD_VERT
FACTORY:RED,ROAD_HORT,ROAD_HORT,CITY,MOUNTAIN,CITY,ROAD_HORT,ROAD_HORT,FACTORY:BLUE,ROAD_VERT,PLAIN,ROAD_VERT
ROAD_VERT,PLAIN,WOOD,PLAIN,BASE_TOWER_1:RED,BASE_TOWER_1:BLUE,PLAIN,WOOD,ROAD_VERT,ROAD_VERT,MOUNTAIN,ROAD_VERT
ROAD_VERT,MOUNTAIN,CITY,WOOD,PLAIN,PLAIN,WOOD,CITY,ROAD_VERT,ROAD_VERT,WOOD,ROAD_VERT
AIRPORT:RED,ROAD_HORT,ROAD_HORT,ROAD_HORT,PLAIN,PLAIN,ROAD_HORT,ROAD_HORT,AIRPORT:BLUE,ROAD_SW,ROAD_HORT,ROAD_SE
PLAIN,PLAIN,PLAIN,PLAIN,MOUNTAIN,MOUNTAIN,PLAIN,PLAIN,PLAIN,CITY,PLAIN,CITY
PLAIN,MOUNTAIN,WOOD,PLAIN,CITY,CITY,PLAIN,WOOD,MOUNTAIN,PLAIN,FACTORY:RED,PLAIN''', "Test Map for Combat Testing")

        # Scorpion Operation map
        self._maps['scorpion'] = Map.parse('''RED,BLUE
PLAIN,WOOD,RIVER_VERT,MOUNTAIN,ROAD_VERT,WOOD,PLAIN,PLAIN,CITY,PLAIN,PLAIN,WOOD,PLAIN,MOUNTAIN,RIVER_VERT,MOUNTAIN,PLAIN,CITY,PLAIN,WOOD,ROAD_VERT,PLAIN,PLAIN,CITY,MOUNTAIN
MOUNTAIN,FACTORY,RIVER_VERT,MOUNTAIN,ROAD_SW,ROAD_HORT,ROAD_NE,WOOD,PLAIN,WOOD,PLAIN,PLAIN,AIRPORT,WOOD,HBridge,FACTORY:BLUE,ROAD_NW,ROAD_SE,PLAIN,PLAIN,CITY,PLAIN,WOOD,ROAD_VERT,PLAIN
WOOD,PLAIN,RIVER_SW,RIVER_NW,WOOD,PLAIN,ROAD_VERT,WOOD,MOUNTAIN,PLAIN,BASE_TOWER_1:BLUE,PLAIN,PLAIN,RIVER_NE,RIVER_SE,ROAD_NW,ROAD_SE,WOOD,PLAIN,PLAIN,ROAD_VERT,WOOD,MOUNTAIN,ROAD_VERT,PLAIN
CITY,PLAIN,MOUNTAIN,RIVER_VERT,PLAIN,PLAIN,FACTORY:BLUE,PLAIN,MOUNTAIN,PLAIN,BEACH_NE,BEACH_NW,WOOD,RIVER_VERT,PLAIN,ROAD_VERT,PLAIN,MOUNTAIN,PLAIN,MOUNTAIN,ROAD_SW,ROAD_HORT,ROAD_HORT,ROAD_SE,WOOD
PLAIN,ROAD_NW,ROAD_HORT,HBridge,CITY,ROAD_HORT,ROAD_SE,PLAIN,CITY,MOUNTAIN,BEACH_SE,BEACH_SW,MOUNTAIN,CITY,PLAIN,CITY,MOUNTAIN,ROAD_NW,ROAD_HORT,CITY,MOUNTAIN,PLAIN,PLAIN,PLAIN,CITY
WOOD,ROAD_VERT,PLAIN,RIVER_VERT,WOOD,PLAIN,RIVER_NE,RIVER_HORT,RIVER_HORT,MOUNTAIN,CITY,ROAD_NE,WOOD,PLAIN,PLAIN,WOOD,MOUNTAIN,ROAD_VERT,MOUNTAIN,PLAIN,PLAIN,MOUNTAIN,WOOD,ROAD_NW,ROAD_HORT
MOUNTAIN,ROAD_VERT,CITY,RIVER_SW,VBridge,MOUNTAIN,RIVER_SE,CITY,PLAIN,PLAIN,WOOD,ROAD_SW,ROAD_NE,EMPTY_SILO,PLAIN,PLAIN,PLAIN,ROAD_VERT,PLAIN,MOUNTAIN,PLAIN,MOUNTAIN,PLAIN,ROAD_VERT,PLAIN
PLAIN,ROAD_VERT,PLAIN,MOUNTAIN,PLAIN,MOUNTAIN,PLAIN,ROAD_VERT,PLAIN,PLAIN,PLAIN,EMPTY_SILO,ROAD_SW,ROAD_NE,WOOD,PLAIN,PLAIN,CITY,RIVER_NE,MOUNTAIN,VBridge,RIVER_NW,CITY,ROAD_VERT,MOUNTAIN
ROAD_HORT,ROAD_SE,WOOD,MOUNTAIN,PLAIN,PLAIN,MOUNTAIN,ROAD_VERT,MOUNTAIN,WOOD,PLAIN,PLAIN,WOOD,ROAD_SW,CITY,MOUNTAIN,RIVER_HORT,RIVER_HORT,RIVER_SE,PLAIN,WOOD,RIVER_VERT,PLAIN,ROAD_VERT,WOOD
CITY,PLAIN,PLAIN,PLAIN,MOUNTAIN,CITY,ROAD_HORT,ROAD_SE,MOUNTAIN,CITY,PLAIN,CITY,MOUNTAIN,BEACH_NE,BEACH_NW,MOUNTAIN,CITY,PLAIN,ROAD_NW,ROAD_HORT,CITY,HBridge,ROAD_HORT,ROAD_SE,PLAIN
WOOD,ROAD_NW,ROAD_HORT,ROAD_HORT,ROAD_NE,MOUNTAIN,PLAIN,MOUNTAIN,PLAIN,ROAD_VERT,PLAIN,RIVER_VERT,WOOD,BEACH_SE,BEACH_SW,PLAIN,MOUNTAIN,PLAIN,FACTORY:RED,PLAIN,PLAIN,RIVER_VERT,MOUNTAIN,PLAIN,CITY
PLAIN,ROAD_VERT,MOUNTAIN,PLAIN,ROAD_VERT,PLAIN,PLAIN,WOOD,ROAD_NW,ROAD_SE,RIVER_NE,RIVER_SE,PLAIN,PLAIN,BASE_TOWER_1:RED,PLAIN,MOUNTAIN,WOOD,ROAD_VERT,PLAIN,WOOD,RIVER_SW,RIVER_NW,PLAIN,WOOD
PLAIN,ROAD_VERT,WOOD,PLAIN,CITY,PLAIN,PLAIN,ROAD_NW,ROAD_SE,FACTORY:RED,HBridge,WOOD,AIRPORT,PLAIN,PLAIN,WOOD,PLAIN,WOOD,ROAD_SW,ROAD_HORT,ROAD_NE,MOUNTAIN,RIVER_VERT,FACTORY,MOUNTAIN
MOUNTAIN,CITY,PLAIN,PLAIN,ROAD_VERT,WOOD,PLAIN,CITY,PLAIN,MOUNTAIN,RIVER_VERT,MOUNTAIN,PLAIN,WOOD,PLAIN,PLAIN,CITY,PLAIN,PLAIN,WOOD,ROAD_VERT,MOUNTAIN,RIVER_VERT,WOOD,PLAIN''', "Scorpion Operation")

        # 3-Player Triangle Arena - Enhanced with more cities
        self._maps['triangle'] = Map.parse('''RED,BLUE,GREEN
FACTORY:RED,CITY:RED,PLAIN,CITY:RED,MOUNTAIN,CITY,WOOD,CITY,MOUNTAIN,CITY:BLUE,PLAIN,CITY:BLUE,FACTORY:BLUE
CITY:RED,BASE_TOWER_1:RED,WOOD,PLAIN,CITY,PLAIN,PLAIN,PLAIN,CITY,PLAIN,WOOD,BASE_TOWER_1:BLUE,CITY:BLUE
PLAIN,WOOD,PLAIN,PLAIN,WOOD,MOUNTAIN,CITY,MOUNTAIN,WOOD,PLAIN,PLAIN,WOOD,PLAIN
WOOD,PLAIN,CITY,WOOD,PLAIN,ROAD_NW,ROAD_HORT,ROAD_NE,PLAIN,WOOD,CITY,PLAIN,WOOD
MOUNTAIN,CITY,WOOD,PLAIN,ROAD_NW,ROAD_SE,CITY,ROAD_SW,ROAD_NE,PLAIN,WOOD,CITY,MOUNTAIN
PLAIN,PLAIN,MOUNTAIN,ROAD_NW,ROAD_SE,CITY,WOOD,CITY,ROAD_SW,ROAD_NE,MOUNTAIN,PLAIN,PLAIN
WOOD,PLAIN,PLAIN,ROAD_VERT,CITY,WOOD,MOUNTAIN,WOOD,CITY,ROAD_VERT,PLAIN,PLAIN,WOOD
PLAIN,PLAIN,MOUNTAIN,ROAD_SW,ROAD_NE,CITY,WOOD,CITY,ROAD_NW,ROAD_SE,MOUNTAIN,PLAIN,PLAIN
MOUNTAIN,CITY,WOOD,PLAIN,ROAD_SW,ROAD_NE,CITY,ROAD_NW,ROAD_SE,PLAIN,WOOD,CITY,MOUNTAIN
WOOD,PLAIN,CITY,WOOD,PLAIN,ROAD_SW,ROAD_HORT,ROAD_SE,PLAIN,WOOD,CITY,PLAIN,WOOD
PLAIN,WOOD,PLAIN,PLAIN,WOOD,MOUNTAIN,CITY,MOUNTAIN,WOOD,PLAIN,PLAIN,WOOD,PLAIN
CITY:GREEN,BASE_TOWER_1:GREEN,WOOD,PLAIN,CITY:GREEN,PLAIN,PLAIN,PLAIN,CITY:GREEN,PLAIN,WOOD,CITY:GREEN,CITY:GREEN
FACTORY:GREEN,CITY:GREEN,PLAIN,CITY:GREEN,MOUNTAIN,CITY,WOOD,CITY,MOUNTAIN,CITY:GREEN,PLAIN,CITY:GREEN,FACTORY:GREEN''', "Triangle Arena - 3 Players")

        # 4-Player Cross Battle - Enhanced with more cities
        self._maps['cross'] = Map.parse('''RED,BLUE,GREEN,YELLOW
FACTORY:RED,CITY:RED,CITY:RED,WOOD,MOUNTAIN,CITY,PLAIN,CITY,MOUNTAIN,WOOD,CITY:BLUE,CITY:BLUE,FACTORY:BLUE
CITY:RED,BASE_TOWER_1:RED,WOOD,CITY,PLAIN,PLAIN,CITY,PLAIN,PLAIN,CITY,WOOD,BASE_TOWER_1:BLUE,CITY:BLUE
CITY:RED,WOOD,PLAIN,PLAIN,CITY:RED,ROAD_NW,ROAD_HORT,ROAD_NE,CITY:BLUE,PLAIN,PLAIN,WOOD,CITY:BLUE
WOOD,CITY:RED,PLAIN,PLAIN,ROAD_NW,ROAD_SE,CITY,ROAD_SW,ROAD_NE,PLAIN,PLAIN,CITY:BLUE,WOOD
MOUNTAIN,PLAIN,CITY:RED,ROAD_NW,ROAD_SE,CITY,WOOD,CITY,ROAD_SW,ROAD_NE,CITY:BLUE,PLAIN,MOUNTAIN
CITY:YELLOW,PLAIN,ROAD_NW,ROAD_SE,CITY,WOOD,MOUNTAIN,WOOD,CITY,ROAD_SW,ROAD_NE,PLAIN,CITY:GREEN
PLAIN,CITY:YELLOW,ROAD_VERT,CITY,WOOD,MOUNTAIN,AIRPORT,MOUNTAIN,WOOD,CITY,ROAD_VERT,CITY:GREEN,PLAIN
CITY:YELLOW,PLAIN,ROAD_SW,ROAD_NE,CITY,WOOD,MOUNTAIN,WOOD,CITY,ROAD_NW,ROAD_SE,PLAIN,CITY:GREEN
MOUNTAIN,PLAIN,CITY:YELLOW,ROAD_SW,ROAD_NE,CITY,WOOD,CITY,ROAD_NW,ROAD_SE,CITY:GREEN,PLAIN,MOUNTAIN
WOOD,CITY:YELLOW,PLAIN,PLAIN,ROAD_SW,ROAD_NE,CITY,ROAD_NW,ROAD_SE,PLAIN,PLAIN,CITY:GREEN,WOOD
CITY:YELLOW,WOOD,PLAIN,PLAIN,CITY:YELLOW,ROAD_SW,ROAD_HORT,ROAD_SE,CITY:GREEN,PLAIN,PLAIN,WOOD,CITY:GREEN
CITY:YELLOW,BASE_TOWER_1:YELLOW,WOOD,CITY:YELLOW,PLAIN,PLAIN,CITY,PLAIN,PLAIN,CITY:GREEN,WOOD,BASE_TOWER_1:GREEN,CITY:GREEN
FACTORY:YELLOW,CITY:YELLOW,CITY:YELLOW,WOOD,MOUNTAIN,CITY,PLAIN,CITY,MOUNTAIN,WOOD,CITY:GREEN,CITY:GREEN,FACTORY:GREEN''', "Cross Battle - 4 Players")

        # 5-Player Pentagon Chaos - Enhanced with balanced starting positions
        self._maps['pentagon'] = Map.parse('''RED,BLUE,GREEN,YELLOW,GREY
FACTORY:RED,CITY:RED,CITY:RED,WOOD,MOUNTAIN,WOOD,CITY,WOOD,MOUNTAIN,WOOD,CITY:BLUE,CITY:BLUE,FACTORY:BLUE
CITY:RED,BASE_TOWER_1:RED,WOOD,CITY:RED,PLAIN,PLAIN,CITY,PLAIN,PLAIN,CITY:BLUE,WOOD,BASE_TOWER_1:BLUE,CITY:BLUE
CITY:RED,WOOD,PLAIN,PLAIN,WOOD,ROAD_NW,ROAD_HORT,ROAD_NE,WOOD,PLAIN,PLAIN,WOOD,CITY:BLUE
WOOD,CITY:RED,PLAIN,ROAD_NW,ROAD_SE,CITY,AIRPORT,CITY,ROAD_SW,ROAD_NE,PLAIN,CITY:BLUE,WOOD
MOUNTAIN,PLAIN,WOOD,ROAD_VERT,CITY,WOOD,CITY,WOOD,CITY,ROAD_VERT,WOOD,PLAIN,MOUNTAIN
WOOD,PLAIN,ROAD_NW,ROAD_SE,WOOD,CITY,MOUNTAIN,CITY,WOOD,ROAD_SW,ROAD_NE,PLAIN,WOOD
CITY:GREY,CITY:YELLOW,ROAD_VERT,AIRPORT,CITY,MOUNTAIN,COM_TOWER,MOUNTAIN,CITY,AIRPORT,ROAD_VERT,CITY:GREEN,CITY:GREEN
WOOD,PLAIN,ROAD_SW,ROAD_NE,WOOD,CITY,MOUNTAIN,CITY,WOOD,ROAD_NW,ROAD_SE,PLAIN,WOOD
MOUNTAIN,PLAIN,WOOD,ROAD_VERT,CITY,WOOD,CITY,WOOD,CITY,ROAD_VERT,WOOD,PLAIN,MOUNTAIN
WOOD,CITY:GREY,PLAIN,ROAD_SW,ROAD_NE,CITY,AIRPORT,CITY,ROAD_NW,ROAD_SE,PLAIN,CITY:GREEN,WOOD
CITY:GREY,WOOD,PLAIN,PLAIN,WOOD,ROAD_SW,ROAD_HORT,ROAD_SE,WOOD,PLAIN,PLAIN,WOOD,CITY:GREEN
CITY:GREY,BASE_TOWER_1:GREY,WOOD,CITY:GREY,PLAIN,PLAIN,CITY,PLAIN,PLAIN,CITY:GREEN,WOOD,BASE_TOWER_1:GREEN,CITY:GREEN
FACTORY:GREY,CITY:GREY,CITY:GREY,WOOD,MOUNTAIN,WOOD,CITY,WOOD,MOUNTAIN,WOOD,CITY:GREEN,CITY:GREEN,FACTORY:GREEN
PLAIN,PLAIN,PLAIN,CITY:YELLOW,CITY:YELLOW,CITY:YELLOW,BASE_TOWER_1:YELLOW,CITY:YELLOW,CITY:YELLOW,CITY:YELLOW,PLAIN,PLAIN,PLAIN
PLAIN,PLAIN,PLAIN,PLAIN,WOOD,FACTORY:YELLOW,AIRPORT:YELLOW,FACTORY:YELLOW,WOOD,PLAIN,PLAIN,PLAIN,PLAIN''', "Pentagon Chaos - 5 Players")

        # Victory Test Maps - GREEN vs YELLOW focused scenarios
        
        # 1. Green vs Yellow Arena - Small map for quick victory tests
        self._maps['green_yellow_arena'] = Map.parse('''GREEN,YELLOW
FACTORY:GREEN,CITY:GREEN,BASE_TOWER_1:GREEN,CITY:GREEN,MOUNTAIN,CITY:YELLOW,BASE_TOWER_1:YELLOW,CITY:YELLOW,FACTORY:YELLOW
CITY:GREEN,PLAIN,WOOD,PLAIN,CITY,PLAIN,WOOD,PLAIN,CITY:YELLOW
PLAIN,WOOD,PLAIN,MOUNTAIN,ROAD_HORT,MOUNTAIN,PLAIN,WOOD,PLAIN
MOUNTAIN,PLAIN,ROAD_VERT,CITY,AIRPORT,CITY,ROAD_VERT,PLAIN,MOUNTAIN
PLAIN,WOOD,PLAIN,MOUNTAIN,ROAD_HORT,MOUNTAIN,PLAIN,WOOD,PLAIN
CITY:GREEN,PLAIN,WOOD,PLAIN,CITY,PLAIN,WOOD,PLAIN,CITY:YELLOW
FACTORY:GREEN,CITY:GREEN,PLAIN,CITY:GREEN,MOUNTAIN,CITY:YELLOW,PLAIN,CITY:YELLOW,FACTORY:YELLOW''', "Green vs Yellow Arena")

        # 2. GREEN vs BLUE Island Battle
        self._maps['green_blue_islands'] = Map.parse('''GREEN,BLUE
FACTORY:GREEN,CITY:GREEN,BASE_TOWER_1:GREEN,CITY:GREEN,SEA,CITY:BLUE,BASE_TOWER_1:BLUE,CITY:BLUE,FACTORY:BLUE
CITY:GREEN,PLAIN,WOOD,BEACH_E,SEA,BEACH_W,WOOD,PLAIN,CITY:BLUE
PLAIN,WOOD,PLAIN,BEACH_E,SEA,BEACH_W,PLAIN,WOOD,PLAIN
BEACH_S,BEACH_SE,BEACH_E,SEA,REEF,SEA,BEACH_W,BEACH_SW,BEACH_S
SEA,SEA,SEA,REEF,CITY,REEF,SEA,SEA,SEA
BEACH_N,BEACH_NE,BEACH_E,SEA,REEF,SEA,BEACH_W,BEACH_NW,BEACH_N
PLAIN,WOOD,PLAIN,BEACH_E,SEA,BEACH_W,PLAIN,WOOD,PLAIN
CITY:GREEN,PLAIN,WOOD,BEACH_E,SEA,BEACH_W,WOOD,PLAIN,CITY:BLUE
FACTORY:GREEN,CITY:GREEN,AIRPORT:GREEN,CITY:GREEN,SEA,CITY:BLUE,AIRPORT:BLUE,CITY:BLUE,FACTORY:BLUE''', "Green vs Blue Islands")

        # 3. YELLOW vs GREY Mountain War
        self._maps['yellow_grey_mountains'] = Map.parse('''YELLOW,GREY
FACTORY:YELLOW,CITY:YELLOW,BASE_TOWER_1:YELLOW,CITY:YELLOW,MOUNTAIN,CITY:GREY,BASE_TOWER_1:GREY,CITY:GREY,FACTORY:GREY
CITY:YELLOW,PLAIN,WOOD,MOUNTAIN,CITY,MOUNTAIN,WOOD,PLAIN,CITY:GREY
PLAIN,WOOD,PLAIN,CITY,MOUNTAIN,CITY,PLAIN,WOOD,PLAIN
MOUNTAIN,MOUNTAIN,CITY,WOOD,AIRPORT,WOOD,CITY,MOUNTAIN,MOUNTAIN
CITY,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,CITY
MOUNTAIN,MOUNTAIN,CITY,WOOD,AIRPORT,WOOD,CITY,MOUNTAIN,MOUNTAIN
PLAIN,WOOD,PLAIN,CITY,MOUNTAIN,CITY,PLAIN,WOOD,PLAIN
CITY:YELLOW,PLAIN,WOOD,MOUNTAIN,CITY,MOUNTAIN,WOOD,PLAIN,CITY:GREY
FACTORY:YELLOW,CITY:YELLOW,AIRPORT:YELLOW,CITY:YELLOW,MOUNTAIN,CITY:GREY,AIRPORT:GREY,CITY:GREY,FACTORY:GREY''', "Yellow vs Grey Mountains")

        # 4. Small HQ Rush map for GREEN vs YELLOW
        self._maps['green_yellow_hq_rush'] = Map.parse('''GREEN,YELLOW
BASE_TOWER_1:GREEN,CITY:GREEN,PLAIN,WOOD,CITY,WOOD,PLAIN,CITY:YELLOW,BASE_TOWER_1:YELLOW
CITY:GREEN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,CITY:YELLOW
PLAIN,PLAIN,WOOD,ROAD_HORT,ROAD_HORT,ROAD_HORT,WOOD,PLAIN,PLAIN
WOOD,PLAIN,ROAD_VERT,CITY,AIRPORT,CITY,ROAD_VERT,PLAIN,WOOD
PLAIN,PLAIN,WOOD,ROAD_HORT,ROAD_HORT,ROAD_HORT,WOOD,PLAIN,PLAIN
CITY:GREEN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,CITY:YELLOW
BASE_TOWER_1:GREEN,CITY:GREEN,PLAIN,WOOD,CITY,WOOD,PLAIN,CITY:YELLOW,BASE_TOWER_1:YELLOW''', "Green vs Yellow HQ Rush")

        # 5. Complex multi-army test map
        self._maps['multi_army_test'] = Map.parse('''GREEN,YELLOW,BLUE,GREY
FACTORY:GREEN,CITY:GREEN,BASE_TOWER_1:GREEN,PLAIN,CITY,PLAIN,BASE_TOWER_1:YELLOW,CITY:YELLOW,FACTORY:YELLOW
CITY:GREEN,PLAIN,WOOD,PLAIN,CITY,PLAIN,WOOD,PLAIN,CITY:YELLOW
PLAIN,WOOD,PLAIN,ROAD_NW,ROAD_HORT,ROAD_NE,PLAIN,WOOD,PLAIN
PLAIN,PLAIN,ROAD_VERT,CITY,AIRPORT,CITY,ROAD_VERT,PLAIN,PLAIN
CITY,CITY,ROAD_SW,ROAD_HORT,CITY,ROAD_HORT,ROAD_SE,CITY,CITY
PLAIN,PLAIN,ROAD_VERT,CITY,AIRPORT,CITY,ROAD_VERT,PLAIN,PLAIN
PLAIN,WOOD,PLAIN,ROAD_SW,ROAD_HORT,ROAD_SE,PLAIN,WOOD,PLAIN
CITY:BLUE,PLAIN,WOOD,PLAIN,CITY,PLAIN,WOOD,PLAIN,CITY:GREY
FACTORY:BLUE,CITY:BLUE,BASE_TOWER_1:BLUE,PLAIN,CITY,PLAIN,BASE_TOWER_1:GREY,CITY:GREY,FACTORY:GREY''', "Multi-Army Test - 4 Colors")

        # 6. Unit Elimination Test (small map with few units)
        self._maps['elimination_test'] = Map.parse('''GREEN,YELLOW
BASE_TOWER_1:GREEN,PLAIN,CITY,PLAIN,BASE_TOWER_1:YELLOW
PLAIN,WOOD,PLAIN,WOOD,PLAIN
CITY,PLAIN,MOUNTAIN,PLAIN,CITY
PLAIN,WOOD,PLAIN,WOOD,PLAIN
FACTORY:GREEN,PLAIN,CITY,PLAIN,FACTORY:YELLOW''', "Elimination Test - Small")


    def get_map(self, map_id: str) -> Optional[Map]:
        """Get map by ID."""
        return self._maps.get(map_id)
    
    def list_maps(self) -> List[str]:
        """List available map IDs."""
        return list(self._maps.keys())
    
    def add_map(self, map_id: str, map_obj: Map):
        """Add a new map to the repository."""
        self._maps[map_id] = map_obj
    
    def remove_map(self, map_id: str) -> bool:
        """Remove a map from the repository."""
        if map_id in self._maps:
            del self._maps[map_id]
            return True
        return False


# Global map repository instance
map_repository = MapRepository()


def get_default_map() -> Map:
    """Get the default map for new games."""
    return map_repository.get_map('test') or Map.parse('''RED,BLUE
PLAIN,PLAIN,PLAIN
PLAIN,CITY,PLAIN
PLAIN,PLAIN,PLAIN''', "Fallback Map")
    
# Function to add pre-deployed units to test map
def add_test_units_to_game(game_manager):
    """Add pre-deployed units to the test map for immediate testing."""
    
    # Naval Units
    test_units = [
        # Naval Combat Zone
        {"type": "BATTLESHIP", "army": "RED", "x": 3, "y": 0},      # Naval power
        {"type": "CRUISER", "army": "BLUE", "x": 5, "y": 0},        # Anti-air naval
        {"type": "SUB", "army": "RED", "x": 1, "y": 1},             # Stealth naval
        {"type": "LANDER", "army": "BLUE", "x": 7, "y": 1},         # Naval transport
        {"type": "CRUISER", "army": "RED", "x": 4, "y": 2},         # Naval engagement
        {"type": "BATTLESHIP", "army": "BLUE", "x": 5, "y": 2},     # Counter naval
        
        # Land Combat Zone
        {"type": "INFANTRY", "army": "RED", "x": 1, "y": 4},        # Basic infantry
        {"type": "MECH", "army": "BLUE", "x": 7, "y": 4},           # Mountain specialist
        {"type": "TANK", "army": "RED", "x": 3, "y": 5},            # Heavy armor
        {"type": "RECON", "army": "BLUE", "x": 6, "y": 5},          # Fast recon
        {"type": "MECH", "army": "RED", "x": 1, "y": 6},            # Mountain defense
        {"type": "TANK", "army": "BLUE", "x": 8, "y": 6},           # Mobile armor
        
        # Air Operations
        {"type": "FIGHTER", "army": "RED", "x": 1, "y": 7},         # Air superiority
        {"type": "FIGHTER", "army": "BLUE", "x": 8, "y": 8},        # Air combat
        {"type": "BOMBER", "army": "RED", "x": 1, "y": 8},          # Ground attack
        
        # Artillery Support
        {"type": "ARTILLERY", "army": "RED", "x": 3, "y": 9},       # Indirect fire
        {"type": "ROCKET", "army": "BLUE", "x": 6, "y": 9},         # Long range
    ]
    
    # Create each unit
    for unit_data in test_units:
        try:
            game_manager.create_unit(
                army=unit_data["army"],
                unit_type=unit_data["type"],
                x=unit_data["x"],
                y=unit_data["y"]
            )
        except Exception as e:
            print(f"Failed to create {unit_data['type']} at ({unit_data['x']},{unit_data['y']}): {e}")
    
    return len(test_units)

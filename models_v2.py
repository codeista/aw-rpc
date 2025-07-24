"""
Player-based models for the clean API v2 system.
No more hardcoded colors - players are assigned colors at game creation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class SpriteColor(Enum):
    """Available sprite colors in our tileset"""
    RED = 'red'
    BLUE = 'blue'
    GREEN = 'green'
    YELLOW = 'yellow'
    GREY = 'grey'
    NEUTRAL = 'neutral'
    FOG = 'fog'


class TerrainType(Enum):
    """Terrain types"""
    PLAIN = 'plain'
    ROAD = 'road'
    WOOD = 'wood'
    MOUNTAIN = 'mountain'
    RIVER = 'river'
    SEA = 'sea'
    BEACH = 'beach'
    REEF = 'reef'
    BRIDGE = 'bridge'
    PIPE = 'pipe'
    MISSILE_SILO = 'missile_silo'


class BuildingType(Enum):
    """Building types"""
    CITY = 'city'
    FACTORY = 'factory'
    AIRPORT = 'airport'
    PORT = 'port'
    HQ = 'hq'
    COM_TOWER = 'com_tower'
    LAB = 'lab'


class UnitType(Enum):
    """All unit types"""
    # Infantry
    INFANTRY = 'infantry'
    MECH = 'mech'
    
    # Vehicles
    RECON = 'recon'
    TANK = 'tank'
    MD_TANK = 'md_tank'
    NEOTANK = 'neotank'
    MEGATANK = 'megatank'
    APC = 'apc'
    ARTILLERY = 'artillery'
    ROCKET = 'rocket'
    AA = 'aa'
    MISSILE = 'missile'
    
    # Air
    FIGHTER = 'fighter'
    BOMBER = 'bomber'
    BCOPTER = 'bcopter'
    TCOPTER = 'tcopter'
    STEALTH = 'stealth'
    BLACK_BOMB = 'black_bomb'
    
    # Naval
    BATTLESHIP = 'battleship'
    CRUISER = 'cruiser'
    LANDER = 'lander'
    SUB = 'sub'
    CARRIER = 'carrier'
    BLACK_BOAT = 'black_boat'


@dataclass
class Player:
    """Player information"""
    id: str  # 'player1', 'player2', etc.
    name: str  # Display name
    color: SpriteColor  # Assigned color
    funds: int = 0
    team: Optional[str] = None  # For team games
    
    
@dataclass
class Terrain:
    """Terrain tile data"""
    type: TerrainType
    defense: int = 0  # Defense bonus (0-4 stars)
    movement_cost: Dict[str, int] = field(default_factory=dict)  # Per movement type
    

@dataclass
class Building:
    """Building data"""
    type: BuildingType
    owner_id: Optional[str] = None  # None = neutral
    capture_hp: int = 20
    
    @property
    def is_production(self) -> bool:
        return self.type in [BuildingType.FACTORY, BuildingType.AIRPORT, BuildingType.PORT]
        
    @property
    def is_capturable(self) -> bool:
        return self.type != BuildingType.MISSILE_SILO


@dataclass
class Unit:
    """Unit data"""
    id: str  # Unique unit ID
    type: UnitType
    owner_id: str  # Player ID who owns this unit
    hp: int = 100
    fuel: int = 99
    ammo: int = 99
    has_moved: bool = False
    has_acted: bool = False  # Attacked, captured, etc.
    cargo: List[str] = field(default_factory=list)  # Unit IDs being transported
    
    # Unit stats (normally would load from config)
    movement: int = 3
    vision: int = 2
    range_min: int = 1
    range_max: int = 1
    

@dataclass 
class Tile:
    """Complete tile information"""
    x: int
    y: int
    terrain: Terrain
    building: Optional[Building] = None
    unit: Optional[Unit] = None
    
    # Calculated fields for current selection
    is_valid_move: bool = False
    is_valid_attack: bool = False
    is_valid_load: bool = False
    move_cost: Optional[int] = None
    damage_preview: Optional[int] = None


@dataclass
class GameAction:
    """Represents a valid action from current position"""
    action_type: str  # 'move', 'attack', 'capture', 'load', etc.
    target_x: int
    target_y: int
    details: Dict = field(default_factory=dict)


@dataclass
class GameStateV2:
    """Complete game state"""
    game_id: str
    players: Dict[str, Player]  # player_id -> Player
    current_player_id: str
    active_unit_pos: Optional[Tuple[int, int]] = None  # Unit that moved but hasn't finished
    selected_pos: Optional[Tuple[int, int]] = None  # Currently selected tile
    day: int = 1
    phase: str = 'main'  # 'main', 'combat', 'game_over'
    turn_order: List[str] = field(default_factory=list)  # Player IDs in turn order
    winner_id: Optional[str] = None
    
    # Board dimensions
    map_width: int = 20
    map_height: int = 15
    
    # Cached board state (would be in database)
    tiles: Dict[Tuple[int, int], Tile] = field(default_factory=dict)
    units: Dict[str, Unit] = field(default_factory=dict)  # unit_id -> Unit
    
    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        return self.tiles.get((x, y))
        
    def get_unit_at(self, x: int, y: int) -> Optional[Unit]:
        tile = self.get_tile(x, y)
        return tile.unit if tile else None
        
    def get_player_color(self, player_id: str) -> str:
        """Get the color name for sprite mapping"""
        player = self.players.get(player_id)
        return player.color.value if player else 'neutral'
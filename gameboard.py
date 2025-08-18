"""
GameBoard V2 - Color-agnostic game board with backward compatibility
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from core.map_system import Army, MapTile, Map
from core.player_system import PlayerManager
from core.unit import Unit
import jsons


@dataclass
class GameTile:
    """Tile in the game grid with unit and map information"""
    x: int
    y: int
    unit: Optional[Unit] = None
    mapTile: Optional[MapTile] = None
    can_be_moved_to: bool = False
    can_be_attacked: bool = False
    capture_hp: int = 20

@dataclass
class GameBoard:
    """Game board that works with PlayerManager system"""
    
    # Core game state
    grid: List[Any] = field(default_factory=list)
    width: int = 0
    height: int = 0
    
    # Player management
    player_manager: Optional[PlayerManager] = None
    
    # Army state - now player-index based internally
    player_funds: Dict[int, int] = field(default_factory=dict)
    player_properties: Dict[int, int] = field(default_factory=dict)
    player_troops: Dict[int, int] = field(default_factory=dict)
    
    # Turn management
    turn_order: List[int] = field(default_factory=list)  # Player indices
    current_player: int = 0
    days: int = 1
    game_active: bool = True
    winner: Optional[str] = None  # Player name who won
    victory_type: Optional[str] = None  # How they won (e.g. "HQ Capture", "Elimination")
    
    # TEMPORARY: Keep these until Manager.py is updated
    army_funds: Dict[Army, int] = field(default_factory=dict)
    army_properties: Dict[Army, int] = field(default_factory=dict)
    army_troops: Dict[Army, int] = field(default_factory=dict)
    
    # Reference to the original map
    map: Optional[Map] = None
    
    # Selection state
    selected: Optional[Any] = None  # Selected tile
    
    def create_from_tiles(self, tiles: List[MapTile], width: int, height: int) -> None:
        """Create grid from map tiles"""
        self.width = width
        self.height = height
        self.grid = []
        
        for i, map_tile in enumerate(tiles):
            x = i % width
            y = i // width
            tile = GameTile(x, y, mapTile=map_tile)
            self.grid.append(tile)
        
    def initialize_from_player_manager(self, player_manager: PlayerManager):
        """Initialize board with player configuration"""
        self.player_manager = player_manager
        
        # Setup player data
        for player in player_manager.get_players():
            # Initialize player state
            self.player_funds[player.id] = 0
            self.player_properties[player.id] = 0
            self.player_troops[player.id] = 0
            
            # TEMPORARY: Also initialize army dicts for compatibility
            army = self.get_army_for_player(player.id)
            if army:
                self.army_funds[army] = 0
                self.army_properties[army] = 0
                self.army_troops[army] = 0
                
        # Setup turn order
        self.turn_order = list(range(player_manager.get_player_count()))
        self.current_player = 0
        
    # TEMPORARY compatibility properties until RPC methods are updated
    @property
    def red_funds(self) -> int:
        """Temporary compatibility - returns player 0 funds"""
        return self.player_funds.get(0, 0)
        
    @property
    def blue_funds(self) -> int:
        """Temporary compatibility - returns player 1 funds"""
        return self.player_funds.get(1, 0)
        
    @property
    def current_turn(self) -> Optional[Army]:
        """Temporary compatibility - returns Army enum for current player"""
        # Map player 0->RED, 1->BLUE, etc
        player_to_army_map = {0: Army.RED, 1: Army.BLUE, 2: Army.GREEN, 3: Army.YELLOW}
        return player_to_army_map.get(self.current_player)
        
    def get_army_for_player(self, player_id: int) -> Optional[Army]:
        """TEMPORARY compatibility until all code is updated"""
        # Map player 0->RED, 1->BLUE, etc
        player_to_army_map = {0: Army.RED, 1: Army.BLUE, 2: Army.GREEN, 3: Army.YELLOW}
        return player_to_army_map.get(player_id)
        
    def get_player_for_army(self, army: Army) -> Optional[int]:
        """TEMPORARY compatibility until all code is updated"""
        # Map RED->0, BLUE->1, etc
        army_to_player_map = {Army.RED: 0, Army.BLUE: 1, Army.GREEN: 2, Army.YELLOW: 3}
        return army_to_player_map.get(army)
    
    def get_player_sprite_color(self, player_id: int) -> Optional[str]:
        """Get the sprite color for a player"""
        if self.player_manager and player_id in self.player_manager.players:
            player = self.player_manager.players[player_id]
            return player.sprite_color.value
        else:
            # Fallback to simple mapping
            player_to_color = {0: "RED", 1: "BLUE", 2: "GREEN", 3: "YELLOW"}
            return player_to_color.get(player_id, "RED")
        
    def update_player_funds(self, player_id: int, amount: int):
        """Update funds for a player"""
        if player_id in self.player_funds:
            self.player_funds[player_id] += amount
            # TEMPORARY: Sync with army funds
            army = self.get_army_for_player(player_id)
            if army:
                self.army_funds[army] += amount
                
    def update_player_properties(self, player_id: int, delta: int):
        """Update property count for a player"""
        if player_id in self.player_properties:
            self.player_properties[player_id] += delta
            # TEMPORARY: Sync with army properties
            army = self.get_army_for_player(player_id)
            if army:
                self.army_properties[army] += delta
                
    def update_player_troops(self, player_id: int, delta: int):
        """Update troop count for a player"""
        if player_id in self.player_troops:
            self.player_troops[player_id] += delta
            # TEMPORARY: Sync with army troops
            army = self.get_army_for_player(player_id)
            if army:
                self.army_troops[army] += delta
                
    def get_next_player(self) -> int:
        """Get next player in turn order"""
        if not self.turn_order:
            return 0
            
        current_idx = self.turn_order.index(self.current_player)
        next_idx = (current_idx + 1) % len(self.turn_order)
        return self.turn_order[next_idx]
        
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        # Serialize grid with proper unit/tile data
        grid_data = []
        for tile in self.grid:
            tile_dict = {
                'x': tile.x,
                'y': tile.y,
                'mapTile': jsons.dumps(tile.mapTile) if tile.mapTile else None,
                'unit': jsons.dumps(tile.unit) if tile.unit else None,
                'can_be_moved_to': tile.can_be_moved_to,
                'can_be_attacked': tile.can_be_attacked,
                'capture_hp': tile.capture_hp
            }
            grid_data.append(tile_dict)
            
        return {
            'width': self.width,
            'height': self.height,
            'grid': grid_data,  # CRITICAL: Include grid for proper serialization
            'days': self.days,
            'current_player': self.current_player,
            'player_funds': self.player_funds,
            'player_properties': self.player_properties,
            'player_troops': self.player_troops,
            'turn_order': self.turn_order,
            'game_active': self.game_active,
            'winner': self.winner,
            'victory_type': self.victory_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict, player_manager: Optional[PlayerManager] = None) -> 'GameBoard':
        """Create GameBoard from dictionary (for deserialization)"""
        board = cls(player_manager=player_manager)
        
        # Set basic fields
        board.width = data.get('width', 0)
        board.height = data.get('height', 0)
        board.days = data.get('days', 1)
        board.current_player = data.get('current_player', 0)
        # Convert string keys to int for player data
        board.player_funds = {int(k): v for k, v in data.get('player_funds', {}).items()}
        board.player_properties = {int(k): v for k, v in data.get('player_properties', {}).items()}
        board.player_troops = {int(k): v for k, v in data.get('player_troops', {}).items()}
        board.turn_order = data.get('turn_order', [])
        
        # Reconstruct grid if present
        if 'grid' in data:
            board.grid = []
            for tile_data in data['grid']:
                tile = GameTile(
                    x=tile_data['x'],
                    y=tile_data['y'],
                    can_be_moved_to=tile_data.get('can_be_moved_to', False),
                    can_be_attacked=tile_data.get('can_be_attacked', False),
                    capture_hp=tile_data.get('capture_hp', 20)
                )
                
                # Deserialize mapTile and unit if present
                if tile_data.get('mapTile'):
                    tile.mapTile = jsons.loads(tile_data['mapTile'], MapTile)
                if tile_data.get('unit'):
                    tile.unit = jsons.loads(tile_data['unit'], Unit)
                    
                board.grid.append(tile)
        
        # Set game state fields
        board.game_active = data.get('game_active', True)
        board.winner = data.get('winner')
        board.victory_type = data.get('victory_type')
        
        return board
    
    # Tile Ownership Helper Methods
    def is_tile_owned_by_player(self, tile: GameTile, player_id: int) -> bool:
        """Check if a tile is owned by a specific player"""
        if not tile.mapTile:
            return False
            
        # Primary check: use player_id if available
        if hasattr(tile.mapTile, 'player_id') and tile.mapTile.player_id is not None:
            return tile.mapTile.player_id == player_id
            
        # Fallback: convert army to player_id
        if hasattr(tile.mapTile, 'army') and tile.mapTile.army is not None:
            converted_player_id = self.get_player_for_army(tile.mapTile.army)
            return converted_player_id == player_id
            
        return False
        
    def set_tile_owner(self, tile: GameTile, player_id: Optional[int]) -> None:
        """Set tile ownership for a player (handles both army and player_id)"""
        if not tile.mapTile:
            return
            
        # Set primary field
        tile.mapTile.player_id = player_id
        
        # Set legacy field for compatibility
        if player_id is not None:
            tile.mapTile.army = self.get_army_for_player(player_id)
        else:
            tile.mapTile.army = None
            
    def get_tile_owner_player_id(self, tile: GameTile) -> Optional[int]:
        """Get the player ID that owns a tile"""
        if not tile.mapTile:
            return None
            
        # Primary check: use player_id if available
        if hasattr(tile.mapTile, 'player_id') and tile.mapTile.player_id is not None:
            return tile.mapTile.player_id
            
        # Fallback: convert army to player_id
        if hasattr(tile.mapTile, 'army') and tile.mapTile.army is not None:
            return self.get_player_for_army(tile.mapTile.army)
            
        return None
        
    def is_tile_neutral(self, tile: GameTile) -> bool:
        """Check if a tile is neutral (unowned)"""
        return self.get_tile_owner_player_id(tile) is None
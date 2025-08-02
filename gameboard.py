"""
GameBoard V2 - Color-agnostic game board with backward compatibility
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from core.map_system import Army, MapTile, Map
from core.player_system import PlayerManager
from core.unit import Unit


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
    
    # Army mapping for backward compatibility
    army_to_player: Dict[Army, int] = field(default_factory=dict)
    player_to_army: Dict[int, Army] = field(default_factory=dict)
    
    # These provide backward compatibility
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
    
    # Legacy fields as properties for backward compatibility
    @property
    def red_funds(self) -> int:
        """Legacy property for RED army funds"""
        player_id = self.army_to_player.get(Army.RED, -1)
        return self.player_funds.get(player_id, 0)
        
    @red_funds.setter
    def red_funds(self, value: int):
        player_id = self.army_to_player.get(Army.RED, -1)
        if player_id >= 0:
            self.player_funds[player_id] = value
            self.army_funds[Army.RED] = value
            
    @property
    def blue_funds(self) -> int:
        """Legacy property for BLUE army funds"""
        player_id = self.army_to_player.get(Army.BLUE, -1)
        return self.player_funds.get(player_id, 0)
        
    @blue_funds.setter
    def blue_funds(self, value: int):
        player_id = self.army_to_player.get(Army.BLUE, -1)
        if player_id >= 0:
            self.player_funds[player_id] = value
            self.army_funds[Army.BLUE] = value
            
    @property
    def total_red_properties(self) -> int:
        """Legacy property for RED army properties"""
        player_id = self.army_to_player.get(Army.RED, -1)
        return self.player_properties.get(player_id, 0)
        
    @total_red_properties.setter
    def total_red_properties(self, value: int):
        """Legacy setter for RED army properties"""
        player_id = self.army_to_player.get(Army.RED, -1)
        if player_id >= 0:
            self.player_properties[player_id] = value
            self.army_properties[Army.RED] = value
        
    @property
    def total_blue_properties(self) -> int:
        """Legacy property for BLUE army properties"""
        player_id = self.army_to_player.get(Army.BLUE, -1)
        return self.player_properties.get(player_id, 0)
        
    @total_blue_properties.setter
    def total_blue_properties(self, value: int):
        """Legacy setter for BLUE army properties"""
        player_id = self.army_to_player.get(Army.BLUE, -1)
        if player_id >= 0:
            self.player_properties[player_id] = value
            self.army_properties[Army.BLUE] = value
        
    @property
    def total_red_troops(self) -> int:
        """Legacy property for RED army troops"""
        player_id = self.army_to_player.get(Army.RED, -1)
        return self.player_troops.get(player_id, 0)
        
    @total_red_troops.setter
    def total_red_troops(self, value: int):
        """Legacy setter for RED army troops"""
        player_id = self.army_to_player.get(Army.RED, -1)
        if player_id >= 0:
            self.player_troops[player_id] = value
            self.army_troops[Army.RED] = value
        
    @property
    def total_blue_troops(self) -> int:
        """Legacy property for BLUE army troops"""
        player_id = self.army_to_player.get(Army.BLUE, -1)
        return self.player_troops.get(player_id, 0)
        
    @total_blue_troops.setter  
    def total_blue_troops(self, value: int):
        """Legacy setter for BLUE army troops"""
        player_id = self.army_to_player.get(Army.BLUE, -1)
        if player_id >= 0:
            self.player_troops[player_id] = value
            self.army_troops[Army.BLUE] = value
        
    @property
    def current_turn(self) -> Optional[Army]:
        """Get current army (for backward compatibility)"""
        return self.player_to_army.get(self.current_player, None)
        
    @current_turn.setter
    def current_turn(self, army: Army):
        """Set current turn by army (for backward compatibility)"""
        player_id = self.army_to_player.get(army, -1)
        if player_id >= 0:
            self.current_player = player_id
        
    def initialize_from_player_manager(self, player_manager: PlayerManager):
        """Initialize board with player configuration"""
        self.player_manager = player_manager
        
        # Clear existing mappings
        self.army_to_player.clear()
        self.player_to_army.clear()
        
        # Setup player data
        for player in player_manager.get_players():
            # Initialize player state
            self.player_funds[player.id] = 0
            self.player_properties[player.id] = 0
            self.player_troops[player.id] = 0
            
            # Create army mapping for backward compatibility
            # Map sprite color to Army enum
            try:
                army = Army[player.sprite_color.value]
                self.army_to_player[army] = player.id
                self.player_to_army[player.id] = army
                
                # Also maintain army-based dicts for compatibility
                self.army_funds[army] = 0
                self.army_properties[army] = 0
                self.army_troops[army] = 0
            except KeyError:
                # Handle case where sprite color doesn't match Army enum
                pass
                
        # Setup turn order
        self.turn_order = list(range(player_manager.get_player_count()))
        self.current_player = 0
        
    def get_army_for_player(self, player_id: int) -> Optional[Army]:
        """Get army enum for a player (for backward compatibility)"""
        return self.player_to_army.get(player_id)
        
    def get_player_for_army(self, army: Army) -> Optional[int]:
        """Get player ID for an army (for backward compatibility)"""
        return self.army_to_player.get(army)
        
    def update_player_funds(self, player_id: int, amount: int):
        """Update funds for a player"""
        if player_id in self.player_funds:
            self.player_funds[player_id] += amount
            
            # Update army funds for backward compatibility
            army = self.player_to_army.get(player_id)
            if army:
                self.army_funds[army] += amount
                
    def update_player_properties(self, player_id: int, delta: int):
        """Update property count for a player"""
        if player_id in self.player_properties:
            self.player_properties[player_id] += delta
            
            # Update army properties for backward compatibility
            army = self.player_to_army.get(player_id)
            if army:
                self.army_properties[army] += delta
                
    def update_player_troops(self, player_id: int, delta: int):
        """Update troop count for a player"""
        if player_id in self.player_troops:
            self.player_troops[player_id] += delta
            
            # Update army troops for backward compatibility
            army = self.player_to_army.get(player_id)
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
        return {
            'width': self.width,
            'height': self.height,
            'days': self.days,
            'current_player': self.current_player,
            'player_funds': self.player_funds,
            'player_properties': self.player_properties,
            'player_troops': self.player_troops,
            'turn_order': self.turn_order,
            # Include legacy fields for backward compatibility
            'red_funds': self.red_funds,
            'blue_funds': self.blue_funds,
            'total_red_properties': self.total_red_properties,
            'total_blue_properties': self.total_blue_properties,
            'total_red_troops': self.total_red_troops,
            'total_blue_troops': self.total_blue_troops,
            'current_turn': self.current_turn.value if self.current_turn else None,
            # Include army dicts for compatibility
            'army_funds': {(army.value if hasattr(army, 'value') else army): funds 
                          for army, funds in self.army_funds.items()},
            'army_properties': {(army.value if hasattr(army, 'value') else army): props 
                               for army, props in self.army_properties.items()},
            'army_troops': {(army.value if hasattr(army, 'value') else army): troops 
                           for army, troops in self.army_troops.items()},
        }
"""
Player System - Decouples player identity from color
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class SpriteColor(str, Enum):
    """Available sprite colors in the game"""
    RED = "RED"
    BLUE = "BLUE"
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    GREY = "GREY"
    
@dataclass
class Player:
    """Represents a player in the game"""
    id: int  # 0-based index
    name: str
    color: str  # Display color (can be any string)
    sprite_color: SpriteColor  # Which sprite set to use
    is_ai: bool = False
    team: Optional[int] = None  # For team games
    
class PlayerManager:
    """Manages player configuration and color mapping"""
    
    def __init__(self):
        self.players: Dict[int, Player] = {}
        self.sprite_mapping: Dict[int, str] = {}
        
    def add_player(self, player_id: int, name: str, color: str, 
                   sprite_color: Optional[SpriteColor] = None,
                   is_ai: bool = False, team: Optional[int] = None) -> Player:
        """Add a player to the game"""
        # Auto-assign sprite color if not specified
        if sprite_color is None:
            available_colors = [c for c in SpriteColor if c.value not in self.sprite_mapping.values()]
            if available_colors:
                sprite_color = available_colors[0]
            else:
                # Reuse colors if we run out
                sprite_color = list(SpriteColor)[player_id % len(SpriteColor)]
                
        player = Player(
            id=player_id,
            name=name,
            color=color,
            sprite_color=sprite_color,
            is_ai=is_ai,
            team=team
        )
        
        self.players[player_id] = player
        self.sprite_mapping[player_id] = sprite_color.value
        return player
        
    def get_player(self, player_id: int) -> Optional[Player]:
        """Get player by ID"""
        return self.players.get(player_id)
        
    def get_sprite_color(self, player_id: int) -> str:
        """Get the sprite color for a player"""
        return self.sprite_mapping.get(player_id, "NEUTRAL")
        
    def get_players(self) -> List[Player]:
        """Get all players"""
        return list(self.players.values())
        
    def get_player_count(self) -> int:
        """Get number of players"""
        return len(self.players)
        
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "players": {
                str(pid): {
                    "id": p.id,
                    "name": p.name,
                    "color": p.color,
                    "sprite_color": p.sprite_color.value,
                    "is_ai": p.is_ai,
                    "team": p.team
                }
                for pid, p in self.players.items()
            },
            "sprite_mapping": {str(k): v for k, v in self.sprite_mapping.items()}
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'PlayerManager':
        """Create from dictionary"""
        manager = cls()
        
        for pid_str, player_data in data.get("players", {}).items():
            pid = int(pid_str)
            manager.add_player(
                player_id=pid,
                name=player_data["name"],
                color=player_data["color"],
                sprite_color=SpriteColor(player_data["sprite_color"]),
                is_ai=player_data.get("is_ai", False),
                team=player_data.get("team")
            )
            
        return manager
        
    @classmethod
    def create_default_2_player(cls) -> 'PlayerManager':
        """Create a default 2-player configuration"""
        manager = cls()
        manager.add_player(0, "Player 1", "Red", SpriteColor.RED)
        manager.add_player(1, "Player 2", "Blue", SpriteColor.BLUE)
        return manager
        
    @classmethod
    def create_default_4_player(cls) -> 'PlayerManager':
        """Create a default 4-player configuration"""
        manager = cls()
        manager.add_player(0, "Player 1", "Red", SpriteColor.RED)
        manager.add_player(1, "Player 2", "Blue", SpriteColor.BLUE)
        manager.add_player(2, "Player 3", "Green", SpriteColor.GREEN)
        manager.add_player(3, "Player 4", "Yellow", SpriteColor.YELLOW)
        return manager
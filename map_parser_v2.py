"""
Map Parser V2 - Supports both legacy color-based and new index-based formats
"""
from typing import List, Tuple, Dict, Optional
from map_system import MapType
from player_system import PlayerManager, SpriteColor
import re

class MapParserV2:
    """Parses map files supporting both legacy and new formats"""
    
    # Legacy color to player index mapping
    LEGACY_COLOR_MAP = {
        "RED": 0,
        "BLUE": 1,
        "GREEN": 2,
        "YELLOW": 3,
        "GREY": 4,
        "NEUTRAL": -1
    }
    
    def __init__(self):
        self.width = 0
        self.height = 0
        self.player_manager: Optional[PlayerManager] = None
        self.tiles: List[List[Tuple[MapType, Optional[int]]]] = []
        
    def parse_file(self, filename: str) -> Tuple[PlayerManager, List[List[Tuple[MapType, Optional[int]]]]]:
        """Parse a map file and return player configuration and tiles"""
        with open(filename, 'r') as f:
            lines = f.readlines()
            
        return self.parse_lines(lines)
        
    def parse_lines(self, lines: List[str]) -> Tuple[PlayerManager, List[List[Tuple[MapType, Optional[int]]]]]:
        """Parse map from lines"""
        # Skip comments and empty lines
        lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
        
        if not lines:
            raise ValueError("Empty map file")
            
        # Parse header
        header = lines[0]
        if header.isdigit():
            # New format: just number of players
            self._parse_new_header(int(header))
        else:
            # Legacy format: color names
            self._parse_legacy_header(header)
            
        # Parse dimensions
        if len(lines) < 2:
            raise ValueError("Missing map dimensions")
            
        dims = lines[1].split(',')
        if len(dims) != 2:
            raise ValueError(f"Invalid dimensions: {lines[1]}")
            
        self.width = int(dims[0])
        self.height = int(dims[1])
        
        # Parse tiles
        if len(lines) < 2 + self.height:
            raise ValueError("Not enough map rows")
            
        self.tiles = []
        for y in range(self.height):
            row = []
            tiles = lines[2 + y].split()
            
            if len(tiles) != self.width:
                raise ValueError(f"Row {y} has {len(tiles)} tiles, expected {self.width}")
                
            for x in range(self.width):
                tile_type, owner = self._parse_tile(tiles[x])
                row.append((tile_type, owner))
                
            self.tiles.append(row)
            
        return self.player_manager, self.tiles
        
    def _parse_new_header(self, player_count: int):
        """Parse new format header (just player count)"""
        self.player_manager = PlayerManager()
        
        # Create default players
        default_colors = [
            ("Red", SpriteColor.RED),
            ("Blue", SpriteColor.BLUE),
            ("Green", SpriteColor.GREEN),
            ("Yellow", SpriteColor.YELLOW),
            ("Grey", SpriteColor.GREY)
        ]
        
        for i in range(player_count):
            if i < len(default_colors):
                name = f"Player {i + 1}"
                color, sprite = default_colors[i]
                self.player_manager.add_player(i, name, color, sprite)
            else:
                # More than 5 players - reuse sprite colors
                name = f"Player {i + 1}"
                color = f"Color{i + 1}"
                sprite = list(SpriteColor)[i % len(SpriteColor)]
                self.player_manager.add_player(i, name, color, sprite)
                
    def _parse_legacy_header(self, header: str):
        """Parse legacy format header (color names)"""
        colors = [c.strip().upper() for c in header.split(',')]
        
        self.player_manager = PlayerManager()
        
        for i, color in enumerate(colors):
            if color not in self.LEGACY_COLOR_MAP:
                raise ValueError(f"Unknown army color: {color}")
                
            # Map legacy colors to sprite colors
            sprite_color = SpriteColor(color) if color != "NEUTRAL" else SpriteColor.GREY
            
            # Create player with legacy color as both display and sprite color
            self.player_manager.add_player(
                player_id=i,
                name=f"{color.title()} Army",
                color=color.title(),
                sprite_color=sprite_color
            )
            
    def _parse_tile(self, tile_str: str) -> Tuple[MapType, Optional[int]]:
        """Parse a single tile string"""
        # Check for ownership indicator
        if ':' in tile_str:
            tile_part, owner_part = tile_str.split(':', 1)
            
            # Parse tile type
            try:
                tile_type = MapType[tile_part]
            except KeyError:
                raise ValueError(f"Unknown tile type: {tile_part}")
                
            # Parse owner
            if owner_part.isdigit():
                # New format: player index
                owner = int(owner_part)
            else:
                # Legacy format: color name
                owner_part = owner_part.upper()
                if owner_part not in self.LEGACY_COLOR_MAP:
                    raise ValueError(f"Unknown owner: {owner_part}")
                owner = self.LEGACY_COLOR_MAP[owner_part]
                
            # Convert -1 (neutral) to None
            if owner == -1:
                owner = None
                
            return tile_type, owner
        else:
            # No ownership
            try:
                tile_type = MapType[tile_str]
                return tile_type, None
            except KeyError:
                raise ValueError(f"Unknown tile type: {tile_str}")
                
    def save_map(self, filename: str, use_new_format: bool = True):
        """Save map to file"""
        lines = []
        
        # Header
        if use_new_format:
            lines.append(str(self.player_manager.get_player_count()))
        else:
            # Legacy format - use sprite colors
            colors = []
            for i in range(self.player_manager.get_player_count()):
                sprite_color = self.player_manager.get_sprite_color(i)
                colors.append(sprite_color)
            lines.append(','.join(colors))
            
        # Dimensions
        lines.append(f"{self.width},{self.height}")
        
        # Tiles
        for row in self.tiles:
            tile_strs = []
            for tile_type, owner in row:
                if owner is not None:
                    if use_new_format:
                        tile_strs.append(f"{tile_type.name}:{owner}")
                    else:
                        # Legacy format - convert back to color
                        sprite_color = self.player_manager.get_sprite_color(owner)
                        tile_strs.append(f"{tile_type.name}:{sprite_color}")
                else:
                    tile_strs.append(tile_type.name)
                    
            lines.append(' '.join(tile_strs))
            
        # Write file
        with open(filename, 'w') as f:
            f.write('\n'.join(lines))
            
    @staticmethod
    def convert_legacy_to_new(input_file: str, output_file: str):
        """Convert a legacy map to new format"""
        parser = MapParserV2()
        player_manager, tiles = parser.parse_file(input_file)
        parser.player_manager = player_manager
        parser.tiles = tiles
        parser.save_map(output_file, use_new_format=True)
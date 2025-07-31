"""
Map Parser V2 - Parses slot-based map format
"""
from typing import List, Tuple, Dict, Optional
from map_system import MapType
from player_system import PlayerManager, SpriteColor

class MapParserV2:
    """Parses map files using player slot indices"""
    
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
            
        # Parse header - must be number of players
        header = lines[0]
        if not header.isdigit():
            raise ValueError(f"Invalid map format. Expected number of players, got: {header}")
        
        self._parse_header(int(header))
            
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
        
    def _parse_header(self, player_count: int):
        """Parse header (player count)"""
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
                
            # Parse owner - must be player index
            if not owner_part.isdigit():
                raise ValueError(f"Invalid owner format. Expected player index, got: {owner_part}")
            
            owner = int(owner_part)
            
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
                
    def save_map(self, filename: str):
        """Save map to file in slot format"""
        lines = []
        
        # Header - player count
        lines.append(str(self.player_manager.get_player_count()))
        
        # Dimensions
        lines.append(f"{self.width},{self.height}")
        
        # Tiles
        for row in self.tiles:
            tile_strs = []
            for tile_type, owner in row:
                if owner is not None:
                    tile_strs.append(f"{tile_type.name}:{owner}")
                else:
                    tile_strs.append(tile_type.name)
                    
            lines.append(' '.join(tile_strs))
            
        # Write file
        with open(filename, 'w') as f:
            f.write('\n'.join(lines))
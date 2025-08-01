"""
Game Factory - Creates games with flexible player configuration
"""
from typing import List, Dict, Optional, Tuple
from map_system import Map, Army, map_repository
from gameboard import GameBoard, GameTile
from player_system import PlayerManager, SpriteColor
from map_parser_v2 import MapParserV2
from manager import GameManager
from config import Config
import uuid
import os

class GameFactory:
    """Factory for creating games with different player configurations"""
    
    @staticmethod
    def create_standard_game(map_name: str = "small_battle") -> Tuple[GameManager, str]:
        """Create a standard 2-player game"""
        player_manager = PlayerManager.create_default_2_player()
        return GameFactory._create_game(map_name, player_manager)
        
    @staticmethod
    def create_game_with_players(map_name: str, players: List[Dict]) -> Tuple[GameManager, str]:
        """
        Create a game with custom players
        
        Args:
            map_name: Name of the map to use
            players: List of player configs, each with:
                - name: Player display name
                - color: Display color
                - sprite_color: Which sprite set to use (RED, BLUE, GREEN, YELLOW, GREY)
                - is_ai: Whether player is AI controlled (optional)
                - team: Team number for team games (optional)
                
        Example:
            players = [
                {"name": "Alice", "color": "Purple", "sprite_color": "RED"},
                {"name": "Bob", "color": "Orange", "sprite_color": "BLUE"}
            ]
        """
        player_manager = PlayerManager()
        
        for i, player_config in enumerate(players):
            sprite_color = SpriteColor[player_config.get('sprite_color', 'GREY')]
            player_manager.add_player(
                player_id=i,
                name=player_config.get('name', f'Player {i+1}'),
                color=player_config.get('color', sprite_color.value),
                sprite_color=sprite_color,
                is_ai=player_config.get('is_ai', False),
                team=player_config.get('team')
            )
            
        return GameFactory._create_game(map_name, player_manager)
        
    @staticmethod
    def create_3_player_game(map_name: str = "triangle_arena") -> Tuple[GameManager, str]:
        """Create a 3-player game"""
        player_manager = PlayerManager()
        player_manager.add_player(0, "Player 1", "Red", SpriteColor.RED)
        player_manager.add_player(1, "Player 2", "Blue", SpriteColor.BLUE)
        player_manager.add_player(2, "Player 3", "Green", SpriteColor.GREEN)
        return GameFactory._create_game(map_name, player_manager)
        
    @staticmethod
    def create_4_player_game(map_name: str = "cross_battle") -> Tuple[GameManager, str]:
        """Create a 4-player game"""
        player_manager = PlayerManager.create_default_4_player()
        return GameFactory._create_game(map_name, player_manager)
        
    @staticmethod
    def _create_game(map_name: str, player_manager: PlayerManager) -> Tuple[GameManager, str]:
        """Internal method to create a game with given player configuration"""
        # Generate game token
        token = str(uuid.uuid4())
        
        # Load map (try new format first, fall back to legacy)
        map_obj = None
        
        # First check if the map exists in the repository
        map_obj = map_repository.get_map(map_name)
        
        # If not found, try loading from maps_v2 directory
        if map_obj is None and os.path.exists(f'maps_v2/{map_name}.txt'):
            try:
                parser = MapParserV2()
                pm_from_map, tiles = parser.parse_file(f'maps_v2/{map_name}.txt')
                
                # Create Map object from parsed data
                from map_system import MapTile
                map_tiles = []
                turn_order = []
                
                for y in range(parser.height):
                    for x in range(parser.width):
                        tile_type, owner = tiles[y][x]
                        map_tile = MapTile(tile_type)
                        if owner is not None:
                            # Convert player index to army based on sprite color
                            player = player_manager.get_player(owner)
                            if player:
                                # Map sprite color to army
                                army_map = {
                                    SpriteColor.RED: Army.RED,
                                    SpriteColor.BLUE: Army.BLUE,
                                    SpriteColor.GREEN: Army.GREEN,
                                    SpriteColor.YELLOW: Army.YELLOW,
                                    SpriteColor.GREY: Army.GREY
                                }
                                army = army_map.get(player.sprite_color)
                                if army:
                                    map_tile.army = army
                                    if army not in turn_order:
                                        turn_order.append(army)
                        map_tiles.append(map_tile)
                
                map_obj = Map(
                    width=parser.width,
                    height=parser.height,
                    tiles=map_tiles,
                    turn_order=turn_order if turn_order else [Army.RED, Army.BLUE],
                    name=map_name
                )
            except Exception as e:
                print(f"Failed to load from maps_v2: {e}")
                
        # If still no map found, default to test map
        if map_obj is None:
            map_obj = map_repository.get_map('test')
            
        # Create board directly
        board = GameBoard()
        board.width = map_obj.width
        board.height = map_obj.height
        board.days = 1
        board.game_active = True
        board.map = map_obj  # Store the map reference
        
        # Create grid from map
        board.grid = []
        for i in range(map_obj.width * map_obj.height):
            x = i % map_obj.width
            y = int(i / map_obj.width)
            tile = GameTile(x, y, mapTile=map_obj.tiles[i])
            board.grid.append(tile)
        
        # Initialize with player manager
        board.initialize_from_player_manager(player_manager)
        
        # Set turn order based on players
        board.turn_order = [board.get_army_for_player(i) 
                           for i in range(player_manager.get_player_count())
                           if board.get_army_for_player(i) is not None]
        board.current_turn = board.turn_order[0] if board.turn_order else Army.RED
        
        # Create config
        config = Config()  # Will be set by setup_initial_economy
        
        # Create manager
        manager = GameManager(config, board, player_manager)
        manager.setup_initial_economy()
        
        # Distribute initial income to the first player
        manager._update_army_statistics()  # Ensure property counts are updated
        current_army = manager.board.current_turn
        manager._apply_turn_start_effects(current_army)  # Give first player their income
        
        return manager, token
        
    @staticmethod
    def create_from_map_data(map_data: str, player_configs: Optional[List[Dict]] = None) -> Tuple[GameManager, str]:
        """Create a game from raw map data"""
        # Parse map data
        parser = MapParserV2()
        player_manager_from_map, tiles = parser.parse_lines(map_data.strip().split('\n'))
        
        # Use provided player configs or defaults from map
        if player_configs:
            player_manager = PlayerManager()
            for i, config in enumerate(player_configs):
                sprite_color = SpriteColor[config.get('sprite_color', 'GREY')]
                player_manager.add_player(
                    player_id=i,
                    name=config.get('name', f'Player {i+1}'),
                    color=config.get('color', sprite_color.value),
                    sprite_color=sprite_color,
                    is_ai=config.get('is_ai', False),
                    team=config.get('team')
                )
        else:
            player_manager = player_manager_from_map
            
        # Create game
        # ... implementation similar to _create_game ...
        token = str(uuid.uuid4())
        return None, token  # Placeholder
        
    @staticmethod
    def convert_legacy_game(old_manager: GameManager) -> GameManager:
        """Convert a legacy game to the new system"""
        # Detect players from turn order
        player_manager = PlayerManager()
        
        for i, army in enumerate(old_manager.board.turn_order):
            # Map army to sprite color
            sprite_color = SpriteColor[army.name] if army.name in [e.name for e in SpriteColor] else SpriteColor.GREY
            
            player_manager.add_player(
                player_id=i,
                name=f"{army.name} Army",
                color=army.name.title(),
                sprite_color=sprite_color
            )
            
        # Create new board
        board = GameBoard()
        board.grid = old_manager.board.grid
        board.width = old_manager.board.width
        board.height = old_manager.board.height
        board.days = old_manager.board.days
        board.map = old_manager.board.map if hasattr(old_manager.board, 'map') else None
        
        # Initialize with player manager
        board.initialize_from_player_manager(player_manager)
        
        # Copy game state
        board.current_player = old_manager.board.turn_order.index(old_manager.board.current_turn)
        
        # Create new manager
        new_manager = GameManager(old_manager.config, board, player_manager)
        
        # Copy funds
        if hasattr(old_manager.board, 'red_funds'):
            board.red_funds = old_manager.board.red_funds
        if hasattr(old_manager.board, 'blue_funds'):
            board.blue_funds = old_manager.board.blue_funds
            
        return new_manager
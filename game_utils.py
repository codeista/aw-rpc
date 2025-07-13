"""
Game Utilities Module
Shared utilities to avoid circular imports between routes and main app
"""

# Global games dictionary - shared between app and routes
games = {}

def get_games():
    """Get the global games dictionary"""
    return games

def set_games(games_dict):
    """Set the global games dictionary"""
    global games
    games = games_dict

def game_load(token):
    """Load a game by token - shared implementation"""
    from app_core import app_logger
    from models import Game
    from app_core import db
    from manager import GameManager
    from gameboard import GameBoard
    from config import Config
    from map_system import map_repository
    import jsons
    import json
    
    app_logger.info(f"Loading game: {token}")
    
    # CHECK IN-MEMORY GAMES FIRST
    if token in games:
        app_logger.info(f"Game found in memory: {token}")
        return games[token]
    
    game = Game.from_token(db.session, token)
    if game:
        app_logger.info(f"Game found in database: {token}")
        
        try:
            # Handle board data format
            board_data = game.board
            
            # Convert to dict if it's a string
            if isinstance(board_data, str):
                board_dict = json.loads(board_data)
                app_logger.debug(f"Parsed JSON string to dict")
            else:
                board_dict = board_data
                app_logger.debug(f"Board data is already a dict")
            
            # Try to deserialize with jsons
            try:
                board = jsons.loads(board_dict, GameBoard)
                app_logger.debug(f"jsons.loads succeeded")
            except Exception as jsons_error:
                app_logger.debug(f"jsons.loads failed: {jsons_error}")
                # Use simple fallback
                from map_system import Map
                default_map = Map()
                board = GameBoard.create(default_map)
            
            config_game = Config()
            mngr = GameManager(config_game, board)
            mngr.app_logger = app_logger
            return mngr
            
        except Exception as e:
            app_logger.error(f"Failed to deserialize game {token}: {str(e)}")
    
    app_logger.info(f"Creating new game: {token}")   
    # Create new game with default map 
    try:
        default_map = map_repository.get_map('test')
        if not default_map:
            default_map = map_repository.get_map('scorpion')  
    except:
        from map_system import Map
        default_map = Map()
    
    config_game = Config()
    board = GameBoard.create(default_map)
    mngr = GameManager(config_game, board)
    mngr.app_logger = app_logger
    
    return mngr
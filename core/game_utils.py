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
    from core.game_factory import GameFactory
    from core.player_system import PlayerManager, SpriteColor
    from core.map_system import Army
    from config import Config
    import json
    
    app_logger.info(f"Loading game: {token}")
    
    # Check in-memory games first
    if token in games:
        app_logger.info(f"Game found in memory: {token}")
        return games[token]
    
    game = Game.from_token(db.session, token)
    if game:
        app_logger.info(f"Game found in database: {token}")
        
        try:
            # Handle different types of board data
            import jsons
            if isinstance(game.board, str):
                # It's a JSON string, parse it
                board_dict = jsons.loads(game.board)
            else:
                # Already parsed or some other format
                board_dict = game.board
            
            # Check if this is a valid game with player data
            app_logger.info(f"Board dict keys: {list(board_dict.keys()) if board_dict else 'None'}")
            if 'player_funds' in board_dict and 'turn_order' in board_dict:
                # Create player manager from saved data
                player_manager = PlayerManager()
                
                # Reconstruct players based on turn order
                for player_id in board_dict.get('turn_order', []):
                    if player_id not in player_manager.players:
                        # For now, use default colors - this should be saved in game data
                        colors = ['RED', 'BLUE', 'GREEN', 'YELLOW']
                        color = colors[player_id % len(colors)]
                        sprite_color = SpriteColor[color]
                        player_manager.add_player(
                            player_id=player_id,
                            name=f"Player {player_id + 1}",
                            color=color,
                            sprite_color=sprite_color
                        )
                
                # Use the new from_dict method for proper deserialization
                board = GameBoard.from_dict(board_dict, player_manager)
                
                # Create v2 game manager
                config_game = Config()
                mngr = GameManager(config_game, board, player_manager)
                mngr.app_logger = app_logger
                games[token] = mngr  # Cache in memory
                return mngr
            else:
                # Invalid game format
                app_logger.error(f"Invalid game format for {token} - creating new game")
                db.session.delete(game)
                db.session.commit()
            
        except Exception as e:
            app_logger.error(f"Failed to deserialize game {token}: {str(e)}")
            # Delete corrupted game
            try:
                db.session.delete(game)
                db.session.commit()
            except:
                pass
    
    # Create new game if none found or deserialization failed
    app_logger.info(f"Creating new game: {token}")
    mngr, _ = GameFactory.create_standard_game(token)
    mngr.app_logger = app_logger
    games[token] = mngr  # Cache in memory
    
    # Save the new game to database
    try:
        board_dict = mngr.board.to_dict() if hasattr(mngr.board, 'to_dict') else {}
        new_game = Game(board_dict, token)
        db.session.add(new_game)
        db.session.commit()
        app_logger.info(f"Saved new game to database: {token}")
    except Exception as e:
        app_logger.error(f"Failed to save new game to database: {str(e)}")
        db.session.rollback()
    
    return mngr
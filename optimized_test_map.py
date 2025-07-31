"""
Optimized test map creation for quick testing scenarios
"""

from manager_v2 import GameManager
from game_factory import GameFactory
from player_system import PlayerManager, Player, SpriteColor
from map_system import map_repository
import logging

logger = logging.getLogger(__name__)

def create_quick_combat_scenario(token):
    """Create a quick combat test scenario"""
    try:
        # Create player configurations
        players = [
            {'name': 'Player 1', 'color': 'Red', 'sprite_color': 'RED'},
            {'name': 'Player 2', 'color': 'Blue', 'sprite_color': 'BLUE'}
        ]
        
        # Use factory to create game
        game_manager, _ = GameFactory.create_game_with_players(
            map_name='test',
            players=players
        )
        
        # Set high funds for testing
        game_manager.board.player_funds[0] = 50000
        game_manager.board.player_funds[1] = 50000
        
        # Create some units for combat testing
        board = game_manager.board
        
        # RED units (correct parameter order: army, unit_type, x, y)
        game_manager.unit_create('RED', 'INFANTRY', 2, 3)
        game_manager.unit_create('RED', 'TANK', 5, 3)
        game_manager.unit_create('RED', 'ARTILLERY', 7, 4)
        
        # End turn to switch to BLUE
        game_manager.army_end_turn()
        
        # BLUE units
        game_manager.unit_create('BLUE', 'INFANTRY', 3, 3)
        game_manager.unit_create('BLUE', 'MECH', 6, 3)
        game_manager.unit_create('BLUE', 'ROCKET', 8, 4)
        
        # End turn to go back to RED
        game_manager.army_end_turn()
        
        # IMPORTANT: Reset all unit movement flags so they can move
        for tile in board.grid:
            if tile.unit:
                tile.unit.has_moved = False
                tile.unit.done = False
                tile.unit.can_move = True
                tile.unit.can_attack = True
                
        logger.info("All units reset to allow movement in combat test")
        
        logger.info(f"Created quick combat scenario for token: {token}")
        return game_manager
        
    except Exception as e:
        logger.error(f"Failed to create combat scenario: {e}")
        raise

def get_optimized_test_game(token):
    """Create an optimized test game with pre-placed units"""
    try:
        # Create player configurations
        players = [
            {'name': 'Player 1', 'color': 'Red', 'sprite_color': 'RED'},
            {'name': 'Player 2', 'color': 'Blue', 'sprite_color': 'BLUE'}
        ]
        
        # Use factory to create game
        game_manager, _ = GameFactory.create_game_with_players(
            map_name='test',
            players=players
        )
        
        # Set starting funds
        game_manager.board.player_funds[0] = 20000
        game_manager.board.player_funds[1] = 20000
        
        # Create some units for general testing (correct parameter order)
        game_manager.unit_create('RED', 'INFANTRY', 1, 1)
        game_manager.unit_create('RED', 'TANK', 2, 2)
        game_manager.army_end_turn()
        
        game_manager.unit_create('BLUE', 'INFANTRY', 8, 8)
        game_manager.unit_create('BLUE', 'RECON', 7, 7)
        game_manager.army_end_turn()
        
        logger.info(f"Created optimized test game for token: {token}")
        return game_manager
        
    except Exception as e:
        logger.error(f"Failed to create optimized test game: {e}")
        raise
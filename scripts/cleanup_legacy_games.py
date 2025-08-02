#!/usr/bin/env python3
"""
Clean up legacy games from the database
"""

from app_core import app, db
from models import Game
import jsons

def cleanup_legacy_games():
    with app.app_context():
        # Check how many games are in the database
        total_games = db.session.query(Game).count()
        print(f'Total games in database: {total_games}')
        
        # Check for legacy games
        legacy_games = []
        v2_games = []
        
        for game in db.session.query(Game).all():
            try:
                board_data = jsons.loads(game.board)
                if isinstance(board_data, dict) and 'player_manager' in board_data:
                    v2_games.append(game)
                else:
                    legacy_games.append(game)
            except Exception as e:
                # If we can't parse it, it's probably legacy
                legacy_games.append(game)
        
        print(f'\nGame formats:')
        print(f'- V2 games: {len(v2_games)}')
        print(f'- Legacy games: {len(legacy_games)}')
        
        if legacy_games:
            print(f'\nLegacy game tokens to be deleted:')
            for game in legacy_games[:10]:  # Show first 10
                print(f'  - {game.token}')
            if len(legacy_games) > 10:
                print(f'  ... and {len(legacy_games) - 10} more')
            
            # Delete all legacy games
            print('\nDeleting all legacy games...')
            for game in legacy_games:
                db.session.delete(game)
            db.session.commit()
            print(f'\n✓ Deleted {len(legacy_games)} legacy games')
            print('Database is now clean!')
        else:
            print('\n✓ No legacy games found!')

if __name__ == '__main__':
    cleanup_legacy_games()
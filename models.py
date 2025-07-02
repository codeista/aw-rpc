import datetime
import secrets

import jsons

from app_core import db


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(), nullable=False, unique=True)
    date = db.Column(db.DateTime())
    updated = db.Column(db.DateTime())
    board = db.Column(db.String())

    def __init__(self, board, token=None):
        if not token:
            token = secrets.token_urlsafe(4)
        self.token = token
        self.date = datetime.datetime.now()
        self.update = self.date
        self.board = jsons.dumps(board)

    @classmethod
    def from_id(cls, session, id):
        return session.query(cls).filter(cls.id == id).first()

    @classmethod
    def from_token(cls, session, token):
        return session.query(cls).filter(cls.token == token).first()
    def save_optimized(self, board_data):
        """Optimized save using database pool"""
        from database_optimization import optimize_game_save
        import jsons
        
        serialized_board = jsons.dumps(board_data)
        return optimize_game_save(serialized_board, self.token)
    
    @classmethod
    def load_optimized(cls, session, token):
        """Optimized load using database pool"""
        from database_optimization import optimize_game_load
        import jsons
        
        result = optimize_game_load(token)
        if result:
            # Create a model instance
            game = cls.__new__(cls)
            game.token = token
            game.board = result['board']
            game.updated = result['updated']
            return game
        return None

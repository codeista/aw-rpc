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

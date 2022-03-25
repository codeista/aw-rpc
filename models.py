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
    player_one = db.Column(db.Integer, nullable=False, unique=True)
    player_two = db.Column(db.Integer, nullable=False, unique=True)
    players = db.relationship('Player', backref='game', lazy=True)

    def __init__(self, board, token=None):
        if not token:
            token = secrets.token_urlsafe(4)
        self.token = token
        self.date = datetime.datetime.now()
        self.update = self.date
        self.board = jsons.dumps(board)
        self.player_one = 0
        self.player_two = 0

    @classmethod
    def from_id(cls, session, id):
        return session.query(cls).filter(cls.id == id).first()

    @classmethod
    def from_token(cls, session, token):
        return session.query(cls).filter(cls.token == token).first()

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    colour = db.Column(db.String(), nullable=False)
    co = db.Column(db.String(), nullable=False)
    token = db.Column(db.String(), nullable=False)
    pos = db.Column(db.Integer,nullable=False)
    troops = db.Column(db.Integer)
    cities = db.Column(db.Integer)
    stars = db.Column(db.Integer)
    troop_value = db.Column(db.Integer)
    wallet = db.Column(db.Integer)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))

    def __init__(self, token, colour, co, pos):
        self.token = token
        self.colour = colour
        self.co = co
        self.pos = pos
        self.troops = 0
        self.cities = 0
        self.stars= 0
        self.troops_value = 0
        self.wallet = 0

    @classmethod
    def from_id(cls, session, id):
        return session.query(cls).filter(cls.id == id).first()

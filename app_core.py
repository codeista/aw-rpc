'''[This module sets up the Database using SQLAlchemy]'''

import os

from flask import Flask
from flask_jsonrpc import JSONRPC
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key =b'rsgrgewjglwjglwkjgw'
jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)
socketio = SocketIO(app)

if os.getenv('DATABASE_URL'):
    url = os.getenv('DATABASE_URL')
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aw-rpc.db'
db = SQLAlchemy(app)

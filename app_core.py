'''[This module sets up the Database using SQLAlchemy]'''

import os

from flask import Flask
from flask_jsonrpc.app import JSONRPC
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create main JSONRPC instance with enhanced web browsable API
jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)

# Create categorized namespaces for better API organization
game_management_api = jsonrpc.namespace('game_management', description='🎮 Game Management - Core game lifecycle operations')
unit_operations_api = jsonrpc.namespace('unit_operations', description='🪖 Unit Operations - Unit creation, movement, and actions')
combat_system_api = jsonrpc.namespace('combat_system', description='⚔️ Combat System - Attack mechanics and damage calculations')
transport_system_api = jsonrpc.namespace('transport_system', description='🚢 Transport System - Cargo loading and transport operations')
map_tile_api = jsonrpc.namespace('map_tile', description='🗺️ Map & Tile Information - Terrain and tile data access')
special_actions_api = jsonrpc.namespace('special_actions', description='🏰 Special Actions - Property capture and special abilities')
production_economic_api = jsonrpc.namespace('production_economic', description='🏭 Production & Economic - Unit production and financial operations')
information_api = jsonrpc.namespace('information', description='📋 Information & Reference - Configuration and reference data')
communication_api = jsonrpc.namespace('communication', description='💬 Communication - Chat and messaging features')

socketio = SocketIO(app)

if os.getenv('DATABASE_URL'):
    url = os.getenv('DATABASE_URL')
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aw-rpc.db'
from database_optimization import init_database_pool, create_indexes
db = SQLAlchemy(app)

# Set up logging for app_core
import logging
app_logger = logging.getLogger(__name__)

# Export ENHANCED_LOGGING flag
try:
    from logging_config import setup_application_logging
    ENHANCED_LOGGING = True
except ImportError:
    ENHANCED_LOGGING = False

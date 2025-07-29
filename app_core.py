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

# Load production configuration if available
if os.environ.get('FLASK_ENV') == 'production':
    try:
        from config_production import ProductionConfig
        app.config.from_object(ProductionConfig)
    except ImportError:
        pass

# Initialize security middleware in production
if not app.debug and os.environ.get('FLASK_ENV') == 'production':
    try:
        from security_middleware import init_security
        init_security(app)
    except ImportError:
        app_logger.warning("Security middleware not found - running without enhanced security")

# Configure JSON to handle mixed key types
app.config['JSON_SORT_KEYS'] = False  # Prevent sorting that causes mixed key type errors

# Create main JSONRPC instance with enhanced web browsable API
jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)

# For compatibility with current Flask-JSONRPC version, use single instance
# The categorization is handled by our custom documentation route
game_management_api = jsonrpc
unit_operations_api = jsonrpc
combat_system_api = jsonrpc
transport_system_api = jsonrpc
map_tile_api = jsonrpc
special_actions_api = jsonrpc
production_economic_api = jsonrpc
information_api = jsonrpc
communication_api = jsonrpc

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

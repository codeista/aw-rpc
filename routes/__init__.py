# Routes package initialization
"""
Routes Package
Modular route organization for AW-RPC game engine

This package contains organized route modules:
- game_routes.py: Main game functionality (index, maps, game creation)
- admin_routes.py: Administrative functions (debug, logs, testing)
- test_routes.py: Test game creation and validation
- rpc_methods.py: Core JSONRPC API methods
- transport_rpc.py: Transport-specific RPC methods  
- combat_rpc.py: Combat-specific RPC methods
"""

from .game_routes import game_bp
from .admin_routes import admin_bp
from .test_routes import test_bp
from .unified_test_route import unified_test_bp
from .unified_test_api import unified_test_api_bp

__all__ = ['game_bp', 'admin_bp', 'test_bp', 'unified_test_bp', 'unified_test_api_bp']
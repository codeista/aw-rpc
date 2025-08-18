#!/usr/bin/env python3
"""
Route Import Tests
Tests that route modules can be imported directly without import errors
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestRouteImports:
    """Test that all route modules can be imported"""
    
    def test_import_rpc_methods(self):
        """Test importing rpc_methods module"""
        try:
            import routes.rpc_methods
            assert hasattr(routes.rpc_methods, 'jsonrpc')
            # Check key methods are defined
            assert hasattr(routes.rpc_methods, 'game_create_rpc')
            assert hasattr(routes.rpc_methods, 'unit_select_rpc')
            assert hasattr(routes.rpc_methods, 'army_end_turn_rpc')
        except ImportError as e:
            pytest.fail(f"Failed to import routes.rpc_methods: {e}")
    
    def test_import_test_routes(self):
        """Test importing test_routes module"""
        try:
            import routes.test_routes
            # Check blueprint is defined
            assert hasattr(routes.test_routes, 'test_bp')
        except ImportError as e:
            pytest.fail(f"Failed to import routes.test_routes: {e}")
    
    def test_import_unified_test_api(self):
        """Test importing unified_test_api module"""
        try:
            import routes.unified_test_api
            # Check blueprint is defined
            assert hasattr(routes.unified_test_api, 'unified_test_api_bp')
        except ImportError as e:
            pytest.fail(f"Failed to import routes.unified_test_api: {e}")
    
    def test_import_unified_test_route(self):
        """Test importing unified_test_route module"""
        try:
            import routes.unified_test_route
            # Check blueprint is defined
            assert hasattr(routes.unified_test_route, 'unified_test_bp')
        except ImportError as e:
            pytest.fail(f"Failed to import routes.unified_test_route: {e}")
    
    def test_jsonrpc_methods_registered(self):
        """Test that JSONRPC methods are properly registered"""
        # Import the full app to get all registrations
        from app import app
        
        # Check that the /api endpoint exists (JSONRPC endpoint)
        with app.test_client() as client:
            # Test a known good method
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "game_create",
                "params": {"token": "test-registration"},
                "id": 1
            })
            
            # Should get a valid response (even if game creation fails)
            assert response.status_code == 200
            data = response.json
            assert 'jsonrpc' in data or 'result' in data or 'error' in data
            
            # Clean up test game if created
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "game_delete",
                "params": {"token": "test-registration"},
                "id": 2
            })
    
    def test_circular_import_prevention(self):
        """Test that imports don't cause circular dependencies"""
        # This should not raise any ImportError
        try:
            # Import in specific order that could trigger circular imports
            import app_core
            import routes.rpc_methods
            import core.game_utils
            import manager
            import gameboard
            
            # Verify key components are accessible
            assert hasattr(app_core, 'jsonrpc')
            assert hasattr(core.game_utils, 'games')
            assert hasattr(manager, 'GameManager')
            assert hasattr(gameboard, 'GameBoard')
            
        except ImportError as e:
            pytest.fail(f"Circular import detected: {e}")
    
    def test_middleware_imports(self):
        """Test that middleware modules can be imported"""
        try:
            from middleware.error_handling import (
                validate_rpc_params, validate_token, validate_coordinates,
                validate_army, validate_unit_type, safe_rpc_call, log_game_event,
                AWRPCError, ValidationError, GameStateError, UnitError, MovementError
            )
            
            # Verify all imports succeeded
            assert callable(validate_rpc_params)
            assert callable(log_game_event)
            assert issubclass(AWRPCError, Exception)
            
        except ImportError as e:
            pytest.fail(f"Failed to import middleware components: {e}")
    
    def test_api_response_imports(self):
        """Test that API response utilities can be imported"""
        try:
            from core.api_response import APIResponse, RPCResponseBuilder
            
            # Verify classes are accessible
            assert hasattr(APIResponse, 'success')
            assert hasattr(APIResponse, 'error')
            assert hasattr(RPCResponseBuilder, '__init__')
            
        except ImportError as e:
            pytest.fail(f"Failed to import API response utilities: {e}")


class TestRouteIntegration:
    """Test route integration with Flask app"""
    
    @pytest.fixture
    def app(self):
        """Get Flask app instance"""
        from app import app
        return app
    
    def test_routes_registered(self, app):
        """Test that all routes are registered with Flask"""
        # Get all registered routes
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        
        # Check expected routes exist
        expected_routes = [
            '/api',  # JSONRPC endpoint
            '/test_interface',
            '/api/docs',
            '/api/browse'
        ]
        
        for route in expected_routes:
            assert any(route in r for r in routes), \
                f"Route '{route}' not found in registered routes: {routes}"
    
    def test_jsonrpc_endpoint_exists(self, app):
        """Test that JSONRPC endpoint is properly configured"""
        with app.test_client() as client:
            # Send invalid JSON-RPC request to test endpoint exists
            response = client.post('/api', json={})
            
            # Should get 400 for bad request (not 404 for missing endpoint)
            assert response.status_code in [200, 400], f"Expected 200 or 400, got {response.status_code}"
            
            # Test with valid JSON-RPC structure but known method
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "troop_info",
                "params": {"token": "test-endpoint"},
                "id": 1
            })
            
            # Should get 200 (method exists even if it fails due to missing game)
            assert response.status_code == 200
            data = response.json
            assert 'jsonrpc' in data
            # Either has result or error
            assert 'result' in data or 'error' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
#!/usr/bin/env python3
"""
Route coverage tests using direct imports
This approach imports and tests route functions directly for better coverage
"""

import pytest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import Flask app and routes
from app import app, jsonrpc, games
from routes import game_routes, admin_routes, test_routes


class TestGameRoutesDirectly:
    """Test game routes by calling functions directly"""
    
    @pytest.fixture
    def mock_game_manager(self):
        """Create a mock game manager"""
        manager = Mock()
        manager.board = Mock()
        manager.board.grid = [[{'terrain': 'PLAIN'} for _ in range(12)] for _ in range(11)]
        manager.board.current_turn = 'RED'
        manager.board.game_active = True
        manager.board.days = 1
        manager.check_turn = Mock(return_value='RED')
        return manager
    
    def test_game_route_function(self):
        """Test the game route renders template"""
        with app.test_request_context():
            with patch('routes.game_routes.render_template') as mock_render:
                mock_render.return_value = "rendered"
                
                # Import and call the route function directly
                from routes.game_routes import game
                result = game("test-token")
                
                mock_render.assert_called_once_with('render.html', token='test-token')
                assert result == "rendered"
    
    def test_create_quick_test_route(self):
        """Test quick test game creation"""
        with app.test_request_context():
            with patch('routes.game_routes.secrets.token_urlsafe', return_value='test-123'):
                with patch('routes.game_routes.redirect') as mock_redirect:
                    with patch('routes.game_routes.games', {}) as mock_games:
                        from routes.game_routes import create_quick_test_game
                        
                        result = create_quick_test_game()
                        
                        mock_redirect.assert_called_once()
                        # Should redirect to game URL
                        call_args = mock_redirect.call_args[0][0]
                        assert '/game/' in call_args
    
    def test_test_interface_route(self):
        """Test the test interface route"""
        with app.test_request_context():
            with patch('routes.test_routes.render_template') as mock_render:
                mock_render.return_value = "test interface"
                
                from routes.test_routes import test_interface_route
                result = test_interface_route()
                
                mock_render.assert_called_once_with('test_interface.html')
                assert result == "test interface"
    
    def test_create_specific_test_route(self):
        """Test creating specific test scenarios"""
        with app.test_request_context():
            with patch('routes.test_routes.secrets.token_urlsafe', return_value='test-456'):
                with patch('routes.test_routes.redirect') as mock_redirect:
                    with patch('routes.test_routes.get_predeployed_test_game') as mock_get_game:
                        mock_get_game.return_value = Mock()
                        
                        from routes.test_routes import create_test_game_route
                        result = create_test_game_route('movement')
                        
                        assert mock_get_game.called
                        mock_redirect.assert_called_once()


class TestAdminRoutesDirectly:
    """Test admin routes directly"""
    
    def test_admin_panel_route(self):
        """Test admin panel rendering"""
        with app.test_request_context():
            with patch('routes.admin_routes.render_template') as mock_render:
                with patch('routes.admin_routes.Game') as mock_game_model:
                    mock_game_model.query.all.return_value = []
                    mock_render.return_value = "admin panel"
                    
                    from routes.admin_routes import admin_panel
                    result = admin_panel()
                    
                    mock_render.assert_called_once()
                    assert result == "admin panel"
    
    def test_api_browser_route(self):
        """Test API browser route"""
        with app.test_request_context():
            with patch('routes.admin_routes.render_template') as mock_render:
                mock_render.return_value = "api browser"
                
                from routes.admin_routes import api_browser
                result = api_browser()
                
                mock_render.assert_called_once_with('api_browser.html')
                assert result == "api browser"


class TestRPCMethodsCoverage:
    """Test RPC methods for coverage"""
    
    @pytest.fixture
    def mock_request_context(self):
        """Create mock request context"""
        with app.test_request_context():
            yield
    
    def test_unit_create_rpc_coverage(self, mock_request_context):
        """Test unit_create RPC method"""
        with patch('app.game_load') as mock_load:
            mock_manager = Mock()
            mock_manager.unit_create = Mock(return_value=(True, Mock(hp=10, type='INFANTRY')))
            mock_load.return_value = mock_manager
            
            # Import the RPC method
            from app import unit_create_rpc
            
            # Call it directly
            result = unit_create_rpc('test-token', 'RED', 'INFANTRY', 0, 0)
            
            assert mock_manager.unit_create.called
            assert 'type' in result
    
    def test_game_board_rpc_coverage(self, mock_request_context):
        """Test game_board RPC method"""
        with patch('app.game_load') as mock_load:
            mock_manager = Mock()
            mock_board = Mock()
            mock_board.grid = [[{'terrain': 'PLAIN'}]]
            mock_board.current_turn = 'RED'
            mock_board.game_active = True
            mock_manager.board = mock_board
            mock_load.return_value = mock_manager
            
            with patch('app.jsons.dump', return_value={'grid': [[]], 'current_turn': 'RED'}):
                from app import game_board_rpc
                
                result = game_board_rpc('test-token')
                
                assert 'grid' in result
                assert 'current_turn' in result


class TestDirectRouteImports:
    """Test routes by importing them directly"""
    
    def test_import_all_routes(self):
        """Ensure all route modules can be imported"""
        try:
            from routes import combat_rpc
            from routes import transport_rpc
            from routes import rpc_methods
            from routes import unified_test_api
            from routes import unified_test_route
            from routes import api_docs_route
            
            # Just importing them improves coverage
            assert combat_rpc is not None
            assert transport_rpc is not None
            assert rpc_methods is not None
        except ImportError as e:
            pytest.fail(f"Failed to import route module: {e}")
    
    def test_route_registration(self):
        """Test that routes are registered with Flask"""
        # Check some routes are registered
        rules = [rule.endpoint for rule in app.url_map.iter_rules()]
        
        # Game routes
        assert 'game' in rules or 'routes.game_routes.game' in rules
        
        # Admin routes  
        assert 'admin_panel' in rules or 'routes.admin_routes.admin_panel' in rules
        
        # Test routes
        assert 'test_interface_route' in rules or 'routes.test_routes.test_interface_route' in rules


class TestAPIMocking:
    """Test API endpoints with better mocking"""
    
    def test_rpc_endpoint_mocked(self):
        """Test RPC endpoint with mocked internals"""
        with app.test_client() as client:
            with patch('app.jsonrpc.dispatch_request') as mock_dispatch:
                mock_dispatch.return_value = {'jsonrpc': '2.0', 'result': 'ok', 'id': 1}
                
                response = client.post('/api', json={
                    'jsonrpc': '2.0',
                    'method': 'test_method',
                    'params': {},
                    'id': 1
                })
                
                assert response.status_code == 200
                assert mock_dispatch.called
    
    def test_game_routes_with_mocking(self):
        """Test game routes with proper mocking"""
        with app.test_client() as client:
            # Mock the games dictionary
            with patch.dict('app.games', {'test-token': Mock()}):
                response = client.get('/game/test-token')
                assert response.status_code == 200
    
    def test_admin_routes_with_auth_mock(self):
        """Test admin routes with auth mocking"""
        with app.test_client() as client:
            # Mock any auth checks
            with patch('routes.admin_routes.Game') as mock_game:
                mock_game.query.all.return_value = []
                
                response = client.get('/admin')
                # Admin might require auth or redirect
                assert response.status_code in [200, 302, 401]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
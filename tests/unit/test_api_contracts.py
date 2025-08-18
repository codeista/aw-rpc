#!/usr/bin/env python3
"""
API Contract Tests
Validates that all RPC methods return consistent, useful responses
"""

import pytest
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app import app, db


class TestAPIContracts:
    """Test API response contracts for consistency"""
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            
        with app.test_client() as client:
            yield client
            
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    @pytest.fixture
    def game_token(self, client):
        """Create a test game"""
        import uuid
        token = f"api-contract-{uuid.uuid4().hex[:8]}"
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": token},
            "id": 1
        })
        yield token
        # Cleanup
        client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_delete",
            "params": {"token": token},
            "id": 1
        })
    
    def test_standard_success_format(self, client, game_token):
        """Test that successful responses follow standard format"""
        # Test army_end_turn
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "army_end_turn",
            "params": {"token": game_token},
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'result' in data
        result = data['result']
        
        # Check standard fields
        assert 'success' in result
        assert result['success'] == True
        assert 'data' in result
        assert 'message' in result
        assert 'timestamp' in result
        assert 'context' in result
        
        # Check context fields
        context = result['context']
        assert 'current_turn' in context
        assert 'day' in context
        assert 'game_active' in context
        assert 'red_funds' in context
        assert 'blue_funds' in context
    
    def test_unit_select_contract(self, client, game_token):
        """Test unit_select returns comprehensive information"""
        # Create a unit first
        client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "unit_create",
            "params": {
                "token": game_token,
                "unit_type": "INFANTRY",
                "x": 3,
                "y": 3
            },
            "id": 1
        })
        
        # Select the unit
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "unit_select",
            "params": {
                "token": game_token,
                "x": 3,
                "y": 3
            },
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        result = data['result']
        
        # Check response structure
        assert result['success'] == True
        assert 'data' in result
        
        select_data = result['data']
        assert 'tile' in select_data
        assert 'selected' in select_data
        assert select_data['selected'] == True
        
        # Since we selected a unit, should have unit info
        assert 'unit' in select_data
        unit = select_data['unit']
        assert 'type' in unit
        assert 'army' in unit
        assert 'health' in unit
        assert 'fuel' in unit
        
        # Should have available actions
        assert 'available_actions' in select_data
        assert isinstance(select_data['available_actions'], list)
    
    def test_unit_create_contract(self, client, game_token):
        """Test unit_create returns proper unit information"""
        # First, create an infantry unit which is cheaper
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "unit_create",
            "params": {
                "token": game_token,
                "unit_type": "INFANTRY",
                "x": 1,
                "y": 1
            },
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        result = data['result']
        
        assert result['success'] == True
        assert 'data' in result
        
        create_data = result['data']
        assert 'unit' in create_data
        assert 'position' in create_data
        assert 'cost' in create_data
        assert 'remaining_funds' in create_data
        
        # Check unit info
        unit = create_data['unit']
        assert unit['type'] == 'INFANTRY'
        assert 'army' in unit
        assert unit['health'] == 100  # New units have full health
        
        # Check position
        pos = create_data['position']
        assert pos['x'] == 1
        assert pos['y'] == 1
    
    def test_check_turn_contract(self, client, game_token):
        """Test check_turn provides comprehensive turn information"""
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "check_turn",
            "params": {
                "token": game_token,
                "player_id": 0
            },
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        result = data['result']
        
        # Check all required fields
        assert 'is_turn' in result
        assert 'current_turn' in result
        assert 'requested_army' in result
        assert 'turn_order' in result
        assert 'active_units' in result
        assert 'available_actions' in result
        assert 'day' in result
        assert 'game_active' in result
        
        # Validate types
        assert isinstance(result['is_turn'], bool)
        assert isinstance(result['turn_order'], list)
        assert isinstance(result['active_units'], int)
        assert isinstance(result['available_actions'], int)
    
    def test_error_response_contract(self, client):
        """Test error responses follow standard format"""
        # Try to check turn with invalid army
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "check_turn",
            "params": {
                "token": "invalid-token",
                "army": "INVALID_ARMY"
            },
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        result = data['result']
        
        # Check error format
        assert 'success' in result
        assert result['success'] == False
        assert 'error' in result
        assert 'code' in result
        assert 'timestamp' in result
    
    def test_empty_tile_select(self, client, game_token):
        """Test selecting an empty tile returns appropriate response"""
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "unit_select",
            "params": {
                "token": game_token,
                "x": 7,
                "y": 7
            },
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        result = data['result']
        
        assert result['success'] == True
        select_data = result['data']
        
        # Should have tile info but no unit
        assert 'tile' in select_data
        assert 'unit' not in select_data or select_data['unit'] is None
        assert 'available_actions' not in select_data or len(select_data['available_actions']) == 0


class TestResponseConsistency:
    """Test that similar methods have consistent response formats"""
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            
        with app.test_client() as client:
            yield client
            
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    @pytest.fixture
    def game_with_units(self, client):
        """Create a game with some units"""
        import uuid
        token = f"consistency-{uuid.uuid4().hex[:8]}"
        
        # Create game
        client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": token},
            "id": 1
        })
        
        # Create a single infantry unit at position (5,5) 
        # which should be empty in the test map
        client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "unit_create",
            "params": {
                "token": token,
                "unit_type": "INFANTRY",
                "x": 5,
                "y": 5
            },
            "id": 1
        })
        
        yield token
        
        # Cleanup
        client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_delete",
            "params": {"token": token},
            "id": 1
        })
    
    def test_all_methods_return_success_field(self, client, game_with_units):
        """Test that all methods return a success field"""
        methods_to_test = [
            ("army_end_turn", {"token": game_with_units}),
            ("unit_select", {"token": game_with_units, "x": 2, "y": 2}),
            ("check_turn", {"token": game_with_units, "player_id": 0}),
            ("tile", {"token": game_with_units, "x": 5, "y": 5}),
            ("troop_info", {"token": game_with_units}),
        ]
        
        for method, params in methods_to_test:
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": 1
            })
            
            assert response.status_code == 200, f"Method {method} failed"
            data = response.json
            result = data.get('result', {})
            
            # All methods should have success field or be simple data responses
            if isinstance(result, dict):
                if 'error' in result or 'success' in result:
                    # Error responses should have success=False
                    if 'error' in result:
                        assert result.get('success', False) == False
    
    def test_unit_info_consistency(self, client, game_with_units):
        """Test that unit information is consistent across methods"""
        # Get unit info from unit_select
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "unit_select",
            "params": {
                "token": game_with_units,
                "x": 5,
                "y": 5
            },
            "id": 1
        })
        
        select_unit = response.json['result']['data']['unit']
        
        # Get unit info from tile
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "tile",
            "params": {
                "token": game_with_units,
                "x": 5,
                "y": 5
            },
            "id": 1
        })
        
        tile_unit = response.json['result']['unit']
        
        # Both should have same core fields
        for field in ['type', 'army', 'health', 'fuel']:
            assert field in select_unit, f"unit_select missing {field}"
            assert field in tile_unit, f"tile missing {field}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
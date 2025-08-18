#!/usr/bin/env python3
"""
Performance Benchmark Tests for AW-RPC
Tests API response times and performance characteristics
"""

import pytest
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app import app

class TestAPIPerformance:
    """Benchmark API response times"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def game_token(self, client):
        """Create a test game and return token"""
        token = f"perf-test-{int(time.time())}"
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": token},
            "id": 1
        })
        assert response.json['result'] == 'ok'
        return token
    
    def test_game_board_performance(self, client, game_token, benchmark):
        """Benchmark game_board API call"""
        def api_call():
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "game_board",
                "params": {"token": game_token},
                "id": 1
            })
            return response.json
        
        result = benchmark(api_call)
        assert 'result' in result
        assert 'grid' in result['result']
    
    def test_unit_creation_performance(self, client, game_token, benchmark):
        """Benchmark unit creation"""
        def create_unit():
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "unit_create",
                "params": {
                    "token": game_token,
                    "player_id": 0,
                    "unit_type": "INFANTRY",
                    "x": 0,
                    "y": 0
                },
                "id": 1
            })
            return response.json
        
        result = benchmark(create_unit)
        assert 'result' in result
    
    def test_movement_calculation_performance(self, client, game_token, benchmark):
        """Benchmark movement range calculation"""
        # First create a unit
        client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "unit_create",
            "params": {
                "token": game_token,
                "player_id": 0,
                "unit_type": "RECON",
                "x": 5,
                "y": 5
            },
            "id": 1
        })
        
        # End turn to enable movement
        client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "army_end_turn",
            "params": {"token": game_token},
            "id": 1
        })
        
        def calculate_movement():
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "movement_range",
                "params": {
                    "token": game_token,
                    "unit_x": 5,
                    "unit_y": 5
                },
                "id": 1
            })
            return response.json
        
        result = benchmark(calculate_movement)
        assert 'result' in result
    
    def test_combat_preview_performance(self, client, game_token, benchmark):
        """Benchmark combat preview calculation"""
        # Create attacker and defender
        for pos in [(3, 3), (3, 4)]:
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "unit_create",
                "params": {
                    "token": game_token,
                    "player_id": 0 if pos == (3, 3) else "BLUE",
                    "unit_type": "TANK",
                    "x": pos[0],
                    "y": pos[1]
                },
                "id": 1
            })
        
        def preview_combat():
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "combat_preview",
                "params": {
                    "token": game_token,
                    "attacker_x": 3,
                    "attacker_y": 3,
                    "defender_x": 3,
                    "defender_y": 4
                },
                "id": 1
            })
            return response.json
        
        result = benchmark(preview_combat)
        assert 'result' in result

class TestLoadPerformance:
    """Test performance under load"""
    
    def test_concurrent_game_creation(self, benchmark):
        """Test creating multiple games concurrently"""
        def create_games():
            with app.test_client() as client:
                tokens = []
                for i in range(10):
                    token = f"load-test-{i}-{int(time.time())}"
                    response = client.post('/api', json={
                        "jsonrpc": "2.0",
                        "method": "game_create_test",
                        "params": {"token": token},
                        "id": 1
                    })
                    tokens.append(token)
                return tokens
        
        tokens = benchmark(create_games)
        assert len(tokens) == 10
    
    def test_large_map_performance(self, benchmark):
        """Test performance with many units on the map"""
        with app.test_client() as client:
            token = f"large-map-{int(time.time())}"
            # Create game
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "game_create_test",
                "params": {"token": token},
                "id": 1
            })
            
            # Add many units
            positions = [(x, y) for x in range(10) for y in range(10) if (x + y) % 3 == 0]
            for x, y in positions[:20]:  # Limit to 20 units
                client.post('/api', json={
                    "jsonrpc": "2.0",
                    "method": "unit_create",
                    "params": {
                        "token": token,
                        "player_id": 0 if (x + y) % 2 == 0 else "BLUE",
                        "unit_type": "INFANTRY",
                        "x": x,
                        "y": y
                    },
                    "id": 1
                })
            
            def get_board_with_many_units():
                response = client.post('/api', json={
                    "jsonrpc": "2.0",
                    "method": "game_board",
                    "params": {"token": token},
                    "id": 1
                })
                return response.json
            
            result = benchmark(get_board_with_many_units)
            assert 'result' in result

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--benchmark-only'])
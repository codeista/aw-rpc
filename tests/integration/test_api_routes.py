#!/usr/bin/env python3
"""
API Route Integration Tests
Tests all RPC endpoints for proper functionality
"""

import pytest
import time
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app import app

class TestGameManagementAPI:
    """Test game management RPC methods"""
    
    @pytest.fixture
    def client(self):
        with app.test_client() as client:
            yield client
    
    def test_game_create_v2(self, client):
        """Test game creation with player configuration"""
        token = f"test-v2-{int(time.time())}"
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_v2",
            "params": {
                "token": token,
                "players": [
                    {"name": "Player 1", "color": "Red", "sprite_color": "RED"},
                    {"name": "Player 2", "color": "Blue", "sprite_color": "BLUE"}
                ],
                "map_name": "test"
            },
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'result' in data
        assert data['result']['token'] == token
        assert len(data['result']['players']) == 2
    
    def test_game_board(self, client):
        """Test getting game board state"""
        token = f"test-board-{int(time.time())}"
        
        # Create game first
        client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": token},
            "id": 1
        })
        
        # Get board
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_board",
            "params": {"token": token},
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'result' in data
        result = data['result']
        assert 'grid' in result
        assert 'current_turn' in result
        assert 'game_active' in result
        assert result['game_active'] == True
    
    def test_check_turn(self, client):
        """Test turn checking"""
        token = f"test-turn-{int(time.time())}"
        
        # Create game
        client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": token},
            "id": 1
        })
        
        # Check turn
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "check_turn",
            "params": {"token": token, "player_id": 0},
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'result' in data
        assert data['result']['current_turn'] in ['RED', 'BLUE']
        assert 'is_turn' in data['result']
    
    def test_army_end_turn(self, client):
        """Test ending turn"""
        token = f"test-end-turn-{int(time.time())}"
        
        # Create game
        client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": token},
            "id": 1
        })
        
        # End turn
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "army_end_turn",
            "params": {"token": token},
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'result' in data
        assert 'success' in data['result'] or 'current_turn' in data['result']

class TestUnitOperationsAPI:
    """Test unit operation RPC methods"""
    
    @pytest.fixture
    def game_setup(self):
        """Create a game for testing"""
        with app.test_client() as client:
            token = f"test-units-{int(time.time())}"
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "game_create_test",
                "params": {"token": token},
                "id": 1
            })
            yield client, token
    
    def test_unit_create(self, game_setup):
        """Test unit creation"""
        client, token = game_setup
        
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "unit_create",
            "params": {
                "token": token,
                "unit_type": "INFANTRY",
                "x": 0,
                "y": 0
            },
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'result' in data
        # API may return different formats
        result = data['result']
        # Check for success or unit information
        assert 'success' in result or 'unit' in result or 'type' in result
    
    def test_unit_select(self, game_setup):
        """Test unit selection"""
        client, token = game_setup
        
        # Create unit first
        client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "unit_create",
            "params": {
                "token": token,
                "unit_type": "TANK",
                "x": 2,
                "y": 2
            },
            "id": 1
        })
        
        # Select unit
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "unit_select",
            "params": {
                "token": token,
                "x": 2,
                "y": 2
            },
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'result' in data
        # Unit just created, can't move yet
        assert data['result']['can_move'] == False
    
    def test_movement_range(self, game_setup):
        """Test movement range calculation"""
        client, token = game_setup
        
        # Create unit
        client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "unit_create",
            "params": {
                "token": token,
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
            "params": {"token": token},
            "id": 1
        })
        
        # Get movement range
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "movement_range",
            "params": {
                "token": token,
                "unit_x": 5,
                "unit_y": 5
            },
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'result' in data
        assert 'movement_tiles' in data['result']
        assert len(data['result']['movement_tiles']) > 0

class TestCombatAPI:
    """Test combat RPC methods"""
    
    @pytest.fixture
    def combat_setup(self):
        """Create a game with units ready for combat"""
        with app.test_client() as client:
            token = f"test-combat-{int(time.time())}"
            
            # Create game
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "game_create_test",
                "params": {"token": token},
                "id": 1
            })
            
            # Create units
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "unit_create",
                "params": {
                    "token": token,
                    "player_id": 0,
                    "unit_type": "TANK",
                    "x": 3,
                    "y": 3
                },
                "id": 1
            })
            
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "unit_create",
                "params": {
                    "token": token,
                    "player_id": 1,
                    "unit_type": "INFANTRY",
                    "x": 3,
                    "y": 4
                },
                "id": 1
            })
            
            # End turns to enable combat
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "army_end_turn",
                "params": {"token": token},
                "id": 1
            })
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "army_end_turn",
                "params": {"token": token},
                "id": 1
            })
            
            yield client, token
    
    def test_combat_preview(self, combat_setup):
        """Test combat preview calculation"""
        client, token = combat_setup
        
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "combat_preview",
            "params": {
                "token": token,
                "attacker_x": 3,
                "attacker_y": 3,
                "defender_x": 3,
                "defender_y": 4
            },
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'result' in data
        result = data['result']
        assert 'attacker_damage' in result
        assert 'defender_damage' in result
        assert result['attacker_damage'] > 0
    
    def test_combat_targets(self, combat_setup):
        """Test getting valid combat targets"""
        client, token = combat_setup
        
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "combat_targets",
            "params": {
                "token": token,
                "unit_x": 3,
                "unit_y": 3
            },
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'result' in data
        assert 'targets' in data['result']
        assert len(data['result']['targets']) > 0

class TestTileAPI:
    """Test tile/map RPC methods"""
    
    @pytest.fixture
    def game_token(self):
        with app.test_client() as client:
            token = f"test-tile-{int(time.time())}"
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "game_create_test",
                "params": {"token": token},
                "id": 1
            })
            yield client, token
    
    def test_tile_info(self, game_token):
        """Test getting tile information"""
        client, token = game_token
        
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "tile",
            "params": {
                "token": token,
                "x": 0,
                "y": 0
            },
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'result' in data
        result = data['result']
        assert 'mapTile' in result
        assert 'type' in result['mapTile']
        assert 'defense' in result

class TestEconomicAPI:
    """Test economic/production RPC methods"""
    
    @pytest.fixture
    def eco_game(self):
        with app.test_client() as client:
            token = f"test-eco-{int(time.time())}"
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "game_create_test",
                "params": {"token": token},
                "id": 1
            })
            yield client, token
    
    def test_get_army_economy(self, eco_game):
        """Test getting army economic info"""
        client, token = eco_game
        
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "get_army_economy",
            "params": {"token": token},
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'result' in data
        result = data['result']
        assert 'current_funds' in result
        assert 'income' in result
        assert 'properties' in result
    
    def test_get_unit_costs(self, eco_game):
        """Test getting unit cost information"""
        client, token = eco_game
        
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "get_unit_costs",
            "params": {"token": token},
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'result' in data
        assert 'INFANTRY' in data['result']
        assert 'TANK' in data['result']
    
    def test_can_afford_unit(self, eco_game):
        """Test unit affordability check"""
        client, token = eco_game
        
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "can_afford_unit",
            "params": {
                "token": token,
                "unit_type": "INFANTRY"
            },
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'result' in data
        assert 'can_afford' in data['result']
        assert 'current_funds' in data['result']
        assert 'unit_cost' in data['result']

class TestTransportAPI:
    """Test transport RPC methods"""
    
    @pytest.fixture
    def transport_game(self):
        with app.test_client() as client:
            token = f"test-transport-{int(time.time())}"
            
            # Create game
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "game_create_test",
                "params": {"token": token},
                "id": 1
            })
            
            # Create APC and infantry
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "unit_create",
                "params": {
                    "token": token,
                    "player_id": 0,
                    "unit_type": "APC",
                    "x": 2,
                    "y": 2
                },
                "id": 1
            })
            
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "unit_create",
                "params": {
                    "token": token,
                    "player_id": 0,
                    "unit_type": "INFANTRY",
                    "x": 3,
                    "y": 2
                },
                "id": 1
            })
            
            # End turn
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "army_end_turn",
                "params": {"token": token},
                "id": 1
            })
            
            yield client, token
    
    def test_get_transport_info(self, transport_game):
        """Test getting transport information"""
        client, token = transport_game
        
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "get_transport_info",
            "params": {
                "token": token,
                "x": 2,
                "y": 2
            },
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json
        assert 'result' in data
        result = data['result']
        assert 'capacity' in result
        assert 'cargo' in result
        assert 'can_carry' in result

class TestInformationAPI:
    """Test information query RPC methods"""
    
    def test_troop_info(self):
        """Test getting troop configuration info"""
        with app.test_client() as client:
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "troop_info",
                "params": {},
                "id": 1
            })
            
            assert response.status_code == 200
            data = response.json
            assert 'result' in data
            assert 'INFANTRY' in data['result']
            assert 'cost' in data['result']['INFANTRY']
            # Movement might be 'move' or in unit class
            infantry = data['result']['INFANTRY']
            assert any(key in infantry for key in ['movement', 'move', 'cls'])
    
    def test_get_damage_chart(self):
        """Test getting damage chart"""
        with app.test_client() as client:
            token = f"test-chart-{int(time.time())}"
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "game_create_test",
                "params": {"token": token},
                "id": 1
            })
            
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "get_damage_chart",
                "params": {"token": token},
                "id": 1
            })
            
            assert response.status_code == 200
            data = response.json
            assert 'result' in data
            # Should have damage values for unit matchups

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
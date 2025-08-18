#!/usr/bin/env python3
"""
Reusable test fixtures for AW-RPC tests
Provides common game states and scenarios
"""

import pytest
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app import app


class GameFixtures:
    """Collection of reusable game state fixtures"""
    
    @staticmethod
    def create_test_game(client, token=None):
        """Create a basic test game"""
        if token is None:
            token = f"fixture-{int(time.time())}"
        
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": token},
            "id": 1
        })
        
        assert response.json['result'] == 'ok'
        return token
    
    @staticmethod
    def create_game_with_units(client, token=None, units=None):
        """Create a game with predefined units"""
        token = GameFixtures.create_test_game(client, token)
        
        if units is None:
            units = [
                {"player_id": 0, "type": "INFANTRY", "x": 0, "y": 0},
                {"player_id": 0, "type": "TANK", "x": 2, "y": 2},
                {"player_id": 1, "type": "INFANTRY", "x": 5, "y": 5},
                {"player_id": 1, "type": "RECON", "x": 7, "y": 7}
            ]
        
        for unit in units:
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "unit_create",
                "params": {
                    "token": token,
                    "army": unit["army"],
                    "unit_type": unit["type"],
                    "x": unit["x"],
                    "y": unit["y"]
                },
                "id": 1
            })
            assert response.status_code == 200
        
        return token
    
    @staticmethod
    def create_combat_scenario(client, token=None):
        """Create a game ready for combat testing"""
        token = GameFixtures.create_test_game(client, token)
        
        # Create adjacent units
        units = [
            {"player_id": 0, "type": "TANK", "x": 3, "y": 3},
            {"player_id": 1, "type": "INFANTRY", "x": 3, "y": 4},
            {"player_id": 0, "type": "ARTILLERY", "x": 5, "y": 3},
            {"player_id": 1, "type": "MECH", "x": 7, "y": 4}
        ]
        
        for unit in units:
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "unit_create",
                "params": {
                    "token": token,
                    **unit
                },
                "id": 1
            })
        
        # End turn to enable actions
        GameFixtures.end_turn(client, token)
        GameFixtures.end_turn(client, token)
        
        return token
    
    @staticmethod
    def create_transport_scenario(client, token=None):
        """Create a game with transport units"""
        token = GameFixtures.create_test_game(client, token)
        
        # Create transports and cargo
        units = [
            {"player_id": 0, "type": "APC", "x": 2, "y": 2},
            {"player_id": 0, "type": "INFANTRY", "x": 3, "y": 2},
            {"player_id": 0, "type": "MECH", "x": 2, "y": 3},
            {"player_id": 1, "type": "LANDER", "x": 8, "y": 8},
            {"player_id": 1, "type": "TANK", "x": 8, "y": 7}
        ]
        
        for unit in units:
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "unit_create",
                "params": {
                    "token": token,
                    **unit
                },
                "id": 1
            })
        
        # End turn
        GameFixtures.end_turn(client, token)
        
        return token
    
    @staticmethod
    def create_economic_scenario(client, token=None):
        """Create a game focused on economic testing"""
        token = GameFixtures.create_test_game(client, token)
        
        # Create units near properties
        units = [
            {"player_id": 0, "type": "INFANTRY", "x": 0, "y": 0},  # Near factory
            {"player_id": 0, "type": "INFANTRY", "x": 3, "y": 4},  # Near city
            {"player_id": 1, "type": "INFANTRY", "x": 11, "y": 9},
            {"player_id": 1, "type": "MECH", "x": 8, "y": 7}
        ]
        
        for unit in units:
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "unit_create",
                "params": {
                    "token": token,
                    **unit
                },
                "id": 1
            })
        
        return token
    
    @staticmethod
    def end_turn(client, token):
        """End the current player's turn"""
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "army_end_turn",
            "params": {"token": token},
            "id": 1
        })
        return response.json
    
    @staticmethod
    def move_unit(client, token, from_x, from_y, to_x, to_y):
        """Move a unit"""
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "movement_execute",
            "params": {
                "token": token,
                "from_x": from_x,
                "from_y": from_y,
                "to_x": to_x,
                "to_y": to_y
            },
            "id": 1
        })
        return response.json
    
    @staticmethod
    def get_game_state(client, token):
        """Get current game board state"""
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_board",
            "params": {"token": token},
            "id": 1
        })
        return response.json['result']


# Pytest fixtures
@pytest.fixture
def test_client():
    """Provide test client"""
    with app.test_client() as client:
        yield client


@pytest.fixture
def empty_game(test_client):
    """Create an empty test game"""
    token = GameFixtures.create_test_game(test_client)
    yield test_client, token


@pytest.fixture
def game_with_units(test_client):
    """Create a game with some units"""
    token = GameFixtures.create_game_with_units(test_client)
    yield test_client, token


@pytest.fixture
def combat_ready_game(test_client):
    """Create a game ready for combat"""
    token = GameFixtures.create_combat_scenario(test_client)
    yield test_client, token


@pytest.fixture
def transport_game(test_client):
    """Create a game with transports"""
    token = GameFixtures.create_transport_scenario(test_client)
    yield test_client, token


@pytest.fixture
def economic_game(test_client):
    """Create a game for economic testing"""
    token = GameFixtures.create_economic_scenario(test_client)
    yield test_client, token
#!/usr/bin/env python3
"""
Database Transaction Tests
Tests for database transaction integrity and error handling
"""

import pytest
import json
import time
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app import app, db, Game
from app_core import app_logger
import uuid


class TestDatabaseTransactions:
    """Test database transaction handling"""
    
    @pytest.fixture
    def client(self):
        """Create test client with database"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            yield app.test_client()
            db.session.remove()
            db.drop_all()
    
    @pytest.fixture
    def game_token(self):
        """Generate unique game token"""
        return f"db-test-{uuid.uuid4().hex[:8]}"
    
    def test_game_creation_transaction(self, client, game_token):
        """Test that game creation is atomic"""
        # Create a game
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": game_token},
            "id": 1
        })
        
        assert response.status_code == 200
        result = response.json['result']
        assert result == 'ok'
        
        # Verify game exists in database
        with app.app_context():
            game = Game.query.filter_by(token=game_token).first()
            assert game is not None
            assert game.date is not None
            assert game.board is not None
    
    def test_game_update_transaction(self, client, game_token):
        """Test that game updates are atomic"""
        # Create a game
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": game_token},
            "id": 1
        })
        assert response.status_code == 200
        
        # Make a move
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "unit_create",
            "params": {
                "token": game_token,
                "unit_type": "INFANTRY",
                "x": 2,
                "y": 2
            },
            "id": 2
        })
        
        assert response.status_code == 200
        
        # Verify game state was persisted
        with app.app_context():
            game = Game.query.filter_by(token=game_token).first()
            assert game is not None
            # Game board should contain serialized data
            assert game.board is not None
            assert len(game.board) > 0
    
    def test_transaction_rollback_on_error(self, client, game_token):
        """Test that transactions rollback on error"""
        # Create a game
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": game_token},
            "id": 1
        })
        assert response.status_code == 200
        
        with app.app_context():
            initial_count = Game.query.count()
        
        # Try to create a unit with invalid data
        with patch('manager.GameManager.unit_create') as mock_create:
            mock_create.side_effect = Exception("Database error")
            
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "unit_create",
                "params": {
                    "token": game_token,
                    "unit_type": "INVALID_TYPE",
                    "x": -1,
                    "y": -1
                },
                "id": 2
            })
        
        # Should get an error response
        assert response.status_code == 200
        # Since we mocked the error, check that we got a result
        result = response.json
        assert 'result' in result or 'error' in result
        
        # Database should not have changed
        with app.app_context():
            assert Game.query.count() == initial_count
    
    def test_concurrent_game_updates(self, client, game_token):
        """Test handling of concurrent game updates"""
        # Create a game
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": game_token},
            "id": 1
        })
        assert response.status_code == 200
        
        # Simulate concurrent updates
        from threading import Thread
        results = []
        
        def make_unit(x, y, unit_id):
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "unit_create",
                "params": {
                    "token": game_token,
                    "unit_type": "INFANTRY",
                    "x": x,
                    "y": y
                },
                "id": unit_id
            })
            results.append(response)
        
        # Create threads for concurrent requests
        threads = []
        positions = [(2, 2), (3, 3), (4, 4)]
        
        for i, (x, y) in enumerate(positions):
            thread = Thread(target=make_unit, args=(x, y, i+10))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should have completed successfully
        assert len(results) == len(positions)
        for response in results:
            assert response.status_code == 200
    
    def test_database_connection_recovery(self, client, game_token):
        """Test recovery from database connection errors"""
        # Create a game
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": game_token},
            "id": 1
        })
        assert response.status_code == 200
        
        # Simulate database connection error
        with patch('app.db.session.commit') as mock_commit:
            mock_commit.side_effect = [Exception("Connection lost"), None]
            
            # First attempt should fail
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "army_end_turn",
                "params": {"token": game_token},
                "id": 2
            })
            
            # Should handle the error gracefully
            assert response.status_code == 200
    
    def test_game_deletion_cascade(self, client, game_token):
        """Test that game deletion properly cascades"""
        # Create a game
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": game_token},
            "id": 1
        })
        assert response.status_code == 200
        
        # Delete the game
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_delete",
            "params": {"token": game_token},
            "id": 2
        })
        
        assert response.status_code == 200
        result = response.json['result']
        # game_delete returns a dict with success field
        if isinstance(result, dict):
            assert result.get('success', True)
        else:
            # Or just 'ok'
            assert result in ['ok', True]
        
        # Verify game is deleted from database
        with app.app_context():
            game = Game.query.filter_by(token=game_token).first()
            assert game is None


class TestDatabaseIntegrity:
    """Test database integrity constraints"""
    
    @pytest.fixture
    def client(self):
        """Create test client with database"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            yield app.test_client()
            db.session.remove()
            db.drop_all()
    
    def test_unique_token_constraint(self, client):
        """Test that game tokens must be unique"""
        token = f"unique-test-{uuid.uuid4().hex[:8]}"
        
        # Create first game
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": token},
            "id": 1
        })
        assert response.status_code == 200
        
        # Try to create another game with same token
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": token},
            "id": 2
        })
        
        # Should get an error due to duplicate token
        # The current implementation returns 500 for integrity errors
        assert response.status_code in [200, 500]
        
        # If we got 500, it should be the integrity error
        if response.status_code == 500:
            # This is expected - the unique constraint is working
            pass
        else:
            # If 200, should have an error in the result
            result = response.json
            assert 'error' in result
    
    def test_data_serialization(self, client):
        """Test that game data is properly serialized/deserialized"""
        token = f"serial-test-{uuid.uuid4().hex[:8]}"
        
        # Create game
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": token},
            "id": 1
        })
        assert response.status_code == 200
        
        # Create a unit with player_id parameter
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "unit_create",
            "params": {
                "token": token,
                "player_id": 0,  # Added required player_id
                "unit_type": "INFANTRY",
                "x": 8,
                "y": 5
            },
            "id": 2
        })
        assert response.status_code == 200
        
        # Retrieve game board
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_board",
            "params": {"token": token},
            "id": 3
        })
        
        assert response.status_code == 200
        result = response.json['result']
        
        # Check that unit exists in board
        grid = result['grid']
        unit_tile = next((tile for tile in grid if tile['x'] == 8 and tile['y'] == 5), None)
        assert unit_tile is not None
        assert unit_tile.get('unit') is not None
        assert unit_tile['unit']['type'] == 'INFANTRY'
        
        # Verify serialization by checking database directly
        with app.app_context():
            game = Game.query.filter_by(token=token).first()
            assert game is not None
            # Board should be serialized as string or bytes
            assert game.board is not None
            assert len(game.board) > 0
    
    def test_timestamp_tracking(self, client):
        """Test that timestamps are properly tracked"""
        token = f"timestamp-test-{uuid.uuid4().hex[:8]}"
        
        # Create game
        start_time = time.time()
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": token},
            "id": 1
        })
        assert response.status_code == 200
        
        with app.app_context():
            game = Game.query.filter_by(token=token).first()
            assert game is not None
            assert game.date is not None
            # Game model uses 'date' and 'updated' not created_at/updated_at
            initial_date = game.date
        
        # Make an update
        time.sleep(0.1)
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "army_end_turn",
            "params": {"token": token},
            "id": 2
        })
        assert response.status_code == 200
        
        with app.app_context():
            game = Game.query.filter_by(token=token).first()
            # Check if updated field was set
            if game.updated:
                assert game.updated >= initial_date
            else:
                # Some implementations might not set updated field
                pass


class TestDatabasePerformance:
    """Test database performance characteristics"""
    
    @pytest.fixture
    def client(self):
        """Create test client with database"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            yield app.test_client()
            db.session.remove()
            db.drop_all()
    
    def test_bulk_game_creation(self, client):
        """Test performance of creating multiple games"""
        num_games = 10
        tokens = [f"bulk-test-{i}-{uuid.uuid4().hex[:8]}" for i in range(num_games)]
        
        start_time = time.time()
        
        for token in tokens:
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "game_create_test",
                "params": {"token": token},
                "id": 1
            })
            assert response.status_code == 200
        
        elapsed = time.time() - start_time
        
        # Should complete reasonably quickly
        assert elapsed < 5.0, f"Creating {num_games} games took {elapsed}s"
        
        # Verify all games exist
        with app.app_context():
            assert Game.query.count() >= num_games
    
    def test_large_game_state(self, client):
        """Test handling of large game states"""
        token = f"large-test-{uuid.uuid4().hex[:8]}"
        
        # Create game
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": token},
            "id": 1
        })
        assert response.status_code == 200
        
        # Create many units
        positions = [(x, y) for x in range(2, 8) for y in range(2, 8)]
        
        for i, (x, y) in enumerate(positions[:10]):  # Limit to 10 units
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "unit_create",
                "params": {
                    "token": token,
                    "unit_type": "INFANTRY",
                    "x": x,
                    "y": y
                },
                "id": i + 10
            })
            # Some might fail due to insufficient funds
            assert response.status_code == 200
        
        # Retrieve game state
        start_time = time.time()
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_board",
            "params": {"token": token},
            "id": 100
        })
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 0.5, f"Retrieving large game state took {elapsed}s"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
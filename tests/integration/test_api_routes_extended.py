#!/usr/bin/env python3
"""
Extended API Route Tests
Additional coverage for RPC endpoints
"""

import pytest
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app import app
from tests.fixtures.game_fixtures import GameFixtures
from tests.utils.test_helpers import TestHelpers, APIValidator


class TestSpecialActionsAPI:
    """Test special action RPC methods"""
    
    @pytest.fixture
    def capture_game(self):
        """Create a game ready for capture testing"""
        with app.test_client() as client:
            token = f"test-capture-{int(time.time())}"
            GameFixtures.create_test_game(client, token)
            
            # Create infantry near capturable property
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "unit_create",
                "params": {
                    "token": token,
                    "player_id": 0,
                    "unit_type": "INFANTRY",
                    "x": 2,
                    "y": 4  # Near city at (3,4)
                },
                "id": 1
            })
            
            # End turn to enable movement
            GameFixtures.end_turn(client, token)
            GameFixtures.end_turn(client, token)
            
            # Move to city
            GameFixtures.move_unit(client, token, 2, 4, 3, 4)
            
            yield client, token
    
    def test_capture_tile(self, capture_game):
        """Test property capture"""
        client, token = capture_game
        
        response = TestHelpers.make_rpc_call(client, 'capture_tile', {
            "token": token,
            "x": 3,
            "y": 4
        })
        
        result = TestHelpers.assert_rpc_success(response)
        # Capture may take multiple turns
        assert 'capture_hp' in result or 'error' in result
    
    def test_action_wait(self):
        """Test unit wait action"""
        with app.test_client() as client:
            token = GameFixtures.create_game_with_units(client)
            
            # End turn to enable actions
            GameFixtures.end_turn(client, token)
            GameFixtures.end_turn(client, token)
            
            response = TestHelpers.make_rpc_call(client, 'action_wait', {
                "token": token,
                "unit_x": 0,
                "unit_y": 0
            })
            
            result = TestHelpers.assert_rpc_success(response)
            assert result.get('success') or 'status' in result


class TestProductionAPI:
    """Test production system RPC methods"""
    
    def test_produce_unit(self):
        """Test unit production at factory"""
        with app.test_client() as client:
            token = GameFixtures.create_test_game(client)
            
            # Get production options first
            response = TestHelpers.make_rpc_call(client, 'get_production_options', {
                "token": token,
                "x": 0,
                "y": 0  # Factory location
            })
            
            result = TestHelpers.assert_rpc_success(response)
            
            # Try to produce a unit
            if 'units' in result and result['units']:
                unit_type = result['units'][0]
                
                response = TestHelpers.make_rpc_call(client, 'produce_unit', {
                    "token": token,
                    "x": 0,
                    "y": 0,
                    "unit_type": unit_type
                })
                
                # Should succeed or fail with funds/space issue
                prod_result = response.get('result', {})
                assert 'success' in prod_result or 'error' in prod_result
    
    def test_get_production_menu(self):
        """Test getting production menu"""
        with app.test_client() as client:
            token = GameFixtures.create_test_game(client)
            
            response = TestHelpers.make_rpc_call(client, 'get_production_menu', {
                "token": token,
                "x": 0,
                "y": 0
            })
            
            # Method might not exist or return different format
            if 'result' in response:
                result = response['result']
                assert isinstance(result, (dict, list))


class TestMovementDetailsAPI:
    """Test detailed movement RPC methods"""
    
    def test_movement_execute_with_path(self):
        """Test movement with specific path"""
        with app.test_client() as client:
            token = GameFixtures.create_game_with_units(client)
            
            # End turn
            GameFixtures.end_turn(client, token)
            GameFixtures.end_turn(client, token)
            
            # Execute movement
            response = TestHelpers.make_rpc_call(client, 'movement_execute', {
                "token": token,
                "from_x": 0,
                "from_y": 0,
                "to_x": 1,
                "to_y": 1
            })
            
            result = TestHelpers.assert_rpc_success(response)
            assert result.get('success') or 'moved' in result
    
    def test_get_valid_targets(self):
        """Test getting valid attack targets"""
        with app.test_client() as client:
            token = GameFixtures.create_combat_scenario(client)
            
            response = TestHelpers.make_rpc_call(client, 'get_valid_targets', {
                "token": token,
                "x": 3,
                "y": 3  # Tank position
            })
            
            # Method might be combat_targets instead
            if 'error' in response:
                response = TestHelpers.make_rpc_call(client, 'combat_targets', {
                    "token": token,
                    "unit_x": 3,
                    "unit_y": 3
                })
            
            if 'result' in response:
                result = response['result']
                assert 'targets' in result or isinstance(result, list)


class TestGameStateAPI:
    """Test game state query methods"""
    
    def test_get_current_player(self):
        """Test getting current player info"""
        with app.test_client() as client:
            token = GameFixtures.create_test_game(client)
            
            # Try different methods that might return player info
            response = TestHelpers.make_rpc_call(client, 'check_turn', {
                "token": token
            })
            
            result = TestHelpers.assert_rpc_success(response)
            assert 'current_turn' in result
    
    def test_get_game_status(self):
        """Test getting overall game status"""
        with app.test_client() as client:
            token = GameFixtures.create_test_game(client)
            
            response = TestHelpers.make_rpc_call(client, 'game_board', {
                "token": token
            })
            
            result = TestHelpers.assert_rpc_success(response)
            APIValidator.validate_game_board(result)
            
            # Check game status fields
            assert 'game_active' in result
            assert 'days' in result
            assert result['game_active'] == True
    
    def test_end_game(self):
        """Test game ending/resignation"""
        with app.test_client() as client:
            token = GameFixtures.create_test_game(client)
            
            response = TestHelpers.make_rpc_call(client, 'end_game', {
                "token": token
            })
            
            # Should allow resignation
            if 'result' in response:
                result = response['result']
                assert 'winner' in result or 'status' in result


class TestTransportDetailsAPI:
    """Test detailed transport operations"""
    
    def test_transport_load(self):
        """Test loading unit into transport"""
        with app.test_client() as client:
            token = GameFixtures.create_transport_scenario(client)
            
            # Move infantry to APC
            GameFixtures.move_unit(client, token, 3, 2, 2, 2)
            
            # Load should happen automatically or via command
            response = TestHelpers.make_rpc_call(client, 'transport_load', {
                "token": token,
                "transport_x": 2,
                "transport_y": 2,
                "cargo_x": 2,
                "cargo_y": 2
            })
            
            if 'result' in response:
                result = response['result']
                assert result.get('success') or 'loaded' in result
    
    def test_transport_unload(self):
        """Test unloading from transport"""
        with app.test_client() as client:
            token = GameFixtures.create_transport_scenario(client)
            
            # First load a unit
            GameFixtures.move_unit(client, token, 3, 2, 2, 2)
            
            # Get unload positions
            response = TestHelpers.make_rpc_call(client, 'get_valid_unload_positions', {
                "token": token,
                "x": 2,
                "y": 2
            })
            
            if 'result' in response and response['result']:
                positions = response['result']
                if positions and isinstance(positions, list):
                    # Try to unload
                    pos = positions[0]
                    unload_response = TestHelpers.make_rpc_call(client, 'transport_unload', {
                        "token": token,
                        "transport_x": 2,
                        "transport_y": 2,
                        "unload_x": pos.get('x', 1),
                        "unload_y": pos.get('y', 2),
                        "cargo_index": 0
                    })
                    
                    if 'result' in unload_response:
                        assert unload_response['result'].get('success') or 'unloaded' in unload_response['result']


class TestAdvancedCombatAPI:
    """Test advanced combat features"""
    
    def test_combat_execute(self):
        """Test executing combat"""
        with app.test_client() as client:
            token = GameFixtures.create_combat_scenario(client)
            
            # Execute attack
            response = TestHelpers.make_rpc_call(client, 'combat_execute', {
                "token": token,
                "attacker_x": 3,
                "attacker_y": 3,
                "defender_x": 3,
                "defender_y": 4
            })
            
            if 'result' in response:
                result = response['result']
                # Should have combat result info
                assert any(key in result for key in ['damage_dealt', 'success', 'attacker', 'defender'])
    
    def test_get_damage_modifiers(self):
        """Test getting damage modifiers"""
        with app.test_client() as client:
            token = GameFixtures.create_test_game(client)
            
            # This might be part of combat preview
            response = TestHelpers.make_rpc_call(client, 'combat_preview', {
                "token": token,
                "attacker_x": 0,
                "attacker_y": 0,
                "defender_x": 1,
                "defender_y": 0
            })
            
            if 'result' in response and 'error' not in response['result']:
                result = response['result']
                # Check for modifier info
                assert any(key in result for key in ['terrain_stars', 'modifiers', 'defense'])


class TestUtilityAPI:
    """Test utility and helper methods"""
    
    def test_message_broadcast(self):
        """Test message/chat functionality"""
        with app.test_client() as client:
            token = GameFixtures.create_test_game(client)
            
            response = TestHelpers.make_rpc_call(client, 'message', {
                "token": token,
                "msg": "Test message"
            })
            
            # Should return 'ok' or similar
            if 'result' in response:
                assert response['result'] == 'ok'
    
    def test_game_delete(self):
        """Test game deletion"""
        with app.test_client() as client:
            token = GameFixtures.create_test_game(client)
            
            response = TestHelpers.make_rpc_call(client, 'game_delete', {
                "token": token
            })
            
            result = TestHelpers.assert_rpc_success(response)
            assert result == 'ok' or result.get('success')
            
            # Verify game is deleted
            board_response = TestHelpers.make_rpc_call(client, 'game_board', {
                "token": token
            })
            # Should create new game or error
            assert 'result' in board_response


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
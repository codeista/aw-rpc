#!/usr/bin/env python3
"""
Test helper utilities for AW-RPC tests
Common assertions and utility functions
"""

import json
from typing import Dict, List, Any, Optional


class TestHelpers:
    """Collection of test helper methods"""
    
    @staticmethod
    def assert_valid_rpc_response(response_data: Dict) -> None:
        """Assert that RPC response has valid structure"""
        assert 'jsonrpc' in response_data
        assert response_data['jsonrpc'] == '2.0'
        assert 'id' in response_data
        assert 'result' in response_data or 'error' in response_data
    
    @staticmethod
    def assert_rpc_success(response_data: Dict) -> Dict:
        """Assert RPC call succeeded and return result"""
        TestHelpers.assert_valid_rpc_response(response_data)
        assert 'result' in response_data, f"RPC error: {response_data.get('error')}"
        return response_data['result']
    
    @staticmethod
    def assert_rpc_error(response_data: Dict) -> Dict:
        """Assert RPC call failed and return error"""
        TestHelpers.assert_valid_rpc_response(response_data)
        assert 'error' in response_data
        return response_data['error']
    
    @staticmethod
    def assert_unit_at_position(game_state: Dict, x: int, y: int, 
                               unit_type: Optional[str] = None,
                               army: Optional[str] = None) -> Dict:
        """Assert a unit exists at given position"""
        grid = game_state['grid']
        assert y < len(grid), f"Y coordinate {y} out of bounds"
        assert x < len(grid[y]), f"X coordinate {x} out of bounds"
        
        tile = grid[y][x]
        assert tile.get('unit') is not None, f"No unit at ({x}, {y})"
        
        unit = tile['unit']
        if unit_type:
            assert unit['type'] == unit_type, f"Expected {unit_type}, got {unit['type']}"
        if army:
            assert unit['army'] == army, f"Expected {army}, got {unit['army']}"
        
        return unit
    
    @staticmethod
    def assert_no_unit_at_position(game_state: Dict, x: int, y: int) -> None:
        """Assert no unit exists at given position"""
        grid = game_state['grid']
        tile = grid[y][x]
        assert tile.get('unit') is None, f"Unexpected unit at ({x}, {y}): {tile.get('unit')}"
    
    @staticmethod
    def count_units(game_state: Dict, army: Optional[str] = None) -> int:
        """Count units in game state"""
        count = 0
        for row in game_state['grid']:
            for tile in row:
                if tile.get('unit'):
                    if army is None or tile['unit']['army'] == army:
                        count += 1
        return count
    
    @staticmethod
    def get_unit_positions(game_state: Dict, army: Optional[str] = None,
                          unit_type: Optional[str] = None) -> List[tuple]:
        """Get all unit positions matching criteria"""
        positions = []
        for y, row in enumerate(game_state['grid']):
            for x, tile in enumerate(row):
                if tile.get('unit'):
                    unit = tile['unit']
                    if (army is None or unit['army'] == army) and \
                       (unit_type is None or unit['type'] == unit_type):
                        positions.append((x, y))
        return positions
    
    @staticmethod
    def assert_funds(game_state: Dict, army: str, expected_funds: int,
                    tolerance: int = 0) -> None:
        """Assert army has expected funds"""
        if 'player_funds' in game_state:
            # V2 system
            player_id = 0 if army == 0 else 1
            actual = game_state['player_funds'].get(str(player_id), 0)
        else:
            # Legacy system
            actual = game_state.get(f'{army.lower()}_funds', 0)
        
        assert abs(actual - expected_funds) <= tolerance, \
            f"Expected {army} to have {expected_funds} funds, got {actual}"
    
    @staticmethod
    def assert_turn(game_state: Dict, expected_turn: str) -> None:
        """Assert current turn"""
        actual = game_state.get('current_turn')
        assert actual == expected_turn, \
            f"Expected turn {expected_turn}, got {actual}"
    
    @staticmethod
    def assert_game_active(game_state: Dict) -> None:
        """Assert game is still active"""
        assert game_state.get('game_active', False), "Game is not active"
    
    @staticmethod
    def assert_property_owner(game_state: Dict, x: int, y: int, 
                             expected_owner: Optional[str]) -> None:
        """Assert property ownership"""
        tile = game_state['grid'][y][x]
        terrain = tile.get('terrain', tile.get('type'))
        
        # Check if it's a capturable property
        capturable = ['CITY', 'FACTORY', 'AIRPORT', 'PORT', 'BASE']
        assert any(prop in terrain for prop in capturable), \
            f"Tile at ({x}, {y}) is not a capturable property"
        
        owner = tile.get('owner', tile.get('army'))
        assert owner == expected_owner, \
            f"Expected owner {expected_owner}, got {owner}"
    
    @staticmethod
    def make_rpc_call(client, method: str, params: Dict) -> Dict:
        """Make RPC call and return parsed response"""
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        })
        assert response.status_code == 200
        return response.json
    
    @staticmethod
    def print_game_grid(game_state: Dict) -> None:
        """Print game grid for debugging"""
        grid = game_state['grid']
        print("\n  ", end="")
        print("".join(str(i % 10) for i in range(len(grid[0]))))
        
        for y, row in enumerate(grid):
            print(f"{y:2}", end="")
            for tile in row:
                if tile.get('unit'):
                    army = tile['unit']['army']
                    unit_char = 'R' if army == 0 else 'B'
                else:
                    unit_char = '.'
                print(unit_char, end="")
            print()
        print()


class APIValidator:
    """Validate API responses match expected format"""
    
    @staticmethod
    def validate_game_board(result: Dict) -> None:
        """Validate game_board response"""
        required = ['grid', 'current_turn', 'game_active', 'days']
        for field in required:
            assert field in result, f"Missing required field: {field}"
        
        # Validate grid structure
        assert isinstance(result['grid'], list)
        assert len(result['grid']) > 0
        assert all(isinstance(row, list) for row in result['grid'])
    
    @staticmethod
    def validate_unit_create(result: Dict) -> None:
        """Validate unit_create response"""
        # Result is the unit object
        assert 'type' in result
        assert 'army' in result
        assert 'hp' in result
    
    @staticmethod
    def validate_movement_range(result: Dict) -> None:
        """Validate movement_range response"""
        if 'error' not in result:
            assert 'movement_tiles' in result
            assert isinstance(result['movement_tiles'], list)
    
    @staticmethod
    def validate_combat_preview(result: Dict) -> None:
        """Validate combat_preview response"""
        if 'error' not in result:
            assert 'attacker_damage' in result
            assert 'defender_damage' in result
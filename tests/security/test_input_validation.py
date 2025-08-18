#!/usr/bin/env python3
"""
Security Test Suite for AW-RPC
Tests input validation, injection prevention, and security boundaries
"""

import pytest
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app import app

class TestInputValidation:
    """Test input validation and sanitization"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        with app.test_client() as client:
            yield client
    
    def test_sql_injection_prevention(self, client):
        """Test SQL injection attack prevention"""
        sql_injections = [
            "'; DROP TABLE games; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM games--",
            "1; DELETE FROM games WHERE 1=1--"
        ]
        
        for injection in sql_injections:
            # Try injection in token
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "game_board",
                "params": {"token": injection},
                "id": 1
            })
            # Should handle safely without executing SQL
            assert response.status_code == 200
            # Game should be created with the injection string as token
            # not execute any SQL commands
            data = response.json
            assert 'result' in data
            assert 'grid' in data['result']
    
    def test_xss_prevention(self, client):
        """Test XSS attack prevention"""
        xss_attempts = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'></iframe>"
        ]
        
        for xss in xss_attempts:
            # Try XSS in various parameters
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "game_create_v2",
                "params": {
                    "token": xss,
                    "players": [
                        {"name": xss, "color": "Red", "sprite_color": "RED"}
                    ]
                },
                "id": 1
            })
            
            # Response should not contain unescaped scripts
            response_text = response.get_data(as_text=True)
            assert '<script>' not in response_text
            assert 'onerror=' not in response_text
    
    def test_parameter_type_validation(self, client):
        """Test parameter type validation"""
        # String instead of integer
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "unit_select",
            "params": {"token": "test", "x": "not-a-number", "y": "also-not"},
            "id": 1
        })
        assert response.status_code == 200
        data = response.json
        assert 'error' in data  # Should get type error
        
        # Array instead of string
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_board",
            "params": {"token": ["array", "not", "string"]},
            "id": 1
        })
        assert 'error' in response.json
    
    def test_boundary_values(self, client):
        """Test boundary value handling"""
        token = f"boundary-test-{int(time.time())}"
        
        # Create test game
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": token},
            "id": 1
        })
        assert response.json['result'] == 'ok'
        
        # Test negative coordinates
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "unit_create",
            "params": {
                "token": token,
                "player_id": 0,
                "unit_type": "INFANTRY",
                "x": -1,
                "y": -1
            },
            "id": 1
        })
        result = response.json.get('result', {})
        assert result.get('success') == False or 'error' in result
        
        # Test very large coordinates
        response = client.post('/api', json={
            "jsonrpc": "2.0",
            "method": "tile",
            "params": {"token": token, "x": 999999, "y": 999999},
            "id": 1
        })
        result = response.json.get('result', {})
        assert result.get('success') == False or 'error' in result

class TestAuthenticationSecurity:
    """Test authentication and session security"""
    
    def test_token_format_validation(self):
        """Test that tokens are properly validated"""
        with app.test_client() as client:
            invalid_tokens = [
                "",  # Empty
                " " * 100,  # Very long whitespace
                "a" * 1000,  # Very long token
                "../../../etc/passwd",  # Path traversal attempt
                "token\x00null",  # Null byte injection
            ]
            
            for bad_token in invalid_tokens:
                response = client.post('/api', json={
                    "jsonrpc": "2.0",
                    "method": "game_board",
                    "params": {"token": bad_token},
                    "id": 1
                })
                # Should handle gracefully
                assert response.status_code == 200
    
    def test_concurrent_access_control(self):
        """Test concurrent access to same game"""
        with app.test_client() as client:
            token = f"concurrent-{int(time.time())}"
            
            # Create game
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "game_create_test",
                "params": {"token": token},
                "id": 1
            })
            assert response.json['result'] == 'ok'
            
            # Try to end turn multiple times rapidly
            results = []
            for i in range(5):
                response = client.post('/api', json={
                    "jsonrpc": "2.0",
                    "method": "army_end_turn",
                    "params": {"token": token},
                    "id": 1
                })
                results.append(response.json)
            
            # Should handle concurrent requests gracefully
            assert all('result' in r or 'error' in r for r in results)

class TestDataValidation:
    """Test data validation and constraints"""
    
    def test_unit_type_validation(self):
        """Test invalid unit type handling"""
        with app.test_client() as client:
            token = f"unit-val-{int(time.time())}"
            
            # Create game
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "game_create_test",
                "params": {"token": token},
                "id": 1
            })
            
            # Try to create invalid unit type
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "unit_create",
                "params": {
                    "token": token,
                    "player_id": 0,
                    "unit_type": "SUPER_MEGA_TANK",
                    "x": 0,
                    "y": 0
                },
                "id": 1
            })
            
            result = response.json.get('result', {})
            assert result.get('success') == False or 'error' in result
    
    def test_army_validation(self):
        """Test invalid army handling"""
        with app.test_client() as client:
            token = f"army-val-{int(time.time())}"
            
            # Create game
            client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "game_create_test",
                "params": {"token": token},
                "id": 1
            })
            
            # Try to create unit with invalid army
            response = client.post('/api', json={
                "jsonrpc": "2.0",
                "method": "unit_create",
                "params": {
                    "token": token,
                    "army": "PURPLE",
                    "unit_type": "INFANTRY",
                    "x": 0,
                    "y": 0
                },
                "id": 1
            })
            
            result = response.json.get('result', {})
            assert result.get('success') == False or 'error' in result

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
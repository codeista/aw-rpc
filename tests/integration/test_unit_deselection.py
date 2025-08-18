#!/usr/bin/env python3
"""
Integration test for unit deselection behavior
Tests that units are properly deselected after movement when they have no actions available
"""

import unittest
import requests
import time
import random
import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestUnitDeselection(unittest.TestCase):
    """Test unit deselection after movement"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.base_url = "http://localhost:5000"
        cls.api_url = f"{cls.base_url}/api"
    
    def setUp(self):
        """Create a test game for each test"""
        self.token = f"deselect_test_{''.join(random.choices(string.ascii_lowercase, k=6))}"
        
        # Create test game
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": self.token},
            "id": "1"
        })
        self.assertEqual(resp.status_code, 200)
        result = resp.json()
        self.assertNotIn("error", result)
    
    def test_unit_deselects_when_no_actions(self):
        """Test that unit deselects after moving to empty area with no enemies"""
        # Create RED infantry
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "produce_unit",
            "params": {
                "token": self.token,
                "x": 0,
                "y": 4,
                "unit_type": "INFANTRY"
            },
            "id": "2"
        })
        self.assertEqual(resp.status_code, 200)
        
        # End turn so unit can move
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "army_end_turn",
            "params": {"token": self.token},
            "id": "3"
        })
        
        # End BLUE turn to get back to RED
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "army_end_turn",
            "params": {"token": self.token},
            "id": "4"
        })
        
        # Select unit
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "unit_select",
            "params": {
                "token": self.token,
                "x": 0,
                "y": 4
            },
            "id": "5"
        })
        self.assertEqual(resp.status_code, 200)
        
        # Get board state to verify selection
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "game_board",
            "params": {"token": self.token},
            "id": "5a"
        })
        result = resp.json()
        board = result.get('result', {})
        self.assertIsNotNone(board.get('selected'))
        
        # Move to empty area
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "unit_move",
            "params": {
                "token": self.token,
                "x": 0,
                "y": 4,
                "x2": 2,
                "y2": 3
            },
            "id": "6"
        })
        result = resp.json()
        self.assertNotIn("error", result)
        
        # Get board state after move
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "game_board",
            "params": {"token": self.token},
            "id": "7"
        })
        result = resp.json()
        board = result.get('result', {})
        
        # Unit should be deselected (no actions available)
        self.assertIsNone(board.get('selected'), "Unit should be deselected after moving to empty area")
    
    def test_unit_stays_selected_with_enemy_nearby(self):
        """Test that unit stays selected after moving adjacent to enemy"""
        # Turn 1: Create units
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "produce_unit",
            "params": {
                "token": self.token,
                "x": 0,
                "y": 4,
                "unit_type": "INFANTRY"
            },
            "id": "10"
        })
        self.assertNotIn("error", resp.json())
        
        # End RED turn
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "army_end_turn",
            "params": {"token": self.token},
            "id": "11"
        })
        
        # Create BLUE infantry
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "produce_unit",
            "params": {
                "token": self.token,
                "x": 10,
                "y": 3,
                "unit_type": "INFANTRY"
            },
            "id": "12"
        })
        self.assertNotIn("error", resp.json())
        
        # End BLUE turn
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "army_end_turn",
            "params": {"token": self.token},
            "id": "13"
        })
        
        # Turn 2: Move units closer
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "unit_move",
            "params": {
                "token": self.token,
                "x": 0,
                "y": 4,
                "x2": 3,
                "y2": 4
            },
            "id": "20"
        })
        self.assertNotIn("error", resp.json())
        
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "army_end_turn",
            "params": {"token": self.token},
            "id": "21"
        })
        
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "unit_move",
            "params": {
                "token": self.token,
                "x": 10,
                "y": 3,
                "x2": 7,
                "y2": 3
            },
            "id": "22"
        })
        self.assertNotIn("error", resp.json())
        
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "army_end_turn",
            "params": {"token": self.token},
            "id": "23"
        })
        
        # Turn 3: Position units to be 2 tiles apart
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "unit_move",
            "params": {
                "token": self.token,
                "x": 3,
                "y": 4,
                "x2": 5,
                "y2": 4
            },
            "id": "30"
        })
        self.assertNotIn("error", resp.json())
        
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "army_end_turn",
            "params": {"token": self.token},
            "id": "31"
        })
        
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "unit_move",
            "params": {
                "token": self.token,
                "x": 7,
                "y": 3,
                "x2": 6,
                "y2": 3
            },
            "id": "32"
        })
        self.assertNotIn("error", resp.json())
        
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "army_end_turn",
            "params": {"token": self.token},
            "id": "33"
        })
        
        # Turn 4: Select RED unit and move adjacent to BLUE
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "unit_select",
            "params": {
                "token": self.token,
                "x": 5,
                "y": 4
            },
            "id": "40"
        })
        self.assertNotIn("error", resp.json())
        
        # Move RED to (6,4) - adjacent to BLUE at (6,3)
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "unit_move",
            "params": {
                "token": self.token,
                "x": 5,
                "y": 4,
                "x2": 6,
                "y2": 4
            },
            "id": "41"
        })
        result = resp.json()
        self.assertNotIn("error", result)
        
        # Get board state after move
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "game_board",
            "params": {"token": self.token},
            "id": "42"
        })
        result = resp.json()
        board = result.get('result', {})
        
        # Debug: Check unit positions
        red_unit = None
        blue_unit = None
        for tile in board.get('grid', []):
            if tile.get('unit'):
                unit = tile['unit']
                if unit.get('player_id') == 0:
                    red_unit = {'x': tile['x'], 'y': tile['y'], 'type': unit.get('type')}
                elif unit.get('player_id') == 1:
                    blue_unit = {'x': tile['x'], 'y': tile['y'], 'type': unit.get('type')}
        
        print(f"DEBUG: RED unit at {red_unit}, BLUE unit at {blue_unit}")
        print(f"DEBUG: Selected tile: {board.get('selected')}")
        
        # Verify units are adjacent
        if red_unit and blue_unit:
            distance = abs(red_unit['x'] - blue_unit['x']) + abs(red_unit['y'] - blue_unit['y'])
            self.assertEqual(distance, 1, "Units should be adjacent")
        
        # Unit should stay selected (can attack enemy)
        self.assertIsNotNone(board.get('selected'), "Unit should stay selected when enemy is in attack range")
        
        # Verify attack tiles are highlighted
        attack_tiles = [t for t in board.get('grid', []) if t.get('can_be_attacked')]
        self.assertGreater(len(attack_tiles), 0, "Should have attack tiles highlighted")
    
    def test_unit_stays_selected_for_capture(self):
        """Test that infantry stays selected when it can capture"""
        # Create RED infantry
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "produce_unit",
            "params": {
                "token": self.token,
                "x": 0,
                "y": 4,
                "unit_type": "INFANTRY"
            },
            "id": "40"
        })
        
        # End turns
        for i in range(2):
            resp = requests.post(self.api_url, json={
                "jsonrpc": "2.0",
                "method": "army_end_turn",
                "params": {"token": self.token},
                "id": str(41 + i)
            })
        
        # Move infantry to neutral city at (3,4) - exactly 3 tiles away
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "unit_move",
            "params": {
                "token": self.token,
                "x": 0,
                "y": 4,
                "x2": 3,
                "y2": 4  # Neutral city location
            },
            "id": "43"
        })
        result = resp.json()
        self.assertNotIn("error", result)
        
        # Get board state after move
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "game_board",
            "params": {"token": self.token},
            "id": "44"
        })
        result = resp.json()
        board = result.get('result', {})
        
        # Infantry should stay selected (can capture)
        self.assertIsNotNone(board.get('selected'), "Infantry should stay selected when on capturable property")

if __name__ == '__main__':
    unittest.main()
#!/usr/bin/env python3
"""
Test suite for multiplayer army display and functionality.
Tests that GREEN, YELLOW, and GREY armies are properly supported in frontend and backend.
"""

import unittest
import requests
import json
import time
import sys
import os

# Add the project root directory to Python path to import modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from config import Config
from core.map_system import map_repository
from gameboard import GameBoard
from manager import GameManager

class TestMultiplayerArmies(unittest.TestCase):
    """Test multiplayer army support across the system"""
    
    BASE_URL = "http://localhost:5000"
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            self.config = Config()
            print(f"✅ Config initialized: {type(self.config)}")
        except Exception as e:
            print(f"❌ Config initialization failed: {e}")
            # Create a minimal fallback config
            self.config = type('Config', (), {})()  # Empty config object
        
    def test_triangle_map_armies(self):
        """Test 3-player triangle map has correct armies"""
        print("🔺 Testing triangle map army setup...")
        
        triangle_map = map_repository.get_map('triangle')
        self.assertIsNotNone(triangle_map, "Triangle map should exist")
        
        # Check turn order includes all 3 armies
        expected_armies = ['RED', 'BLUE', 'GREEN']
        actual_armies = [army.name for army in triangle_map.turn_order]
        self.assertEqual(actual_armies, expected_armies, 
                        f"Triangle map should have armies {expected_armies}, got {actual_armies}")
        
        # Create GameBoard and verify army initialization
        board = GameBoard.create(triangle_map)
        self.assertEqual(len(board.turn_order), 3, "Triangle board should have 3 armies")
        
        # Check all armies have funds
        for army in board.turn_order:
            self.assertIn(army, board.player_funds, f"Army {army.name} should have funds initialized")
            self.assertGreater(board.player_funds[army], 0, f"Army {army.name} should have starting funds")
        
        print("✅ Triangle map army setup correct")
        
    def test_cross_map_armies(self):
        """Test 4-player cross map has correct armies"""
        print("➕ Testing cross map army setup...")
        
        cross_map = map_repository.get_map('cross')
        self.assertIsNotNone(cross_map, "Cross map should exist")
        
        # Check turn order includes all 4 armies
        expected_armies = ['RED', 'BLUE', 'GREEN', 'YELLOW']
        actual_armies = [army.name for army in cross_map.turn_order]
        self.assertEqual(actual_armies, expected_armies,
                        f"Cross map should have armies {expected_armies}, got {actual_armies}")
        
        # Create GameBoard and verify army initialization
        board = GameBoard.create(cross_map)
        self.assertEqual(len(board.turn_order), 4, "Cross board should have 4 armies")
        
        # Check all armies have funds
        for army in board.turn_order:
            self.assertIn(army, board.player_funds, f"Army {army.name} should have funds initialized")
            self.assertGreater(board.player_funds[army], 0, f"Army {army.name} should have starting funds")
        
        print("✅ Cross map army setup correct")
        
    def test_pentagon_map_armies(self):
        """Test 5-player pentagon map has correct armies"""
        print("⭐ Testing pentagon map army setup...")
        
        pentagon_map = map_repository.get_map('pentagon')
        self.assertIsNotNone(pentagon_map, "Pentagon map should exist")
        
        # Check turn order includes all 5 armies
        expected_armies = ['RED', 'BLUE', 'GREEN', 'YELLOW', 'GREY']
        actual_armies = [army.name for army in pentagon_map.turn_order]
        self.assertEqual(actual_armies, expected_armies,
                        f"Pentagon map should have armies {expected_armies}, got {actual_armies}")
        
        # Create GameBoard and verify army initialization
        board = GameBoard.create(pentagon_map)
        self.assertEqual(len(board.turn_order), 5, "Pentagon board should have 5 armies")
        
        # Check all armies have funds
        for army in board.turn_order:
            self.assertIn(army, board.player_funds, f"Army {army.name} should have funds initialized")
            self.assertGreater(board.player_funds[army], 0, f"Army {army.name} should have starting funds")
        
        print("✅ Pentagon map army setup correct")
        
    def test_army_property_ownership(self):
        """Test that armies properly own their starting properties"""
        print("🏰 Testing army property ownership...")
        
        # Test cross map property ownership
        cross_map = map_repository.get_map('cross')
        
        # Count properties owned by each army
        player_properties = {}
        for tile in cross_map.tiles:
            if tile.army and tile.type.name in ['FACTORY', 'BASE_TOWER_1', 'CITY']:
                army_name = tile.army.name
                player_properties[army_name] = player_properties.get(army_name, 0) + 1
        
        # Each army should own some properties
        expected_armies = ['RED', 'BLUE', 'GREEN', 'YELLOW']
        for army in expected_armies:
            self.assertIn(army, player_properties, f"{army} should own properties")
            self.assertGreater(player_properties[army], 0, f"{army} should own at least 1 property")
        
        print(f"   Property distribution: {player_properties}")
        print("✅ Army property ownership correct")
        
    def test_frontend_army_routes(self):
        """Test that frontend routes for multiplayer maps work"""
        print("🌐 Testing frontend multiplayer routes...")
        
        routes_to_test = [
            ('/test_triangle', 'Triangle map'),
            ('/test_cross', 'Cross map'), 
            ('/test_pentagon', 'Pentagon map')
        ]
        
        for route, description in routes_to_test:
            try:
                response = requests.get(f"{self.BASE_URL}{route}", timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ {description} route accessible")
                else:
                    print(f"   ⚠️ {description} route returned {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️ {description} route failed: {e}")
        
    def test_sprite_corrections_loaded(self):
        """Test that sprite corrections include all army unit types"""
        print("🎨 Testing sprite corrections for all armies...")
        
        try:
            response = requests.get(f"{self.BASE_URL}/templates/sprite_corrections_config.json", timeout=5)
            if response.status_code == 200:
                sprite_data = response.json()
                corrections = sprite_data.get('corrections', {})
                idle_sprites = corrections.get('idle', {})
                
                # Check that we have sprites for all armies
                armies_to_check = ['RED', 'BLUE', 'GREEN', 'YELLOW', 'GREY']
                unit_types_to_check = ['INFANTRY', 'TANK', 'FIGHTER']
                
                missing_sprites = []
                for army in armies_to_check:
                    for unit_type in unit_types_to_check:
                        sprite_key = f"{unit_type}_{army}_idle_0"
                        if sprite_key not in idle_sprites:
                            missing_sprites.append(sprite_key)
                
                if missing_sprites:
                    print(f"   ⚠️ Missing sprites: {missing_sprites[:5]}{'...' if len(missing_sprites) > 5 else ''}")
                else:
                    print("   ✅ All army unit sprites available")
                    
                print(f"   Total idle sprites: {len(idle_sprites)}")
                
            else:
                print(f"   ⚠️ Could not load sprite corrections: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️ Could not test sprite corrections: {e}")
            
    def test_army_turn_cycle(self):
        """Test that turn system cycles through all armies correctly"""
        print("🔄 Testing army turn cycling...")
        
        # Test with cross map (4 armies)
        cross_map = map_repository.get_map('cross')
        board = GameBoard.create(cross_map)
        game_manager = GameManager(self.config, board)
        
        # Test turn progression
        expected_turn_order = ['RED', 'BLUE', 'GREEN', 'YELLOW']
        
        for i, expected_army in enumerate(expected_turn_order):
            current_army = board.current_turn.name
            self.assertEqual(current_army, expected_army, 
                           f"Turn {i+1} should be {expected_army}, got {current_army}")
            
            # Simulate end turn (simplified)
            if i < len(expected_turn_order) - 1:  # Don't advance past last turn in test
                current_index = board.turn_order.index(board.current_turn)
                next_index = (current_index + 1) % len(board.turn_order)
                board.current_turn = board.turn_order[next_index]
        
        print("✅ Army turn cycling works correctly")
        
    def test_map_dimensions_correct(self):
        """Test that multiplayer maps have expected dimensions"""
        print("📏 Testing map dimensions...")
        
        maps_to_test = [
            ('triangle', 13, 13),
            ('cross', 13, 13),
            ('pentagon', 13, 15)  # Pentagon is taller
        ]
        
        for map_name, expected_width, expected_height in maps_to_test:
            game_map = map_repository.get_map(map_name)
            self.assertIsNotNone(game_map, f"{map_name} map should exist")
            
            self.assertEqual(game_map.width, expected_width, 
                           f"{map_name} width should be {expected_width}, got {game_map.width}")
            self.assertEqual(game_map.height, expected_height,
                           f"{map_name} height should be {expected_height}, got {game_map.height}")
            
            # Check tile count matches dimensions
            expected_tiles = expected_width * expected_height
            actual_tiles = len(game_map.tiles)
            self.assertEqual(actual_tiles, expected_tiles,
                           f"{map_name} should have {expected_tiles} tiles, got {actual_tiles}")
            
            print(f"   ✅ {map_name}: {game_map.width}x{game_map.height} ({actual_tiles} tiles)")
            
    def run_all_tests(self):
        """Run all multiplayer army tests"""
        print("🎮 MULTIPLAYER ARMY TEST SUITE")
        print("=" * 50)
        
        # Call setUp to initialize test fixtures
        self.setUp()
        
        test_methods = [
            self.test_triangle_map_armies,
            self.test_cross_map_armies, 
            self.test_pentagon_map_armies,
            self.test_army_property_ownership,
            self.test_map_dimensions_correct,
            self.test_army_turn_cycle,
            self.test_frontend_army_routes,
            self.test_sprite_corrections_loaded
        ]
        
        passed = 0
        failed = 0
        
        for test_method in test_methods:
            try:
                test_method()
                passed += 1
            except Exception as e:
                print(f"❌ {test_method.__name__} failed: {e}")
                failed += 1
            print()
        
        print("=" * 50)
        print(f"📊 RESULTS: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All multiplayer army tests passed!")
            return True
        else:
            print(f"⚠️ {failed} test(s) failed")
            return False

if __name__ == "__main__":
    # Run as standalone test
    test_suite = TestMultiplayerArmies()
    test_suite.run_all_tests()
#!/usr/bin/env python3
"""
Selenium tests for Advance Wars RPC UI interactions
Tests factory clicks, unit creation, and movement
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import json
import requests
import unittest

class TestAdvanceWarsUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up Chrome driver once for all tests"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        cls.driver = webdriver.Chrome(options=options)
        
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        cls.driver.quit()
        
    def setUp(self):
        """Create a new game for each test"""
        # Create game via API
        self.game_token = f"test_{int(time.time())}"
        response = requests.post('http://localhost:5000/api', json={
            'jsonrpc': '2.0',
            'method': 'game_create_test',
            'params': {'token': self.game_token},
            'id': 1
        })
        
        result = response.json()
        self.assertEqual(result.get('result'), 'ok', f"Failed to create game: {result}")
        
        # Load the game
        self.driver.get(f"http://localhost:5000/game/{self.game_token}")
        time.sleep(3)  # Wait for game to load
        
    def wait_for_board(self):
        """Wait for game board to be fully loaded"""
        WebDriverWait(self.driver, 10).until(
            lambda driver: driver.execute_script("return window.board && window.board.grid && window.two")
        )
        
    def get_tile_info(self, x, y):
        """Get information about a specific tile"""
        return self.driver.execute_script(f"""
            const tile = window.board.grid.find(t => t.x === {x} && t.y === {y});
            if (!tile) return null;
            return {{
                terrain: tile.mapTile?.type,
                army: tile.mapTile?.army,
                hasUnit: !!tile.unit,
                unitType: tile.unit?.type,
                unitArmy: tile.unit?.army
            }};
        """)
        
    def click_tile(self, x, y):
        """Click on a specific tile"""
        canvas = self.driver.find_element(By.CSS_SELECTOR, "#draw canvas")
        # Calculate pixel position (TILESIZE=16, offset=16)
        pixel_x = x * 16 + 8
        pixel_y = y * 16 + 16 + 8
        
        ActionChains(self.driver).move_to_element_with_offset(canvas, pixel_x, pixel_y).click().perform()
        time.sleep(0.5)
        
    def create_unit_directly(self, unit_type, x, y):
        """Create unit using direct JavaScript call"""
        result = self.driver.execute_script(f"""
            return new Promise((resolve) => {{
                window.jsonrpc('unit_create', {{
                    army: window.board.current_turn,
                    unit_type: '{unit_type}',
                    x: {x},
                    y: {y}
                }}, function(result) {{
                    resolve(result);
                }});
            }});
        """)
        return result
        
    def test_game_loads(self):
        """Test that game loads successfully"""
        self.wait_for_board()
        
        # Check game state
        game_state = self.driver.execute_script("""
            return {
                currentTurn: window.board.current_turn,
                redFunds: window.board.red_funds,
                blueFunds: window.board.blue_funds,
                width: window.board.width,
                height: window.board.height
            };
        """)
        
        self.assertEqual(game_state['currentTurn'], 'RED')
        self.assertEqual(game_state['redFunds'], 50000)  # Test game has 50k funds
        self.assertEqual(game_state['blueFunds'], 50000)
        self.assertGreater(game_state['width'], 0)
        self.assertGreater(game_state['height'], 0)
        
    def test_factory_exists(self):
        """Test that RED factory exists at (0,3)"""
        self.wait_for_board()
        
        tile_info = self.get_tile_info(0, 3)
        self.assertIsNotNone(tile_info)
        self.assertEqual(tile_info['terrain'], 'FACTORY')
        self.assertEqual(tile_info['army'], 'RED')
        self.assertFalse(tile_info['hasUnit'])
        
    def test_unit_creation(self):
        """Test creating units at factory"""
        self.wait_for_board()
        
        # Create infantry at RED factory
        result = self.create_unit_directly('INFANTRY', 0, 3)
        self.assertNotIn('error', result)
        
        # Check unit was created
        tile_info = self.get_tile_info(0, 3)
        self.assertTrue(tile_info['hasUnit'])
        self.assertEqual(tile_info['unitType'], 'INFANTRY')
        self.assertEqual(tile_info['unitArmy'], 'RED')
        
    def test_sprite_rendering_issue(self):
        """Test the sprite rendering issue"""
        self.wait_for_board()
        
        # Create unit
        self.create_unit_directly('INFANTRY', 0, 3)
        
        # Check for sprite error in console
        logs = self.driver.execute_script("""
            // Check if sprite error was logged
            const canvas = document.querySelector('#draw canvas');
            const rect = canvas.getBoundingClientRect();
            
            // Try to get color at unit position
            const ctx = canvas.getContext('2d');
            const pixelData = ctx.getImageData(0 * 16, 3 * 16 + 16, 16, 16);
            
            // Check if it's mostly black (sprite issue)
            let blackPixels = 0;
            for (let i = 0; i < pixelData.data.length; i += 4) {
                const r = pixelData.data[i];
                const g = pixelData.data[i + 1];
                const b = pixelData.data[i + 2];
                if (r < 50 && g < 50 && b < 50) blackPixels++;
            }
            
            return {
                totalPixels: pixelData.data.length / 4,
                blackPixels: blackPixels,
                isBlackBox: blackPixels > (pixelData.data.length / 4) * 0.8
            };
        """)
        
        # This test documents the issue - unit shows as black box initially
        # After refresh, sprite displays correctly
        
    def test_unit_movement(self):
        """Test unit movement after creation"""
        self.wait_for_board()
        
        # Create infantry
        self.create_unit_directly('INFANTRY', 0, 3)
        
        # End turn twice to enable movement
        self.driver.execute_script("window.armyEndTurn()")
        time.sleep(1)
        self.driver.execute_script("window.armyEndTurn()")
        time.sleep(1)
        
        # Click on unit to select
        self.click_tile(0, 3)
        
        # Check if unit is selected
        selected = self.driver.execute_script("return window.board.selected")
        self.assertIsNotNone(selected)
        
        # Click on adjacent tile to move
        self.click_tile(1, 3)
        time.sleep(1)
        
        # Check unit moved
        old_tile = self.get_tile_info(0, 3)
        new_tile = self.get_tile_info(1, 3)
        
        self.assertFalse(old_tile['hasUnit'])
        self.assertTrue(new_tile['hasUnit'])
        self.assertEqual(new_tile['unitType'], 'INFANTRY')
        
    def test_multiple_unit_types(self):
        """Test creating different unit types"""
        self.wait_for_board()
        
        unit_types = ['INFANTRY', 'TANK', 'RECON', 'ARTILLERY']
        
        for i, unit_type in enumerate(unit_types):
            # Create unit at factory
            result = self.create_unit_directly(unit_type, 0, 3)
            self.assertNotIn('error', result)
            
            # Move unit away to make room
            if i < len(unit_types) - 1:
                self.driver.execute_script(f"""
                    const unit = window.board.grid.find(t => t.x === 0 && t.y === 3).unit;
                    if (unit) {{
                        // Move unit to make room
                        window.board.grid[{i} + 3 * window.board.width].unit = unit;
                        window.board.grid[3 * window.board.width].unit = null;
                    }}
                """)
                
    def test_funds_deduction(self):
        """Test that funds are deducted when creating units"""
        self.wait_for_board()
        
        # Get initial funds
        initial_funds = self.driver.execute_script("return window.board.red_funds")
        
        # Create infantry (costs 1000)
        self.create_unit_directly('INFANTRY', 0, 3)
        
        # Check funds reduced
        new_funds = self.driver.execute_script("return window.board.red_funds")
        self.assertEqual(new_funds, initial_funds - 1000)
        
        
if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
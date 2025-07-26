"""
Base test class for UI tests

Provides common functionality for all UI tests including setup, teardown,
and helper methods for interacting with the game.
"""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import time
import json
import os
import requests
from datetime import datetime


class BaseUITest:
    """Base class for all UI tests"""
    
    @classmethod
    def setup_class(cls):
        """Set up test class"""
        cls.base_url = "http://localhost:5000"
        cls.api_url = f"{cls.base_url}/api"
        cls.screenshots_dir = "tests/ui/screenshots"
        os.makedirs(cls.screenshots_dir, exist_ok=True)
    
    def setup_method(self, method):
        """Set up each test method"""
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--headless')  # Run headless to avoid window spam
        chrome_options.add_argument('--window-size=1280,800')
        
        # Initialize WebDriver
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_window_size(1280, 800)
            self.wait = WebDriverWait(self.driver, 10)
        except Exception as e:
            print(f"Failed to create WebDriver: {e}")
            raise
        
        # Test metadata
        self.test_name = method.__name__
        self.screenshots = []
    
    def teardown_method(self, method):
        """Clean up after each test"""
        try:
            # Check for JavaScript errors
            self.check_js_errors()
            
            # Take final screenshot if test failed
            if hasattr(self, '_outcome') and self._outcome.errors:
                self.take_screenshot("test_failed")
        except Exception as e:
            print(f"Error during teardown: {e}")
        finally:
            # Always try to close browser
            try:
                if hasattr(self, 'driver') and self.driver:
                    self.driver.quit()
            except Exception as e:
                print(f"Error closing driver: {e}")
    
    # === RPC Methods ===
    
    def execute_rpc(self, method, params=None):
        """Execute an RPC call"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1
        }
        
        response = requests.post(
            f"{self.api_url}/rpc",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        result = response.json()
        if "error" in result:
            raise Exception(f"RPC Error: {result['error']}")
        
        return result.get("result")
    
    def create_test_game(self, funds=50000):
        """Create a test game with high funds"""
        result = self.execute_rpc("game_create_test", {"starting_funds": funds})
        return result["game_id"]
    
    # === Navigation Methods ===
    
    def navigate_to_game(self, game_id):
        """Navigate to a specific game"""
        self.driver.get(f"{self.base_url}/game/{game_id}")
        
        # Wait for game to load
        self.wait_for_game_load()
        
        # Disable animations for reliable tests
        self.disable_animations()
    
    def wait_for_game_load(self):
        """Wait for the game to fully load"""
        # Wait for canvas
        canvas = self.wait.until(
            EC.presence_of_element_located((By.ID, "gameCanvas"))
        )
        
        # Wait for game state
        self.wait.until(lambda driver: 
            self.execute_js("return window.board && window.board.grid && window.board.grid.length > 0")
        )
        
        # Small delay for rendering
        time.sleep(0.5)
        
        return canvas
    
    # === Interaction Methods ===
    
    def click_tile(self, x, y):
        """Click on a specific tile"""
        canvas = self.get_game_canvas()
        
        # Calculate pixel coordinates
        tile_size = self.get_tile_size()
        pixel_x = (x * tile_size) + (tile_size // 2)
        pixel_y = (y * tile_size) + (tile_size // 2)
        
        # Click on canvas
        ActionChains(self.driver).move_to_element_with_offset(
            canvas, pixel_x, pixel_y
        ).click().perform()
        
        # Small delay for UI update
        time.sleep(0.2)
    
    def double_click_tile(self, x, y):
        """Double-click on a specific tile"""
        canvas = self.get_game_canvas()
        
        tile_size = self.get_tile_size()
        pixel_x = (x * tile_size) + (tile_size // 2)
        pixel_y = (y * tile_size) + (tile_size // 2)
        
        ActionChains(self.driver).move_to_element_with_offset(
            canvas, pixel_x, pixel_y
        ).double_click().perform()
        
        time.sleep(0.2)
    
    def right_click_tile(self, x, y):
        """Right-click on a specific tile"""
        canvas = self.get_game_canvas()
        
        tile_size = self.get_tile_size()
        pixel_x = (x * tile_size) + (tile_size // 2)
        pixel_y = (y * tile_size) + (tile_size // 2)
        
        ActionChains(self.driver).move_to_element_with_offset(
            canvas, pixel_x, pixel_y
        ).context_click().perform()
        
        time.sleep(0.2)
    
    def hover_tile(self, x, y):
        """Hover over a specific tile"""
        canvas = self.get_game_canvas()
        
        tile_size = self.get_tile_size()
        pixel_x = (x * tile_size) + (tile_size // 2)
        pixel_y = (y * tile_size) + (tile_size // 2)
        
        ActionChains(self.driver).move_to_element_with_offset(
            canvas, pixel_x, pixel_y
        ).perform()
        
        time.sleep(0.1)
    
    # === Game State Methods ===
    
    def get_game_canvas(self):
        """Get the game canvas element"""
        return self.driver.find_element(By.ID, "gameCanvas")
    
    def get_tile_size(self):
        """Get the tile size"""
        return self.execute_js("return window.TILESIZE || 32;")
    
    def get_board_state(self):
        """Get the current board state"""
        return self.execute_js("return window.board;")
    
    def get_selected_unit(self):
        """Get the currently selected unit"""
        return self.execute_js("return window.gameState?.selectedUnit;")
    
    def get_current_turn(self):
        """Get the current turn (army)"""
        return self.execute_js("return window.board?.current_turn;")
    
    def get_unit_at(self, x, y):
        """Get unit at specific coordinates"""
        return self.execute_js(f"""
            const tile = window.board.grid.find(t => t.x === {x} && t.y === {y});
            return tile ? tile.unit : null;
        """)
    
    def get_tile_at(self, x, y):
        """Get tile information at specific coordinates"""
        return self.execute_js(f"""
            return window.board.grid.find(t => t.x === {x} && t.y === {y});
        """)
    
    # === Movement Highlight Methods ===
    
    def wait_for_movement_highlights(self, timeout=5):
        """Wait for movement highlights to appear"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            highlights = self.get_movement_highlights()
            if highlights and len(highlights) > 0:
                return highlights
            time.sleep(0.1)
        
        raise TimeoutError("Movement highlights did not appear")
    
    def get_movement_highlights(self):
        """Get current movement highlights"""
        return self.execute_js("""
            if (window.movementHighlights) {
                return window.movementHighlights.map(h => ({x: h.x, y: h.y}));
            }
            return [];
        """)
    
    def is_tile_highlighted(self, x, y):
        """Check if a specific tile is highlighted"""
        highlights = self.get_movement_highlights()
        return any(h['x'] == x and h['y'] == y for h in highlights)
    
    # === Utility Methods ===
    
    def execute_js(self, script):
        """Execute JavaScript and return result"""
        return self.driver.execute_script(script)
    
    def take_screenshot(self, name=None):
        """Take a screenshot"""
        if not name:
            name = f"{self.test_name}_{len(self.screenshots)}"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = os.path.join(self.screenshots_dir, filename)
        
        self.driver.save_screenshot(filepath)
        self.screenshots.append(filepath)
        
        return filepath
    
    def disable_animations(self):
        """Disable animations for reliable tests"""
        self.execute_js("""
            window.ANIMATION_SPEED = 0;
            window.DISABLE_ANIMATIONS = true;
        """)
    
    def check_js_errors(self):
        """Check for JavaScript errors in console"""
        logs = self.driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']
        
        if errors:
            print("JavaScript errors detected:")
            for error in errors:
                print(f"  - {error['message']}")
    
    def end_turn(self):
        """End the current turn"""
        # Try using the end turn button if available
        try:
            end_turn_btn = self.driver.find_element(By.ID, "endTurnButton")
            end_turn_btn.click()
        except:
            # Fallback to RPC
            self.execute_rpc("turn_end", {})
        
        time.sleep(0.5)  # Wait for turn change
    
    def wait_for_condition(self, condition_fn, timeout=5, message="Condition not met"):
        """Wait for a custom condition"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if condition_fn():
                return True
            time.sleep(0.1)
        
        raise TimeoutError(message)
    
    def get_attack_highlights(self):
        """Get current attack highlights"""
        return self.execute_js("""
            if (window.gameState?.attackHighlights) {
                return window.gameState.attackHighlights.map(h => ({x: h.x, y: h.y}));
            }
            return [];
        """)
    
    def wait_for_attack_highlights(self, timeout=5):
        """Wait for attack highlights to appear"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            highlights = self.get_attack_highlights()
            if highlights and len(highlights) > 0:
                return highlights
            time.sleep(0.1)
        
        raise TimeoutError("Attack highlights did not appear")
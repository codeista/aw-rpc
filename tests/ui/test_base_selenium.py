"""
Base Selenium Test Framework for AW-RPC UI Testing

This module provides the foundation for all UI tests including:
- WebDriver setup and teardown
- Common wait conditions
- Screenshot capabilities
- Game state extraction
"""

import os
import time
import json
import random
from typing import Dict, Any, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
import pytest
from PIL import Image
import io


class BaseSeleniumTest:
    """Base class for all Selenium UI tests"""
    
    # Configuration
    BASE_URL = "http://localhost:5000"
    WAIT_TIMEOUT = 10
    CANVAS_ID = "draw"
    TILE_SIZE = 16
    SCENE_Y_OFFSET = 16  # Two.js scene translation
    
    @classmethod
    def setup_class(cls):
        """Set up the test class - runs once per test class"""
        cls.ensure_server_running()
    
    def setup_method(self, method):
        """Set up each test method - runs before each test"""
        # Initialize WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # options.add_argument('--headless')  # Uncomment for headless mode
        
        # Enable browser logging
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1280, 800)
        self.wait = WebDriverWait(self.driver, self.WAIT_TIMEOUT)
        
        # Create a test game
        self.game_token = self.create_test_game()
        
        # Navigate to the game
        self.driver.get(f"{self.BASE_URL}/game/{self.game_token}")
        
        # Wait for canvas to be ready
        self.wait_for_canvas()
        
        # Force reload to get latest JS
        self.driver.refresh()
        
        # Wait for canvas to be ready again
        self.wait_for_canvas()
        
        # Disable animations for tests
        self.disable_animations()
        
        # Wait for initial render
        time.sleep(2)  # Give Two.js time to render
    
    def teardown_method(self, method):
        """Clean up after each test"""
        if hasattr(self, 'driver'):
            # Take screenshot on failure
            if hasattr(self, '_outcome') and not self._outcome.success:
                self.take_screenshot(f"failure_{method.__name__}")
            
            self.driver.quit()
    
    @classmethod
    def ensure_server_running(cls):
        """Ensure the game server is running"""
        try:
            response = requests.get(f"{cls.BASE_URL}/api/browse", timeout=2)
            if response.status_code != 200:
                pytest.skip("Game server not responding properly")
        except requests.exceptions.RequestException:
            pytest.skip("Game server is not running at http://localhost:5000")
    
    def create_test_game(self) -> str:
        """Create a test game via RPC and return the token"""
        # Generate unique token with timestamp and random number
        import random
        token = f"ui_test_{int(time.time())}_{random.randint(1000, 9999)}"
        
        response = requests.post(
            f"{self.BASE_URL}/api",
            json={
                "jsonrpc": "2.0",
                "method": "game_create_test",
                "params": {"token": token, "use_optimized": True},
                "id": 1
            }
        )
        
        result = response.json()
        if "error" in result:
            raise Exception(f"Failed to create test game: {result['error']}")
        
        # The result is the token itself, not a dict with 'token' key
        return token
    
    def wait_for_canvas(self):
        """Wait for the game canvas to be ready"""
        canvas = self.wait.until(
            EC.presence_of_element_located((By.ID, self.CANVAS_ID))
        )
        
        # Wait for Two.js to initialize
        self.wait.until(lambda driver: driver.execute_script(
            "return window.two && window.two.scene !== undefined"
        ))
        
        return canvas
    
    def get_canvas(self):
        """Get the game canvas element"""
        return self.driver.find_element(By.ID, self.CANVAS_ID)
    
    def click_tile(self, x: int, y: int):
        """Click on a specific tile coordinate"""
        canvas = self.get_canvas()
        
        # Calculate canvas pixel coordinates
        # Note: The game adds TILESIZE offset in the tileAt function
        canvas_x = x * self.TILE_SIZE + (self.TILE_SIZE // 2)
        canvas_y = y * self.TILE_SIZE + (self.TILE_SIZE // 2) + self.TILE_SIZE
        
        # Perform the click
        ActionChains(self.driver).move_to_element_with_offset(
            canvas, canvas_x, canvas_y
        ).click().perform()
        
        # Small delay for action to register
        time.sleep(0.1)
    
    def double_click_tile(self, x: int, y: int):
        """Double-click on a specific tile coordinate"""
        canvas = self.get_canvas()
        
        canvas_x = x * self.TILE_SIZE + (self.TILE_SIZE // 2)
        canvas_y = y * self.TILE_SIZE + (self.TILE_SIZE // 2) + self.TILE_SIZE
        
        ActionChains(self.driver).move_to_element_with_offset(
            canvas, canvas_x, canvas_y
        ).double_click().perform()
        
        time.sleep(0.1)
    
    def right_click_tile(self, x: int, y: int):
        """Right-click on a specific tile coordinate"""
        canvas = self.get_canvas()
        
        canvas_x = x * self.TILE_SIZE + (self.TILE_SIZE // 2)
        canvas_y = y * self.TILE_SIZE + (self.TILE_SIZE // 2) + self.TILE_SIZE
        
        ActionChains(self.driver).move_to_element_with_offset(
            canvas, canvas_x, canvas_y
        ).context_click().perform()
        
        time.sleep(0.1)
    
    def ctrl_click_tile(self, x: int, y: int):
        """Ctrl+Click on a specific tile coordinate"""
        canvas = self.get_canvas()
        
        canvas_x = x * self.TILE_SIZE + (self.TILE_SIZE // 2)
        canvas_y = y * self.TILE_SIZE + (self.TILE_SIZE // 2) + self.TILE_SIZE
        
        ActionChains(self.driver).move_to_element_with_offset(
            canvas, canvas_x, canvas_y
        ).key_down('\ue009').click().key_up('\ue009').perform()  # \ue009 is CONTROL key
        
        time.sleep(0.1)
    
    def get_game_state(self) -> Dict[str, Any]:
        """Get the current game state via JavaScript"""
        return self.driver.execute_script("""
            return {
                selected: window.board?.selected,
                currentTurn: window.board?.current_turn,
                movementHighlights: window.movementHighlights?.length || 0,
                attackHighlights: window.gameState?.attackHighlights?.length || 0,
                transportHighlights: window.transportHighlights?.length || 0,
                selectedUnit: window.gameState?.selectedUnit,
                board: {
                    width: window.board?.width,
                    height: window.board?.height,
                    currentTurn: window.board?.current_turn,
                    redFunds: window.board?.red_funds,
                    blueFunds: window.board?.blue_funds
                }
            };
        """)
    
    def get_movement_highlights(self) -> list:
        """Get the current movement highlight positions"""
        return self.driver.execute_script("""
            return window.movementHighlights || [];
        """)
    
    def get_attack_highlights(self) -> list:
        """Get the current attack highlight positions"""
        return self.driver.execute_script("""
            return window.gameState?.attackHighlights || [];
        """)
    
    def wait_for_highlights(self, highlight_type: str = "movement", timeout: int = 3):
        """Wait for highlights to appear"""
        def check_highlights(driver):
            state = self.get_game_state()
            if highlight_type == "movement":
                return state.get("movementHighlights", 0) > 0
            elif highlight_type == "attack":
                return state.get("attackHighlights", 0) > 0
            elif highlight_type == "transport":
                return state.get("transportHighlights", 0) > 0
            return False
        
        try:
            WebDriverWait(self.driver, timeout).until(check_highlights)
            return True
        except TimeoutException:
            return False
    
    def wait_for_no_highlights(self, timeout: int = 3):
        """Wait for all highlights to be cleared"""
        def check_no_highlights(driver):
            state = self.get_game_state()
            return (state.get("movementHighlights", 0) == 0 and
                    state.get("attackHighlights", 0) == 0 and
                    state.get("transportHighlights", 0) == 0)
        
        try:
            WebDriverWait(self.driver, timeout).until(check_no_highlights)
            return True
        except TimeoutException:
            return False
    
    def take_screenshot(self, name: str = None):
        """Take a screenshot of the current state"""
        if not name:
            name = f"screenshot_{int(time.time())}"
        
        # Ensure screenshots directory exists
        screenshots_dir = "/home/box/Documents/aw-rpc/tests/ui/screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        
        filepath = os.path.join(screenshots_dir, f"{name}.png")
        self.driver.save_screenshot(filepath)
        return filepath
    
    def capture_canvas(self) -> Image.Image:
        """Capture just the canvas as a PIL Image"""
        canvas = self.get_canvas()
        png_data = canvas.screenshot_as_png
        return Image.open(io.BytesIO(png_data))
    
    def find_unit_at(self, x: int, y: int) -> Optional[Dict[str, Any]]:
        """Find unit at specific tile coordinates"""
        return self.driver.execute_script("""
            const x = arguments[0];
            const y = arguments[1];
            if (!window.board || !window.board.grid) return null;
            
            const tile = window.board.grid.find(t => t.x === x && t.y === y);
            return tile?.unit || null;
        """, x, y)
    
    def get_tile_info(self, x: int, y: int) -> Optional[Dict[str, Any]]:
        """Get complete tile information"""
        return self.driver.execute_script("""
            const x = arguments[0];
            const y = arguments[1];
            if (!window.board || !window.board.grid) return null;
            
            return window.board.grid.find(t => t.x === x && t.y === y) || null;
        """, x, y)
    
    def end_turn(self):
        """End the current turn"""
        self.driver.execute_script("""
            window.armyEndTurn();
        """)
        time.sleep(0.5)  # Wait for turn transition
    
    def get_current_turn(self) -> str:
        """Get the current turn (RED or BLUE)"""
        state = self.get_game_state()
        return state.get('currentTurn', 'RED')
    
    def ensure_turn(self, army: str):
        """Ensure it's the specified army's turn"""
        current = self.get_current_turn()
        if current != army:
            self.end_turn()
            # Check again in case there are more than 2 players
            current = self.get_current_turn()
            if current != army:
                self.end_turn()
    
    def get_units_for_current_turn(self) -> list:
        """Get all units that can act on the current turn"""
        current_turn = self.get_current_turn()
        return self.get_unit_positions(current_turn)
    
    def wait_for_animation(self, timeout: float = 0.5):
        """Wait for any animations to complete"""
        # With animations disabled, we only need a short wait
        # for state updates
        time.sleep(timeout)
    
    def disable_animations(self):
        """Disable animations for faster and more reliable tests"""
        self.driver.execute_script("""
            // Disable animations if animation system exists
            if (window.animationSystem) {
                window.animationSystem.setEnabled(false);
                console.log('Animations disabled for testing');
            }
            
            // Also set localStorage to keep it disabled
            localStorage.setItem('animationsEnabled', 'false');
            
            // Disable any CSS transitions
            const style = document.createElement('style');
            style.textContent = `
                * {
                    transition: none !important;
                    animation: none !important;
                }
            `;
            document.head.appendChild(style);
        """)
    
    def get_unit_positions(self, army: str = None) -> list:
        """Get all unit positions, optionally filtered by army"""
        result = self.driver.execute_script("""
            const army = arguments[0];
            if (!window.board || !window.board.grid) return [];
            
            // Debug: log what we're finding
            const allTiles = window.board.grid.length;
            const tilesWithUnits = window.board.grid.filter(tile => tile.unit).length;
            console.log(`Board has ${allTiles} tiles, ${tilesWithUnits} have units`);
            
            return window.board.grid
                .filter(tile => tile.unit && (!army || tile.unit.army === army))
                .map(tile => ({
                    x: tile.x,
                    y: tile.y,
                    unit_type: tile.unit.type,
                    army: tile.unit.army,
                    hp: tile.unit.hp || tile.unit.status?.hp || 100
                }));
        """, army)
        
        # Also get economy data to verify
        economy = self.driver.execute_script("""
            return window.jsonrpc('get_army_economy', {})
                .then(result => result)
                .catch(error => ({error: error.message}));
        """)
        
        # Wait for promise
        time.sleep(0.5)
        
        print(f"Found {len(result)} units for {army or 'all armies'}")
        
        return result
    
    def verify_no_errors(self):
        """Check browser console for JavaScript errors"""
        logs = self.driver.get_log('browser')
        
        # Filter out 404s and circular JSON errors (known issues)
        real_errors = []
        for log in logs:
            if log['level'] == 'SEVERE':
                message = log['message']
                # Ignore 404s and known circular JSON warning
                if ('404' not in message and 
                    'Failed to load resource' not in message and
                    'Converting circular structure to JSON' not in message):
                    real_errors.append(log)
        
        if real_errors:
            error_messages = '\n'.join([log['message'] for log in real_errors])
            pytest.fail(f"JavaScript errors detected:\n{error_messages}")


# Example test to verify setup works
class TestBasicSetup(BaseSeleniumTest):
    """Test that basic setup and helpers work correctly"""
    
    def test_game_loads(self):
        """Test that a game loads successfully"""
        # Verify canvas exists
        canvas = self.get_canvas()
        assert canvas is not None
        
        # Verify game state
        state = self.get_game_state()
        assert state['board']['width'] > 0
        assert state['board']['height'] > 0
        assert state['currentTurn'] in ['RED', 'BLUE']
    
    def test_click_tile(self):
        """Test that clicking tiles works"""
        # Click on a tile
        self.click_tile(5, 5)
        
        # Small delay for click to register
        time.sleep(0.2)
        
        # Verify no JavaScript errors
        self.verify_no_errors()
    
    def test_screenshot_capture(self):
        """Test screenshot functionality"""
        filepath = self.take_screenshot("test_capture")
        assert os.path.exists(filepath)
        
        # Capture canvas
        canvas_img = self.capture_canvas()
        assert canvas_img.width > 0
        assert canvas_img.height > 0
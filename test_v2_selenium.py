#!/usr/bin/env python3
"""
Comprehensive Selenium tests for v2 game mechanics
Tests factory production, unit movement, combat, and multi-player features
"""

import time
import json
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests

class GameV2Tester:
    def __init__(self):
        self.driver = None
        self.base_url = "http://localhost:5000"
        self.test_results = []
        
    def setup(self):
        """Setup Chrome driver with options"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        self.driver = webdriver.Chrome(options=options)
        
    def teardown(self):
        """Clean up driver"""
        if self.driver:
            self.driver.quit()
            
    def log_test(self, test_name, passed, details=""):
        """Log test result"""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details
        }
        self.test_results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}: {details}")
        
    def create_test_game(self, game_id="selenium_test", players=None):
        """Create a test game via API"""
        if players is None:
            players = [
                {"name": "Player 1", "color": "Red", "sprite_color": "RED"},
                {"name": "Player 2", "color": "Blue", "sprite_color": "BLUE"},
                {"name": "Player 3", "color": "Green", "sprite_color": "GREEN"}
            ]
            
        resp = requests.post(f"{self.base_url}/api", json={
            "jsonrpc": "2.0",
            "method": "game_create_v2",
            "params": {
                "token": game_id,
                "map_name": "test",
                "players": players
            },
            "id": "1"
        })
        
        result = resp.json()
        if "error" in result:
            raise Exception(f"Failed to create game: {result['error']}")
            
        return game_id
        
    def wait_for_element(self, selector, timeout=10):
        """Wait for element to be present"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        
    def click_tile(self, x, y):
        """Click on a tile at given coordinates"""
        canvas = self.driver.find_element(By.ID, "game-canvas")
        # Each tile is 32x32 pixels
        offset_x = x * 32 + 16  # Center of tile
        offset_y = y * 32 + 16
        
        actions = ActionChains(self.driver)
        actions.move_to_element_with_offset(canvas, offset_x, offset_y)
        actions.click()
        actions.perform()
        time.sleep(0.5)  # Allow time for game state update
        
    def right_click_tile(self, x, y):
        """Right-click on a tile at given coordinates"""
        canvas = self.driver.find_element(By.ID, "game-canvas")
        offset_x = x * 32 + 16
        offset_y = y * 32 + 16
        
        actions = ActionChains(self.driver)
        actions.move_to_element_with_offset(canvas, offset_x, offset_y)
        actions.context_click()
        actions.perform()
        time.sleep(0.5)
        
    def hover_tile(self, x, y):
        """Hover over a tile to check info"""
        canvas = self.driver.find_element(By.ID, "game-canvas")
        # Need to account for canvas position on page
        # Move to element first, then offset
        offset_x = x * 32 + 16
        offset_y = y * 32 + 16
        
        actions = ActionChains(self.driver)
        actions.move_to_element(canvas).move_by_offset(offset_x - canvas.size['width']//2, offset_y - canvas.size['height']//2)
        actions.perform()
        time.sleep(0.3)
        
    def get_tile_info(self):
        """Get the current tile info text"""
        try:
            info_elem = self.driver.find_element(By.ID, "tile-info")
            return info_elem.text
        except:
            return ""
            
    def get_current_turn(self):
        """Get current turn info"""
        try:
            turn_elem = self.driver.find_element(By.ID, "current-turn")
            return turn_elem.text
        except:
            return ""
            
    def click_end_turn(self):
        """Click the end turn button"""
        btn = self.driver.find_element(By.ID, "end-turn")
        btn.click()
        time.sleep(1)  # Allow time for turn change
        
    def select_unit_from_modal(self, unit_type):
        """Select a unit from production modal"""
        try:
            # Wait for modal to appear
            self.wait_for_element("#modal", timeout=2)
            
            # Select the unit type
            select = self.driver.find_element(By.ID, "unit-select")
            for option in select.find_elements(By.TAG_NAME, "option"):
                if unit_type.upper() in option.text:
                    option.click()
                    break
                    
            # Click create
            create_btn = self.driver.find_element(By.ID, "create")
            create_btn.click()
            time.sleep(0.5)
            return True
        except:
            return False
            
    def test_game_loads(self, game_id):
        """Test that game page loads correctly"""
        try:
            self.driver.get(f"{self.base_url}/game/{game_id}")
            
            # Wait for canvas
            canvas = self.wait_for_element("#game-canvas")
            
            # Wait for canvas to be properly sized (game needs to load)
            time.sleep(2)
            
            # Check canvas size
            width = canvas.get_attribute("width")
            height = canvas.get_attribute("height")
            
            self.log_test(
                "Game Page Loads",
                width == "384" and height == "320",  # 12x10 tiles * 32px
                f"Canvas size: {width}x{height}"
            )
            
            # Check UI elements
            elements_found = True
            for elem_id in ["current-turn", "day", "red-funds", "blue-funds", "end-turn"]:
                try:
                    self.driver.find_element(By.ID, elem_id)
                except:
                    elements_found = False
                    break
                    
            self.log_test("UI Elements Present", elements_found)
            
        except Exception as e:
            self.log_test("Game Page Loads", False, str(e))
            
    def test_factory_production(self, game_id):
        """Test unit production on factories"""
        try:
            self.driver.get(f"{self.base_url}/game/{game_id}")
            self.wait_for_element("#game-canvas")
            time.sleep(1)
            
            # Player 1's factory is at (0, 4)
            self.right_click_tile(0, 4)
            
            # Check if modal appeared
            modal_appeared = self.select_unit_from_modal("INFANTRY")
            self.log_test("Factory Production Modal", modal_appeared)
            
            if modal_appeared:
                # Check if unit was created
                time.sleep(0.5)
                self.hover_tile(0, 4)
                info = self.get_tile_info()
                unit_created = "INFANTRY" in info
                self.log_test(
                    "Unit Creation", 
                    unit_created,
                    f"Tile info after creation: {info}"
                )
            
        except Exception as e:
            self.log_test("Factory Production", False, str(e))
            
    def test_unit_movement(self, game_id):
        """Test unit movement mechanics"""
        try:
            # First create a unit
            self.right_click_tile(0, 4)
            self.select_unit_from_modal("INFANTRY")
            time.sleep(0.5)
            
            # Try to move the unit (should fail - units can't move on creation turn)
            self.click_tile(0, 4)  # Select unit
            time.sleep(0.5)
            self.click_tile(1, 4)  # Try to move
            time.sleep(0.5)
            
            # Check unit is still at factory
            self.hover_tile(0, 4)
            info1 = self.get_tile_info()
            self.hover_tile(1, 4)
            info2 = self.get_tile_info()
            
            unit_didnt_move = "INFANTRY" in info1 and "INFANTRY" not in info2
            self.log_test(
                "Unit Can't Move on Creation Turn",
                unit_didnt_move,
                f"Factory: {info1}, Adjacent: {info2}"
            )
            
            # End turn and try again
            self.click_end_turn()
            self.click_end_turn()  # Player 2's turn
            self.click_end_turn()  # Player 3's turn (if 3 player game)
            
            # Back to Player 1 - now unit should be able to move
            current_turn = self.get_current_turn()
            
            # Select and move unit
            self.click_tile(0, 4)
            time.sleep(0.5)
            self.click_tile(1, 4)
            time.sleep(0.5)
            
            # Verify movement
            self.hover_tile(0, 4)
            info1 = self.get_tile_info()
            self.hover_tile(1, 4) 
            info2 = self.get_tile_info()
            
            unit_moved = "INFANTRY" not in info1 and "INFANTRY" in info2
            self.log_test(
                "Unit Movement After Turn",
                unit_moved,
                f"Factory: {info1}, Adjacent: {info2}"
            )
            
        except Exception as e:
            self.log_test("Unit Movement", False, str(e))
            
    def test_turn_order(self, game_id):
        """Test turn order for 3 players"""
        try:
            turns = []
            
            # Record initial turn
            turn = self.get_current_turn()
            turns.append(turn)
            
            # Cycle through turns
            for i in range(6):  # Go through 2 full cycles
                self.click_end_turn()
                turn = self.get_current_turn()
                turns.append(turn)
                
            # Check if we have proper cycling
            # Should see each player twice in order
            expected_pattern = turns[0:3] * 2  # First 3 turns repeated
            actual_pattern = turns[0:6]
            
            pattern_matches = all(
                expected_pattern[i] == actual_pattern[i] 
                for i in range(6)
            )
            
            self.log_test(
                "3-Player Turn Order",
                pattern_matches,
                f"Turn sequence: {' -> '.join(turns)}"
            )
            
        except Exception as e:
            self.log_test("Turn Order", False, str(e))
            
    def test_hover_info(self, game_id):
        """Test tile hover information"""
        try:
            # Test various tile types
            test_tiles = [
                (0, 0, "HQ"),      # Player 1 HQ
                (0, 4, "FACTORY"), # Player 1 Factory
                (5, 5, "PLAIN"),   # Empty plain
                (11, 0, "HQ"),     # Player 2 HQ
            ]
            
            all_correct = True
            details = []
            
            for x, y, expected in test_tiles:
                self.hover_tile(x, y)
                info = self.get_tile_info()
                contains_expected = expected in info
                details.append(f"({x},{y}): {info}")
                
                if not contains_expected:
                    all_correct = False
                    
            self.log_test(
                "Tile Hover Info",
                all_correct,
                " | ".join(details)
            )
            
        except Exception as e:
            self.log_test("Hover Info", False, str(e))
            
    def test_canvas_rendering(self, game_id):
        """Test that canvas is rendering properly"""
        try:
            # Take a screenshot to verify rendering
            canvas = self.driver.find_element(By.ID, "game-canvas")
            
            # Execute JavaScript to check if canvas has content
            has_content = self.driver.execute_script("""
                const canvas = document.getElementById('game-canvas');
                const ctx = canvas.getContext('2d');
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const data = imageData.data;
                
                // Check if there's any non-transparent content
                for (let i = 0; i < data.length; i += 4) {
                    if (data[i+3] > 0) {  // Alpha channel
                        return true;
                    }
                }
                return false;
            """)
            
            self.log_test(
                "Canvas Rendering",
                has_content,
                "Canvas has visible content" if has_content else "Canvas is empty"
            )
            
            # Check canvas dimensions
            width = int(canvas.get_attribute("width"))
            height = int(canvas.get_attribute("height"))
            expected_width = 384  # 12 * 32
            expected_height = 320  # 10 * 32
            
            self.log_test(
                "Canvas Dimensions",
                width == expected_width and height == expected_height,
                f"Size: {width}x{height} (expected {expected_width}x{expected_height})"
            )
            
        except Exception as e:
            self.log_test("Canvas Rendering", False, str(e))
            
    def test_production_ownership(self, game_id):
        """Test that only current player can produce units"""
        try:
            # Try to produce on Player 2's factory as Player 1
            self.right_click_tile(11, 5)  # Player 2's factory
            time.sleep(0.5)
            
            # Modal should not appear
            modal_present = False
            try:
                self.driver.find_element(By.ID, "modal")
                modal_style = self.driver.find_element(By.ID, "modal").get_attribute("style")
                modal_present = "display: flex" in modal_style or "display:flex" in modal_style
            except:
                pass
                
            self.log_test(
                "Can't Produce on Enemy Factory",
                not modal_present,
                "Modal did not appear for enemy factory"
            )
            
            # Now try on own factory
            self.right_click_tile(0, 4)
            time.sleep(0.5)
            
            try:
                modal = self.driver.find_element(By.ID, "modal")
                modal_style = modal.get_attribute("style")
                modal_present = "display: flex" in modal_style or "display:flex" in modal_style
                
                # Cancel the modal
                if modal_present:
                    cancel_btn = self.driver.find_element(By.ID, "cancel")
                    cancel_btn.click()
                    
            except:
                modal_present = False
                
            self.log_test(
                "Can Produce on Own Factory",
                modal_present,
                "Modal appeared for own factory"
            )
            
        except Exception as e:
            self.log_test("Production Ownership", False, str(e))
            
    def test_funds_display(self, game_id):
        """Test that funds are displayed and updated"""
        try:
            # Get initial funds
            red_funds_elem = self.driver.find_element(By.ID, "red-funds")
            initial_funds = int(red_funds_elem.text)
            
            self.log_test(
                "Initial Funds Display",
                initial_funds == 5000,
                f"Starting funds: {initial_funds}"
            )
            
            # Create a unit to spend funds
            self.right_click_tile(0, 4)
            self.select_unit_from_modal("INFANTRY")
            time.sleep(0.5)
            
            # Check funds decreased
            new_funds = int(red_funds_elem.text)
            funds_decreased = new_funds == initial_funds - 1000
            
            self.log_test(
                "Funds Update After Purchase",
                funds_decreased,
                f"Funds: {initial_funds} -> {new_funds}"
            )
            
        except Exception as e:
            self.log_test("Funds Display", False, str(e))
            
    def run_all_tests(self):
        """Run all tests"""
        print("=== Starting V2 Game Selenium Tests ===\n")
        
        try:
            self.setup()
            
            # Create a 3-player test game
            game_id = self.create_test_game()
            print(f"Created test game: {game_id}\n")
            
            # Run tests
            self.test_game_loads(game_id)
            self.test_hover_info(game_id)
            self.test_canvas_rendering(game_id)
            self.test_funds_display(game_id)
            self.test_factory_production(game_id)
            self.test_production_ownership(game_id)
            self.test_unit_movement(game_id)
            self.test_turn_order(game_id)
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            traceback.print_exc()
            
        finally:
            self.teardown()
            
        # Summary
        print("\n=== Test Summary ===")
        passed = sum(1 for r in self.test_results if r["passed"])
        total = len(self.test_results)
        print(f"Passed: {passed}/{total}")
        
        if passed < total:
            print("\nFailed tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['details']}")
                    
        return passed == total

if __name__ == "__main__":
    tester = GameV2Tester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
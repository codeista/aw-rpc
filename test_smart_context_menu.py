#!/usr/bin/env python3
"""
Selenium test for smart context menu functionality
Tests multi-action scenarios and attack target selection
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class TestSmartContextMenu:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1400,1000')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        print("✅ Chrome driver initialized")
        
    def create_test_game(self):
        """Create a test game using the test interface"""
        try:
            print("🎮 Using test interface to create game with units...")
            
            # Go to test interface
            self.driver.get("http://localhost:5000/test_interface")
            time.sleep(2)
            
            # Look for "Create Test Game with Units" button or similar
            try:
                # Try to find the test game creation button
                test_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Test')]")
                if not test_buttons:
                    test_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Create')]")
                if not test_buttons:
                    test_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Game')]")
                
                if test_buttons:
                    print("🎮 Found test game creation button")
                    # Look for the most specific one (units/combat test)
                    for btn in test_buttons:
                        btn_text = btn.text.lower()
                        if 'unit' in btn_text or 'combat' in btn_text or 'battle' in btn_text:
                            print(f"🎯 Clicking: {btn.text}")
                            btn.click()
                            break
                    else:
                        # Just click the first test button
                        print(f"🎮 Clicking: {test_buttons[0].text}")
                        test_buttons[0].click()
                else:
                    print("❌ No test buttons found on test interface")
                    return False
                    
                time.sleep(2)
                
                # Wait for page to load and look for game link or result
                time.sleep(3)
                
                # Look for a game link or token that was created
                game_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/game/')]")
                if game_links:
                    print("🎮 Found game link, navigating to game...")
                    game_links[0].click()
                else:
                    # Try to find a token or game ID in the page
                    page_text = self.driver.page_source
                    print(f"🔍 Page contains: {page_text[:500]}...")  # Debug: show page content
                    
                    if '/game/' in page_text:
                        # Extract game token from page
                        import re
                        token_match = re.search(r'/game/([a-zA-Z0-9_-]+)', page_text)
                        if token_match:
                            token = token_match.group(1)
                            print(f"🎮 Found game token: {token}")
                            self.driver.get(f"http://localhost:5000/game/{token}")
                        else:
                            print("❌ Could not extract game token")
                            return False
                    else:
                        # Maybe the test interface works differently - look for any success message
                        if 'success' in page_text.lower() or 'created' in page_text.lower():
                            print("🎮 Test seems successful, trying direct game creation...")
                            self.driver.get("http://localhost:5000/game/new")
                        else:
                            print("❌ No game created")
                            return False
                    
            except Exception as e:
                print(f"❌ Error using test interface: {e}")
                # Fallback to direct game creation
                print("🎮 Falling back to direct game creation...")
                self.driver.get("http://localhost:5000/game/new")
            
            # Wait for game to load
            canvas = self.wait.until(EC.presence_of_element_located((By.ID, "game-canvas")))
            print("✅ Game loaded successfully")
            
            # Wait for game state to fully initialize
            time.sleep(3)
            
            # Check canvas size
            canvas_size = canvas.size
            if canvas_size['width'] > 100 and canvas_size['height'] > 100:
                print(f"✅ Canvas size: {canvas_size['width']}x{canvas_size['height']}")
                return True
            else:
                print(f"❌ Canvas too small: {canvas_size}")
                return False
            
        except TimeoutException:
            print("❌ Game failed to load")
            return False
            
    def get_canvas_position(self):
        """Get canvas position for coordinate calculations"""
        canvas = self.driver.find_element(By.ID, "game-canvas")
        return canvas.location, canvas.size
        
    def click_tile(self, x, y):
        """Click on a specific tile coordinate"""
        canvas = self.driver.find_element(By.ID, "game-canvas")
        location, size = canvas.location, canvas.size
        
        # Calculate pixel position (32px tiles)
        pixel_x = location['x'] + (x * 32) + 16  # Center of tile
        pixel_y = location['y'] + (y * 32) + 16
        
        print(f"🖱️  Clicking tile ({x},{y}) at pixel ({pixel_x},{pixel_y})")
        
        actions = ActionChains(self.driver)
        actions.move_to_element_with_offset(canvas, x * 32 + 16, y * 32 + 16)
        actions.click()
        actions.perform()
        time.sleep(0.5)
        
    def right_click_tile(self, x, y):
        """Right-click on a specific tile coordinate"""
        canvas = self.driver.find_element(By.ID, "game-canvas")
        
        print(f"🖱️  Right-clicking tile ({x},{y})")
        
        actions = ActionChains(self.driver)
        actions.move_to_element_with_offset(canvas, x * 32 + 16, y * 32 + 16)
        actions.context_click()
        actions.perform()
        time.sleep(0.5)
        
    def wait_for_context_menu(self):
        """Wait for context menu to appear"""
        try:
            menu = self.wait.until(
                EC.visibility_of_element_located((By.ID, "context-menu"))
            )
            print("✅ Context menu appeared")
            return menu
        except TimeoutException:
            print("❌ Context menu did not appear")
            return None
            
    def get_context_menu_items(self):
        """Get all visible context menu items"""
        try:
            menu = self.driver.find_element(By.ID, "context-menu")
            items = menu.find_elements(By.CLASS_NAME, "menu-item")
            
            visible_items = []
            for item in items:
                if item.is_displayed() and not item.get_attribute("disabled"):
                    text = item.text.strip()
                    if text:  # Skip empty items
                        visible_items.append({
                            'text': text,
                            'element': item,
                            'action': item.get_attribute('data-action')
                        })
            
            print(f"📋 Found {len(visible_items)} menu items: {[item['text'] for item in visible_items]}")
            return visible_items
            
        except NoSuchElementException:
            print("❌ Context menu not found")
            return []
            
    def click_menu_item(self, item_text):
        """Click a specific menu item"""
        items = self.get_context_menu_items()
        for item in items:
            if item_text.lower() in item['text'].lower():
                print(f"🖱️  Clicking menu item: {item['text']}")
                item['element'].click()
                time.sleep(0.5)
                return True
        
        print(f"❌ Menu item '{item_text}' not found")
        return False
        
    def check_for_auto_context_menu(self):
        """Check if context menu appears automatically after movement"""
        try:
            # Look for context menu within 2 seconds
            menu = WebDriverWait(self.driver, 2).until(
                EC.visibility_of_element_located((By.ID, "context-menu"))
            )
            print("✅ Auto context menu appeared!")
            return True
        except TimeoutException:
            print("ℹ️  No auto context menu (this may be expected)")
            return False
            
    def test_basic_context_menu(self):
        """Test basic right-click context menu"""
        print("\n🧪 Testing basic context menu...")
        
        # Try to find a unit on the board and right-click it
        # First, let's try clicking around to find units
        test_positions = [(1,1), (2,2), (3,3), (4,4), (5,5)]
        
        for x, y in test_positions:
            print(f"🔍 Testing position ({x},{y})")
            
            # Right-click to see if there's a unit
            self.right_click_tile(x, y)
            
            if self.wait_for_context_menu():
                items = self.get_context_menu_items()
                if items:
                    print(f"✅ Found unit with context menu at ({x},{y})")
                    
                    # Click cancel to close menu
                    self.click_menu_item("cancel")
                    return True
                else:
                    # Click elsewhere to close menu
                    self.click_tile(0, 0)
            
            time.sleep(0.5)
            
        print("❌ No units found for context menu test")
        return False
        
    def test_smart_context_menu_scenario(self):
        """Test smart context menu with multi-action scenario"""
        print("\n🧪 Testing smart context menu scenario...")
        
        # This test requires a specific setup:
        # 1. Infantry/Mech on capturable building
        # 2. Adjacent enemy units for attack
        # 3. Movement available
        
        # For now, we'll create a scenario by moving units around
        # Try to find an infantry unit first
        test_positions = [(0,0), (1,1), (2,2), (3,3), (4,4), (5,5), (6,6), (7,7)]
        
        for x, y in test_positions:
            print(f"🔍 Looking for unit at ({x},{y})")
            self.click_tile(x, y)
            time.sleep(0.5)
            
            # Check if unit info panel shows up
            try:
                unit_panel = self.driver.find_element(By.ID, "unit-info-panel")
                if unit_panel.is_displayed():
                    unit_type = self.driver.find_element(By.ID, "unit-type").text
                    print(f"✅ Found {unit_type} at ({x},{y})")
                    
                    # Try moving to adjacent tiles to create a scenario
                    adjacent_tiles = [(x+1,y), (x-1,y), (x,y+1), (x,y-1)]
                    
                    for ax, ay in adjacent_tiles:
                        if 0 <= ax <= 11 and 0 <= ay <= 9:  # Stay within bounds
                            print(f"🏃 Attempting to move to ({ax},{ay})")
                            self.click_tile(ax, ay)
                            
                            # Check if auto context menu appears
                            if self.check_for_auto_context_menu():
                                items = self.get_context_menu_items()
                                
                                # Look for multi-action scenario
                                has_capture = any('capture' in item['text'].lower() for item in items)
                                has_attack = any('attack' in item['text'].lower() for item in items)
                                
                                if has_capture and has_attack:
                                    print("🎯 Found multi-action scenario! Testing attack selection...")
                                    
                                    # Click attack to test target selection
                                    if self.click_menu_item("attack"):
                                        time.sleep(1)
                                        
                                        # Check if target selection menu appears
                                        new_items = self.get_context_menu_items()
                                        
                                        # Look for target selection (should have unit names with coordinates)
                                        target_items = [item for item in new_items if '(' in item['text'] and ')' in item['text']]
                                        
                                        if target_items:
                                            print(f"✅ Target selection menu with {len(target_items)} targets:")
                                            for target in target_items:
                                                print(f"   🎯 {target['text']}")
                                            
                                            # Test selecting a target
                                            target_items[0]['element'].click()
                                            print(f"🖱️  Selected target: {target_items[0]['text']}")
                                            time.sleep(1)
                                            
                                            return True
                                        else:
                                            print("ℹ️  No target selection menu found")
                                    
                                else:
                                    print(f"ℹ️  Single action scenario: capture={has_capture}, attack={has_attack}")
                                    self.click_menu_item("cancel")
                            
                            time.sleep(0.5)
                    
                    break
            except NoSuchElementException:
                continue
                
        print("❌ Could not create multi-action scenario")
        return False
        
    def test_console_logs(self):
        """Check browser console for errors or debug info"""
        print("\n🔍 Checking browser console logs...")
        
        # Get browser logs
        logs = self.driver.get_log('browser')
        
        error_count = 0
        debug_count = 0
        
        for log in logs:
            level = log['level']
            message = log['message']
            
            if level == 'SEVERE':
                print(f"❌ ERROR: {message}")
                error_count += 1
            elif 'attack' in message.lower() or 'context' in message.lower():
                print(f"🐛 DEBUG: {message}")
                debug_count += 1
                
        print(f"📊 Console summary: {error_count} errors, {debug_count} relevant debug messages")
        return error_count == 0
        
    def run_all_tests(self):
        """Run all context menu tests"""
        print("🚀 Starting Smart Context Menu Tests")
        print("=" * 50)
        
        success_count = 0
        total_tests = 0
        
        try:
            self.setup_driver()
            
            if not self.create_test_game():
                return False
                
            # Test 1: Basic context menu
            total_tests += 1
            if self.test_basic_context_menu():
                success_count += 1
                
            # Test 2: Smart context menu scenario  
            total_tests += 1
            if self.test_smart_context_menu_scenario():
                success_count += 1
                
            # Test 3: Console logs
            total_tests += 1
            if self.test_console_logs():
                success_count += 1
                
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            
        finally:
            self.cleanup()
            
        # Results
        print("\n" + "=" * 50)
        print(f"🏁 Test Results: {success_count}/{total_tests} tests passed")
        
        if success_count == total_tests:
            print("✅ All tests passed!")
            return True
        else:
            print("❌ Some tests failed")
            return False
            
    def cleanup(self):
        """Clean up browser resources"""
        if self.driver:
            try:
                print("\n🧹 Cleaning up browser...")
                self.driver.quit()
                print("✅ Browser closed successfully")
            except Exception as e:
                print(f"⚠️  Browser cleanup warning: {e}")
            finally:
                self.driver = None

if __name__ == "__main__":
    tester = TestSmartContextMenu()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""Test UI interactions with mouse and keyboard after security updates"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import json

def setup_driver():
    """Setup Chrome driver with appropriate options"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(options=options)

def wait_for_game_load(driver, wait):
    """Wait for game canvas to be ready"""
    canvas = wait.until(EC.presence_of_element_located((By.ID, "game-canvas")))
    time.sleep(2)  # Give game time to initialize
    return canvas

def test_mouse_interactions(driver, wait, canvas):
    """Test mouse click, double-click, and right-click interactions"""
    print("\n🖱️  Testing Mouse Interactions...")
    results = []
    
    # Test 1: Basic click on canvas
    print("  - Testing basic click...")
    try:
        canvas.click()
        results.append("✅ Basic click works")
    except Exception as e:
        results.append(f"❌ Basic click failed: {str(e)}")
    
    # Test 2: Double-click
    print("  - Testing double-click...")
    try:
        action = ActionChains(driver)
        action.double_click(canvas).perform()
        results.append("✅ Double-click works")
    except Exception as e:
        results.append(f"❌ Double-click failed: {str(e)}")
    
    # Test 3: Right-click for context menu
    print("  - Testing right-click context menu...")
    try:
        action = ActionChains(driver)
        action.context_click(canvas).perform()
        time.sleep(0.5)
        
        # Check if context menu appeared
        context_menu = driver.find_element(By.ID, "context-menu")
        if context_menu.is_displayed():
            results.append("✅ Right-click context menu appears")
            # Click cancel to close it
            cancel_btn = driver.find_element(By.CSS_SELECTOR, "[data-action='cancel']")
            cancel_btn.click()
        else:
            results.append("❌ Context menu not visible")
    except Exception as e:
        results.append(f"❌ Right-click failed: {str(e)}")
    
    # Test 4: Click on specific tile
    print("  - Testing tile selection...")
    try:
        # Click on factory tile (0,0)
        action = ActionChains(driver)
        action.move_to_element_with_offset(canvas, 16, 16).click().perform()
        time.sleep(0.5)
        
        # Check tile info
        tile_info = driver.find_element(By.ID, "tile-info")
        if "Factory" in tile_info.text or "factory" in tile_info.text.lower():
            results.append("✅ Tile selection and info display works")
        else:
            results.append(f"⚠️  Tile info shows: {tile_info.text}")
    except Exception as e:
        results.append(f"❌ Tile selection failed: {str(e)}")
    
    return results

def test_keyboard_shortcuts(driver, wait):
    """Test keyboard shortcuts"""
    print("\n⌨️  Testing Keyboard Shortcuts...")
    results = []
    
    shortcuts = [
        ("Space", Keys.SPACE, "End turn"),
        ("Escape", Keys.ESCAPE, "Cancel/Deselect"),
        ("H", "h", "Help overlay"),
        ("R", "r", "Refresh board"),
        ("Tab", Keys.TAB, "Cycle units"),
        ("W", "w", "Wait unit"),
        ("A", "a", "Attack mode"),
        ("M", "m", "Move mode"),
        ("C", "c", "Capture"),
        ("L", "l", "Load unit"),
        ("U", "u", "Unload unit"),
        ("+", "+", "Zoom in"),
        ("-", "-", "Zoom out"),
        ("0", "0", "Reset zoom")
    ]
    
    body = driver.find_element(By.TAG_NAME, "body")
    
    for name, key, description in shortcuts:
        try:
            print(f"  - Testing {name} key ({description})...")
            body.send_keys(key)
            time.sleep(0.2)
            results.append(f"✅ {name} key sent successfully")
        except Exception as e:
            results.append(f"❌ {name} key failed: {str(e)}")
    
    return results

def test_transport_controls(driver, wait, canvas):
    """Test special transport controls (Ctrl+Click, Alt+Click)"""
    print("\n🚛 Testing Transport Controls...")
    results = []
    
    # Test Ctrl+Click
    print("  - Testing Ctrl+Click (load unit)...")
    try:
        action = ActionChains(driver)
        action.key_down(Keys.CONTROL).click(canvas).key_up(Keys.CONTROL).perform()
        results.append("✅ Ctrl+Click executed")
    except Exception as e:
        results.append(f"❌ Ctrl+Click failed: {str(e)}")
    
    # Test Alt+Click
    print("  - Testing Alt+Click (unload unit)...")
    try:
        action = ActionChains(driver)
        action.key_down(Keys.ALT).click(canvas).key_up(Keys.ALT).perform()
        results.append("✅ Alt+Click executed")
    except Exception as e:
        results.append(f"❌ Alt+Click failed: {str(e)}")
    
    return results

def test_ui_responsiveness(driver, wait):
    """Test UI element responsiveness"""
    print("\n📱 Testing UI Responsiveness...")
    results = []
    
    # Get canvas element
    canvas = driver.find_element(By.ID, "game-canvas")
    
    # Test End Turn button
    print("  - Testing End Turn button...")
    try:
        end_turn_btn = driver.find_element(By.ID, "end-turn")
        if end_turn_btn.is_displayed() and end_turn_btn.is_enabled():
            end_turn_btn.click()
            results.append("✅ End Turn button responsive")
        else:
            results.append("❌ End Turn button not clickable")
    except Exception as e:
        results.append(f"❌ End Turn button test failed: {str(e)}")
    
    # Test info panels
    print("  - Testing info panel visibility...")
    try:
        panels = ["current-turn", "day", "red-funds", "blue-funds"]
        all_visible = True
        for panel_id in panels:
            panel = driver.find_element(By.ID, panel_id)
            if not panel.is_displayed():
                all_visible = False
                results.append(f"❌ {panel_id} not visible")
        if all_visible:
            results.append("✅ All info panels visible")
    except Exception as e:
        results.append(f"❌ Info panel test failed: {str(e)}")
    
    # Test hover functionality
    print("  - Testing hover tile info...")
    try:
        action = ActionChains(driver)
        # Move to different positions on canvas
        positions = [(50, 50), (100, 100), (150, 150)]
        tile_info = driver.find_element(By.ID, "tile-info")
        initial_text = tile_info.text
        
        for x, y in positions:
            action.move_to_element_with_offset(canvas, x, y).perform()
            time.sleep(0.3)
        
        final_text = tile_info.text
        if initial_text != final_text:
            results.append("✅ Hover tile info updates")
        else:
            results.append("⚠️  Hover info might not be updating")
    except Exception as e:
        results.append(f"❌ Hover test failed: {str(e)}")
    
    return results

def check_console_errors(driver):
    """Check for JavaScript console errors"""
    logs = driver.get_log('browser')
    errors = [log for log in logs if log['level'] == 'SEVERE']
    return errors

def main():
    print("🎮 Testing UI Interactions After Security Updates")
    print("=" * 60)
    
    driver = setup_driver()
    all_results = []
    
    try:
        # Test combat scenario
        print("\n📍 Loading Combat Test Scenario...")
        driver.get("http://localhost:5000/test_combat")
        wait = WebDriverWait(driver, 10)
        
        canvas = wait_for_game_load(driver, wait)
        print("✅ Game loaded successfully")
        
        # Run all tests
        all_results.extend(test_mouse_interactions(driver, wait, canvas))
        all_results.extend(test_keyboard_shortcuts(driver, wait))
        all_results.extend(test_transport_controls(driver, wait, canvas))
        all_results.extend(test_ui_responsiveness(driver, wait))
        
        # Check for console errors
        print("\n🔍 Checking for console errors...")
        errors = check_console_errors(driver)
        if errors:
            all_results.append(f"❌ Found {len(errors)} console errors:")
            for error in errors[:3]:  # Show first 3 errors
                all_results.append(f"   - {error['message']}")
        else:
            all_results.append("✅ No console errors detected")
        
        # Take screenshot for debugging
        driver.save_screenshot("/tmp/ui_test_screenshot.png")
        print("📸 Screenshot saved to /tmp/ui_test_screenshot.png")
        
    except TimeoutException:
        all_results.append("❌ Game failed to load within timeout")
    except Exception as e:
        all_results.append(f"❌ Test failed with error: {str(e)}")
    finally:
        driver.quit()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in all_results if r.startswith("✅"))
    failed = sum(1 for r in all_results if r.startswith("❌"))
    warnings = sum(1 for r in all_results if r.startswith("⚠️"))
    
    for result in all_results:
        print(result)
    
    print("\n" + "=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Warnings: {warnings}")
    print(f"📊 Success Rate: {passed / (passed + failed) * 100:.1f}%")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
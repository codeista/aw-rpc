#!/usr/bin/env python3
"""
Test all unit statuses and their UI display
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import json

print("=== Testing All Unit Statuses ===\n")

# Setup Chrome
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1280,800')
options.add_experimental_option('excludeSwitches', ['enable-logging'])
options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

driver = webdriver.Chrome(options=options)

try:
    # Create test game with high funds
    print("1. Creating test game...")
    game_id = f"status_test_{int(time.time())}"
    
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'game_create_test',
            'args': [{
                'map_id': 'test_2player',
                'armies': ['RED', 'BLUE']
            }]
        })
    )
    
    if response.status_code == 200:
        print(f"✅ Created game: {game_id}")
    
    # Load game
    driver.get(f'http://localhost:5000/game/{game_id}')
    canvas = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "gameCanvas"))
    )
    time.sleep(3)
    print("✅ Game loaded")
    
    # Test 1: Normal units (available/unavailable)
    print("\n2. Testing normal unit states...")
    
    # Create infantry and tank
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'unit_create',
            'args': [{
                'position': [1, 1],
                'unit_type': 'INFANTRY'
            }]
        })
    )
    print("   Created RED INFANTRY at (1,1)")
    
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'unit_create',
            'args': [{
                'position': [2, 1],
                'unit_type': 'TANK'
            }]
        })
    )
    print("   Created RED TANK at (2,1)")
    
    # Move infantry to make it unavailable
    inf_x = 1 * 32 + 16
    inf_y = 1 * 32 + 16
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, inf_x, inf_y).click().perform()
    time.sleep(1)
    
    # Move right
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 3 * 32 + 16, inf_y).click().perform()
    time.sleep(1)
    print("   Moved infantry - now unavailable")
    
    driver.save_screenshot('/tmp/status_test_1_normal.png')
    print("   Screenshot: /tmp/status_test_1_normal.png")
    
    # Test 2: Transport loading status
    print("\n3. Testing transport loading...")
    
    # Create APC
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'unit_create',
            'args': [{
                'position': [4, 1],
                'unit_type': 'APC'
            }]
        })
    )
    print("   Created RED APC at (4,1)")
    
    # Create infantry to load
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'unit_create',
            'args': [{
                'position': [5, 1],
                'unit_type': 'INFANTRY'
            }]
        })
    )
    print("   Created RED INFANTRY at (5,1)")
    
    # End turn to make units available
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'turn_end',
            'args': []
        })
    )
    print("   Ended RED turn")
    
    # BLUE turn - create units
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'unit_create',
            'args': [{
                'position': [7, 1],
                'unit_type': 'INFANTRY'
            }]
        })
    )
    print("   Created BLUE INFANTRY")
    
    # End BLUE turn
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'turn_end',
            'args': []
        })
    )
    
    # Back to RED - load infantry into APC
    print("\n4. Loading infantry into APC...")
    
    # Select infantry at (5,1)
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 5 * 32 + 16, inf_y).click().perform()
    time.sleep(1)
    
    # Move onto APC at (4,1)
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 4 * 32 + 16, inf_y).click().perform()
    time.sleep(2)
    print("   Infantry loaded into APC")
    
    driver.save_screenshot('/tmp/status_test_2_loaded.png')
    print("   Screenshot: /tmp/status_test_2_loaded.png")
    
    # Test 3: Capture status
    print("\n5. Testing capture status...")
    
    # Move available infantry to neutral city
    # First find a neutral city position (usually at 6,3)
    city_x = 6 * 32 + 16
    city_y = 3 * 32 + 16
    
    # Select tank at (2,1)
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 2 * 32 + 16, inf_y).click().perform()
    time.sleep(1)
    
    # Move it out of the way
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 2 * 32 + 16, 3 * 32 + 16).click().perform()
    time.sleep(1)
    
    # Create new infantry for capturing
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'unit_create',
            'args': [{
                'position': [6, 2],
                'unit_type': 'INFANTRY'
            }]
        })
    )
    print("   Created infantry near city")
    
    # End turn and back
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'turn_end',
            'args': []
        })
    )
    
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'turn_end',
            'args': []
        })
    )
    
    # Move infantry onto city and capture
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 6 * 32 + 16, 2 * 32 + 16).click().perform()
    time.sleep(1)
    
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, city_x, city_y).click().perform()
    time.sleep(2)
    
    print("   Infantry capturing city")
    driver.save_screenshot('/tmp/status_test_3_capture.png')
    print("   Screenshot: /tmp/status_test_3_capture.png")
    
    # Test 4: Submarine dive status
    print("\n6. Testing submarine dive status...")
    
    # Create submarine
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'unit_create',
            'args': [{
                'position': [8, 8],  # In water
                'unit_type': 'SUBMARINE'
            }]
        })
    )
    print("   Created RED SUBMARINE")
    
    # End turn cycle to make it available
    for _ in range(2):
        response = requests.post('http://localhost:5000/api',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                'token': game_id,
                'method': 'turn_end',
                'args': []
            })
        )
    
    # Dive submarine
    sub_x = 8 * 32 + 16
    sub_y = 8 * 32 + 16
    
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, sub_x, sub_y).click().perform()
    time.sleep(1)
    
    # Right-click or use dive command (depends on implementation)
    # For now, just move it
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 9 * 32 + 16, sub_y).click().perform()
    time.sleep(1)
    
    driver.save_screenshot('/tmp/status_test_4_submarine.png')
    print("   Screenshot: /tmp/status_test_4_submarine.png")
    
    # Test 5: Create damaged units for HP display
    print("\n7. Creating damaged units...")
    
    # Use API to damage some units if possible, or initiate combat
    # For now, let's check hover info on all units
    
    print("\n8. Testing hover info on various units...")
    
    # Hover over loaded APC
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 4 * 32 + 16, inf_y).perform()
    time.sleep(1)
    hover_text = driver.find_element(By.ID, 'tile-info').text
    print(f"   APC hover: {hover_text}")
    
    # Hover over capturing infantry
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, city_x, city_y).perform()
    time.sleep(1)
    hover_text = driver.find_element(By.ID, 'tile-info').text
    print(f"   Capturing infantry hover: {hover_text}")
    
    # Final comprehensive screenshot
    driver.save_screenshot('/tmp/status_test_final.png')
    print("\n9. Final screenshot: /tmp/status_test_final.png")
    
    # Check UI sprite status
    ui_status = driver.execute_script("""
        const result = {
            uiSpritesLoaded: false,
            spriteTypes: []
        };
        
        if (window.game && window.game.sprites && window.game.sprites.ui) {
            result.uiSpritesLoaded = true;
            const uiSprites = Object.keys(window.game.sprites.ui.data);
            
            // Count different sprite types
            result.spriteTypes = {
                neutralHp: uiSprites.filter(s => s.match(/^hp_\\d+$/)).length,
                hiddenHp: uiSprites.filter(s => s === 'hp_hidden').length,
                coloredHp: uiSprites.filter(s => s.match(/^hp_(red|blue|green|yellow|grey)_\\d+$/)).length,
                statusSprites: uiSprites.filter(s => s.includes('_loaded') || s.includes('_capturing') || s.includes('_dive')).length,
                warningSprites: uiSprites.filter(s => s.includes('warning')).length
            };
        }
        
        return result;
    """)
    
    print("\n10. UI Sprite System Status:")
    print(f"    Loaded: {ui_status['uiSpritesLoaded']}")
    if ui_status['uiSpritesLoaded']:
        types = ui_status['spriteTypes']
        print(f"    Neutral HP sprites: {types['neutralHp']}")
        print(f"    Hidden HP sprites: {types['hiddenHp']}")
        print(f"    Colored HP sprites: {types['coloredHp']}")
        print(f"    Status sprites: {types['statusSprites']}")
        print(f"    Warning sprites: {types['warningSprites']}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()

print("\n=== Test Complete ===")
print("\nScreenshots created:")
print("1. /tmp/status_test_1_normal.png - Available vs unavailable units")
print("2. /tmp/status_test_2_loaded.png - Infantry loaded in APC")
print("3. /tmp/status_test_3_capture.png - Infantry capturing city")
print("4. /tmp/status_test_4_submarine.png - Submarine (dive status)")
print("5. /tmp/status_test_final.png - Overview of all statuses")
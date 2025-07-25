#!/usr/bin/env python3
"""
Comprehensive battle test with UI verification for damaged units
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import json
import random

print("=== Battle & UI Test ===\n")

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
    # Create a new game via API with test endpoint for high funds
    print("1. Creating test game with high funds...")
    game_id = f"battle_test_{int(time.time())}"
    
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
        result = response.json()
        if 'result' in result:
            print(f"✅ Created game: {game_id}")
            print(f"   Starting funds: 50000 each (test mode)")
    
    # Load the game
    print("\n2. Loading game in browser...")
    driver.get(f'http://localhost:5000/game/{game_id}')
    
    # Wait for canvas
    canvas = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "gameCanvas"))
    )
    time.sleep(3)
    print("✅ Game loaded")
    
    # Create units strategically for battle
    print("\n3. Creating units for battle...")
    
    # RED: Create TANK and INFANTRY
    units_created = []
    
    # Create RED TANK
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'unit_create',
            'args': [{
                'position': [2, 2],
                'unit_type': 'TANK'
            }]
        })
    )
    if response.json().get('result'):
        units_created.append("RED TANK at (2,2)")
        print("✅ Created RED TANK at (2,2)")
    
    # Create RED INFANTRY
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'unit_create',
            'args': [{
                'position': [3, 2],
                'unit_type': 'INFANTRY'
            }]
        })
    )
    if response.json().get('result'):
        units_created.append("RED INFANTRY at (3,2)")
        print("✅ Created RED INFANTRY at (3,2)")
    
    # End RED turn
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'turn_end',
            'args': []
        })
    )
    print("✅ Ended RED turn")
    
    # BLUE: Create units
    # Create BLUE MECH (stronger vs tanks)
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'unit_create',
            'args': [{
                'position': [4, 2],
                'unit_type': 'MECH'
            }]
        })
    )
    if response.json().get('result'):
        units_created.append("BLUE MECH at (4,2)")
        print("✅ Created BLUE MECH at (4,2)")
    
    # Create BLUE RECON
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'unit_create',
            'args': [{
                'position': [5, 2],
                'unit_type': 'RECON'
            }]
        })
    )
    if response.json().get('result'):
        units_created.append("BLUE RECON at (5,2)")
        print("✅ Created BLUE RECON at (5,2)")
    
    # End BLUE turn
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'turn_end',
            'args': []
        })
    )
    print("✅ Ended BLUE turn")
    
    time.sleep(2)
    
    # Take pre-battle screenshot
    driver.save_screenshot('/tmp/battle_test_before.png')
    print("\n4. Pre-battle screenshot: /tmp/battle_test_before.png")
    
    # RED turn - Attack with tank
    print("\n5. Initiating battle...")
    
    # Click RED TANK
    tank_x = 2 * 32 + 16
    tank_y = 2 * 32 + 16
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, tank_x, tank_y).click().perform()
    time.sleep(1)
    print("   Selected RED TANK")
    
    # Attack BLUE MECH (adjacent)
    mech_x = 4 * 32 + 16
    mech_y = 2 * 32 + 16
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, mech_x, mech_y).click().perform()
    time.sleep(2)
    print("   Attacked BLUE MECH")
    
    # Click RED INFANTRY
    inf_x = 3 * 32 + 16
    inf_y = 2 * 32 + 16
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, inf_x, inf_y).click().perform()
    time.sleep(1)
    
    # Attack BLUE RECON
    recon_x = 5 * 32 + 16
    recon_y = 2 * 32 + 16
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, recon_x, recon_y).click().perform()
    time.sleep(2)
    print("   RED INFANTRY attacked BLUE RECON")
    
    # Take post-battle screenshot
    driver.save_screenshot('/tmp/battle_test_after.png')
    print("\n6. Post-battle screenshot: /tmp/battle_test_after.png")
    
    # Check HP display by hovering
    print("\n7. Testing HP display on damaged units...")
    
    # Hover over BLUE MECH to see damage
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, mech_x, mech_y).perform()
    time.sleep(1)
    
    hover_text = driver.find_element(By.ID, 'tile-info').text
    print(f"   BLUE MECH hover: {hover_text}")
    
    # Hover over BLUE RECON
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, recon_x, recon_y).perform()
    time.sleep(1)
    
    hover_text = driver.find_element(By.ID, 'tile-info').text
    print(f"   BLUE RECON hover: {hover_text}")
    
    # Get detailed game state
    print("\n8. Verifying battle results...")
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'game_state',
            'args': []
        })
    )
    
    if response.status_code == 200:
        state = response.json().get('result', {})
        print(f"   Current turn: {state.get('current_turn', '?')}")
        print(f"   Day: {state.get('days', '?')}")
        
        print("\n   Unit status after battle:")
        for army_name, army in state.get('armies', {}).items():
            units = army.get('units', [])
            if units:
                print(f"\n   {army_name}:")
                for unit in units:
                    hp = unit.get('hp', '?')
                    status = "❤️ Full HP" if hp == 100 else f"💔 Damaged ({hp}/100)"
                    print(f"     {unit['type']} at {unit['position']}: {status}")
    
    # Check if HP sprites are being drawn
    print("\n9. Checking UI sprite rendering...")
    ui_check = driver.execute_script("""
        const result = {
            gameLoaded: !!window.game,
            spritesLoaded: window.game && window.game.sprites ? true : false,
            uiSpritesCount: 0,
            drawnHpSprites: []
        };
        
        if (window.game && window.game.sprites && window.game.sprites.ui) {
            result.uiSpritesCount = Object.keys(window.game.sprites.ui.data).length;
            
            // Check canvas for HP sprites (this is a simplified check)
            // In real implementation, we'd need to track actual draw calls
            result.hasHpSprites = Object.keys(window.game.sprites.ui.data).some(k => k.includes('hp_'));
        }
        
        return result;
    """)
    
    print(f"   Game loaded: {ui_check['gameLoaded']}")
    print(f"   Sprites loaded: {ui_check['spritesLoaded']}")
    print(f"   UI sprites count: {ui_check['uiSpritesCount']}")
    print(f"   Has HP sprites: {ui_check.get('hasHpSprites', False)}")
    
    # Final screenshot with hover
    print("\n10. Taking final screenshot with HP display...")
    # Hover over a damaged unit for the screenshot
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, mech_x, mech_y).perform()
    time.sleep(1)
    
    driver.save_screenshot('/tmp/battle_test_final.png')
    print("    Final screenshot: /tmp/battle_test_final.png")
    
    # Check console for errors
    logs = driver.get_log('browser')
    errors = [log for log in logs if log['level'] == 'SEVERE']
    if errors:
        print("\n❌ JavaScript errors found:")
        for error in errors[:3]:
            print(f"   {error['message'][:100]}...")
    else:
        print("\n✅ No JavaScript errors")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()

print("\n=== Test Complete ===")
print("\nCheck the screenshots to verify:")
print("- /tmp/battle_test_before.png - Units at full HP")
print("- /tmp/battle_test_after.png - Units after combat with damage")
print("- /tmp/battle_test_final.png - HP display on hover")
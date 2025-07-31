#!/usr/bin/env python3
"""
Final battle test with proper API format
"""

import requests
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

print("=== Final Battle Test ===\n")

# Create game via API with correct format
print("1. Creating game via API...")
game_id = f"battle_final_{int(time.time())}"

response = requests.post('http://localhost:5000/api',
    headers={'Content-Type': 'application/json'},
    data=json.dumps({
        'method': 'game_create_test',
        'params': {
            'token': game_id,
            'use_optimized': True
        },
        'jsonrpc': '2.0',
        'id': 1
    })
)

if response.status_code == 200:
    result = response.json()
    if 'result' in result:
        print(f"✅ Created game: {game_id}")
        print(f"   Starting funds: 50000 (test mode)")
    else:
        print(f"❌ Failed: {result}")
        exit(1)
else:
    print(f"❌ API error: {response.status_code}")
    print(response.text)
    exit(1)

# Setup Chrome
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1280,800')

driver = webdriver.Chrome(options=options)

try:
    # Load the game
    print("\n2. Loading game in browser...")
    driver.get(f'http://localhost:5000/game/{game_id}')
    
    # Wait for canvas
    canvas = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "gameCanvas"))
    )
    time.sleep(3)
    print("✅ Game loaded")
    
    # Check initial UI state
    ui_check = driver.execute_script("""
        return {
            gameLoaded: !!window.game,
            uiSpritesLoaded: window.game && window.game.sprites && window.game.sprites.ui ? true : false,
            canvasSize: window.game && window.game.canvas ? 
                [window.game.canvas.width, window.game.canvas.height] : [0, 0]
        };
    """)
    print(f"   Canvas size: {ui_check['canvasSize']}")
    print(f"   UI sprites loaded: {ui_check['uiSpritesLoaded']}")
    
    # Create units via UI
    print("\n3. Creating units via UI...")
    
    # Click RED factory at (0,4) 
    factory_x = 0 * 32 + 16
    factory_y = 4 * 32 + 16
    
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, factory_x, factory_y).click().perform()
    time.sleep(1)
    
    # Create infantry
    modal = driver.find_element(By.ID, 'modal')
    if modal.value_of_css_property('display') == 'flex':
        create_btn = driver.find_element(By.ID, 'create')
        create_btn.click()
        time.sleep(1)
        print("   Created RED INFANTRY at factory")
    
    # Create more units via API for speed
    print("\n4. Creating additional units via API...")
    
    # RED TANK at (2,2)
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'method': 'unit_create',
            'params': {
                'token': game_id,
                'position': [2, 2],
                'unit_type': 'TANK'
            },
            'jsonrpc': '2.0',
            'id': 2
        })
    )
    if response.json().get('result'):
        print("   Created RED TANK at (2,2)")
    
    # End RED turn
    end_btn = driver.find_element(By.ID, 'end-turn')
    end_btn.click()
    time.sleep(1)
    
    # BLUE units
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'method': 'unit_create',
            'params': {
                'token': game_id,
                'position': [5, 2],
                'unit_type': 'MECH'
            },
            'jsonrpc': '2.0',
            'id': 3
        })
    )
    if response.json().get('result'):
        print("   Created BLUE MECH at (5,2)")
    
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'method': 'unit_create',
            'params': {
                'token': game_id,
                'position': [6, 2],
                'unit_type': 'RECON'
            },
            'jsonrpc': '2.0',
            'id': 4
        })
    )
    if response.json().get('result'):
        print("   Created BLUE RECON at (6,2)")
    
    # End BLUE turn via API
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'method': 'turn_end',
            'params': {'token': game_id},
            'jsonrpc': '2.0',
            'id': 5
        })
    )
    
    # Refresh to see all units
    driver.refresh()
    time.sleep(2)
    canvas = driver.find_element(By.ID, "gameCanvas")
    
    # Take pre-battle screenshot
    driver.save_screenshot('/tmp/battle_final_before.png')
    print("\n5. Pre-battle screenshot: /tmp/battle_final_before.png")
    
    # Battle - move and attack
    print("\n6. Initiating combat...")
    
    # Move RED infantry from factory
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, factory_x, factory_y).click().perform()
    time.sleep(1)
    
    # Move toward BLUE units
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 4 * 32 + 16, 3 * 32 + 16).click().perform()
    time.sleep(1)
    
    # Attack BLUE MECH
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 5 * 32 + 16, 2 * 32 + 16).click().perform()
    time.sleep(2)
    print("   RED INFANTRY attacked BLUE MECH")
    
    # Move and attack with tank
    tank_x = 2 * 32 + 16
    tank_y = 2 * 32 + 16
    
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, tank_x, tank_y).click().perform()
    time.sleep(1)
    
    # Attack BLUE RECON
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 6 * 32 + 16, tank_y).click().perform()
    time.sleep(2)
    print("   RED TANK attacked BLUE RECON")
    
    # Take post-battle screenshot
    driver.save_screenshot('/tmp/battle_final_after.png')
    print("\n7. Post-battle screenshot: /tmp/battle_final_after.png")
    
    # Test HP display
    print("\n8. Testing HP display on damaged units...")
    
    # Hover over damaged BLUE MECH
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 5 * 32 + 16, 2 * 32 + 16).perform()
    time.sleep(1)
    
    hover_text = driver.find_element(By.ID, 'tile-info').text
    print(f"   BLUE MECH: {hover_text}")
    
    # Hover over damaged BLUE RECON
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 6 * 32 + 16, 2 * 32 + 16).perform()
    time.sleep(1)
    
    hover_text = driver.find_element(By.ID, 'tile-info').text
    print(f"   BLUE RECON: {hover_text}")
    
    # Check game state
    game_state = driver.execute_script("""
        const result = {
            units: [],
            uiSpritesLoaded: false,
            hpSpriteCount: 0,
            damagedUnits: []
        };
        
        if (window.game && window.game.board && window.game.board.grid) {
            for (let tile of window.game.board.grid) {
                if (tile.unit) {
                    const unitData = {
                        type: tile.unit.type,
                        army: tile.unit.army,
                        hp: tile.unit.status ? tile.unit.status.hp : 100,
                        pos: [tile.x, tile.y],
                        available: !tile.unit.has_moved && !tile.unit.done
                    };
                    result.units.push(unitData);
                    
                    if (unitData.hp < 100) {
                        result.damagedUnits.push({
                            army: unitData.army,
                            type: unitData.type,
                            hp: unitData.hp
                        });
                    }
                }
            }
        }
        
        if (window.game && window.game.sprites && window.game.sprites.ui) {
            result.uiSpritesLoaded = true;
            const sprites = Object.keys(window.game.sprites.ui.data);
            result.hpSpriteCount = sprites.filter(s => s.startsWith('hp_')).length;
        }
        
        return result;
    """)
    
    print("\n9. Game State Analysis:")
    print(f"   UI sprites loaded: {game_state['uiSpritesLoaded']}")
    print(f"   HP sprite count: {game_state['hpSpriteCount']}")
    print(f"   Total units: {len(game_state['units'])}")
    print(f"   Damaged units: {len(game_state['damagedUnits'])}")
    
    if game_state['damagedUnits']:
        print("\n   Damaged unit details:")
        for unit in game_state['damagedUnits']:
            print(f"   - {unit['army']} {unit['type']}: {unit['hp']} HP")
    
    # Final screenshot with damage display
    driver.save_screenshot('/tmp/battle_final_complete.png')
    print("\n10. Final screenshot: /tmp/battle_final_complete.png")

except Exception as e:
    print(f"\n❌ Error: {e}")
    driver.save_screenshot('/tmp/battle_final_error.png')
    print("Error screenshot: /tmp/battle_final_error.png")

finally:
    driver.quit()

print("\n=== Test Complete ===")
print("\nVerify the following in screenshots:")
print("1. /tmp/battle_final_before.png - Units at full HP")
print("2. /tmp/battle_final_after.png - Combat damage visible")
print("3. /tmp/battle_final_complete.png - HP sprites on damaged units")
#!/usr/bin/env python3
"""
Battle test using API to create game
"""

import requests
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

print("=== API Battle Test ===\n")

# Create game via API
print("1. Creating game via API...")
game_id = f"api_battle_{int(time.time())}"

response = requests.post('http://localhost:5000/api',
    headers={'Content-Type': 'application/json'},
    data=json.dumps({
        'method': 'game_create_test',
        'params': {
            'token': game_id,
            'use_optimized': True
        }
    })
)

if response.status_code == 200:
    result = response.json()
    if 'result' in result:
        print(f"✅ Created game: {game_id}")
    else:
        print(f"❌ Failed to create game: {result}")
        exit(1)
else:
    print(f"❌ API error: {response.status_code}")
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
    
    # Create units via API for speed
    print("\n3. Creating units via API...")
    
    # RED INFANTRY at (2,2)
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'unit_create',
            'args': [{
                'position': [2, 2],
                'unit_type': 'INFANTRY'
            }]
        })
    )
    print("   Created RED INFANTRY at (2,2)")
    
    # RED TANK at (3,2)
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'unit_create',
            'args': [{
                'position': [3, 2],
                'unit_type': 'TANK'
            }]
        })
    )
    print("   Created RED TANK at (3,2)")
    
    # End RED turn
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'turn_end',
            'args': []
        })
    )
    
    # BLUE MECH at (5,2)
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'unit_create',
            'args': [{
                'position': [5, 2],
                'unit_type': 'MECH'
            }]
        })
    )
    print("   Created BLUE MECH at (5,2)")
    
    # BLUE RECON at (6,2)
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'unit_create',
            'args': [{
                'position': [6, 2],
                'unit_type': 'RECON'
            }]
        })
    )
    print("   Created BLUE RECON at (6,2)")
    
    # End BLUE turn
    response = requests.post('http://localhost:5000/api',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'token': game_id,
            'method': 'turn_end',
            'args': []
        })
    )
    
    # Refresh page to see units
    driver.refresh()
    time.sleep(2)
    
    # Take pre-battle screenshot
    driver.save_screenshot('/tmp/api_battle_before.png')
    print("\n4. Pre-battle screenshot: /tmp/api_battle_before.png")
    
    # Battle via UI - RED attacks
    print("\n5. Initiating combat via UI...")
    
    # Click RED INFANTRY at (2,2)
    inf_x = 2 * 32 + 16
    inf_y = 2 * 32 + 16
    
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, inf_x, inf_y).click().perform()
    time.sleep(1)
    
    # Move toward BLUE units
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 4 * 32 + 16, inf_y).click().perform()
    time.sleep(1)
    
    # Attack BLUE MECH
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 5 * 32 + 16, inf_y).click().perform()
    time.sleep(2)
    print("   RED INFANTRY attacked BLUE MECH")
    
    # Click RED TANK at (3,2)
    tank_x = 3 * 32 + 16
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, tank_x, inf_y).click().perform()
    time.sleep(1)
    
    # Attack BLUE RECON
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 6 * 32 + 16, inf_y).click().perform()
    time.sleep(2)
    print("   RED TANK attacked BLUE RECON")
    
    # Take post-battle screenshot
    driver.save_screenshot('/tmp/api_battle_after.png')
    print("\n6. Post-battle screenshot: /tmp/api_battle_after.png")
    
    # Hover over damaged units
    print("\n7. Testing HP display on damaged units...")
    
    # Hover over BLUE MECH
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 5 * 32 + 16, inf_y).perform()
    time.sleep(1)
    
    hover_text = driver.find_element(By.ID, 'tile-info').text
    print(f"   BLUE MECH: {hover_text}")
    
    # Hover over BLUE RECON
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 6 * 32 + 16, inf_y).perform()
    time.sleep(1)
    
    hover_text = driver.find_element(By.ID, 'tile-info').text
    print(f"   BLUE RECON: {hover_text}")
    
    # Check game state
    game_state = driver.execute_script("""
        const result = {
            units: [],
            uiSpritesLoaded: false,
            hpSprites: []
        };
        
        if (window.game && window.game.board && window.game.board.grid) {
            for (let tile of window.game.board.grid) {
                if (tile.unit) {
                    result.units.push({
                        type: tile.unit.type,
                        army: tile.unit.army,
                        hp: tile.unit.status ? tile.unit.status.hp : 100,
                        pos: [tile.x, tile.y],
                        available: !tile.unit.has_moved && !tile.unit.done
                    });
                }
            }
        }
        
        if (window.game && window.game.sprites && window.game.sprites.ui) {
            result.uiSpritesLoaded = true;
            const sprites = Object.keys(window.game.sprites.ui.data);
            result.hpSprites = sprites.filter(s => s.startsWith('hp_')).length;
        }
        
        return result;
    """)
    
    print("\n8. Game State Analysis:")
    print(f"   UI sprites loaded: {game_state['uiSpritesLoaded']}")
    print(f"   HP sprites available: {game_state['hpSprites']}")
    
    print("\n   Units after combat:")
    for unit in game_state['units']:
        hp_status = "Full HP" if unit['hp'] == 100 else f"Damaged ({unit['hp']}/100)"
        availability = "Available" if unit['available'] else "Unavailable"
        print(f"   - {unit['army']} {unit['type']} at {unit['pos']}: {hp_status}, {availability}")
    
    # Final screenshot
    driver.save_screenshot('/tmp/api_battle_final.png')
    print("\n9. Final screenshot: /tmp/api_battle_final.png")
    
    # Get actual game state from API
    print("\n10. Verifying with API...")
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
        print(f"   Turn: {state.get('current_turn', '?')}, Day: {state.get('days', '?')}")
        
        # Count damaged units
        damaged_count = 0
        for army_name, army in state.get('armies', {}).items():
            for unit in army.get('units', []):
                if unit.get('hp', 100) < 100:
                    damaged_count += 1
        
        print(f"   Damaged units: {damaged_count}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    driver.save_screenshot('/tmp/api_battle_error.png')
    print("Error screenshot: /tmp/api_battle_error.png")

finally:
    driver.quit()

print("\n=== Test Complete ===")
print("\nScreenshots:")
print("1. /tmp/api_battle_before.png - Units before battle")
print("2. /tmp/api_battle_after.png - Units after combat")
print("3. /tmp/api_battle_final.png - Final state with HP display")
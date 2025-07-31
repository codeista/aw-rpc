#!/usr/bin/env python3
"""
Quick battle test via test interface
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

print("=== Quick Battle Test ===\n")

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1280,800')

driver = webdriver.Chrome(options=options)

try:
    # Go directly to test interface
    print("1. Using test interface...")
    driver.get('http://localhost:5000/test_interface')
    time.sleep(2)
    
    # Click the test game button (50000 funds)
    test_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Create Test Game')]")
    test_btn.click()
    time.sleep(3)
    
    # Should redirect to game
    current_url = driver.current_url
    print(f"   Game URL: {current_url}")
    
    # Wait for canvas
    canvas = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "gameCanvas"))
    )
    print("✅ Game loaded")
    time.sleep(2)
    
    # Create units - RED infantry and tank
    print("\n2. Creating units...")
    
    # RED factory at (0,4)
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
        print("   Created RED INFANTRY")
    
    # End turn
    end_btn = driver.find_element(By.ID, 'end-turn')
    end_btn.click()
    time.sleep(1)
    
    # BLUE turn - create MECH
    blue_factory_x = 11 * 32 + 16
    blue_factory_y = 4 * 32 + 16
    
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, blue_factory_x, blue_factory_y).click().perform()
    time.sleep(1)
    
    modal = driver.find_element(By.ID, 'modal')
    if modal.value_of_css_property('display') == 'flex':
        unit_select = driver.find_element(By.ID, 'unit-select')
        for option in unit_select.find_elements(By.TAG_NAME, 'option'):
            if 'MECH' in option.text:
                option.click()
                break
        
        create_btn = driver.find_element(By.ID, 'create')
        create_btn.click()
        time.sleep(1)
        print("   Created BLUE MECH")
    
    # End BLUE turn
    end_btn.click()
    time.sleep(1)
    
    # Screenshot before battle
    driver.save_screenshot('/tmp/quick_battle_before.png')
    print("\n3. Pre-battle screenshot: /tmp/quick_battle_before.png")
    
    # Move units into attack position over several turns
    print("\n4. Moving units into battle...")
    
    # Move RED infantry toward center
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, factory_x, factory_y).click().perform()
    time.sleep(0.5)
    actions.move_to_element_with_offset(canvas, 3 * 32 + 16, factory_y).click().perform()
    time.sleep(0.5)
    
    end_btn.click()
    time.sleep(0.5)
    
    # Move BLUE MECH
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, blue_factory_x, blue_factory_y).click().perform()
    time.sleep(0.5)
    actions.move_to_element_with_offset(canvas, 8 * 32 + 16, factory_y).click().perform()
    time.sleep(0.5)
    
    end_btn.click()
    time.sleep(0.5)
    
    # Move closer
    for i in range(3):
        # RED
        actions = ActionChains(driver)
        actions.move_to_element_with_offset(canvas, (3 + i) * 32 + 16, factory_y).click().perform()
        time.sleep(0.5)
        actions.move_to_element_with_offset(canvas, (4 + i) * 32 + 16, factory_y).click().perform()
        time.sleep(0.5)
        end_btn.click()
        time.sleep(0.5)
        
        # BLUE
        actions = ActionChains(driver)
        actions.move_to_element_with_offset(canvas, (8 - i) * 32 + 16, factory_y).click().perform()
        time.sleep(0.5)
        actions.move_to_element_with_offset(canvas, (7 - i) * 32 + 16, factory_y).click().perform()
        time.sleep(0.5)
        end_btn.click()
        time.sleep(0.5)
    
    # Attack
    print("\n5. Initiating combat...")
    inf_x = 6 * 32 + 16
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, inf_x, factory_y).click().perform()
    time.sleep(1)
    
    # Attack BLUE MECH at (5,4)
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 5 * 32 + 16, factory_y).click().perform()
    time.sleep(2)
    print("   Combat occurred!")
    
    # Screenshot after battle
    driver.save_screenshot('/tmp/quick_battle_after.png')
    print("\n6. Post-battle screenshot: /tmp/quick_battle_after.png")
    
    # Hover over damaged unit
    print("\n7. Testing HP display...")
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 5 * 32 + 16, factory_y).perform()
    time.sleep(1)
    
    hover_text = driver.find_element(By.ID, 'tile-info').text
    print(f"   Damaged unit: {hover_text}")
    
    # Check game state
    game_state = driver.execute_script("""
        const result = {
            units: [],
            uiLoaded: false
        };
        
        if (window.game && window.game.board && window.game.board.grid) {
            for (let tile of window.game.board.grid) {
                if (tile.unit) {
                    result.units.push({
                        type: tile.unit.type,
                        army: tile.unit.army,
                        hp: tile.unit.status ? tile.unit.status.hp : 100,
                        pos: [tile.x, tile.y]
                    });
                }
            }
        }
        
        if (window.game && window.game.sprites && window.game.sprites.ui) {
            result.uiLoaded = true;
        }
        
        return result;
    """)
    
    print("\n8. Game state:")
    print(f"   UI sprites loaded: {game_state['uiLoaded']}")
    print("   Units:")
    for unit in game_state['units']:
        status = "Full HP" if unit['hp'] == 100 else f"HP: {unit['hp']}/100"
        print(f"   - {unit['army']} {unit['type']} at {unit['pos']}: {status}")
    
    # Final screenshot
    driver.save_screenshot('/tmp/quick_battle_final.png')
    print("\n9. Final screenshot: /tmp/quick_battle_final.png")

except Exception as e:
    print(f"\n❌ Error: {e}")
    driver.save_screenshot('/tmp/quick_battle_error.png')

finally:
    driver.quit()

print("\n=== Test Complete ===")
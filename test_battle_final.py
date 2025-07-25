#!/usr/bin/env python3
"""
Final battle test with UI verification
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
import time

print("=== Battle & UI Test ===\n")

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1280,800')

driver = webdriver.Chrome(options=options)

try:
    # Create game via landing page
    print("1. Creating game via UI...")
    driver.get('http://localhost:5000/')
    time.sleep(2)
    
    # Select a map
    map_select = Select(driver.find_element(By.CSS_SELECTOR, 'select'))
    map_select.select_by_visible_text('Test Map')
    time.sleep(1)
    
    # Click create game
    create_btn = driver.find_element(By.ID, 'createGameBtn')
    driver.execute_script("arguments[0].scrollIntoView();", create_btn)
    create_btn.click()
    time.sleep(3)
    
    # Should be redirected to game
    current_url = driver.current_url
    print(f"   Game URL: {current_url}")
    
    # Wait for canvas
    canvas = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "gameCanvas"))
    )
    print("✅ Game loaded")
    
    # Create units at factories
    print("\n2. Creating units...")
    
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
    
    # Click RED base at (1,1) if exists
    base_x = 1 * 32 + 16
    base_y = 1 * 32 + 16
    
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, base_x, base_y).click().perform()
    time.sleep(1)
    
    modal = driver.find_element(By.ID, 'modal')
    if modal.value_of_css_property('display') == 'flex':
        # Select TANK
        unit_select = driver.find_element(By.ID, 'unit-select')
        for option in unit_select.find_elements(By.TAG_NAME, 'option'):
            if 'TANK' in option.text:
                option.click()
                break
        
        create_btn = driver.find_element(By.ID, 'create')
        create_btn.click()
        time.sleep(1)
        print("   Created RED TANK at base")
    
    # End RED turn
    end_btn = driver.find_element(By.ID, 'end-turn')
    end_btn.click()
    time.sleep(1)
    print("   Ended RED turn")
    
    # BLUE turn - create MECH at factory
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
        print("   Created BLUE MECH at factory")
    
    # End BLUE turn
    end_btn.click()
    time.sleep(1)
    print("   Ended BLUE turn")
    
    # Take screenshot before battle
    driver.save_screenshot('/tmp/battle_ui_before.png')
    print("\n3. Pre-battle screenshot: /tmp/battle_ui_before.png")
    
    # RED turn - move units toward center
    print("\n4. Moving units into battle position...")
    
    # Move infantry from factory
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, factory_x, factory_y).click().perform()
    time.sleep(1)
    
    # Move right 3 spaces
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 3 * 32 + 16, factory_y).click().perform()
    time.sleep(1)
    print("   Moved RED INFANTRY")
    
    # Move tank if it exists
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, base_x, base_y).click().perform()
    time.sleep(1)
    
    # Try to move it
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 4 * 32 + 16, 3 * 32 + 16).click().perform()
    time.sleep(1)
    
    # End turn
    end_btn.click()
    time.sleep(1)
    
    # BLUE turn - move MECH closer
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, blue_factory_x, blue_factory_y).click().perform()
    time.sleep(1)
    
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 8 * 32 + 16, factory_y).click().perform()
    time.sleep(1)
    print("   Moved BLUE MECH")
    
    # End turn - back to RED for combat
    end_btn.click()
    time.sleep(1)
    
    # Continue moving units into attack range over next few turns
    for i in range(2):
        # RED moves
        actions = ActionChains(driver)
        actions.move_to_element_with_offset(canvas, 3 * 32 + 16, factory_y).click().perform()
        time.sleep(0.5)
        actions.move_to_element_with_offset(canvas, (4 + i) * 32 + 16, factory_y).click().perform()
        time.sleep(0.5)
        
        end_btn.click()
        time.sleep(0.5)
        
        # BLUE moves
        actions = ActionChains(driver)
        actions.move_to_element_with_offset(canvas, 8 * 32 + 16, factory_y).click().perform()
        time.sleep(0.5)
        actions.move_to_element_with_offset(canvas, (7 - i) * 32 + 16, factory_y).click().perform()
        time.sleep(0.5)
        
        end_btn.click()
        time.sleep(0.5)
    
    print("\n5. Initiating combat...")
    
    # RED attacks - find and click infantry
    inf_x = 5 * 32 + 16
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, inf_x, factory_y).click().perform()
    time.sleep(1)
    
    # Attack adjacent BLUE unit
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 6 * 32 + 16, factory_y).click().perform()
    time.sleep(2)
    print("   Combat occurred!")
    
    # Take post-battle screenshot
    driver.save_screenshot('/tmp/battle_ui_after.png')
    print("\n6. Post-battle screenshot: /tmp/battle_ui_after.png")
    
    # Test hover on damaged units
    print("\n7. Testing HP display on damaged units...")
    
    # Hover over position where combat occurred
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 6 * 32 + 16, factory_y).perform()
    time.sleep(1)
    
    hover_text = driver.find_element(By.ID, 'tile-info').text
    print(f"   Hover text: {hover_text}")
    
    # Check game state
    game_state = driver.execute_script("""
        if (!window.game || !window.game.board) return { error: "Game not loaded" };
        
        const result = {
            units: [],
            uiSpritesLoaded: false,
            hpSpritesFound: []
        };
        
        // Get all units
        if (window.game.board.grid) {
            for (let tile of window.game.board.grid) {
                if (tile.unit) {
                    result.units.push({
                        type: tile.unit.type,
                        army: tile.unit.army,
                        pos: [tile.x, tile.y],
                        hp: tile.unit.status ? tile.unit.status.hp : 100,
                        available: !tile.unit.has_moved && !tile.unit.done
                    });
                }
            }
        }
        
        // Check UI sprites
        if (window.game.sprites && window.game.sprites.ui) {
            result.uiSpritesLoaded = true;
            const sprites = Object.keys(window.game.sprites.ui.data);
            result.hpSpritesFound = sprites.filter(s => s.includes('hp_')).slice(0, 10);
        }
        
        return result;
    """)
    
    print("\n8. Game State Analysis:")
    print(f"   UI sprites loaded: {game_state['uiSpritesLoaded']}")
    print(f"   Sample HP sprites: {game_state['hpSpritesFound']}")
    
    print("\n   Units after combat:")
    for unit in game_state['units']:
        hp_display = "💚 Full HP" if unit['hp'] == 100 else f"💔 HP: {unit['hp']}/100"
        status = "Available" if unit['available'] else "Unavailable"
        print(f"   {unit['army']} {unit['type']} at {unit['pos']}: {hp_display} ({status})")
    
    # Take final screenshot
    driver.save_screenshot('/tmp/battle_ui_final.png')
    print("\n9. Final screenshot: /tmp/battle_ui_final.png")

except Exception as e:
    print(f"\n❌ Error: {e}")
    driver.save_screenshot('/tmp/battle_ui_error.png')

finally:
    driver.quit()

print("\n=== Test Complete ===")
print("\nScreenshots:")
print("1. /tmp/battle_ui_before.png - Units before battle")
print("2. /tmp/battle_ui_after.png - Units after combat")
print("3. /tmp/battle_ui_final.png - Final state with HP display")
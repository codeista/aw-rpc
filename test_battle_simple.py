#!/usr/bin/env python3
"""
Simple battle test using existing game
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import requests
import json

print("=== Simple Battle Test ===\n")

# First create a game via browser
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1280,800')

driver = webdriver.Chrome(options=options)

try:
    # Go to home page
    print("1. Creating new game via UI...")
    driver.get('http://localhost:5000/')
    time.sleep(2)
    
    # Click test interface link
    test_link = driver.find_element(By.LINK_TEXT, 'Test Interface')
    test_link.click()
    time.sleep(2)
    
    # Click button to create test game
    create_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Create Test Game')]")
    create_btn.click()
    time.sleep(3)
    
    # Should redirect to game
    current_url = driver.current_url
    if '/game/' in current_url:
        game_id = current_url.split('/')[-1]
        print(f"✅ Created game: {game_id}")
    else:
        print(f"❌ Unexpected URL: {current_url}")
        exit(1)
    
    # Now we're in the game
    canvas = driver.find_element(By.ID, 'gameCanvas')
    print("✅ Game loaded")
    
    # Click on RED factory to create unit
    print("\n2. Creating units...")
    factory_x = 0 * 32 + 16
    factory_y = 4 * 32 + 16
    
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, factory_x, factory_y).click().perform()
    time.sleep(1)
    
    # Check if modal opened
    modal = driver.find_element(By.ID, 'modal')
    if modal.is_displayed():
        # Create infantry
        create_btn = driver.find_element(By.ID, 'create')
        create_btn.click()
        time.sleep(1)
        print("✅ Created RED INFANTRY")
    
    # Create another unit at different position
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 1 * 32 + 16, 4 * 32 + 16).click().perform()
    time.sleep(1)
    
    # If this is a base, create tank
    modal = driver.find_element(By.ID, 'modal')
    if modal.is_displayed():
        select = driver.find_element(By.ID, 'unit-select')
        # Find TANK option
        for option in select.find_elements(By.TAG_NAME, 'option'):
            if 'TANK' in option.text:
                option.click()
                break
        
        create_btn = driver.find_element(By.ID, 'create')
        create_btn.click()
        time.sleep(1)
        print("✅ Created RED TANK")
    
    # End turn
    end_turn = driver.find_element(By.ID, 'end-turn')
    end_turn.click()
    time.sleep(1)
    print("✅ Ended RED turn")
    
    # BLUE turn - create unit
    blue_factory_x = 11 * 32 + 16
    blue_factory_y = 4 * 32 + 16
    
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, blue_factory_x, blue_factory_y).click().perform()
    time.sleep(1)
    
    modal = driver.find_element(By.ID, 'modal')
    if modal.is_displayed():
        # Create MECH (good vs tanks)
        select = driver.find_element(By.ID, 'unit-select')
        for option in select.find_elements(By.TAG_NAME, 'option'):
            if 'MECH' in option.text:
                option.click()
                break
        
        create_btn = driver.find_element(By.ID, 'create')
        create_btn.click()
        time.sleep(1)
        print("✅ Created BLUE MECH")
    
    # End BLUE turn
    end_turn.click()
    time.sleep(1)
    print("✅ Ended BLUE turn")
    
    # Take pre-battle screenshot
    driver.save_screenshot('/tmp/battle_before.png')
    print("\n3. Pre-battle screenshot: /tmp/battle_before.png")
    
    # Back to RED - move and attack
    print("\n4. Moving units closer for battle...")
    
    # Move infantry
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, factory_x, factory_y).click().perform()
    time.sleep(1)
    
    # Move right towards center
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 3 * 32 + 16, factory_y).click().perform()
    time.sleep(1)
    print("   Moved RED INFANTRY")
    
    # Move tank if exists
    if 'TANK' in driver.page_source:
        actions = ActionChains(driver)
        actions.move_to_element_with_offset(canvas, 1 * 32 + 16, factory_y).click().perform()
        time.sleep(1)
        
        actions = ActionChains(driver)
        actions.move_to_element_with_offset(canvas, 4 * 32 + 16, factory_y).click().perform()
        time.sleep(1)
        print("   Moved RED TANK")
    
    # End turn
    end_turn.click()
    time.sleep(1)
    
    # BLUE turn - move MECH closer
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, blue_factory_x, blue_factory_y).click().perform()
    time.sleep(1)
    
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 8 * 32 + 16, factory_y).click().perform()
    time.sleep(1)
    print("   Moved BLUE MECH")
    
    # End turn - back to RED
    end_turn.click()
    time.sleep(1)
    
    # Move units into attack range and attack
    print("\n5. Initiating combat...")
    
    # Move tank to attack position
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 4 * 32 + 16, factory_y).click().perform()
    time.sleep(1)
    
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 7 * 32 + 16, factory_y).click().perform()
    time.sleep(1)
    
    # Attack MECH
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 8 * 32 + 16, factory_y).click().perform()
    time.sleep(2)
    print("   RED TANK attacked BLUE MECH")
    
    # Take post-battle screenshot
    driver.save_screenshot('/tmp/battle_after.png')
    print("\n6. Post-battle screenshot: /tmp/battle_after.png")
    
    # Test hover on damaged unit
    print("\n7. Testing HP display...")
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, 8 * 32 + 16, factory_y).perform()
    time.sleep(1)
    
    hover_text = driver.find_element(By.ID, 'tile-info').text
    print(f"   Damaged unit hover: {hover_text}")
    
    # Check game state via JavaScript
    game_info = driver.execute_script("""
        if (!window.game || !window.game.board) return { error: "No game" };
        
        let units = [];
        for (let tile of window.game.board.grid) {
            if (tile.unit) {
                units.push({
                    type: tile.unit.type,
                    army: tile.unit.army,
                    hp: tile.unit.status ? tile.unit.status.hp : 'unknown',
                    pos: [tile.x, tile.y]
                });
            }
        }
        
        return {
            units: units,
            uiSprites: window.game.sprites && window.game.sprites.ui ? 
                Object.keys(window.game.sprites.ui.data).length : 0
        };
    """)
    
    print("\n8. Game state:")
    print(f"   UI sprites loaded: {game_info.get('uiSprites', 0)}")
    print("   Units:")
    for unit in game_info.get('units', []):
        hp_status = "Full" if unit['hp'] == 100 else f"Damaged ({unit['hp']}/100)"
        print(f"     {unit['army']} {unit['type']} at {unit['pos']}: {hp_status}")
    
    # Final screenshot with hover
    driver.save_screenshot('/tmp/battle_final.png')
    print("\n9. Final screenshot: /tmp/battle_final.png")

except Exception as e:
    print(f"\n❌ Error: {e}")
    driver.save_screenshot('/tmp/battle_error.png')
    print("Error screenshot: /tmp/battle_error.png")

finally:
    driver.quit()

print("\n=== Test Complete ===")
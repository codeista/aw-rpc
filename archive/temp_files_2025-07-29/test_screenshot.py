#!/usr/bin/env python3
"""
Take screenshot of existing game
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sys

if len(sys.argv) < 2:
    print("Usage: python test_screenshot.py <game_id>")
    game_id = "ui_visual_1753430988"
else:
    game_id = sys.argv[1]

print(f"Taking screenshot of game: {game_id}")

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1280,800')

driver = webdriver.Chrome(options=options)

try:
    driver.get(f'http://localhost:5000/game/{game_id}')
    time.sleep(3)
    
    # Wait for canvas
    canvas = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "gameCanvas"))
    )
    time.sleep(2)
    
    # Take screenshot
    driver.save_screenshot(f'/tmp/game_{game_id}.png')
    print(f"Screenshot saved: /tmp/game_{game_id}.png")
    
    # Check game state
    state = driver.execute_script("""
        const result = {
            gameLoaded: !!window.game,
            units: []
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
        
        return result;
    """)
    
    print(f"Game loaded: {state['gameLoaded']}")
    print(f"Units found: {len(state['units'])}")
    
    for unit in state['units']:
        print(f"  {unit['army']} {unit['type']} at {unit['pos']}: {unit['hp']} HP")
    
except Exception as e:
    print(f"Error: {e}")
    driver.save_screenshot('/tmp/game_error.png')

finally:
    driver.quit()
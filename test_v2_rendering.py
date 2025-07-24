#!/usr/bin/env python3
"""Test V2 game rendering with Selenium"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# Create driver
driver = webdriver.Chrome(options=chrome_options)

try:
    # Visit the game page
    driver.get('http://localhost:5000/game/v2/632959bf')
    
    # Wait for canvas to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "game-canvas"))
    )
    
    # Get JavaScript console logs
    logs = driver.get_log('browser')
    print("Browser console logs:")
    for log in logs:
        print(f"  {log['level']}: {log['message']}")
    
    # Execute JavaScript to check game state
    game_info = driver.execute_script("""
        if (window.game) {
            return {
                gameId: window.game.gameId,
                hasSprites: !!window.game.sprites,
                hasGameState: !!window.game.gameState,
                canvasSize: {
                    width: window.game.canvas.width,
                    height: window.game.canvas.height
                },
                spriteTypes: window.game.sprites ? Object.keys(window.game.sprites) : []
            };
        } else {
            return { error: 'Game not initialized' };
        }
    """)
    
    print("\nGame info:")
    print(json.dumps(game_info, indent=2))
    
    # Check if canvas is visible
    canvas = driver.find_element(By.ID, "game-canvas")
    print(f"\nCanvas displayed: {canvas.is_displayed()}")
    print(f"Canvas size: {canvas.size}")
    
    # Take screenshot
    driver.save_screenshot('/tmp/v2_game_screenshot.png')
    print("\nScreenshot saved to /tmp/v2_game_screenshot.png")
    
finally:
    driver.quit()
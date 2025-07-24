#!/usr/bin/env python3
"""Test V2 game loading"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--enable-logging')
chrome_options.add_argument('--log-level=0')
chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

# Create driver
driver = webdriver.Chrome(options=chrome_options)

try:
    # Visit the v2 game creation page
    driver.get('http://localhost:5000/game/v2')
    
    # Wait a bit for JavaScript to run
    time.sleep(2)
    
    # Get JavaScript console logs
    logs = driver.get_log('browser')
    print("Browser console logs:")
    for log in logs:
        # Print full log message including INFO level
        print(f"  {log['level']}: {log['message']}")
    
    # Check current URL
    current_url = driver.current_url
    print(f"\nCurrent URL: {current_url}")
    
    # Check if canvas exists
    try:
        canvas = driver.find_element(By.ID, "game-canvas")
        print(f"Canvas found: {canvas.is_displayed()}")
        print(f"Canvas size: {canvas.size}")
    except:
        print("Canvas not found!")
    
    # Check game state
    game_info = driver.execute_script("""
        if (window.game) {
            return {
                initialized: true,
                gameId: window.game.gameId,
                hasSprites: !!window.game.sprites,
                hasGameState: !!window.game.gameState,
                gameStateKeys: window.game.gameState ? Object.keys(window.game.gameState) : null,
                error: null,
                boardInfo: window.game.gameState ? {
                    width: window.game.gameState.board.width,
                    height: window.game.gameState.board.height,
                    tilesCount: window.game.gameState.board.tiles.length
                } : null
            };
        } else {
            return { initialized: false, error: 'Game object not found' };
        }
    """)
    
    print(f"\nGame info: {game_info}")
    
    # Take screenshot
    driver.save_screenshot('/tmp/v2_loading_test.png')
    print("\nScreenshot saved to /tmp/v2_loading_test.png")
    
finally:
    driver.quit()
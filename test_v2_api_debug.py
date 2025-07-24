#!/usr/bin/env python3
"""Debug V2 API game state loading"""

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
    
    # Wait a bit for async operations
    time.sleep(2)
    
    # Execute JavaScript to debug the issue
    debug_info = driver.execute_script("""
        return new Promise(async (resolve) => {
            const info = {
                gameId: window.game.gameId,
                hasSprites: !!window.game.sprites,
                hasGameState: !!window.game.gameState
            };
            
            // Try to get game state manually
            try {
                const response = await window.game.rpc('v2.game_state', { game_id: window.game.gameId });
                info.manualStateCall = {
                    success: true,
                    hasBoard: !!response.board,
                    boardSize: response.board ? `${response.board.width}x${response.board.height}` : null,
                    numTiles: response.board ? response.board.tiles.length : 0,
                    currentPlayer: response.current_player
                };
                
                // Also set it on the game object
                window.game.gameState = response;
                info.hasGameStateAfterManual = !!window.game.gameState;
                
                // Try to render
                window.game.render();
                
                // Check canvas content
                const ctx = window.game.canvas.getContext('2d');
                const imageData = ctx.getImageData(0, 0, 10, 10);
                const pixels = Array.from(imageData.data);
                info.canvasHasContent = pixels.some(p => p !== 0);
                
            } catch (e) {
                info.manualStateCall = {
                    success: false,
                    error: e.message
                };
            }
            
            resolve(info);
        });
    """)
    
    print("Debug info:")
    print(json.dumps(debug_info, indent=2))
    
    # Take screenshot after manual render
    driver.save_screenshot('/tmp/v2_game_debug.png')
    print("\nScreenshot saved to /tmp/v2_game_debug.png")
    
    # Check display text
    day_text = driver.find_element(By.ID, "day").text
    current_turn = driver.find_element(By.ID, "current-turn").text
    print(f"\nUI Info:")
    print(f"  Day: {day_text}")
    print(f"  Current Turn: {current_turn}")
    
finally:
    driver.quit()
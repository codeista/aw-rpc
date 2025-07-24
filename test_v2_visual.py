#!/usr/bin/env python3
"""Test V2 game visual rendering"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import requests

# Create a new game first
create_response = requests.post('http://localhost:5000/api', json={
    'jsonrpc': '2.0',
    'method': 'v2.create_game',
    'params': {
        'config': {
            'players': [
                {'name': 'Player 1', 'color': 'red'},
                {'name': 'Player 2', 'color': 'blue'}
            ],
            'map': 'test_map',
            'settings': {'starting_funds': 5000}
        }
    },
    'id': '1'
})

game_id = create_response.json()['result']['game_id']
print(f"Created new game: {game_id}")

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# Create driver
driver = webdriver.Chrome(options=chrome_options)

try:
    # Visit the game page
    driver.get(f'http://localhost:5000/game/v2/{game_id}')
    
    # Wait for canvas to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "game-canvas"))
    )
    
    # Wait for game to fully load
    time.sleep(3)
    
    # Take screenshot
    driver.save_screenshot('/tmp/v2_game_with_hqs.png')
    print("Screenshot saved to /tmp/v2_game_with_hqs.png")
    
    # Check game state
    game_info = driver.execute_script("""
        if (window.game && window.game.gameState) {
            const state = window.game.gameState;
            const hqs = state.board.tiles.filter(t => t.building && t.building.type === 'hq');
            return {
                currentPlayer: state.current_player,
                day: state.day,
                numHqs: hqs.length,
                hqs: hqs.map(h => ({
                    x: h.x,
                    y: h.y,
                    owner: h.building.owner
                })),
                playerFunds: state.players
            };
        }
        return null;
    """)
    
    print("\nGame info:")
    print(json.dumps(game_info, indent=2))
    
finally:
    driver.quit()
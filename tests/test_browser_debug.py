#!/usr/bin/env python3
"""
Debug browser console output
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import requests
import json

def rpc_call(method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    }
    response = requests.post("http://localhost:5000/api", json=payload)
    return response.json().get("result", response.json())

# Create test game
game_id = f'browser_debug_{int(time.time())}'
print(f"Creating test game: {game_id}")

result = rpc_call('game_create_v2', {
    'token': game_id,
    'map_name': 'test',
    'players': [
        {'name': 'Player 1', 'color': 'Red', 'sprite_color': 'RED'},
        {'name': 'Player 2', 'color': 'Blue', 'sprite_color': 'BLUE'}
    ]
})

# Create units
rpc_call('unit_create', {'token': game_id, 'player_id': 0, 'unit_type': 'INFANTRY', 'x': 2, 'y': 3})
rpc_call('army_end_turn', {'token': game_id})
rpc_call('unit_create', {'token': game_id, 'player_id': 1, 'unit_type': 'INFANTRY', 'x': 3, 'y': 3})
rpc_call('army_end_turn', {'token': game_id})

# Setup browser
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
# Enable logging
options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

driver = webdriver.Chrome(options=options)

try:
    # Navigate to game
    url = f"http://localhost:5000/game/{game_id}"
    driver.get(url)
    time.sleep(3)  # Wait for game to load
    
    # Execute click
    driver.execute_script("""
        const canvas = document.getElementById('game-canvas');
        const rect = canvas.getBoundingClientRect();
        const clickEvent = new MouseEvent('click', {
            view: window,
            bubbles: true,
            cancelable: true,
            clientX: rect.left + 2 * 32 + 16,
            clientY: rect.top + 3 * 32 + 16
        });
        canvas.dispatchEvent(clickEvent);
    """)
    
    # Wait for async operations
    time.sleep(3)
    
    # Get ALL console logs
    logs = driver.get_log('browser')
    print("\nBrowser Console Output:")
    print("=" * 60)
    for log in logs:
        level = log['level']
        message = log['message']
        # Clean up the message (remove timestamp and source info)
        if '" ' in message:
            message = message.split('" ', 1)[1]
        print(f"[{level}] {message}")
        
finally:
    driver.quit()

print(f"\nGame URL: http://localhost:5000/game/{game_id}")
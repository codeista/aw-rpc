#!/usr/bin/env python3
"""
Test what actually happens in the frontend
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
game_id = f'frontend_test_{int(time.time())}'
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

driver = webdriver.Chrome(options=options)

try:
    # Navigate to game
    url = f"http://localhost:5000/game/{game_id}"
    driver.get(url)
    time.sleep(3)  # Wait for game to load
    
    # Check what JavaScript file is loaded
    scripts = driver.find_elements(By.TAG_NAME, 'script')
    js_file = None
    for script in scripts:
        src = script.get_attribute('src')
        if src and 'game' in src:
            js_file = src
            break
    
    print(f"\nLoaded JavaScript: {js_file}")
    
    # Execute JavaScript to check game state and simulate click
    result = driver.execute_script("""
        // Check if game exists
        if (!window.game) {
            return { error: "No game object found" };
        }
        
        const game = window.game;
        
        // Initial state
        const initialState = {
            boardExists: !!game.board,
            selectedBefore: game.board && game.board.selected,
            highlightsBefore: 0
        };
        
        if (game.board && game.board.grid) {
            game.board.grid.forEach(tile => {
                if (tile.can_be_moved_to) initialState.highlightsBefore++;
            });
        }
        
        // Find canvas and simulate click at (2,3)
        const canvas = document.getElementById('game-canvas');
        if (!canvas) {
            return { error: "No canvas found" };
        }
        
        // Calculate click position
        const tileSize = 32;
        const clickX = 2 * tileSize + tileSize / 2;
        const clickY = 3 * tileSize + tileSize / 2;
        
        // Create click event
        const rect = canvas.getBoundingClientRect();
        const clickEvent = new MouseEvent('click', {
            view: window,
            bubbles: true,
            cancelable: true,
            clientX: rect.left + clickX,
            clientY: rect.top + clickY
        });
        
        // Dispatch click
        canvas.dispatchEvent(clickEvent);
        
        // Wait for async operations and check results
        return new Promise(resolve => {
            setTimeout(() => {
                const afterState = {
                    selectedAfter: game.board && game.board.selected,
                    highlightsAfter: 0,
                    updateMethodExists: typeof game.updateMovementHighlights === 'function'
                };
                
                if (game.board && game.board.grid) {
                    game.board.grid.forEach(tile => {
                        if (tile.can_be_moved_to) afterState.highlightsAfter++;
                    });
                }
                
                // Try to manually call updateMovementHighlights
                if (afterState.updateMethodExists && game.board && game.board.selected) {
                    game.updateMovementHighlights().then(() => {
                        // Count highlights again
                        let finalHighlights = 0;
                        game.board.grid.forEach(tile => {
                            if (tile.can_be_moved_to) finalHighlights++;
                        });
                        
                        resolve({
                            ...initialState,
                            ...afterState,
                            finalHighlights,
                            selectedPos: game.board.selected ? 
                                {x: game.board.selected.x, y: game.board.selected.y} : null
                        });
                    }).catch(err => {
                        resolve({
                            ...initialState,
                            ...afterState,
                            updateError: err.toString()
                        });
                    });
                } else {
                    resolve({
                        ...initialState,
                        ...afterState
                    });
                }
            }, 2000); // Wait 2 seconds
        });
    """)
    
    print("\nFrontend Test Results:")
    print("=" * 40)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"Board exists: {result.get('boardExists', False)}")
        print(f"Update method exists: {result.get('updateMethodExists', False)}")
        print(f"\nBefore click:")
        print(f"  Selected: {result.get('selectedBefore', False)}")
        print(f"  Highlights: {result.get('highlightsBefore', 0)}")
        print(f"\nAfter click:")
        print(f"  Selected: {result.get('selectedAfter', False)}")
        if result.get('selectedPos'):
            print(f"  Selected position: ({result['selectedPos']['x']}, {result['selectedPos']['y']})")
        print(f"  Highlights: {result.get('highlightsAfter', 0)}")
        
        if 'finalHighlights' in result:
            print(f"\nAfter manual update:")
            print(f"  Highlights: {result['finalHighlights']}")
            
        if 'updateError' in result:
            print(f"\n❌ Update error: {result['updateError']}")
    
    # Get console logs
    logs = driver.get_log('browser')
    if logs:
        print("\nBrowser console logs:")
        for log in logs[-5:]:
            if log['level'] == 'SEVERE':
                print(f"  ❌ {log['message']}")
            else:
                print(f"  ℹ️  {log['message']}")
                
finally:
    driver.quit()

print(f"\nGame URL: http://localhost:5000/game/{game_id}")
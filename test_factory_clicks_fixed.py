#!/usr/bin/env python3
"""
Test factory clicks using Selenium - fixed version
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import json
import requests

def test_factory_clicks():
    # First create a game using requests
    print("1. Creating test game via API...")
    response = requests.post('http://localhost:5000/api', json={
        'jsonrpc': '2.0',
        'method': 'game_create_test',
        'params': {},
        'id': 1
    })
    
    game_data = response.json()
    game_token = game_data['result']['token']
    print(f"Created game: {game_token}")
    
    # Set up Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    print("\n2. Starting Chrome driver...")
    driver = webdriver.Chrome(options=options)
    
    try:
        # Navigate to the game
        print(f"\n3. Loading game at /game/{game_token}")
        driver.get(f"http://localhost:5000/game/{game_token}")
        
        # Wait for game to load
        print("Waiting for game to load...")
        time.sleep(5)  # Give it more time
        
        # Check if game loaded
        print("\n4. Checking if game loaded...")
        is_loaded = driver.execute_script("""
            return !!(window.board && window.board.grid && window.two);
        """)
        print(f"Game loaded: {is_loaded}")
        
        if not is_loaded:
            # Try to debug what's missing
            debug_info = driver.execute_script("""
                return {
                    hasWindow: !!window,
                    hasBoard: !!window.board,
                    hasGrid: !!(window.board && window.board.grid),
                    hasTwo: !!window.two,
                    hasTileAt: !!window.tileAt,
                    hasUnitCreate: !!window.unitCreate
                };
            """)
            print(f"Debug info: {json.dumps(debug_info, indent=2)}")
            return
        
        # Check game state
        print("\n5. Checking game state...")
        game_state = driver.execute_script("""
            return {
                currentTurn: window.board.current_turn,
                redFunds: window.board.red_funds,
                blueFunds: window.board.blue_funds,
                gridSize: window.board.grid.length
            };
        """)
        print(f"Game state: {json.dumps(game_state, indent=2)}")
        
        # Find the RED factory
        print("\n6. Finding RED factory at (0,4)...")
        factory_info = driver.execute_script("""
            const tile = window.board.grid.find(t => t.x === 0 && t.y === 4);
            if (!tile) return null;
            return {
                x: tile.x,
                y: tile.y,
                terrain: tile.mapTile ? tile.mapTile.type : 'unknown',
                army: tile.mapTile ? tile.mapTile.army : 'unknown',
                hasUnit: !!tile.unit
            };
        """)
        print(f"Factory info: {json.dumps(factory_info, indent=2)}")
        
        # Try clicking using JavaScript directly
        print("\n7. Simulating click via JavaScript...")
        click_result = driver.execute_script("""
            // Find canvas
            const canvas = document.querySelector('#draw canvas');
            if (!canvas) return 'No canvas found';
            
            // Create click event
            const clickEvent = new MouseEvent('click', {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: 8,
                clientY: 88,
                offsetX: 8,
                offsetY: 88
            });
            
            // Dispatch the event
            canvas.dispatchEvent(clickEvent);
            
            return 'Click dispatched';
        """)
        print(f"Click result: {click_result}")
        
        time.sleep(2)
        
        # Check if modal appeared
        print("\n8. Checking if modal appeared...")
        modal_check = driver.execute_script("""
            const modal = document.getElementById('modalcreate');
            if (!modal) return 'Modal element not found';
            return {
                exists: true,
                display: modal.style.display,
                visible: modal.style.display === 'block'
            };
        """)
        print(f"Modal state: {json.dumps(modal_check, indent=2)}")
        
        # Get console messages
        print("\n9. Recent console activity:")
        console_msgs = driver.execute_script("""
            // Capture console messages
            if (!window.consoleLogs) window.consoleLogs = [];
            const originalLog = console.log;
            console.log = function() {
                window.consoleLogs.push(Array.from(arguments).join(' '));
                originalLog.apply(console, arguments);
            };
            
            // Return last 10 messages
            return window.consoleLogs.slice(-10);
        """)
        
        # Try direct unitCreate call
        print("\n10. Trying direct unitCreate call...")
        direct_result = driver.execute_script("""
            try {
                const tile = window.board.grid.find(t => t.x === 0 && t.y === 4);
                if (!tile) return 'Tile not found';
                if (!window.unitCreate) return 'unitCreate function not found';
                
                console.log('Calling unitCreate directly...');
                window.unitCreate(tile);
                
                // Check modal again
                const modal = document.getElementById('modalcreate');
                return {
                    called: true,
                    modalVisible: modal && modal.style.display === 'block'
                };
            } catch (e) {
                return 'Error: ' + e.message;
            }
        """)
        print(f"Direct call result: {json.dumps(direct_result, indent=2)}")
        
        # Final modal check
        time.sleep(1)
        final_check = driver.execute_script("""
            const modal = document.getElementById('modalcreate');
            return modal ? modal.style.display : 'Modal not found';
        """)
        print(f"\n11. Final modal display value: {final_check}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\nClosing browser...")
        driver.quit()

if __name__ == "__main__":
    test_factory_clicks()
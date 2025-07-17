#!/usr/bin/env python3
"""
Test factory clicks using Selenium to diagnose the issue
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import json

def test_factory_clicks():
    # Set up Chrome options for headless mode
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # Enable console logging
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    
    print("Starting Chrome driver...")
    driver = webdriver.Chrome(options=options)
    
    try:
        # Create a new game
        print("\n1. Creating new test game...")
        driver.get("http://localhost:5000/api")
        
        # Call game_create_test
        driver.execute_script("""
            fetch('/api', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'game_create_test',
                    params: {},
                    id: 1
                })
            })
            .then(r => r.json())
            .then(data => {
                window.testGameToken = data.result.token;
                console.log('Created test game:', data.result.token);
            });
        """)
        
        time.sleep(2)
        
        # Get the game token
        game_token = driver.execute_script("return window.testGameToken")
        print(f"Created game: {game_token}")
        
        # Navigate to the game
        print(f"\n2. Loading game at /game/{game_token}")
        driver.get(f"http://localhost:5000/game/{game_token}")
        
        # Wait for game to load
        print("Waiting for game to load...")
        time.sleep(3)
        
        # Check initial game state
        print("\n3. Checking game state...")
        game_state = driver.execute_script("""
            if (!window.board) return 'Board not loaded';
            return {
                currentTurn: window.board.current_turn,
                redFunds: window.board.red_funds,
                blueFunds: window.board.blue_funds,
                hasCanvas: !!document.querySelector('#draw canvas')
            };
        """)
        print(f"Game state: {json.dumps(game_state, indent=2)}")
        
        # Find factories
        print("\n4. Finding factories...")
        factories = driver.execute_script("""
            if (!window.board || !window.board.grid) return [];
            return window.board.grid
                .filter(t => t.mapTile && t.mapTile.type === 'FACTORY')
                .map(t => ({
                    x: t.x,
                    y: t.y,
                    army: t.mapTile.army,
                    hasUnit: !!t.unit
                }));
        """)
        print(f"Found {len(factories)} factories:")
        for f in factories:
            print(f"  - Factory at ({f['x']}, {f['y']}): {f['army']} {'(occupied)' if f['hasUnit'] else '(empty)'}")
        
        # Find RED factory at (0,4)
        red_factory = next((f for f in factories if f['x'] == 0 and f['y'] == 4), None)
        if not red_factory:
            print("ERROR: No RED factory found at (0,4)")
            return
        
        print(f"\n5. Testing click on RED factory at (0, 4)...")
        
        # Get canvas element
        canvas = driver.find_element(By.CSS_SELECTOR, "#draw canvas")
        
        # Calculate click position (tile 0,4 with TILESIZE=16)
        # x = 0 * 16 + 8 = 8 (center of tile)
        # y = 4 * 16 + 16 + 8 = 88 (account for offset + center)
        click_x = 8
        click_y = 88
        
        print(f"Clicking at canvas coordinates ({click_x}, {click_y})")
        
        # Clear console logs
        driver.get_log('browser')
        
        # Perform click
        ActionChains(driver).move_to_element_with_offset(canvas, click_x, click_y).click().perform()
        
        # Wait a bit
        time.sleep(1)
        
        # Get console logs
        print("\n6. Console logs after click:")
        logs = driver.get_log('browser')
        for log in logs:
            if 'favicon' not in log['message']:
                print(f"  [{log['level']}] {log['message']}")
        
        # Check if modal appeared
        print("\n7. Checking if modal appeared...")
        modal_visible = driver.execute_script("""
            const modal = document.getElementById('modalcreate');
            return modal && modal.style.display === 'block';
        """)
        print(f"Modal visible: {modal_visible}")
        
        if not modal_visible:
            # Try manual trigger
            print("\n8. Trying manual trigger...")
            result = driver.execute_script("""
                const tile = window.board.grid.find(t => t.x === 0 && t.y === 4);
                if (tile && window.unitCreate) {
                    console.log('Manually calling unitCreate');
                    window.unitCreate(tile);
                    return 'Called unitCreate';
                }
                return 'Could not call unitCreate';
            """)
            print(f"Manual trigger result: {result}")
            
            time.sleep(1)
            
            # Check again
            modal_visible = driver.execute_script("""
                const modal = document.getElementById('modalcreate');
                return modal && modal.style.display === 'block';
            """)
            print(f"Modal visible after manual trigger: {modal_visible}")
        
        # Get any errors
        print("\n9. Checking for JavaScript errors...")
        errors = driver.execute_script("""
            return window.lastError || 'No errors captured';
        """)
        print(f"Errors: {errors}")
        
        # Detailed click handler check
        print("\n10. Checking click handler chain...")
        handlers = driver.execute_script("""
            const canvas = document.querySelector('#draw canvas');
            if (!canvas) return 'No canvas found';
            
            // Check what handlers are attached
            const handlers = [];
            if (canvas.onclick) handlers.push('onclick');
            if (canvas.addEventListener) {
                // Can't directly inspect event listeners, but we know they exist
                handlers.push('addEventListener (multiple)');
            }
            
            return {
                handlers: handlers,
                hasAdvanceWarsCanvasClick: typeof window.advanceWarsCanvasClick === 'function',
                hasUnitCreate: typeof window.unitCreate === 'function',
                hasTileAt: typeof window.tileAt === 'function'
            };
        """)
        print(f"Handler info: {json.dumps(handlers, indent=2)}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\nClosing browser...")
        driver.quit()

if __name__ == "__main__":
    test_factory_clicks()
#!/usr/bin/env python3
"""
Test v2 movement mechanics
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests

def create_test_game():
    """Create a v2 test game with units"""
    import random
    import string
    token = "movement_" + ''.join(random.choices(string.ascii_lowercase, k=6))
    
    resp = requests.post("http://localhost:5000/api", json={
        "jsonrpc": "2.0",
        "method": "game_create_test",  # High funds for testing
        "params": {"token": token},
        "id": "1"
    })
    
    result = resp.json()
    if "error" in result:
        raise Exception(f"Failed to create game: {result['error']}")
    print("✅ Created test game with high funds")
    
    # Create a unit at RED factory
    resp = requests.post("http://localhost:5000/api", json={
        "jsonrpc": "2.0",
        "method": "produce_unit",
        "params": {
            "token": token,
            "x": 0,
            "y": 4,
            "unit_type": "INFANTRY"
        },
        "id": "2"
    })
    print("✅ Created INFANTRY at (0,4)")
    
    # End turn twice to make unit moveable
    for i in range(2):
        resp = requests.post("http://localhost:5000/api", json={
            "jsonrpc": "2.0",
            "method": "army_end_turn",
            "params": {"token": token},
            "id": str(i+3)
        })
    
    print("✅ Advanced to next turn - unit should be moveable")
    return token

def test_movement():
    """Test unit selection and movement"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=options)
    
    try:
        game_id = create_test_game()
        
        # Load game page
        driver.get(f"http://localhost:5000/game/{game_id}")
        print("✅ Loaded game page")
        
        # Wait for canvas to load
        canvas = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "game-canvas"))
        )
        time.sleep(2)  # Allow time for full load
        
        # Get JavaScript console logs
        driver.execute_script("console.log('=== MOVEMENT TEST START ===');")
        
        # Click on the unit at (0,4) to select it
        print("\n🎯 Clicking on unit at (0,4) to select...")
        actions = ActionChains(driver)
        # Click at center of tile (0,4)
        offset_x = 0 * 32 + 16
        offset_y = 4 * 32 + 16
        actions.move_to_element(canvas).click().perform()
        actions.move_to_element_with_offset(canvas, offset_x - 192, offset_y - 160).click().perform()
        time.sleep(1)
        
        # Check if unit was selected by looking for highlights
        highlights = driver.execute_script("""
            const board = window.game.board;
            if (!board) return null;
            
            // Count highlighted tiles
            let moveCount = 0;
            let attackCount = 0;
            
            for (const tile of board.grid) {
                if (tile.can_be_moved_to) moveCount++;
                if (tile.can_be_attacked) attackCount++;
            }
            
            return {
                selected: board.selected,
                moveHighlights: moveCount,
                attackHighlights: attackCount
            };
        """)
        
        if highlights and highlights['selected']:
            print(f"✅ Unit selected at {highlights['selected']}")
            print(f"   Movement tiles: {highlights['moveHighlights']}")
            print(f"   Attack tiles: {highlights['attackHighlights']}")
        else:
            print("❌ Unit not selected - no highlights found")
            
        # Try to move to (1,4)
        print("\n🎯 Clicking on (1,4) to move unit...")
        offset_x = 1 * 32 + 16
        offset_y = 4 * 32 + 16
        actions.move_to_element_with_offset(canvas, offset_x - 192, offset_y - 160).click().perform()
        time.sleep(1)
        
        # Check if unit moved
        unit_positions = driver.execute_script("""
            const board = window.game.board;
            if (!board) return null;
            
            const positions = [];
            for (const tile of board.grid) {
                if (tile.unit && tile.unit.type === 'INFANTRY') {
                    positions.push({x: tile.x, y: tile.y});
                }
            }
            return positions;
        """)
        
        if unit_positions:
            print(f"✅ Unit positions after move: {unit_positions}")
            if any(p['x'] == 1 and p['y'] == 4 for p in unit_positions):
                print("✅ MOVEMENT SUCCESSFUL! Unit moved from (0,4) to (1,4)")
            else:
                print("❌ Movement failed - unit still at original position")
        
        # Get console logs for debugging
        logs = driver.get_log('browser')
        print("\n📋 Browser console logs:")
        for log in logs[-20:]:  # Last 20 logs
            if 'game_v2_simple.js' in log.get('source', ''):
                print(f"  {log['level']}: {log['message']}")
                
        # Take screenshot
        driver.save_screenshot("/tmp/movement_test.png")
        print("\n✅ Screenshot saved to /tmp/movement_test.png")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        driver.quit()

if __name__ == "__main__":
    print("=== V2 Movement Test ===\n")
    test_movement()
    print("\n=== Test Complete ===")
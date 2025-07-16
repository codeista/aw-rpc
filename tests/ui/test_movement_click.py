"""
Test clicking on movement highlights to execute moves
"""

import pytest
import time
from .test_base_selenium import BaseSeleniumTest


class TestMovementClick(BaseSeleniumTest):
    """Test that clicking on movement highlights executes moves"""
    
    def test_click_movement_highlight_executes_move(self):
        """Test that clicking on a movement highlight executes the movement"""
        # Ensure we're on RED turn
        self.ensure_turn('RED')
        
        # Get RED units
        units = self.get_unit_positions('RED')
        
        # Find a unit that can move
        land_unit = None
        for unit in units:
            if unit['unit_type'] in ['INFANTRY', 'TANK', 'RECON', 'MECH']:
                land_unit = unit
                break
        
        if not land_unit:
            pytest.skip("No land unit found")
        
        print(f"Testing movement with {land_unit['unit_type']} at ({land_unit['x']}, {land_unit['y']})")
        
        # Check the tile info before clicking
        tile_before_click = self.driver.execute_script("""
            const tile = window.tileAt(arguments[0] * 16 + 8, arguments[1] * 16 + 8 + 16);
            return {
                x: tile?.x,
                y: tile?.y,
                hasUnit: !!tile?.unit,
                unitArmy: tile?.unit?.army,
                currentTurn: window.board?.current_turn,
                armyMatch: tile?.unit?.army === window.board?.current_turn
            };
        """, land_unit['x'], land_unit['y'])
        print(f"Tile before click: {tile_before_click}")
        
        # Check which click handler is active and monitor all click events
        self.driver.execute_script("""
            const canvas = document.querySelector('#draw canvas');
            
            console.error('🔍 Click handler diagnostics:');
            console.error('- Canvas onclick handler:', canvas?.onclick?.name || 'none');
            console.error('- window.advanceWarsCanvasClick exists:', typeof window.advanceWarsCanvasClick);
            console.error('- window.canvasClick exists:', typeof window.canvasClick);
            console.error('- window.advanceWarsUnitSelect exists:', typeof window.advanceWarsUnitSelect);
            
            // Override the actual canvas click handler to see what's happening
            if (canvas && canvas.onclick) {
                const originalHandler = canvas.onclick;
                canvas.onclick = function(event) {
                    console.error('🖱️ Canvas click intercepted - calling original handler:', originalHandler.name);
                    console.error('🖱️ Click coords:', event.offsetX, event.offsetY);
                    
                    // Call the original handler
                    try {
                        const result = originalHandler.call(this, event);
                        console.error('🖱️ Original handler completed, result:', result);
                        return result;
                    } catch (e) {
                        console.error('🖱️ Original handler error:', e);
                        throw e;
                    }
                };
            }
            
            // Monitor advanceWarsUnitSelect calls
            if (window.advanceWarsUnitSelect) {
                const original = window.advanceWarsUnitSelect;
                window.advanceWarsUnitSelect = function(tile) {
                    console.error('🎯 advanceWarsUnitSelect called with:', tile);
                    try {
                        const result = original.call(this, tile);
                        console.error('🎯 advanceWarsUnitSelect completed');
                        return result;
                    } catch (e) {
                        console.error('🎯 advanceWarsUnitSelect error:', e);
                        throw e;
                    }
                };
            }
        """)
        
        # 1. Click the unit to select it
        print(f"Clicking unit at ({land_unit['x']}, {land_unit['y']})")
        self.click_tile(land_unit['x'], land_unit['y'])
        self.wait_for_animation(0.5)
        
        # Check console logs for debugging
        console_logs = self.driver.get_log('browser')
        
        # Show all recent console logs to see what's happening
        print("All recent console logs:")
        for log in console_logs[-10:]:
            print(f"  {log['level']}: {log['message']}")
        
        # Also check specifically for handler-related logs
        handler_logs = [log for log in console_logs if any(keyword in log['message'].lower() for keyword in ['click', 'handler', 'canvas', 'select'])]
        if handler_logs:
            print("Handler-related logs:")
            for log in handler_logs[-5:]:
                print(f"  {log['message']}")
        else:
            print("No handler-related logs found")
        
        # Wait for unit selection to complete (both highlights and gameState.selectedUnit)
        def wait_for_unit_selection():
            state = self.get_game_state()
            return (state.get('movementHighlights', 0) > 0 and 
                    state.get('selectedUnit') is not None)
        
        if not self.wait_for_highlights("movement", timeout=3):
            # Try triggering highlights manually
            self.driver.execute_script("""
                window.highlightMovementRange(arguments[0], arguments[1]);
            """, land_unit['x'], land_unit['y'])
            self.wait_for_animation(1.0)
        
        # Also wait for gameState.selectedUnit to be set by the RPC Promise
        from selenium.webdriver.support.ui import WebDriverWait
        try:
            WebDriverWait(self.driver, 5).until(lambda driver: 
                driver.execute_script("return window.gameState?.selectedUnit != null;")
            )
            print("✅ Unit selection RPC completed")
        except:
            print("⚠️ Timeout waiting for gameState.selectedUnit to be set")
        
        # Check we have movement highlights
        highlights = self.get_movement_highlights()
        print(f"Movement highlights: {len(highlights)}")
        assert len(highlights) > 0, "No movement highlights after unit selection"
        
        # Get unit's original position 
        original_unit = self.find_unit_at(land_unit['x'], land_unit['y'])
        assert original_unit, "Unit not found at original position"
        print(f"Original unit: {original_unit}")
        
        # Pick a target tile from highlights
        target_tile = highlights[0]  # Use first highlight
        print(f"Target tile: ({target_tile['x']}, {target_tile['y']})")
        
        # Take screenshot before move
        self.take_screenshot("before_movement_click")
        
        # Check game state before click and verify gameState object
        state_before = self.get_game_state()
        gamestate_info = self.driver.execute_script("""
            return {
                gameStateExists: !!window.gameState,
                selectedUnitExists: !!window.gameState?.selectedUnit,
                selectedUnitValue: window.gameState?.selectedUnit,
                boardSelectedExists: !!window.board?.selected,
                boardSelectedValue: window.board?.selected
            };
        """)
        print(f"State before move click: selected={state_before.get('selected') is not None}, selectedUnit={state_before.get('selectedUnit') is not None}")
        print(f"GameState details: {gamestate_info}")
        
        # Check if the target tile has can_be_moved_to flag
        tile_info = self.driver.execute_script("""
            const tile = window.tileAt(arguments[0] * 16 + 8, arguments[1] * 16 + 8 + 16);
            return {
                x: tile?.x,
                y: tile?.y,
                can_be_moved_to: tile?.can_be_moved_to,
                can_be_attacked: tile?.can_be_attacked
            };
        """, target_tile['x'], target_tile['y'])
        print(f"Target tile info: {tile_info}")
        
        # 2. Click on the highlighted tile to move
        print(f"Clicking target tile at ({target_tile['x']}, {target_tile['y']})")
        self.click_tile(target_tile['x'], target_tile['y'])
        self.wait_for_animation(1.0)
        
        # Take screenshot after move
        self.take_screenshot("after_movement_click")
        
        # 3. Verify the unit moved
        # Check original position is empty
        unit_at_original = self.find_unit_at(land_unit['x'], land_unit['y'])
        print(f"Unit at original position: {unit_at_original}")
        
        # Check target position has the unit
        unit_at_target = self.find_unit_at(target_tile['x'], target_tile['y'])
        print(f"Unit at target position: {unit_at_target}")
        
        assert unit_at_original is None, f"Unit still at original position: {unit_at_original}"
        assert unit_at_target is not None, f"No unit found at target position ({target_tile['x']}, {target_tile['y']})"
        assert unit_at_target['type'] == original_unit['type'], f"Wrong unit type at target: {unit_at_target['type']} vs {original_unit['type']}"
        
    def test_debug_click_handling(self):
        """Debug test to see what happens when we click tiles"""
        # Ensure we're on RED turn  
        self.ensure_turn('RED')
        
        # Get RED units
        units = self.get_unit_positions('RED')
        land_unit = units[0] if units else None
        
        if not land_unit:
            pytest.skip("No units found")
            
        print(f"Debug test with {land_unit['unit_type']} at ({land_unit['x']}, {land_unit['y']})")
        
        # Enable detailed logging
        self.driver.execute_script("""
            // Enable detailed click logging
            const originalLog = console.log;
            const originalError = console.error;
            
            window.debugClickLog = [];
            
            console.log = function(...args) {
                window.debugClickLog.push(['LOG', ...args]);
                return originalLog.apply(console, args);
            };
            
            console.error = function(...args) {
                window.debugClickLog.push(['ERROR', ...args]);
                return originalError.apply(console, args);
            };
            
            // Also log render_legacy click handler activity
            if (window.advanceWarsCanvasClick) {
                const originalClick = window.advanceWarsCanvasClick;
                window.advanceWarsCanvasClick = function(event) {
                    console.log('🔵 render_legacy click handler called');
                    return originalClick.call(this, event);
                };
            }
        """)
        
        # Click the unit
        print("Clicking unit...")
        self.click_tile(land_unit['x'], land_unit['y'])
        self.wait_for_animation(0.5)
        
        # Get the click log
        click_log = self.driver.execute_script("return window.debugClickLog || [];")
        print("Click log:")
        for entry in click_log[-10:]:  # Show last 10 entries
            print(f"  {entry}")
        
        # Check game state
        state = self.get_game_state()
        print(f"Game state after click: selected={state.get('selected')}, highlights={state.get('movementHighlights', 0)}")
        
        # Check if click handlers are properly set up
        handlers_info = self.driver.execute_script("""
            const canvas = document.querySelector('#draw canvas');
            return {
                canvasOnclick: !!canvas?.onclick,
                canvasOnclickName: canvas?.onclick?.name || 'unknown',
                windowAdvanceWarsCanvasClick: typeof window.advanceWarsCanvasClick,
                windowCanvasClick: typeof window.canvasClick,
                renderLegacyLoaded: typeof window.tileAt,
                clickHandlerLoaded: typeof window.clickHandler,
                centralizedHandlerActive: canvas?.onclick?.name === 'centralizedClickHandler'
            };
        """)
        
        print("Click handlers status:")
        for key, value in handlers_info.items():
            print(f"  {key}: {value}")
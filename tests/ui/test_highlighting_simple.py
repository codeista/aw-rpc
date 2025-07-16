"""
Simple test to verify RPC fix for movement highlights
"""

import pytest
import time
from .test_base_selenium import BaseSeleniumTest


class TestSimpleHighlights(BaseSeleniumTest):
    """Simple tests to verify movement highlights work"""
    
    def test_movement_highlights_via_rpc(self):
        """Test that movement highlights work via direct RPC call"""
        # Get current turn units
        current_turn = self.get_current_turn()
        units = self.get_unit_positions(current_turn)
        
        # Find a land unit
        land_unit = None
        for unit in units:
            if unit['unit_type'] in ['INFANTRY', 'TANK', 'RECON', 'MECH']:
                land_unit = unit
                break
        
        if not land_unit:
            pytest.skip("No land unit found")
        
        print(f"Testing with {land_unit['unit_type']} at ({land_unit['x']}, {land_unit['y']})")
        
        # Call highlightMovementRange directly
        self.driver.execute_script("""
            window.highlightMovementRange(arguments[0], arguments[1]);
        """, land_unit['x'], land_unit['y'])
        
        # Wait for RPC to complete
        time.sleep(1.0)
        
        # Check highlights
        state = self.get_game_state()
        highlights = state.get('movementHighlights', 0)
        
        print(f"Movement highlights: {highlights}")
        assert highlights > 0, "No movement highlights appeared"
        
        # Get the actual highlight data
        highlight_data = self.get_movement_highlights()
        print(f"Highlight tiles: {len(highlight_data)}")
        
        assert len(highlight_data) > 0, "No highlight data found"
        assert len(highlight_data) == highlights, f"Highlight count mismatch: {len(highlight_data)} vs {highlights}"
    
    def test_attack_targets_rpc(self):
        """Test getting attack targets via RPC"""
        # Get current turn units
        current_turn = self.get_current_turn()
        units = self.get_unit_positions(current_turn)
        
        # Find a unit that can attack
        attack_unit = None
        for unit in units:
            if unit['unit_type'] in ['TANK', 'INFANTRY', 'ARTILLERY', 'BOMBER']:
                attack_unit = unit
                break
        
        if not attack_unit:
            pytest.skip("No attack unit found")
        
        print(f"Testing attack targets for {attack_unit['unit_type']} at ({attack_unit['x']}, {attack_unit['y']})")
        
        # Call get_attack_targets RPC
        result = self.driver.execute_script("""
            return window.jsonrpc('get_attack_targets', {
                unit_x: arguments[0], 
                unit_y: arguments[1]
            }).then(result => {
                console.log('Attack targets result:', result);
                return result;
            }).catch(error => {
                console.error('Attack targets error:', error);
                return {error: error.message};
            });
        """, attack_unit['x'], attack_unit['y'])
        
        # Wait for promise
        time.sleep(1.0)
        
        print(f"Attack targets result: {result}")
        
        # Note: This test is just to explore the get_attack_targets RPC
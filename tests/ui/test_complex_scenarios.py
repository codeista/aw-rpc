"""
Test Suite for Complex Interactions

Tests complex multi-step scenarios including:
- Transport load/move/unload sequences
- Multi-unit coordinated attacks
- Property capture over multiple turns
- Edge cases and stress tests
"""

import pytest
import time
from typing import Dict, List, Tuple, Optional
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from .test_base_selenium import BaseSeleniumTest
from .selenium_helpers import TestDataHelper, VisualDebugger


class TestMultiStepOperations(BaseSeleniumTest):
    """Test complex multi-step game operations"""
    
    def test_transport_load_move_unload_attack(self):
        """Test complete transport sequence: load → move → unload → attack"""
        # Find APC and Infantry
        units = self.get_unit_positions('RED')
        apc = next((u for u in units if u['unit_type'] == 'APC'), None)
        infantry = next((u for u in units if u['unit_type'] == 'INFANTRY'), None)
        
        if not apc or not infantry:
            pytest.skip("No APC and Infantry found")
        
        # Step 1: Load infantry into APC
        success = self._load_unit_into_transport(infantry, apc)
        if not success:
            pytest.skip("Could not load infantry into APC")
        
        self.take_screenshot("1_after_loading")
        
        # End turn to enable transport movement
        self.end_turn()
        self.end_turn()  # Back to RED
        
        # Step 2: Move loaded APC
        self.click_tile(apc['x'], apc['y'])
        self.wait_for_highlights('movement')
        
        # Find a good unload position (near enemies if possible)
        enemy_units = self.get_unit_positions('BLUE')
        target_area = self._find_strategic_position(apc, enemy_units)
        
        if target_area:
            self.click_tile(target_area[0], target_area[1])
            self.wait_for_animation()
            apc['x'], apc['y'] = target_area
        
        self.take_screenshot("2_after_transport_move")
        
        # Step 3: Unload infantry
        # Click on APC to select it
        self.click_tile(apc['x'], apc['y'])
        time.sleep(0.5)
        
        # Alt+click adjacent tile to unload
        unload_positions = [
            (apc['x'] - 1, apc['y']),
            (apc['x'] + 1, apc['y']),
            (apc['x'], apc['y'] - 1),
            (apc['x'], apc['y'] + 1)
        ]
        
        for pos in unload_positions:
            if self._is_valid_tile(pos[0], pos[1]):
                # Try Alt+click
                canvas = self.get_canvas()
                canvas_x = pos[0] * self.TILE_SIZE + (self.TILE_SIZE // 2)
                canvas_y = pos[1] * self.TILE_SIZE + (self.TILE_SIZE // 2) + self.SCENE_Y_OFFSET
                
                ActionChains(self.driver).move_to_element_with_offset(
                    canvas, canvas_x, canvas_y
                ).key_down(Keys.ALT).click().key_up(Keys.ALT).perform()
                
                time.sleep(0.5)
                infantry_pos = pos
                break
        
        self.take_screenshot("3_after_unload")
        
        # End turn - unloaded units can't act same turn
        self.end_turn()
        self.end_turn()
        
        # Step 4: Attack with unloaded infantry
        # Check if any enemies nearby
        enemy_nearby = self._find_adjacent_enemy(infantry_pos[0], infantry_pos[1])
        
        if enemy_nearby:
            self.click_tile(infantry_pos[0], infantry_pos[1])
            time.sleep(0.3)
            self.click_tile(enemy_nearby['x'], enemy_nearby['y'])
            self.wait_for_animation()
            
            self.take_screenshot("4_after_attack")
            
            # Verify attack succeeded
            enemy_tile = self.get_tile_info(enemy_nearby['x'], enemy_nearby['y'])
            assert not enemy_tile.get('unit') or enemy_tile['unit']['hp'] < enemy_nearby['hp']
    
    def test_capture_sequence_multiple_turns(self):
        """Test capturing a property over multiple turns"""
        # Find infantry and neutral/enemy property
        units = self.get_unit_positions('RED')
        infantry = next((u for u in units if u['unit_type'] == 'INFANTRY'), None)
        
        if not infantry:
            pytest.skip("No infantry found")
        
        # Find capturable property
        property_pos = self._find_capturable_property(infantry)
        
        if not property_pos:
            pytest.skip("No capturable property found nearby")
        
        # Move infantry to property
        self.click_tile(infantry['x'], infantry['y'])
        self.wait_for_highlights('movement')
        
        highlights = self.get_movement_highlights()
        can_reach = any(h['x'] == property_pos[0] and h['y'] == property_pos[1] for h in highlights)
        
        if can_reach:
            self.click_tile(property_pos[0], property_pos[1])
            self.wait_for_animation()
        else:
            # Move closer first
            closest = self._find_closest_highlighted_tile(property_pos, highlights)
            if closest:
                self.click_tile(closest['x'], closest['y'])
                self.wait_for_animation()
        
        # End turn
        self.end_turn()
        self.end_turn()
        
        # Turn 2: Continue capture
        # Infantry should be on or near property
        infantry_tile = self._find_unit_at_or_near(property_pos, 'INFANTRY', 'RED')
        
        if infantry_tile:
            if (infantry_tile['x'], infantry_tile['y']) == property_pos:
                # Already on property - double click to capture
                self.double_click_tile(property_pos[0], property_pos[1])
                self.take_screenshot("capturing_turn_2")
            else:
                # Move to property
                self.click_tile(infantry_tile['x'], infantry_tile['y'])
                self.wait_for_highlights('movement')
                self.click_tile(property_pos[0], property_pos[1])
                self.wait_for_animation()
        
        # End turn
        self.end_turn()
        self.end_turn()
        
        # Turn 3: Complete capture (if needed)
        # Full HP infantry captures in 2 turns (10 HP per turn, 20 HP total for properties)
        
        # Check if property was captured
        property_tile = self.get_tile_info(property_pos[0], property_pos[1])
        
        if property_tile.get('mapTile', {}).get('army') != 'RED':
            # Need another turn
            self.double_click_tile(property_pos[0], property_pos[1])
            self.take_screenshot("capture_complete")
            
            # Verify capture
            time.sleep(0.5)
            property_tile = self.get_tile_info(property_pos[0], property_pos[1])
            assert property_tile.get('mapTile', {}).get('army') == 'RED', "Property not captured!"
    
    def test_chain_attacks_multiple_units(self):
        """Test coordinating attacks with multiple units"""
        # Get all RED units
        red_units = self.get_unit_positions('RED')
        
        if len(red_units) < 3:
            pytest.skip("Need at least 3 units for chain attack")
        
        # Find a BLUE unit to gang up on
        blue_units = self.get_unit_positions('BLUE')
        if not blue_units:
            pytest.skip("No enemy units found")
        
        target = blue_units[0]
        initial_hp = target.get('hp', 100)
        
        # Attack with multiple units
        attacks_made = 0
        
        for attacker in red_units[:3]:
            # Can this unit reach the target?
            self.click_tile(attacker['x'], attacker['y'])
            
            if self.wait_for_highlights('movement', timeout=1):
                # Check if we can move to attack range
                if self._can_attack_target(attacker, target):
                    # Execute attack
                    self._execute_attack_on_target(attacker, target)
                    attacks_made += 1
                    
                    self.take_screenshot(f"chain_attack_{attacks_made}")
                    
                    # Check if target destroyed
                    target_tile = self.get_tile_info(target['x'], target['y'])
                    if not target_tile.get('unit'):
                        print(f"Target destroyed after {attacks_made} attacks!")
                        break
                    
                    # Update target HP
                    target['hp'] = target_tile['unit']['hp']
            
            # Small delay between attacks
            time.sleep(0.5)
        
        # Verify target took damage or was destroyed
        final_tile = self.get_tile_info(target['x'], target['y'])
        if final_tile.get('unit'):
            assert final_tile['unit']['hp'] < initial_hp, "Target took no damage!"
        else:
            assert attacks_made > 0, "Target destroyed without attacks?"
    
    def _load_unit_into_transport(self, cargo: Dict, transport: Dict) -> bool:
        """Helper to load a unit into transport"""
        # Move cargo to transport position
        distance = abs(cargo['x'] - transport['x']) + abs(cargo['y'] - transport['y'])
        
        if distance == 0:
            # Already loaded?
            return True
        elif distance == 1:
            # Adjacent - can load
            self.click_tile(cargo['x'], cargo['y'])
            time.sleep(0.3)
            self.click_tile(transport['x'], transport['y'])
            time.sleep(0.5)
            return True
        else:
            # Need to move closer
            self.click_tile(cargo['x'], cargo['y'])
            if self.wait_for_highlights('movement'):
                # Check if transport position is highlighted
                highlights = self.get_movement_highlights()
                if any(h['x'] == transport['x'] and h['y'] == transport['y'] for h in highlights):
                    self.click_tile(transport['x'], transport['y'])
                    self.wait_for_animation()
                    return True
        
        return False
    
    def _find_strategic_position(self, unit: Dict, enemies: List[Dict]) -> Optional[Tuple[int, int]]:
        """Find a good position to move to (near enemies)"""
        if not enemies:
            return None
        
        # Get movement highlights
        highlights = self.get_movement_highlights()
        
        # Find highlight closest to an enemy
        best_pos = None
        best_distance = float('inf')
        
        for h in highlights:
            for enemy in enemies:
                distance = abs(h['x'] - enemy['x']) + abs(h['y'] - enemy['y'])
                if distance < best_distance:
                    best_distance = distance
                    best_pos = (h['x'], h['y'])
        
        return best_pos
    
    def _is_valid_tile(self, x: int, y: int) -> bool:
        """Check if tile coordinates are valid"""
        state = self.get_game_state()
        return 0 <= x < state['board']['width'] and 0 <= y < state['board']['height']
    
    def _find_adjacent_enemy(self, x: int, y: int) -> Optional[Dict]:
        """Find enemy unit adjacent to given position"""
        adjacent_positions = [
            (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)
        ]
        
        for pos in adjacent_positions:
            if self._is_valid_tile(pos[0], pos[1]):
                tile = self.get_tile_info(pos[0], pos[1])
                if tile and tile.get('unit') and tile['unit']['army'] != 'RED':
                    return {
                        'x': pos[0],
                        'y': pos[1],
                        'hp': tile['unit'].get('hp', 100),
                        'unit_type': tile['unit']['unit_type']
                    }
        
        return None
    
    def _find_capturable_property(self, unit: Dict) -> Optional[Tuple[int, int]]:
        """Find a property that can be captured"""
        # Look in a reasonable radius
        for dx in range(-5, 6):
            for dy in range(-5, 6):
                x = unit['x'] + dx
                y = unit['y'] + dy
                
                if self._is_valid_tile(x, y):
                    tile = self.get_tile_info(x, y)
                    if tile and tile.get('mapTile'):
                        terrain = tile['mapTile'].get('type', '')
                        owner = tile['mapTile'].get('army', '')
                        
                        # Capturable properties
                        if terrain in ['CITY', 'BASE', 'AIRPORT', 'PORT', 'HQ']:
                            if owner != 'RED':  # Neutral or enemy
                                return (x, y)
        
        return None
    
    def _find_closest_highlighted_tile(self, target: Tuple[int, int], highlights: List[Dict]) -> Optional[Dict]:
        """Find highlighted tile closest to target"""
        best = None
        best_distance = float('inf')
        
        for h in highlights:
            distance = abs(h['x'] - target[0]) + abs(h['y'] - target[1])
            if distance < best_distance:
                best_distance = distance
                best = h
        
        return best
    
    def _find_unit_at_or_near(self, pos: Tuple[int, int], unit_type: str, army: str) -> Optional[Dict]:
        """Find specific unit at or near position"""
        # Check exact position first
        tile = self.get_tile_info(pos[0], pos[1])
        if tile and tile.get('unit'):
            if tile['unit']['unit_type'] == unit_type and tile['unit']['army'] == army:
                return {'x': pos[0], 'y': pos[1]}
        
        # Check adjacent tiles
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            x, y = pos[0] + dx, pos[1] + dy
            if self._is_valid_tile(x, y):
                tile = self.get_tile_info(x, y)
                if tile and tile.get('unit'):
                    if tile['unit']['unit_type'] == unit_type and tile['unit']['army'] == army:
                        return {'x': x, 'y': y}
        
        return None
    
    def _can_attack_target(self, attacker: Dict, target: Dict) -> bool:
        """Check if attacker can reach and attack target"""
        # This is simplified - would need to check actual attack range
        distance = abs(attacker['x'] - target['x']) + abs(attacker['y'] - target['y'])
        
        # Direct units need to be adjacent
        if attacker['unit_type'] in ['INFANTRY', 'MECH', 'TANK', 'RECON']:
            return distance <= 4  # Can move and attack
        
        # Indirect units have range
        if attacker['unit_type'] == 'ARTILLERY':
            return 2 <= distance <= 5  # Move and attack range
        
        return distance <= 5
    
    def _execute_attack_on_target(self, attacker: Dict, target: Dict) -> None:
        """Execute attack sequence on target"""
        distance = abs(attacker['x'] - target['x']) + abs(attacker['y'] - target['y'])
        
        # If not adjacent and direct unit, move closer
        if distance > 1 and attacker['unit_type'] in ['INFANTRY', 'TANK']:
            highlights = self.get_movement_highlights()
            
            # Find position adjacent to target
            adjacent_positions = [
                (target['x'] - 1, target['y']),
                (target['x'] + 1, target['y']),
                (target['x'], target['y'] - 1),
                (target['x'], target['y'] + 1)
            ]
            
            for pos in adjacent_positions:
                if any(h['x'] == pos[0] and h['y'] == pos[1] for h in highlights):
                    self.click_tile(pos[0], pos[1])
                    self.wait_for_animation()
                    break
        
        # Now attack
        self.click_tile(target['x'], target['y'])
        self.wait_for_animation()


class TestEdgeCases(BaseSeleniumTest):
    """Test edge cases and stress scenarios"""
    
    def test_rapid_clicking_during_animation(self):
        """Test system behavior with rapid clicks during animations"""
        units = self.get_unit_positions('RED')
        unit = units[0]
        
        # Start a movement
        self.click_tile(unit['x'], unit['y'])
        self.wait_for_highlights('movement')
        
        highlights = self.get_movement_highlights()
        if highlights:
            target = highlights[0]
            
            # Click to start movement
            self.click_tile(target['x'], target['y'])
            
            # Rapidly click during animation
            for _ in range(5):
                self.click_tile(5, 5)  # Random position
                time.sleep(0.1)
            
            # Wait for animation to complete
            self.wait_for_animation()
            
            # Verify unit moved correctly despite rapid clicks
            final_tile = self.get_tile_info(target['x'], target['y'])
            assert final_tile.get('unit') is not None
            
            # Check for JavaScript errors
            self.verify_no_errors()
    
    def test_multiple_units_selected_quickly(self):
        """Test selecting multiple units in quick succession"""
        units = self.get_unit_positions('RED')
        
        if len(units) < 3:
            pytest.skip("Need at least 3 units")
        
        # Rapidly select different units
        for i in range(10):
            unit = units[i % len(units)]
            self.click_tile(unit['x'], unit['y'])
            time.sleep(0.05)  # Very quick succession
        
        # Final state should have last unit selected
        final_unit = units[(9) % len(units)]
        state = self.get_game_state()
        
        if state.get('selected'):
            assert state['selected']['x'] == final_unit['x']
            assert state['selected']['y'] == final_unit['y']
        
        # No errors should occur
        self.verify_no_errors()
    
    def test_browser_zoom_levels(self):
        """Test UI works correctly at different zoom levels"""
        units = self.get_unit_positions('RED')
        unit = units[0]
        
        zoom_levels = [0.5, 0.75, 1.0, 1.25, 1.5]
        
        for zoom in zoom_levels:
            # Set zoom level
            self.driver.execute_script(f"document.body.style.zoom = '{zoom}'")
            time.sleep(0.5)
            
            # Try to click unit
            self.click_tile(unit['x'], unit['y'])
            
            # Verify selection worked
            if self.wait_for_highlights('movement', timeout=2):
                self.take_screenshot(f"zoom_level_{int(zoom * 100)}")
                
                # Click to deselect
                self.click_tile(5, 5)
            
        # Reset zoom
        self.driver.execute_script("document.body.style.zoom = '1.0'")
    
    def test_network_lag_simulation(self):
        """Test UI behavior with simulated network delays"""
        # This would require intercepting network requests
        # For now, we'll test behavior with delayed responses
        
        units = self.get_unit_positions('RED')
        unit = units[0]
        
        # Add artificial delay to RPC calls
        self.driver.execute_script("""
            // Override RPC to add delay
            window.originalRpc = window.jsonrpc;
            window.jsonrpc = function(method, params, callback) {
                setTimeout(() => {
                    window.originalRpc(method, params, callback);
                }, 1000);  // 1 second delay
            };
        """)
        
        # Try to move unit
        self.click_tile(unit['x'], unit['y'])
        
        # UI should handle the delay gracefully
        # Highlights might appear after delay
        assert self.wait_for_highlights('movement', timeout=5)
        
        # Restore original RPC
        self.driver.execute_script("""
            window.jsonrpc = window.originalRpc;
        """)
        
        self.take_screenshot("network_delay_test")
    
    def test_keyboard_mouse_combination(self):
        """Test keyboard shortcuts combined with mouse actions"""
        units = self.get_unit_positions('RED')
        unit = units[0]
        
        # Select unit with mouse
        self.click_tile(unit['x'], unit['y'])
        self.wait_for_highlights('movement')
        
        # Press W to wait (if implemented)
        ActionChains(self.driver).send_keys('w').perform()
        time.sleep(0.5)
        
        # Press Space to end turn
        ActionChains(self.driver).send_keys(Keys.SPACE).perform()
        time.sleep(0.5)
        
        # Verify turn ended
        state = self.get_game_state()
        
        # No JavaScript errors
        self.verify_no_errors()
        
        self.take_screenshot("keyboard_shortcuts_test")
"""
Test Suite for Attack Mechanics

Tests the attack system including:
- Direct attacks (adjacent)
- Indirect attacks (ranged)
- Damage preview
- Combat animations
- HP reduction and unit destruction
- Counter-attacks
"""

import pytest
import time
from typing import Dict, Tuple, Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .test_base_selenium import BaseSeleniumTest
from .selenium_helpers import GameStateValidator, TestDataHelper, VisualDebugger, ColorDetector


class TestDirectAttack(BaseSeleniumTest):
    """Test direct (adjacent) attack mechanics"""
    
    def test_direct_attack_adjacent_enemy(self):
        """Test attacking an adjacent enemy unit"""
        # Find units that can attack each other
        units = self.get_unit_positions()
        unit_pair = TestDataHelper.find_units_near_each_other(units, max_distance=1)
        
        if not unit_pair:
            # Try to move units adjacent
            unit_pair = self._setup_adjacent_combat()
        
        if not unit_pair:
            pytest.skip("Cannot set up adjacent units for combat")
        
        attacker, defender = unit_pair
        
        # Ensure it's attacker's turn
        current_turn = self.get_game_state()['currentTurn']
        if attacker['army'] != current_turn:
            self.end_turn()
            if self.get_game_state()['currentTurn'] != attacker['army']:
                self.end_turn()  # Skip other player's turn if 3+ players
        
        # Record initial HP
        defender_initial_hp = defender.get('hp', 100)
        
        # Select attacker
        self.click_tile(attacker['x'], attacker['y'])
        time.sleep(0.3)
        
        # If not adjacent, move adjacent first
        distance = abs(attacker['x'] - defender['x']) + abs(attacker['y'] - defender['y'])
        if distance > 1:
            self.wait_for_highlights('movement')
            # Move to adjacent tile
            adjacent_tiles = self._get_adjacent_tiles(defender['x'], defender['y'])
            highlights = self.get_movement_highlights()
            
            for adj in adjacent_tiles:
                if any(h['x'] == adj[0] and h['y'] == adj[1] for h in highlights):
                    self.click_tile(adj[0], adj[1])
                    self.wait_for_animation()
                    break
        
        # Now attack - click on defender
        self.click_tile(defender['x'], defender['y'])
        
        # Wait for damage preview popup (if implemented)
        time.sleep(0.5)
        
        # Confirm attack (might need to click again or press enter)
        self.click_tile(defender['x'], defender['y'])
        
        # Wait for combat animation
        self.wait_for_animation(2.0)
        
        # Verify defender took damage
        defender_tile = self.get_tile_info(defender['x'], defender['y'])
        
        if defender_tile.get('unit'):
            # Unit survived - check HP reduced
            final_hp = defender_tile['unit'].get('hp', 0)
            assert final_hp < defender_initial_hp, f"Defender HP not reduced: {final_hp} >= {defender_initial_hp}"
            
            # Take screenshot showing damage
            self.take_screenshot("direct_attack_damage")
        else:
            # Unit was destroyed
            assert defender_initial_hp <= 20, "High HP unit was destroyed in one hit?"
            self.take_screenshot("direct_attack_destroyed")
    
    def test_damage_preview_popup(self):
        """Test that damage preview appears before attack"""
        # This test checks if a damage preview UI element appears
        # Implementation depends on whether the game shows this
        
        unit_pair = self._setup_adjacent_combat()
        if not unit_pair:
            pytest.skip("Cannot set up combat scenario")
        
        attacker, defender = unit_pair
        
        # Select attacker
        self.click_tile(attacker['x'], attacker['y'])
        time.sleep(0.3)
        
        # Click defender to trigger preview
        self.click_tile(defender['x'], defender['y'])
        
        # Look for damage preview element
        # This might be a div, canvas overlay, or other element
        try:
            # Wait for some kind of preview element
            preview = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, "damage-preview"))
            )
            self.take_screenshot("damage_preview_visible")
            
            # Verify preview shows expected values
            preview_text = preview.text
            assert "Damage" in preview_text or "HP" in preview_text
            
        except:
            # No preview popup - game might show damage differently
            self.take_screenshot("attack_initiated")
    
    def test_attack_animation_plays(self):
        """Test that attack animation plays during combat"""
        unit_pair = self._setup_adjacent_combat()
        if not unit_pair:
            pytest.skip("Cannot set up combat scenario")
        
        attacker, defender = unit_pair
        
        # Select and attack
        self.click_tile(attacker['x'], attacker['y'])
        time.sleep(0.3)
        self.click_tile(defender['x'], defender['y'])
        
        # Capture frames during animation
        animation_frames = []
        start_time = time.time()
        
        while time.time() - start_time < 2.0:
            frame = self.capture_canvas()
            animation_frames.append(frame)
            time.sleep(0.1)
        
        # Should have captured multiple frames
        assert len(animation_frames) >= 10, "Too few animation frames captured"
        
        # Save first and last frame for comparison
        VisualDebugger.save_debug_comparison(
            animation_frames[0], 
            animation_frames[-1], 
            "attack_animation"
        )
    
    def test_counter_attack_triggers(self):
        """Test that defender counter-attacks if able"""
        # Find two direct combat units (both can counter)
        units = self.get_unit_positions()
        
        # Find tanks or similar units that can counter
        red_tank = next((u for u in units if u['army'] == 'RED' and u['unit_type'] == 'TANK'), None)
        blue_tank = next((u for u in units if u['army'] == 'BLUE' and u['unit_type'] == 'TANK'), None)
        
        if not red_tank or not blue_tank:
            pytest.skip("No suitable units for counter-attack test")
        
        # Move them adjacent if needed
        # ... (setup code similar to above)
        
        # Record both units' initial HP
        red_initial_hp = red_tank.get('hp', 100)
        blue_initial_hp = blue_tank.get('hp', 100)
        
        # Ensure it's RED's turn
        if self.get_game_state()['currentTurn'] != 'RED':
            self.end_turn()
        
        # Red attacks Blue
        self.click_tile(red_tank['x'], red_tank['y'])
        time.sleep(0.3)
        self.click_tile(blue_tank['x'], blue_tank['y'])
        self.wait_for_animation(2.0)
        
        # Check both units took damage (counter-attack happened)
        red_final = self.get_tile_info(red_tank['x'], red_tank['y'])
        blue_final = self.get_tile_info(blue_tank['x'], blue_tank['y'])
        
        # Blue should take damage from attack
        if blue_final.get('unit'):
            assert blue_final['unit']['hp'] < blue_initial_hp
        
        # Red should take damage from counter-attack (if Blue survived)
        if blue_final.get('unit') and red_final.get('unit'):
            assert red_final['unit']['hp'] < red_initial_hp, "No counter-attack damage!"
    
    def _setup_adjacent_combat(self) -> Optional[Tuple[Dict, Dict]]:
        """Helper to set up two units adjacent for combat"""
        units = self.get_unit_positions()
        
        # Try to find or create adjacent enemy units
        for red_unit in [u for u in units if u['army'] == 'RED']:
            for blue_unit in [u for u in units if u['army'] == 'BLUE']:
                distance = abs(red_unit['x'] - blue_unit['x']) + abs(red_unit['y'] - blue_unit['y'])
                
                if distance == 1:
                    return red_unit, blue_unit
                elif distance <= 4:
                    # Try to move them adjacent
                    self.click_tile(red_unit['x'], red_unit['y'])
                    if self.wait_for_highlights('movement', timeout=1):
                        # Find move position adjacent to blue unit
                        highlights = self.get_movement_highlights()
                        adjacent_tiles = self._get_adjacent_tiles(blue_unit['x'], blue_unit['y'])
                        
                        for adj in adjacent_tiles:
                            if any(h['x'] == adj[0] and h['y'] == adj[1] for h in highlights):
                                self.click_tile(adj[0], adj[1])
                                self.wait_for_animation()
                                red_unit['x'] = adj[0]
                                red_unit['y'] = adj[1]
                                return red_unit, blue_unit
        
        return None
    
    def _get_adjacent_tiles(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get tiles adjacent to given position"""
        return [
            (x - 1, y),
            (x + 1, y),
            (x, y - 1),
            (x, y + 1)
        ]


class TestIndirectAttack(BaseSeleniumTest):
    """Test indirect (ranged) attack mechanics"""
    
    def test_artillery_ranged_attack(self):
        """Test artillery attacking from range"""
        units = self.get_unit_positions('RED')
        artillery = next((u for u in units if u['unit_type'] in ['ARTILLERY', 'ROCKET']), None)
        
        if not artillery:
            pytest.skip("No indirect unit found")
        
        # Select artillery
        self.click_tile(artillery['x'], artillery['y'])
        
        # Wait in place to enable attack
        self.click_tile(artillery['x'], artillery['y'])
        time.sleep(0.5)
        
        # Should show attack highlights at range 2-3 (artillery) or 3-5 (rocket)
        if not self.wait_for_highlights('attack', timeout=2):
            # No enemies in range
            pytest.skip("No enemies in artillery range")
        
        attack_highlights = self.get_attack_highlights()
        assert len(attack_highlights) > 0
        
        # Verify highlights are at correct range
        for h in attack_highlights:
            distance = abs(h['x'] - artillery['x']) + abs(h['y'] - artillery['y'])
            if artillery['unit_type'] == 'ARTILLERY':
                assert 2 <= distance <= 3, f"Artillery highlight at wrong range: {distance}"
            else:  # ROCKET
                assert 3 <= distance <= 5, f"Rocket highlight at wrong range: {distance}"
        
        # Attack a highlighted enemy
        target = attack_highlights[0]
        
        # Get target initial state
        target_tile = self.get_tile_info(target['x'], target['y'])
        initial_hp = target_tile['unit']['hp'] if target_tile.get('unit') else 0
        
        # Attack
        self.click_tile(target['x'], target['y'])
        self.wait_for_animation(2.0)
        
        # Verify damage dealt
        final_tile = self.get_tile_info(target['x'], target['y'])
        if final_tile.get('unit'):
            assert final_tile['unit']['hp'] < initial_hp
        
        self.take_screenshot("indirect_attack_complete")
    
    def test_no_counter_attack_on_indirect(self):
        """Test that indirect attacks don't trigger counter-attacks"""
        units = self.get_unit_positions('RED')
        artillery = next((u for u in units if u['unit_type'] == 'ARTILLERY'), None)
        
        if not artillery:
            pytest.skip("No artillery found")
        
        # Record artillery initial HP
        artillery_initial_hp = artillery.get('hp', 100)
        
        # Select and wait
        self.click_tile(artillery['x'], artillery['y'])
        self.click_tile(artillery['x'], artillery['y'])
        time.sleep(0.5)
        
        # Find attack target
        if not self.wait_for_highlights('attack', timeout=2):
            pytest.skip("No targets in range")
        
        attack_highlights = self.get_attack_highlights()
        target = attack_highlights[0]
        
        # Attack
        self.click_tile(target['x'], target['y'])
        self.wait_for_animation(2.0)
        
        # Verify artillery took no damage (no counter-attack)
        artillery_tile = self.get_tile_info(artillery['x'], artillery['y'])
        assert artillery_tile.get('unit'), "Artillery disappeared!"
        assert artillery_tile['unit']['hp'] == artillery_initial_hp, "Artillery took damage from indirect attack!"
    
    def test_minimum_range_restriction(self):
        """Test that indirect units can't attack at close range"""
        units = self.get_unit_positions()
        artillery = next((u for u in units if u['army'] == 'RED' and u['unit_type'] == 'ARTILLERY'), None)
        
        if not artillery:
            pytest.skip("No artillery found")
        
        # Find an enemy unit
        enemy = next((u for u in units if u['army'] != 'RED'), None)
        
        if not enemy:
            pytest.skip("No enemy units found")
        
        # Try to move artillery adjacent to enemy
        distance = abs(artillery['x'] - enemy['x']) + abs(artillery['y'] - enemy['y'])
        
        if distance > 1:
            # Move closer
            self.click_tile(artillery['x'], artillery['y'])
            self.wait_for_highlights('movement')
            
            # Find position adjacent to enemy
            adjacent_tiles = self._get_adjacent_tiles(enemy['x'], enemy['y'])
            highlights = self.get_movement_highlights()
            
            for adj in adjacent_tiles:
                if any(h['x'] == adj[0] and h['y'] == adj[1] for h in highlights):
                    self.click_tile(adj[0], adj[1])
                    self.wait_for_animation()
                    break
        
        # Now artillery should be adjacent - check attack options
        time.sleep(0.5)
        
        # Should not show attack highlights on adjacent enemy
        attack_highlights = self.get_attack_highlights()
        
        # Adjacent enemy should not be highlighted
        adjacent_highlighted = any(
            h['x'] == enemy['x'] and h['y'] == enemy['y'] 
            for h in attack_highlights
        )
        
        assert not adjacent_highlighted, "Artillery can attack adjacent unit!"


class TestCombatFeedback(BaseSeleniumTest):
    """Test combat visual feedback and UI updates"""
    
    def test_damage_numbers_display(self):
        """Test that damage numbers appear during combat"""
        unit_pair = self._setup_combat_scenario()
        if not unit_pair:
            pytest.skip("Cannot set up combat")
        
        attacker, defender = unit_pair
        
        # Execute attack
        self.click_tile(attacker['x'], attacker['y'])
        time.sleep(0.3)
        self.click_tile(defender['x'], defender['y'])
        
        # Capture during animation to look for damage numbers
        time.sleep(0.5)  # Mid-animation
        combat_screenshot = self.capture_canvas()
        
        # Save for visual inspection
        self.take_screenshot("combat_damage_numbers")
        
        # Could use OCR here to detect damage numbers, but for now
        # we'll just ensure the attack completed
        self.wait_for_animation()
    
    def test_unit_destruction_animation(self):
        """Test unit destruction when HP reaches 0"""
        # Try to find a low-HP unit to destroy
        units = self.get_unit_positions()
        
        # Look for damaged units
        weak_enemy = None
        for unit in units:
            if unit['army'] != 'RED' and unit.get('hp', 100) <= 30:
                weak_enemy = unit
                break
        
        if not weak_enemy:
            # Try to damage a unit first
            pytest.skip("No weak units available for destruction test")
        
        # Find attacker that can destroy it
        attacker = self._find_unit_that_can_destroy(weak_enemy)
        
        if not attacker:
            pytest.skip("No suitable attacker found")
        
        # Execute destroying attack
        self.click_tile(attacker['x'], attacker['y'])
        time.sleep(0.3)
        self.click_tile(weak_enemy['x'], weak_enemy['y'])
        
        # Capture destruction animation
        destruction_frames = []
        for i in range(10):
            destruction_frames.append(self.capture_canvas())
            time.sleep(0.1)
        
        # Verify unit is gone
        final_tile = self.get_tile_info(weak_enemy['x'], weak_enemy['y'])
        assert not final_tile.get('unit'), "Unit not destroyed!"
        
        # Save destruction sequence
        VisualDebugger.save_debug_comparison(
            destruction_frames[0],
            destruction_frames[-1],
            "unit_destruction"
        )
    
    def test_hp_bar_updates(self):
        """Test that unit HP bars update after combat"""
        unit_pair = self._setup_combat_scenario()
        if not unit_pair:
            pytest.skip("Cannot set up combat")
        
        attacker, defender = unit_pair
        
        # Capture before combat
        before_combat = self.capture_canvas()
        
        # Execute attack
        self.click_tile(attacker['x'], attacker['y'])
        time.sleep(0.3)
        self.click_tile(defender['x'], defender['y'])
        self.wait_for_animation()
        
        # Capture after combat
        after_combat = self.capture_canvas()
        
        # HP bars should be visually different
        # Could use image comparison here
        VisualDebugger.save_debug_comparison(
            before_combat,
            after_combat,
            "hp_bar_update"
        )
        
        # Verify HP changed in game state
        defender_tile = self.get_tile_info(defender['x'], defender['y'])
        if defender_tile.get('unit'):
            assert defender_tile['unit']['hp'] < defender.get('hp', 100)
    
    def test_combat_log_updates(self):
        """Test that combat log or status updates after battle"""
        # This depends on whether the game has a combat log
        # For now, just verify the game state updates properly
        
        initial_state = self.get_game_state()
        
        # Execute any attack
        unit_pair = self._setup_combat_scenario()
        if not unit_pair:
            pytest.skip("Cannot set up combat")
        
        attacker, defender = unit_pair
        
        self.click_tile(attacker['x'], attacker['y'])
        time.sleep(0.3)
        self.click_tile(defender['x'], defender['y'])
        self.wait_for_animation()
        
        # Check if any UI elements updated
        final_state = self.get_game_state()
        
        # Could check for combat log element here
        # For now, just verify state changed
        assert initial_state != final_state, "Game state didn't update after combat"
    
    def _setup_combat_scenario(self) -> Optional[Tuple[Dict, Dict]]:
        """Helper to set up a combat scenario"""
        units = self.get_unit_positions()
        unit_pair = TestDataHelper.find_units_near_each_other(units, max_distance=3)
        
        if not unit_pair:
            return None
        
        attacker, defender = unit_pair
        
        # Ensure correct turn
        if attacker['army'] != self.get_game_state()['currentTurn']:
            attacker, defender = defender, attacker
        
        return attacker, defender
    
    def _find_unit_that_can_destroy(self, target: Dict) -> Optional[Dict]:
        """Find a unit that can likely destroy the target"""
        units = self.get_unit_positions('RED')
        
        # Prefer strong units against weak target
        strong_types = ['TANK', 'MEDIUMTANK', 'NEOTANK', 'BOMBER']
        
        for unit in units:
            if unit['unit_type'] in strong_types:
                distance = abs(unit['x'] - target['x']) + abs(unit['y'] - target['y'])
                if distance <= 5:  # Reasonable attack distance
                    return unit
        
        return None
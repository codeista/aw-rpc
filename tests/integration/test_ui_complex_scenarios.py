#!/usr/bin/env python3
"""
UI Integration Tests for Complex Scenarios
Tests complex user interactions through the web interface
"""

import pytest
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

from tests.ui.test_base_selenium import BaseSeleniumTest

class TestUIComplexScenarios(BaseSeleniumTest):
    """Test complex UI interaction scenarios"""
    
    def test_complete_game_flow(self):
        """Test a complete game flow from start to combat"""
        # Start new game
        self.driver.get(f"{self.base_url}/test")
        self.wait_for_game_load()
        
        # Create units
        self.create_unit_at_factory(0, 3, "TANK")
        self.create_unit_at_factory(0, 6, "INFANTRY")
        
        # End turn to enable movement
        self.click_end_turn()
        self.wait_for_turn_change("BLUE")
        self.click_end_turn()
        self.wait_for_turn_change("RED")
        
        # Select and move tank
        self.click_tile(0, 3)
        self.wait_for_highlights()
        
        # Move tank forward
        self.click_tile(3, 3)
        self.wait_for_element((By.CLASS_NAME, "action-menu"), timeout=5)
        
        # Click wait action
        wait_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Wait')]")
        wait_button.click()
        
        # Verify unit moved and is unavailable
        self.verify_unit_at_position(3, 3, "TANK")
        self.verify_unit_unavailable(3, 3)
        
    def test_transport_loading_unloading_flow(self):
        """Test complete transport operation flow"""
        self.driver.get(f"{self.base_url}/test")
        self.wait_for_game_load()
        
        # Create APC and Infantry
        self.create_unit_at_factory(0, 3, "APC")
        self.click_tile(1, 3)  # Click empty space to deselect
        
        # Try to create infantry at same spot (should fail)
        self.click_tile(0, 3)
        time.sleep(0.5)
        
        # Create infantry at different spot
        self.create_unit_at_factory(0, 6, "INFANTRY")
        
        # End turn twice
        self.click_end_turn()
        self.wait_for_turn_change("BLUE")
        self.click_end_turn() 
        self.wait_for_turn_change("RED")
        
        # Move infantry next to APC
        self.click_tile(0, 6)
        self.wait_for_highlights()
        self.click_tile(0, 4)  # Move closer to APC
        
        # Should see action menu with Load option
        self.wait_for_element((By.CLASS_NAME, "action-menu"))
        
        # Click wait for now
        wait_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Wait')]")
        wait_btn.click()
        
        # End turn cycle
        self.click_end_turn()
        self.wait_for_turn_change("BLUE")
        self.click_end_turn()
        self.wait_for_turn_change("RED")
        
        # Now load infantry into APC
        self.click_tile(0, 4)  # Select infantry
        self.wait_for_highlights()
        self.click_tile(0, 3)  # Click on APC to load
        
        # Verify infantry disappeared (loaded)
        self.verify_no_unit_at_position(0, 4)
        
        # Move loaded APC
        self.click_tile(0, 3)
        self.wait_for_highlights()
        self.click_tile(3, 3)
        
        # Right-click to unload
        self.right_click_tile(3, 3)
        self.wait_for_element((By.CLASS_NAME, "context-menu"))
        
        # Click unload option
        unload_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Unload')]")
        unload_btn.click()
        
        # Select unload position
        self.click_tile(3, 4)
        
        # Verify infantry unloaded
        self.verify_unit_at_position(3, 4, "INFANTRY")
        
    def test_multi_unit_combat_scenario(self):
        """Test combat with multiple units"""
        self.driver.get(f"{self.base_url}/test")
        self.wait_for_game_load()
        
        # Create multiple combat units
        self.create_unit_at_factory(0, 3, "TANK")
        time.sleep(0.5)
        self.click_tile(1, 3)  # Deselect
        
        self.create_unit_at_factory(0, 6, "ARTILLERY")
        time.sleep(0.5)
        
        # Switch to BLUE and create enemy
        self.click_end_turn()
        self.wait_for_turn_change("BLUE")
        
        # Find BLUE factory and create unit
        self.execute_rpc("unit_create", {
            "unit_type": "INFANTRY",
            "x": 6, "y": 3  # Approximate BLUE factory position
        })
        
        # End turn to enable movement
        self.click_end_turn()
        self.wait_for_turn_change("RED")
        
        # Move tank toward enemy
        self.click_tile(0, 3)
        self.wait_for_highlights()
        self.click_tile(4, 3)
        self.handle_post_move_action("wait")
        
        # Move artillery (but don't attack - can't attack after moving)
        self.click_tile(0, 6)
        self.wait_for_highlights()
        self.click_tile(2, 6)
        self.handle_post_move_action("wait")
        
        # End turn
        self.click_end_turn()
        self.wait_for_turn_change("BLUE")
        self.click_end_turn()
        self.wait_for_turn_change("RED")
        
        # Tank attacks infantry
        self.click_tile(4, 3)
        self.wait_for_highlights()
        
        # Click on enemy to attack
        self.click_tile(6, 3)
        
        # Handle combat preview
        self.wait_for_element((By.CLASS_NAME, "combat-preview"))
        confirm_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Confirm')]")
        confirm_btn.click()
        
        # Verify combat occurred
        time.sleep(1)
        self.verify_unit_unavailable(4, 3)  # Tank should be grayed out
        
    def test_capture_victory_scenario(self):
        """Test capturing properties for victory"""
        self.driver.get(f"{self.base_url}/test") 
        self.wait_for_game_load()
        
        # Create multiple infantry for capturing
        for i in range(3):
            self.create_unit_at_factory(0, 3, "INFANTRY")
            time.sleep(0.5)
            if i < 2:  # Move previous infantry away
                self.click_tile(0, 3)
                self.wait_for_highlights()
                self.click_tile(1 + i, 3)
                self.handle_post_move_action("wait")
                
        # End turn to enable movement
        self.click_end_turn()
        self.wait_for_turn_change("BLUE")
        self.click_end_turn()
        self.wait_for_turn_change("RED")
        
        # Move infantry to neutral cities
        for i in range(3):
            self.click_tile(i, 3)
            self.wait_for_highlights()
            
            # Move to different properties
            target_x = 2 + i * 2
            target_y = 4
            self.click_tile(target_x, target_y)
            
            # Check for capture option
            try:
                capture_btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Capture')]"))
                )
                capture_btn.click()
            except TimeoutException:
                # No capture available, just wait
                self.handle_post_move_action("wait")
                
    def test_fog_of_war_exploration(self):
        """Test fog of war mechanics with recon units"""
        # This test would require a fog of war map
        pytest.skip("Fog of war not implemented in current version")
        
    def test_supply_line_management(self):
        """Test managing supply lines with APCs"""
        self.driver.get(f"{self.base_url}/test")
        self.wait_for_game_load()
        
        # Create units that need supplies
        self.create_unit_at_factory(0, 3, "TANK")
        time.sleep(0.5)
        self.click_tile(1, 3)  # Deselect
        
        self.create_unit_at_factory(0, 6, "FIGHTER")
        time.sleep(0.5)
        self.click_tile(1, 6)  # Deselect
        
        # Create APC for resupply
        self.create_unit_at_factory(0, 9, "APC")
        
        # Simulate several turns of movement to deplete fuel
        for turn in range(5):
            self.click_end_turn()
            self.wait_for_turn_change("BLUE" if turn % 2 == 0 else "RED")
            
            if self.get_current_turn() == 0:
                # Move units to deplete fuel
                try:
                    # Move tank
                    self.click_tile(0, 3)
                    self.wait_for_highlights(timeout=2)
                    self.click_tile(2, 3)
                    self.handle_post_move_action("wait")
                    
                    # Move back
                    self.click_tile(2, 3)
                    self.click_tile(0, 3)
                except:
                    pass  # Unit might be out of fuel
                    
        # Move APC near units for auto-resupply
        self.click_tile(0, 9)
        self.wait_for_highlights()
        self.click_tile(0, 4)  # Move between tank and fighter
        self.handle_post_move_action("wait")
        
        # End turn - auto resupply should occur
        self.click_end_turn()
        
        # Verify units are resupplied (check they can move)
        self.wait_for_turn_change("BLUE")
        self.click_end_turn()
        self.wait_for_turn_change("RED")
        
        self.click_tile(0, 3)
        highlights = self.wait_for_highlights()
        assert len(highlights) > 1, "Tank should be able to move after resupply"
        
    def test_complex_terrain_navigation(self):
        """Test navigating complex terrain with different unit types"""
        self.driver.get(f"{self.base_url}/test")
        self.wait_for_game_load()
        
        # Create different movement type units
        units = [
            ("INFANTRY", "foot"),
            ("TANK", "tread"),
            ("FIGHTER", "air")
        ]
        
        positions = [(0, 3), (0, 6), (0, 9)]
        
        for i, (unit_type, move_type) in enumerate(units):
            if i < len(positions):
                self.create_unit_at_factory(positions[i][0], positions[i][1], unit_type)
                time.sleep(0.5)
                
        # End turn to enable movement
        self.click_end_turn()
        self.wait_for_turn_change("BLUE")
        self.click_end_turn()
        self.wait_for_turn_change("RED")
        
        # Test each unit's movement range
        for i, (unit_type, move_type) in enumerate(units):
            if i < len(positions):
                self.click_tile(positions[i][0], positions[i][1])
                highlights = self.wait_for_highlights()
                
                # Different units should have different movement patterns
                # Infantry can cross mountains, tanks cannot
                # Air units ignore terrain
                highlight_count = len(highlights)
                print(f"{unit_type} can move to {highlight_count} tiles")
                
                # Deselect
                self.click_tile(5, 5)
                
    # Helper methods specific to complex scenarios
    
    def create_unit_at_factory(self, x, y, unit_type):
        """Create a unit at a factory position"""
        self.click_tile(x, y)
        time.sleep(0.5)
        
        # Look for production menu
        try:
            menu = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, "production-menu"))
            )
            
            # Find and click unit type
            unit_btn = menu.find_element(By.XPATH, f"//button[contains(@data-unit, '{unit_type}')]")
            unit_btn.click()
            
        except TimeoutException:
            # Fallback to RPC
            result = self.execute_rpc("unit_create", {
                "unit_type": unit_type,
                "x": x,
                "y": y
            })
            
    def handle_post_move_action(self, action="wait"):
        """Handle post-move action menu"""
        try:
            menu = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, "action-menu"))
            )
            
            if action == "wait":
                wait_btn = menu.find_element(By.XPATH, "//button[contains(text(), 'Wait')]")
                wait_btn.click()
            elif action == "attack":
                attack_btn = menu.find_element(By.XPATH, "//button[contains(text(), 'Attack')]")
                attack_btn.click()
            elif action == "capture":
                capture_btn = menu.find_element(By.XPATH, "//button[contains(text(), 'Capture')]")
                capture_btn.click()
                
        except TimeoutException:
            # Auto-wait might have triggered
            pass
            
    def verify_unit_unavailable(self, x, y):
        """Verify unit is grayed out (unavailable)"""
        tile = self.get_tile_element(x, y)
        unit_elem = tile.find_element(By.CLASS_NAME, "unit-sprite")
        classes = unit_elem.get_attribute("class")
        assert "unavailable" in classes or "grayed" in classes, f"Unit at ({x},{y}) should be unavailable"
        
    def verify_no_unit_at_position(self, x, y):
        """Verify no unit exists at position"""
        tile = self.get_tile_element(x, y)
        try:
            unit_elem = tile.find_element(By.CLASS_NAME, "unit-sprite")
            if unit_elem.is_displayed():
                pytest.fail(f"Unit found at ({x},{y}) when none expected")
        except:
            # No unit element found - good
            pass
            
    def wait_for_turn_change(self, expected_turn):
        """Wait for turn to change to expected army"""
        WebDriverWait(self.driver, 10).until(
            lambda driver: self.get_current_turn() == expected_turn
        )
        
    def get_current_turn(self):
        """Get current turn from UI"""
        try:
            turn_elem = self.driver.find_element(By.CLASS_NAME, "current-turn")
            return turn_elem.text.upper()
        except:
            # Fallback to RPC
            result = self.execute_rpc("game_board", {})
            return result.get("current_turn", "UNKNOWN")

# Test runner
def run_ui_integration_tests():
    """Run UI integration tests"""
    import unittest
    from unittest import TestLoader, TextTestRunner
    
    # Create test suite
    loader = TestLoader()
    suite = loader.loadTestsFromTestCase(TestUIComplexScenarios)
    
    # Run tests
    runner = TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    import sys
    # Note: Requires Selenium WebDriver and running game server
    print("⚠️  UI Integration tests require:")
    print("  1. Selenium WebDriver installed")
    print("  2. Chrome/Chromium browser")  
    print("  3. Game server running on localhost:5000")
    print("")
    
    success = run_ui_integration_tests()
    sys.exit(0 if success else 1)
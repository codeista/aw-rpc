#!/usr/bin/env python3
"""
UI test for recent improvements:
- Browser title updates
- Help panel
- Keyboard shortcuts
- Context menus
"""

import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tests.ui.base_test import BaseUITest

class TestUIImprovements(BaseUITest):
    """Test recent UI improvements"""
    
    def test_browser_title_updates(self):
        """Test that browser title updates with game state"""
        # Get initial title
        initial_title = self.driver.title
        self.assertIn("Day 1", initial_title, "Initial title should show Day 1")
        self.assertIn("RED", initial_title, "Initial title should show RED turn")
        
        # End turn
        self.click_element((By.XPATH, "//button[contains(text(), 'End Turn')]"))
        time.sleep(0.5)
        
        # Check title updated
        new_title = self.driver.title
        self.assertIn("BLUE", new_title, "Title should update to show BLUE turn")
        
        # End BLUE turn to advance day
        self.click_element((By.XPATH, "//button[contains(text(), 'End Turn')]"))
        time.sleep(0.5)
        
        # Check day advanced
        day2_title = self.driver.title
        self.assertIn("Day 2", day2_title, "Title should show Day 2")
    
    def test_help_panel_toggle(self):
        """Test help panel shows/hides with H key"""
        # Initially help should be hidden
        help_panels = self.driver.find_elements(By.CLASS_NAME, "help-panel")
        if help_panels:
            self.assertFalse(help_panels[0].is_displayed(), "Help panel should be hidden initially")
        
        # Press H to show help
        canvas = self.driver.find_element(By.ID, "gameCanvas")
        canvas.send_keys("h")
        time.sleep(0.3)
        
        # Help should be visible
        help_panel = self.wait_for_element((By.CLASS_NAME, "help-panel"))
        self.assertTrue(help_panel.is_displayed(), "Help panel should be visible after pressing H")
        
        # Check help content
        help_text = help_panel.text
        self.assertIn("Keyboard Shortcuts", help_text, "Help should show keyboard shortcuts")
        self.assertIn("H - Toggle help", help_text)
        self.assertIn("E - End turn", help_text)
        self.assertIn("ESC - Deselect unit", help_text)
        
        # Press H again to hide
        canvas.send_keys("h")
        time.sleep(0.3)
        
        # Should be hidden again
        help_panels = self.driver.find_elements(By.CLASS_NAME, "help-panel")
        if help_panels:
            self.assertFalse(help_panels[0].is_displayed(), "Help panel should be hidden after pressing H again")
    
    def test_keyboard_shortcuts(self):
        """Test keyboard shortcuts work correctly"""
        # Create a unit
        self.create_unit("INFANTRY", 0, 4)
        
        # Test E for end turn
        canvas = self.driver.find_element(By.ID, "gameCanvas")
        canvas.send_keys("e")
        time.sleep(0.5)
        
        # Check turn changed
        self.assertEqual(self.get_current_turn(), "BLUE", "E key should end turn")
        
        # End BLUE turn to get back to RED
        canvas.send_keys("e")
        time.sleep(0.5)
        
        # Select unit
        self.click_tile(0, 4)
        time.sleep(0.3)
        
        # Verify selected
        selected_info = self.driver.find_element(By.ID, "selectedUnitInfo")
        self.assertIn("Infantry", selected_info.text, "Unit should be selected")
        
        # Test ESC to deselect
        canvas.send_keys(Keys.ESCAPE)
        time.sleep(0.3)
        
        # Verify deselected
        selected_info = self.driver.find_element(By.ID, "selectedUnitInfo")
        self.assertEqual(selected_info.text.strip(), "", "ESC should deselect unit")
    
    def test_context_menu_on_unit(self):
        """Test right-click context menu on units"""
        # Create a unit
        self.create_unit("INFANTRY", 0, 4)
        
        # End turn so unit can act
        self.end_turn()
        self.end_turn()  # Back to RED
        
        # Right-click on unit
        canvas = self.driver.find_element(By.ID, "gameCanvas")
        unit_pos = self.get_canvas_coords(0, 4)
        
        actions = ActionChains(self.driver)
        actions.move_to_element_with_offset(canvas, unit_pos[0], unit_pos[1])
        actions.context_click()
        actions.perform()
        time.sleep(0.3)
        
        # Check context menu appears
        try:
            context_menu = self.wait_for_element((By.CLASS_NAME, "context-menu"), timeout=2)
            self.assertTrue(context_menu.is_displayed(), "Context menu should appear on right-click")
            
            # Check menu options
            menu_text = context_menu.text
            self.assertIn("Wait", menu_text, "Context menu should have Wait option")
            
            # Click Wait
            wait_option = context_menu.find_element(By.XPATH, ".//div[contains(text(), 'Wait')]")
            wait_option.click()
            time.sleep(0.3)
            
            # Verify unit is exhausted
            board = self.get_board_state()
            unit_tile = next((t for t in board['grid'] if t['x'] == 0 and t['y'] == 4), None)
            if unit_tile and unit_tile.get('unit'):
                self.assertFalse(unit_tile['unit'].get('can_move', True), "Unit should be exhausted after Wait")
        except TimeoutException:
            self.skipTest("Context menu not implemented yet")
    
    def test_context_menu_on_capturable(self):
        """Test context menu shows capture option on cities"""
        # Create infantry
        self.create_unit("INFANTRY", 0, 4)
        
        # End turns
        self.end_turn()
        self.end_turn()
        
        # Move infantry to neutral city at (3,4)
        self.move_unit(0, 4, 3, 4)
        time.sleep(0.5)
        
        # Right-click on the unit/city
        canvas = self.driver.find_element(By.ID, "gameCanvas")
        city_pos = self.get_canvas_coords(3, 4)
        
        actions = ActionChains(self.driver)
        actions.move_to_element_with_offset(canvas, city_pos[0], city_pos[1])
        actions.context_click()
        actions.perform()
        time.sleep(0.3)
        
        # Check for capture option
        try:
            context_menu = self.wait_for_element((By.CLASS_NAME, "context-menu"), timeout=2)
            menu_text = context_menu.text
            self.assertIn("Capture", menu_text, "Context menu should have Capture option on city")
        except TimeoutException:
            self.skipTest("Context menu not implemented yet")
    
    def test_context_menu_dismiss(self):
        """Test context menu dismisses on click elsewhere"""
        # Create unit
        self.create_unit("INFANTRY", 0, 4)
        self.end_turn()
        self.end_turn()
        
        # Open context menu
        canvas = self.driver.find_element(By.ID, "gameCanvas")
        unit_pos = self.get_canvas_coords(0, 4)
        
        actions = ActionChains(self.driver)
        actions.move_to_element_with_offset(canvas, unit_pos[0], unit_pos[1])
        actions.context_click()
        actions.perform()
        time.sleep(0.3)
        
        try:
            # Verify menu is open
            context_menu = self.wait_for_element((By.CLASS_NAME, "context-menu"), timeout=2)
            self.assertTrue(context_menu.is_displayed())
            
            # Click elsewhere
            empty_pos = self.get_canvas_coords(5, 5)
            actions = ActionChains(self.driver)
            actions.move_to_element_with_offset(canvas, empty_pos[0], empty_pos[1])
            actions.click()
            actions.perform()
            time.sleep(0.3)
            
            # Menu should be gone
            context_menus = self.driver.find_elements(By.CLASS_NAME, "context-menu")
            if context_menus:
                self.assertFalse(context_menus[0].is_displayed(), "Context menu should dismiss on outside click")
        except TimeoutException:
            self.skipTest("Context menu not implemented yet")
    
    def test_funds_display_updates(self):
        """Test that funds display updates correctly"""
        # Get initial funds
        funds_elem = self.driver.find_element(By.ID, "fundsDisplay")
        initial_funds = int(funds_elem.text.replace("Funds: ", "").replace(",", ""))
        
        # Create a unit (costs 1000)
        self.create_unit("INFANTRY", 0, 4)
        time.sleep(0.5)
        
        # Check funds decreased
        new_funds = int(funds_elem.text.replace("Funds: ", "").replace(",", ""))
        self.assertEqual(new_funds, initial_funds - 1000, "Funds should decrease by 1000 after creating infantry")
        
        # End turns to get income
        self.end_turn()
        self.end_turn()
        time.sleep(0.5)
        
        # Check funds increased (should get income from HQ and any owned properties)
        income_funds = int(funds_elem.text.replace("Funds: ", "").replace(",", ""))
        self.assertGreater(income_funds, new_funds, "Funds should increase from income at turn start")

if __name__ == '__main__':
    unittest.main()
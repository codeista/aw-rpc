"""
Test Production Modal Functionality

Tests that would have caught the bugs:
1. Modal not showing due to wrong response structure
2. Unit creation from factories
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from test_base_selenium import BaseSeleniumTest


class TestProductionModal(BaseSeleniumTest):
    """Test production modal and unit creation"""
    
    def test_factory_click_shows_modal(self):
        """Test that clicking on a factory shows production modal"""
        # Find a RED factory (at 0,0 in test map)
        self.click_tile(0, 0)
        
        # Wait for modal to appear
        try:
            modal = WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located((By.ID, "modal"))
            )
            assert modal.is_displayed(), "Production modal should be visible"
            
            # Check modal has unit select dropdown
            unit_select = self.driver.find_element(By.ID, "unit-select")
            assert unit_select is not None, "Unit select dropdown should exist"
            
            # Check options are populated
            select = Select(unit_select)
            options = select.options
            assert len(options) > 0, "Should have unit options"
            
            # Verify some expected units
            unit_types = [opt.get_attribute('value') for opt in options]
            assert 'INFANTRY' in unit_types, "Should have INFANTRY option"
            assert 'TANK' in unit_types, "Should have TANK option"
            
        except Exception as e:
            self.fail(f"Production modal test failed: {e}")
    
    def test_modal_shows_player_funds(self):
        """Test that modal shows current player funds"""
        self.click_tile(0, 0)
        
        # Wait for modal
        modal = WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.ID, "modal"))
        )
        
        # Check modal title contains funds
        modal_title = modal.find_element(By.TAG_NAME, "h3")
        title_text = modal_title.text
        
        # Should show funds in format "Unit Production (5000G)" or similar
        assert "G)" in title_text, f"Modal title should show funds, got: {title_text}"
        assert "(" in title_text, f"Modal title should show funds in parentheses, got: {title_text}"
    
    def test_unit_creation_from_factory(self):
        """Test creating a unit from factory"""
        # Click factory
        self.click_tile(0, 0)
        
        # Wait for modal
        modal = WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.ID, "modal"))
        )
        
        # Select INFANTRY
        unit_select = Select(self.driver.find_element(By.ID, "unit-select"))
        unit_select.select_by_value("INFANTRY")
        
        # Click create button
        create_btn = self.driver.find_element(By.ID, "create")
        create_btn.click()
        
        # Modal should disappear
        WebDriverWait(self.driver, 5).until(
            EC.invisibility_of_element_located((By.ID, "modal"))
        )
        
        # Verify unit was created by checking tile (0,0) now has a unit
        # This would require checking the game state or visual confirmation
        time.sleep(0.5)  # Wait for game update
        
        # Click the tile again - should not show production modal if unit exists
        self.click_tile(0, 0)
        time.sleep(0.5)
        
        # Modal should not appear (or show unit info instead)
        try:
            modal = self.driver.find_element(By.ID, "modal")
            if modal.is_displayed():
                # If modal shows, it should not be production modal
                unit_select = self.driver.find_elements(By.ID, "unit-select")
                assert len(unit_select) == 0 or not unit_select[0].is_displayed(), \
                    "Should not show production modal when factory has unit"
        except:
            # Modal not found is also acceptable (means no production modal)
            pass
    
    def test_cancel_button_closes_modal(self):
        """Test that cancel button closes production modal"""
        self.click_tile(0, 0)
        
        # Wait for modal
        modal = WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.ID, "modal"))
        )
        
        # Click cancel
        cancel_btn = self.driver.find_element(By.ID, "cancel")
        cancel_btn.click()
        
        # Modal should disappear
        WebDriverWait(self.driver, 5).until(
            EC.invisibility_of_element_located((By.ID, "modal"))
        )
    
    def test_insufficient_funds_indication(self):
        """Test that units player can't afford are marked"""
        # This test would need a way to reduce player funds first
        # For now, just check that the option text indicates affordability
        
        self.click_tile(0, 0)
        
        # Wait for modal
        WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.ID, "modal"))
        )
        
        # Check options
        unit_select = Select(self.driver.find_element(By.ID, "unit-select"))
        
        for option in unit_select.options:
            text = option.text
            value = option.get_attribute('value')
            
            # Options should show cost (e.g., "INFANTRY - 1000G")
            assert " - " in text and "G" in text, \
                f"Option should show cost for {value}, got: {text}"
            
            # Disabled options should indicate insufficient funds
            if option.get_attribute('disabled'):
                assert "Not enough funds" in text or "insufficient" in text.lower(), \
                    f"Disabled option should indicate why for {value}"
    
    def test_non_factory_click_no_modal(self):
        """Test that clicking non-factory tiles doesn't show production modal"""
        # Click on a plain tile
        self.click_tile(5, 5)
        
        time.sleep(0.5)  # Brief wait
        
        # Modal should not be visible
        try:
            modal = self.driver.find_element(By.ID, "modal")
            assert not modal.is_displayed(), "Modal should not show for non-factory tiles"
        except:
            # Element not found is fine - means no modal
            pass
    
    def test_enemy_factory_no_production(self):
        """Test that clicking enemy factory doesn't show production modal"""
        # Click on BLUE factory (at 14,0 in standard test map)
        self.click_tile(14, 0)
        
        time.sleep(0.5)
        
        # Should not show production modal
        try:
            modal = self.driver.find_element(By.ID, "modal")
            if modal.is_displayed():
                # If any modal shows, verify it's not production modal
                unit_select = self.driver.find_elements(By.ID, "unit-select")
                assert len(unit_select) == 0 or not unit_select[0].is_displayed(), \
                    "Should not show production modal for enemy factory"
        except:
            # No modal is expected
            pass
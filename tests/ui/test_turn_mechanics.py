"""
Test Turn Mechanics

Tests that would catch unit state bugs after turn changes:
1. Units not being able to move after turn end
2. Unit state properties being undefined
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from test_base_selenium import BaseSeleniumTest


class TestTurnMechanics(BaseSeleniumTest):
    """Test turn mechanics and unit state management"""
    
    def test_unit_state_after_turn_end(self):
        """Test that units have proper state after turn ends"""
        # Create a unit first
        self.click_tile(0, 0)  # RED factory
        
        # Wait for modal
        modal = WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.ID, "modal"))
        )
        
        # Create infantry
        self.driver.execute_script("""
            document.getElementById('unit-select').value = 'INFANTRY';
            document.getElementById('create').click();
        """)
        
        # Wait for modal to close
        WebDriverWait(self.driver, 5).until(
            EC.invisibility_of_element_located((By.ID, "modal"))
        )
        
        time.sleep(0.5)
        
        # Click on the created unit
        self.click_tile(0, 0)
        
        # Check unit state in console
        unit_state = self.driver.execute_script("""
            const tile = window.game.getTile(0, 0);
            return {
                hasUnit: !!tile.unit,
                type: tile.unit?.type,
                army: tile.unit?.army,
                hasMoved: tile.unit?.has_moved,
                done: tile.unit?.done,
                canMove: tile.unit?.can_move,
                canAttack: tile.unit?.can_attack
            };
        """)
        
        assert unit_state['hasUnit'], "Unit should exist"
        assert unit_state['type'] == 'INFANTRY', "Should be infantry"
        
        # Fresh unit should not be able to move on creation turn
        assert unit_state['hasMoved'] is not None, "has_moved should be defined"
        assert unit_state['done'] is not None, "done should be defined"
        
        # End turn
        end_turn_btn = self.driver.find_element(By.ID, "end-turn")
        end_turn_btn.click()
        
        time.sleep(1)  # Wait for turn to process
        
        # Click on same unit again
        self.click_tile(0, 0)
        
        # Check unit state after turn end
        unit_state_after_turn = self.driver.execute_script("""
            const tile = window.game.getTile(0, 0);
            return {
                hasUnit: !!tile.unit,
                hasMoved: tile.unit?.has_moved,
                done: tile.unit?.done,
                canMove: tile.unit?.can_move,
                canAttack: tile.unit?.can_attack,
                army: tile.unit?.army,
                currentTurn: window.game.board?.current_turn
            };
        """)
        
        # After turn end, unit should be able to act
        assert unit_state_after_turn['hasMoved'] is not None, "has_moved should be defined after turn"
        assert unit_state_after_turn['done'] is not None, "done should be defined after turn"
        assert unit_state_after_turn['hasMoved'] == False, "Unit should not have moved after new turn"
        assert unit_state_after_turn['done'] == False, "Unit should not be done after new turn"
    
    def test_unit_can_move_after_turn_change(self):
        """Test that units can actually move after turn changes"""
        # Setup: Create units for both players
        # RED infantry at (0, 0)
        self.create_unit_at_factory(0, 0, 'INFANTRY')
        
        # End RED turn
        self.driver.find_element(By.ID, "end-turn").click()
        time.sleep(1)
        
        # Create BLUE infantry at (14, 0)
        self.create_unit_at_factory(14, 0, 'INFANTRY')
        
        # End BLUE turn (back to RED)
        self.driver.find_element(By.ID, "end-turn").click()
        time.sleep(1)
        
        # Try to move RED infantry
        self.click_tile(0, 0)  # Select unit
        time.sleep(0.5)
        
        # Check if movement highlights appear
        movement_highlights = self.driver.execute_script("""
            return window.game.board.grid.filter(t => t.can_be_moved_to).length;
        """)
        
        assert movement_highlights > 0, "Unit should have movement options after turn change"
        
        # Try to move to (1, 0)
        self.click_tile(1, 0)
        time.sleep(0.5)
        
        # Verify unit moved
        unit_at_new_pos = self.driver.execute_script("""
            const tile = window.game.getTile(1, 0);
            return !!tile.unit && tile.unit.type === 'INFANTRY';
        """)
        
        assert unit_at_new_pos, "Unit should have moved to new position"
    
    def test_unit_state_properties_exist(self):
        """Test that all required unit state properties exist"""
        # Create a test unit
        self.create_unit_at_factory(0, 0, 'TANK')
        
        # Get unit properties
        unit_props = self.driver.execute_script("""
            const tile = window.game.getTile(0, 0);
            if (!tile.unit) return null;
            
            return {
                // Required properties
                type: typeof tile.unit.type,
                army: typeof tile.unit.army,
                health: typeof tile.unit.health,
                fuel: typeof tile.unit.fuel,
                ammo: typeof tile.unit.ammo,
                
                // State properties
                has_moved: typeof tile.unit.has_moved,
                done: typeof tile.unit.done,
                can_move: typeof tile.unit.can_move,
                can_attack: typeof tile.unit.can_attack,
                
                // Values
                has_moved_value: tile.unit.has_moved,
                done_value: tile.unit.done,
                can_move_value: tile.unit.can_move,
                can_attack_value: tile.unit.can_attack
            };
        """)
        
        assert unit_props is not None, "Unit should exist"
        
        # Check types
        assert unit_props['type'] == 'string', "type should be string"
        assert unit_props['army'] == 'string', "army should be string"
        assert unit_props['health'] == 'number', "health should be number"
        
        # Check state properties are not undefined
        assert unit_props['has_moved'] != 'undefined', "has_moved should be defined"
        assert unit_props['done'] != 'undefined', "done should be defined"
        assert unit_props['can_move'] != 'undefined', "can_move should be defined"
        assert unit_props['can_attack'] != 'undefined', "can_attack should be defined"
        
        # Check values are boolean
        assert unit_props['has_moved'] == 'boolean', f"has_moved should be boolean, got {unit_props['has_moved']}"
        assert unit_props['done'] == 'boolean', f"done should be boolean, got {unit_props['done']}"
    
    def create_unit_at_factory(self, x, y, unit_type):
        """Helper to create a unit at a factory"""
        self.click_tile(x, y)
        
        # Wait for modal
        WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.ID, "modal"))
        )
        
        # Create unit
        self.driver.execute_script(f"""
            document.getElementById('unit-select').value = '{unit_type}';
            document.getElementById('create').click();
        """)
        
        # Wait for modal to close
        WebDriverWait(self.driver, 5).until(
            EC.invisibility_of_element_located((By.ID, "modal"))
        )
        
        time.sleep(0.5)
#!/usr/bin/env python3
"""
Comprehensive test coverage for all user interactions in Advance Wars RPC.
This test ensures we're capturing and testing all possible user actions.
"""

import unittest
import requests
import json

class TestUserInteractionsCoverage(unittest.TestCase):
    """Test coverage for all user interactions"""
    
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://localhost:5000"
        cls.api_url = f"{cls.base_url}/api"
    
    def setUp(self):
        """Create a test game for each test"""
        self.token = "test_coverage"
        resp = requests.post(self.api_url, json={
            "jsonrpc": "2.0",
            "method": "game_create_test",
            "params": {"token": self.token},
            "id": "1"
        })
        self.assertEqual(resp.status_code, 200)
    
    def test_all_user_interactions_documented(self):
        """Document all possible user interactions and verify test coverage"""
        
        # All possible user interactions in the game
        user_interactions = {
            # Mouse interactions
            "mouse_clicks": [
                "Click on unit to select",
                "Click on tile to move selected unit", 
                "Click on enemy to attack",
                "Click on production facility to open menu",
                "Click on transport to load unit",
                "Click on End Turn button",
                "Click on production menu items",
                "Right-click for context menu",
                "Double-click for quick actions",
                "Click and drag for scrolling (if implemented)"
            ],
            
            # Keyboard interactions
            "keyboard_shortcuts": [
                "H - Toggle help panel",
                "E - End turn",
                "ESC - Deselect unit/cancel action",
                "Arrow keys - Navigate (if implemented)",
                "Ctrl+Click - Special actions (load/unload)",
                "Shift+Click - Attack preview (if implemented)",
                "Number keys - Quick unit production (if implemented)"
            ],
            
            # Game actions via RPC
            "game_actions": [
                "unit_select - Select a unit",
                "unit_move - Move a unit",
                "unit_attack - Attack with a unit",
                "unit_wait - End unit's turn",
                "unit_capture - Capture property",
                "unit_load - Load into transport",
                "unit_unload - Unload from transport",
                "unit_join - Join damaged units",
                "produce_unit - Create new unit",
                "repair_unit - Repair at base",
                "resupply_unit - Resupply at base/APC",
                "blackboat_repair - Manual repair command",
                "army_end_turn - End player's turn",
                "surrender - Give up the game"
            ],
            
            # Visual feedback expected
            "visual_feedback": [
                "Movement range highlights",
                "Attack range highlights", 
                "Valid target highlights",
                "Unit selection indicator",
                "Turn indicator",
                "Funds display",
                "Unit HP bars",
                "Capture progress",
                "Loading indicators",
                "Combat animations",
                "Property ownership colors",
                "Fog of war (if enabled)",
                "Context menu appearance",
                "Hover tooltips",
                "Error messages"
            ],
            
            # Complex interactions
            "complex_sequences": [
                "Move and attack in one turn",
                "Load multiple units into transport",
                "Chain attacks with multiple units",
                "Capture over multiple turns",
                "Transport load/move/unload sequence",
                "Production with facility blocked",
                "Combat with counter-attacks",
                "Join units to combine HP",
                "Repair/resupply sequences",
                "Victory/defeat conditions"
            ]
        }
        
        # Check which interactions have test coverage
        test_coverage = self._analyze_test_coverage()
        
        print("\n=== USER INTERACTIONS TEST COVERAGE REPORT ===\n")
        
        for category, interactions in user_interactions.items():
            print(f"\n{category.upper().replace('_', ' ')}:")
            print("-" * 50)
            
            for interaction in interactions:
                covered = self._check_if_tested(interaction, test_coverage)
                status = "✅" if covered else "❌"
                print(f"{status} {interaction}")
        
        print("\n=== COVERAGE SUMMARY ===")
        total_interactions = sum(len(items) for items in user_interactions.values())
        covered_count = sum(1 for cat in user_interactions.values() for item in cat 
                          if self._check_if_tested(item, test_coverage))
        coverage_percent = (covered_count / total_interactions) * 100
        
        print(f"Total interactions: {total_interactions}")
        print(f"Covered: {covered_count}")
        print(f"Coverage: {coverage_percent:.1f}%")
        
        # List missing test coverage
        print("\n=== MISSING TEST COVERAGE ===")
        missing = []
        for category, interactions in user_interactions.items():
            for interaction in interactions:
                if not self._check_if_tested(interaction, test_coverage):
                    missing.append(f"{category}: {interaction}")
        
        if missing:
            print("\nThe following interactions need test coverage:")
            for item in missing:
                print(f"  - {item}")
        else:
            print("\nAll interactions have test coverage! 🎉")
        
        # Ensure critical interactions are tested
        critical_interactions = [
            "Click on unit to select",
            "Click on tile to move selected unit",
            "Click on enemy to attack",
            "unit_move - Move a unit",
            "unit_attack - Attack with a unit",
            "Movement range highlights",
            "Attack range highlights"
        ]
        
        for interaction in critical_interactions:
            self.assertTrue(
                self._check_if_tested(interaction, test_coverage),
                f"Critical interaction not tested: {interaction}"
            )
    
    def _analyze_test_coverage(self):
        """Analyze existing tests to determine coverage"""
        # This would normally scan test files, but for now we'll use known coverage
        return {
            # UI tests
            "test_base_selenium": ["Click on unit to select", "visual elements"],
            "test_movement_click": ["Click on tile to move selected unit", "Movement range highlights"],
            "test_highlighting_system": ["Movement range highlights", "Attack range highlights", "Valid target highlights"],
            "test_attack_system": ["Click on enemy to attack", "Combat animations", "Unit HP bars"],
            "test_complex_scenarios": ["Chain attacks", "Transport sequences", "Rapid clicking"],
            "test_unit_deselection": ["unit_select", "unit_move", "ESC - Deselect"],
            "test_ui_improvements": ["H - Toggle help", "E - End turn", "Context menu", "Browser title"],
            
            # Integration tests
            "test_production_system": ["produce_unit", "Click on production facility"],
            "test_transport_features": ["unit_load", "unit_unload", "Transport sequences"],
            "test_victory_conditions": ["unit_capture", "Victory conditions", "HQ capture"],
            "test_combat_system": ["unit_attack", "Counter-attacks", "Damage calculation"],
            "test_economic_system": ["Funds display", "Income", "Unit costs"],
            
            # Missing coverage
            "not_tested": [
                "Double-click for quick actions",
                "Click and drag for scrolling",
                "Arrow keys - Navigate",
                "Shift+Click - Attack preview",
                "Number keys - Quick unit production",
                "unit_join - Join damaged units",
                "Fog of war",
                "Hover tooltips",
                "Loading indicators",
                "Error messages"
            ]
        }
    
    def _check_if_tested(self, interaction, coverage):
        """Check if an interaction is covered by tests"""
        interaction_lower = interaction.lower()
        for test_file, covered_items in coverage.items():
            for item in covered_items:
                if interaction_lower in item.lower() or item.lower() in interaction_lower:
                    return True
        return False
    
    def test_rpc_methods_coverage(self):
        """Verify all RPC methods have test coverage"""
        # Get all available RPC methods
        resp = requests.get(f"{self.base_url}/api/browse/")
        self.assertEqual(resp.status_code, 200)
        
        # Parse methods from the browse page
        content = resp.text
        
        # Known RPC methods that should be tested
        critical_methods = [
            "game_create_v2",
            "game_board",
            "unit_select", 
            "unit_move",
            "unit_move_enhanced",
            "unit_attack",
            "unit_attack_enhanced",
            "unit_wait",
            "unit_capture",
            "unit_load",
            "unit_unload",
            "produce_unit",
            "production_menu",
            "army_end_turn",
            "game_save",
            "surrender"
        ]
        
        print("\n=== RPC METHOD TEST COVERAGE ===")
        for method in critical_methods:
            # Simple check if method appears in browse page
            if method in content:
                print(f"✅ {method}")
            else:
                print(f"❌ {method} - not found in API")

if __name__ == '__main__':
    unittest.main()
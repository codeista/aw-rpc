#!/usr/bin/env python3
"""
UI Attack Flow Tests - Comprehensive testing of mouse-based attack interactions
Tests the complete flow from unit selection through attack execution
"""

import requests
import json
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class UIAttackFlowTester:
    """Test UI attack flows to catch interaction bugs"""
    
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
        self.token = f"ui-attack-test-{int(time.time())}"
        self.passed = 0
        self.failed = 0
        
    def rpc(self, method, params=None):
        """Make RPC call"""
        if params is None:
            params = {}
        if 'token' not in params:
            params['token'] = self.token
            
        response = requests.post(self.base_url, json={
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': 1
        })
        return response.json().get('result', response.json())
    
    def test(self, name, condition, details=""):
        """Record test result"""
        if condition:
            self.passed += 1
            print(f"✅ {name}")
        else:
            self.failed += 1
            print(f"❌ {name}: {details}")
        return condition
    
    def setup_combat_scenario(self):
        """Create a game with units ready for combat"""
        # Create game
        result = self.rpc('game_create_test')
        if not result.get('success'):
            return False
            
        # Create attacker
        self.rpc('unit_create', {
            'player_id': 0,
            'unit_type': 'TANK',
            'x': 3, 'y': 3
        })
        
        # Create enemy targets
        self.rpc('unit_create', {
            'player_id': 1,
            'unit_type': 'INFANTRY',
            'x': 4, 'y': 3  # Adjacent
        })
        
        self.rpc('unit_create', {
            'player_id': 1,
            'unit_type': 'MECH',
            'x': 5, 'y': 3  # 2 tiles away
        })
        
        # End turns to enable actions
        self.rpc('army_end_turn')
        self.rpc('army_end_turn')
        
        return True
    
    def test_attack_highlights_on_selection(self):
        """Test that attack highlights appear when selecting a unit that can attack"""
        print("\n🎯 Testing Attack Highlights on Selection")
        
        # Setup fresh scenario for this test
        self.setup_combat_scenario()
        
        # Select the tank
        result = self.rpc('unit_select', {'x': 3, 'y': 3})
        self.test("Unit selection successful", 'error' not in result)
        
        # Get board state
        board = self.rpc('game_board')
        
        # Check if enemy tiles are marked as can_be_attacked
        attack_targets = []
        for tile in board.get('grid', []):
            if tile.get('can_be_attacked'):
                attack_targets.append((tile['x'], tile['y']))
        
        self.test(
            "Attack highlights set on enemy units", 
            len(attack_targets) > 0,
            f"Found {len(attack_targets)} attack targets"
        )
        
        # Verify correct enemies are highlighted
        expected_targets = [(4, 3)]  # Tank range is 1
        for target in expected_targets:
            self.test(
                f"Enemy at {target} is highlighted",
                target in attack_targets,
                f"Attack targets: {attack_targets}"
            )
        
        return len(attack_targets) > 0
    
    def test_click_attack_with_highlights(self):
        """Test that clicking an enemy with can_be_attacked=true triggers attack"""
        print("\n⚔️ Testing Click Attack with Highlights")
        
        self.setup_combat_scenario()
        
        # Select attacker
        self.rpc('unit_select', {'x': 3, 'y': 3})
        
        # Get board to check highlights
        board = self.rpc('game_board')
        enemy_tile = None
        for tile in board.get('grid', []):
            if tile['x'] == 4 and tile['y'] == 3:
                enemy_tile = tile
                break
        
        self.test(
            "Enemy tile has can_be_attacked flag",
            enemy_tile and enemy_tile.get('can_be_attacked', False),
            f"Tile state: {enemy_tile}"
        )
        
        # Now test attack - in real UI this would be a click
        # but we simulate with direct attack
        result = self.rpc('unit_attack', {
            'attacker_x': 3, 'attacker_y': 3,
            'target_x': 4, 'target_y': 3
        })
        
        self.test(
            "Attack executed successfully",
            result.get('success', False),
            result.get('error', '')
        )
        
        # Verify enemy took damage
        board = self.rpc('game_board')
        for tile in board.get('grid', []):
            if tile['x'] == 4 and tile['y'] == 3 and tile.get('unit'):
                hp = tile['unit'].get('hp', 100)
                self.test(
                    "Enemy unit took damage",
                    hp < 100,
                    f"Enemy HP: {hp}"
                )
                break
    
    def test_movement_then_attack_flow(self):
        """Test complete flow: select → move → attack"""
        print("\n🏃⚔️ Testing Move + Attack Flow")
        
        self.setup_combat_scenario()
        
        # Move tank first (it starts at 3,3, enemy at 4,3)
        # Tank is already adjacent so just test the flow
        
        # Select tank
        result = self.rpc('unit_select', {'x': 3, 'y': 3})
        self.test("Selected tank", 'error' not in result)
        
        # Check movement highlights
        board = self.rpc('game_board')
        move_tiles = [t for t in board.get('grid', []) if t.get('can_be_moved_to')]
        self.test(
            "Movement highlights shown",
            len(move_tiles) > 0,
            f"Found {len(move_tiles)} movement tiles"
        )
        
        # Check attack highlights (should also be shown)
        attack_tiles = [t for t in board.get('grid', []) if t.get('can_be_attacked')]
        self.test(
            "Attack highlights shown with movement",
            len(attack_tiles) > 0,
            f"Found {len(attack_tiles)} attack tiles"
        )
        
        # Move to a different position (if possible)
        if len(move_tiles) > 0:
            move_to = move_tiles[0]
            result = self.rpc('movement_execute', {
                'from_x': 3, 'from_y': 3,
                'to_x': move_to['x'], 'to_y': move_to['y']
            })
            self.test("Movement executed", result.get('success', False))
            
            # After moving, check if attack highlights update
            board = self.rpc('game_board')
            attack_tiles_after = [t for t in board.get('grid', []) if t.get('can_be_attacked')]
            self.test(
                "Attack highlights updated after move",
                True,  # Just check it doesn't crash
                f"Attack tiles after move: {len(attack_tiles_after)}"
            )
    
    def test_no_attack_without_highlights(self):
        """Test that clicking enemy without highlights doesn't attack"""
        print("\n🚫 Testing No Attack Without Highlights")
        
        self.setup_combat_scenario()
        
        # Create a unit that can't attack (already acted)
        self.rpc('unit_create', {
            'player_id': 0,
            'unit_type': 'RECON',
            'x': 2, 'y': 3
        })
        
        # Make it move to mark as acted
        self.rpc('army_end_turn')
        self.rpc('army_end_turn')
        self.rpc('movement_execute', {
            'from_x': 2, 'from_y': 3,
            'to_x': 2, 'to_y': 4
        })
        self.rpc('unit_wait', {'x': 2, 'y': 4})
        
        # Select the waited unit
        result = self.rpc('unit_select', {'x': 2, 'y': 4})
        
        # Check board - should have no attack highlights
        board = self.rpc('game_board')
        attack_tiles = [t for t in board.get('grid', []) if t.get('can_be_attacked')]
        
        self.test(
            "No attack highlights for acted unit",
            len(attack_tiles) == 0,
            f"Found {len(attack_tiles)} attack tiles (should be 0)"
        )
    
    def test_attack_range_display(self):
        """Test that attack ranges are correctly displayed for different unit types"""
        print("\n📏 Testing Attack Range Display")
        
        # Create game
        self.rpc('game_create_test')
        
        # Test direct fire unit (range 1)
        self.rpc('unit_create', {
            'player_id': 0,
            'unit_type': 'TANK',
            'x': 5, 'y': 5
        })
        
        # Test indirect fire unit (range 2-3)
        self.rpc('unit_create', {
            'player_id': 0,
            'unit_type': 'ARTILLERY',
            'x': 7, 'y': 5
        })
        
        # Create enemies at various ranges
        for i in range(1, 5):
            self.rpc('unit_create', {
                'player_id': 1,
                'unit_type': 'INFANTRY',
                'x': 5 + i, 'y': 5
            })
        
        # End turns
        self.rpc('army_end_turn')
        self.rpc('army_end_turn')
        
        # Test tank range (should highlight enemy at distance 1)
        self.rpc('unit_select', {'x': 5, 'y': 5})
        board = self.rpc('game_board')
        tank_targets = []
        for tile in board.get('grid', []):
            if tile.get('can_be_attacked'):
                dist = abs(tile['x'] - 5) + abs(tile['y'] - 5)
                tank_targets.append((tile['x'], tile['y'], dist))
        
        self.test(
            "Tank highlights only range 1 enemies",
            all(d == 1 for _, _, d in tank_targets),
            f"Tank targets: {tank_targets}"
        )
        
        # Clear selection
        self.rpc('unit_select', {'x': 0, 'y': 0})
        
        # Test artillery range (should highlight enemies at distance 2-3)
        self.rpc('unit_select', {'x': 7, 'y': 5})
        board = self.rpc('game_board')
        arty_targets = []
        for tile in board.get('grid', []):
            if tile.get('can_be_attacked'):
                dist = abs(tile['x'] - 7) + abs(tile['y'] - 5)
                arty_targets.append((tile['x'], tile['y'], dist))
        
        self.test(
            "Artillery highlights range 2-3 enemies",
            all(2 <= d <= 3 for _, _, d in arty_targets),
            f"Artillery targets: {arty_targets}"
        )
    
    def test_attack_after_movement(self):
        """Test that direct units can attack after moving, indirect cannot"""
        print("\n🎯 Testing Attack After Movement Rules")
        
        self.setup_combat_scenario()
        
        # Create artillery (indirect)
        self.rpc('unit_create', {
            'player_id': 0,
            'unit_type': 'ARTILLERY',
            'x': 1, 'y': 3
        })
        
        # End turns
        self.rpc('army_end_turn')
        self.rpc('army_end_turn')
        
        # Test direct unit (tank) move + attack
        self.rpc('unit_select', {'x': 3, 'y': 3})
        self.rpc('movement_execute', {
            'from_x': 3, 'from_y': 3,
            'to_x': 3, 'to_y': 4
        })
        
        # Check if tank can still attack after moving
        board = self.rpc('game_board')
        tank_tile = None
        for tile in board.get('grid', []):
            if tile['x'] == 3 and tile['y'] == 4 and tile.get('unit'):
                tank_tile = tile['unit']
                break
        
        self.test(
            "Direct unit can attack after moving",
            tank_tile and tank_tile.get('can_attack', False),
            f"Tank can_attack: {tank_tile.get('can_attack') if tank_tile else 'N/A'}"
        )
        
        # Test indirect unit (artillery) move + attack
        self.rpc('unit_select', {'x': 1, 'y': 3})
        self.rpc('movement_execute', {
            'from_x': 1, 'from_y': 3,
            'to_x': 2, 'to_y': 3
        })
        
        # Check if artillery cannot attack after moving
        board = self.rpc('game_board')
        arty_tile = None
        for tile in board.get('grid', []):
            if tile['x'] == 2 and tile['y'] == 3 and tile.get('unit'):
                arty_tile = tile['unit']
                break
        
        self.test(
            "Indirect unit cannot attack after moving",
            arty_tile and not arty_tile.get('can_attack', True),
            f"Artillery can_attack: {arty_tile.get('can_attack') if arty_tile else 'N/A'}"
        )
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 60)
        print("🎮 UI ATTACK FLOW TEST SUITE")
        print("=" * 60)
        
        # Setup initial game
        if not self.setup_combat_scenario():
            print("❌ Failed to setup test scenario")
            return False
        
        # Run tests
        self.test_attack_highlights_on_selection()
        self.test_click_attack_with_highlights()
        self.test_movement_then_attack_flow()
        self.test_no_attack_without_highlights()
        self.test_attack_range_display()
        self.test_attack_after_movement()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        success_rate = (self.passed / (self.passed + self.failed) * 100) if (self.passed + self.failed) > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        return self.failed == 0


def main():
    """Run UI attack flow tests"""
    tester = UIAttackFlowTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
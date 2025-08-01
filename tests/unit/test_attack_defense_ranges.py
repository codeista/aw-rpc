#!/usr/bin/env python3
"""
Comprehensive test suite for attack and defense ranges in Advance Wars RPC.
Tests indirect fire units, counter-attack mechanics, and range restrictions.
"""

import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from manager import GameManager
from gameboard import GameBoard, GameTile
from player_system import PlayerManager, Player, SpriteColor
from game_factory import GameFactory
from config import Config
from unit import Unit, UnitType
from map_system import MapTile, MapType, Army

class TestAttackDefenseRanges(unittest.TestCase):
    """Test attack ranges, defense capabilities, and counter-attack rules"""
    
    def setUp(self):
        """Create a test game with various unit types"""
        # Use GameFactory to create a proper v2 game
        players = [
            {"name": "Player 1", "color": "Red", "sprite_color": "RED"},
            {"name": "Player 2", "color": "Blue", "sprite_color": "BLUE"}
        ]
        
        self.manager, _ = GameFactory.create_game_with_players('test', players)
        self.board = self.manager.board
        
        # Give lots of funds for testing
        self.manager.board_v2.player_funds[0] = 500000
        self.manager.board_v2.player_funds[1] = 500000
        self.manager._update_army_funds(Army.RED, 0)  # Update to 500000
        self.manager._update_army_funds(Army.BLUE, 0)  # Update to 500000
    
    def create_unit(self, unit_type, army, x, y):
        """Helper to create a unit at position"""
        # First place appropriate facility if needed
        tile = self.manager.tile_at(x, y).mapTile
        
        # Determine which facility type we need
        if unit_type in [UnitType.BATTLESHIP, UnitType.CRUISER, UnitType.CARRIER, UnitType.SUB, UnitType.LANDER, UnitType.BLACKBOAT]:
            tile.type = MapType.PORT
            tile.army = Army[army]
        elif unit_type in [UnitType.FIGHTER, UnitType.BOMBER, UnitType.BCOPTER, UnitType.TCOPTER, UnitType.STEALTH, UnitType.BLACKBOMB]:
            tile.type = MapType.AIRPORT
            tile.army = Army[army]
        else:
            tile.type = MapType.FACTORY
            tile.army = Army[army]
        
        # Create unit using manager method
        unit = self.manager.unit_create(army, unit_type.name, x, y)
        # Return position tuple along with unit for easy tracking
        return (x, y, unit)
    
    def test_battleship_cannot_counter_at_any_range(self):
        """Test that battleships cannot counter-attack at ANY range (indirect unit rule)"""
        # Create battleship (indirect unit with range 2-6)
        bx, by, battleship = self.create_unit(UnitType.BATTLESHIP, "RED", 11, 1)
        
        # Test 1: Attack at range 1 (below minimum)
        sx, sy, sub = self.create_unit(UnitType.SUB, "BLUE", 11, 2)
        
        # End RED turn so BLUE can attack
        self.manager.army_end_turn()
        
        result = self.manager.unit_attack_enhanced(sx, sy, bx, by)
        
        self.assertGreater(result.attacker_damage_dealt, 0, "Battleship should take damage")
        self.assertEqual(result.defender_damage_dealt, 0, "Battleship cannot counter (indirect unit)")
        self.assertFalse(result.counter_attack_occurred, "No counter-attack from indirect unit")
        
        # Clear attacker
        self.manager.unit_remove(11, 2)
        
        # Test 2: Attack at range 3 (within battleship's attack range)
        # First recreate the RED battleship since it might have been destroyed
        if not self.manager.unit_at(bx, by):
            bx, by, battleship = self.create_unit(UnitType.BATTLESHIP, "RED", 11, 1)
            
        ebx, eby, enemy_battleship = self.create_unit(UnitType.BATTLESHIP, "BLUE", 11, 4)
        
        # End turns to allow the new unit to act
        self.manager.army_end_turn()  # End BLUE turn
        self.manager.army_end_turn()  # End RED turn, back to BLUE
        
        result = self.manager.unit_attack_enhanced(ebx, eby, bx, by)
        
        self.assertGreater(result.attacker_damage_dealt, 0, "Battleship should take damage")
        self.assertEqual(result.defender_damage_dealt, 0, "Battleship still cannot counter (indirect)")
        self.assertFalse(result.counter_attack_occurred, "Indirect units never counter-attack")
    
    def test_all_indirect_units_cannot_counter(self):
        """Test that ALL indirect units cannot counter-attack"""
        indirect_units = [
            (UnitType.ARTILLERY, "Artillery"),
            (UnitType.ROCKET, "Rocket"),
            (UnitType.MISSILE, "Missile"),
            (UnitType.BATTLESHIP, "Battleship"),
            (UnitType.CARRIER, "Carrier"),
            (UnitType.PIPERUNNER, "Piperunner")
        ]
        
        for unit_type, name in indirect_units:
            with self.subTest(unit=name):
                # Clear board
                for tile in self.board.grid:
                    tile.unit = None
                
                # Reset turn
                self.board.current_turn = Army.RED
                
                # Create indirect unit
                if unit_type in [UnitType.BATTLESHIP, UnitType.CARRIER]:
                    ix, iy, indirect = self.create_unit(unit_type, "RED", 11, 1)
                    ax, ay, attacker = self.create_unit(UnitType.SUB, "BLUE", 11, 2)
                elif unit_type == UnitType.MISSILE:
                    ix, iy, indirect = self.create_unit(unit_type, "RED", 5, 5)
                    ax, ay, attacker = self.create_unit(UnitType.TANK, "BLUE", 5, 6)  # Ground unit
                else:
                    ix, iy, indirect = self.create_unit(unit_type, "RED", 5, 5)
                    ax, ay, attacker = self.create_unit(UnitType.TANK, "BLUE", 5, 6)  # Range 1
                
                # Ensure units are ready  
                self.manager.unit_wait(ix, iy)
                self.manager.army_end_turn()
                
                # Attack indirect unit
                result = self.manager.unit_attack_enhanced(ax, ay, ix, iy)
                
                # Verify no counter-attack
                self.assertEqual(result.defender_damage_dealt, 0, 
                               f"{name} should never counter-attack")
                self.assertFalse(result.counter_attack_occurred, 
                               f"{name} is indirect and cannot counter")
    
    def test_artillery_minimum_range(self):
        """Test artillery cannot attack at range 1"""
        # Create artillery (range 2-3)
        ax, ay, artillery = self.create_unit(UnitType.ARTILLERY, "RED", 5, 5)
        
        # Create target at range 1
        ix, iy, infantry = self.create_unit(UnitType.INFANTRY, "BLUE", 5, 6)
        
        # End turns to allow attack
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Try to attack - should fail due to minimum range
        with self.assertRaises(ValueError) as context:
            self.manager.unit_attack_enhanced(ax, ay, ix, iy)
        
        self.assertIn("out of range", str(context.exception).lower())
    
    def test_artillery_maximum_range(self):
        """Test artillery can attack at range 2-3 but not beyond"""
        ax, ay, artillery = self.create_unit(UnitType.ARTILLERY, "RED", 5, 5)
        
        # Create targets at various ranges
        tx1, ty1, target1 = self.create_unit(UnitType.INFANTRY, "BLUE", 5, 7)  # Range 2
        tx2, ty2, target2 = self.create_unit(UnitType.INFANTRY, "BLUE", 5, 8)  # Range 3
        tx3, ty3, target3 = self.create_unit(UnitType.INFANTRY, "BLUE", 5, 9)  # Range 4
        
        # End turns to allow attack
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Test range 2 - should work
        result = self.manager.unit_attack_enhanced(ax, ay, tx1, ty1)
        self.assertGreater(result.attacker_damage_dealt, 0, "Artillery can attack at range 2")
        
        # Recreate artillery since it used its turn
        self.manager.unit_remove(ax, ay)
        ax, ay, artillery = self.create_unit(UnitType.ARTILLERY, "RED", 5, 5)
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Test range 3 - should work
        result = self.manager.unit_attack_enhanced(ax, ay, tx2, ty2)
        self.assertGreater(result.attacker_damage_dealt, 0, "Artillery can attack at range 3")
        
        # Recreate artillery
        self.manager.unit_remove(ax, ay)
        ax, ay, artillery = self.create_unit(UnitType.ARTILLERY, "RED", 5, 5)
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Test range 4 - should fail
        with self.assertRaises(ValueError) as context:
            self.manager.unit_attack_enhanced(ax, ay, tx3, ty3)
        self.assertIn("out of range", str(context.exception).lower())
    
    def test_direct_units_can_counter(self):
        """Test that direct units CAN counter-attack when in range"""
        direct_units = [
            UnitType.INFANTRY, UnitType.MECH, UnitType.RECON, UnitType.ANTIAIR,
            UnitType.TANK, UnitType.MEDIUMTANK, UnitType.NEOTANK, UnitType.MEGATANK,
            UnitType.APC, UnitType.CRUISER, UnitType.FIGHTER, UnitType.BOMBER,
            UnitType.BCOPTER, UnitType.TCOPTER, UnitType.STEALTH, UnitType.SUB,
            UnitType.LANDER, UnitType.BLACKBOAT, UnitType.PIPERUNNER
        ]
        
        for unit_type in direct_units:
            with self.subTest(unit=unit_type.name):
                # Clear board
                for tile in self.board.grid:
                    tile.unit = None
                
                # Reset turn
                self.board.current_turn = Army.RED
                
                # Create units at range 1
                if unit_type == UnitType.CRUISER:
                    dx, dy, defender = self.create_unit(unit_type, "RED", 11, 1)
                    ax, ay, attacker = self.create_unit(UnitType.SUB, "BLUE", 11, 2)
                else:
                    dx, dy, defender = self.create_unit(unit_type, "RED", 5, 5)
                    # Use MECH which has secondary weapons vs infantry/mech but primary vs tanks
                    if unit_type in [UnitType.INFANTRY, UnitType.MECH]:
                        ax, ay, attacker = self.create_unit(UnitType.MECH, "BLUE", 5, 6)
                    else:
                        ax, ay, attacker = self.create_unit(UnitType.TANK, "BLUE", 5, 6)
                
                # Ensure units are ready
                self.manager.unit_wait(dx, dy)
                self.manager.army_end_turn()
                
                # Attack direct unit
                result = self.manager.unit_attack_enhanced(ax, ay, dx, dy)
                
                # Verify counter-attack occurs (if unit can damage attacker)
                defender_unit = self.manager.unit_at(dx, dy)
                attacker_unit = self.manager.unit_at(ax, ay)
                if defender_unit and attacker_unit and defender_unit._select_weapon_damage(attacker_unit) > 0:
                    self.assertGreater(result.defender_damage_dealt, 0, 
                                     f"{unit_type.name} should counter-attack")
                    self.assertTrue(result.counter_attack_occurred, 
                                  f"{unit_type.name} is direct and should counter")
    
    def test_missile_anti_air_only(self):
        """Test missile units can only attack air units"""
        mx, my, missile = self.create_unit(UnitType.MISSILE, "RED", 5, 5)
        
        # Create various targets
        tx, ty, tank = self.create_unit(UnitType.TANK, "BLUE", 8, 5)  # Range 3
        fx, fy, fighter = self.create_unit(UnitType.FIGHTER, "BLUE", 7, 5)  # Range 2 (too close)
        bx, by, bomber = self.create_unit(UnitType.BOMBER, "BLUE", 8, 6)  # Range 4
        
        # End turns to allow attack
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Test attacking ground unit - should fail
        with self.assertRaises(ValueError) as context:
            self.manager.unit_attack_enhanced(mx, my, tx, ty)
        self.assertIn("cannot attack", str(context.exception).lower())
        
        # Test attacking air unit too close - should fail
        with self.assertRaises(ValueError) as context:
            self.manager.unit_attack_enhanced(mx, my, fx, fy)
        self.assertIn("out of range", str(context.exception).lower())
        
        # Test attacking air unit in range - should work
        result = self.manager.unit_attack_enhanced(mx, my, bx, by)
        self.assertGreater(result.attacker_damage_dealt, 0, "Missile can attack bomber at range 4")
    
    def test_direct_unit_ranges(self):
        """Test that direct units have range 1 only"""
        direct_units = [
            UnitType.INFANTRY, UnitType.MECH, UnitType.RECON, UnitType.ANTIAIR,
            UnitType.TANK, UnitType.MEDIUMTANK, UnitType.NEOTANK, UnitType.MEGATANK,
            UnitType.APC, UnitType.CRUISER, UnitType.FIGHTER, UnitType.BOMBER,
            UnitType.BCOPTER, UnitType.TCOPTER, UnitType.STEALTH, UnitType.SUB,
            UnitType.LANDER, UnitType.BLACKBOAT
        ]
        
        for unit_type in direct_units:
            with self.subTest(unit=unit_type.name):
                # Clear board
                for tile in self.board.grid:
                    tile.unit = None
                
                # Create unit at center
                if unit_type == UnitType.CRUISER:
                    ux, uy, unit = self.create_unit(unit_type, "RED", 11, 1)
                    # Create targets
                    t1x, t1y, t1 = self.create_unit(UnitType.SUB, "BLUE", 11, 2)  # Range 1
                    t2x, t2y, t2 = self.create_unit(UnitType.SUB, "BLUE", 11, 3)  # Range 2
                else:
                    ux, uy, unit = self.create_unit(unit_type, "RED", 7, 5)
                    # Create targets  
                    t1x, t1y, t1 = self.create_unit(UnitType.INFANTRY, "BLUE", 7, 6)  # Range 1
                    t2x, t2y, t2 = self.create_unit(UnitType.INFANTRY, "BLUE", 7, 7)  # Range 2
                
                # End turns
                self.manager.army_end_turn()
                self.manager.army_end_turn()
                
                # Test range 1 - should work
                result = self.manager.unit_attack_enhanced(ux, uy, t1x, t1y)
                self.assertGreater(result.attacker_damage_dealt, 0, f"{unit_type.name} can attack at range 1")
                
                # Recreate attacker
                self.manager.unit_remove(ux, uy)
                ux, uy, unit = self.create_unit(unit_type, "RED", ux, uy)
                self.manager.army_end_turn()
                self.manager.army_end_turn()
                
                # Test range 2 - should fail
                with self.assertRaises(ValueError) as context:
                    self.manager.unit_attack_enhanced(ux, uy, t2x, t2y)
                self.assertIn("out of range", str(context.exception).lower())
    
    def test_counter_attack_with_reduced_hp(self):
        """Test counter-attack damage is calculated with defender's reduced HP"""
        # Create two tanks
        ax, ay, attacker = self.create_unit(UnitType.TANK, "RED", 5, 5)
        dx, dy, defender = self.create_unit(UnitType.TANK, "BLUE", 5, 6)
        
        # Set defender to 70 HP so it survives the attack
        defender_unit = self.manager.unit_at(dx, dy)
        defender_unit.status.hp = 70
        
        # End turns to allow attack
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Attack
        result = self.manager.unit_attack_enhanced(ax, ay, dx, dy)
        
        # Debug info
        print(f"Attacker damage dealt: {result.attacker_damage_dealt}")
        print(f"Defender HP before: {result.defender_hp_before}")
        print(f"Defender HP after: {result.defender_hp_after}")
        print(f"Counter-attack occurred: {result.counter_attack_occurred}")
        print(f"Counter damage: {result.defender_damage_dealt}")
        
        # Verify counter-attack occurred
        self.assertTrue(result.counter_attack_occurred, "Counter-attack should occur")
        
        # Counter damage is based on defender's HP AFTER taking damage
        # Defender has 26 HP left (26%), so damage is ~55 * 0.26 = ~14
        # With terrain defense, it could be even lower
        self.assertLess(result.defender_damage_dealt, 20, 
                       "Counter damage should be reduced due to defender's lower HP")
        self.assertGreater(result.defender_damage_dealt, 5,
                          "Counter damage should still occur")
    
    def test_carrier_missile_range(self):
        """Test carrier has long missile range 3-8"""
        cx, cy, carrier = self.create_unit(UnitType.CARRIER, "RED", 5, 5)
        
        # Just test a few key ranges instead of all 9
        # Range 2 (too close)
        f2x, f2y, f2 = self.create_unit(UnitType.FIGHTER, "BLUE", 7, 5)
        # Range 3 (minimum)
        f3x, f3y, f3 = self.create_unit(UnitType.FIGHTER, "BLUE", 8, 5)
        # Range 5 (mid-range)
        f5x, f5y, f5 = self.create_unit(UnitType.FIGHTER, "BLUE", 10, 5)
        # Range 6 (still valid)
        f6x, f6y, f6 = self.create_unit(UnitType.FIGHTER, "BLUE", 11, 5)
        
        targets_created = [(7, 5, 2), (8, 5, 3), (10, 5, 5), (11, 5, 6)]
        
        # End turns
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Test ranges
        for x, y, range_val in targets_created:
            # Clear previous attack state
            if not self.manager.unit_at(cx, cy):
                cx, cy, carrier = self.create_unit(UnitType.CARRIER, "RED", 5, 5)
                self.manager.army_end_turn()
                self.manager.army_end_turn()
            
            if 3 <= range_val <= 8:
                # Should be able to attack
                try:
                    result = self.manager.unit_attack_enhanced(cx, cy, x, y)
                    self.assertGreater(result.attacker_damage_dealt, 0, 
                                     f"Carrier should attack at range {range_val}")
                    # Recreate carrier for next test
                    self.manager.unit_remove(cx, cy)
                except ValueError as e:
                    self.fail(f"Carrier should be able to attack at range {range_val}: {e}")
            else:
                # Should not be able to attack
                with self.assertRaises(ValueError) as context:
                    self.manager.unit_attack_enhanced(cx, cy, x, y)
                self.assertIn("out of range", str(context.exception).lower())
    
    def test_no_friendly_fire(self):
        """Test units cannot attack friendly units"""
        # Create friendly units
        tx1, ty1, tank1 = self.create_unit(UnitType.TANK, "RED", 5, 5)
        tx2, ty2, tank2 = self.create_unit(UnitType.TANK, "RED", 5, 6)
        
        # End turns
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Try to attack friendly unit - should fail
        with self.assertRaises(ValueError) as context:
            self.manager.unit_attack_enhanced(tx1, ty1, tx2, ty2)
        
        self.assertIn("friendly", str(context.exception).lower())
    
    def test_attack_after_movement(self):
        """Test Advance Wars movement rules: direct units can move+attack, indirect units cannot"""
        # Test 1: Direct unit (Tank) CAN move and attack
        tx, ty, tank = self.create_unit(UnitType.TANK, "RED", 5, 5)
        ex, ey, enemy = self.create_unit(UnitType.INFANTRY, "BLUE", 8, 5)
        
        # End turns to allow movement
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Move tank closer (direct unit)
        self.manager.unit_move(tx, ty, 7, 5)
        
        # Tank should be able to attack after moving (direct unit rule)
        result = self.manager.unit_attack_enhanced(7, 5, ex, ey)
        self.assertGreater(result.attacker_damage_dealt, 0, "Direct units can move and attack")
        
        # Test 2: Indirect unit (Artillery) CANNOT move and attack
        # Clear board first
        for tile in self.board.grid:
            tile.unit = None
        self.board.current_turn = Army.RED
        
        ax, ay, artillery = self.create_unit(UnitType.ARTILLERY, "RED", 5, 5)
        ix, iy, infantry = self.create_unit(UnitType.INFANTRY, "BLUE", 8, 5)
        
        # End turns
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Move artillery
        self.manager.unit_move(ax, ay, 6, 5)
        
        # Artillery should NOT be able to attack after moving (indirect unit rule)
        with self.assertRaises(ValueError) as context:
            self.manager.unit_attack_enhanced(6, 5, ix, iy)
        
        self.assertIn("cannot attack", str(context.exception).lower())

if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
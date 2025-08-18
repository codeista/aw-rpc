"""Test Carrier and Cruiser attack+unload restriction"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from manager import GameManager
from core.unit import UnitType
from core.map_system import MapType
from core.game_factory import GameFactory

class TestCarrierCruiserRestriction:
    """Test that Carriers and Cruisers cannot unload after attacking"""
    
    def setup_method(self):
        """Set up test game"""
        # Use GameFactory to create a standard game
        self.manager, self.token = GameFactory.create_standard_game('tiny')
        
        # Give players funds
        self.manager.board_v2.player_funds[0] = 100000
        self.manager.board_v2.player_funds[1] = 100000
    
    def test_carrier_cannot_unload_after_attack(self):
        """Test that Carrier cannot unload after attacking"""
        # Find a sea/port tile to create carrier
        cx, cy = None, None
        for y in range(self.manager.board.height):
            for x in range(self.manager.board.width):
                tile = self.manager.tile_at(x, y)
                if tile.mapTile.type in [MapType.SEA, MapType.PORT]:
                    cx, cy = x, y
                    break
            if cx is not None:
                break
        
        if cx is None:
            # Skip test if no water tiles
            pytest.skip("No water tiles on this map")
        
        # Create carrier for player 0
        result = self.manager.create_unit(0, UnitType.CARRIER, cx, cy)
        assert result['success']
        
        carrier_tile = self.manager.tile_at(cx, cy)
        carrier = carrier_tile.unit
        assert carrier is not None
        
        # Create fighter to load into carrier
        fx, fy = cx, cy - 1 if cy > 0 else cy + 1  # Adjacent to carrier
        result = self.manager.create_unit(0, UnitType.FIGHTER, fx, fy)
        assert result['success']
        
        fighter_tile = self.manager.tile_at(fx, fy)
        fighter = fighter_tile.unit
        
        # Load fighter into carrier
        result = self.manager.transport_system.load_unit_enhanced(
            carrier, fighter, cx, cy, fx, fy
        )
        assert result.success
        assert self.manager.transport_system.get_cargo_count(carrier) == 1
        
        # Create enemy bomber for carrier to attack
        bx, by = 4, 5  # Adjacent to carrier
        result = self.manager.create_unit(1, UnitType.BOMBER, bx, by)
        assert result['success']
        
        bomber_tile = self.manager.tile_at(bx, by)
        bomber = bomber_tile.unit
        
        # End turn to allow units to act
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Carrier attacks bomber
        result = self.manager.unit_attack(cx, cy, bx, by)
        assert result['success']
        
        # Verify carrier has attacked
        assert carrier.has_attacked == True
        
        # Try to unload fighter - should fail
        unload_x, unload_y = 5, 6  # Adjacent empty tile
        can_unload, message = self.manager.transport_system.can_unload_unit(
            carrier, 0, cx, cy, unload_x, unload_y
        )
        assert not can_unload
        assert "cannot unload after attacking" in message
    
    def test_cruiser_cannot_unload_after_attack(self):
        """Test that Cruiser cannot unload after attacking"""
        # Create cruiser for player 0
        cx, cy = 5, 5
        result = self.manager.create_unit(0, UnitType.CRUISER, cx, cy)
        assert result['success']
        
        cruiser_tile = self.manager.tile_at(cx, cy)
        cruiser = cruiser_tile.unit
        assert cruiser is not None
        
        # Create battle copter to load into cruiser
        bcx, bcy = 5, 4  # Adjacent to cruiser
        result = self.manager.create_unit(0, UnitType.BCOPTER, bcx, bcy)
        assert result['success']
        
        bcopter_tile = self.manager.tile_at(bcx, bcy)
        bcopter = bcopter_tile.unit
        
        # Load bcopter into cruiser
        result = self.manager.transport_system.load_unit_enhanced(
            cruiser, bcopter, cx, cy, bcx, bcy
        )
        assert result.success
        assert self.manager.transport_system.get_cargo_count(cruiser) == 1
        
        # Create enemy fighter for cruiser to attack (using anti-air)
        fx, fy = 4, 5  # Adjacent to cruiser
        result = self.manager.create_unit(1, UnitType.FIGHTER, fx, fy)
        assert result['success']
        
        fighter_tile = self.manager.tile_at(fx, fy)
        fighter = fighter_tile.unit
        
        # End turn to allow units to act
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Cruiser attacks fighter with anti-air weapon
        result = self.manager.unit_attack(cx, cy, fx, fy)
        assert result['success']
        
        # Verify cruiser has attacked
        assert cruiser.has_attacked == True
        
        # Try to unload bcopter - should fail
        unload_x, unload_y = 5, 6  # Adjacent empty tile
        can_unload, message = self.manager.transport_system.can_unload_unit(
            cruiser, 0, cx, cy, unload_x, unload_y
        )
        assert not can_unload
        assert "cannot unload after attacking" in message
    
    def test_carrier_can_unload_before_attack(self):
        """Test that Carrier can unload before attacking"""
        # Create carrier for player 0
        cx, cy = 5, 5
        result = self.manager.create_unit(0, UnitType.CARRIER, cx, cy)
        assert result['success']
        
        carrier_tile = self.manager.tile_at(cx, cy)
        carrier = carrier_tile.unit
        
        # Create fighter to load
        fx, fy = 5, 4
        result = self.manager.create_unit(0, UnitType.FIGHTER, fx, fy)
        assert result['success']
        
        fighter_tile = self.manager.tile_at(fx, fy)
        fighter = fighter_tile.unit
        
        # Load fighter
        result = self.manager.transport_system.load_unit_enhanced(
            carrier, fighter, cx, cy, fx, fy
        )
        assert result.success
        
        # End turn
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Verify carrier has NOT attacked yet
        assert not carrier.has_attacked
        
        # Unload fighter - should succeed
        unload_x, unload_y = 5, 6
        can_unload, message = self.manager.transport_system.can_unload_unit(
            carrier, 0, cx, cy, unload_x, unload_y
        )
        assert can_unload
        
        result = self.manager.transport_system.unload_unit_enhanced(
            carrier, 0, cx, cy, unload_x, unload_y
        )
        assert result.success
    
    def test_other_transports_can_unload_after_move(self):
        """Test that other transports (APC, Lander) are not affected by this restriction"""
        # Create lander at beach
        lx, ly = 5, 3  # On beach
        result = self.manager.create_unit(0, UnitType.LANDER, lx, ly)
        assert result['success']
        
        lander_tile = self.manager.tile_at(lx, ly)
        lander = lander_tile.unit
        
        # Create infantry to load
        ix, iy = 5, 2
        result = self.manager.create_unit(0, UnitType.INFANTRY, ix, iy)
        assert result['success']
        
        infantry_tile = self.manager.tile_at(ix, iy)
        infantry = infantry_tile.unit
        
        # Load infantry
        result = self.manager.transport_system.load_unit_enhanced(
            lander, infantry, lx, ly, ix, iy
        )
        assert result.success
        
        # End turn
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Move lander to another beach
        new_lx, new_ly = 5, 7  # South beach
        result = self.manager.unit_move(lx, ly, new_lx, new_ly)
        assert result['success']
        
        # Update lander reference
        lander_tile = self.manager.tile_at(new_lx, new_ly)
        lander = lander_tile.unit
        
        # Lander should be able to unload even after moving (no attack restriction)
        unload_x, unload_y = 5, 8
        can_unload, message = self.manager.transport_system.can_unload_unit(
            lander, 0, new_lx, new_ly, unload_x, unload_y
        )
        assert can_unload
    
    def test_has_attacked_flag_resets_on_turn_start(self):
        """Test that has_attacked flag resets at turn start"""
        # Create carrier
        cx, cy = 5, 5
        result = self.manager.create_unit(0, UnitType.CARRIER, cx, cy)
        assert result['success']
        
        carrier_tile = self.manager.tile_at(cx, cy)
        carrier = carrier_tile.unit
        
        # Create enemy to attack
        ex, ey = 4, 5
        result = self.manager.create_unit(1, UnitType.FIGHTER, ex, ey)
        assert result['success']
        
        # End turn to enable actions
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # Attack
        result = self.manager.unit_attack(cx, cy, ex, ey)
        assert result['success']
        assert carrier.has_attacked == True
        
        # End turn and start new turn
        self.manager.army_end_turn()
        self.manager.army_end_turn()
        
        # has_attacked should be reset
        assert carrier.has_attacked == False


if __name__ == "__main__":
    test = TestCarrierCruiserRestriction()
    test.setup_method()
    
    print("Testing Carrier cannot unload after attack...")
    test.test_carrier_cannot_unload_after_attack()
    print("✓ Passed")
    
    print("Testing Cruiser cannot unload after attack...")
    test.test_cruiser_cannot_unload_after_attack()
    print("✓ Passed")
    
    print("Testing Carrier can unload before attack...")
    test.test_carrier_can_unload_before_attack()
    print("✓ Passed")
    
    print("Testing other transports can unload after move...")
    test.test_other_transports_can_unload_after_move()
    print("✓ Passed")
    
    print("Testing has_attacked flag resets on turn start...")
    test.test_has_attacked_flag_resets_on_turn_start()
    print("✓ Passed")
    
    print("\nAll Carrier/Cruiser restriction tests passed!")
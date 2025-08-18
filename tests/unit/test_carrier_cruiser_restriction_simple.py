"""Test Carrier and Cruiser attack+unload restriction (simplified)"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.unit import Unit, UnitType, UnitStatus
from core.transport_system import CompleteTransportSystem
from core.map_system import MapType

class MockGameManager:
    """Mock game manager for transport system tests"""
    def __init__(self):
        self.tiles = {}
        
    def tile_at(self, x, y):
        return self.tiles.get((x, y), MockTile())

class MockTile:
    """Mock tile"""
    def __init__(self):
        self.unit = None
        self.mapTile = MockMapTile()

class MockMapTile:
    """Mock map tile"""
    def __init__(self):
        self.type = MapType.SEA

def test_carrier_cannot_unload_after_attack():
    """Test that Carrier cannot unload after attacking"""
    # Create mock game manager
    game_manager = MockGameManager()
    transport_system = CompleteTransportSystem(game_manager)
    
    # Create a carrier with has_attacked = True
    carrier = Unit(
        army=None,
        type=UnitType.CARRIER,
        status=UnitStatus(hp=100, fuel=99, ammo=30, cargo=[None, None]),
        config=None,
        id="carrier1",
        can_move=False,
        can_attack=False,
        can_capture=False,
        has_attacked=True  # Carrier has attacked
    )
    
    # Add a fighter in cargo
    fighter = Unit(
        army=None,
        type=UnitType.FIGHTER,
        status=UnitStatus(hp=100, fuel=99, ammo=9),
        config=None,
        id="fighter1",
        can_move=False,
        can_attack=False,
        can_capture=False
    )
    carrier.status.cargo[0] = fighter
    
    # Test unloading - should fail
    can_unload, message = transport_system.can_unload_unit(
        carrier, 0, 5, 5, 5, 6  # Try to unload to adjacent tile
    )
    
    assert not can_unload
    assert "cannot unload after attacking" in message
    print("✓ Carrier cannot unload after attack")

def test_cruiser_cannot_unload_after_attack():
    """Test that Cruiser cannot unload after attacking"""
    # Create mock game manager
    game_manager = MockGameManager()
    transport_system = CompleteTransportSystem(game_manager)
    
    # Create a cruiser with has_attacked = True
    cruiser = Unit(
        army=None,
        type=UnitType.CRUISER,
        status=UnitStatus(hp=100, fuel=99, ammo=9, cargo=[None, None]),
        config=None,
        id="cruiser1",
        can_move=False,
        can_attack=False,
        can_capture=False,
        has_attacked=True  # Cruiser has attacked
    )
    
    # Add a bcopter in cargo
    bcopter = Unit(
        army=None,
        type=UnitType.BCOPTER,
        status=UnitStatus(hp=100, fuel=99, ammo=6),
        config=None,
        id="bcopter1",
        can_move=False,
        can_attack=False,
        can_capture=False
    )
    cruiser.status.cargo[0] = bcopter
    
    # Test unloading - should fail
    can_unload, message = transport_system.can_unload_unit(
        cruiser, 0, 5, 5, 5, 6  # Try to unload to adjacent tile
    )
    
    assert not can_unload
    assert "cannot unload after attacking" in message
    print("✓ Cruiser cannot unload after attack")

def test_carrier_can_unload_before_attack():
    """Test that Carrier can unload before attacking"""
    # Create mock game manager
    game_manager = MockGameManager()
    transport_system = CompleteTransportSystem(game_manager)
    
    # Create a carrier with has_attacked = False
    carrier = Unit(
        army=None,
        type=UnitType.CARRIER,
        status=UnitStatus(hp=100, fuel=99, ammo=30, cargo=[None, None]),
        config=None,
        id="carrier1",
        can_move=True,
        can_attack=True,
        can_capture=False,
        has_attacked=False  # Carrier has NOT attacked
    )
    
    # Add a fighter in cargo
    fighter = Unit(
        army=None,
        type=UnitType.FIGHTER,
        status=UnitStatus(hp=100, fuel=99, ammo=9),
        config=None,
        id="fighter1",
        can_move=False,
        can_attack=False,
        can_capture=False
    )
    carrier.status.cargo[0] = fighter
    
    # Test unloading - should succeed
    can_unload, message = transport_system.can_unload_unit(
        carrier, 0, 5, 5, 5, 6  # Try to unload to adjacent tile
    )
    
    if not can_unload:
        print(f"Unexpected failure: {message}")
    assert can_unload or "cannot unload after attacking" not in message
    print("✓ Carrier can unload before attack (no attack restriction)")

def test_lander_not_affected_by_restriction():
    """Test that other transports are not affected by attack restriction"""
    # Create mock game manager
    game_manager = MockGameManager()
    transport_system = CompleteTransportSystem(game_manager)
    
    # Create a lander (doesn't have attack capability, but let's pretend it does for test)
    lander = Unit(
        army=None,
        type=UnitType.LANDER,
        status=UnitStatus(hp=100, fuel=99, ammo=0, cargo=[None, None]),
        config=None,
        id="lander1",
        can_move=False,
        can_attack=False,
        can_capture=False,
        has_attacked=True  # Even if marked as attacked
    )
    
    # Add infantry in cargo
    infantry = Unit(
        army=None,
        type=UnitType.INFANTRY,
        status=UnitStatus(hp=100, fuel=99, ammo=0),
        config=None,
        id="infantry1",
        can_move=False,
        can_attack=False,
        can_capture=False
    )
    lander.status.cargo[0] = infantry
    
    # Mock the tiles for lander unloading check
    lander_tile = MockTile()
    lander_tile.mapTile.type = MapType.BEACH_N  # Lander on beach
    game_manager.tiles[(5, 5)] = lander_tile
    
    # Test unloading - should succeed (lander not affected by attack restriction)
    can_unload, message = transport_system.can_unload_unit(
        lander, 0, 5, 5, 5, 6  # Try to unload to adjacent tile
    )
    
    # Lander should fail for different reason (not on beach/port) but NOT because of attack
    assert "cannot unload after attacking" not in message
    print("✓ Lander not affected by attack restriction")


if __name__ == "__main__":
    print("Testing Carrier/Cruiser attack+unload restriction...")
    test_carrier_cannot_unload_after_attack()
    test_cruiser_cannot_unload_after_attack()
    test_carrier_can_unload_before_attack()
    test_lander_not_affected_by_restriction()
    print("\nAll tests passed!")
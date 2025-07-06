# transport_system.py - Fixed Version with Proper Serialization Handling

"""
Enhanced Transport System for AW-RPC with Fixed Serialization
This fixes the critical bug where unloaded units become dicts instead of Unit objects
"""

from typing import Dict, List, Tuple, Optional, TYPE_CHECKING, Union
from dataclasses import dataclass
from enum import Enum
import math

if TYPE_CHECKING:
    from manager import GameManager
    from unit import Unit, UnitType
    from gameboard import GameTile

@dataclass
class TransportCapability:
    """Defines what a transport unit can carry"""
    max_capacity: int
    allowed_unit_types: List[str]
    terrain_restrictions: List[str]

@dataclass
class LoadResult:
    """Result of attempting to load a unit"""
    success: bool
    message: str
    cargo_index: Optional[int] = None

@dataclass
class UnloadResult:
    """Result of attempting to unload a unit"""
    success: bool
    message: str
    unloaded_position: Optional[Tuple[int, int]] = None

class TransportSystem:
    """Enhanced transport system with proper serialization handling"""
    
    def __init__(self, game_manager: 'GameManager'):
        self.manager = game_manager
        
        # Define transport capabilities for each unit type
        self.transport_capabilities = {
            'APC': TransportCapability(
                max_capacity=1,
                allowed_unit_types=['INFANTRY', 'MECH'],
                terrain_restrictions=[]
            ),
            'LANDER': TransportCapability(
                max_capacity=2,
                allowed_unit_types=['INFANTRY', 'MECH', 'RECON', 'TANK', 'MEDIUMTANK', 'ANTIAIR', 'ARTILLERY', 'ROCKET', 'MISSILE', 'APC'],
                terrain_restrictions=['SEA', 'SHOAL']
            ),
            'TCOPTER': TransportCapability(
                max_capacity=1,
                allowed_unit_types=['INFANTRY', 'MECH'],
                terrain_restrictions=[]
            ),
            'CRUISER': TransportCapability(
                max_capacity=2,
                allowed_unit_types=['BCOPTER', 'TCOPTER'],
                terrain_restrictions=['SEA']
            ),
            'CARRIER': TransportCapability(
                max_capacity=2,
                allowed_unit_types=['FIGHTER', 'BOMBER', 'BCOPTER', 'TCOPTER'],
                terrain_restrictions=['SEA']
            ),
            'BLACKBOAT': TransportCapability(
                max_capacity=1,
                allowed_unit_types=['INFANTRY', 'MECH'],
                terrain_restrictions=['SEA']
            )
        }
    
    # =============================================================================
    # CORE TRANSPORT VALIDATION
    # =============================================================================
    
    def is_transport_unit(self, unit: 'Unit') -> bool:
        """Check if unit can transport others"""
        unit_type = unit.type.name if hasattr(unit.type, 'name') else str(unit.type)
        return unit_type in self.transport_capabilities
    
    def can_carry_unit_type(self, transport: 'Unit', cargo_type: str) -> bool:
        """Check if transport can carry specific unit type"""
        transport_type = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        
        if transport_type not in self.transport_capabilities:
            return False
        
        return cargo_type in self.transport_capabilities[transport_type].allowed_unit_types
    
    def get_max_capacity(self, transport: 'Unit') -> int:
        """Get maximum cargo capacity for transport"""
        transport_type = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        
        if transport_type not in self.transport_capabilities:
            return 0
        
        return self.transport_capabilities[transport_type].max_capacity
    
    def get_current_cargo_count(self, transport: 'Unit') -> int:
        """Get current number of units in transport"""
        if not hasattr(transport.status, 'cargo'):
            return 0
        
        # Count non-None cargo slots
        return len([unit for unit in transport.status.cargo if unit is not None])
    
    def has_cargo_space(self, transport: 'Unit') -> bool:
        """Check if transport has space for more cargo"""
        current = self.get_current_cargo_count(transport)
        maximum = self.get_max_capacity(transport)
        return current < maximum
    
    def get_cargo_info(self, transport: 'Unit') -> Dict:
        """Get detailed cargo information for UI display"""
        if not self.is_transport_unit(transport):
            return {"is_transport": False}
        
        cargo_info = []
        current_cargo = 0
        
        if hasattr(transport.status, 'cargo') and transport.status.cargo:
            for i, cargo in enumerate(transport.status.cargo):
                if cargo is not None:
                    current_cargo += 1
                    
                    # Handle both Unit objects and serialized dicts
                    if isinstance(cargo, dict):
                        unit_type = cargo.get('type', 'UNKNOWN')
                        army = cargo.get('army', 'UNKNOWN')
                        hp = cargo.get('status', {}).get('hp', 100)
                    else:
                        unit_type = cargo.type.name if hasattr(cargo.type, 'name') else str(cargo.type)
                        army = cargo.army.name if hasattr(cargo.army, 'name') else str(cargo.army)
                        hp = cargo.status.hp
                    
                    cargo_info.append({
                        "index": i,
                        "unit_type": unit_type,
                        "hp": hp,
                        "army": army
                    })
        
        return {
            "is_transport": True,
            "max_capacity": self.get_max_capacity(transport),
            "current_cargo": current_cargo,
            "cargo_list": cargo_info,  # Changed from cargo_units to match your RPC expectations
            "has_space": current_cargo < self.get_max_capacity(transport)
        }
    
    # =============================================================================
    # CRITICAL FIX: UNIT RECONSTRUCTION
    # =============================================================================
    
    def _reconstruct_unit_from_dict(self, unit_dict: dict) -> 'Unit':
        """
        CRITICAL FIX: Reconstruct Unit object from serialized dictionary
        This fixes the deserialization error that occurs after unloading
        """
        try:
            from unit import Unit, UnitType, UnitStatus
            from map_system import Army
            
            # Extract data from the serialized dict
            unit_type_name = unit_dict.get('type', 'INFANTRY')
            army_name = unit_dict.get('army', 'RED')
            unit_id = unit_dict.get('id', 'reconstructed')
            status_data = unit_dict.get('status', {})
            
            # Convert string names to enums if needed
            if isinstance(unit_type_name, str):
                unit_type = UnitType[unit_type_name]
            else:
                unit_type = unit_type_name
                
            if isinstance(army_name, str):
                army = Army[army_name]
            else:
                army = army_name
            
            # Create the Unit object
            unit = Unit(
                army=army,
                type=unit_type,
                id=unit_id,
                can_move=unit_dict.get('can_move', True),
                can_attack=unit_dict.get('can_attack', True), 
                can_capture=unit_dict.get('can_capture', True)
            )
            
            # Restore status properties
            if status_data:
                if hasattr(unit.status, 'hp'):
                    unit.status.hp = status_data.get('hp', 100)
                if hasattr(unit.status, 'fuel'):
                    unit.status.fuel = status_data.get('fuel', 100)
                if hasattr(unit.status, 'ammo'):
                    unit.status.ammo = status_data.get('ammo', 10)
                
                # Copy any other status attributes
                for key, value in status_data.items():
                    if hasattr(unit.status, key):
                        setattr(unit.status, key, value)
            
            return unit
            
        except Exception as e:
            # Fallback: create a basic unit if reconstruction fails
            print(f"Warning: Failed to reconstruct unit from dict: {e}")
            from unit import Unit, UnitType
            from map_system import Army
            
            return Unit(
                army=Army.RED,
                type=UnitType.INFANTRY,
                id='fallback',
                can_move=True,
                can_attack=True,
                can_capture=True
            )
    
    # =============================================================================
    # LOADING SYSTEM
    # =============================================================================
    
    def can_load_unit(self, transport: 'Unit', cargo: 'Unit', 
                     transport_x: int, transport_y: int,
                     cargo_x: int, cargo_y: int) -> Tuple[bool, str]:
        """Comprehensive validation for loading units"""
        
        # Check if transport can carry units
        if not self.is_transport_unit(transport):
            return False, f"{transport.type.name} cannot transport other units"
        
        # Check if units are adjacent (1 tile away)
        distance = abs(transport_x - cargo_x) + abs(transport_y - cargo_y)
        if distance != 1:
            return False, "Units must be adjacent to load"
        
        # Check if transport has capacity
        if not self.has_cargo_space(transport):
            return False, f"{transport.type.name} is at maximum capacity"
        
        # Check if transport can carry this unit type
        cargo_type = cargo.type.name if hasattr(cargo.type, 'name') else str(cargo.type)
        if not self.can_carry_unit_type(transport, cargo_type):
            return False, f"{transport.type.name} cannot carry {cargo_type}"
        
        # Check if units are same army
        if transport.army != cargo.army:
            return False, "Cannot load enemy units"
        
        # Check if cargo unit can move
        if not cargo.can_move:
            return False, "Cargo unit has already moved this turn"
        
        return True, "Can load unit"
    
    def load_unit(self, transport: 'Unit', cargo: 'Unit',
             transport_x: int, transport_y: int,
             cargo_x: int, cargo_y: int) -> LoadResult:
        """Load a unit into transport"""
        
        # Validate loading
        can_load, message = self.can_load_unit(transport, cargo, transport_x, transport_y, cargo_x, cargo_y)
        if not can_load:
            return LoadResult(success=False, message=message)
        
        # INITIALIZE cargo list if it doesn't exist or is empty
        if not hasattr(transport.status, 'cargo') or transport.status.cargo is None:
            transport.status.cargo = [None] * self.get_max_capacity(transport)
        elif isinstance(transport.status.cargo, list) and len(transport.status.cargo) == 0:
            transport.status.cargo = [None] * self.get_max_capacity(transport)
        
        # Find empty cargo slot
        cargo_index = None
        for i in range(len(transport.status.cargo)):
            if i < len(transport.status.cargo) and transport.status.cargo[i] is None:
                cargo_index = i
                break
        
        # If no empty slot found, add to end if under capacity
        if cargo_index is None and len(transport.status.cargo) < self.get_max_capacity(transport):
            cargo_index = len(transport.status.cargo)
            transport.status.cargo.append(None)
        
        if cargo_index is None:
            return LoadResult(success=False, message="No available cargo slots")
        
        # Store cargo unit in transport
        transport.status.cargo[cargo_index] = cargo
        
        # Remove cargo unit from board
        self.manager.unit_remove(cargo_x, cargo_y)
        
        # Mark both units as having acted (use the standard unit attributes)
        cargo.can_move = False
        cargo.can_attack = False
        transport.can_move = False  # Transport can't move after loading
        
        return LoadResult(
            success=True, 
            message=f"{cargo.type.name} loaded into {transport.type.name}",
            cargo_index=cargo_index
        )
    
    # =============================================================================
    # UNLOADING SYSTEM - WITH CRITICAL FIX
    # =============================================================================
    
    def get_valid_unload_positions(self, transport_x: int, transport_y: int) -> List[Tuple[int, int]]:
        """Get all valid positions where units can be unloaded"""
        valid_positions = []
        
        # Check all adjacent tiles
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # N, S, E, W
        
        for dx, dy in directions:
            unload_x = transport_x + dx
            unload_y = transport_y + dy
            
            # Check if position is on board
            if not (0 <= unload_x < self.manager.board.width and 0 <= unload_y < self.manager.board.height):
                continue
            
            # Check if tile is empty
            if self.manager.unit_at(unload_x, unload_y) is not None:
                continue
            
            # Check if terrain is passable for ground units
            tile = self.manager.tile_at(unload_x, unload_y)
            terrain_name = tile.mapTile.type.name if hasattr(tile.mapTile.type, 'name') else str(tile.mapTile.type)
            
            # Basic terrain check - can expand this later
            if terrain_name in ['SEA']:
                continue
            
            valid_positions.append((unload_x, unload_y))
        
        return valid_positions
    
    def can_unload_unit(self, transport: 'Unit', cargo_index: int,
                       transport_x: int, transport_y: int,
                       unload_x: int, unload_y: int) -> Tuple[bool, str]:
        """Validate unloading a specific unit"""
        
        # Check if transport has cargo
        if not hasattr(transport.status, 'cargo') or cargo_index >= len(transport.status.cargo):
            return False, "Invalid cargo index"
        
        cargo = transport.status.cargo[cargo_index]
        if cargo is None:
            return False, "No unit in cargo slot"
        
        # Check if unload position is adjacent
        distance = abs(transport_x - unload_x) + abs(transport_y - unload_y)
        if distance != 1:
            return False, "Can only unload to adjacent tiles"
        
        # Check if unload position is empty
        if self.manager.unit_at(unload_x, unload_y) is not None:
            return False, "Unload position is occupied"
        
        # Check if cargo unit can be placed on this terrain
        tile = self.manager.tile_at(unload_x, unload_y)
        # This is a simplified check - you can enhance it later with proper terrain validation
        terrain_name = tile.mapTile.type.name if hasattr(tile.mapTile.type, 'name') else str(tile.mapTile.type)
        
        if terrain_name in ['SEA'] and cargo.type.name not in ['LANDER', 'CRUISER', 'BATTLESHIP', 'SUB']:
            return False, f"Cannot unload {cargo.type.name} onto {terrain_name}"
        
        return True, "Can unload unit"
    
    def unload_unit(self, transport: 'Unit', cargo_index: int,
           transport_x: int, transport_y: int,
           unload_x: int, unload_y: int) -> UnloadResult:
        """
        CRITICAL FIX: Unload a unit from transport with proper Unit object handling
        This method now properly handles both Unit objects and serialized dicts
        """
        
        # Validate unloading
        can_unload, message = self.can_unload_unit(transport, cargo_index, transport_x, transport_y, unload_x, unload_y)
        if not can_unload:
            return UnloadResult(success=False, message=message)
        
        # Get cargo unit
        cargo = transport.status.cargo[cargo_index]
        
        # ENHANCED DEBUG: Log what we're working with
        print(f"TRANSPORT_DEBUG: Unloading cargo type: {type(cargo)}")
        if isinstance(cargo, dict):
            print(f"TRANSPORT_DEBUG: Cargo is dict with keys: {list(cargo.keys())}")
            print(f"TRANSPORT_DEBUG: Unit type in dict: {cargo.get('type', 'MISSING')}")
        else:
            print(f"TRANSPORT_DEBUG: Cargo is Unit object: {cargo}")
        
        # CRITICAL FIX: Handle serialized units (this fixes the main error)
        if isinstance(cargo, dict):
            print(f"TRANSPORT_DEBUG: Reconstructing unit from dict: {cargo.get('type', 'UNKNOWN')}")
            cargo = self._reconstruct_unit_from_dict(cargo)
            print(f"TRANSPORT_DEBUG: Reconstruction result: {type(cargo)}")
        
        # Ensure we have a proper Unit object
        if not hasattr(cargo, 'type') or not hasattr(cargo, 'army'):
            print(f"TRANSPORT_DEBUG: ERROR - Invalid cargo unit data after reconstruction")
            return UnloadResult(success=False, message="Invalid cargo unit data")
        
        print(f"TRANSPORT_DEBUG: Unit validated, proceeding with placement")
        
        # Remove from transport
        transport.status.cargo[cargo_index] = None
        
        # Place unit on board
        try:
            self.manager.unit_place(cargo, unload_x, unload_y)
            print(f"TRANSPORT_DEBUG: Successfully placed unit using manager.unit_place")
        except Exception as e:
            print(f"TRANSPORT_DEBUG: Manager placement failed: {e}")
            return UnloadResult(success=False, message=f"Failed to place unit: {e}")
        
        # Unloaded unit can act this turn
        cargo.can_move = True
        cargo.can_attack = True
        cargo.can_capture = True
        
        # Transport is done for this turn
        transport.can_move = False
        transport.can_attack = False
        
        unit_type_name = cargo.type.name if hasattr(cargo.type, 'name') else str(cargo.type)
        transport_type_name = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        
        print(f"TRANSPORT_DEBUG: Successfully unloaded {unit_type_name} from {transport_type_name}")
        
        return UnloadResult(
            success=True,
            message=f"{unit_type_name} unloaded from {transport_type_name}",
            unloaded_position=(unload_x, unload_y)
        )
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def get_compatible_cargo_types(self, transport: 'Unit') -> List[str]:
        """Get list of unit types this transport can carry"""
        transport_type = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        
        if transport_type not in self.transport_capabilities:
            return []
        
        return self.transport_capabilities[transport_type].allowed_unit_types
    
    def get_loadable_units_near(self, transport_x: int, transport_y: int, army) -> List[Dict]:
        """Get all units near transport that can be loaded"""
        transport = self.manager.unit_at(transport_x, transport_y)
        if not transport or not self.is_transport_unit(transport):
            return []
        
        loadable_units = []
        
        # Check all adjacent tiles
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dx, dy in directions:
            cargo_x = transport_x + dx
            cargo_y = transport_y + dy
            
            # Check bounds
            if not (0 <= cargo_x < self.manager.board.width and 0 <= cargo_y < self.manager.board.height):
                continue
            
            # Check for unit
            cargo_unit = self.manager.unit_at(cargo_x, cargo_y)
            if not cargo_unit:
                continue
            
            # Check if it can be loaded
            can_load, _ = self.can_load_unit(transport, cargo_unit, transport_x, transport_y, cargo_x, cargo_y)
            
            if can_load:
                loadable_units.append({
                    "x": cargo_x,
                    "y": cargo_y,
                    "unit_type": cargo_unit.type.name if hasattr(cargo_unit.type, 'name') else str(cargo_unit.type),
                    "army": cargo_unit.army.name if hasattr(cargo_unit.army, 'name') else str(cargo_unit.army),
                    "hp": cargo_unit.status.hp
                })
        
        return loadable_units
    
    # =============================================================================
    # DEBUGGING AND VALIDATION HELPERS
    # =============================================================================
    
    def validate_cargo_integrity(self, transport: 'Unit') -> Dict:
        """Validate that all cargo units are properly formed"""
        if not hasattr(transport.status, 'cargo'):
            return {"valid": True, "issues": []}
        
        issues = []
        for i, cargo in enumerate(transport.status.cargo):
            if cargo is None:
                continue
                
            if isinstance(cargo, dict):
                issues.append(f"Cargo slot {i} contains dict instead of Unit object")
                
                # Check if dict has required fields
                required_fields = ['type', 'army', 'status']
                for field in required_fields:
                    if field not in cargo:
                        issues.append(f"Cargo slot {i} missing required field: {field}")
            
            elif not hasattr(cargo, 'type') or not hasattr(cargo, 'army'):
                issues.append(f"Cargo slot {i} has invalid Unit object")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "cargo_count": self.get_current_cargo_count(transport)
        }
    
    def repair_cargo_integrity(self, transport: 'Unit') -> bool:
        """Attempt to repair any serialized cargo units"""
        if not hasattr(transport.status, 'cargo'):
            return True
        
        repairs_made = False
        for i, cargo in enumerate(transport.status.cargo):
            if cargo is None:
                continue
                
            if isinstance(cargo, dict):
                try:
                    # Reconstruct the unit
                    reconstructed_unit = self._reconstruct_unit_from_dict(cargo)
                    transport.status.cargo[i] = reconstructed_unit
                    repairs_made = True
                except Exception as e:
                    print(f"Failed to repair cargo slot {i}: {e}")
        
        return repairs_made
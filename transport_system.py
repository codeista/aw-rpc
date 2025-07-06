"""
Enhanced Transport System for AW-RPC Phase 2B-1
Provides comprehensive transport mechanics including:
- Load/unload validation
- Capacity management  
- Transport compatibility
- Position validation
"""

from typing import Dict, List, Tuple, Optional, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

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
    """Enhanced transport system for Phase 2B-1"""
    
    def __init__(self, game_manager: 'GameManager'):
        self.manager = game_manager
        
        # Define transport capabilities for each unit type
        self.transport_capabilities = {
            'APC': TransportCapability(
                max_capacity=1,
                allowed_unit_types=['INFANTRY', 'MECH'],
                terrain_restrictions=[]  # Can go anywhere ground units can
            ),
            'LANDER': TransportCapability(
                max_capacity=2,
                allowed_unit_types=['INFANTRY', 'MECH', 'RECON', 'TANK', 'MEDIUMTANK', 'ANTIAIR', 'ARTILLERY', 'ROCKET', 'MISSILE', 'APC'],
                terrain_restrictions=['SEA', 'SHOAL', 'BEACH_N', 'BEACH_E', 'BEACH_S', 'BEACH_W', 'BEACH_NE', 'BEACH_NW', 'BEACH_SE', 'BEACH_SW']
            ),
            'TCOPTER': TransportCapability(
                max_capacity=1,
                allowed_unit_types=['INFANTRY'],
                terrain_restrictions=[]  # Can fly anywhere
            ),
            'BLACKBOAT': TransportCapability(
                max_capacity=2,
                allowed_unit_types=['INFANTRY', 'MECH'],
                terrain_restrictions=['SEA', 'SHOAL']
            )
        }
    
    # =============================================================================
    # TRANSPORT VALIDATION
    # =============================================================================
    
    def is_transport_unit(self, unit: 'Unit') -> bool:
        """Check if unit can transport other units"""
        unit_type = unit.type.name if hasattr(unit.type, 'name') else str(unit.type)
        return unit_type in self.transport_capabilities
    
    def can_carry_unit_type(self, transport: 'Unit', cargo_unit_type: str) -> bool:
        """Check if transport can carry this type of unit"""
        transport_type = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        
        if transport_type not in self.transport_capabilities:
            return False
        
        capability = self.transport_capabilities[transport_type]
        return cargo_unit_type in capability.allowed_unit_types
    
    def get_current_cargo_count(self, transport: 'Unit') -> int:
        """Get number of units currently in transport"""
        if not hasattr(transport.status, 'cargo'):
            return 0
        
        count = 0
        for cargo_slot in transport.status.cargo:
            if cargo_slot is not None:
                count += 1
        return count
    
    def get_max_capacity(self, transport: 'Unit') -> int:
        """Get maximum capacity for transport unit"""
        transport_type = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        
        if transport_type not in self.transport_capabilities:
            return 0
        
        return self.transport_capabilities[transport_type].max_capacity
    
    def has_cargo_space(self, transport: 'Unit') -> bool:
        """Check if transport has space for more cargo"""
        current = self.get_current_cargo_count(transport)
        maximum = self.get_max_capacity(transport)
        return current < maximum
    
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
        
        # Check if cargo unit can be loaded (not already in transport, can move, etc.)
        if hasattr(cargo.status, 'moved') and cargo.status.moved:
            return False, "Unit has already moved this turn"
        
        # Check if transport has already acted this turn
        if hasattr(transport.status, 'moved') and transport.status.moved:
            return False, "Transport has already moved this turn"
        
        return True, "Can load unit"
    
    def load_unit(self, transport: 'Unit', cargo: 'Unit',
                 transport_x: int, transport_y: int,
                 cargo_x: int, cargo_y: int) -> LoadResult:
        """Load a unit into transport"""
        
        # Validate loading
        can_load, message = self.can_load_unit(transport, cargo, transport_x, transport_y, cargo_x, cargo_y)
        if not can_load:
            return LoadResult(success=False, message=message)
        
        # Find empty cargo slot
        cargo_index = None
        for i, slot in enumerate(transport.status.cargo):
            if slot is None:
                cargo_index = i
                break
        
        if cargo_index is None:
            return LoadResult(success=False, message="No available cargo slots")
        
        # Store cargo unit in transport
        transport.status.cargo[cargo_index] = cargo
        
        # Remove cargo unit from board
        self.manager.unit_remove(cargo_x, cargo_y)
        
        # Mark transport as having acted
        if hasattr(transport.status, 'moved'):
            transport.status.moved = True
        
        return LoadResult(
            success=True, 
            message=f"{cargo.type.name} loaded into {transport.type.name}",
            cargo_index=cargo_index
        )
    
    # =============================================================================
    # UNLOADING SYSTEM
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
            
            # Check if terrain is passable for ground units (we'll make this more specific later)
            tile = self.manager.tile_at(unload_x, unload_y)
            if tile.mapTile.type.name in ['SEA']:  # Basic check - infantry can't be unloaded into sea
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
        
        # Check if unload position is valid
        valid_positions = self.get_valid_unload_positions(transport_x, transport_y)
        if (unload_x, unload_y) not in valid_positions:
            return False, "Cannot unload unit at this position"
        
        return True, "Can unload unit"
    
    def unload_unit(self, transport: 'Unit', cargo_index: int,
                   transport_x: int, transport_y: int,
                   unload_x: int, unload_y: int) -> UnloadResult:
        """Unload a unit from transport"""
        
        # Validate unloading
        can_unload, message = self.can_unload_unit(transport, cargo_index, transport_x, transport_y, unload_x, unload_y)
        if not can_unload:
            return UnloadResult(success=False, message=message)
        
        # Get cargo unit
        cargo = transport.status.cargo[cargo_index]
        
        # Remove from transport
        transport.status.cargo[cargo_index] = None
        
        # Place unit on board
        self.manager.unit_place(cargo, unload_x, unload_y)
        
        # Reset cargo unit status (can act this turn)
        if hasattr(cargo.status, 'moved'):
            cargo.status.moved = False
        if hasattr(cargo.status, 'attacked'):
            cargo.status.attacked = False
        
        # Mark transport as having acted
        if hasattr(transport.status, 'moved'):
            transport.status.moved = True
        
        return UnloadResult(
            success=True,
            message=f"{cargo.type.name} unloaded from {transport.type.name}",
            unloaded_position=(unload_x, unload_y)
        )
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def get_cargo_info(self, transport: 'Unit') -> Dict:
        """Get detailed cargo information for UI display"""
        if not self.is_transport_unit(transport):
            return {"is_transport": False}
        
        cargo_info = []
        if hasattr(transport.status, 'cargo'):
            for i, cargo in enumerate(transport.status.cargo):
                if cargo is not None:
                    cargo_info.append({
                        "index": i,
                        "unit_type": cargo.type.name if hasattr(cargo.type, 'name') else str(cargo.type),
                        "hp": cargo.status.hp,
                        "army": cargo.army.name if hasattr(cargo.army, 'name') else str(cargo.army)
                    })
        
        return {
            "is_transport": True,
            "max_capacity": self.get_max_capacity(transport),
            "current_cargo": len(cargo_info),
            "cargo_units": cargo_info,
            "has_space": self.has_cargo_space(transport)
        }
    
    def get_compatible_cargo_types(self, transport: 'Unit') -> List[str]:
        """Get list of unit types this transport can carry"""
        transport_type = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        
        if transport_type not in self.transport_capabilities:
            return []
        
        return self.transport_capabilities[transport_type].allowed_unit_types

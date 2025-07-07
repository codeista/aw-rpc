# transport_system.py - Complete transport mechanics for AW-RPC

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

@dataclass
class TransportResult:
    """Result of a transport operation"""
    success: bool
    message: str = ""
    cargo_index: int = -1
    unloaded_position: Optional[Tuple[int, int]] = None

@dataclass 
class TransportCapability:
    """Defines what a transport unit can carry"""
    max_capacity: int
    compatible_units: List[str]  # Unit type names
    terrain_restrictions: List[str] = None  # Terrain types where loading/unloading is restricted

class TransportSystem:
    """Complete transport system for AW-RPC"""
    
    def __init__(self, game_manager):
        self.game_manager = game_manager
        
        # Define transport capabilities for each unit type
        self.transport_capabilities = {
            'APC': TransportCapability(
                max_capacity=1,
                compatible_units=['INFANTRY', 'MECH']
            ),
            'LANDER': TransportCapability(
                max_capacity=2,
                compatible_units=['INFANTRY', 'MECH', 'RECON', 'TANK', 'MEDIUMTANK', 'NEOTANK', 'ARTILLERY', 'ROCKET', 'ANTIAIR', 'MISSILE'],
                terrain_restrictions=['SEA', 'BEACH_N', 'BEACH_S', 'BEACH_E', 'BEACH_W']
            ),
            'TCOPTER': TransportCapability(
                max_capacity=1,
                compatible_units=['INFANTRY', 'MECH']
            ),
            'CRUISER': TransportCapability(
                max_capacity=2,
                compatible_units=['BCOPTER', 'TCOPTER']
            ),
            'CARRIER': TransportCapability(
                max_capacity=2,
                compatible_units=['FIGHTER', 'BOMBER']
            ),
            'BLACKBOAT': TransportCapability(
                max_capacity=1,
                compatible_units=['INFANTRY', 'MECH']
            )
        }
    
    def is_transport_unit(self, unit) -> bool:
        """Check if unit can transport other units"""
        if not unit or not hasattr(unit, 'type'):
            return False
        unit_type = unit.type.name if hasattr(unit.type, 'name') else str(unit.type)
        return unit_type in self.transport_capabilities
    
    def get_max_capacity(self, transport) -> int:
        """Get maximum cargo capacity for transport unit - with debugging"""
        transport_type = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        
        capacity_map = {
            'APC': 1,
            'LANDER': 2, 
            'TCOPTER': 1,
            'CRUISER': 2,
            'CARRIER': 2,
            'BLACKBOAT': 1
        }
        
        capacity = capacity_map.get(transport_type, 0)
        print(f"DEBUG: get_max_capacity for {transport_type}: {capacity}")
        return capacity
    
    # def get_max_capacity(self, transport) -> int:
    #     """Get maximum cargo capacity for transport"""
    #     if not self.is_transport_unit(transport):
    #         return 0
    #     transport_type = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
    #     return self.transport_capabilities[transport_type].max_capacity
    
    def get_compatible_cargo_types(self, transport) -> List[str]:
        """Get list of unit types this transport can carry"""
        if not self.is_transport_unit(transport):
            return []
        transport_type = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        return self.transport_capabilities[transport_type].compatible_units
    
    def has_cargo_space(self, transport) -> bool:
        """Check if transport has available cargo space"""
        if not hasattr(transport.status, 'cargo') or transport.status.cargo is None:
            return True
        
        max_capacity = self.get_max_capacity(transport)
        current_cargo = sum(1 for slot in transport.status.cargo if slot is not None)
        return current_cargo < max_capacity
    
    def get_cargo_count(self, transport) -> int:
        """Get current number of units in cargo"""
        if not hasattr(transport.status, 'cargo') or transport.status.cargo is None:
            return 0
        return sum(1 for slot in transport.status.cargo if slot is not None)
    
    def can_load_unit(self, transport, cargo, transport_x: int, transport_y: int, cargo_x: int, cargo_y: int) -> Tuple[bool, str]:
        """Check if cargo unit can be loaded into transport"""
        
        # Basic validation
        if not transport or not cargo:
            return False, "Missing transport or cargo unit"
        
        # Check if transport can carry units
        if not self.is_transport_unit(transport):
            return False, f"{transport.type.name} cannot transport other units"
        
        # Check army ownership
        if transport.army != cargo.army:
            return False, "Cannot load enemy units"
        
        # Check adjacency (units must be next to each other)
        distance = abs(transport_x - cargo_x) + abs(transport_y - cargo_y)
        if distance != 1:
            return False, "Units must be adjacent to load"
        
        # Check if transport has capacity
        if not self.has_cargo_space(transport):
            return False, "Transport is at full capacity"
        
        # Check unit compatibility
        transport_type = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        cargo_type = cargo.type.name if hasattr(cargo.type, 'name') else str(cargo.type)
        
        compatible_types = self.get_compatible_cargo_types(transport)
        if cargo_type not in compatible_types:
            return False, f"{transport_type} cannot carry {cargo_type}"
        
        return True, "Unit can be loaded"
    
# PRODUCTION VERSION - Clean transport_system.py load_unit method
# Replace your current load_unit method with this clean version

    def load_unit(self, transport, cargo, transport_x: int, transport_y: int, cargo_x: int, cargo_y: int) -> TransportResult:
        """Load cargo unit into transport"""
        
        # Validate the operation
        can_load, message = self.can_load_unit(transport, cargo, transport_x, transport_y, cargo_x, cargo_y)
        if not can_load:
            return TransportResult(False, message)
        
        try:
            # Ensure cargo array exists and has correct structure
            max_capacity = self.get_max_capacity(transport)
            
            # Initialize or fix cargo array if needed
            if (not hasattr(transport.status, 'cargo') or 
                transport.status.cargo is None or 
                not isinstance(transport.status.cargo, list) or 
                len(transport.status.cargo) != max_capacity):
                
                # Preserve existing cargo if any
                old_cargo = []
                if (hasattr(transport.status, 'cargo') and 
                    isinstance(transport.status.cargo, list)):
                    old_cargo = list(transport.status.cargo)
                
                # Create new cargo array
                transport.status.cargo = [None] * max_capacity
                
                # Restore valid cargo units
                for i, item in enumerate(old_cargo[:max_capacity]):
                    if item is not None:
                        transport.status.cargo[i] = item
            
            # Find first available cargo slot
            cargo_index = -1
            for i, slot in enumerate(transport.status.cargo):
                if slot is None:
                    cargo_index = i
                    break
            
            if cargo_index == -1:
                return TransportResult(False, "No available cargo slots", cargo_index=-1)
            
            # Store the cargo unit
            transport.status.cargo[cargo_index] = cargo
            
            # Remove cargo unit from the board
            cargo_tile = self.game_manager.tile_at(cargo_x, cargo_y)
            if cargo_tile:
                cargo_tile.unit = None
            
            return TransportResult(
                success=True,
                message=f"{cargo.type.name} loaded into {transport.type.name}",
                cargo_index=cargo_index
            )
            
        except Exception as e:
            return TransportResult(False, f"Loading failed: {str(e)}")

    def get_valid_unload_positions(self, transport_x: int, transport_y: int) -> List[Tuple[int, int]]:
        """Get valid positions where units can be unloaded"""
        valid_positions = []
        
        # Check all adjacent tiles
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # N, S, E, W
        
        for dx, dy in directions:
            unload_x = transport_x + dx
            unload_y = transport_y + dy
            
            # Check if position is on board
            if not (0 <= unload_x < self.game_manager.board.width and 0 <= unload_y < self.game_manager.board.height):
                continue
            
            # Check if tile is empty
            tile = self.game_manager.tile_at(unload_x, unload_y)
            if tile and tile.unit is None:
                valid_positions.append((unload_x, unload_y))
        
        return valid_positions
    
    def can_unload_unit(self, transport, cargo_index: int, transport_x: int, transport_y: int, unload_x: int, unload_y: int) -> Tuple[bool, str]:
        """Check if unit can be unloaded at specific position"""
        
        # Check if transport has cargo
        if not hasattr(transport.status, 'cargo') or transport.status.cargo is None:
            return False, "Transport has no cargo"
        
        # Check cargo index validity
        if cargo_index < 0 or cargo_index >= len(transport.status.cargo):
            return False, "Invalid cargo index"
        
        # Check if cargo slot has a unit
        if transport.status.cargo[cargo_index] is None:
            return False, "No unit in specified cargo slot"
        
        # Check adjacency
        distance = abs(transport_x - unload_x) + abs(transport_y - unload_y)
        if distance != 1:
            return False, "Can only unload to adjacent tiles"
        
        # Check if unload position is empty
        unload_tile = self.game_manager.tile_at(unload_x, unload_y)
        if unload_tile and unload_tile.unit is not None:
            return False, "Unload position is occupied"
        
        return True, "Unit can be unloaded"
    
    def unload_unit(self, transport, cargo_index: int, transport_x: int, transport_y: int, unload_x: int, unload_y: int) -> TransportResult:
        """Unload unit from transport to specified position"""
        
        # Validate the operation
        can_unload, message = self.can_unload_unit(transport, cargo_index, transport_x, transport_y, unload_x, unload_y)
        if not can_unload:
            return TransportResult(False, message)
        
        try:
            # Get the cargo unit
            cargo_unit = transport.status.cargo[cargo_index]
            
            # Place unit on the board
            unload_tile = self.game_manager.tile_at(unload_x, unload_y)
            if unload_tile:
                unload_tile.unit = cargo_unit
                
                # Remove from cargo
                transport.status.cargo[cargo_index] = None
                
                return TransportResult(
                    success=True,
                    message=f"{cargo_unit.type.name} unloaded from {transport.type.name}",
                    unloaded_position=(unload_x, unload_y)
                )
            else:
                return TransportResult(False, "Invalid unload position")
                
        except Exception as e:
            return TransportResult(False, f"Unloading failed: {str(e)}")
    
    def get_cargo_info(self, unit) -> Dict:
        """Get detailed cargo information for a unit"""
        info = {
            "is_transport": self.is_transport_unit(unit),
            "max_capacity": 0,
            "current_cargo": 0,
            "cargo_units": [],
            "compatible_types": []
        }
        
        if self.is_transport_unit(unit):
            info["max_capacity"] = self.get_max_capacity(unit)
            info["current_cargo"] = self.get_cargo_count(unit)
            info["compatible_types"] = self.get_compatible_cargo_types(unit)
            
            # Get cargo unit details
            if hasattr(unit.status, 'cargo') and unit.status.cargo:
                for i, cargo_unit in enumerate(unit.status.cargo):
                    if cargo_unit:
                        info["cargo_units"].append({
                            "index": i,
                            "type": cargo_unit.type.name if hasattr(cargo_unit.type, 'name') else str(cargo_unit.type),
                            "army": cargo_unit.army.name if hasattr(cargo_unit.army, 'name') else str(cargo_unit.army),
                            "hp": cargo_unit.status.hp
                        })
        
        return info
    
    def get_loadable_transports_near(self, cargo_x: int, cargo_y: int) -> List[Dict]:
        """Get all transport units that can load the cargo unit at specified position"""
        cargo_unit = self.game_manager.unit_at(cargo_x, cargo_y)
        if not cargo_unit:
            return []
        
        loadable_transports = []
        
        # Check all adjacent tiles for friendly transports
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dx, dy in directions:
            transport_x = cargo_x + dx
            transport_y = cargo_y + dy
            
            # Check bounds
            if not (0 <= transport_x < self.game_manager.board.width and 0 <= transport_y < self.game_manager.board.height):
                continue
            
            transport = self.game_manager.unit_at(transport_x, transport_y)
            if not transport:
                continue
            
            # Check if it can load this cargo
            can_load, message = self.can_load_unit(transport, cargo_unit, transport_x, transport_y, cargo_x, cargo_y)
            if can_load:
                loadable_transports.append({
                    "x": transport_x,
                    "y": transport_y,
                    "transport_type": transport.type.name if hasattr(transport.type, 'name') else str(transport.type),
                    "current_cargo": self.get_cargo_count(transport),
                    "max_capacity": self.get_max_capacity(transport)
                })
        
        return loadable_transports
    
    def cargo_move_into_transport(self, cargo, transport, cargo_x: int, cargo_y: int, transport_x: int, transport_y: int) -> TransportResult:
        """Advance Wars style: cargo unit moves into transport"""
        return self.load_unit(transport, cargo, transport_x, transport_y, cargo_x, cargo_y)
    
    def cargo_exit_transport(self, transport, cargo_index: int, transport_x: int, transport_y: int, exit_x: int, exit_y: int) -> TransportResult:
        """Advance Wars style: cargo unit exits transport"""
        return self.unload_unit(transport, cargo_index, transport_x, transport_y, exit_x, exit_y)
    
    def get_valid_exit_positions(self, transport_x: int, transport_y: int) -> List[Tuple[int, int]]:
        """Get valid positions where cargo can exit (same as unload positions)"""
        return self.get_valid_unload_positions(transport_x, transport_y)
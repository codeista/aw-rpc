# transport_system.py - Enhanced transport mechanics for AW-RPC

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
    repair_cost: int = 0

@dataclass 
class TransportCapability:
    """Defines what a transport unit can carry"""
    max_capacity: int
    compatible_units: List[str]
    loading_terrain: List[str] = None  # Terrain where loading is allowed
    can_resupply: bool = False
    can_repair: bool = False
    auto_resupply_cargo: bool = False

class CompleteTransportSystem:
    """Complete transport system with all AW mechanics"""
    
    def __init__(self, game_manager):
        self.game_manager = game_manager
        
        # Define all transport capabilities
        self.transport_capabilities = {
            'APC': TransportCapability(
                max_capacity=1,
                compatible_units=['INFANTRY', 'MECH'],
                loading_terrain=['PLAIN', 'ROAD', 'BRIDGE', 'FOREST', 'MOUNTAIN', 'FACTORY', 'CITY', 'HQ', 'BEACH_N', 'BEACH_S', 'BEACH_E', 'BEACH_W'],
                can_resupply=True,
                can_repair=False,
                auto_resupply_cargo=False
            ),
            'TCOPTER': TransportCapability(
                max_capacity=1,
                compatible_units=['INFANTRY', 'MECH'],
                loading_terrain=None,  # Can load anywhere (air unit)
                can_resupply=False,
                can_repair=False,
                auto_resupply_cargo=False
            ),
            'LANDER': TransportCapability(
                max_capacity=2,
                compatible_units=['INFANTRY', 'MECH', 'RECON', 'TANK', 'MEDIUMTANK', 
                                'NEOTANK', 'ARTILLERY', 'ROCKET', 'ANTIAIR', 'MISSILE'],
                loading_terrain=['BEACH_N', 'BEACH_S', 'BEACH_E', 'BEACH_W', 'PORT'],
                can_resupply=False,
                can_repair=False,
                auto_resupply_cargo=False
            ),
            'BLACKBOAT': TransportCapability(
                max_capacity=2,
                compatible_units=['INFANTRY', 'MECH'],
                loading_terrain=['BEACH_N', 'BEACH_S', 'BEACH_E', 'BEACH_W', 'PORT'],
                can_resupply=True,
                can_repair=True,
                auto_resupply_cargo=False
            ),
            'CRUISER': TransportCapability(
                max_capacity=2,
                compatible_units=['BCOPTER', 'TCOPTER'],
                loading_terrain=None,  # Can load anywhere at sea
                can_resupply=True,
                can_repair=False,
                auto_resupply_cargo=True
            ),
            'CARRIER': TransportCapability(
                max_capacity=2,
                compatible_units=['FIGHTER', 'BOMBER', 'STEALTH'],
                loading_terrain=None,  # Can load anywhere at sea
                can_resupply=True,
                can_repair=False,
                auto_resupply_cargo=True
            )
        }
    
    def is_transport_unit(self, unit) -> bool:
        """Check if unit can transport other units"""
        if not unit or not hasattr(unit, 'type'):
            return False
        unit_type = unit.type.name if hasattr(unit.type, 'name') else str(unit.type)
        return unit_type in self.transport_capabilities
    
    def get_transport_capability(self, unit):
        """Get transport capability for a unit"""
        if not self.is_transport_unit(unit):
            return None
        unit_type = unit.type.name if hasattr(unit.type, 'name') else str(unit.type)
        return self.transport_capabilities.get(unit_type)
    
    def can_load_on_terrain(self, transport, transport_x: int, transport_y: int) -> bool:
        """Check if transport can load on current terrain"""
        capability = self.get_transport_capability(transport)
        
        if not capability or not capability.loading_terrain:
            return True  # No terrain restrictions (for sea units like CRUISER/CARRIER)
        
        tile = self.game_manager.tile_at(transport_x, transport_y)
        terrain_type = tile.mapTile.type.name if hasattr(tile.mapTile.type, 'name') else str(tile.mapTile.type)
        
        return terrain_type in capability.loading_terrain
    
    def can_load_unit(self, transport, cargo, transport_x: int, transport_y: int, 
                     cargo_x: int, cargo_y: int) -> Tuple[bool, str]:
        """Check if transport can load this cargo unit"""
        
        # Basic validation
        if not self.is_transport_unit(transport):
            return False, "Unit is not a transport"
        
        capability = self.get_transport_capability(transport)
        if not capability:
            return False, "Unknown transport type"
        
        # Check unit compatibility
        cargo_type = cargo.type.name if hasattr(cargo.type, 'name') else str(cargo.type)
        if cargo_type not in capability.compatible_units:
            return False, f"Cannot carry {cargo_type} units"
        
        # Check terrain restrictions for transport location
        if not self.can_load_on_terrain(transport, transport_x, transport_y):
            terrain_names = ", ".join(capability.loading_terrain) if capability.loading_terrain else "any"
            return False, f"Transport must be on {terrain_names} terrain to load"
        
        # Special case: Aircraft carriers and cruisers can load from adjacent tiles
        transport_type = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        if transport_type in ['CRUISER', 'CARRIER']:
            # Aircraft can be loaded from any adjacent tile
            distance = abs(transport_x - cargo_x) + abs(transport_y - cargo_y)
            if distance != 1:
                return False, "Aircraft must be adjacent to carrier/cruiser to load"
            
            # Special restriction: TCOPTERS can only be loaded from land tiles or beaches
            if cargo_type == 'TCOPTER':
                cargo_tile = self.game_manager.tile_at(cargo_x, cargo_y)
                cargo_terrain = cargo_tile.mapTile.type.name if hasattr(cargo_tile.mapTile.type, 'name') else str(cargo_tile.mapTile.type)
                
                # TCOPTER must be on land or beach (not sea)
                sea_terrains = ['SEA', 'OCEAN', 'SHOAL']
                if cargo_terrain in sea_terrains:
                    return False, f"TCOPTER can only be loaded from land tiles or beaches, not from {cargo_terrain}"
        else:
            # Land/sea transports: cargo must be adjacent or same tile
            distance = abs(transport_x - cargo_x) + abs(transport_y - cargo_y)
            if distance > 1:
                return False, "Must be adjacent to load"
            
            # For non-aircraft carriers, check cargo terrain restrictions
            if distance == 1:
                cargo_tile = self.game_manager.tile_at(cargo_x, cargo_y)
                cargo_terrain = cargo_tile.mapTile.type.name if hasattr(cargo_tile.mapTile.type, 'name') else str(cargo_tile.mapTile.type)
                
                # Land units can't load from deep sea
                if cargo_type in ['INFANTRY', 'MECH', 'RECON', 'TANK', 'MEDIUMTANK', 'NEOTANK', 'ARTILLERY', 'ROCKET', 'ANTIAIR', 'MISSILE']:
                    if cargo_terrain in ['SEA', 'OCEAN']:
                        return False, f"{cargo_type} cannot load from {cargo_terrain}"
        
        # Check capacity
        current_cargo = self.get_cargo_count(transport)
        if current_cargo >= capability.max_capacity:
            return False, f"Transport is full ({current_cargo}/{capability.max_capacity})"
        
        # Check armies
        if transport.army != cargo.army:
            return False, "Cannot load enemy units"
        
        return True, "Can load unit"
    
    def load_unit_enhanced(self, transport, cargo, transport_x: int, transport_y: int, 
                          cargo_x: int, cargo_y: int) -> TransportResult:
        """Enhanced loading with terrain restrictions and auto-resupply"""
        
        # Validate loading
        can_load, message = self.can_load_unit(transport, cargo, transport_x, transport_y, cargo_x, cargo_y)
        if not can_load:
            return TransportResult(False, message)
        
        try:
            # Initialize cargo array if needed
            capability = self.get_transport_capability(transport)
            max_capacity = capability.max_capacity
            
            if (not hasattr(transport.status, 'cargo') or 
                transport.status.cargo is None or 
                not isinstance(transport.status.cargo, list) or 
                len(transport.status.cargo) != max_capacity):
                transport.status.cargo = [None] * max_capacity
            
            # Find first available cargo slot
            cargo_index = -1
            for i, slot in enumerate(transport.status.cargo):
                if slot is None:
                    cargo_index = i
                    break
            
            if cargo_index == -1:
                return TransportResult(False, "No available cargo slots")
            
            # Auto-resupply cargo if transport supports it
            if capability and capability.auto_resupply_cargo:
                self.game_manager.resupply_unit(cargo)
            
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
    
    def can_unload_unit(self, transport, cargo_index: int, transport_x: int, transport_y: int, 
                       unload_x: int, unload_y: int) -> Tuple[bool, str]:
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
    
    def unload_unit_enhanced(self, transport, cargo_index: int, transport_x: int, transport_y: int, 
                           unload_x: int, unload_y: int) -> TransportResult:
        """Enhanced unloading - cargo cannot act after unloading"""
        
        # Validate the operation
        can_unload, message = self.can_unload_unit(transport, cargo_index, transport_x, transport_y, unload_x, unload_y)
        if not can_unload:
            return TransportResult(False, message)
        
        try:
            # Get the cargo unit
            cargo_unit = transport.status.cargo[cargo_index]
            
            # Place unit on unload position
            unload_tile = self.game_manager.tile_at(unload_x, unload_y)
            unload_tile.unit = cargo_unit
            
            # CRITICAL: Unloaded units cannot act this turn
            cargo_unit.can_move = False
            cargo_unit.can_attack = False
            cargo_unit.can_capture = False
            
            # Remove from transport cargo
            transport.status.cargo[cargo_index] = None
            
            return TransportResult(
                success=True,
                message=f"{cargo_unit.type.name} unloaded and cannot act this turn",
                unloaded_position=(unload_x, unload_y)
            )
            
        except Exception as e:
            return TransportResult(False, f"Unloading failed: {str(e)}")
    
    def get_cargo_count(self, transport) -> int:
        """Get number of units currently in transport"""
        if not hasattr(transport.status, 'cargo') or not transport.status.cargo:
            return 0
        return sum(1 for unit in transport.status.cargo if unit is not None)
    
    def get_max_capacity(self, transport) -> int:
        """Get maximum capacity of transport"""
        capability = self.get_transport_capability(transport)
        return capability.max_capacity if capability else 0
    
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
            capability = self.get_transport_capability(unit)
            info["max_capacity"] = capability.max_capacity
            info["current_cargo"] = self.get_cargo_count(unit)
            info["compatible_types"] = capability.compatible_units
            
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
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
    """Complete transport system implementing all Advance Wars transport mechanics.
    
    Transport types and their capabilities:
    - APC: Carries 1 Infantry/Mech, auto-resupplies adjacent units at turn start
    - T-Copter: Carries 1 Infantry/Mech, air transport
    - Lander: Carries 2 ground units, loads/unloads at beaches
    - Black Boat: Carries 2 Infantry/Mech, can repair adjacent units (manual, 2HP max)
    - Cruiser: Carries 2 helicopters, auto-resupplies cargo at turn start
    - Carrier: Carries 2 planes, auto-resupplies cargo at turn start
    
    Key mechanics:
    - Units move INTO transports to board (not transport picking them up)
    - Unloaded units cannot act on the same turn
    - Transport cannot move after unloading (but CAN unload after moving)
    - Transports can unload multiple units in the same turn
    - Some transports have terrain restrictions for loading
    - Auto-resupply happens at turn start for specific transports
    """
    
    def __init__(self, game_manager):
        self.game_manager = game_manager
        
        # Define all transport capabilities
        self.transport_capabilities = {
            'APC': TransportCapability(
                max_capacity=1,
                compatible_units=['INFANTRY', 'MECH'],
                loading_terrain=['PLAIN', 'ROAD', 'ROAD_HORT', 'ROAD_VERT', 'BRIDGE', 'FOREST', 'MOUNTAIN', 'FACTORY', 'CITY', 'HQ', 'BEACH_N', 'BEACH_S', 'BEACH_E', 'BEACH_W', 'BASE_TOWER_1', 'BASE_TOWER_2', 'BASE_TOWER_3', 'BASE_TOWER_4'],
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
                compatible_units=['FIGHTER', 'BOMBER', 'STEALTH', 'BCOPTER', 'TCOPTER', 'BLACKBOMB'],
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
        
        # Check Carrier/Cruiser attack+unload restriction
        transport_type = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        if transport_type in ['CARRIER', 'CRUISER']:
            # Check if the transport has attacked this turn
            if hasattr(transport, 'has_attacked') and transport.has_attacked:
                return False, f"{transport_type} cannot unload after attacking"
        
        # CRITICAL FIX: Check transport positioning requirements for unloading
        transport_tile = self.game_manager.tile_at(transport_x, transport_y)
        transport_type = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        
        if transport_type == 'LANDER':
            # Landers can only unload when on beach or port tiles
            transport_terrain = transport_tile.mapTile.type.name if hasattr(transport_tile.mapTile.type, 'name') else str(transport_tile.mapTile.type)
            allowed_lander_terrains = ['BEACH_N', 'BEACH_S', 'BEACH_E', 'BEACH_W', 'PORT']
            
            if transport_terrain not in allowed_lander_terrains:
                return False, f"Lander must be on beach or port to unload (currently on {transport_terrain})"
        
        elif transport_type == 'BLACKBOAT':
            # Black boats (like landers) can only unload when on beach or port tiles
            transport_terrain = transport_tile.mapTile.type.name if hasattr(transport_tile.mapTile.type, 'name') else str(transport_tile.mapTile.type)
            allowed_blackboat_terrains = ['BEACH_N', 'BEACH_S', 'BEACH_E', 'BEACH_W', 'PORT']
            
            if transport_terrain not in allowed_blackboat_terrains:
                return False, f"Black Boat must be on beach or port to unload (currently on {transport_terrain})"
        
        # Check if cargo unit can traverse destination terrain
        cargo_unit = transport.status.cargo[cargo_index]
        if unload_tile:
            try:
                from core.map_system import get_movement_cost, INF
                terrain_type = unload_tile.mapTile.type
                movement_cost = get_movement_cost(cargo_unit.status.cls, terrain_type)
                
                if movement_cost == INF:
                    return False, f"{cargo_unit.type.name} cannot traverse {terrain_type.name} terrain"
            except (KeyError, IndexError, AttributeError) as e:
                return False, f"Unable to validate terrain compatibility for {cargo_unit.type.name}: {e}"
        
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
            
            # CRITICAL: Ensure cargo array cleanup
            # Remove all None values and compact the array
            transport.status.cargo = [unit for unit in transport.status.cargo if unit is not None]
            
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
    
    def get_valid_unload_positions(self, transport_x: int, transport_y: int) -> List[Tuple[int, int]]:
        """Get all valid positions where transport cargo can be unloaded"""
        valid_positions = []
        
        # Check all adjacent tiles (N, S, E, W)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dx, dy in directions:
            unload_x = transport_x + dx
            unload_y = transport_y + dy
            
            # Check if position is on the board
            if not (0 <= unload_x < self.game_manager.board.width and 
                    0 <= unload_y < self.game_manager.board.height):
                continue
            
            # Check if position is empty
            unload_tile = self.game_manager.tile_at(unload_x, unload_y)
            if unload_tile and unload_tile.unit is None:
                valid_positions.append((unload_x, unload_y))
        
        return valid_positions

    def get_valid_exit_positions(self, transport_x: int, transport_y: int) -> List[Tuple[int, int]]:
        """Alias for get_valid_unload_positions (for compatibility)"""
        return self.get_valid_unload_positions(transport_x, transport_y)
    
# Add these methods to your CompleteTransportSystem class in transport_system.py
# Place them after the existing methods (around the end of the class)

    def cargo_move_into_transport(self, cargo, transport, cargo_x: int, cargo_y: int, 
                                transport_x: int, transport_y: int) -> TransportResult:
        """
        Handle cargo unit moving into transport (Advance Wars style)
        This is an alias for load_unit_enhanced with parameter reordering
        """
        return self.load_unit_enhanced(transport, cargo, transport_x, transport_y, cargo_x, cargo_y)

    def get_compatible_cargo_types(self, transport) -> List[str]:
        """Get list of unit types that can be loaded into this transport"""
        if not self.is_transport_unit(transport):
            return []
        
        capability = self.get_transport_capability(transport)
        if not capability:
            return []
        
        return capability.compatible_units.copy()

    def get_loadable_transports_near(self, cargo_x: int, cargo_y: int) -> List[Dict]:
        """Get all friendly transports near a cargo unit that can load it"""
        loadable_transports = []
        # Get the cargo unit
        cargo_tile = self.game_manager.tile_at(cargo_x, cargo_y)
        if not cargo_tile or not cargo_tile.unit:
            return loadable_transports
        
        cargo_unit = cargo_tile.unit
        
        # Check all adjacent tiles for compatible transports
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # N, S, E, W
        
        for dx, dy in directions:
            transport_x = cargo_x + dx
            transport_y = cargo_y + dy
            # Check if position is on board
            if not (0 <= transport_x < self.game_manager.board.width and 
                    0 <= transport_y < self.game_manager.board.height):
                continue
            
            # Check if there's a transport there
            transport_tile = self.game_manager.tile_at(transport_x, transport_y)
            if not transport_tile or not transport_tile.unit:
                continue
            
            transport_unit = transport_tile.unit
            
            # Check if it's a friendly transport that can load this cargo
            if (self.is_transport_unit(transport_unit) and 
                transport_unit.army == cargo_unit.army):
                
                can_load, message = self.can_load_unit(
                    transport_unit, cargo_unit, transport_x, transport_y, cargo_x, cargo_y
                )
                
                if can_load:
                    cargo_info = self.get_cargo_info(transport_unit)
                    loadable_transports.append({
                        "x": transport_x,
                        "y": transport_y,
                        "unit_type": transport_unit.type.name if hasattr(transport_unit.type, 'name') else str(transport_unit.type),
                        "army": transport_unit.army.name if hasattr(transport_unit.army, 'name') else str(transport_unit.army),
                        "cargo_info": cargo_info,
                        "can_load_message": message
                    })
        
        return loadable_transports

    def can_cargo_exit_transport(self, transport, cargo_index: int, transport_x: int, transport_y: int,
                            exit_x: int, exit_y: int) -> Tuple[bool, str]:
        """
        Check if cargo can exit transport at specific position
        This is an alias for can_unload_unit
        """
        return self.can_unload_unit(transport, cargo_index, transport_x, transport_y, exit_x, exit_y)

    def cargo_exit_transport(self, transport, cargo_index: int, transport_x: int, transport_y: int,
                            exit_x: int, exit_y: int) -> TransportResult:
        """
        Handle cargo exiting transport (Advance Wars style)
        This is an alias for unload_unit_enhanced
        """
        return self.unload_unit_enhanced(transport, cargo_index, transport_x, transport_y, exit_x, exit_y)
    
TransportSystem = CompleteTransportSystem
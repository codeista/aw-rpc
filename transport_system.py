# transport_system.py - Advance Wars Style Transport Mechanics

"""
Advance Wars Style Transport System
- Cargo units move INTO transports (not the other way around)
- Cargo units unload themselves FROM transports
- Matches original Advance Wars gameplay exactly
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
    """Advance Wars style transport system - cargo units move into transports"""
    
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
    # UNIT RECONSTRUCTION - SERIALIZATION FIX
    # =============================================================================
    
    def _reconstruct_unit_from_dict(self, unit_dict: dict) -> 'Unit':
        """Properly reconstruct Unit objects from serialized dictionaries"""
        try:
            from unit import Unit, UnitType, UnitConfig, UnitClass
            from map_system import Army
            import uuid
            
            print(f"TRANSPORT_FIX: Reconstructing unit from dict: {unit_dict.get('type', 'UNKNOWN')}")
            
            # Extract basic unit data with safe defaults
            unit_type_name = unit_dict.get('type', 'INFANTRY')
            army_name = unit_dict.get('army', 'RED')
            unit_id = unit_dict.get('id', str(uuid.uuid4()))
            
            # Convert string type to UnitType enum
            try:
                unit_type = UnitType[unit_type_name]
            except KeyError:
                print(f"TRANSPORT_FIX: Unknown unit type {unit_type_name}, defaulting to INFANTRY")
                unit_type = UnitType.INFANTRY
            
            # Convert string army to Army enum  
            try:
                army = Army[army_name]
            except (KeyError, AttributeError):
                print(f"TRANSPORT_FIX: Unknown army {army_name}, defaulting to RED")
                army = Army.RED
            
            # Create proper UnitConfig from status data
            status_data = unit_dict.get('status', {})
            
            # Get unit class safely
            unit_class_name = status_data.get('cls', 'FOOT')
            try:
                unit_class = UnitClass[unit_class_name]
            except (KeyError, AttributeError):
                unit_class = UnitClass.FOOT
            
            # Create unit config with proper defaults
            unit_config = UnitConfig(
                cls=unit_class,
                cost=status_data.get('cost', 1000),
                move=status_data.get('move', 3),
                rangemin=status_data.get('rangemin', 1),
                rangemax=status_data.get('rangemax', 1),
                fuel=status_data.get('fuel', 99),
                vision=status_data.get('vision', 2),
                hp=status_data.get('hp', 100),
                ammo=status_data.get('ammo', 99),
                cargo=status_data.get('cargo', [])
            )
            
            # Create the unit with proper action flags
            unit = Unit(
                army=army,
                type=unit_type,
                status=unit_config,
                id=unit_id,
                can_move=unit_dict.get('can_move', True),
                can_attack=unit_dict.get('can_attack', True), 
                can_capture=unit_dict.get('can_capture', True)
            )
            
            print(f"TRANSPORT_FIX: Successfully reconstructed {unit_type_name} unit")
            return unit
            
        except Exception as e:
            print(f"TRANSPORT_FIX: Reconstruction failed: {e}")
            # Create minimal fallback unit
            from unit import Unit, UnitType, UnitConfig, UnitClass
            from map_system import Army
            
            fallback_config = UnitConfig(
                cls=UnitClass.FOOT,
                cost=1000,
                move=3,
                rangemin=1,
                rangemax=1,
                fuel=99,
                vision=2,
                hp=100,
                ammo=99,
                cargo=[]
            )
            
            return Unit(
                army=Army.RED,
                type=UnitType.INFANTRY,
                status=fallback_config,
                id='fallback',
                can_move=True,
                can_attack=True,
                can_capture=True
            )
    
    # =============================================================================
    # TRANSPORT UNIT IDENTIFICATION
    # =============================================================================
    
    def is_transport_unit(self, unit: 'Unit') -> bool:
        """Check if unit can transport other units"""
        unit_type = unit.type.name if hasattr(unit.type, 'name') else str(unit.type)
        return unit_type in self.transport_capabilities
    
    def get_max_capacity(self, transport: 'Unit') -> int:
        """Get maximum cargo capacity for transport"""
        transport_type = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        
        if transport_type not in self.transport_capabilities:
            return 0
        
        return self.transport_capabilities[transport_type].max_capacity
    
    def has_cargo_space(self, transport: 'Unit') -> bool:
        """Check if transport has available cargo space"""
        if not hasattr(transport.status, 'cargo') or transport.status.cargo is None:
            return True
        
        max_capacity = self.get_max_capacity(transport)
        current_cargo = sum(1 for slot in transport.status.cargo if slot is not None)
        
        return current_cargo < max_capacity
    
    def can_carry_unit_type(self, transport: 'Unit', cargo_unit_type: str) -> bool:
        """Check if transport can carry specific unit type"""
        transport_type = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        
        if transport_type not in self.transport_capabilities:
            return False
        
        allowed_types = self.transport_capabilities[transport_type].allowed_unit_types
        return cargo_unit_type in allowed_types
    
    # =============================================================================
    # ADVANCE WARS STYLE LOADING - CARGO MOVES INTO TRANSPORT
    # =============================================================================
    
    def can_cargo_move_into_transport(self, cargo: 'Unit', transport: 'Unit',
                                    cargo_x: int, cargo_y: int,
                                    transport_x: int, transport_y: int) -> Tuple[bool, str]:
        """
        ADVANCE WARS STYLE: Check if cargo unit can move into transport
        This is called when the CARGO UNIT is selected and wants to move INTO a transport
        """
        
        # Check if target is actually a transport
        if not self.is_transport_unit(transport):
            return False, f"{transport.type.name} cannot transport other units"
        
        # Check if units are adjacent (cargo can reach transport)
        distance = abs(cargo_x - transport_x) + abs(cargo_y - transport_y)
        if distance != 1:
            return False, "Must move to adjacent transport"
        
        # Check if cargo unit can move
        if not cargo.can_move:
            return False, "Unit has already moved this turn"
        
        # Check if transport has capacity
        if not self.has_cargo_space(transport):
            return False, f"{transport.type.name} is at maximum capacity"
        
        # Check if transport can carry this unit type
        cargo_type = cargo.type.name if hasattr(cargo.type, 'name') else str(cargo.type)
        if not self.can_carry_unit_type(transport, cargo_type):
            return False, f"{transport.type.name} cannot carry {cargo_type}"
        
        # Check if units are same army
        if transport.army != cargo.army:
            return False, "Cannot board enemy transport"
        
        return True, f"Can board {transport.type.name}"
    
    def cargo_move_into_transport(self, cargo: 'Unit', transport: 'Unit',
                                cargo_x: int, cargo_y: int,
                                transport_x: int, transport_y: int) -> LoadResult:
        """
        ADVANCE WARS STYLE: Cargo unit moves into transport
        This is the main loading method - cargo moves TO the transport location
        """
        
        # Validate the move
        can_board, message = self.can_cargo_move_into_transport(
            cargo, transport, cargo_x, cargo_y, transport_x, transport_y
        )
        if not can_board:
            return LoadResult(success=False, message=message)
        
        # Initialize transport cargo if needed
        if not hasattr(transport.status, 'cargo') or transport.status.cargo is None:
            transport.status.cargo = [None] * self.get_max_capacity(transport)
        elif isinstance(transport.status.cargo, list) and len(transport.status.cargo) == 0:
            transport.status.cargo = [None] * self.get_max_capacity(transport)
        
        # Find empty cargo slot
        cargo_index = None
        for i in range(len(transport.status.cargo)):
            if transport.status.cargo[i] is None:
                cargo_index = i
                break
        
        if cargo_index is None:
            return LoadResult(success=False, message="No available cargo slots")
        
        # Calculate movement cost for the cargo unit
        move_distance = abs(cargo_x - transport_x) + abs(cargo_y - transport_y)
        
        # Check if cargo has enough movement
        if move_distance > cargo.status.move:
            return LoadResult(success=False, message="Not enough movement to reach transport")
        
        # Execute the boarding
        print(f"AW_TRANSPORT: {cargo.type.name} moving from ({cargo_x},{cargo_y}) into {transport.type.name} at ({transport_x},{transport_y})")
        
        # Store cargo unit in transport
        transport.status.cargo[cargo_index] = cargo
        
        # Remove cargo unit from board (it's now inside the transport)
        self.manager.unit_remove(cargo_x, cargo_y)
        
        # Cargo unit is now "spent" for this turn (moved into transport)
        cargo.can_move = False
        cargo.can_attack = False
        cargo.can_capture = False
        
        # Transport does NOT lose its turn for having a unit board it
        # (This matches Advance Wars - transports can still move after loading)
        
        cargo_type_name = cargo.type.name if hasattr(cargo.type, 'name') else str(cargo.type)
        transport_type_name = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        
        return LoadResult(
            success=True, 
            message=f"{cargo_type_name} boarded {transport_type_name}",
            cargo_index=cargo_index
        )
    
    # =============================================================================
    # ADVANCE WARS STYLE UNLOADING - CARGO EXITS FROM TRANSPORT
    # =============================================================================
    
    def can_cargo_exit_transport(self, transport: 'Unit', cargo_index: int,
                               transport_x: int, transport_y: int,
                               exit_x: int, exit_y: int) -> Tuple[bool, str]:
        """
        ADVANCE WARS STYLE: Check if cargo can exit transport to specific position
        This is called when a cargo unit wants to EXIT the transport
        """
        
        # Check if transport has cargo
        if not hasattr(transport.status, 'cargo') or not transport.status.cargo:
            return False, "Transport has no cargo"
        
        # Check cargo index
        if cargo_index >= len(transport.status.cargo) or transport.status.cargo[cargo_index] is None:
            return False, "No unit at specified cargo index"
        
        # Check if exit position is adjacent to transport
        distance = abs(transport_x - exit_x) + abs(transport_y - exit_y)
        if distance != 1:
            return False, "Can only exit to adjacent tiles"
        
        # Check if destination is empty
        if self.manager.unit_at(exit_x, exit_y):
            return False, "Exit position is occupied"
        
        # Check terrain compatibility
        cargo = transport.status.cargo[cargo_index]
        if isinstance(cargo, dict):
            cargo = self._reconstruct_unit_from_dict(cargo)
        
        exit_tile = self.manager.tile_at(exit_x, exit_y)
        terrain_name = exit_tile.mapTile.type.name if hasattr(exit_tile.mapTile.type, 'name') else str(exit_tile.mapTile.type)
        
        # Check if cargo unit can move on this terrain
        cargo_type = cargo.type.name if hasattr(cargo.type, 'name') else str(cargo.type)
        
        # Basic terrain restrictions
        if terrain_name == 'SEA' and cargo_type not in ['LANDER', 'CRUISER', 'BATTLESHIP', 'SUB']:
            return False, f"Cannot deploy {cargo_type} onto water"
        
        # Check if transport can operate on current terrain (for naval units)
        transport_tile = self.manager.tile_at(transport_x, transport_y)
        transport_terrain = transport_tile.mapTile.type.name if hasattr(transport_tile.mapTile.type, 'name') else str(transport_tile.mapTile.type)
        transport_type = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        
        # Landers can only unload on shoals/beaches
        if transport_type == 'LANDER' and transport_terrain not in ['SHOAL', 'BEACH']:
            return False, "Lander must be on shoal or beach to deploy units"
        
        return True, f"Can deploy {cargo_type}"
    
    def cargo_exit_transport(self, transport: 'Unit', cargo_index: int,
                           transport_x: int, transport_y: int,
                           exit_x: int, exit_y: int) -> UnloadResult:
        """
        ADVANCE WARS STYLE: Cargo unit exits transport to specified position
        This is the main unloading method - cargo exits TO a specific location
        """
        
        # Validate the exit
        can_exit, message = self.can_cargo_exit_transport(
            transport, cargo_index, transport_x, transport_y, exit_x, exit_y
        )
        if not can_exit:
            return UnloadResult(success=False, message=message)
        
        # Get cargo unit
        cargo = transport.status.cargo[cargo_index]
        
        # Handle serialized units
        if isinstance(cargo, dict):
            print(f"AW_TRANSPORT: Reconstructing serialized unit from transport")
            cargo = self._reconstruct_unit_from_dict(cargo)
        
        # Ensure we have a proper Unit object
        if not hasattr(cargo, 'type') or not hasattr(cargo, 'army'):
            print(f"AW_TRANSPORT: Invalid cargo unit data")
            return UnloadResult(success=False, message="Invalid cargo unit data")
        
        # Remove from transport
        transport.status.cargo[cargo_index] = None
        
        # ADVANCE WARS RULE: Unloaded unit can act immediately this turn
        cargo.can_move = True
        cargo.can_attack = True
        cargo.can_capture = True
        
        # Clear any previous turn flags
        if hasattr(cargo, '_unloaded_this_turn'):
            delattr(cargo, '_unloaded_this_turn')
        
        print(f"AW_TRANSPORT: {cargo.type.name} exiting transport to ({exit_x},{exit_y})")
        
        # Place unit at exit position
        try:
            self.manager.unit_place(cargo, exit_x, exit_y)
            print(f"AW_TRANSPORT: Successfully deployed {cargo.type.name} at ({exit_x}, {exit_y})")
        except Exception as e:
            print(f"AW_TRANSPORT: Failed to deploy unit: {e}")
            return UnloadResult(success=False, message=f"Failed to deploy unit: {e}")
        
        # Transport becomes inactive after unloading (Advance Wars rule)
        transport.can_move = False
        transport.can_attack = False
        
        cargo_type_name = cargo.type.name if hasattr(cargo.type, 'name') else str(cargo.type)
        transport_type_name = transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        
        return UnloadResult(
            success=True,
            message=f"{cargo_type_name} deployed from {transport_type_name}",
            unloaded_position=(exit_x, exit_y)
        )
    
    # =============================================================================
    # MOVEMENT INTEGRATION - FOR UI AND PATHFINDING
    # =============================================================================
    
    def get_loadable_transports_near(self, cargo_x: int, cargo_y: int) -> List[Dict]:
        """
        Get all adjacent transports that this cargo unit can board
        Used for UI highlighting when cargo unit is selected
        """
        cargo_unit = self.manager.unit_at(cargo_x, cargo_y)
        if not cargo_unit:
            return []
        
        loadable_transports = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dx, dy in directions:
            transport_x = cargo_x + dx
            transport_y = cargo_y + dy
            
            # Check bounds
            if not (0 <= transport_x < self.manager.board.width and 0 <= transport_y < self.manager.board.height):
                continue
            
            # Check for transport unit
            transport_unit = self.manager.unit_at(transport_x, transport_y)
            if not transport_unit:
                continue
            
            # Check if cargo can board this transport
            can_board, message = self.can_cargo_move_into_transport(
                cargo_unit, transport_unit, cargo_x, cargo_y, transport_x, transport_y
            )
            
            if can_board:
                loadable_transports.append({
                    'x': transport_x,
                    'y': transport_y,
                    'transport_type': transport_unit.type.name if hasattr(transport_unit.type, 'name') else str(transport_unit.type),
                    'available_space': self.get_max_capacity(transport_unit) - self._get_current_cargo_count(transport_unit),
                    'message': message
                })
        
        return loadable_transports
    
    def get_valid_exit_positions(self, transport_x: int, transport_y: int) -> List[Tuple[int, int]]:
        """
        Get all valid positions where cargo can exit from transport
        Used for UI highlighting when transport is selected
        """
        transport = self.manager.unit_at(transport_x, transport_y)
        if not transport or not self.is_transport_unit(transport):
            return []
        
        valid_positions = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dx, dy in directions:
            exit_x = transport_x + dx
            exit_y = transport_y + dy
            
            # Check bounds
            if not (0 <= exit_x < self.manager.board.width and 0 <= exit_y < self.manager.board.height):
                continue
            
            # Check if position is empty
            if self.manager.unit_at(exit_x, exit_y):
                continue
            
            # Check if any cargo can exit here
            if hasattr(transport.status, 'cargo') and transport.status.cargo:
                for i, cargo in enumerate(transport.status.cargo):
                    if cargo is not None:
                        can_exit, _ = self.can_cargo_exit_transport(
                            transport, i, transport_x, transport_y, exit_x, exit_y
                        )
                        if can_exit:
                            valid_positions.append((exit_x, exit_y))
                            break
        
        return valid_positions
    
    # =============================================================================
    # TURN MANAGEMENT INTEGRATION
    # =============================================================================
    
    def reset_units_for_new_turn(self, army):
        """Reset all units for new turn, including cargo units"""
        print(f"AW_TRANSPORT: Resetting units for {army} turn")
        
        # Reset all units on the board
        for tile in self.manager.board.grid:
            if tile.unit and tile.unit.army == army:
                self._reset_unit_for_turn(tile.unit)
                
                # Also reset any cargo units
                if (hasattr(tile.unit.status, 'cargo') and 
                    tile.unit.status.cargo and 
                    self.is_transport_unit(tile.unit)):
                    
                    for i, cargo in enumerate(tile.unit.status.cargo):
                        if cargo is not None:
                            # Handle serialized cargo
                            if isinstance(cargo, dict):
                                cargo = self._reconstruct_unit_from_dict(cargo)
                                tile.unit.status.cargo[i] = cargo
                            
                            # Reset cargo unit flags
                            if hasattr(cargo, 'can_move'):
                                self._reset_unit_for_turn(cargo)
                                print(f"AW_TRANSPORT: Reset cargo unit {cargo.type.name}")
    
    def _reset_unit_for_turn(self, unit):
        """Reset individual unit for new turn"""
        unit.can_move = True
        unit.can_attack = True
        unit.can_capture = True
        
        # Clear any previous turn flags
        if hasattr(unit, '_unloaded_this_turn'):
            delattr(unit, '_unloaded_this_turn')
        
        print(f"AW_TRANSPORT: Reset {unit.type.name} - can_move: {unit.can_move}")
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def _get_current_cargo_count(self, transport: 'Unit') -> int:
        """Get current number of units in transport"""
        if not hasattr(transport.status, 'cargo') or not transport.status.cargo:
            return 0
        
        return sum(1 for slot in transport.status.cargo if slot is not None)
    
    def get_cargo_info(self, transport: 'Unit') -> Dict:
        """Get detailed information about transport's current cargo"""
        if not self.is_transport_unit(transport):
            return {"is_transport": False}
        
        cargo_list = []
        if hasattr(transport.status, 'cargo') and transport.status.cargo:
            for i, cargo in enumerate(transport.status.cargo):
                if cargo is not None:
                    # Handle both Unit objects and dicts
                    if isinstance(cargo, dict):
                        unit_type = cargo.get('type', 'UNKNOWN')
                        unit_hp = cargo.get('status', {}).get('hp', 0)
                    else:
                        unit_type = cargo.type.name if hasattr(cargo.type, 'name') else str(cargo.type)
                        unit_hp = cargo.status.hp if hasattr(cargo.status, 'hp') else 0
                    
                    cargo_list.append({
                        "index": i,
                        "unit_type": unit_type,
                        "hp": unit_hp
                    })
        
        return {
            "is_transport": True,
            "max_capacity": self.get_max_capacity(transport),
            "current_cargo": len(cargo_list),
            "cargo_units": cargo_list,
            "has_space": self.has_cargo_space(transport),
            "transport_type": transport.type.name if hasattr(transport.type, 'name') else str(transport.type)
        }
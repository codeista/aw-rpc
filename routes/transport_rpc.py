"""
Transport RPC Methods Module
Contains all transport-related JSONRPC methods
"""

from typing import Dict, List, Any, Optional, Tuple
from app_core import jsonrpc, app_logger

# Import decorator locally to avoid circular imports
from functools import wraps
import time

def log_rpc_performance(func):
    """Decorator to log RPC call performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        method_name = func.__name__.replace('_rpc', '')
        
        try:
            app_logger.info(f"RPC_START {method_name}")
            result = func(*args, **kwargs)
            
            duration_ms = (time.time() - start_time) * 1000
            app_logger.info(f"RPC_SUCCESS {method_name} duration={duration_ms:.2f}ms")
            
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            app_logger.error(f"RPC_ERROR {method_name} error={str(e)}")
            raise
    return wrapper

@log_rpc_performance
@jsonrpc.method('cargo_board_transport')
def cargo_board_transport_rpc(token: str, cargo_x: int, cargo_y: int, transport_x: int, transport_y: int) -> Dict[str, Any]:
    """Board a cargo unit onto a transport"""
    # Import here to avoid circular imports
    from game_utils import game_load, games
    
    mngr = game_load(token)
    
    try:
        # Use enhanced transport system if available
        if hasattr(mngr, 'transport_system'):
            # Get the units
            cargo_tile = mngr.tile_at(cargo_x, cargo_y)
            transport_tile = mngr.tile_at(transport_x, transport_y)
            
            if not cargo_tile or not cargo_tile.unit:
                return {'success': False, 'error': 'No cargo unit at specified position'}
            if not transport_tile or not transport_tile.unit:
                return {'success': False, 'error': 'No transport at specified position'}
            
            cargo = cargo_tile.unit
            transport = transport_tile.unit
            
            result = mngr.transport_system.load_unit_enhanced(transport, cargo, transport_x, transport_y, cargo_x, cargo_y)
            
            # Convert TransportResult to dict
            if hasattr(result, 'success'):
                return {
                    'success': result.success,
                    'message': result.message
                }
            return result
        else:
            result = mngr.unit_load(cargo_x, cargo_y, transport_x, transport_y)
        
        if result.get('success'):
            # Save game state
            games[token] = mngr
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error boarding transport from ({cargo_x},{cargo_y}) to ({transport_x},{transport_y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('cargo_exit_transport')
def cargo_exit_transport_rpc(token: str, transport_x: int, transport_y: int, exit_x: int, exit_y: int, cargo_index: int = 0) -> Dict[str, Any]:
    """Exit a cargo unit from a transport"""
    # Import here to avoid circular imports
    from game_utils import game_load, games
    
    mngr = game_load(token)
    
    try:
        # Use enhanced transport system if available
        if hasattr(mngr, 'transport_system'):
            # Get the transport unit
            transport_tile = mngr.tile_at(transport_x, transport_y)
            if not transport_tile or not transport_tile.unit:
                return {'success': False, 'error': 'No transport at specified position'}
            
            transport = transport_tile.unit
            result = mngr.transport_system.cargo_exit_transport(transport, cargo_index, transport_x, transport_y, exit_x, exit_y)
            
            # Convert TransportResult to dict
            if hasattr(result, 'success'):
                if result.success:
                    # Save game state
                    games[token] = mngr
                return {
                    'success': result.success,
                    'message': result.message,
                    'unloaded_position': result.unloaded_position
                }
            return result
        else:
            result = mngr.unit_unload(transport_x, transport_y, exit_x, exit_y)
            if result.get('success'):
                # Save game state
                games[token] = mngr
            return result
        
    except Exception as e:
        app_logger.error(f"Error exiting transport from ({transport_x},{transport_y}) to ({exit_x},{exit_y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('get_loadable_transports')
def get_loadable_transports_rpc(token: str, cargo_x: int, cargo_y: int) -> Dict[str, Any]:
    """Get transports that can load the specified cargo unit"""
    # Import here to avoid circular imports
    from game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        print(f"DEBUG: Starting get_loadable_transports for cargo at ({cargo_x},{cargo_y})")
        
        if hasattr(mngr, 'transport_system'):
            print(f"DEBUG: Manager has transport_system")
            # First try the transport system method
            try:
                transports = mngr.transport_system.get_loadable_transports_near(cargo_x, cargo_y)
                print(f"DEBUG: Found {len(transports)} transports")
                
                # Get cargo unit type for context
                cargo_tile = mngr.tile_at(cargo_x, cargo_y)
                cargo_type = "UNKNOWN"
                if cargo_tile and cargo_tile.unit:
                    cargo_type = cargo_tile.unit.type.name
                
                return {
                    'success': True,
                    'loadable_transports': transports,
                    'cargo_type': cargo_type,
                    'count': len(transports),
                    'debug': 'transport_system_used'
                }
            except Exception as e:
                import traceback
                print(f"DEBUG: Transport system method failed: {e}")
                print(f"DEBUG: Full traceback: {traceback.format_exc()}")
                # Fall through to fallback implementation
        else:
            print(f"DEBUG: Manager missing transport_system")
            # Fallback implementation - find adjacent transports
            loadable_transports = []
            
            # Check adjacent tiles for compatible transports
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                        
                    check_x = cargo_x + dx
                    check_y = cargo_y + dy
                    
                    if (0 <= check_x < mngr.board.width and 0 <= check_y < mngr.board.height):
                        index = check_y * mngr.board.width + check_x
                        tile = mngr.board.grid[index]
                        
                        # Check if unit is a transport type and can load this cargo
                        transport_types = ['APC', 'TCOPTER', 'LANDER', 'CRUISER', 'CARRIER', 'BLACKBOAT']
                        cargo_types = ['INFANTRY', 'MECH', 'RECON', 'TANK']
                        
                        if (tile.unit and 
                            tile.unit.type.name in transport_types):
                            
                            # Check if transport can load this type of unit
                            cargo_index = cargo_y * mngr.board.width + cargo_x
                            cargo_tile = mngr.board.grid[cargo_index]
                            
                            if (cargo_tile.unit and 
                                cargo_tile.unit.army == tile.unit.army and
                                cargo_tile.unit.type.name in cargo_types):
                                
                                # Default cargo capacity by unit type
                                cargo_capacity = {
                                    'APC': 1, 'TCOPTER': 1, 'LANDER': 2, 
                                    'CRUISER': 2, 'CARRIER': 2, 'BLACKBOAT': 1
                                }.get(tile.unit.type.name, 1)
                                
                                current_cargo = len(getattr(tile.unit, 'cargo', []))
                                
                                transport_info = {
                                    'x': check_x,
                                    'y': check_y,
                                    'unit_type': tile.unit.type.name,
                                    'army': tile.unit.army.name,
                                    'cargo_space': cargo_capacity - current_cargo,
                                    'cargo_info': {
                                        'current_cargo': current_cargo,
                                        'max_capacity': cargo_capacity
                                    }
                                }
                                loadable_transports.append(transport_info)
            
            # Add debug info about what we checked
            cargo_tile = mngr.board.grid[cargo_y * mngr.board.width + cargo_x] if cargo_y * mngr.board.width + cargo_x < len(mngr.board.grid) else None
            debug_info = {
                'cargo_exists': cargo_tile is not None and cargo_tile.unit is not None,
                'cargo_type': cargo_tile.unit.type.name if cargo_tile and cargo_tile.unit else "None",
                'cargo_army': cargo_tile.unit.army.name if cargo_tile and cargo_tile.unit else "None",
                'checked_positions': []
            }
            
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    check_x = cargo_x + dx
                    check_y = cargo_y + dy
                    if (0 <= check_x < mngr.board.width and 0 <= check_y < mngr.board.height):
                        index = check_y * mngr.board.width + check_x
                        tile = mngr.board.grid[index]
                        debug_info['checked_positions'].append({
                            'pos': (check_x, check_y),
                            'has_unit': tile.unit is not None,
                            'unit_type': tile.unit.type.name if tile.unit else "None",
                            'unit_army': tile.unit.army.name if tile.unit else "None"
                        })
            
            return {
                'success': True,
                'loadable_transports': loadable_transports,
                'debug': debug_info
            }
        
    except Exception as e:
        app_logger.error(f"Error getting loadable transports for cargo at ({cargo_x},{cargo_y}) for {token}: {e}")
        return {'transports': [], 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('get_exit_positions')
def get_exit_positions_rpc(token: str, transport_x: int, transport_y: int) -> Dict[str, Any]:
    """Get valid exit positions for a transport"""
    # Import here to avoid circular imports
    from game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        if hasattr(mngr, 'transport_system'):
            positions = mngr.transport_system.get_valid_exit_positions(transport_x, transport_y)
            return {
                'success': True,
                'valid_positions': positions
            }
        else:
            # Use existing method
            positions = mngr.get_unload_positions(transport_x, transport_y)
            return {
                'success': True,
                'valid_positions': positions
            }
        
    except Exception as e:
        app_logger.error(f"Error getting exit positions for transport at ({transport_x},{transport_y}) for {token}: {e}")
        return {'positions': [], 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('can_cargo_exit_transport')
def can_cargo_exit_transport_rpc(token: str, transport_x: int, transport_y: int, exit_x: int, exit_y: int) -> Dict[str, Any]:
    """Check if cargo can exit transport at specified position"""
    # Import here to avoid circular imports
    from game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        if hasattr(mngr, 'transport_system'):
            result = mngr.transport_system.can_exit_transport(transport_x, transport_y, exit_x, exit_y)
        else:
            # Basic validation
            result = {'can_exit': True}  # Simplified check
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error checking exit from transport at ({transport_x},{transport_y}) to ({exit_x},{exit_y}) for {token}: {e}")
        return {'can_exit': False, 'error': str(e)}

# Note: unit_move_enhanced is implemented in rpc_methods.py to avoid duplication

@log_rpc_performance
@jsonrpc.method('can_transport_move')
def can_transport_move_rpc(token: str, transport_x: int, transport_y: int, to_x: int, to_y: int) -> Dict[str, Any]:
    """Check if a transport can move to specified position"""
    # Import here to avoid circular imports
    from game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        result = mngr.validate_movement(transport_x, transport_y, to_x, to_y)
        return result
        
    except Exception as e:
        app_logger.error(f"Error checking transport movement from ({transport_x},{transport_y}) to ({to_x},{to_y}) for {token}: {e}")
        return {'can_move': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('load_transport_unit')
def load_transport_unit_rpc(token: str, cargo_x: int, cargo_y: int, transport_x: int, transport_y: int) -> Dict[str, Any]:
    """Load a unit into a transport (enhanced version)"""
    # Import here to avoid circular imports
    from game_utils import game_load, games
    
    mngr = game_load(token)
    
    try:
        if hasattr(mngr, 'transport_system'):
            result = mngr.transport_system.load_unit(cargo_x, cargo_y, transport_x, transport_y)
        else:
            result = mngr.unit_load(cargo_x, cargo_y, transport_x, transport_y)
        
        if result.get('success'):
            # Save game state
            games[token] = mngr
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error loading transport unit from ({cargo_x},{cargo_y}) to ({transport_x},{transport_y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('unload_transport_unit')
def unload_transport_unit_rpc(token: str, transport_x: int, transport_y: int, unload_x: int, unload_y: int) -> Dict[str, Any]:
    """Unload a unit from a transport (enhanced version)"""
    # Import here to avoid circular imports
    from game_utils import game_load, games
    
    mngr = game_load(token)
    
    try:
        if hasattr(mngr, 'transport_system'):
            result = mngr.transport_system.unload_unit(transport_x, transport_y, unload_x, unload_y)
        else:
            result = mngr.unit_unload(transport_x, transport_y, unload_x, unload_y)
        
        if result.get('success'):
            # Save game state
            games[token] = mngr
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error unloading transport unit from ({transport_x},{transport_y}) to ({unload_x},{unload_y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('get_transport_info')
def get_transport_info_rpc(token: str, transport_x: int, transport_y: int) -> Dict[str, Any]:
    """Get detailed information about a transport"""
    # Import here to avoid circular imports
    from game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        # Get tile info
        index = transport_y * mngr.board.width + transport_x
        tile = mngr.board.grid[index]
        
        if not tile.unit:
            return {'error': 'No unit at specified position'}
        
        unit = tile.unit
        transport_info = {
            'type': unit.type.name,
            'army': unit.army.name,
            'health': unit.status.health,
            'fuel': unit.status.fuel,
            'cargo_capacity': getattr(unit, 'cargo_capacity', 0),
            'cargo_units': []
        }
        
        # Get cargo information if available
        if hasattr(unit, 'cargo') and unit.cargo:
            for cargo_unit in unit.cargo:
                transport_info['cargo_units'].append({
                    'type': cargo_unit.type.name,
                    'army': cargo_unit.army.name,
                    'health': cargo_unit.status.health
                })
        
        return transport_info
        
    except Exception as e:
        app_logger.error(f"Error getting transport info at ({transport_x},{transport_y}) for {token}: {e}")
        return {'error': str(e)}

@log_rpc_performance
@jsonrpc.method('get_valid_unload_positions')
def get_valid_unload_positions_rpc(token: str, transport_x: int, transport_y: int) -> Dict[str, Any]:
    """Get all valid unload positions for a transport"""
    # Import here to avoid circular imports
    from game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        positions = mngr.get_unload_positions(transport_x, transport_y)
        return {
            'positions': positions,
            'count': len(positions)
        }
        
    except Exception as e:
        app_logger.error(f"Error getting valid unload positions for transport at ({transport_x},{transport_y}) for {token}: {e}")
        return {'positions': [], 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('get_transport_summary')
def get_transport_summary_rpc(token: str) -> Dict[str, Any]:
    """Get summary of all transports in the game"""
    # Import here to avoid circular imports
    from game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        transports = []
        
        for i, tile in enumerate(mngr.board.grid):
            if tile.unit and hasattr(tile.unit, 'cargo_capacity'):
                x = i % mngr.board.width
                y = i // mngr.board.width
                
                transport_data = {
                    'position': (x, y),
                    'type': tile.unit.type.name,
                    'army': tile.unit.army.name,
                    'health': tile.unit.status.health,
                    'cargo_count': len(getattr(tile.unit, 'cargo', []))
                }
                transports.append(transport_data)
        
        return {
            'transports': transports,
            'total_count': len(transports)
        }
        
    except Exception as e:
        app_logger.error(f"Error getting transport summary for {token}: {e}")
        return {'transports': [], 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('get_cargo_info')
def get_cargo_info_rpc(token: str, transport_x: int, transport_y: int) -> Dict[str, Any]:
    """Get information about cargo units in a transport"""
    # Import here to avoid circular imports
    from game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        index = transport_y * mngr.board.width + transport_x
        tile = mngr.board.grid[index]
        
        if not tile.unit:
            return {'error': 'No unit at specified position'}
        
        unit = tile.unit
        cargo_info = []
        
        if hasattr(unit, 'cargo') and unit.cargo:
            for i, cargo_unit in enumerate(unit.cargo):
                cargo_info.append({
                    'slot': i,
                    'type': cargo_unit.type.name,
                    'army': cargo_unit.army.name,
                    'health': cargo_unit.status.health,
                    'fuel': cargo_unit.status.fuel,
                    'ammo': cargo_unit.status.ammo
                })
        elif hasattr(unit.status, 'cargo') and unit.status.cargo:
            # Check if cargo is stored in unit.status instead
            for i, cargo_unit in enumerate(unit.status.cargo):
                if cargo_unit:  # Skip None entries
                    cargo_info.append({
                        'slot': i,
                        'type': cargo_unit.type.name if hasattr(cargo_unit.type, 'name') else str(cargo_unit.type),
                        'army': cargo_unit.army.name if hasattr(cargo_unit.army, 'name') else str(cargo_unit.army),
                        'health': cargo_unit.status.hp if hasattr(cargo_unit.status, 'hp') else cargo_unit.status.health,
                        'fuel': cargo_unit.status.fuel,
                        'ammo': cargo_unit.status.ammo
                    })
        
        # Try to get transport info from transport system
        cargo_info_dict = {
            'cargo_units': cargo_info,
            'cargo_count': len(cargo_info),
            'capacity': getattr(unit, 'cargo_capacity', 0)
        }
        
        # Add transport system info if available
        if hasattr(mngr, 'transport_system'):
            ts_info = mngr.transport_system.get_cargo_info(unit)
            cargo_info_dict.update(ts_info)
        
        return cargo_info_dict
        
    except Exception as e:
        app_logger.error(f"Error getting cargo info for transport at ({transport_x},{transport_y}) for {token}: {e}")
        return {'cargo_units': [], 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('get_loadable_units')
def get_loadable_units_rpc(token: str, transport_x: int, transport_y: int) -> Dict[str, Any]:
    """Get units that can be loaded into a transport"""
    # Import here to avoid circular imports
    from game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        loadable_units = []
        
        # Check adjacent tiles for loadable units
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                    
                check_x = transport_x + dx
                check_y = transport_y + dy
                
                if (0 <= check_x < mngr.board.width and 0 <= check_y < mngr.board.height):
                    index = check_y * mngr.board.width + check_x
                    tile = mngr.board.grid[index]
                    
                    if tile.unit and tile.unit.army == mngr.board.current_turn:
                        # Check if unit can be loaded (simplified check)
                        unit_info = {
                            'position': (check_x, check_y),
                            'type': tile.unit.type.name,
                            'army': tile.unit.army.name,
                            'health': tile.unit.status.health
                        }
                        loadable_units.append(unit_info)
        
        return {
            'loadable_units': loadable_units,
            'count': len(loadable_units)
        }
        
    except Exception as e:
        app_logger.error(f"Error getting loadable units for transport at ({transport_x},{transport_y}) for {token}: {e}")
        return {'loadable_units': [], 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('load_unit')
def load_unit_rpc(token: str, unit_x: int, unit_y: int, transport_x: int, transport_y: int) -> Dict[str, Any]:
    """Load a unit into a transport (wrapper method)"""
    # Import here to avoid circular imports
    from game_utils import game_load, games
    
    mngr = game_load(token)
    
    try:
        result = mngr.unit_load(unit_x, unit_y, transport_x, transport_y)
        
        if result.get('success'):
            # Save game state
            games[token] = mngr
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error loading unit from ({unit_x},{unit_y}) into transport at ({transport_x},{transport_y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('unload_unit')
def unload_unit_rpc(token: str, transport_x: int, transport_y: int, target_x: int, target_y: int) -> Dict[str, Any]:
    """Unload a unit from a transport (wrapper method)"""
    # Import here to avoid circular imports
    from game_utils import game_load, games
    
    mngr = game_load(token)
    
    try:
        result = mngr.unit_unload(transport_x, transport_y, target_x, target_y)
        
        if result.get('success'):
            # Save game state
            games[token] = mngr
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error unloading unit from transport at ({transport_x},{transport_y}) to ({target_x},{target_y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('get_transport_units')
def get_transport_units_rpc(token: str) -> Dict[str, Any]:
    """Get all transport units in the game"""
    # Import here to avoid circular imports
    from game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        transport_units = []
        
        for i, tile in enumerate(mngr.board.grid):
            if tile.unit and hasattr(tile.unit, 'cargo_capacity'):
                x = i % mngr.board.width
                y = i // mngr.board.width
                
                unit_info = {
                    'position': (x, y),
                    'type': tile.unit.type.name,
                    'army': tile.unit.army.name,
                    'health': tile.unit.status.health,
                    'fuel': tile.unit.status.fuel,
                    'cargo_capacity': getattr(tile.unit, 'cargo_capacity', 0),
                    'cargo_count': len(getattr(tile.unit, 'cargo', []))
                }
                transport_units.append(unit_info)
        
        return {
            'transport_units': transport_units,
            'total_transports': len(transport_units)
        }
        
    except Exception as e:
        app_logger.error(f"Error getting transport units for {token}: {e}")
        return {'transport_units': [], 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('can_load_unit')
def can_load_unit_rpc(token: str, unit_x: int, unit_y: int, transport_x: int, transport_y: int) -> Dict[str, Any]:
    """Check if a unit can be loaded into a transport"""
    # Import here to avoid circular imports
    from game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        # Basic validation checks
        unit_index = unit_y * mngr.board.width + unit_x
        transport_index = transport_y * mngr.board.width + transport_x
        
        unit_tile = mngr.board.grid[unit_index]
        transport_tile = mngr.board.grid[transport_index]
        
        if not unit_tile.unit:
            return {'can_load': False, 'reason': 'No unit at specified position'}
        
        if not transport_tile.unit:
            return {'can_load': False, 'reason': 'No transport at specified position'}
        
        # Check if units are same army
        if unit_tile.unit.army != transport_tile.unit.army:
            return {'can_load': False, 'reason': 'Units must be same army'}
        
        # Check if transport has capacity
        if hasattr(transport_tile.unit, 'cargo_capacity'):
            current_cargo = len(getattr(transport_tile.unit, 'cargo', []))
            if current_cargo >= transport_tile.unit.cargo_capacity:
                return {'can_load': False, 'reason': 'Transport at full capacity'}
        
        return {'can_load': True}
        
    except Exception as e:
        app_logger.error(f"Error checking if unit at ({unit_x},{unit_y}) can load into transport at ({transport_x},{transport_y}) for {token}: {e}")
        return {'can_load': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('can_unload_unit')
def can_unload_unit_rpc(token: str, transport_x: int, transport_y: int, target_x: int, target_y: int) -> Dict[str, Any]:
    """Check if a unit can be unloaded from a transport"""
    # Import here to avoid circular imports
    from game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        # Check if transport has cargo
        transport_index = transport_y * mngr.board.width + transport_x
        transport_tile = mngr.board.grid[transport_index]
        
        if not transport_tile.unit:
            return {'can_unload': False, 'reason': 'No transport at specified position'}
        
        if not hasattr(transport_tile.unit, 'cargo') or not transport_tile.unit.cargo:
            return {'can_unload': False, 'reason': 'Transport has no cargo'}
        
        # Check if target position is valid
        target_index = target_y * mngr.board.width + target_x
        target_tile = mngr.board.grid[target_index]
        
        if target_tile.unit:
            return {'can_unload': False, 'reason': 'Target position occupied'}
        
        # Check if target is adjacent to transport
        distance = abs(transport_x - target_x) + abs(transport_y - target_y)
        if distance != 1:
            return {'can_unload': False, 'reason': 'Target must be adjacent to transport'}
        
        return {'can_unload': True}
        
    except Exception as e:
        app_logger.error(f"Error checking if unit can unload from transport at ({transport_x},{transport_y}) to ({target_x},{target_y}) for {token}: {e}")
        return {'can_unload': False, 'error': str(e)}
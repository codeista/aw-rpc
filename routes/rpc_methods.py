"""
RPC Methods Module  
Contains all JSONRPC method definitions for the game API
"""

from typing import Dict, List, Any, Optional, Tuple
import time
import json
from app_core import jsonrpc, app_logger
from core.map_system import Army
from middleware.error_handling import (
    validate_rpc_params, validate_token, validate_coordinates, 
    validate_army, validate_unit_type, safe_rpc_call, log_game_event,
    AWRPCError, ValidationError, GameStateError, UnitError, MovementError
)

# Import decorator - define here to avoid circular imports
from functools import wraps
import time

def log_rpc_performance(func):
    """Decorator to log RPC call performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        method_name = func.__name__.replace('_rpc', '')
        
        try:
            app_logger.info(f"RPC_START {method_name} args={len(args)} kwargs={len(kwargs)}")
            result = func(*args, **kwargs)
            
            duration_ms = (time.time() - start_time) * 1000
            app_logger.info(f"RPC_SUCCESS {method_name} duration={duration_ms:.2f}ms")
            
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            app_logger.error(f"RPC_ERROR {method_name} duration={duration_ms:.2f}ms error={str(e)}")
            raise
    return wrapper

@jsonrpc.method('game_create_with_setup')
def game_create_with_setup(token: str, setup_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new game with complete setup configuration"""
    try:
        # Import here to avoid circular imports
        from core.game_utils import games
        from manager import GameManager
        from gameboard import GameBoard
        from config import Config
        from core.map_system import map_repository, Army
        
        app_logger.info(f"Creating game with setup: {token}")
        
        # Get the specified map
        map_id = setup_data.get('map_id', 'test')
        game_map = map_repository.get_map(map_id)
        if not game_map:
            game_map = map_repository.get_map('test')  # Fallback
            
        # Create game board
        config_game = Config()
        board = GameBoard.create(game_map)
        
        # Configure armies based on player setup
        players = setup_data.get('players', [])
        if players:
            # Set up turn order based on player configuration
            turn_order = []
            for player in players:
                army_name = player.get('color', 'RED')
                try:
                    army = Army[army_name]
                    turn_order.append(army)
                except KeyError:
                    app_logger.warning(f"Invalid army color: {army_name}, using RED")
                    turn_order.append(Army.RED)
            
            board.turn_order = turn_order
            board.current_turn = turn_order[0] if turn_order else Army.RED
        
        # Set initial funds (default starting funds from properties)
        board.red_funds = 10000  # Starting funds for testing
        board.blue_funds = 10000
        
        # Create manager and store game
        mngr = GameManager(config_game, board)
        mngr.app_logger = app_logger
        games[token] = mngr
        
        app_logger.info(f"Game created successfully: {token}")
        return {
            'success': True,
            'token': token,
            'map': map_id,
            'players': len(players)
        }
        
    except Exception as e:
        app_logger.error(f"Failed to create game with setup: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('troop_info')
def troop_info_rpc(token: str) -> Dict[str, Any]:
    """Get troop information for the game"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    
    mngr = game_load(token)
    return {
        'red_troops': mngr.board.total_red_troops,
        'blue_troops': mngr.board.total_blue_troops
    }

@log_rpc_performance
@jsonrpc.method('message')
def message_rpc(token: str, message: str) -> Dict[str, Any]:
    """Send a message to the game log"""
    app_logger.info(f"Game message {token}: {message}")
    return {'success': True, 'message': message}

@log_rpc_performance
@jsonrpc.method('game_delete')
def game_delete_rpc(token: str) -> Dict[str, Any]:
    """Delete a game"""
    # Import here to avoid circular imports
    from core.game_utils import games
    
    if token in games:
        del games[token]
        app_logger.info(f"Deleted game: {token}")
        return {'success': True}
    return {'success': False, 'error': 'Game not found'}

@log_rpc_performance
@jsonrpc.method('game_create')
def game_create_rpc(token: str) -> Dict[str, Any]:
    """Create a new game with default settings"""
    # Import here to avoid circular imports
    from core.game_utils import game_load, games
    
    mngr = game_load(token)
    games[token] = mngr
    app_logger.info(f"Created game: {token}")
    return {'success': True, 'token': token}

@log_rpc_performance
@jsonrpc.method('game_board')
def game_board_rpc(token: str) -> Dict[str, Any]:
    """Get the current game board state"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    
    mngr = game_load(token)
    
    # Convert board to dictionary format for frontend
    grid_data = []
    for i, tile in enumerate(mngr.board.grid):
        x = i % mngr.board.width
        y = i // mngr.board.width
        
        tile_data = {
            'x': x,
            'y': y,
            'type': tile.mapTile.type.name if (tile.mapTile and hasattr(tile.mapTile.type, 'name')) else 'PLAIN',
            'army': tile.mapTile.army.name if (tile.mapTile and tile.mapTile.army) else None,
            'unit': None
        }
        
        if tile.unit:
            from core.api_response import APIResponse
            tile_data['unit'] = APIResponse.unit_info(tile.unit)
            
        grid_data.append(tile_data)
    
    return {
        'width': mngr.board.width,
        'height': mngr.board.height,
        'grid': grid_data,
        'current_turn': mngr.board.current_turn.name if mngr.board.current_turn else 'RED',
        'days': mngr.board.days,
        'red_funds': mngr.board.red_funds,
        'blue_funds': mngr.board.blue_funds,
        'game_active': mngr.board.game_active
    }

@log_rpc_performance
@jsonrpc.method('army_end_turn')
def army_end_turn_rpc(token: str) -> Dict[str, Any]:
    """End the current army's turn"""
    # Import here to avoid circular imports
    from core.game_utils import game_load, games
    from core.api_response import APIResponse
    
    mngr = game_load(token)
    
    try:
        previous_turn = mngr.board.current_turn.name if mngr.board.current_turn else 'RED'
        
        # End turn and process next army
        mngr.army_end_turn()
        
        # Save game state
        games[token] = mngr
        
        # Log the turn change
        log_game_event(app_logger, 'TURN_ENDED', {
            'token': token,
            'previous_army': previous_turn,
            'new_army': mngr.board.current_turn.name if mngr.board.current_turn else 'RED',
            'day': mngr.board.days
        })
        
        # Get turn order as army names
        turn_order_names = []
        for player_id in mngr.board.turn_order:
            army = mngr.board.get_army_for_player(player_id)
            if army:
                turn_order_names.append(army.name)
        
        return APIResponse.success(
            data={
                'previous_turn': previous_turn,
                'current_turn': mngr.board.current_turn.name if mngr.board.current_turn else 'RED',
                'day': mngr.board.days,
                'turn_order': turn_order_names
            },
            message=f"Turn ended. Now {mngr.board.current_turn.name if mngr.board.current_turn else 'RED'}'s turn.",
            context=APIResponse.game_context(mngr)
        )
        
    except Exception as e:
        app_logger.error(f"Error ending turn for {token}: {e}")
        return APIResponse.error(str(e), code='TURN_END_ERROR')

@log_rpc_performance  
@jsonrpc.method('tile')
def tile_rpc(token: str, x: int, y: int) -> Dict[str, Any]:
    """Get information about a specific tile"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    
    mngr = game_load(token)
    
    if not validate_coordinates(x, y, mngr.board.width, mngr.board.height):
        return {'error': 'Invalid coordinates'}
    
    index = y * mngr.board.width + x
    tile = mngr.board.grid[index]
    
    # Get tile type from mapTile
    tile_type = "PLAIN"  # default
    if tile.mapTile and hasattr(tile.mapTile.type, 'name'):
        tile_type = tile.mapTile.type.name
    
    tile_info = {
        'x': x,
        'y': y,
        'type': tile_type,
        'army': tile.mapTile.army.name if (tile.mapTile and tile.mapTile.army) else None,
        'unit': None
    }
    
    if tile.unit:
        # Get unit config for range information
        from config import Config
        config = Config()
        unit_config = config.units.get(tile.unit.type.name)
        
        tile_info['unit'] = {
            'type': tile.unit.type.name,
            'army': tile.unit.army.name,
            'health': tile.unit.status.hp,
            'fuel': tile.unit.status.fuel,
            'ammo': tile.unit.status.ammo,
            'moved': getattr(tile.unit.status, 'moved', False),
            'id': getattr(tile.unit, 'id', 'unknown'),
            'rangemax': unit_config.rangemax if unit_config else 0
        }
    
    return tile_info

@log_rpc_performance
@jsonrpc.method('capture_tile')
def capture_tile_rpc(token: str, x: int, y: int) -> Dict[str, Any]:
    """Attempt to capture a tile"""
    # Import here to avoid circular imports
    from core.game_utils import game_load, games
    
    mngr = game_load(token)
    
    try:
        result = mngr.capture_tile(x, y)
        
        if result.get('success'):
            # Log the capture
            log_game_event(app_logger, 'PROPERTY_CAPTURED', {
                'token': token,
                'army': mngr.board.current_turn.name,
                'position': (x, y),
                'property_type': result.get('property_type', 'unknown')
            })
            
            # Save game state
            games[token] = mngr
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error capturing tile at ({x},{y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('unit_create')
def unit_create_rpc(token: str, unit_type: str, x: int, y: int, army: str = None) -> Dict[str, Any]:
    """Create a new unit at the specified position
    
    Args:
        token: Game token
        unit_type: Type of unit to create
        x: X coordinate
        y: Y coordinate
        army: Army name (optional, defaults to current turn)
    """
    # Import here to avoid circular imports
    from core.game_utils import game_load, games
    from core.api_response import RPCResponseBuilder
    
    mngr = game_load(token)
    
    try:
        # Use provided army or default to current turn
        if army is None:
            current_turn = mngr.board.current_turn
            if current_turn is None:
                # Fallback to player 0's army if no current turn set
                army = mngr.board.player_to_army.get(0, Army.RED).name
            else:
                army = current_turn.name
        unit = mngr.unit_create(army, unit_type, x, y)
        
        # Build response
        response_builder = RPCResponseBuilder(mngr)
        response = response_builder.unit_create_response(unit_type, x, y, unit)
        
        # Log unit creation
        log_game_event(app_logger, 'UNIT_CREATED', {
            'token': token,
            'army': army,
            'unit_type': unit_type,
            'x': x,
            'y': y,
            'cost': getattr(unit, 'cost', 0)
        })
        
        # Save game state
        games[token] = mngr
        
        return response
        
    except Exception as e:
        app_logger.error(f"Error creating unit {unit_type} at ({x},{y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('unit_move')
def unit_move_rpc(token: str, from_x: int, from_y: int, to_x: int, to_y: int) -> Dict[str, Any]:
    """Move a unit from one position to another"""
    # Import here to avoid circular imports
    from core.game_utils import game_load, games
    
    mngr = game_load(token)
    
    try:
        result = mngr.unit_move(from_x, from_y, to_x, to_y)
        
        if result.get('success'):
            # Log unit movement
            log_game_event(app_logger, 'UNIT_MOVED', {
                'token': token,
                'army': mngr.board.current_turn.name,
                'from_pos': (from_x, from_y),
                'to_pos': (to_x, to_y),
                'fuel_used': result.get('fuel_used', 0)
            })
            
            # Save game state
            games[token] = mngr
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error moving unit from ({from_x},{from_y}) to ({to_x},{to_y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('unit_select')
def unit_select_rpc(token: str, x: int, y: int) -> Dict[str, Any]:
    """Select a unit and get its available actions"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    from core.api_response import RPCResponseBuilder
    
    mngr = game_load(token)
    
    try:
        # Call the manager method to update selection state
        mngr.unit_select(x, y)
        
        # Build comprehensive response
        response_builder = RPCResponseBuilder(mngr)
        return response_builder.unit_select_response(x, y)
        
    except Exception as e:
        app_logger.error(f"Error selecting unit at ({x},{y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('unit_attack')
def unit_attack_rpc(token: str, attacker_x: int, attacker_y: int, target_x: int, target_y: int) -> Dict[str, Any]:
    """Have one unit attack another"""
    # Import here to avoid circular imports
    from core.game_utils import game_load, games
    
    mngr = game_load(token)
    
    try:
        result = mngr.unit_attack(attacker_x, attacker_y, target_x, target_y)
        
        if result.get('success'):
            # Log combat
            log_game_event(app_logger, 'COMBAT_OCCURRED', {
                'token': token,
                'attacker_pos': (attacker_x, attacker_y),
                'target_pos': (target_x, target_y),
                'damage_dealt': result.get('damage_dealt', 0),
                'counter_damage': result.get('counter_damage', 0)
            })
            
            # Save game state
            games[token] = mngr
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error in combat at ({attacker_x},{attacker_y}) -> ({target_x},{target_y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('unit_load')
def unit_load_rpc(token: str, cargo_x: int, cargo_y: int, transport_x: int, transport_y: int) -> Dict[str, Any]:
    """Load a unit into a transport"""
    # Import here to avoid circular imports
    from core.game_utils import game_load, games
    
    mngr = game_load(token)
    
    try:
        result = mngr.unit_load(cargo_x, cargo_y, transport_x, transport_y)
        
        if result.get('success'):
            # Save game state
            games[token] = mngr
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error loading unit at ({cargo_x},{cargo_y}) into transport at ({transport_x},{transport_y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('unit_unload')
def unit_unload_rpc(token: str, transport_x: int, transport_y: int, unload_x: int, unload_y: int) -> Dict[str, Any]:
    """Unload a unit from a transport"""
    # Import here to avoid circular imports
    from core.game_utils import game_load, games
    
    mngr = game_load(token)
    
    try:
        result = mngr.unit_unload(transport_x, transport_y, unload_x, unload_y)
        
        if result.get('success'):
            # Save game state
            games[token] = mngr
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error unloading from transport at ({transport_x},{transport_y}) to ({unload_x},{unload_y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

# Additional RPC methods for enhanced functionality

@log_rpc_performance
@jsonrpc.method('get_unload_positions_internal')
def get_unload_positions_internal_rpc(token: str, transport_x: int, transport_y: int) -> Dict[str, Any]:
    """Get valid unload positions for a transport (internal method)"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        result = mngr.get_unload_positions_internal(transport_x, transport_y)
        return result
        
    except Exception as e:
        app_logger.error(f"Error getting unload positions for transport at ({transport_x},{transport_y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('get_unload_positions')
def get_unload_positions_rpc(token: str, transport_x: int, transport_y: int) -> List[Tuple[int, int]]:
    """Get valid unload positions for a transport"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        result = mngr.get_unload_positions(transport_x, transport_y)
        return result
        
    except Exception as e:
        app_logger.error(f"Error getting unload positions for transport at ({transport_x},{transport_y}) for {token}: {e}")
        return []

@log_rpc_performance
@jsonrpc.method('damage_estimate')
def damage_estimate_rpc(token: str, attacker_x: int, attacker_y: int, target_x: int, target_y: int) -> Dict[str, Any]:
    """Estimate damage between two units"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        result = mngr.damage_estimate(attacker_x, attacker_y, target_x, target_y)
        return result
        
    except Exception as e:
        app_logger.error(f"Error estimating damage from ({attacker_x},{attacker_y}) to ({target_x},{target_y}) for {token}: {e}")
        return {'error': str(e)}

@log_rpc_performance
@jsonrpc.method('check_turn')
def check_turn_rpc(token: str, army: str = None) -> Dict[str, Any]:
    """Check turn status and game information"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    from core.map_system import Army
    from core.api_response import APIResponse
    
    mngr = game_load(token)
    
    try:
        # Get current turn info
        current_turn_army = mngr.board.current_turn
        current_turn_name = current_turn_army.name if hasattr(current_turn_army, 'name') else str(current_turn_army)
        
        # Get turn order as army names
        turn_order_names = []
        for player_id in mngr.board.turn_order:
            player_army = mngr.board.get_army_for_player(player_id)
            if player_army:
                turn_order_names.append(player_army.name)
        
        result = {
            'current_turn': current_turn_name,
            'turn_order': turn_order_names,
            'day': mngr.board.days,
            'game_active': mngr.board.game_active
        }
        
        # If army is specified, check if it's their turn and count units
        if army:
            army_enum = Army[army]
            is_turn = mngr.board.current_turn == army_enum
            
            # Count active units for the army
            active_units = 0
            available_actions = 0
            
            for tile in mngr.board.grid:
                if tile.unit and tile.unit.army == army_enum:
                    active_units += 1
                    if not getattr(tile.unit.status, 'moved', False):
                        available_actions += 1
            
            result.update({
                'is_turn': is_turn,
                'requested_army': army,
                'active_units': active_units,
                'available_actions': available_actions
            })
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error checking turn for army {army} in {token}: {e}")
        return APIResponse.error(str(e), code='INVALID_ARMY')

@log_rpc_performance
@jsonrpc.method('damage_preview')
def damage_preview_rpc(token: str, attacker_x: int, attacker_y: int, target_x: int, target_y: int) -> Dict[str, Any]:
    """Get detailed damage preview for combat"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        # Use enhanced combat system if available
        if hasattr(mngr, 'enhanced_combat'):
            result = mngr.enhanced_combat.get_combat_preview(attacker_x, attacker_y, target_x, target_y)
        else:
            result = mngr.damage_estimate(attacker_x, attacker_y, target_x, target_y)
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error getting damage preview from ({attacker_x},{attacker_y}) to ({target_x},{target_y}) for {token}: {e}")
        return {'error': str(e)}

# Movement and validation methods

@log_rpc_performance
@jsonrpc.method('movement_preview')
def movement_preview_rpc(token: str, x: int, y: int) -> Dict[str, Any]:
    """Get movement preview for a unit"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        result = mngr.get_movement_preview(x, y)
        return result
        
    except Exception as e:
        app_logger.error(f"Error getting movement preview for unit at ({x},{y}) for {token}: {e}")
        return {'error': str(e)}

@log_rpc_performance
@jsonrpc.method('unit_valid_moves')
def unit_valid_moves_rpc(token: str, x: int, y: int) -> List[Tuple[int, int]]:
    """Get valid moves for a unit"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        result = mngr.get_valid_moves(x, y)
        return result
        
    except Exception as e:
        app_logger.error(f"Error getting valid moves for unit at ({x},{y}) for {token}: {e}")
        return []

@log_rpc_performance
@jsonrpc.method('validate_movement')
def validate_movement_rpc(token: str, from_x: int, from_y: int, to_x: int, to_y: int) -> Dict[str, Any]:
    """Validate if a movement is legal"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        result = mngr.validate_movement(from_x, from_y, to_x, to_y)
        return result
        
    except Exception as e:
        app_logger.error(f"Error validating movement from ({from_x},{from_y}) to ({to_x},{to_y}) for {token}: {e}")
        return {'valid': False, 'error': str(e)}

# Production and economy methods

@log_rpc_performance
@jsonrpc.method('produce_unit')
def produce_unit_rpc(token: str, unit_type: str, x: int, y: int) -> Dict[str, Any]:
    """Produce a unit at a factory"""
    # Import here to avoid circular imports
    from core.game_utils import game_load, games
    
    mngr = game_load(token)
    
    try:
        result = mngr.produce_unit(unit_type, x, y)
        
        if result.get('success'):
            # Log unit production
            log_game_event(app_logger, 'UNIT_PRODUCED', {
                'token': token,
                'army': mngr.board.current_turn.name,
                'unit_type': unit_type,
                'factory_pos': (x, y),
                'cost': result.get('cost', 0)
            })
            
            # Save game state
            games[token] = mngr
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error producing unit {unit_type} at ({x},{y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('get_production_options')
def get_production_options_rpc(token: str, x: int, y: int) -> Dict[str, Any]:
    """Get available units for production at a factory"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        # Get current player's army
        current_player_id = mngr.board_v2.current_player
        army_enum = mngr.board_v2.get_army_for_player(current_player_id)
        if not army_enum:
            return {'available_units': [], 'error': 'No army found for current player'}
            
        result = mngr.get_production_options(x, y, army_enum)
        return result
        
    except Exception as e:
        app_logger.error(f"Error getting production options at ({x},{y}) for {token}: {e}")
        return {'available_units': [], 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('get_army_economy')
def get_army_economy_rpc(token: str, army: str = None) -> Dict[str, Any]:
    """Get economic information for an army (defaults to current player)"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    from core.map_system import Army
    
    mngr = game_load(token)
    
    try:
        if army:
            army_enum = Army[army]
        else:
            # Use current player's army
            current_player_id = mngr.board_v2.current_player
            army_enum = mngr.board_v2.get_army_for_player(current_player_id)
            if not army_enum:
                return {'error': 'No army found for current player'}
                
        result = mngr.get_army_economy(army_enum)
        return result
        
    except Exception as e:
        app_logger.error(f"Error getting economy for army {army} in {token}: {e}")
        return {'error': str(e)}

@log_rpc_performance
@jsonrpc.method('get_army_facilities')
def get_army_facilities_rpc(token: str, army: str = None) -> Dict[str, Any]:
    """Get facilities owned by an army (defaults to current player)"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    from core.map_system import Army
    
    mngr = game_load(token)
    
    try:
        if army:
            army_enum = Army[army]
        else:
            # Use current player's army
            current_player_id = mngr.board_v2.current_player
            army_enum = mngr.board_v2.get_army_for_player(current_player_id)
            if not army_enum:
                return {'error': 'No army found for current player'}
                
        result = mngr.get_army_facilities(army_enum)
        return result
        
    except Exception as e:
        app_logger.error(f"Error getting facilities for army {army} in {token}: {e}")
        return {'error': str(e)}

@log_rpc_performance
@jsonrpc.method('can_afford_unit')
def can_afford_unit_rpc(token: str, unit_type: str, army: str = None) -> Dict[str, Any]:
    """Check if an army can afford a specific unit (defaults to current player)"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    from core.map_system import Army
    
    mngr = game_load(token)
    
    try:
        if army:
            army_enum = Army[army]
        else:
            # Use current player's army
            current_player_id = mngr.board_v2.current_player
            army_enum = mngr.board_v2.get_army_for_player(current_player_id)
            if not army_enum:
                return {'can_afford': False, 'error': 'No army found for current player'}
                
        can_afford = mngr.can_afford_unit(unit_type, army_enum)
        return {'can_afford': can_afford}
        
    except Exception as e:
        app_logger.error(f"Error checking if army {army} can afford {unit_type} in {token}: {e}")
        return {'can_afford': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('get_unit_costs')
def get_unit_costs_rpc(token: str) -> Dict[str, Any]:
    """Get cost information for all unit types"""
    try:
        # Import unit cost data and config
        from core.unit import UnitType
        from config import Config
        
        cfg = Config()
        costs = {}
        for unit_type in UnitType:
            config = cfg.units[unit_type.name]
            costs[unit_type.name] = config.cost
            
        return {'unit_costs': costs}
        
    except Exception as e:
        app_logger.error(f"Error getting unit costs for {token}: {e}")
        return {'error': str(e)}

@log_rpc_performance
@jsonrpc.method('unit_move_enhanced')
def unit_move_enhanced_rpc(token: str, from_x: int, from_y: int, to_x: int, to_y: int) -> Dict[str, Any]:
    """Enhanced unit movement with transport and validation support"""
    # Import here to avoid circular imports
    from core.game_utils import game_load, games
    
    mngr = game_load(token)
    
    try:
        # Use enhanced movement if available, otherwise fall back to regular movement
        if hasattr(mngr, 'enhanced_movement'):
            result = mngr.enhanced_movement.move_unit(from_x, from_y, to_x, to_y)
        else:
            result = mngr.unit_move(from_x, from_y, to_x, to_y)
        
        if result.get('success'):
            # Log enhanced movement
            log_game_event(app_logger, 'UNIT_MOVED_ENHANCED', {
                'token': token,
                'army': mngr.board.current_turn.name,
                'from_pos': (from_x, from_y),
                'to_pos': (to_x, to_y),
                'fuel_used': result.get('fuel_used', 0),
                'enhanced': True
            })
            
            # Save game state
            games[token] = mngr
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error in enhanced movement from ({from_x},{from_y}) to ({to_x},{to_y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('unit_delete')
def unit_delete_rpc(token: str, x: int, y: int) -> Dict[str, Any]:
    """Delete a unit at the specified position"""
    # Import here to avoid circular imports
    from core.game_utils import game_load, games
    
    mngr = game_load(token)
    
    if not validate_coordinates(x, y, mngr.board.width, mngr.board.height):
        return {'success': False, 'error': 'Invalid coordinates'}
    
    try:
        # Check if there's a unit at the position
        index = y * mngr.board.width + x
        tile = mngr.board.grid[index]
        
        if not tile.unit:
            return {'success': False, 'error': 'No unit at specified position'}
        
        # Check if the unit belongs to the current player
        current_player = mngr.board.current_turn
        if tile.unit.army != current_player:
            return {'success': False, 'error': 'Can only delete your own units'}
        
        # Store unit info before deletion
        unit_type_name = tile.unit.type.name
        
        # Delete the unit
        tile.unit = None
        
        # Log the deletion
        log_game_event(app_logger, 'UNIT_DELETED', {
            'token': token,
            'army': current_player.name,
            'position': (x, y),
            'unit_type': unit_type_name
        })
        
        # Save game state
        games[token] = mngr
        
        return {'success': True, 'message': 'Unit deleted successfully'}
        
    except Exception as e:
        app_logger.error(f"Error deleting unit at ({x},{y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('game_create_test')
def game_create_test_rpc(token: str, use_optimized: bool = True) -> Dict[str, Any]:
    """Create a test game with high starting funds for testing purposes"""
    try:
        # Import here to avoid circular imports
        from core.game_utils import games
        from core.game_factory import GameFactory
        
        # Create a standard game then set high starting funds
        mngr, msg = GameFactory.create_standard_game(map_name="test")
        
        # Set high starting funds for all players (50k for testing)
        for player_id in range(mngr.board.player_manager.get_player_count()):
            mngr.board.player_funds[player_id] = 50000
        
        # Set up the game manager properly
        mngr.app_logger = app_logger
        
        # Store the game
        games[token] = mngr
        
        # Log the game creation
        log_game_event(app_logger, 'GAME_CREATED_TEST', {
            'token': token,
            'starting_funds': 50000,
            'map': "test",
            'optimized': use_optimized
        })
        
        return {
            'success': True, 
            'message': f'Test game created with high funds: {msg}',
            'starting_funds': 50000,
            'width': mngr.board.width,
            'height': mngr.board.height
        }
        
    except Exception as e:
        app_logger.error(f"Error creating test game {token}: {e}")
        return {'success': False, 'error': str(e)}
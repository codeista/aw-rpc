"""
Combat RPC Methods Module
Contains all combat-related JSONRPC methods
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
@jsonrpc.method('get_attack_targets')
def get_attack_targets_rpc(token: str, attacker_x: int, attacker_y: int) -> Dict[str, Any]:
    """Get valid attack targets for a unit"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        # Get unit at position
        index = attacker_y * mngr.board.width + attacker_x
        tile = mngr.board.grid[index]
        
        if not tile.unit:
            return {'targets': [], 'error': 'No unit at specified position'}
        
        attacker = tile.unit
        targets = []
        
        # Get unit's attack range (simplified)
        attack_range = getattr(attacker, 'attack_range', 1)
        
        # Check all tiles within attack range
        for target_y in range(max(0, attacker_y - attack_range), 
                            min(mngr.board.height, attacker_y + attack_range + 1)):
            for target_x in range(max(0, attacker_x - attack_range), 
                                min(mngr.board.width, attacker_x + attack_range + 1)):
                
                # Skip self
                if target_x == attacker_x and target_y == attacker_y:
                    continue
                
                target_index = target_y * mngr.board.width + target_x
                target_tile = mngr.board.grid[target_index]
                
                # Check if there's an enemy unit
                if target_tile.unit and target_tile.unit.army != attacker.army:
                    target_info = {
                        'position': (target_x, target_y),
                        'type': target_tile.unit.type.name,
                        'army': target_tile.unit.army.name,
                        'health': target_tile.unit.status.health
                    }
                    targets.append(target_info)
        
        return {
            'targets': targets,
            'attacker_range': attack_range,
            'total_targets': len(targets)
        }
        
    except Exception as e:
        app_logger.error(f"Error getting attack targets for unit at ({attacker_x},{attacker_y}) for {token}: {e}")
        return {'targets': [], 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('combat_preview')
def combat_preview_rpc(token: str, attacker_x: int, attacker_y: int, target_x: int, target_y: int, skip_range_check: bool = False) -> Dict[str, Any]:
    """Get detailed combat preview between two units"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        # Note: skip_range_check is ignored for now as the enhanced combat system
        # doesn't support it. This is used for hypothetical combat calculations.
        
        # Use enhanced combat system if available
        if hasattr(mngr, 'enhanced_combat'):
            preview = mngr.enhanced_combat.get_combat_preview(attacker_x, attacker_y, target_x, target_y)
            # Convert CombatPreview dataclass to dict
            result = {
                'damage': {
                    'attacker_damage': preview.attacker_damage,
                    'defender_damage': preview.counter_damage,
                    'counter_damage': preview.counter_damage,
                    'can_counter': preview.can_counter,
                    'attacker_hp_after': preview.attacker_hp_after,
                    'defender_hp_after': preview.defender_hp_after,
                    'attacker_destroyed': preview.attacker_destroyed,
                    'defender_destroyed': preview.defender_destroyed,
                    'terrain_bonus': preview.terrain_bonus,
                    'damage_range': preview.luck_range,
                    'ammo_warning': preview.ammo_warning
                }
            }
        else:
            # Fallback to basic damage estimation
            damage_tuple = mngr.damage_estimate(attacker_x, attacker_y, target_x, target_y)
            # Convert tuple to dict format
            result = {
                'damage': {
                    'attacker_damage': damage_tuple[0],
                    'defender_damage': damage_tuple[1],
                    'counter_damage': damage_tuple[1],
                    'can_counter': damage_tuple[1] > 0
                }
            }
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error getting combat preview from ({attacker_x},{attacker_y}) to ({target_x},{target_y}) for {token}: {e}")
        return {'error': str(e)}

@log_rpc_performance
@jsonrpc.method('unit_attack_enhanced')
def unit_attack_enhanced_rpc(token: str, attacker_x: int, attacker_y: int, target_x: int, target_y: int) -> Dict[str, Any]:
    """Enhanced unit attack with detailed combat results"""
    # Import here to avoid circular imports
    from core.game_utils import game_load, games
    
    mngr = game_load(token)
    
    try:
        # Use enhanced combat system if available
        if hasattr(mngr, 'enhanced_combat'):
            result = mngr.enhanced_combat.execute_combat(attacker_x, attacker_y, target_x, target_y)
        else:
            result = mngr.unit_attack(attacker_x, attacker_y, target_x, target_y)
        
        if result.get('success'):
            # Log detailed combat result
            from middleware.error_handling import log_game_event
            log_game_event('ENHANCED_COMBAT', token, {
                'attacker_pos': (attacker_x, attacker_y),
                'target_pos': (target_x, target_y),
                'damage_dealt': result.get('damage_dealt', 0),
                'counter_damage': result.get('counter_damage', 0),
                'attacker_destroyed': result.get('attacker_destroyed', False),
                'target_destroyed': result.get('target_destroyed', False)
            })
            
            # Save game state
            games[token] = mngr
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error in enhanced combat from ({attacker_x},{attacker_y}) to ({target_x},{target_y}) for {token}: {e}")
        return {'success': False, 'error': str(e)}

@log_rpc_performance
@jsonrpc.method('get_damage_chart')
def get_damage_chart_rpc(token: str) -> Dict[str, Any]:
    """Get damage chart for all unit type combinations"""
    try:
        # Import damage calculation data
        from core.unit import UnitType
        from core.enhanced_combat_system import EnhancedCombatSystem
        
        damage_chart = {}
        
        # Generate damage chart for all unit combinations
        for attacker_type in UnitType:
            damage_chart[attacker_type.name] = {}
            for target_type in UnitType:
                # For now, return a placeholder value
                # TODO: Implement proper damage chart lookup
                base_damage = 55  # Default damage value
                damage_chart[attacker_type.name][target_type.name] = base_damage
        
        return {
            'damage_chart': damage_chart,
            'unit_types': [unit_type.name for unit_type in UnitType]
        }
        
    except Exception as e:
        app_logger.error(f"Error getting damage chart for {token}: {e}")
        return {'error': str(e)}

@log_rpc_performance
@jsonrpc.method('get_movement_costs')
def get_movement_costs_rpc(token: str, unit_x: int, unit_y: int) -> Dict[str, Any]:
    """Get movement costs for a unit across different terrain types"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        index = unit_y * mngr.board.width + unit_x
        tile = mngr.board.grid[index]
        
        if not tile.unit:
            return {'error': 'No unit at specified position'}
        
        unit = tile.unit
        movement_costs = {}
        
        # Get movement costs for different terrain types
        from core.map_system import MapType
        for terrain_type in MapType:
            # This would typically come from unit configuration
            cost = 1  # Simplified - actual cost would depend on unit type and terrain
            movement_costs[terrain_type.name] = cost
        
        return {
            'unit_type': unit.type.name,
            'movement_costs': movement_costs,
            'max_movement': getattr(unit, 'movement_range', 2)
        }
        
    except Exception as e:
        app_logger.error(f"Error getting movement costs for unit at ({unit_x},{unit_y}) for {token}: {e}")
        return {'error': str(e)}

@log_rpc_performance
@jsonrpc.method('get_movement_highlights')
def get_movement_highlights_rpc(token: str, unit_x: int, unit_y: int) -> Dict[str, Any]:
    """Get movement highlights and attack range for a unit"""
    # Import here to avoid circular imports
    from core.game_utils import game_load
    
    mngr = game_load(token)
    
    try:
        index = unit_y * mngr.board.width + unit_x
        tile = mngr.board.grid[index]
        
        if not tile.unit:
            return {'error': 'No unit at specified position'}
        
        unit = tile.unit
        
        # Get valid movement positions
        movement_positions = mngr.get_valid_moves(unit_x, unit_y)
        
        # Get attack positions from each movement position
        attack_positions = set()
        attack_range = getattr(unit, 'attack_range', 1)
        
        for move_x, move_y in movement_positions:
            # Add attack positions from this movement position
            for dy in range(-attack_range, attack_range + 1):
                for dx in range(-attack_range, attack_range + 1):
                    attack_x = move_x + dx
                    attack_y = move_y + dy
                    
                    if (0 <= attack_x < mngr.board.width and 
                        0 <= attack_y < mngr.board.height):
                        attack_positions.add((attack_x, attack_y))
        
        # Find enemy units in attack range
        enemy_targets = []
        for attack_x, attack_y in attack_positions:
            attack_index = attack_y * mngr.board.width + attack_x
            attack_tile = mngr.board.grid[attack_index]
            
            if attack_tile.unit and attack_tile.unit.army != unit.army:
                enemy_targets.append({
                    'position': (attack_x, attack_y),
                    'type': attack_tile.unit.type.name,
                    'health': attack_tile.unit.status.health
                })
        
        return {
            'movement_positions': movement_positions,
            'attack_positions': list(attack_positions),
            'enemy_targets': enemy_targets,
            'unit_stats': {
                'type': unit.type.name,
                'movement_range': getattr(unit, 'movement_range', 2),
                'attack_range': attack_range,
                'health': unit.status.health,
                'fuel': unit.status.fuel
            }
        }
        
    except Exception as e:
        app_logger.error(f"Error getting movement highlights for unit at ({unit_x},{unit_y}) for {token}: {e}")
        return {'error': str(e)}
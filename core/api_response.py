"""
API Response Builder Utilities
Provides consistent response formatting for all RPC methods
"""

from typing import Dict, Any, Optional, List
from datetime import datetime


class APIResponse:
    """Standard API response builder for consistent formatting"""
    
    @staticmethod
    def success(data: Dict[str, Any], message: str = "Success", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build a successful response"""
        response = {
            "success": True,
            "data": data,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if context:
            response["context"] = context
            
        return response
    
    @staticmethod
    def error(error: str, code: str = "ERROR", details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build an error response"""
        response = {
            "success": False,
            "error": error,
            "code": code,
            "timestamp": datetime.now().isoformat()
        }
        
        if details:
            response["details"] = details
            
        return response
    
    @staticmethod
    def game_context(manager) -> Dict[str, Any]:
        """Extract game context from manager"""
        # Get current player info
        current_player = manager.board.current_player
        
        # Count units per player
        player_units = {}
        for player_id in manager.board.turn_order:
            player_units[player_id] = 0
            
        for tile in manager.board.grid:
            if tile.unit:
                player_id = tile.unit.player_id
                if player_id in player_units:
                    player_units[player_id] += 1
        
        return {
            "current_player": current_player,
            "day": manager.board.days,
            "game_active": manager.board.game_active,
            "player_funds": dict(manager.board.player_funds),
            "player_units": player_units
        }
    
    @staticmethod
    def unit_info(unit) -> Dict[str, Any]:
        """Convert unit to API format"""
        if not unit:
            return None
            
        # Check if unit can capture (only INFANTRY and MECH)
        can_capture = unit.type.name in ['INFANTRY', 'MECH'] and not getattr(unit.status, 'action_taken', False)
        
        return {
            "id": getattr(unit, 'id', 'unknown'),
            "type": unit.type.name,
            "player_id": getattr(unit, 'player_id', None),
            "x": getattr(unit, 'x', None),
            "y": getattr(unit, 'y', None),
            "hp": unit.status.hp,
            "fuel": unit.status.fuel,
            "ammo": unit.status.ammo,
            "can_move": getattr(unit, 'can_move', False),
            "can_attack": getattr(unit, 'can_attack', False),
            "can_capture": can_capture,
            "has_moved": getattr(unit.status, 'has_moved_this_turn', False),
            "done": getattr(unit.status, 'action_taken', False),
            "action_taken": getattr(unit.status, 'action_taken', False),
            "is_hidden": getattr(unit, 'is_hidden', False)
        }
    
    @staticmethod
    def tile_info(tile, x: int, y: int) -> Dict[str, Any]:
        """Convert tile to API format"""
        # Get tile type from mapTile if available
        tile_type = "PLAIN"  # default
        if tile.mapTile and hasattr(tile.mapTile.type, 'name'):
            tile_type = tile.mapTile.type.name
        
        info = {
            "x": x,
            "y": y,
            "type": tile_type,
            "defense": getattr(tile, 'defense_rating', 0)
        }
        
        if tile.mapTile and tile.mapTile.army:
            info["army"] = tile.mapTile.army.name
            
        if tile.unit:
            info["unit"] = APIResponse.unit_info(tile.unit)
            
        return info
    
    @staticmethod
    def movement_info(valid_moves: List[tuple], attack_positions: List[tuple]) -> Dict[str, Any]:
        """Format movement and attack information"""
        return {
            "movement_tiles": [{"x": x, "y": y} for x, y in valid_moves],
            "attack_tiles": [{"x": x, "y": y} for x, y in attack_positions],
            "total_moves": len(valid_moves),
            "total_attacks": len(attack_positions)
        }


class RPCResponseBuilder:
    """Specialized response builder for RPC methods"""
    
    def __init__(self, manager):
        self.manager = manager
        
    def unit_select_response(self, x: int, y: int) -> Dict[str, Any]:
        """Build response for unit_select RPC"""
        tile = self.manager.tile_at(x, y)
        unit = tile.unit
        
        data = {
            "tile": APIResponse.tile_info(tile, x, y),
            "selected": True
        }
        
        if unit and unit.army == self.manager.board.current_turn:
            # Get available actions for the unit
            actions = []
            
            if unit.can_move and not getattr(unit.status, 'moved', False):
                actions.append("move")
                data["movement_range"] = self.manager.get_valid_moves(x, y)
                
            if getattr(unit, 'can_attack', True) and not getattr(unit.status, 'has_attacked', False):
                actions.append("attack")
                # Get attack targets
                targets = []
                attack_range = getattr(unit, 'attack_range', 1)
                
                for dy in range(-attack_range, attack_range + 1):
                    for dx in range(-attack_range, attack_range + 1):
                        tx, ty = x + dx, y + dy
                        if (0 <= tx < self.manager.board.width and 
                            0 <= ty < self.manager.board.height):
                            target_tile = self.manager.tile_at(tx, ty)
                            if target_tile.unit and target_tile.unit.army != unit.army:
                                targets.append({"x": tx, "y": ty, 
                                              "unit": APIResponse.unit_info(target_tile.unit)})
                
                data["attack_targets"] = targets
            
            # Check if unit can capture
            if unit.type.name in ['INFANTRY', 'MECH'] and tile.mapTile and tile.mapTile.type.name in ['CITY', 'BASE', 'PORT', 'AIRPORT', 'HQ']:
                if tile.mapTile.army != unit.army:
                    actions.append("capture")
                    data["can_capture"] = True
                    
            # Check for special actions
            if unit.type.name == 'APC':
                actions.append("resupply")
            elif unit.type.name in ['LANDER', 'CRUISER', 'APC', 'BLACK_BOAT']:
                if len(getattr(unit, 'cargo', [])) > 0:
                    actions.append("unload")
                    
            data["available_actions"] = actions
            data["unit"] = APIResponse.unit_info(unit)
            
        return APIResponse.success(
            data=data,
            message=f"Selected tile at ({x}, {y})",
            context=APIResponse.game_context(self.manager)
        )
    
    def unit_create_response(self, unit_type: str, x: int, y: int, unit) -> Dict[str, Any]:
        """Build response for unit_create RPC"""
        data = {
            "unit": APIResponse.unit_info(unit),
            "position": {"x": x, "y": y},
            "cost": getattr(unit, 'cost', 0),
            "remaining_funds": self.manager.board.player_funds.get(unit.player_id, 0)
        }
        
        return APIResponse.success(
            data=data,
            message=f"Created {unit_type} at ({x}, {y})",
            context=APIResponse.game_context(self.manager)
        )
    
    def movement_response(self, from_x: int, from_y: int, to_x: int, to_y: int, fuel_used: int) -> Dict[str, Any]:
        """Build response for unit movement"""
        tile = self.manager.tile_at(to_x, to_y)
        unit = tile.unit
        
        data = {
            "from": {"x": from_x, "y": from_y},
            "to": {"x": to_x, "y": to_y},
            "fuel_used": fuel_used,
            "unit": APIResponse.unit_info(unit),
            "remaining_fuel": unit.status.fuel if unit else 0
        }
        
        return APIResponse.success(
            data=data,
            message=f"Unit moved from ({from_x}, {from_y}) to ({to_x}, {to_y})",
            context=APIResponse.game_context(self.manager)
        )
    
    def combat_response(self, attacker_result: Dict, defender_result: Dict) -> Dict[str, Any]:
        """Build response for combat results"""
        data = {
            "attacker": attacker_result,
            "defender": defender_result,
            "combat_complete": True
        }
        
        return APIResponse.success(
            data=data,
            message="Combat executed successfully",
            context=APIResponse.game_context(self.manager)
        )
# enhanced_movement_validation.py
"""
Enhanced Movement Validation System for AW-RPC
Fixes invalid moves and provides comprehensive validation
"""

from typing import Tuple, Optional, List, Set
from dataclasses import dataclass
from gameboard import GameBoard, GameTile
from unit import Unit, UnitClass
from map_system import MapType, MOVEMENT_COST, INF, TERRAIN_DEFENSE
from dijkstra import dijkstra


@dataclass
class MovementValidationResult:
    """Result of movement validation check"""
    valid: bool
    reason: str = ""
    MOVEMENT_COST: int = 0
    fuel_required: int = 0
    path_found: bool = False
    blocked_by: Optional[str] = None


class EnhancedMovementValidator:
    """Enhanced movement validation with comprehensive checks"""
    
    def __init__(self, board: GameBoard):
        self.board = board
    
    def validate_movement(self, unit: Unit, from_x: int, from_y: int, to_x: int, to_y: int) -> MovementValidationResult:
        """
        Comprehensive movement validation
        Returns detailed result with validation status and reasons
        """
        
        # 1. Basic coordinate validation
        result = self._validate_coordinates(from_x, from_y, to_x, to_y)
        if not result.valid:
            return result
        
        # 2. Check if unit exists at source
        result = self._validate_unit_exists(from_x, from_y, unit)
        if not result.valid:
            return result
        
        # 3. Check if trying to move to same position
        if from_x == to_x and from_y == to_y:
            return MovementValidationResult(False, "Cannot move to the same position")
        
        # 4. Check if destination is occupied
        result = self._validate_destination_clear(to_x, to_y, unit)
        if not result.valid:
            return result
        
        # 5. Check unit can move (hasn't moved this turn)
        if not unit.can_move:
            return MovementValidationResult(False, "Unit has already moved this turn")
        
        # 6. Check fuel availability
        result = self._validate_fuel_availability(unit, from_x, from_y, to_x, to_y)
        if not result.valid:
            return result
        
        # 7. Check movement range
        result = self._validate_movement_range(unit, from_x, from_y, to_x, to_y)
        if not result.valid:
            return result
        
        # 8. Check terrain accessibility and pathfinding
        result = self._validate_pathfinding(unit, from_x, from_y, to_x, to_y)
        if not result.valid:
            return result
        
        # All validations passed
        return MovementValidationResult(
            valid=True,
            reason="Movement is valid",
            MOVEMENT_COST=result.MOVEMENT_COST,
            fuel_required=result.fuel_required,
            path_found=True
        )
    
    def _validate_coordinates(self, from_x: int, from_y: int, to_x: int, to_y: int) -> MovementValidationResult:
        """Validate coordinates are within board bounds"""
        
        # Check source coordinates
        if not (0 <= from_x < self.board.width and 0 <= from_y < self.board.height):
            return MovementValidationResult(
                False, 
                f"Source coordinates ({from_x}, {from_y}) are out of bounds. " +
                f"Board size: {self.board.width}x{self.board.height}"
            )
        
        # Check destination coordinates
        if not (0 <= to_x < self.board.width and 0 <= to_y < self.board.height):
            return MovementValidationResult(
                False, 
                f"Destination coordinates ({to_x}, {to_y}) are out of bounds. " +
                f"Board size: {self.board.width}x{self.board.height}"
            )
        
        return MovementValidationResult(True)
    
    def _validate_unit_exists(self, x: int, y: int, expected_unit: Unit) -> MovementValidationResult:
        """Validate unit exists at source coordinates"""
        
        tile = self._get_tile(x, y)
        if not tile.unit:
            return MovementValidationResult(False, f"No unit found at ({x}, {y})")
        
        if tile.unit.id != expected_unit.id:
            return MovementValidationResult(
                False, 
                f"Different unit at ({x}, {y}). Expected {expected_unit.type.name}, " +
                f"found {tile.unit.type.name}"
            )
        
        return MovementValidationResult(True)
    
    def _validate_destination_clear(self, x: int, y: int, moving_unit: Unit) -> MovementValidationResult:
        """Validate destination tile is not occupied by another unit"""
        
        tile = self._get_tile(x, y)
        if tile.unit:
            if tile.unit.army == moving_unit.army:
                return MovementValidationResult(
                    False, 
                    f"Destination ({x}, {y}) occupied by friendly {tile.unit.type.name}",
                    blocked_by=f"friendly_{tile.unit.type.name}"
                )
            else:
                return MovementValidationResult(
                    False, 
                    f"Destination ({x}, {y}) occupied by enemy {tile.unit.type.name}",
                    blocked_by=f"enemy_{tile.unit.type.name}"
                )
        
        return MovementValidationResult(True)
    
    def _validate_fuel_availability(self, unit: Unit, from_x: int, from_y: int, to_x: int, to_y: int) -> MovementValidationResult:
        """Validate unit has enough fuel for the movement"""
        
        # Calculate minimum fuel needed (Manhattan distance)
        min_fuel_needed = abs(to_x - from_x) + abs(to_y - from_y)
        
        if unit.status.fuel < min_fuel_needed:
            return MovementValidationResult(
                False, 
                f"Insufficient fuel. Need at least {min_fuel_needed}, have {unit.status.fuel}",
                fuel_required=min_fuel_needed
            )
        
        return MovementValidationResult(True, fuel_required=min_fuel_needed)
    
    def _validate_movement_range(self, unit: Unit, from_x: int, from_y: int, to_x: int, to_y: int) -> MovementValidationResult:
        """Validate movement is within unit's movement range"""
        
        # Calculate Manhattan distance
        distance = abs(to_x - from_x) + abs(to_y - from_y)
        
        if distance > unit.status.move:
            return MovementValidationResult(
                False, 
                f"Distance {distance} exceeds movement range {unit.status.move}",
                MOVEMENT_COST=distance
            )
        
        return MovementValidationResult(True, MOVEMENT_COST=distance)
    
    def _validate_pathfinding(self, unit: Unit, from_x: int, from_y: int, to_x: int, to_y: int) -> MovementValidationResult:
        """Validate path exists considering terrain and obstacles"""
        
        try:
            source_tile = self._get_tile(from_x, from_y)
            target_tile = self._get_tile(to_x, to_y)
            
            # Use Dijkstra's algorithm for pathfinding
            pathfinding_cost = dijkstra(self.board, source_tile, target_tile)
            
            if pathfinding_cost == INF:
                return MovementValidationResult(
                    False, 
                    f"No valid path found from ({from_x}, {from_y}) to ({to_x}, {to_y}). " +
                    "Path may be blocked by terrain or units.",
                    path_found=False
                )
            
            if pathfinding_cost > unit.status.move:
                return MovementValidationResult(
                    False, 
                    f"Path requires {pathfinding_cost} movement, but unit only has {unit.status.move}",
                    MOVEMENT_COST=pathfinding_cost,
                    path_found=True
                )
            
            # Check if unit can traverse the destination terrain
            dest_tile = self._get_tile(to_x, to_y)
            if not self._can_unit_traverse_terrain(unit, dest_tile.mapTile.type):
                return MovementValidationResult(
                    False, 
                    f"Unit type {unit.type.name} cannot traverse {dest_tile.mapTile.type.name} terrain"
                )
            
            return MovementValidationResult(
                True, 
                "Valid path found",
                MOVEMENT_COST=pathfinding_cost,
                path_found=True
            )
            
        except Exception as e:
            # Fallback to simple distance check if pathfinding fails
            distance = abs(to_x - from_x) + abs(to_y - from_y)
            if distance <= unit.status.move:
                return MovementValidationResult(
                    True, 
                    f"Path validation failed, using simple distance check: {e}",
                    MOVEMENT_COST=distance,
                    path_found=False
                )
            else:
                return MovementValidationResult(
                    False, 
                    f"Path validation failed and distance {distance} > range {unit.status.move}: {e}"
                )
    
    def _can_unit_traverse_terrain(self, unit: Unit, terrain_type: MapType) -> bool:
        """Check if unit can traverse specific terrain type"""
        
        try:
            unit_class_index = unit.status.cls.value
            movement_cost = MOVEMENT_COST[terrain_type][unit_class_index]
            return movement_cost != INF
        except (KeyError, IndexError):
            # Unknown terrain or unit class - default to false for safety
            return False
    
    def _get_tile(self, x: int, y: int) -> GameTile:
        """Get tile at coordinates with bounds checking"""
        if not (0 <= x < self.board.width and 0 <= y < self.board.height):
            raise ValueError(f"Coordinates ({x}, {y}) out of bounds")
        
        index = x + y * self.board.width
        return self.board.grid[index]
    
    def get_valid_moves(self, unit: Unit, from_x: int, from_y: int) -> List[Tuple[int, int]]:
        """Get list of all valid move destinations for a unit"""
        
        valid_moves = []
        
        # Check all tiles within movement range
        max_range = min(unit.status.move, unit.status.fuel)
        
        for y in range(max(0, from_y - max_range), min(self.board.height, from_y + max_range + 1)):
            for x in range(max(0, from_x - max_range), min(self.board.width, from_x + max_range + 1)):
                
                # Skip the current position
                if x == from_x and y == from_y:
                    continue
                
                # Quick distance check
                distance = abs(x - from_x) + abs(y - from_y)
                if distance > max_range:
                    continue
                
                # Full validation check
                result = self.validate_movement(unit, from_x, from_y, x, y)
                if result.valid:
                    valid_moves.append((x, y))
        
        return valid_moves
    
    def get_movement_preview(self, unit: Unit, from_x: int, from_y: int, to_x: int, to_y: int) -> dict:
        """Get detailed movement preview information"""
        
        result = self.validate_movement(unit, from_x, from_y, to_x, to_y)
        
        preview = {
            "valid": result.valid,
            "reason": result.reason,
            "MOVEMENT_COST": result.MOVEMENT_COST,
            "fuel_required": result.fuel_required,
            "fuel_remaining": max(0, unit.status.fuel - result.fuel_required),
            "path_found": result.path_found,
            "blocked_by": result.blocked_by,
            "terrain_info": self._get_terrain_info(to_x, to_y) if result.valid else None
        }
        
        return preview
    
    def _get_terrain_info(self, x: int, y: int) -> dict:
        """Get terrain information for a tile"""
        
        tile = self._get_tile(x, y)
        terrain_type = tile.mapTile.type
        
        return {
            "type": terrain_type.name,
            "defense_stars": TERRAIN_DEFENSE.get(terrain_type, 0),
            "is_property": terrain_type in {MapType.CITY, MapType.FACTORY, MapType.AIRPORT, MapType.PORT},
            "owner": tile.mapTile.army.name if tile.mapTile.army else "Neutral"
        }


# Integration with existing GameManager
def enhance_game_manager_movement():
    """
    Enhanced movement methods to integrate with existing GameManager
    Add these methods to your GameManager class
    """
    
    def enhanced_unit_move(self, x: int, y: int, x2: int, y2: int) -> Unit:
        """Enhanced unit movement with comprehensive validation"""
        
        # Initialize validator
        validator = EnhancedMovementValidator(self.board)
        
        # Get the unit
        unit = self._validate_unit_exists(x, y)
        self._validate_unit_turn(unit)
        self._validate_game_active()
        
        # Comprehensive movement validation
        result = validator.validate_movement(unit, x, y, x2, y2)
        
        if not result.valid:
            raise ValueError(f"Invalid movement: {result.reason}")
        
        # Execute the movement
        unit = self.unit_remove(x, y)
        self.unit_place(unit, x2, y2)
        
        # Consume fuel based on actual movement cost
        self._consume_fuel(unit, result.MOVEMENT_COST)
        
        # Update unit state
        unit.can_move = False
        if unit.is_indirect():
            unit.can_attack = False
        
        # Update selection
        self.unit_deselect()
        self.unit_select(x2, y2)
        
        return unit
    
    def enhanced_unit_can_move_to(self, unit: Unit, x: int, y: int) -> bool:
        """Enhanced movement validation for UI indicators"""
        
        # Get unit's current position
        tile = self.tile_from_unit(unit)
        if not tile:
            return False
        
        validator = EnhancedMovementValidator(self.board)
        result = validator.validate_movement(unit, tile.x, tile.y, x, y)
        
        return result.valid
    
    def get_unit_valid_moves(self, unit: Unit) -> List[Tuple[int, int]]:
        """Get all valid moves for a unit"""
        
        tile = self.tile_from_unit(unit)
        if not tile:
            return []
        
        validator = EnhancedMovementValidator(self.board)
        return validator.get_valid_moves(unit, tile.x, tile.y)
    
    def get_movement_preview(self, x: int, y: int, x2: int, y2: int) -> dict:
        """Get movement preview for UI"""
        
        unit = self._validate_unit_exists(x, y)
        validator = EnhancedMovementValidator(self.board)
        
        return validator.get_movement_preview(unit, x, y, x2, y2)

    return {
        'enhanced_unit_move': enhanced_unit_move,
        'enhanced_unit_can_move_to': enhanced_unit_can_move_to,
        'get_unit_valid_moves': get_unit_valid_moves,
        'get_movement_preview': get_movement_preview
    }
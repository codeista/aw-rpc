"""
Input Validation System for AW-RPC
Prevents crashes and ensures data integrity
"""

import re
from functools import wraps
from typing import Tuple, List, Any
from enhanced_logging import log_error

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class InputValidator:
    """Centralized input validation"""
    
    # Valid game constants
    VALID_ARMIES = {'RED', 'BLUE', 'GREEN', 'YELLOW', 'GREY'}
    VALID_UNIT_TYPES = {
        'INFANTRY', 'MECH', 'RECON', 'TANK', 'MEDIUMTANK', 'NEOTANK', 'MEGATANK',
        'ARTILLERY', 'MISSILE', 'ROCKET', 'ANTIAIR', 'APC', 'FIGHTER', 'BOMBER',
        'BCOPTER', 'TCOPTER', 'BATTLESHIP', 'CRUISER', 'LANDER', 'SUB', 'CARRIER',
        'BLACKBOAT', 'STEALTH', 'BLACKBOMB', 'PIPERUNNER'
    }
    
    @staticmethod
    def validate_token(token: str) -> str:
        """Validate game token format"""
        if not token or not isinstance(token, str):
            raise ValidationError("Token must be a non-empty string")
        
        # Remove whitespace
        token = token.strip()
        
        # Check length
        if len(token) < 3 or len(token) > 50:
            raise ValidationError("Token must be 3-50 characters long")
        
        # Check format - alphanumeric, underscore, dash only
        if not re.match(r'^[a-zA-Z0-9_-]+$', token):
            raise ValidationError("Token contains invalid characters. Use only letters, numbers, - and _")
        
        return token
    
    @staticmethod
    def validate_coordinates(x: Any, y: Any, max_x: int = 50, max_y: int = 50) -> Tuple[int, int]:
        """Validate and convert coordinates to integers"""
        try:
            x, y = int(x), int(y)
        except (ValueError, TypeError):
            raise ValidationError(f"Coordinates must be integers, got x={type(x).__name__}, y={type(y).__name__}")
        
        if x < 0 or y < 0:
            raise ValidationError(f"Coordinates cannot be negative: ({x},{y})")
        
        if x >= max_x or y >= max_y:
            raise ValidationError(f"Coordinates ({x},{y}) out of bounds (max: {max_x-1},{max_y-1})")
        
        return x, y
    
    @staticmethod
    def validate_army(army: Any) -> str:
        """Validate army parameter"""
        if not isinstance(army, str):
            raise ValidationError(f"Army must be a string, got {type(army).__name__}")
        
        army = army.upper().strip()
        
        if army not in InputValidator.VALID_ARMIES:
            raise ValidationError(f"Invalid army '{army}'. Valid armies: {sorted(InputValidator.VALID_ARMIES)}")
        
        return army
    
    @staticmethod
    def validate_unit_type(unit_type: Any) -> str:
        """Validate unit type parameter"""
        if not isinstance(unit_type, str):
            raise ValidationError(f"Unit type must be a string, got {type(unit_type).__name__}")
        
        unit_type = unit_type.upper().strip()
        
        if unit_type not in InputValidator.VALID_UNIT_TYPES:
            raise ValidationError(f"Invalid unit type '{unit_type}'. See /api/browse for valid types")
        
        return unit_type
    
    @staticmethod
    def validate_index(index: Any, max_value: int = 10) -> int:
        """Validate array index parameter"""
        try:
            index = int(index)
        except (ValueError, TypeError):
            raise ValidationError(f"Index must be an integer, got {type(index).__name__}")
        
        if index < 0:
            raise ValidationError(f"Index cannot be negative: {index}")
        
        if index >= max_value:
            raise ValidationError(f"Index {index} too large (max: {max_value-1})")
        
        return index

# Validation decorators for RPC methods
def validate_token_param(func):
    """Decorator to validate token parameter"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Token is always the first parameter
        if args:
            token = args[0]
            try:
                validated_token = InputValidator.validate_token(token)
                args = (validated_token,) + args[1:]
            except ValidationError as e:
                log_error(token, func.__name__, str(e), "Token validation failed")
                raise
        elif 'token' in kwargs:
            try:
                kwargs['token'] = InputValidator.validate_token(kwargs['token'])
            except ValidationError as e:
                log_error(kwargs.get('token', 'invalid'), func.__name__, str(e), "Token validation failed")
                raise
        
        return func(*args, **kwargs)
    return wrapper

def validate_coordinates_params(func):
    """Decorator to validate coordinate parameters"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = args[0] if args else kwargs.get('token', 'unknown')
        
        try:
            # Handle positional arguments
            if len(args) >= 3:  # token, x, y at minimum
                x, y = InputValidator.validate_coordinates(args[1], args[2])
                args = (args[0], x, y) + args[3:]
            
            # Handle additional coordinate pairs (x2, y2)
            if len(args) >= 5:  # token, x, y, x2, y2
                x2, y2 = InputValidator.validate_coordinates(args[3], args[4])
                args = args[:3] + (x2, y2) + args[5:]
            
            # Handle keyword arguments
            if 'x' in kwargs and 'y' in kwargs:
                kwargs['x'], kwargs['y'] = InputValidator.validate_coordinates(kwargs['x'], kwargs['y'])
            
            if 'x2' in kwargs and 'y2' in kwargs:
                kwargs['x2'], kwargs['y2'] = InputValidator.validate_coordinates(kwargs['x2'], kwargs['y2'])
        
        except ValidationError as e:
            log_error(token, func.__name__, str(e), "Coordinate validation failed")
            raise
        
        return func(*args, **kwargs)
    return wrapper

def validate_army_param(func):
    """Decorator to validate army parameter"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = args[0] if args else kwargs.get('token', 'unknown')
        
        try:
            # Look for army in args (usually 2nd parameter after token)
            if len(args) >= 2 and isinstance(args[1], str) and args[1].upper() in InputValidator.VALID_ARMIES | {'RED', 'BLUE'}:
                army = InputValidator.validate_army(args[1])
                args = (args[0], army) + args[2:]
            
            # Look for army in kwargs
            if 'army' in kwargs:
                kwargs['army'] = InputValidator.validate_army(kwargs['army'])
        
        except ValidationError as e:
            log_error(token, func.__name__, str(e), "Army validation failed")
            raise
        
        return func(*args, **kwargs)
    return wrapper

def validate_unit_type_param(func):
    """Decorator to validate unit_type parameter"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = args[0] if args else kwargs.get('token', 'unknown')
        
        try:
            # Look for unit_type in args (usually 3rd parameter: token, army, unit_type)
            if len(args) >= 3 and isinstance(args[2], str):
                unit_type = InputValidator.validate_unit_type(args[2])
                args = args[:2] + (unit_type,) + args[3:]
            
            # Look for unit_type in kwargs
            if 'unit_type' in kwargs:
                kwargs['unit_type'] = InputValidator.validate_unit_type(kwargs['unit_type'])
        
        except ValidationError as e:
            log_error(token, func.__name__, str(e), "Unit type validation failed")
            raise
        
        return func(*args, **kwargs)
    return wrapper

def validate_all_params(func):
    """Comprehensive validation decorator - use this for most RPC methods"""
    @validate_token_param
    @validate_coordinates_params
    @validate_army_param
    @validate_unit_type_param
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

# Game state validation functions
def validate_game_active(manager):
    """Ensure game is still active"""
    if not getattr(manager.board, 'game_active', True):
        raise ValidationError("Game has ended. No further moves allowed.")

def validate_unit_exists(manager, x: int, y: int):
    """Ensure unit exists at coordinates"""
    unit = manager.unit_at(x, y)
    if not unit:
        raise ValidationError(f"No unit found at coordinates ({x},{y})")
    return unit

def validate_player_turn(manager, unit):
    """Ensure it's the correct player's turn"""
    if unit.army != manager.board.current_turn:
        raise ValidationError(f"It's {manager.board.current_turn.name}'s turn, not {unit.army.name}'s")

def validate_unit_can_act(unit, action: str):
    """Ensure unit can perform the requested action"""
    if action == "move" and not unit.can_move:
        raise ValidationError(f"{unit.type.name} cannot move this turn")
    elif action == "attack" and not unit.can_attack:
        raise ValidationError(f"{unit.type.name} cannot attack this turn")
    elif action == "capture" and not unit.can_capture:
        raise ValidationError(f"{unit.type.name} cannot capture this turn")

# Enhanced validation decorator for game manager methods
def validate_game_action(action_type: str):
    """Decorator for GameManager methods to validate game state"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, x: int, y: int, *args, **kwargs):
            try:
                # Basic game state validation
                validate_game_active(self)
                
                # Coordinate validation (already done by coordinate decorator)
                # Unit existence validation
                unit = validate_unit_exists(self, x, y)
                
                # Turn validation
                validate_player_turn(self, unit)
                
                # Action-specific validation
                if action_type in ["move", "attack", "capture"]:
                    validate_unit_can_act(unit, action_type)
                
                return func(self, x, y, *args, **kwargs)
            
            except ValidationError:
                raise  # Re-raise validation errors as-is
            except Exception as e:
                log_error(
                    getattr(self, 'current_token', 'unknown'),
                    func.__name__,
                    str(e),
                    f"Unexpected error during {action_type}"
                )
                raise
        
        return wrapper
    return decorator

# Example usage in manager.py:
# @validate_game_action("move")
# def unit_move(self, x: int, y: int, x2: int, y2: int) -> Unit:
#     # Your existing logic here
#     pass

# Example usage in app.py:
# @validate_all_params
# def unit_create_rpc(token: str, army: str, unit_type: str, x: int, y: int) -> dict:
#     # Your existing logic here
#     pass
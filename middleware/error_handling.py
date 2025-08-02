# Phase 1 Task 3: Enhanced Error Handling System
# Create new file: error_handling.py

"""
Enhanced error handling system for AW-RPC
Provides custom exceptions, validation, and error middleware
"""

import logging
import traceback
import functools
from flask import jsonify, request
from typing import Any, Dict, Optional, Tuple, Union
from dataclasses import dataclass


# =============================================================================
# CUSTOM EXCEPTION CLASSES
# =============================================================================

class AWRPCError(Exception):
    """Base exception class for AW-RPC game errors"""
    def __init__(self, message: str, error_code: str = "GENERAL_ERROR", 
                 http_status: int = 400, details: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.http_status = http_status
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response"""
        return {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(AWRPCError):
    """Raised when input validation fails"""
    def __init__(self, message: str, field: str = None, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            http_status=400,
            details={**(details or {}), "field": field} if field else details
        )


class GameStateError(AWRPCError):
    """Raised when game state is invalid"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="GAME_STATE_ERROR",
            http_status=409,
            details=details
        )


class UnitError(AWRPCError):
    """Raised when unit operations fail"""
    def __init__(self, message: str, unit_id: str = None, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="UNIT_ERROR",
            http_status=400,
            details={**(details or {}), "unit_id": unit_id} if unit_id else details
        )


class MovementError(AWRPCError):
    """Raised when movement is invalid"""
    def __init__(self, message: str, from_pos: Tuple[int, int] = None, 
                 to_pos: Tuple[int, int] = None, details: Optional[Dict] = None):
        error_details = details or {}
        if from_pos:
            error_details["from_position"] = {"x": from_pos[0], "y": from_pos[1]}
        if to_pos:
            error_details["to_position"] = {"x": to_pos[0], "y": to_pos[1]}
        
        super().__init__(
            message=message,
            error_code="MOVEMENT_ERROR",
            http_status=400,
            details=error_details
        )


class CombatError(AWRPCError):
    """Raised when combat operations fail"""
    def __init__(self, message: str, attacker_pos: Tuple[int, int] = None,
                 target_pos: Tuple[int, int] = None, details: Optional[Dict] = None):
        error_details = details or {}
        if attacker_pos:
            error_details["attacker_position"] = {"x": attacker_pos[0], "y": attacker_pos[1]}
        if target_pos:
            error_details["target_position"] = {"x": target_pos[0], "y": target_pos[1]}
        
        super().__init__(
            message=message,
            error_code="COMBAT_ERROR",
            http_status=400,
            details=error_details
        )


class TurnError(AWRPCError):
    """Raised when turn management fails"""
    def __init__(self, message: str, current_army: str = None, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="TURN_ERROR",
            http_status=403,
            details={**(details or {}), "current_army": current_army} if current_army else details
        )


class NotFoundError(AWRPCError):
    """Raised when requested resource is not found"""
    def __init__(self, message: str, resource_type: str = None, 
                 resource_id: str = None, details: Optional[Dict] = None):
        error_details = details or {}
        if resource_type:
            error_details["resource_type"] = resource_type
        if resource_id:
            error_details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            http_status=404,
            details=error_details
        )


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_coordinates(x: Any, y: Any, board_width: int, board_height: int) -> Tuple[int, int]:
    """Validate and convert coordinates"""
    try:
        x_int = int(x)
        y_int = int(y)
    except (ValueError, TypeError):
        raise ValidationError(
            f"Coordinates must be integers, got x={x}, y={y}",
            details={"provided_x": x, "provided_y": y}
        )
    
    if not (0 <= x_int < board_width):
        raise ValidationError(
            f"X coordinate {x_int} is out of bounds (0-{board_width-1})",
            field="x",
            details={"value": x_int, "min": 0, "max": board_width-1}
        )
    
    if not (0 <= y_int < board_height):
        raise ValidationError(
            f"Y coordinate {y_int} is out of bounds (0-{board_height-1})",
            field="y",
            details={"value": y_int, "min": 0, "max": board_height-1}
        )
    
    return x_int, y_int


def validate_army(army: Any) -> str:
    """Validate army parameter"""
    if not isinstance(army, str):
        raise ValidationError(
            f"Army must be a string, got {type(army).__name__}",
            field="army"
        )
    
    army_upper = army.upper()
    valid_armies = ["RED", "BLUE", "GREEN", "YELLOW", "GREY"]
    
    if army_upper not in valid_armies:
        raise ValidationError(
            f"Invalid army '{army}'. Must be one of: {', '.join(valid_armies)}",
            field="army",
            details={"provided": army, "valid_options": valid_armies}
        )
    
    return army_upper


def validate_unit_type(unit_type: Any) -> str:
    """Validate unit type parameter"""
    if not isinstance(unit_type, str):
        raise ValidationError(
            f"Unit type must be a string, got {type(unit_type).__name__}",
            field="unit_type"
        )
    
    unit_type_upper = unit_type.upper()
    valid_unit_types = [
        "INFANTRY", "MECH", "RECON", "TANK", "MEDIUMTANK", "NEOTANK", "MEGATANK",
        "APC", "ARTILLERY", "ROCKET", "ANTIAIR", "MISSILE", "FIGHTER", "BOMBER",
        "STEALTH", "BCOPTER", "TCOPTER", "BATTLESHIP", "CRUISER", "LANDER",
        "SUB", "CARRIER", "BLACKBOAT", "PIPERUNNER", "BLACKBOMB"
    ]
    
    if unit_type_upper not in valid_unit_types:
        raise ValidationError(
            f"Invalid unit type '{unit_type}'. Must be one of the supported unit types.",
            field="unit_type",
            details={"provided": unit_type, "valid_count": len(valid_unit_types)}
        )
    
    return unit_type_upper


def validate_token(token: Any) -> str:
    """Validate game token parameter"""
    if not isinstance(token, str):
        raise ValidationError(
            f"Token must be a string, got {type(token).__name__}",
            field="token"
        )
    
    if not token.strip():
        raise ValidationError("Token cannot be empty", field="token")
    
    if len(token) > 50:
        raise ValidationError(
            f"Token too long ({len(token)} chars), maximum 50 characters",
            field="token"
        )
    
    return token.strip()


def validate_message(message: Any) -> str:
    """Validate chat message parameter"""
    if not isinstance(message, str):
        raise ValidationError(
            f"Message must be a string, got {type(message).__name__}",
            field="message"
        )
    
    if len(message.strip()) == 0:
        raise ValidationError("Message cannot be empty", field="message")
    
    if len(message) > 500:
        raise ValidationError(
            f"Message too long ({len(message)} chars), maximum 500 characters",
            field="message"
        )
    
    return message.strip()


# =============================================================================
# DECORATOR FOR RPC METHOD VALIDATION
# =============================================================================

def validate_rpc_params(**validators):
    """Decorator to validate RPC method parameters"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Apply validators to kwargs
                for param_name, validator in validators.items():
                    if param_name in kwargs:
                        kwargs[param_name] = validator(kwargs[param_name])
                    else:
                        # Check if it's a required parameter
                        import inspect
                        sig = inspect.signature(func)
                        if param_name in sig.parameters:
                            param = sig.parameters[param_name]
                            if param.default == inspect.Parameter.empty:
                                raise ValidationError(
                                    f"Missing required parameter: {param_name}",
                                    field=param_name
                                )
                
                return func(*args, **kwargs)
            
            except AWRPCError:
                raise  # Re-raise our custom exceptions
            except Exception as e:
                # Convert unexpected exceptions to AWRPCError
                logging.error(f"Unexpected error in {func.__name__}: {str(e)}")
                logging.error(traceback.format_exc())
                raise AWRPCError(
                    f"Internal error in {func.__name__}",
                    error_code="INTERNAL_ERROR",
                    http_status=500
                )
        
        return wrapper
    return decorator


# =============================================================================
# ERROR HANDLER MIDDLEWARE
# =============================================================================

def setup_error_handlers(app):
    """Setup Flask error handlers"""
    
    @app.errorhandler(AWRPCError)
    def handle_awrpc_error(error):
        """Handle custom AW-RPC exceptions"""
        logging.warning(f"AW-RPC Error: {error.message}")
        response = jsonify(error.to_dict())
        response.status_code = error.http_status
        return response
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle generic bad request errors"""
        return jsonify({
            "error": True,
            "error_code": "BAD_REQUEST",
            "message": "Bad request",
            "details": {}
        }), 400
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle not found errors"""
        return jsonify({
            "error": True,
            "error_code": "NOT_FOUND",
            "message": "Resource not found",
            "details": {"path": request.path}
        }), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle internal server errors"""
        logging.error(f"Internal server error: {str(error)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error",
            "details": {}
        }), 500


# =============================================================================
# GAME STATE VALIDATION
# =============================================================================

def validate_game_active(game_manager):
    """Ensure game is active"""
    if not game_manager.board.game_active:
        raise GameStateError("Game has ended, no actions allowed")


def validate_unit_exists(game_manager, x: int, y: int):
    """Ensure unit exists at coordinates"""
    unit = game_manager.unit_at(x, y)
    if not unit:
        raise NotFoundError(
            f"No unit found at position ({x}, {y})",
            resource_type="unit",
            details={"position": {"x": x, "y": y}}
        )
    return unit


def validate_unit_ownership(unit, current_army):
    """Ensure unit belongs to current army"""
    if unit.army != current_army:
        raise TurnError(
            f"Unit belongs to {unit.army.name}, but it's {current_army.name}'s turn",
            current_army=current_army.name,
            details={"unit_army": unit.army.name}
        )


def validate_unit_can_act(unit, action_type: str):
    """Ensure unit can perform the specified action"""
    if action_type == "move" and not unit.can_move:
        raise UnitError(
            "Unit cannot move this turn",
            unit_id=str(unit.id),
            details={"action": action_type}
        )
    
    if action_type == "attack" and not unit.can_attack:
        raise UnitError(
            "Unit cannot attack this turn",
            unit_id=str(unit.id),
            details={"action": action_type}
        )
    
    if action_type == "capture" and not unit.can_capture:
        raise UnitError(
            "Unit cannot capture this turn",
            unit_id=str(unit.id),
            details={"action": action_type}
        )


# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('awrpc_errors.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create separate logger for game events
    game_logger = logging.getLogger('game_events')
    game_handler = logging.FileHandler('game_events.log')
    game_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    game_logger.addHandler(game_handler)
    game_logger.setLevel(logging.INFO)
    
    return game_logger


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def log_game_event(game_logger, event_type: str, details: Dict[str, Any]):
    """Log game events for debugging and analytics"""
    game_logger.info(f"{event_type}: {details}")


def safe_rpc_call(func):
    """Decorator to safely execute RPC calls with comprehensive error handling"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except AWRPCError:
            raise  # Re-raise our custom exceptions
        except Exception as e:
            # Log unexpected errors
            logging.error(f"Unexpected error in {func.__name__}: {str(e)}")
            logging.error(f"Args: {args}, Kwargs: {kwargs}")
            logging.error(traceback.format_exc())
            
            # Convert to our custom exception
            raise AWRPCError(
                f"Unexpected error occurred",
                error_code="INTERNAL_ERROR",
                http_status=500,
                details={"function": func.__name__}
            )
    
    return wrapper


# =============================================================================
# EXAMPLE USAGE IN RPC METHODS
# =============================================================================

"""
Example of how to use this error handling system in your RPC methods:

@validate_rpc_params(
    token=validate_token,
    x=lambda x: validate_coordinates(x, 0, board_width, board_height)[0],
    y=lambda y: validate_coordinates(0, y, board_width, board_height)[1],
    army=validate_army,
    unit_type=validate_unit_type
)
@safe_rpc_call
def unit_create_rpc(token: str, army: str, unit_type: str, x: int, y: int) -> dict:
    '''Create a unit with comprehensive error handling'''
    mngr = game_load(token)
    
    # Validate game state
    validate_game_active(mngr)
    
    # Validate coordinates (already done by decorator, but shown for completeness)
    x_int, y_int = validate_coordinates(x, y, mngr.board.width, mngr.board.height)
    
    # Check if tile is empty
    if mngr.unit_at(x_int, y_int):
        raise UnitError(
            f"Tile at ({x_int}, {y_int}) is already occupied",
            details={"position": {"x": x_int, "y": y_int}}
        )
    
    # Perform the action
    unit = mngr.unit_create(army, unit_type, x_int, y_int)
    game_save(mngr, token)
    ws_board_update(token)
    
    # Log the event
    log_game_event(game_logger, "UNIT_CREATED", {
        "token": token,
        "army": army,
        "unit_type": unit_type,
        "position": {"x": x_int, "y": y_int},
        "unit_id": str(unit.id)
    })
    
    return jsons.dump(mngr.tile_get(x_int, y_int))
"""
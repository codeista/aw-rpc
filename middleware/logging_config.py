# logging_config.py
"""
Centralized logging configuration for AW-RPC
Fixes all logging issues and provides structured logging
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
import json


def setup_application_logging(log_level=logging.INFO):
    """
    Configure comprehensive logging for AW-RPC application
    
    Returns:
        tuple: (app_logger, game_logger, error_logger)
    """
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Clear any existing handlers to avoid duplicates
    logging.getLogger().handlers.clear()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    game_formatter = logging.Formatter(
        '%(asctime)s - GAME - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 1. Console Handler (for development)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # 2. Application Log Handler (rotating)
    app_handler = logging.handlers.RotatingFileHandler(
        log_dir / "awrpc_app.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(app_handler)
    
    # 3. Error Log Handler (errors only)
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "awrpc_errors.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # 4. Game Events Handler (separate logger)
    game_handler = logging.handlers.RotatingFileHandler(
        log_dir / "game_events.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    game_handler.setLevel(logging.INFO)
    game_handler.setFormatter(game_formatter)
    
    # Create specialized loggers
    game_logger = logging.getLogger('game_events')
    game_logger.setLevel(logging.INFO)
    game_logger.addHandler(game_handler)
    game_logger.propagate = False  # Don't send to root logger
    
    # Get application logger
    app_logger = logging.getLogger('awrpc')
    
    # Log startup
    app_logger.info("Logging system initialized")
    app_logger.info(f"Log files location: {log_dir.absolute()}")
    
    return app_logger, game_logger


class GameEventLogger:
    """Structured logging for game events"""
    
    def __init__(self):
        self.logger = logging.getLogger('game_events')
    
    def log_game_created(self, token, army_count=2):
        """Log game creation"""
        self.logger.info(f"GAME_CREATED token={token} armies={army_count}")
    
    def log_game_deleted(self, token):
        """Log game deletion"""
        self.logger.info(f"GAME_DELETED token={token}")
    
    def log_unit_created(self, token, army, unit_type, x, y, cost=0):
        """Log unit creation"""
        self.logger.info(f"UNIT_CREATED token={token} army={army} type={unit_type} pos=({x},{y}) cost={cost}")
    
    def log_unit_deleted(self, token, army, unit_type, x, y):
        """Log unit deletion"""
        self.logger.info(f"UNIT_DELETED token={token} army={army} type={unit_type} pos=({x},{y})")
    
    def log_unit_moved(self, token, army, unit_type, from_pos, to_pos, fuel_used=0):
        """Log unit movement"""
        self.logger.info(f"UNIT_MOVED token={token} army={army} type={unit_type} from={from_pos} to={to_pos} fuel_used={fuel_used}")
    
    def log_unit_attack(self, token, attacker_army, attacker_type, attacker_pos, 
                       defender_army, defender_type, defender_pos, damage_dealt=0):
        """Log unit attack"""
        self.logger.info(f"UNIT_ATTACK token={token} attacker={attacker_army}:{attacker_type}@{attacker_pos} "
                        f"defender={defender_army}:{defender_type}@{defender_pos} damage={damage_dealt}")
    
    def log_property_captured(self, token, army, property_type, pos):
        """Log property capture"""
        self.logger.info(f"PROPERTY_CAPTURED token={token} army={army} type={property_type} pos={pos}")
    
    def log_turn_ended(self, token, army, turn_number, funds=0):
        """Log turn end"""
        self.logger.info(f"TURN_ENDED token={token} army={army} turn={turn_number} funds={funds}")
    
    def log_game_ended(self, token, winner_army, reason=""):
        """Log game end"""
        self.logger.info(f"GAME_ENDED token={token} winner={winner_army} reason={reason}")
    
    def log_error(self, token, action, error_msg):
        """Log game-related errors"""
        self.logger.error(f"GAME_ERROR token={token} action={action} error={error_msg}")


class PerformanceLogger:
    """Log performance metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger('performance')
        
        # Setup performance log file
        log_dir = Path("logs")
        perf_handler = logging.handlers.RotatingFileHandler(
            log_dir / "performance.log",
            maxBytes=5*1024*1024,
            backupCount=2,
            encoding='utf-8'
        )
        perf_formatter = logging.Formatter(
            '%(asctime)s - PERF - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        perf_handler.setFormatter(perf_formatter)
        self.logger.addHandler(perf_handler)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
    
    def log_rpc_call(self, method_name, duration_ms, success=True, params_count=0):
        """Log RPC call performance"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"RPC_CALL method={method_name} duration={duration_ms}ms status={status} params={params_count}")
    
    def log_database_operation(self, operation, duration_ms, success=True):
        """Log database operation performance"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"DB_OPERATION op={operation} duration={duration_ms}ms status={status}")


def log_function_call(logger_name='awrpc'):
    """Decorator to log function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            start_time = datetime.now()
            
            try:
                logger.debug(f"CALL_START {func.__name__} args={len(args)} kwargs={len(kwargs)}")
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds() * 1000
                logger.debug(f"CALL_END {func.__name__} duration={duration:.2f}ms")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                logger.error(f"CALL_ERROR {func.__name__} duration={duration:.2f}ms error={str(e)}")
                raise
        return wrapper
    return decorator


def cleanup_old_logs(days_to_keep=7):
    """Clean up log files older than specified days"""
    log_dir = Path("logs")
    if not log_dir.exists():
        return
    
    cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
    
    for log_file in log_dir.glob("*.log*"):
        if log_file.stat().st_mtime < cutoff_time:
            try:
                log_file.unlink()
                print(f"Deleted old log file: {log_file}")
            except OSError as e:
                print(f"Failed to delete {log_file}: {e}")


if __name__ == "__main__":
    # Test the logging system
    app_logger, game_logger = setup_application_logging()
    
    # Test different log levels
    app_logger.info("This is an info message")
    app_logger.warning("This is a warning message")
    app_logger.error("This is an error message")
    
    # Test game event logging
    game_event_logger = GameEventLogger()
    game_event_logger.log_game_created("test_token_123", 2)
    game_event_logger.log_unit_created("test_token_123", "RED", "INFANTRY", 1, 1, 1000)
    
    # Test performance logging
    perf_logger = PerformanceLogger()
    perf_logger.log_rpc_call("unit_create", 45.2, True, 5)
    
    print("Logging test complete. Check the logs/ directory for output files.")

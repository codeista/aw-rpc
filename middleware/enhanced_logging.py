"""
Simple Enhanced Logging for AW-RPC
Minimal version to get started quickly
"""

import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
if not os.path.exists("logs"):
    os.makedirs("logs")

# Setup movement logger
movement_logger = logging.getLogger('movement')
movement_logger.setLevel(logging.INFO)
movement_handler = logging.FileHandler('logs/movement.log')
movement_formatter = logging.Formatter(
    '%(asctime)s | %(token)s | MOVE | %(army)s %(unit_type)s | %(from_pos)s → %(to_pos)s | Fuel: %(fuel_used)s/%(fuel_remaining)s'
)
movement_handler.setFormatter(movement_formatter)
movement_logger.addHandler(movement_handler)
movement_logger.propagate = False

# Setup combat logger
combat_logger = logging.getLogger('combat')
combat_logger.setLevel(logging.INFO)
combat_handler = logging.FileHandler('logs/combat.log')
combat_formatter = logging.Formatter(
    '%(asctime)s | %(token)s | ATTACK | %(attacker)s @ %(att_pos)s → %(defender)s @ %(def_pos)s | DMG: %(damage)s | Result: %(result)s'
)
combat_handler.setFormatter(combat_formatter)
combat_logger.addHandler(combat_handler)
combat_logger.propagate = False

# Setup game events logger
events_logger = logging.getLogger('game_events')
events_logger.setLevel(logging.INFO)
events_handler = logging.FileHandler('logs/game_events.log')
events_formatter = logging.Formatter(
    '%(asctime)s | %(token)s | %(event_type)s | %(army)s | %(details)s'
)
events_handler.setFormatter(events_formatter)
events_logger.addHandler(events_handler)
events_logger.propagate = False

def log_movement(token, army, unit_type, from_x, from_y, to_x, to_y, fuel_used=0, fuel_remaining=0):
    """Log unit movement"""
    extra = {
        'token': token,
        'army': army,
        'unit_type': unit_type,
        'from_pos': f'({from_x},{from_y})',
        'to_pos': f'({to_x},{to_y})',
        'fuel_used': fuel_used,
        'fuel_remaining': fuel_remaining
    }
    movement_logger.info("Unit moved", extra=extra)

def log_attack(token, attacker_army, attacker_type, att_x, att_y, 
               defender_army, defender_type, def_x, def_y, damage, result=""):
    """Log combat action"""
    extra = {
        'token': token,
        'attacker': f"{attacker_army} {attacker_type}",
        'att_pos': f'({att_x},{att_y})',
        'defender': f"{defender_army} {defender_type}",
        'def_pos': f'({def_x},{def_y})',
        'damage': damage,
        'result': result
    }
    combat_logger.info("Combat occurred", extra=extra)

def log_game_event(token, event_type, army, details):
    """Log general game events"""
    extra = {
        'token': token,
        'event_type': event_type,
        'army': army,
        'details': details
    }
    events_logger.info(f"{event_type}", extra=extra)

def log_error(token, operation, error_msg, traceback=""):
    """Log errors (for now, just print them)"""
    print(f"ERROR [{token}] {operation}: {error_msg}")
    if traceback:
        print(f"Traceback: {traceback}")

# Test function
def test_logging():
    """Test the logging system"""
    log_movement("test", "RED", "INFANTRY", 0, 0, 1, 0, 1, 98)
    log_attack("test", "RED", "INFANTRY", 1, 0, "BLUE", "TANK", 2, 0, 5, "Damaged")
    log_game_event("test", "TURN_END", "RED", "Turn ended")
    print("✅ Logging test complete - check logs/ directory")

if __name__ == "__main__":
    test_logging()
#!/usr/bin/env python3
"""
Test script to verify movement highlights and action flow
Tests the complete flow: select → move → attack → highlights clear
"""

import time
import requests
import json

# Simple color codes without colorama
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'

Fore = Colors
Style = type('obj', (object,), {'RESET_ALL': Colors.RESET})

BASE_URL = "http://localhost:5000/rpc"
TOKEN = None

def rpc_call(method, params=None):
    """Make an RPC call"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    }
    
    response = requests.post(BASE_URL, json=payload)
    return response.json()

def print_test(test_name, passed, details=""):
    """Print test result"""
    if passed:
        print(f"{Fore.GREEN}✓ {test_name}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗ {test_name}{Style.RESET_ALL}")
    if details:
        print(f"  {Fore.YELLOW}{details}{Style.RESET_ALL}")

def check_highlights(board, expected_movement=0, expected_attack=0):
    """Check highlight counts on board"""
    movement_count = 0
    attack_count = 0
    highlighted_positions = []
    
    for tile in board['grid']:
        if tile.get('can_be_moved_to'):
            movement_count += 1
            highlighted_positions.append(f"Move: ({tile['x']},{tile['y']})")
        if tile.get('can_be_attacked'):
            attack_count += 1
            highlighted_positions.append(f"Attack: ({tile['x']},{tile['y']})")
    
    correct = movement_count == expected_movement and attack_count == expected_attack
    
    if not correct or highlighted_positions:
        details = f"Movement: {movement_count}/{expected_movement}, Attack: {attack_count}/{expected_attack}"
        if highlighted_positions:
            details += f"\n  Highlights: {', '.join(highlighted_positions[:5])}"
            if len(highlighted_positions) > 5:
                details += f" ... and {len(highlighted_positions)-5} more"
        return correct, details
    
    return correct, ""

def find_unit_position(board, unit_type=None, army=None):
    """Find a unit on the board"""
    for tile in board['grid']:
        if tile.get('unit'):
            unit = tile['unit']
            if (not unit_type or unit['type'] == unit_type) and \
               (not army or unit.get('player_id') == army):
                return tile['x'], tile['y']
    return None, None

def test_movement_highlights():
    """Test 1: Movement highlights appear and clear correctly"""
    print(f"\n{Fore.CYAN}=== Test 1: Movement Highlights ==={Style.RESET_ALL}")
    
    # Create test game
    TOKEN = 'highlight-test-1'
    result = rpc_call('game_create_test', {'token': TOKEN, 'use_optimized': True})
    
    # Add to params
    params_with_token = lambda p: {**p, 'token': TOKEN}
    
    # Get initial board
    result = rpc_call('get_game_board', params_with_token({}))
    board = result['result']['board']
    
    # Create a tank
    rpc_call('unit_create', params_with_token({
        'player_id': 0,
        'unit_type': 'TANK',
        'x': 3,
        'y': 3
    }))
    
    # End turn to allow movement
    rpc_call('army_end_turn', params_with_token({}))
    rpc_call('army_end_turn', params_with_token({}))
    
    # Select the tank
    result = rpc_call('unit_select', params_with_token({'x': 3, 'y': 3}))
    
    # Get movement range
    result = rpc_call('movement_range', params_with_token({'unit_x': 3, 'unit_y': 3}))
    movement_tiles = len(result['result'].get('moves', []))
    
    # Check board for highlights
    result = rpc_call('get_game_board', params_with_token({}))
    board = result['result']['board']
    
    passed, details = check_highlights(board, expected_movement=movement_tiles)
    print_test("Movement highlights shown after selection", movement_tiles > 0, 
               f"Found {movement_tiles} movement options")
    
    # Click empty space to deselect
    rpc_call('unit_select', params_with_token({'x': 0, 'y': 0}))
    
    # Check highlights cleared
    result = rpc_call('get_game_board', params_with_token({}))
    board = result['result']['board']
    
    passed, details = check_highlights(board, expected_movement=0)
    print_test("Movement highlights cleared after deselection", passed, details)

def test_move_attack_flow():
    """Test 2: Move → Attack flow without reselection"""
    print(f"\n{Fore.CYAN}=== Test 2: Move + Attack Flow ==={Style.RESET_ALL}")
    
    # Create test game
    TOKEN = 'highlight-test-2'
    result = rpc_call('game_create_test', {'token': TOKEN, 'use_optimized': True})
    
    params_with_token = lambda p: {**p, 'token': TOKEN}
    
    # Create attacker and target
    rpc_call('unit_create', params_with_token({
        'player_id': 0,
        'unit_type': 'TANK',
        'x': 2,
        'y': 2
    }))
    
    # End turn
    rpc_call('army_end_turn', params_with_token({}))
    
    # Create enemy
    rpc_call('unit_create', params_with_token({
        'player_id': 1,
        'unit_type': 'INFANTRY',
        'x': 4,
        'y': 2
    }))
    
    # End turn back to RED
    rpc_call('army_end_turn', params_with_token({}))
    
    # Select tank
    rpc_call('unit_select', params_with_token({'x': 2, 'y': 2}))
    
    # Move tank closer
    result = rpc_call('movement_execute', params_with_token({
        'from_x': 2,
        'from_y': 2,
        'to_x': 3,
        'to_y': 2
    }))
    
    time.sleep(0.2)  # Wait for board update
    
    # Check if tank is still selected at new position
    result = rpc_call('get_game_board', params_with_token({}))
    board = result['result']['board']
    selected = board.get('selected')
    
    print_test("Unit remains selected after move", 
               selected and selected['x'] == 3 and selected['y'] == 2,
               f"Selected: {selected}")
    
    # Check for attack highlights
    result = rpc_call('combat_targets', params_with_token({'unit_x': 3, 'unit_y': 2}))
    targets = result['result'].get('targets', [])
    
    print_test("Attack targets available after move", len(targets) > 0,
               f"Found {len(targets)} targets")
    
    # Execute attack
    if targets:
        result = rpc_call('combat_attack', params_with_token({
            'attacker_x': 3,
            'attacker_y': 2,
            'defender_x': 4,
            'defender_y': 2
        }))
        
        time.sleep(0.2)
        
        # Check highlights are cleared
        result = rpc_call('get_game_board', params_with_token({}))
        board = result['result']['board']
        
        passed, details = check_highlights(board, expected_movement=0, expected_attack=0)
        print_test("All highlights cleared after attack", passed, details)

def test_highlight_persistence():
    """Test 3: Check for highlight persistence bugs"""
    print(f"\n{Fore.CYAN}=== Test 3: Highlight Persistence ==={Style.RESET_ALL}")
    
    TOKEN = 'highlight-test-3'
    result = rpc_call('game_create_test', {'token': TOKEN, 'use_optimized': True})
    
    params_with_token = lambda p: {**p, 'token': TOKEN}
    
    # Create unit
    rpc_call('unit_create', params_with_token({
        'player_id': 0,
        'unit_type': 'RECON',
        'x': 5,
        'y': 5
    }))
    
    rpc_call('army_end_turn', params_with_token({}))
    rpc_call('army_end_turn', params_with_token({}))
    
    # Select unit
    rpc_call('unit_select', params_with_token({'x': 5, 'y': 5}))
    
    # Move unit
    rpc_call('movement_execute', params_with_token({
        'from_x': 5,
        'from_y': 5,
        'to_x': 7,
        'to_y': 5
    }))
    
    time.sleep(0.2)
    
    # Check original position for highlights
    result = rpc_call('get_game_board', params_with_token({}))
    board = result['result']['board']
    
    # Find tile at (5,5)
    original_tile = None
    for tile in board['grid']:
        if tile['x'] == 5 and tile['y'] == 5:
            original_tile = tile
            break
    
    has_highlight = original_tile and (original_tile.get('can_be_moved_to') or original_tile.get('can_be_attacked'))
    print_test("No highlight on original position after move", not has_highlight,
               f"Tile (5,5): move={original_tile.get('can_be_moved_to')}, attack={original_tile.get('can_be_attacked')}" if original_tile else "")
    
    # Wait action
    rpc_call('unit_wait', params_with_token({'x': 7, 'y': 5}))
    
    time.sleep(0.2)
    
    # Check all highlights cleared
    result = rpc_call('get_game_board', params_with_token({}))
    board = result['result']['board']
    
    passed, details = check_highlights(board, expected_movement=0, expected_attack=0)
    print_test("All highlights cleared after wait", passed, details)

def test_indirect_unit_flow():
    """Test 4: Indirect unit movement (no attack after move)"""
    print(f"\n{Fore.CYAN}=== Test 4: Indirect Unit Flow ==={Style.RESET_ALL}")
    
    TOKEN = 'highlight-test-4'
    result = rpc_call('game_create_test', {'token': TOKEN, 'use_optimized': True})
    
    params_with_token = lambda p: {**p, 'token': TOKEN}
    
    # Create artillery
    rpc_call('unit_create', params_with_token({
        'player_id': 0,
        'unit_type': 'ARTILLERY',
        'x': 3,
        'y': 4
    }))
    
    rpc_call('army_end_turn', params_with_token({}))
    
    # Create target
    rpc_call('unit_create', params_with_token({
        'player_id': 1,
        'unit_type': 'TANK',
        'x': 3,
        'y': 7
    }))
    
    rpc_call('army_end_turn', params_with_token({}))
    
    # Select artillery
    rpc_call('unit_select', params_with_token({'x': 3, 'y': 4}))
    
    # Check initial attack range
    result = rpc_call('combat_targets', params_with_token({'unit_x': 3, 'unit_y': 4}))
    initial_targets = len(result['result'].get('targets', []))
    
    # Move artillery
    rpc_call('movement_execute', params_with_token({
        'from_x': 3,
        'from_y': 4,
        'to_x': 3,
        'to_y': 5
    }))
    
    time.sleep(0.2)
    
    # Check attack options after move
    result = rpc_call('combat_targets', params_with_token({'unit_x': 3, 'unit_y': 5}))
    targets_after_move = len(result['result'].get('targets', []))
    
    print_test("Indirect unit cannot attack after moving", targets_after_move == 0,
               f"Targets before: {initial_targets}, after: {targets_after_move}")
    
    # Check board state
    result = rpc_call('get_game_board', params_with_token({}))
    board = result['result']['board']
    
    passed, details = check_highlights(board, expected_movement=0, expected_attack=0)
    print_test("No attack highlights for moved indirect unit", passed, details)

def main():
    print(f"{Fore.MAGENTA}{'='*50}")
    print(f"Movement Highlights and Flow Test Suite")
    print(f"{'='*50}{Style.RESET_ALL}")
    
    try:
        # Check server is running
        response = requests.get("http://localhost:5000/api/browse")
        if response.status_code != 200:
            print(f"{Fore.RED}Error: Server not responding{Style.RESET_ALL}")
            return
    except:
        print(f"{Fore.RED}Error: Cannot connect to server at localhost:5000{Style.RESET_ALL}")
        return
    
    # Run tests
    test_movement_highlights()
    test_move_attack_flow()
    test_highlight_persistence()
    test_indirect_unit_flow()
    
    print(f"\n{Fore.MAGENTA}{'='*50}")
    print("Test Suite Complete")
    print(f"{'='*50}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
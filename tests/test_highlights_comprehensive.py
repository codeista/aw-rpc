#!/usr/bin/env python3
"""
Comprehensive test for movement highlights
"""

import requests
import json
import time

def rpc_call(method, params=None):
    """Make RPC call to the server"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    }
    response = requests.post("http://localhost:5000/api", json=payload)
    return response.json().get("result", response.json())

print("=" * 60)
print("MOVEMENT HIGHLIGHTS COMPREHENSIVE TEST")
print("=" * 60)

# Step 1: Create a test game
game_id = f'test_{int(time.time())}'
print(f"\n1. Creating game: {game_id}")
result = rpc_call('game_create_v2', {
    'token': game_id,
    'map_name': 'test',
    'players': [
        {'name': 'Player 1', 'color': 'Red', 'sprite_color': 'RED'},
        {'name': 'Player 2', 'color': 'Blue', 'sprite_color': 'BLUE'}
    ]
})
print(f"   Result: {'✅ Success' if result else '❌ Failed'}")

# Step 2: Create units
print("\n2. Creating units:")
# RED infantry at (2,3)
r1 = rpc_call('unit_create', {
    'token': game_id,
    'army': 'RED',
    'unit_type': 'INFANTRY',
    'x': 2,
    'y': 3
})
print(f"   RED infantry at (2,3): {'✅' if r1 else '❌'}")

# RED tank at (5,3)
r2 = rpc_call('unit_create', {
    'token': game_id,
    'army': 'RED', 
    'unit_type': 'TANK',
    'x': 5,
    'y': 3
})
print(f"   RED tank at (5,3): {'✅' if r2 else '❌'}")

# End turn to switch to BLUE
rpc_call('army_end_turn', {'token': game_id})

# BLUE infantry at (3,3) - adjacent to RED infantry
r3 = rpc_call('unit_create', {
    'token': game_id,
    'army': 'BLUE',
    'unit_type': 'INFANTRY',
    'x': 3,
    'y': 3
})
print(f"   BLUE infantry at (3,3): {'✅' if r3 else '❌'}")

# End turn to enable units
rpc_call('army_end_turn', {'token': game_id})

# Step 3: Check board state before selection
print("\n3. Board state BEFORE selection:")
board = rpc_call('game_board', {'token': game_id})
print(f"   Current turn: {board.get('current_turn', 'Unknown')}")
print(f"   Selected: {board.get('selected', 'None')}")

# Count highlights
move_count = sum(1 for tile in board.get('grid', []) if tile.get('can_be_moved_to'))
attack_count = sum(1 for tile in board.get('grid', []) if tile.get('can_be_attacked'))
print(f"   Movement highlights: {move_count}")
print(f"   Attack highlights: {attack_count}")

# Step 4: Select the RED infantry
print("\n4. Selecting RED infantry at (2,3):")
select_result = rpc_call('unit_select', {
    'token': game_id,
    'x': 2,
    'y': 3
})
print(f"   Selection result: {'✅ Success' if not select_result or not select_result.get('error') else '❌ Failed'}")

# Step 5: Check board state after selection
print("\n5. Board state AFTER selection:")
board = rpc_call('game_board', {'token': game_id})
selected = board.get('selected')
if selected:
    print(f"   Selected position: ({selected.get('x')}, {selected.get('y')})")
    if selected.get('unit'):
        unit = selected['unit']
        print(f"   Selected unit: {unit.get('type')} ({unit.get('army')})")
        print(f"   Can move: {unit.get('can_move')}")
        print(f"   Can attack: {unit.get('can_attack')}")
else:
    print("   ❌ No tile selected!")

# Count highlights after selection
move_count = sum(1 for tile in board.get('grid', []) if tile.get('can_be_moved_to'))
attack_count = sum(1 for tile in board.get('grid', []) if tile.get('can_be_attacked'))
print(f"   Movement highlights: {move_count}")
print(f"   Attack highlights: {attack_count}")

# Step 6: Test movement_range API directly
print("\n6. Testing movement_range API directly:")
move_result = rpc_call('movement_range', {
    'token': game_id,
    'unit_x': 2,
    'unit_y': 3
})
if move_result.get('success'):
    positions = move_result.get('positions', [])
    print(f"   ✅ API returns {len(positions)} valid positions")
    if positions:
        print(f"   Sample positions: {positions[:3]}")
else:
    print(f"   ❌ API failed: {move_result.get('error', 'Unknown error')}")

# Step 7: Test combat_targets API directly
print("\n7. Testing combat_targets API directly:")
attack_result = rpc_call('combat_targets', {
    'token': game_id,
    'unit_x': 2,
    'unit_y': 3
})
if attack_result.get('success'):
    targets = attack_result.get('targets', [])
    print(f"   ✅ API returns {len(targets)} attack targets")
    if targets:
        print(f"   Targets: {targets}")
else:
    print(f"   ❌ API failed: {attack_result.get('error', 'Unknown error')}")

# Step 8: Summary
print("\n" + "=" * 60)
print("TEST SUMMARY:")
print("=" * 60)
print(f"Game URL: http://localhost:5000/game/{game_id}")
print("\nEXPECTED BEHAVIOR:")
print("- After selecting the unit, can_be_moved_to should be set on tiles")
print("- After selecting the unit, can_be_attacked should be set on enemy units")
print("\nACTUAL RESULTS:")
print(f"- Movement highlights in board after selection: {move_count}")
print(f"- Attack highlights in board after selection: {attack_count}")
print(f"- Movement API returns valid positions: {'✅ Yes' if move_result.get('success') else '❌ No'}")
print(f"- Combat API returns valid targets: {'✅ Yes' if attack_result.get('success') else '❌ No'}")

if move_count == 0:
    print("\n❌ PROBLEM: Movement highlights are NOT being set in the board state")
    print("   even though the movement_range API returns valid positions.")
else:
    print("\n✅ Movement highlights are working correctly")

print("\nNOTE: The issue appears to be that unit_select clears highlights")
print("      but doesn't set them. The frontend must call movement_range")
print("      and update the tiles manually.")
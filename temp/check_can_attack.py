#!/usr/bin/env python3
"""
Check can_attack status on test map units
"""

import requests
import time

def rpc_call(method: str, params: dict = None) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    }
    
    response = requests.post("http://localhost:5000/api", json=payload)
    result = response.json()
    return result.get("result", result)

def main():
    print("=== CAN_ATTACK STATUS CHECK ===\n")
    
    # Create test game
    game_id = "canattack" + str(int(time.time()) % 10000)
    result = rpc_call("game_create_test", {"token": game_id})
    print(f"✅ Created test game: {game_id}")
    
    # Get board
    board = rpc_call("game_board", {"token": game_id})
    
    print(f"\n📊 Game State:")
    print(f"   Day: {board.get('day', 1)}")
    print(f"   Turn: {board.get('current_turn')}")
    
    # Check all units' can_attack status
    print("\n🔍 Units that CAN attack:")
    can_attack_count = 0
    
    for tile in board['grid']:
        if tile.get('unit'):
            unit = tile['unit']
            if unit.get('can_attack'):
                can_attack_count += 1
                print(f"   ✅ {unit['army']} {unit['type']} at ({tile['x']}, {tile['y']}) - can_attack: True")
    
    print(f"\n📈 Total units that can attack: {can_attack_count}")
    
    # Check specific units
    print("\n🎯 Checking specific units:")
    
    # Check battleship at (2,1)
    battleship_info = rpc_call("unit_info", {"token": game_id, "x": 2, "y": 1})
    print(f"\n   Battleship at (2,1):")
    print(f"      can_attack: {battleship_info.get('can_attack')}")
    print(f"      can_move: {battleship_info.get('can_move')}")
    print(f"      HP: {battleship_info.get('hp')}")
    
    # Check tank at (4,5)
    tank_info = rpc_call("unit_info", {"token": game_id, "x": 4, "y": 5})
    print(f"\n   Tank at (4,5):")
    print(f"      can_attack: {tank_info.get('can_attack')}")
    print(f"      can_move: {tank_info.get('can_move')}")
    print(f"      HP: {tank_info.get('hp')}")
    
    # Get attack targets for battleship
    print("\n⚔️ Attack targets for Battleship:")
    targets = rpc_call("get_attack_targets", {"token": game_id, "unit_x": 2, "unit_y": 1})
    if targets.get('success'):
        print(f"   Can attack {len(targets['targets'])} units:")
        for t in targets['targets'][:3]:
            print(f"      - {t['unit_type']} at ({t['x']}, {t['y']})")
    
    print("\n✅ Check complete!")

if __name__ == "__main__":
    main()
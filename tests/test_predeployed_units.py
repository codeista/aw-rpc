#!/usr/bin/env python3
"""
Test script to verify predeployed units are working correctly
"""

import requests
import json
import random
import string

def rpc_call(method: str, params: dict = None) -> dict:
    """Make RPC call to the server"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    }
    
    response = requests.post("http://localhost:5000/api", json=payload)
    result = response.json()
    
    if "error" in result:
        return {"error": result["error"]}
    
    return result.get("result", result)

def test_combat_map():
    """Test creating a game with the combat map and verify units"""
    print("Testing Combat Map with Predeployed Units")
    print("=" * 60)
    
    # Create game with combat map
    game_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    print(f"Creating game with ID: {game_id}")
    result = rpc_call("game_create_v2", {
        "token": game_id,
        "map_name": "combat",
        "players": [
            {"name": "Player 1", "color": "Red", "sprite_color": "RED"},
            {"name": "Player 2", "color": "Blue", "sprite_color": "BLUE"}
        ]
    })
    
    if "error" in result:
        print(f"❌ Failed to create game: {result}")
        return
    
    print(f"✅ Game created successfully")
    print(f"   Map: {result.get('map')}")
    print(f"   Players: {len(result.get('players', []))}")
    
    # Get board state
    board = rpc_call("game_board", {"token": game_id})
    if "error" in board:
        print(f"❌ Failed to get board: {board}")
        return
    
    # Count units
    red_units = 0
    blue_units = 0
    unit_positions = []
    
    for tile in board.get("grid", []):
        if tile.get("unit"):
            unit = tile["unit"]
            army = unit.get("army", {}).get("name", "") if isinstance(unit.get("player_id"), dict) else str(unit.get("army", ""))
            unit_type = unit.get("type", {}).get("name", "") if isinstance(unit.get("type"), dict) else str(unit.get("type", ""))
            
            if army == 0:
                red_units += 1
            elif army == 1:
                blue_units += 1
            
            unit_positions.append({
                "type": unit_type,
                "army": army,
                "x": tile["x"],
                "y": tile["y"],
                "hp": unit.get("status", {}).get("hp", 100) if isinstance(unit.get("status"), dict) else unit.get("hp", 100)
            })
    
    print(f"\n📊 Unit Count:")
    print(f"   RED units: {red_units}")
    print(f"   BLUE units: {blue_units}")
    print(f"   Total units: {red_units + blue_units}")
    
    # Show first few units
    print(f"\n🎮 Sample Units:")
    for i, unit in enumerate(unit_positions[:10]):
        print(f"   {i+1}. {unit['army']} {unit['type']} at ({unit['x']},{unit['y']}) - HP: {unit['hp']}")
    
    if len(unit_positions) > 10:
        print(f"   ... and {len(unit_positions) - 10} more units")
    
    # Test attack targets for first RED unit
    if unit_positions:
        red_unit = next((u for u in unit_positions if u['army'] == 0), None)
        if red_unit:
            print(f"\n⚔️ Testing attack targets for {red_unit['type']} at ({red_unit['x']},{red_unit['y']})")
            targets = rpc_call("combat_targets", {
                "token": game_id,
                "unit_x": red_unit['x'],
                "unit_y": red_unit['y']
            })
            
            if "error" not in targets and targets.get("targets"):
                print(f"   Found {len(targets['targets'])} attack targets")
                for t in targets['targets'][:3]:
                    print(f"   - Can attack position ({t['x']},{t['y']})")
            else:
                print(f"   No attack targets found or error: {targets.get('error', 'No targets')}")
    
    print(f"\n🎮 Game URL: http://localhost:5000/game/{game_id}")

def test_admin_unit_create():
    """Test admin unit creation"""
    print("\n\nTesting Admin Unit Creation")
    print("=" * 60)
    
    # Create a test game first
    game_id = 'test_' + ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    
    result = rpc_call("game_create_v2", {
        "token": game_id,
        "map_name": "test",
        "players": [
            {"name": "Player 1", "color": "Red", "sprite_color": "RED"},
            {"name": "Player 2", "color": "Blue", "sprite_color": "BLUE"}
        ]
    })
    
    if "error" in result:
        print(f"❌ Failed to create test game: {result}")
        return
    
    print(f"✅ Created test game: {game_id}")
    
    # Try admin unit creation
    admin_result = rpc_call("admin_unit_create", {
        "token": game_id,
        "player_id": 0,
        "unit_type": "MEGATANK",
        "x": 5,
        "y": 5,
        "hp": 50,
        "admin_key": None  # Should work for test games
    })
    
    if "error" in admin_result:
        print(f"❌ Admin unit creation failed: {admin_result}")
    else:
        print(f"✅ Admin unit created: {admin_result.get('unit', {}).get('type')} at ({admin_result.get('unit', {}).get('x')},{admin_result.get('unit', {}).get('y')})")
        print(f"   HP: {admin_result.get('unit', {}).get('hp')}")
        print(f"   Can move: {admin_result.get('unit', {}).get('can_move')}")
        print(f"   Can attack: {admin_result.get('unit', {}).get('can_attack')}")

if __name__ == "__main__":
    test_combat_map()
    test_admin_unit_create()
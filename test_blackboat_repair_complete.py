#!/usr/bin/env python3
"""
Complete Black Boat Repair System Test
"""

import requests
import json
import time

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
    return result.get("result", {})

def create_repair_test_scenario():
    """Create a complete test scenario for Black Boat repair"""
    print("🚀 Complete Black Boat Repair Test")
    print("=" * 50)
    
    # Create test game with high funds
    game_id = f"repair_test_{int(time.time())}"
    result = rpc_call("game_create_test", {"token": game_id})
    if "error" in result:
        print(f"❌ Failed to create game: {result['error']}")
        return None
    
    print(f"✅ Created test game: {game_id}")
    
    # Get initial board state
    board = rpc_call("game_board", {"token": game_id})
    red_funds = board.get("red_funds", 0)
    print(f"💰 Starting funds: {red_funds}")
    
    # End turns to clear facilities and enable movement
    print("\n🔄 Cycling turns...")
    for i in range(2):
        rpc_call("army_end_turn", {"token": game_id})
        rpc_call("army_end_turn", {"token": game_id})
    
    print("\n1️⃣ Creating Black Boat at RED port (0,0)")
    bb_result = rpc_call("unit_create", {
        "token": game_id,
        "army": "RED",
        "unit_type": "BLACKBOAT",
        "x": 0,
        "y": 0
    })
    
    if "error" in bb_result:
        print(f"❌ Failed to create Black Boat: {bb_result['error']}")
        return None
    
    print("✅ Black Boat created")
    
    print("\n2️⃣ Creating Infantry at RED factory (0,4)")
    inf_result = rpc_call("unit_create", {
        "token": game_id,
        "army": "RED",
        "unit_type": "INFANTRY",
        "x": 0,
        "y": 4
    })
    
    if "error" in inf_result:
        print(f"❌ Failed to create Infantry: {inf_result['error']}")
        return None
    
    print("✅ Infantry created")
    
    # End turn to enable movement
    print("\n3️⃣ Enabling movement...")
    rpc_call("army_end_turn", {"token": game_id})
    rpc_call("army_end_turn", {"token": game_id})
    
    print("\n4️⃣ Moving Infantry near Black Boat")
    # Move infantry from factory to position (1,1) - adjacent to Black Boat at (0,0)
    move1 = rpc_call("unit_move", {
        "token": game_id,
        "x": 0, "y": 4,  # From factory
        "x2": 0, "y2": 3  # Move up one
    })
    
    if "error" not in move1:
        print("✅ Infantry moved to (0,3)")
        
        # End turn to move again
        rpc_call("army_end_turn", {"token": game_id})
        rpc_call("army_end_turn", {"token": game_id})
        
        # Move infantry to beach position adjacent to Black Boat
        move2 = rpc_call("unit_move", {
            "token": game_id,
            "x": 0, "y": 3,
            "x2": 0, "y2": 2  # Beach position at (0,2)
        })
        
        if "error" not in move2:
            print("✅ Infantry moved to beach at (0,2)")
        else:
            print(f"⚠️ Second move failed: {move2.get('error')}")
    else:
        print(f"⚠️ First move failed: {move1.get('error')}")
    
    print("\n5️⃣ Creating enemy unit to damage Infantry")
    # End turn to enable BLUE creation
    rpc_call("army_end_turn", {"token": game_id})
    
    # Create BLUE tank to attack the infantry
    tank_result = rpc_call("unit_create", {
        "token": game_id,
        "army": "BLUE",
        "unit_type": "TANK",
        "x": 9,
        "y": 4  # BLUE factory
    })
    
    if "error" not in tank_result:
        print("✅ Enemy Tank created")
        
        # Move tank near infantry to attack
        rpc_call("army_end_turn", {"token": game_id})
        rpc_call("army_end_turn", {"token": game_id})
        
        # Move tank closer for attack (will need multiple moves)
        for i in range(3):  # Move tank towards infantry
            tank_move = rpc_call("unit_move", {
                "token": game_id,
                "x": 9-i, "y": 4,
                "x2": 8-i, "y2": 4
            })
            
            if "error" not in tank_move:
                print(f"✅ Tank moved to ({8-i},4)")
                rpc_call("army_end_turn", {"token": game_id})
                rpc_call("army_end_turn", {"token": game_id})
            else:
                break
        
        # Move tank to attack position and attack infantry
        attack_pos = rpc_call("unit_move", {
            "token": game_id,
            "x": 6, "y": 4,
            "x2": 1, "y2": 2  # Position to attack infantry at (0,2)
        })
        
        if "error" not in attack_pos:
            print("✅ Tank in attack position")
            
            # Attack the infantry
            attack_result = rpc_call("unit_attack", {
                "token": game_id,
                "x": 1, "y": 2,
                "x2": 0, "y2": 2
            })
            
            if "error" not in attack_result:
                print("✅ Infantry attacked and damaged!")
            else:
                print(f"⚠️ Attack failed: {attack_result.get('error')}")
        else:
            print(f"⚠️ Tank positioning failed: {attack_pos.get('error')}")
    else:
        print(f"⚠️ Failed to create enemy tank: {tank_result.get('error')}")
    
    print("\n6️⃣ Checking Infantry HP after damage")
    board = rpc_call("game_board", {"token": game_id})
    
    # Find infantry HP
    tiles = board.get("tiles", [])
    infantry_hp = None
    
    for y in range(len(tiles)):
        for x in range(len(tiles[y])):
            tile = tiles[y][x]
            if tile.get("unit") and tile["unit"]["type"] == "INFANTRY" and tile["unit"]["army"] == "RED":
                infantry_hp = tile["unit"].get("hp", tile["unit"].get("status", {}).get("hp", 100))
                print(f"📊 Infantry found at ({x},{y}) with {infantry_hp} HP")
                break
    
    if infantry_hp is None:
        print("⚠️ Could not find infantry (may have been destroyed)")
        return game_id
    
    if infantry_hp >= 100:
        print(f"ℹ️ Infantry has full HP ({infantry_hp}), repair not needed but system is ready")
    else:
        print(f"✅ Infantry damaged to {infantry_hp} HP - ready for repair test!")
    
    print("\n7️⃣ BLACK BOAT REPAIR TEST READY")
    print("=" * 50)
    print("📋 MANUAL TEST INSTRUCTIONS:")
    print("1. Go to: http://localhost:5000/game/" + game_id)
    print("2. LEFT-CLICK on the Black Boat to select it")
    print("3. RIGHT-CLICK on the Infantry unit")
    print("4. Look for context menu with '🔧 Repair Unit (2 HP)'")
    print("5. Click repair option to test functionality")
    print("=" * 50)
    
    return game_id

def test_repair_rpc_directly():
    """Test the repair RPC endpoint directly"""
    print("\n🔧 Testing repair_unit RPC directly...")
    
    # Create a simple test game
    game_id = f"rpc_test_{int(time.time())}"
    rpc_call("game_create_test", {"token": game_id})
    
    # Try to call repair_unit RPC (should fail gracefully with validation)
    repair_result = rpc_call("repair_unit", {
        "token": game_id,
        "blackboat_x": 0,
        "blackboat_y": 0,
        "target_x": 1,
        "target_y": 0,
        "hp_to_repair": 2
    })
    
    if "error" in repair_result:
        print(f"✅ RPC validation working: {repair_result['error']}")
    else:
        print(f"⚠️ Unexpected success: {repair_result}")
    
    return game_id

if __name__ == "__main__":
    # Test RPC endpoint
    test_repair_rpc_directly()
    
    # Create complete test scenario
    scenario_game = create_repair_test_scenario()
    
    print(f"\n🎮 Test scenarios created!")
    print(f"🌐 Server: http://localhost:5000")
    if scenario_game:
        print(f"🎯 Repair test: http://localhost:5000/game/{scenario_game}")
    
    print("\n✅ All test setup complete!")
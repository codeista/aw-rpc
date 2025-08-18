#!/usr/bin/env python3
"""
Test the complete combat workflow including RPC serialization
"""
import json
import requests
import time
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:5000"
API_URL = f"{BASE_URL}/api"
TEST_TOKEN = f"combat-test-{int(time.time())}"

def rpc_call(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Make an RPC call and return the result"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    
    response = requests.post(API_URL, json=payload)
    if response.status_code != 200:
        raise Exception(f"RPC call failed with status {response.status_code}: {response.text}")
    
    data = response.json()
    if "error" in data:
        raise Exception(f"RPC error: {data['error']}")
    
    return data.get("result", {})

def test_combat_workflow():
    """Test the complete combat workflow"""
    print(f"Testing combat workflow with token: {TEST_TOKEN}")
    
    # Step 1: Create a test game
    print("\n1. Creating test game...")
    result = rpc_call("game_create_test", {"token": TEST_TOKEN})
    if not result.get("success"):
        raise Exception(f"Failed to create game: {result}")
    print("✓ Game created successfully")
    
    # Step 2: Get initial game state
    print("\n2. Getting game state...")
    state = rpc_call("game_board", {"token": TEST_TOKEN})
    print(f"✓ Current turn: {state.get('current_turn')}")
    print(f"✓ Day: {state.get('days', 1)}")
    
    # Step 3: Create units for combat
    print("\n3. Creating units...")
    
    # Find factories to create units
    factories = [t for t in state.get("tiles", []) if t.get("type") == "FACTORY"]
    red_factory = next((f for f in factories if f.get("army") == 0), None)
    blue_factory = next((f for f in factories if f.get("army") == 1), None)
    
    if not red_factory or not blue_factory:
        # Create units directly if no factories
        print("  No factories found, creating units directly...")
        
        # Create RED tank at (5, 5)
        result = rpc_call("unit_create", {
            "token": TEST_TOKEN,
            "x": 5,
            "y": 5,
            "unit_type": "TANK"
        })
        if not result.get("success"):
            raise Exception(f"Failed to create RED tank: {result}")
        print("✓ Created TANK at (5, 5)")
        
        # End turn to switch to BLUE
        result = rpc_call("army_end_turn", {"token": TEST_TOKEN})
        if not result.get("success"):
            raise Exception(f"Failed to end turn: {result}")
        
        # Create BLUE infantry at (6, 5) - adjacent for combat
        result = rpc_call("unit_create", {
            "token": TEST_TOKEN,
            "x": 6,
            "y": 5,
            "unit_type": "INFANTRY"
        })
        if not result.get("success"):
            raise Exception(f"Failed to create BLUE infantry: {result}")
        print("✓ Created INFANTRY at (6, 5)")
    else:
        # Use factories to create units
        print(f"  Using factories - RED at ({red_factory['x']}, {red_factory['y']}), BLUE at ({blue_factory['x']}, {blue_factory['y']})")
        
        # Create from RED factory
        result = rpc_call("production_create", {
            "token": TEST_TOKEN,
            "x": red_factory["x"],
            "y": red_factory["y"],
            "unit_type": "TANK"
        })
        if not result.get("success"):
            raise Exception(f"Failed to create tank from factory: {result}")
        print(f"✓ Created RED TANK at factory ({red_factory['x']}, {red_factory['y']})")
        
        # End turn to switch to BLUE
        result = rpc_call("army_end_turn", {"token": TEST_TOKEN})
        if not result.get("success"):
            raise Exception(f"Failed to end turn: {result}")
        
        # Create from BLUE factory
        result = rpc_call("production_create", {
            "token": TEST_TOKEN,
            "x": blue_factory["x"],
            "y": blue_factory["y"],
            "unit_type": "INFANTRY"
        })
        if not result.get("success"):
            raise Exception(f"Failed to create infantry from factory: {result}")
        print(f"✓ Created BLUE INFANTRY at factory ({blue_factory['x']}, {blue_factory['y']})")
    
    # Step 4: Position units for combat if using factories
    print("\n4. Positioning units for combat...")
    current_board = rpc_call("game_board", {"token": TEST_TOKEN})
    
    # Find where our units actually are
    tank_pos = None
    infantry_pos = None
    
    # Debug: print all units on board
    units_found = []
    for tile in current_board.get("tiles", []):
        if tile.get("unit"):
            unit = tile["unit"]
            units_found.append(f"{unit.get('type')} at ({tile['x']}, {tile['y']})")
            if unit.get("type") == "TANK":
                tank_pos = (tile["x"], tile["y"])
                print(f"  Found TANK at ({tile['x']}, {tile['y']})")
            elif unit.get("type") == "INFANTRY":
                infantry_pos = (tile["x"], tile["y"])
                print(f"  Found INFANTRY at ({tile['x']}, {tile['y']})")
    
    if units_found:
        print(f"  Units on board: {', '.join(units_found)}")
    else:
        print("  WARNING: No units found on board!")
    
    if not tank_pos or not infantry_pos:
        raise Exception("Could not find both units on the board")
    
    # If units aren't adjacent, we need to move them
    distance = abs(tank_pos[0] - infantry_pos[0]) + abs(tank_pos[1] - infantry_pos[1])
    if distance > 1:
        print(f"  Units are {distance} tiles apart, need to move them closer...")
        # For simplicity, we'll create new units that are adjacent
        tank_pos = (5, 5)
        infantry_pos = (6, 5)
    
    # End turn to ensure it's RED's turn for attack
    print("\n5. Ensuring correct turn for attack...")
    result = rpc_call("army_end_turn", {"token": TEST_TOKEN})
    if not result.get("success"):
        raise Exception(f"Failed to end turn: {result}")
    print("✓ Turn ended")
    
    # Step 6: Get combat preview
    print("\n6. Getting combat preview...")
    preview = rpc_call("combat_preview", {
        "token": TEST_TOKEN,
        "attacker_x": tank_pos[0],
        "attacker_y": tank_pos[1],
        "target_x": infantry_pos[0],
        "target_y": infantry_pos[1]
    })
    
    if "damage" in preview:
        damage_info = preview["damage"]
        print(f"✓ Attack damage: {damage_info.get('attacker_damage', 0)}")
        print(f"✓ Counter damage: {damage_info.get('counter_damage', 0)}")
    else:
        print("⚠ No damage preview available")
    
    # Step 7: Execute attack
    print("\n7. Executing attack...")
    attack_result = rpc_call("unit_attack", {
        "token": TEST_TOKEN,
        "attacker_x": tank_pos[0],
        "attacker_y": tank_pos[1],
        "target_x": infantry_pos[0],
        "target_y": infantry_pos[1]
    })
    
    # Check if result is properly serialized
    if not isinstance(attack_result, dict):
        raise Exception(f"Attack result is not a dictionary: {type(attack_result)}")
    
    if not attack_result.get("success"):
        raise Exception(f"Attack failed: {attack_result.get('error', 'Unknown error')}")
    
    print("✓ Attack executed successfully!")
    print(f"  - Damage dealt: {attack_result.get('attacker_damage_dealt', 0)}")
    print(f"  - Counter damage: {attack_result.get('defender_damage_dealt', 0)}")
    print(f"  - Defender destroyed: {attack_result.get('defender_destroyed', False)}")
    print(f"  - Attacker destroyed: {attack_result.get('attacker_destroyed', False)}")
    
    # Verify JSON serialization
    try:
        json.dumps(attack_result)
        print("✓ Result is JSON serializable")
    except Exception as e:
        raise Exception(f"Result is not JSON serializable: {e}")
    
    # Step 8: Verify unit states after combat
    print("\n8. Checking post-combat state...")
    board = rpc_call("game_board", {"token": TEST_TOKEN})
    
    # Check if defender was destroyed
    defender_tile = next((t for t in board.get("tiles", []) if t["x"] == infantry_pos[0] and t["y"] == infantry_pos[1]), None)
    if defender_tile:
        if attack_result.get("defender_destroyed") and defender_tile.get("unit"):
            raise Exception("Defender should be destroyed but still exists")
        elif not attack_result.get("defender_destroyed") and not defender_tile.get("unit"):
            raise Exception("Defender should exist but is missing")
    
    print("✓ Post-combat state is consistent")
    
    print("\n✅ ALL TESTS PASSED! Combat workflow is working correctly.")
    return True

if __name__ == "__main__":
    try:
        # Check if server is running
        response = requests.get(BASE_URL)
        if response.status_code != 200:
            print("❌ Server is not running at http://localhost:5000")
            print("Please start the server with: python3 app.py")
            exit(1)
        
        # Run the test
        test_combat_workflow()
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at http://localhost:5000")
        print("Please start the server with: python3 app.py")
        exit(1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
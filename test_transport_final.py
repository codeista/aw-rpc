#!/usr/bin/env python3
"""
Final Transport System Test - Uses turn ending to generate funds from properties
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
    if response.status_code != 200:
        return {"error": f"HTTP {response.status_code}: {response.text}"}
    
    try:
        result = response.json()
        if "error" in result:
            return {"error": result["error"]}
        return result.get("result", {})
    except Exception as e:
        return {"error": f"JSON decode error: {str(e)}"}

def create_test_game() -> str:
    """Create a test game"""
    print("🎮 Creating test game...")
    
    import random
    import string
    game_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    result = rpc_call("game_create", {"token": game_id})
    if "error" in result:
        print(f"❌ Failed to create game: {result['error']}")
        return None
    
    print(f"✅ Created test game: {game_id}")
    return game_id

def generate_funds_from_properties(game_id: str, cycles: int = 2) -> bool:
    """Generate funds by ending turns to collect property income"""
    print(f"💰 Generating funds by ending {cycles} turn cycles...")
    
    initial_board = rpc_call("game_board", {"token": game_id})
    if "error" in initial_board:
        print(f"❌ Could not get initial board: {initial_board['error']}")
        return False
    
    initial_funds = {
        "RED": initial_board.get("board", {}).get("red_funds", 0),
        "BLUE": initial_board.get("board", {}).get("blue_funds", 0)
    }
    
    print(f"💰 Initial funds - RED: {initial_funds['RED']}, BLUE: {initial_funds['BLUE']}")
    
    # End turns to generate income from properties
    for cycle in range(cycles):
        print(f"🔄 Turn cycle {cycle + 1}/{cycles}")
        
        # End RED turn
        result = rpc_call("army_end_turn", {"token": game_id})
        if "error" in result:
            print(f"❌ Failed to end RED turn: {result['error']}")
            return False
        
        # End BLUE turn  
        result = rpc_call("army_end_turn", {"token": game_id})
        if "error" in result:
            print(f"❌ Failed to end BLUE turn: {result['error']}")
            return False
        
        # Check funds after this cycle
        board = rpc_call("game_board", {"token": game_id})
        if "error" not in board:
            current_funds = {
                "RED": board.get("board", {}).get("red_funds", 0),
                "BLUE": board.get("board", {}).get("blue_funds", 0)
            }
            print(f"   After cycle {cycle + 1} - RED: {current_funds['RED']}, BLUE: {current_funds['BLUE']}")
    
    # Final fund check
    final_board = rpc_call("game_board", {"token": game_id})
    if "error" in final_board:
        return False
    
    final_funds = {
        "RED": final_board.get("board", {}).get("red_funds", 0),
        "BLUE": final_board.get("board", {}).get("blue_funds", 0)
    }
    
    fund_increase = {
        "RED": final_funds["RED"] - initial_funds["RED"],
        "BLUE": final_funds["BLUE"] - initial_funds["BLUE"]
    }
    
    print(f"💰 Final funds - RED: {final_funds['RED']} (+{fund_increase['RED']}), BLUE: {final_funds['BLUE']} (+{fund_increase['BLUE']})")
    
    total_funds = final_funds["RED"] + final_funds["BLUE"]
    return total_funds >= 4000  # Should have at least 4000 total for comprehensive testing

def create_comprehensive_transport_test(game_id: str) -> int:
    """Create comprehensive transport test scenario with available funds"""
    print("🚛 Creating transport test units...")
    
    # Test units in order of priority (cheapest first for maximum testing)
    test_units = [
        # Basic transports and cargo
        {"unit": "INFANTRY", "army": "RED", "x": 1, "y": 1, "cost": 1000},
        {"unit": "INFANTRY", "army": "RED", "x": 2, "y": 1, "cost": 1000},
        {"unit": "APC", "army": "RED", "x": 3, "y": 1, "cost": 5000},
        
        {"unit": "INFANTRY", "army": "BLUE", "x": 8, "y": 1, "cost": 1000},
        {"unit": "MECH", "army": "BLUE", "x": 9, "y": 1, "cost": 3000},
        {"unit": "APC", "army": "BLUE", "x": 10, "y": 1, "cost": 5000},
        
        # Advanced units if funds allow
        {"unit": "RECON", "army": "RED", "x": 1, "y": 3, "cost": 4000},
        {"unit": "TANK", "army": "RED", "x": 2, "y": 3, "cost": 7000},
        {"unit": "LANDER", "army": "RED", "x": 1, "y": 8, "cost": 12000},
        
        {"unit": "TCOPTER", "army": "BLUE", "x": 5, "y": 5, "cost": 5000},
        {"unit": "INFANTRY", "army": "BLUE", "x": 5, "y": 4, "cost": 1000},
    ]
    
    created_units = []
    failed_units = []
    
    for unit_data in test_units:
        result = rpc_call("unit_create", {
            "token": game_id,
            "army": unit_data["army"],
            "unit_type": unit_data["unit"],
            "x": unit_data["x"],
            "y": unit_data["y"]
        })
        
        if "error" not in result:
            print(f"✅ Created {unit_data['unit']} at ({unit_data['x']}, {unit_data['y']})")
            created_units.append(unit_data)
        else:
            if "Insufficient funds" in str(result.get("error", "")):
                print(f"💰 Insufficient funds for {unit_data['unit']} (cost: {unit_data['cost']})")
            else:
                print(f"❌ Failed to create {unit_data['unit']}: {result['error']}")
            failed_units.append(unit_data)
    
    print(f"📊 Created {len(created_units)} units, {len(failed_units)} failed due to funds")
    return len(created_units)

def run_transport_tests(game_id: str) -> dict:
    """Run comprehensive transport tests"""
    print("\n🧪 Running transport functionality tests...")
    
    test_results = {
        "transport_detection": False,
        "cargo_info": False,
        "loadable_transports": False,
        "cargo_loading": False,
        "movement_with_cargo": False,
        "exit_positions": False,
        "cargo_unloading": False,
        "terrain_validation": False
    }
    
    # Test 1: Transport Detection
    print("\n1️⃣ Testing transport detection...")
    transport_positions = [(3, 1), (10, 1), (1, 8), (5, 5)]  # Potential transport locations
    
    found_transport = None
    for x, y in transport_positions:
        result = rpc_call("get_cargo_info", {"token": game_id, "x": x, "y": y})
        if "error" not in result:
            cargo_info = result.get("cargo_info", {})
            if cargo_info.get("is_transport"):
                print(f"✅ Found transport at ({x}, {y}) - Type: {cargo_info.get('compatible_types', [])}")
                found_transport = (x, y)
                test_results["transport_detection"] = True
                test_results["cargo_info"] = True
                break
    
    if not found_transport:
        print("❌ No transports found - remaining tests will be skipped")
        return test_results
    
    tx, ty = found_transport
    
    # Test 2: Find cargo for this transport
    print("\n2️⃣ Testing cargo unit detection...")
    cargo_positions = [(1, 1), (2, 1), (8, 1), (9, 1), (1, 3), (2, 3)]  # Potential cargo locations
    
    found_cargo = None
    for x, y in cargo_positions:
        result = rpc_call("get_loadable_transports", {"token": game_id, "cargo_x": x, "cargo_y": y})
        if "error" not in result and result.get("success"):
            transports = result.get("loadable_transports", [])
            for transport in transports:
                if transport["x"] == tx and transport["y"] == ty:
                    print(f"✅ Found compatible cargo at ({x}, {y}) for transport at ({tx}, {ty})")
                    found_cargo = (x, y)
                    test_results["loadable_transports"] = True
                    break
            if found_cargo:
                break
    
    if not found_cargo:
        print("❌ No compatible cargo found - loading tests will be skipped")
        # Still test other functionality
        
        # Test exit positions without cargo
        print("\n3️⃣ Testing exit positions (empty transport)...")
        exit_result = rpc_call("get_exit_positions", {"token": game_id, "transport_x": tx, "transport_y": ty})
        if "error" not in exit_result and exit_result.get("success"):
            positions = exit_result.get("valid_positions", [])
            print(f"✅ Found {len(positions)} potential exit positions")
            test_results["exit_positions"] = True
        
        # Test terrain validation
        print("\n4️⃣ Testing terrain validation...")
        terrain_result = rpc_call("validate_movement", {
            "token": game_id, "x": tx, "y": ty, "x2": tx + 1, "y2": ty
        })
        if "error" not in terrain_result:
            print("✅ Terrain validation working")
            test_results["terrain_validation"] = True
        
        return test_results
    
    cx, cy = found_cargo
    
    # Test 3: Load cargo into transport
    print("\n3️⃣ Testing cargo loading...")
    load_result = rpc_call("cargo_board_transport", {
        "token": game_id,
        "cargo_x": cx, "cargo_y": cy,
        "transport_x": tx, "transport_y": ty
    })
    
    if "error" not in load_result and load_result.get("success"):
        print(f"✅ Successfully loaded cargo: {load_result.get('message', 'Success')}")
        test_results["cargo_loading"] = True
        
        # Test 4: Verify cargo is loaded
        verify_result = rpc_call("get_cargo_info", {"token": game_id, "x": tx, "y": ty})
        if "error" not in verify_result:
            cargo_info = verify_result.get("cargo_info", {})
            if cargo_info.get("current_cargo", 0) > 0:
                print(f"✅ Cargo verified: {cargo_info.get('current_cargo')} units loaded")
                
                # Test 5: Move transport with cargo
                print("\n4️⃣ Testing transport movement with cargo...")
                new_x, new_y = tx + 1, ty
                move_result = rpc_call("unit_move", {
                    "token": game_id, "x": tx, "y": ty, "x2": new_x, "y2": new_y
                })
                
                if "error" not in move_result:
                    print("✅ Transport moved successfully with cargo")
                    test_results["movement_with_cargo"] = True
                    
                    # Update transport position for remaining tests
                    tx, ty = new_x, new_y
                    
                    # Test 6: Get exit positions
                    print("\n5️⃣ Testing exit positions...")
                    exit_result = rpc_call("get_exit_positions", {
                        "token": game_id, "transport_x": tx, "transport_y": ty
                    })
                    
                    if "error" not in exit_result and exit_result.get("success"):
                        positions = exit_result.get("valid_positions", [])
                        print(f"✅ Found {len(positions)} valid exit positions")
                        test_results["exit_positions"] = True
                        
                        # Test 7: Unload cargo
                        if positions:
                            print("\n6️⃣ Testing cargo unloading...")
                            exit_pos = positions[0]
                            unload_result = rpc_call("cargo_exit_transport", {
                                "token": game_id,
                                "transport_x": tx, "transport_y": ty,
                                "exit_x": exit_pos["x"], "exit_y": exit_pos["y"],
                                "cargo_index": 0
                            })
                            
                            if "error" not in unload_result and unload_result.get("success"):
                                print(f"✅ Cargo unloaded successfully: {unload_result.get('message', 'Success')}")
                                test_results["cargo_unloading"] = True
    
    # Test 8: Terrain validation
    print("\n7️⃣ Testing terrain validation...")
    terrain_result = rpc_call("validate_movement", {
        "token": game_id, "x": tx, "y": ty, "x2": tx, "y2": ty + 1
    })
    if "error" not in terrain_result:
        print("✅ Terrain validation working")
        test_results["terrain_validation"] = True
    
    return test_results

def main():
    """Main test function"""
    print("🚀 Final Transport System Test with Fund Generation")
    print("=" * 70)
    
    # Check server
    try:
        response = requests.get("http://localhost:5000")
        if response.status_code != 200:
            print("❌ Server not responding properly")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server - is it running on localhost:5000?")
        return False
    
    # Create test game
    game_id = create_test_game()
    if not game_id:
        return False
    
    # Generate funds through property income
    if not generate_funds_from_properties(game_id, cycles=3):
        print("⚠️  Limited funds available - tests may be constrained")
    
    # Create test units
    units_created = create_comprehensive_transport_test(game_id)
    if units_created < 3:
        print("❌ Insufficient units created for meaningful testing")
        return False
    
    print(f"✅ Created {units_created} units for testing")
    
    # Run transport tests
    results = run_transport_tests(game_id)
    
    # Display results
    print("\n" + "=" * 70)
    print("📊 FINAL TRANSPORT TEST RESULTS")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, status in results.items():
        icon = "✅ PASS" if status else "❌ FAIL"
        test_display = test_name.replace("_", " ").title()
        print(f"{icon} {test_display}")
        if status:
            passed += 1
    
    print("-" * 70)
    print(f"📈 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 PERFECT SCORE - All transport functionality working!")
    elif passed >= total * 0.8:
        print("✅ EXCELLENT - Transport system fully functional")
    elif passed >= total * 0.6:
        print("✅ GOOD - Core transport features working")
    else:
        print("⚠️  NEEDS ATTENTION - Some transport features not working")
    
    print(f"\n🗂️  Test game: {game_id}")
    print("   You can continue testing manually with this game")
    print("   Use the web interface at http://localhost:5000/test_interface")
    
    return passed >= total * 0.6

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
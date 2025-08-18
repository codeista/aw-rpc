#!/usr/bin/env python3
"""
Server Persistence Tests
Tests that game state survives server restarts and reloads correctly
This test file addresses the critical gap where games were disappearing after server restart
"""

import requests
import json
import time
import subprocess
import os
import signal
import sys

API_URL = "http://localhost:5000/api"

def rpc_call(method, params):
    """Make an RPC call to the game server"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    response = requests.post(API_URL, json=payload, timeout=10)
    result = response.json()
    if "error" in result:
        raise Exception(f"RPC Error: {result['error']}")
    return result.get("result")

def wait_for_server(timeout=30):
    """Wait for server to be available"""
    print("⏳ Waiting for server to be available...")
    for i in range(timeout):
        try:
            response = requests.get("http://localhost:5000", timeout=1)
            if response.status_code == 200:
                print("✅ Server is available")
                return True
        except:
            pass
        time.sleep(1)
    print("❌ Server not available after timeout")
    return False

def find_server_process():
    """Find the running Flask server process"""
    try:
        result = subprocess.run(['pgrep', '-f', 'python.*app.py'], 
                              capture_output=True, text=True)
        if result.stdout:
            return int(result.stdout.strip().split('\n')[0])
    except:
        pass
    return None

def stop_server():
    """Stop the Flask server"""
    pid = find_server_process()
    if pid:
        print(f"🛑 Stopping server (PID: {pid})")
        os.kill(pid, signal.SIGTERM)
        time.sleep(2)
        # Check if still running
        if find_server_process():
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
        print("✅ Server stopped")
        return True
    else:
        print("⚠️  No server process found")
        return False

def start_server():
    """Start the Flask server in background"""
    print("🚀 Starting server...")
    process = subprocess.Popen(['python3', 'app.py'], 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL)
    time.sleep(3)  # Give server time to start
    if wait_for_server():
        print(f"✅ Server started (PID: {process.pid})")
        return process
    else:
        print("❌ Failed to start server")
        return None

def test_game_persistence_across_restart():
    """Test that games persist across server restarts"""
    
    print("\n🧪 Testing Game Persistence Across Server Restart")
    print("=" * 60)
    
    # Step 1: Create a game with specific state
    token = f"persist-test-{int(time.time())}"
    print(f"\n1️⃣ Creating test game: {token}")
    
    result = rpc_call("game_create_test", {"token": token})
    assert result == "ok", f"Failed to create game: {result}"
    print("✅ Game created")
    
    # Step 2: Add some state to the game
    print("\n2️⃣ Adding game state...")
    
    # Create a unit
    result = rpc_call("unit_create", {
        "token": token,
        "player_id": 0,
        "unit_type": "TANK",
        "x": 2,
        "y": 2
    })
    print("✅ Created tank at (2,2)")
    
    # End turn to change game state
    result = rpc_call("army_end_turn", {"token": token})
    print("✅ Ended turn for player 0")
    
    # Get current game state for comparison
    board_before = rpc_call("game_board", {"token": token})
    funds_before = board_before.get("player_funds", [])
    day_before = board_before.get("day", 1)
    current_player_before = board_before.get("current_player", 0)
    
    # Find the tank
    tank_found = False
    for tile in board_before.get("grid", []):
        if tile.get("unit") and tile["x"] == 2 and tile["y"] == 2:
            tank_found = True
            tank_hp_before = tile["unit"]["hp"]
            break
    
    assert tank_found, "Tank not found in game state before restart"
    
    print(f"📊 State before restart:")
    print(f"   - Day: {day_before}")
    print(f"   - Current player: {current_player_before}")
    print(f"   - Tank HP: {tank_hp_before}")
    print(f"   - Player funds: {funds_before}")
    
    # Step 3: Stop the server
    print("\n3️⃣ Stopping server...")
    stop_server()
    
    # Step 4: Start the server again
    print("\n4️⃣ Restarting server...")
    server_process = start_server()
    if not server_process:
        raise Exception("Failed to restart server")
    
    # Step 5: Try to load the game
    print(f"\n5️⃣ Loading game after restart: {token}")
    
    try:
        board_after = rpc_call("game_board", {"token": token})
    except Exception as e:
        print(f"❌ Failed to load game after restart: {e}")
        raise Exception("Game did not persist across server restart!")
    
    print("✅ Game loaded successfully after restart")
    
    # Step 6: Verify game state is intact
    print("\n6️⃣ Verifying game state...")
    
    funds_after = board_after.get("player_funds", [])
    day_after = board_after.get("day", 0)
    current_player_after = board_after.get("current_player", -1)
    
    # Find the tank again
    tank_found_after = False
    for tile in board_after.get("grid", []):
        if tile.get("unit") and tile["x"] == 2 and tile["y"] == 2:
            tank_found_after = True
            tank_hp_after = tile["unit"]["hp"]
            break
    
    print(f"📊 State after restart:")
    print(f"   - Day: {day_after}")
    print(f"   - Current player: {current_player_after}")
    print(f"   - Tank found: {tank_found_after}")
    if tank_found_after:
        print(f"   - Tank HP: {tank_hp_after}")
    print(f"   - Player funds: {funds_after}")
    
    # Verify state matches
    errors = []
    
    if day_after != day_before:
        errors.append(f"Day changed: {day_before} -> {day_after}")
    
    if current_player_after != current_player_before:
        errors.append(f"Current player changed: {current_player_before} -> {current_player_after}")
    
    if not tank_found_after:
        errors.append("Tank disappeared after restart")
    elif tank_hp_after != tank_hp_before:
        errors.append(f"Tank HP changed: {tank_hp_before} -> {tank_hp_after}")
    
    if funds_after != funds_before:
        errors.append(f"Funds changed: {funds_before} -> {funds_after}")
    
    if errors:
        print("\n❌ State verification failed:")
        for error in errors:
            print(f"   - {error}")
        raise Exception("Game state not preserved correctly across restart")
    
    print("✅ All state verified - game persisted correctly!")
    
    # Step 7: Test that we can continue playing
    print("\n7️⃣ Testing continued gameplay...")
    
    # Try to create another unit
    result = rpc_call("unit_create", {
        "token": token,
        "player_id": 1,  # Player 1's turn now
        "unit_type": "INFANTRY",
        "x": 8,
        "y": 8
    })
    print("✅ Successfully created new unit after restart")
    
    # End turn
    result = rpc_call("army_end_turn", {"token": token})
    print("✅ Successfully ended turn after restart")
    
    print("\n" + "=" * 60)
    print("✅ TEST PASSED - Game persists correctly across server restart!")
    return True

def test_multiple_games_persistence():
    """Test that multiple games persist correctly"""
    
    print("\n🧪 Testing Multiple Games Persistence")
    print("=" * 60)
    
    # Create multiple games
    tokens = []
    for i in range(3):
        token = f"multi-persist-{i}-{int(time.time())}"
        result = rpc_call("game_create_test", {"token": token})
        tokens.append(token)
        print(f"✅ Created game {i+1}: {token}")
        
        # Add unique state to each game
        result = rpc_call("unit_create", {
            "token": token,
            "player_id": 0,
            "unit_type": "INFANTRY",
            "x": i + 1,
            "y": i + 1
        })
    
    print(f"\n📊 Created {len(tokens)} games")
    
    # Restart server
    print("\n🔄 Restarting server...")
    stop_server()
    start_server()
    
    # Verify all games exist
    print("\n🔍 Verifying all games persist...")
    all_found = True
    for i, token in enumerate(tokens):
        try:
            board = rpc_call("game_board", {"token": token})
            # Find the unit at expected position
            unit_found = False
            for tile in board.get("grid", []):
                if tile.get("unit") and tile["x"] == i+1 and tile["y"] == i+1:
                    unit_found = True
                    break
            if unit_found:
                print(f"✅ Game {i+1} exists with correct state")
            else:
                print(f"❌ Game {i+1} exists but state is wrong")
                all_found = False
        except:
            print(f"❌ Game {i+1} not found after restart")
            all_found = False
    
    if all_found:
        print("\n✅ TEST PASSED - All games persisted correctly!")
        return True
    else:
        print("\n❌ TEST FAILED - Some games lost after restart")
        return False

def test_game_state_recovery_after_crash():
    """Test that game state can recover from unexpected shutdown"""
    
    print("\n🧪 Testing Game State Recovery After Crash")
    print("=" * 60)
    
    token = f"crash-test-{int(time.time())}"
    
    # Create game with complex state
    print("1️⃣ Creating game with complex state...")
    result = rpc_call("game_create_test", {"token": token})
    
    # Create multiple units
    units_created = []
    positions = [(1,1), (2,2), (3,3)]
    for x, y in positions:
        result = rpc_call("unit_create", {
            "token": token,
            "player_id": 0,
            "unit_type": "INFANTRY",
            "x": x,
            "y": y
        })
        units_created.append((x, y))
        print(f"✅ Created unit at ({x},{y})")
    
    # Simulate sudden crash (SIGKILL)
    print("\n2️⃣ Simulating server crash (SIGKILL)...")
    pid = find_server_process()
    if pid:
        os.kill(pid, signal.SIGKILL)
        time.sleep(2)
        print("💥 Server killed suddenly")
    
    # Restart server
    print("\n3️⃣ Restarting server after crash...")
    start_server()
    
    # Check if game recovered
    print(f"\n4️⃣ Checking game recovery: {token}")
    try:
        board = rpc_call("game_board", {"token": token})
        
        # Verify all units exist
        units_found = 0
        for x, y in units_created:
            for tile in board.get("grid", []):
                if tile.get("unit") and tile["x"] == x and tile["y"] == y:
                    units_found += 1
                    break
        
        print(f"📊 Recovery status:")
        print(f"   - Units created: {len(units_created)}")
        print(f"   - Units recovered: {units_found}")
        
        if units_found == len(units_created):
            print("\n✅ TEST PASSED - Game fully recovered after crash!")
            return True
        else:
            print(f"\n⚠️  TEST PARTIAL - {units_found}/{len(units_created)} units recovered")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST FAILED - Game not recovered: {e}")
        return False

def main():
    """Run all persistence tests"""
    
    print("🚀 Starting Server Persistence Test Suite")
    print("=" * 60)
    
    # Ensure server is running initially
    if not wait_for_server(timeout=5):
        print("📌 Starting initial server...")
        start_server()
    
    tests = [
        ("Game Persistence Across Restart", test_game_persistence_across_restart),
        ("Multiple Games Persistence", test_multiple_games_persistence),
        ("Game Recovery After Crash", test_game_state_recovery_after_crash),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n💥 Test crashed: {e}")
            failed += 1
        
        # Ensure server is running for next test
        if not find_server_process():
            start_server()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PERSISTENCE TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All persistence tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} persistence tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Simple test to verify the combat serialization fix works
"""
import subprocess
import sys
import time

def run_test():
    """Run a simple combat test via the test interface"""
    print("Testing combat serialization fix...")
    
    # Start the test via test interface
    print("\n1. Starting combat test game...")
    
    # Use curl to trigger the test game creation
    cmd = [
        "curl", "-s", 
        "http://localhost:5000/test_routes/run_test?test_type=combat"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to start test: {result.stderr}")
        return False
        
    # Extract game URL from response
    response = result.stdout
    if "window.location.href" in response:
        # Extract token from redirect
        start = response.find("/game/") + 6
        end = response.find('"', start)
        token = response[start:end]
        print(f"✓ Test game created with token: {token}")
    else:
        print(f"❌ Unexpected response: {response}")
        return False
    
    # Give the game a moment to initialize
    time.sleep(0.5)
    
    print("\n2. Testing combat via RPC...")
    
    # Test the combat workflow
    test_script = f'''
import requests
import json

def rpc_call(method, params):
    response = requests.post("http://localhost:5000/api", json={{
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }})
    return response.json().get("result", {{}})

# Get board state
board = rpc_call("game_board", {{"token": "{token}"}})
print("Current turn:", board.get("current_turn"))

# Find units
units = [(t["x"], t["y"], t["unit"]["type"], t["unit"]["army"]) 
         for t in board.get("tiles", []) if t.get("unit")]
print(f"Found {{len(units)}} units:", units)

# Find RED and BLUE units that are adjacent
red_unit = None
blue_unit = None

for x, y, unit_type, army in units:
    if army == 0 and not red_unit:
        red_unit = (x, y, unit_type)
    elif army == 1 and not blue_unit:
        blue_unit = (x, y, unit_type)

if not red_unit or not blue_unit:
    print("❌ Could not find both RED and BLUE units")
    exit(1)

print(f"RED unit: {{red_unit[2]}} at ({{red_unit[0]}}, {{red_unit[1]}})")
print(f"BLUE unit: {{blue_unit[2]}} at ({{blue_unit[0]}}, {{blue_unit[1]}})")

# Execute attack
print("\\nExecuting attack...")
try:
    result = rpc_call("unit_attack", {{
        "token": "{token}",
        "attacker_x": red_unit[0],
        "attacker_y": red_unit[1],
        "target_x": blue_unit[0],
        "target_y": blue_unit[1]
    }})
    
    # Check if result is a dictionary (not EnhancedCombatResult)
    if not isinstance(result, dict):
        print(f"❌ Result is not a dict: {{type(result)}}")
        exit(1)
    
    # Check if we can access fields with .get()
    if result.get("success"):
        print("✓ Attack succeeded!")
        print(f"  Damage dealt: {{result.get('attacker_damage_dealt', 0)}}")
        print(f"  Counter damage: {{result.get('defender_damage_dealt', 0)}}")
        print(f"  Defender destroyed: {{result.get('defender_destroyed', False)}}")
        
        # Verify JSON serializable
        json.dumps(result)
        print("✓ Result is JSON serializable")
    else:
        print(f"❌ Attack failed: {{result.get('error', 'Unknown error')}}")
        exit(1)
        
except Exception as e:
    print(f"❌ Exception during attack: {{e}}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\\n✅ Combat serialization test PASSED!")
'''
    
    # Run the test script
    result = subprocess.run([sys.executable, "-c", test_script], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0

if __name__ == "__main__":
    # Check server is running
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:5000"], 
            capture_output=True, 
            timeout=2
        )
        if result.returncode != 0:
            print("❌ Server not running at http://localhost:5000")
            print("Please start the server with: python3 app.py")
            exit(1)
    except subprocess.TimeoutExpired:
        print("❌ Server timeout")
        exit(1)
    
    # Run the test
    if run_test():
        print("\n✅ ALL TESTS PASSED!")
        exit(0)
    else:
        print("\n❌ TEST FAILED!")
        exit(1)
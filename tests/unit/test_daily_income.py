#!/usr/bin/env python3
"""
Test Daily Income System
Verify that armies receive daily income from their properties
"""

import requests
import json

def rpc_call(method, params=None):
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
    
    rpc_result = result.get("result", result)
    if isinstance(rpc_result, str):
        try:
            rpc_result = json.loads(rpc_result)
        except json.JSONDecodeError:
            pass
    
    return rpc_result

def test_daily_income():
    """Test that armies receive daily income when turns end"""
    print("💰 Testing Daily Income System")
    print("=" * 50)
    
    # Create optimized test game
    try:
        response = requests.get("http://localhost:5000/test_optimized", allow_redirects=False)
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            game_id = location.split('/')[-1] if '/' in location else None
            
            if not game_id:
                print("❌ Could not create test game")
                return False
                
            print(f"✅ Created test game: {game_id}")
            
            # Get initial board state
            board = rpc_call("game_board", {"token": game_id})
            if "error" in board:
                print(f"❌ Could not get board: {board['error']}")
                return False
            
            initial_funds = board.get("army_funds", {})
            army_properties = board.get("army_properties", {})
            current_turn = board.get("current_turn", "UNKNOWN")
            
            print(f"🏁 Initial State:")
            print(f"   Current turn: {current_turn}")
            for army, funds in initial_funds.items():
                properties = army_properties.get(army, 0)
                print(f"   {army}: {funds} funds, {properties} properties")
            
            # End turn to trigger income
            print(f"\n⏭️ Ending {current_turn}'s turn...")
            turn_result = rpc_call("army_end_turn", {"token": game_id})
            
            if "error" in turn_result:
                print(f"❌ Could not end turn: {turn_result['error']}")
                return False
            
            # Get updated board state
            new_board = rpc_call("game_board", {"token": game_id})
            if "error" in new_board:
                print(f"❌ Could not get updated board: {new_board['error']}")
                return False
            
            new_funds = new_board.get("army_funds", {})
            new_current_turn = new_board.get("current_turn", "UNKNOWN")
            
            print(f"\n📊 After Turn End:")
            print(f"   Current turn: {new_current_turn}")
            
            income_received = False
            for army in initial_funds.keys():
                old_funds = initial_funds[army]
                new_funds_amt = new_funds.get(army, old_funds)
                properties = army_properties.get(army, 0)
                expected_income = properties * 1000  # Each property gives 1000 funds
                
                if new_funds_amt > old_funds:
                    actual_income = new_funds_amt - old_funds
                    print(f"   {army}: {old_funds} → {new_funds_amt} (+{actual_income}) [Expected: +{expected_income}]")
                    
                    if actual_income == expected_income:
                        print(f"      ✅ Correct income received!")
                        income_received = True
                    else:
                        print(f"      ⚠️ Income mismatch - got {actual_income}, expected {expected_income}")
                else:
                    print(f"   {army}: {old_funds} → {new_funds_amt} (no change)")
                    if properties > 0:
                        print(f"      ❌ Should have received {expected_income} income!")
            
            if income_received:
                print(f"\n🎉 SUCCESS: Daily income system is working!")
                print(f"🎮 Test game: http://localhost:5000/game/{game_id}")
                return True
            else:
                print(f"\n❌ FAILURE: No income was received")
                return False
                
        else:
            print(f"❌ Could not create game: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 Daily Income System Test")
    print("=" * 60)
    
    success = test_daily_income()
    
    if success:
        print("\n✅ DAILY INCOME SYSTEM IS WORKING CORRECTLY!")
        print("Armies will now receive 1000 funds per property each turn.")
    else:
        print("\n❌ Daily income system needs fixing")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
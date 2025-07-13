#!/usr/bin/env python3
"""
Test Daily Income with Cross Map (4-player map that should have properties)
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

def test_cross_map_income():
    """Test income on cross map which should have properties"""
    print("💰 Testing Daily Income on Cross Map")
    print("=" * 50)
    
    # Create cross map game (4-player with properties)
    try:
        response = requests.get("http://localhost:5000/test_cross", allow_redirects=False)
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            game_id = location.split('/')[-1] if '/' in location else None
            
            if not game_id:
                print("❌ Could not create cross map game")
                return False
                
            print(f"✅ Created cross map game: {game_id}")
            
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
            
            # If no properties, armies won't get income. Let's try multiple turns to see if income works
            print(f"\n⏭️ Testing income over multiple turns...")
            
            for turn_num in range(3):
                current_board = rpc_call("game_board", {"token": game_id})
                current_turn = current_board.get("current_turn", "UNKNOWN")
                current_funds = current_board.get("army_funds", {})
                current_properties = current_board.get("army_properties", {})
                
                print(f"\nTurn {turn_num + 1}: {current_turn}'s turn")
                for army, funds in current_funds.items():
                    properties = current_properties.get(army, 0)
                    print(f"   {army}: {funds} funds, {properties} properties")
                
                # End turn
                turn_result = rpc_call("army_end_turn", {"token": game_id})
                if "error" in turn_result:
                    print(f"❌ Could not end turn: {turn_result['error']}")
                    break
            
            # Check final state
            final_board = rpc_call("game_board", {"token": game_id})
            final_funds = final_board.get("army_funds", {})
            final_properties = final_board.get("army_properties", {})
            
            print(f"\n📊 Final State:")
            income_working = False
            for army in initial_funds.keys():
                initial = initial_funds[army]
                final = final_funds.get(army, initial)
                properties = final_properties.get(army, 0)
                
                if final > initial:
                    income_gained = final - initial
                    print(f"   {army}: {initial} → {final} (+{income_gained}) with {properties} properties")
                    income_working = True
                else:
                    print(f"   {army}: {initial} → {final} (no change) with {properties} properties")
            
            if income_working:
                print(f"\n🎉 SUCCESS: Daily income system is working!")
                print(f"🎮 Test game: http://localhost:5000/game/{game_id}")
                return True
            else:
                # If armies have properties but no income, that's the bug
                total_properties = sum(final_properties.values())
                if total_properties > 0:
                    print(f"\n❌ FAILURE: {total_properties} total properties but no income received!")
                    print("This confirms the daily income bug.")
                else:
                    print(f"\n⚠️ No properties on this map - income system cannot be tested")
                return False
                
        else:
            print(f"❌ Could not create game: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 Cross Map Daily Income Test")
    print("=" * 60)
    
    success = test_cross_map_income()
    
    if success:
        print("\n✅ DAILY INCOME SYSTEM IS WORKING!")
    else:
        print("\n❌ Daily income system still needs work")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
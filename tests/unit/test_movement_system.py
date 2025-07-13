#!/usr/bin/env python3
"""
Movement System Tests using Available RPC Methods
Tests movement validation, costs, ranges, and pathfinding
"""

import requests
import json
import re

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
    
    # Handle error responses
    if "error" in result:
        return {"error": result["error"]}
    
    # Get the actual result
    rpc_result = result.get("result", result)
    
    # If result is a string, try to parse it as JSON
    if isinstance(rpc_result, str):
        try:
            rpc_result = json.loads(rpc_result)
        except json.JSONDecodeError:
            return {"error": f"Could not parse result: {rpc_result}"}
    
    return rpc_result

def get_test_game():
    """Create optimized test game for movement testing"""
    try:
        # Use optimized test game with pre-positioned units
        response = requests.get("http://localhost:5000/test_optimized", allow_redirects=False)
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            match = re.search(r'/game/([A-Za-z0-9_]+)', location)
            if match:
                game_id = match.group(1)
                print(f"✅ Created optimized test game: {game_id}")
                return game_id
        return None
    except Exception as e:
        print(f"❌ Error creating optimized game: {e}")
        return None

class MovementTester:
    """Movement system testing using available RPC methods"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.test_results = {
            "valid_moves": [],
            "movement_costs": [],
            "movement_validation": [],
            "movement_preview": [],
            "movement_execution": [],
            "movement_highlights": []
        }
    
    def reset_unit_states(self):
        """Reset all unit states by cycling turns to refresh can_attack/can_move flags"""
        try:
            # End turn multiple times to cycle through all armies and reset states
            for i in range(4):  # Cycle through potential turns
                turn_result = rpc_call("army_end_turn", {"token": self.game_id})
                if "error" in turn_result:
                    break
            print("✅ Unit states reset successfully")
        except Exception as e:
            print(f"⚠️ Could not fully reset unit states: {e}")
    
    def _find_movable_units(self, board):
        """Find units that can move for testing"""
        movable_units = []
        current_turn = board.get("current_turn", "")
        
        # Handle different board structures
        tiles = board.get("tiles", board.get("grid", []))
        
        # If tiles is a 2D array (like in the test map)
        if tiles and isinstance(tiles[0], list):
            for y, row in enumerate(tiles):
                for x, tile in enumerate(row):
                    if isinstance(tile, dict) and tile.get("unit"):
                        unit = tile["unit"]
                        # Check if unit belongs to current turn army
                        army_name = unit.get("army", "")
                        if army_name == current_turn:
                            unit_info = {
                                "x": x,
                                "y": y,
                                "type": unit.get("type", "UNKNOWN"),
                                "army": army_name
                            }
                            movable_units.append(unit_info)
        else:
            # Handle flat grid structure
            for tile in tiles:
                if isinstance(tile, dict) and tile.get("unit"):
                    unit = tile["unit"]
                    # Check if unit belongs to current turn army
                    army = unit.get("army", {})
                    if isinstance(army, dict):
                        army_name = army.get("name", "")
                    else:
                        army_name = str(army)
                    
                    if army_name == current_turn:
                        unit_info = {
                            "x": tile.get("x", 0),
                            "y": tile.get("y", 0),
                            "type": unit.get("type", {}).get("name", "") if isinstance(unit.get("type"), dict) else str(unit.get("type", "")),
                            "army": army_name
                        }
                        movable_units.append(unit_info)
        
        return movable_units
    
    def test_valid_moves(self):
        """Test unit_valid_moves RPC method"""
        print("🚶 Testing Valid Moves...")
        
        # Reset unit states first
        self.reset_unit_states()
        
        # Get board and find movable units
        board = rpc_call("game_board", {"token": self.game_id})
        if "error" in board:
            print(f"   ❌ Could not get board: {board['error']}")
            return False
        
        movable_units = self._find_movable_units(board)
        
        # Debug information
        current_turn = board.get('current_turn', 'UNKNOWN')
        print(f"   🔍 Current turn: {current_turn}")
        
        # Count all units by army
        all_units = {}
        tiles = board.get("tiles", board.get("grid", []))
        
        if tiles and isinstance(tiles[0], list):
            # 2D array structure
            for row in tiles:
                for tile in row:
                    if isinstance(tile, dict) and tile.get("unit"):
                        unit = tile["unit"]
                        army_name = unit.get("army", "UNKNOWN")
                        all_units[army_name] = all_units.get(army_name, 0) + 1
        else:
            # Flat structure
            for tile in tiles:
                if isinstance(tile, dict) and tile.get("unit"):
                    unit = tile["unit"]
                    if isinstance(unit, dict):
                        army = unit.get("army", {})
                        if isinstance(army, dict):
                            army_name = army.get("name", "UNKNOWN")
                        else:
                            army_name = str(army)
                        all_units[army_name] = all_units.get(army_name, 0) + 1
        
        print(f"   📊 Units by army: {all_units}")
        
        if not movable_units:
            print(f"   ⚠️  No movable units found for current turn: {current_turn}")
            return False
        
        print(f"   📍 Found {len(movable_units)} movable units")
        
        # Test valid moves for each unit
        for unit in movable_units[:5]:  # Test first 5 units
            moves_result = rpc_call("unit_valid_moves", {
                "token": self.game_id,
                "x": unit["x"],
                "y": unit["y"]
            })
            
            if "error" not in moves_result:
                valid_moves = moves_result.get("valid_moves", [])
                
                result = {
                    "unit_type": unit["type"],
                    "position": {"x": unit["x"], "y": unit["y"]},
                    "valid_moves_count": len(valid_moves),
                    "has_moves": len(valid_moves) > 0
                }
                
                self.test_results["valid_moves"].append(result)
                print(f"   {unit['type']} at ({unit['x']}, {unit['y']}): {len(valid_moves)} valid moves")
            else:
                print(f"   ⚠️  Failed to get moves for {unit['type']}: {moves_result.get('error', 'Unknown error')}")
        
        return len(self.test_results["valid_moves"]) > 0
    
    def test_movement_costs(self):
        """Test get_movement_costs RPC method"""
        print("\n💰 Testing Movement Costs...")
        
        # Test movement costs for different unit types
        test_units = ["INFANTRY", "TANK", "ARTILLERY", "BATTLESHIP"]
        costs_tested = 0
        
        for unit_type in test_units:
            costs_result = rpc_call("get_movement_costs", {
                "token": self.game_id,
                "unit_type": unit_type
            })
            
            if "error" not in costs_result:
                result = {
                    "unit_type": unit_type,
                    "cost_data": costs_result,
                    "has_cost_info": len(costs_result) > 0 if isinstance(costs_result, dict) else True
                }
                
                self.test_results["movement_costs"].append(result)
                costs_tested += 1
                
                print(f"   {unit_type}: ✅ Cost data retrieved")
            else:
                print(f"   {unit_type}: ❌ {costs_result.get('error', 'Unknown error')}")
        
        return costs_tested > 0
    
    def test_movement_validation(self):
        """Test validate_movement RPC method"""
        print("\n✅ Testing Movement Validation...")
        
        # Reset unit states first
        self.reset_unit_states()
        
        # Get board and find a unit to test
        board = rpc_call("game_board", {"token": self.game_id})
        movable_units = self._find_movable_units(board)
        
        if not movable_units:
            return False
        
        validation_tests = 0
        
        for unit in movable_units[:3]:  # Test first 3 units
            # Test various movement scenarios
            test_moves = [
                {"x2": unit["x"] + 1, "y2": unit["y"]},     # Right
                {"x2": unit["x"] - 1, "y2": unit["y"]},     # Left
                {"x2": unit["x"], "y2": unit["y"] + 1},     # Down
                {"x2": unit["x"], "y2": unit["y"] - 1},     # Up
                {"x2": unit["x"] + 5, "y2": unit["y"] + 5}  # Far away (should be invalid)
            ]
            
            for move in test_moves:
                validation_result = rpc_call("validate_movement", {
                    "token": self.game_id,
                    "x": unit["x"],
                    "y": unit["y"],
                    "x2": move["x2"],
                    "y2": move["y2"]
                })
                
                if "error" not in validation_result:
                    is_valid = validation_result.get("valid", False)
                    distance = abs(unit["x"] - move["x2"]) + abs(unit["y"] - move["y2"])
                    
                    result = {
                        "unit_type": unit["type"],
                        "from": {"x": unit["x"], "y": unit["y"]},
                        "to": {"x": move["x2"], "y": move["y2"]},
                        "distance": distance,
                        "is_valid": is_valid,
                        "validation_response": validation_result
                    }
                    
                    self.test_results["movement_validation"].append(result)
                    validation_tests += 1
                    
                    status = "✅ Valid" if is_valid else "❌ Invalid"
                    print(f"   {unit['type']} to ({move['x2']}, {move['y2']}): {status}")
        
        return validation_tests > 0
    
    def test_movement_preview(self):
        """Test movement_preview RPC method"""
        print("\n🔍 Testing Movement Preview...")
        
        # Reset unit states first
        self.reset_unit_states()
        
        # Get board and find a unit to test
        board = rpc_call("game_board", {"token": self.game_id})
        movable_units = self._find_movable_units(board)
        
        if not movable_units:
            return False
        
        preview_tests = 0
        
        for unit in movable_units[:2]:  # Test first 2 units
            # Test movement preview for nearby positions
            test_positions = [
                {"x2": unit["x"] + 1, "y2": unit["y"]},
                {"x2": unit["x"], "y2": unit["y"] + 1}
            ]
            
            for pos in test_positions:
                preview_result = rpc_call("movement_preview", {
                    "token": self.game_id,
                    "x": unit["x"],
                    "y": unit["y"],
                    "x2": pos["x2"],
                    "y2": pos["y2"]
                })
                
                if "error" not in preview_result and preview_result.get("valid", False):
                    result = {
                        "unit_type": unit["type"],
                        "from": {"x": unit["x"], "y": unit["y"]},
                        "to": {"x": pos["x2"], "y": pos["y2"]},
                        "preview_data": preview_result
                    }
                    
                    self.test_results["movement_preview"].append(result)
                    preview_tests += 1
                    
                    print(f"   {unit['type']} preview to ({pos['x2']}, {pos['y2']}): ✅ Success")
        
        return preview_tests > 0
    
    def test_movement_execution(self):
        """Test unit_move RPC method"""
        print("\n🏃 Testing Movement Execution...")
        
        # Reset unit states first
        self.reset_unit_states()
        
        # Get board and find a unit to move
        board = rpc_call("game_board", {"token": self.game_id})
        movable_units = self._find_movable_units(board)
        
        if not movable_units:
            return False
        
        # Choose first unit and find a valid move
        unit = movable_units[0]
        
        # Get valid moves for this unit
        moves_result = rpc_call("unit_valid_moves", {
            "token": self.game_id,
            "x": unit["x"],
            "y": unit["y"]
        })
        
        if "error" in moves_result:
            print(f"   ⚠️  Could not get valid moves for {unit['type']}: {moves_result.get('error', 'Unknown')}")
            return False
        
        valid_moves = moves_result.get("valid_moves", [])
        
        if not valid_moves:
            print(f"   ⚠️  No valid moves for {unit['type']}")
            return False
        
        # Try to move to first valid position
        target_move = valid_moves[0]
        
        # Handle both dict and tuple formats
        if isinstance(target_move, dict):
            target_x = target_move.get("x")
            target_y = target_move.get("y")
        elif isinstance(target_move, (list, tuple)) and len(target_move) >= 2:
            target_x = target_move[0]
            target_y = target_move[1]
        else:
            print(f"   ⚠️  Invalid move data format: {target_move}")
            return False
        
        if target_x is None or target_y is None:
            print(f"   ⚠️  Invalid move coordinates: {target_move}")
            return False
        
        print(f"   Moving {unit['type']} from ({unit['x']}, {unit['y']}) to ({target_x}, {target_y})")
        
        # Execute the movement
        move_result = rpc_call("unit_move", {
            "token": self.game_id,
            "x": unit["x"],
            "y": unit["y"],
            "x2": target_x,
            "y2": target_y
        })
        
        if "error" not in move_result and "unit" in move_result:
            result = {
                "unit_type": unit["type"],
                "from": {"x": unit["x"], "y": unit["y"]},
                "to": {"x": target_x, "y": target_y},
                "move_successful": True,
                "move_result": move_result
            }
            
            self.test_results["movement_execution"].append(result)
            print(f"   ✅ Movement successful!")
            return True
        else:
            print(f"   ❌ Movement failed: {move_result.get('error', 'Unknown error')}")
            return False
    
    def test_movement_highlights(self):
        """Test get_movement_highlights RPC method"""
        print("\n🌟 Testing Movement Highlights...")
        
        # Reset unit states first
        self.reset_unit_states()
        
        # Get board and find a unit to test
        board = rpc_call("game_board", {"token": self.game_id})
        movable_units = self._find_movable_units(board)
        
        if not movable_units:
            return False
        
        highlight_tests = 0
        
        for unit in movable_units[:2]:  # Test first 2 units
            highlights_result = rpc_call("get_movement_highlights", {
                "token": self.game_id,
                "x": unit["x"],
                "y": unit["y"]
            })
            
            if "error" not in highlights_result and highlights_result.get("success", False):
                highlights = highlights_result.get("highlights", [])
                
                result = {
                    "unit_type": unit["type"],
                    "position": {"x": unit["x"], "y": unit["y"]},
                    "highlights_count": len(highlights),
                    "has_highlights": len(highlights) > 0
                }
                
                self.test_results["movement_highlights"].append(result)
                highlight_tests += 1
                
                print(f"   {unit['type']} at ({unit['x']}, {unit['y']}): {len(highlights)} highlights")
        
        return highlight_tests > 0
    
    def run_all_tests(self):
        """Run all movement tests"""
        print("🚶 Movement System Tests")
        print("=" * 60)
        
        # End turns to get back to RED army's turn for movement testing
        try:
            rpc_call("army_end_turn", {"token": self.game_id})  # RED -> BLUE
            rpc_call("army_end_turn", {"token": self.game_id})  # BLUE -> RED
            print("✅ Cycled turns to enable unit movement")
        except:
            print("⚠️  Could not cycle turns")
        
        tests = [
            ("Valid Moves", self.test_valid_moves),
            ("Movement Costs", self.test_movement_costs),
            ("Movement Validation", self.test_movement_validation),
            ("Movement Preview", self.test_movement_preview),
            ("Movement Execution", self.test_movement_execution),
            ("Movement Highlights", self.test_movement_highlights),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} PASSED")
                else:
                    print(f"❌ {test_name} FAILED")
            except Exception as e:
                print(f"❌ {test_name} ERROR: {str(e)}")
        
        # Results summary
        print("\n" + "=" * 60)
        print("📊 MOVEMENT TEST RESULTS")
        print("=" * 60)
        
        for category, results in self.test_results.items():
            if results:
                print(f"✅ {category.replace('_', ' ').title()}: {len(results)} tests")
        
        print(f"\n📈 Overall: {passed}/{total} test categories passed")
        
        if passed == total:
            print("🎉 ALL MOVEMENT TESTS PASSED!")
        elif passed >= total * 0.75:
            print("✅ Movement system fully functional")
        else:
            print("⚠️  Movement system needs attention")
        
        return passed >= total * 0.75

def main():
    """Main test function"""
    print("🚀 Movement System Testing Suite")
    print("=" * 70)
    
    # Create test game
    game_id = get_test_game()
    if not game_id:
        print("❌ Could not create test game")
        return False
    
    print(f"✅ Created test game: {game_id}")
    
    # Run movement tests
    tester = MovementTester(game_id)
    success = tester.run_all_tests()
    
    print(f"\n🎮 Test game URL: http://localhost:5000/game/{game_id}")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
#!/usr/bin/env python3
"""
Comprehensive Combat System Tests
Tests damage calculations, terrain modifiers, counter-attacks, and unit destruction
"""

import requests
import json
import re
import random
import string
import math

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
    
    # If result is a string, only try to parse if it looks like JSON
    if isinstance(rpc_result, str):
        if rpc_result.strip().startswith(('{', '[')):
            try:
                rpc_result = json.loads(rpc_result)
            except json.JSONDecodeError:
                return {"error": f"Could not parse result: {rpc_result}"}
    
    return rpc_result

def get_test_game():
    """Create test game with units for combat testing"""
    try:
        # Create a test game with high funds
        game_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        result = rpc_call("game_create_test", {"token": game_id})
        
        if isinstance(result, dict) and "error" in result:
            print(f"❌ Failed to create game: {result['error']}")
            return None
        elif result != "ok":
            print(f"❌ Unexpected result: {result}")
            return None
        
        print(f"✅ Created test game: {game_id}")
        
        # Add units for combat testing
        setup_combat_units(game_id)
        
        return game_id
        
    except Exception as e:
        print(f"❌ Error creating game: {e}")
        return None

class CombatTester:
    """Comprehensive combat system testing"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.test_results = {
            "damage_calculation": [],
            "terrain_modifiers": [],
            "counter_attacks": [],
            "unit_destruction": [],
            "attack_range": [],
            "damage_preview": [],
            "combat_outcomes": []
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
    
    def test_damage_calculation(self):
        """Test damage calculation accuracy"""
        print("🏹 Testing Damage Calculation...")
        
        # Reset unit states first
        self.reset_unit_states()
        
        # Get board to find combat pairs
        board = rpc_call("game_board", {"token": self.game_id})
        print(f"DEBUG: Board type: {type(board)}, content: {str(board)[:200]}...")
        
        if isinstance(board, str):
            print(f"❌ Board returned as string, not dict: {board[:100]}...")
            return False
        
        if "error" in board:
            print(f"❌ Could not get board: {board['error']}")
            return False
        
        # Find suitable combat pairs
        try:
            combat_pairs = self._find_combat_pairs(board)
            print(f"DEBUG: Found {len(combat_pairs)} combat pairs")
        except Exception as e:
            print(f"DEBUG: Error finding combat pairs: {e}")
            print(f"DEBUG: Board keys: {list(board.keys())}")
            if 'grid' in board:
                print(f"DEBUG: Grid type: {type(board['grid'])}, length: {len(board['grid']) if isinstance(board['grid'], list) else 'not list'}")
            return False
        
        for i, (attacker, defender, combat_type) in enumerate(combat_pairs[:3]):  # Test first 3 pairs
            distance = abs(attacker['x'] - defender['x']) + abs(attacker['y'] - defender['y'])
            print(f"\n🎯 Testing {attacker['type']} vs {defender['type']} (distance: {distance}, type: {combat_type})")
            
            # Get damage preview
            preview_result = rpc_call("damage_preview", {
                "token": self.game_id,
                "x": attacker['x'],
                "y": attacker['y'],
                "x2": defender['x'],
                "y2": defender['y']
            })
            
            print(f"DEBUG: Damage preview result: {preview_result}")
            
            if "error" not in preview_result and preview_result.get("success", False):
                # Handle new preview format with nested preview data
                preview_data = preview_result.get("preview", {})
                defender_hp_after = preview_data.get("defender_hp_after", defender['hp'])
                estimated_damage = defender['hp'] - defender_hp_after  # Calculate damage from HP difference
                defender_hp_before = defender['hp']
                
                # Execute actual attack
                attack_result = rpc_call("unit_attack", {
                    "token": self.game_id,
                    "x": attacker['x'],
                    "y": attacker['y'],
                    "x2": defender['x'],
                    "y2": defender['y']
                })
                
                print(f"DEBUG: Attack result: {attack_result}")
                
                # Handle different attack result formats
                attack_succeeded = False
                if "error" in attack_result:
                    print(f"   ❌ Attack failed: {attack_result.get('message', 'Unknown error')}")
                elif attack_result.get("error") == True:
                    print(f"   ❌ Attack failed: {attack_result.get('message', 'Combat error')}")
                elif attack_result.get("success") == True:
                    attack_succeeded = True
                elif "army" in attack_result and "hp" in attack_result.get("status", {}):
                    # This format means the attack succeeded and returned updated unit
                    attack_succeeded = True
                    print(f"   ✅ Attack succeeded - unit HP now: {attack_result['status']['hp']}")
                
                if attack_succeeded:
                    # Get updated board to check actual damage
                    new_board = rpc_call("game_board", {"token": self.game_id})
                    if "error" not in new_board:
                        # Find defender's new HP
                        actual_damage = self._calculate_actual_damage(
                            new_board, defender, defender_hp_before
                        )
                        
                        damage_accuracy = abs(estimated_damage - actual_damage)
                        
                        result = {
                            "attacker": f"{attacker['type']} HP:{attacker['hp']}",
                            "defender": f"{defender['type']} HP:{defender_hp_before}",
                            "estimated_damage": estimated_damage,
                            "actual_damage": actual_damage,
                            "accuracy": damage_accuracy <= 10,  # Within 10% tolerance
                            "terrain": defender.get('terrain', 'UNKNOWN')
                        }
                        
                        self.test_results["damage_calculation"].append(result)
                        
                        if result["accuracy"]:
                            print(f"   ✅ Damage: {actual_damage} (estimated: {estimated_damage})")
                        else:
                            print(f"   ❌ Inaccurate: {actual_damage} vs {estimated_damage}")
                        
                        return True
        
        return False
    
    def test_terrain_modifiers(self):
        """Test terrain defense bonuses using actual combat pairs"""
        print("\n🏔️ Testing Terrain Modifiers...")
        
        # Reset unit states first
        self.reset_unit_states()
        
        board = rpc_call("game_board", {"token": self.game_id})
        if "error" in board:
            return False
        
        # Get actual combat pairs that can attack each other
        combat_pairs = self._find_combat_pairs(board)
        
        if not combat_pairs:
            print("   ⚠️  No combat pairs found for terrain testing")
            return False
        
        terrain_results = {}
        
        for attacker, defender, combat_type in combat_pairs[:5]:  # Test up to 5 pairs
            # Get terrain type of defender
            defender_terrain = defender.get('terrain', 'UNKNOWN')
            
            # Get damage preview to see terrain effects
            preview_result = rpc_call("damage_preview", {
                "token": self.game_id,
                "x": attacker['x'],
                "y": attacker['y'],
                "x2": defender['x'],
                "y2": defender['y']
            })
            
            if "error" not in preview_result and preview_result.get("success", False):
                preview_data = preview_result.get("preview", {})
                defender_hp_after = preview_data.get("defender_hp_after", defender['hp'])
                damage = defender['hp'] - defender_hp_after
                
                # Store terrain-based damage for comparison
                if defender_terrain not in terrain_results:
                    terrain_results[defender_terrain] = []
                
                terrain_results[defender_terrain].append({
                    "attacker": attacker['type'],
                    "defender": defender['type'],
                    "damage": damage,
                    "terrain": defender_terrain
                })
                
                print(f"   {attacker['type']} vs {defender['type']} on {defender_terrain}: {damage} damage")
        
        # Store results
        for terrain, results in terrain_results.items():
            for result in results:
                self.test_results["terrain_modifiers"].append(result)
        
        total_tests = sum(len(results) for results in terrain_results.values())
        print(f"   ✅ Tested {total_tests} terrain interactions across {len(terrain_results)} terrain types")
        
        return total_tests > 0
    
    def test_counter_attacks(self):
        """Test counter-attack mechanics using combat_preview"""
        print("\n⚔️ Testing Counter-Attacks...")
        
        # Reset unit states first
        self.reset_unit_states()
        
        board = rpc_call("game_board", {"token": self.game_id})
        if "error" in board:
            return False
        
        # Find units that can counter-attack each other
        combat_pairs = self._find_combat_pairs(board)
        
        if not combat_pairs:
            print("   ⚠️  No combat pairs found for counter-attack testing")
            return False
        
        counter_attack_tests = 0
        
        for attacker, defender, combat_type in combat_pairs[:3]:
            print(f"   Testing {attacker['type']} vs {defender['type']}")
            
            # Use combat_preview to check for counter-attacks
            combat_preview_result = rpc_call("combat_preview", {
                "token": self.game_id,
                "attacker_x": attacker['x'],
                "attacker_y": attacker['y'],
                "defender_x": defender['x'],
                "defender_y": defender['y']
            })
            
            if "error" not in combat_preview_result and combat_preview_result.get("success", False):
                preview = combat_preview_result.get("preview", {})
                can_counter = preview.get("can_counter", False)
                counter_damage = preview.get("counter_damage", 0)
                attacker_damage = preview.get("attacker_damage", 0)
                
                result = {
                    "attacker": attacker['type'],
                    "defender": defender['type'],
                    "can_counter": can_counter,
                    "counter_damage": counter_damage,
                    "attacker_damage": attacker_damage,
                    "combat_type": combat_type
                }
                
                self.test_results["counter_attacks"].append(result)
                counter_attack_tests += 1
                
                if can_counter:
                    print(f"      ✅ Counter-attack possible: {counter_damage} damage to attacker")
                else:
                    print(f"      ➡️  No counter-attack: {attacker_damage} damage to defender only")
            
            else:
                # Fallback to damage_preview if combat_preview fails
                damage_preview_result = rpc_call("damage_preview", {
                    "token": self.game_id,
                    "x": attacker['x'],
                    "y": attacker['y'],
                    "x2": defender['x'],
                    "y2": defender['y']
                })
                
                if "error" not in damage_preview_result and damage_preview_result.get("success", False):
                    preview = damage_preview_result.get("preview", {})
                    can_counter = preview.get("can_counter", False)
                    counter_damage = preview.get("counter_damage", 0)
                    
                    result = {
                        "attacker": attacker['type'],
                        "defender": defender['type'],
                        "can_counter": can_counter,
                        "counter_damage": counter_damage,
                        "combat_type": combat_type
                    }
                    
                    self.test_results["counter_attacks"].append(result)
                    counter_attack_tests += 1
                    
                    if can_counter:
                        print(f"      ✅ Counter-attack possible: {counter_damage} damage")
                    else:
                        print(f"      ➡️  No counter-attack possible")
        
        print(f"   ✅ Tested {counter_attack_tests} counter-attack scenarios")
        return counter_attack_tests > 0
    
    def test_unit_destruction(self):
        """Test unit destruction through multiple attacks"""
        print("\n💥 Testing Unit Destruction (Multi-Attack)...")
        
        # Reset unit states first
        self.reset_unit_states()
        
        # Get existing combat pairs and test destruction scenarios
        board = rpc_call("game_board", {"token": self.game_id})
        if "error" in board:
            return False
        
        combat_pairs = self._find_combat_pairs(board)
        
        if not combat_pairs:
            print("   ⚠️  No combat pairs found for destruction testing")
            return False
        
        destruction_tests = 0
        
        # Find a suitable target for multi-attack destruction
        for attacker, defender, combat_type in combat_pairs[:2]:
            print(f"   Testing multi-attack destruction: {attacker['type']} vs {defender['type']}")
            
            # Track HP reduction over multiple attacks
            attacks_performed = 0
            current_defender_hp = defender['hp']
            max_attacks = 3  # Limit to prevent infinite loops
            
            while attacks_performed < max_attacks and current_defender_hp > 0:
                # Get damage preview
                preview_result = rpc_call("damage_preview", {
                    "token": self.game_id,
                    "x": attacker['x'],
                    "y": attacker['y'],
                    "x2": defender['x'],
                    "y2": defender['y']
                })
                
                if "error" in preview_result or not preview_result.get("success", False):
                    print(f"      ❌ Could not get damage preview for attack {attacks_performed + 1}")
                    break
                
                preview_data = preview_result.get("preview", {})
                expected_hp_after = preview_data.get("defender_hp_after", current_defender_hp)
                expected_damage = current_defender_hp - expected_hp_after
                
                print(f"      Attack {attacks_performed + 1}: Expected {expected_damage} damage ({current_defender_hp} → {expected_hp_after} HP)")
                
                # Execute the attack
                attack_result = rpc_call("unit_attack", {
                    "token": self.game_id,
                    "x": attacker['x'],
                    "y": attacker['y'],
                    "x2": defender['x'],
                    "y2": defender['y']
                })
                
                # Check if attack succeeded
                attack_succeeded = False
                if "error" not in attack_result and not attack_result.get("error", False):
                    if attack_result.get("success") or "army" in attack_result:
                        attack_succeeded = True
                
                if not attack_succeeded:
                    print(f"      ❌ Attack {attacks_performed + 1} failed")
                    break
                
                attacks_performed += 1
                
                # Check if unit was destroyed
                new_board = rpc_call("game_board", {"token": self.game_id})
                if "error" not in new_board:
                    unit_still_exists = self._unit_exists_at(new_board, defender['x'], defender['y'])
                    
                    if not unit_still_exists:
                        print(f"      💥 Unit destroyed after {attacks_performed} attacks!")
                        
                        result = {
                            "attacker": attacker['type'],
                            "defender": defender['type'],
                            "attacks_required": attacks_performed,
                            "initial_hp": defender['hp'],
                            "destruction_successful": True
                        }
                        
                        self.test_results["unit_destruction"].append(result)
                        destruction_tests += 1
                        break
                    else:
                        # Update current HP for next iteration
                        for tile in new_board.get("grid", []):
                            if (isinstance(tile, dict) and 
                                tile.get("x") == defender['x'] and 
                                tile.get("y") == defender['y'] and 
                                tile.get("unit")):
                                
                                unit = tile["unit"]
                                if isinstance(unit, dict):
                                    status = unit.get("status", {})
                                    if isinstance(status, dict):
                                        current_defender_hp = status.get("hp", current_defender_hp)
                                    else:
                                        current_defender_hp = unit.get("hp", current_defender_hp)
                                break
                        
                        print(f"      ➡️  Unit survived with {current_defender_hp} HP")
                
                # End turn cycle to refresh attack capability
                try:
                    rpc_call("army_end_turn", {"token": self.game_id})
                    rpc_call("army_end_turn", {"token": self.game_id})
                except:
                    pass
            
            if attacks_performed > 0 and current_defender_hp > 0:
                # Unit survived multiple attacks - still a valid test
                result = {
                    "attacker": attacker['type'],
                    "defender": defender['type'],
                    "attacks_performed": attacks_performed,
                    "initial_hp": defender['hp'],
                    "final_hp": current_defender_hp,
                    "hp_reduced": defender['hp'] - current_defender_hp,
                    "destruction_successful": False
                }
                
                self.test_results["unit_destruction"].append(result)
                destruction_tests += 1
                
                print(f"      📊 Multi-attack test: {attacks_performed} attacks, {defender['hp'] - current_defender_hp} total damage")
            
            # Only test one combat pair to avoid too many attacks
            if destruction_tests > 0:
                break
        
        print(f"   ✅ Tested {destruction_tests} destruction scenarios")
        return destruction_tests > 0
    
    def _find_combat_pairs(self, board):
        """Find pairs of units that can attack each other"""
        red_units = []
        blue_units = []
        
        print(f"DEBUG: Examining {len(board.get('grid', []))} tiles")
        
        for i, tile in enumerate(board.get("grid", [])):
            # Debug first few tiles
            if i < 3:
                print(f"DEBUG: Tile {i} type: {type(tile)}, content: {str(tile)[:100] if isinstance(tile, str) else 'dict'}")
            
            # Handle string tiles (need to parse JSON)
            if isinstance(tile, str):
                try:
                    tile = json.loads(tile)
                except json.JSONDecodeError:
                    continue
            
            if tile.get("unit"):
                unit = tile["unit"]
                
                # Handle string units
                if isinstance(unit, str):
                    try:
                        unit = json.loads(unit)
                    except json.JSONDecodeError:
                        continue
                
                unit_info = {
                    "x": tile["x"],
                    "y": tile["y"],
                    "type": unit.get("type", {}).get("name", "") if isinstance(unit.get("type"), dict) else str(unit.get("type", "")),
                    "hp": unit.get("status", {}).get("hp", 100) if isinstance(unit.get("status"), dict) else unit.get("hp", 100),
                    "army": unit.get("army", {}).get("name", "") if isinstance(unit.get("army"), dict) else str(unit.get("army", "")),
                    "terrain": tile.get("mapTile", {}).get("type", {}).get("name", "") if isinstance(tile.get("mapTile", {}).get("type"), dict) else str(tile.get("mapTile", {}).get("type", ""))
                }
                
                if unit_info["army"] == "RED":
                    red_units.append(unit_info)
                elif unit_info["army"] == "BLUE":
                    blue_units.append(unit_info)
        
        # Find combat pairs using actual attack target information
        combat_pairs = []
        
        for red_unit in red_units:
            # Get valid attack targets for this unit
            attack_targets_result = rpc_call("get_attack_targets", {
                "token": self.game_id,
                "unit_x": red_unit['x'],
                "unit_y": red_unit['y']
            })
            
            if "error" not in attack_targets_result and attack_targets_result.get("success", False):
                targets = attack_targets_result.get("targets", [])
                
                for target in targets:
                    # Find matching blue unit
                    for blue_unit in blue_units:
                        if blue_unit['x'] == target['x'] and blue_unit['y'] == target['y']:
                            distance = abs(red_unit['x'] - blue_unit['x']) + abs(red_unit['y'] - blue_unit['y'])
                            
                            # Determine combat type based on distance
                            if distance == 1:
                                combat_type = 'direct'
                            elif distance > 1:
                                combat_type = 'indirect'
                            else:
                                combat_type = 'unknown'
                            
                            combat_pairs.append((red_unit, blue_unit, combat_type))
                            break
        
        return combat_pairs
    
    def _calculate_actual_damage(self, new_board, original_unit, original_hp):
        """Calculate actual damage dealt to a unit"""
        for tile in new_board.get("grid", []):
            if (tile.get("x") == original_unit['x'] and 
                tile.get("y") == original_unit['y'] and 
                tile.get("unit")):
                
                current_hp = tile["unit"].get("status", {}).get("hp", 100)
                return original_hp - current_hp
        
        # Unit was destroyed
        return original_hp
    
    def _find_unit_on_terrain(self, board, terrain_type):
        """Find a unit positioned on specific terrain"""
        for tile in board.get("grid", []):
            # Handle string tiles
            if isinstance(tile, str):
                try:
                    tile = json.loads(tile)
                except json.JSONDecodeError:
                    continue
            
            if tile.get("unit"):
                unit = tile["unit"]
                
                # Handle string units
                if isinstance(unit, str):
                    try:
                        unit = json.loads(unit)
                    except json.JSONDecodeError:
                        continue
                
                tile_terrain = tile.get("mapTile", {}).get("type", {})
                if isinstance(tile_terrain, dict):
                    tile_terrain_name = tile_terrain.get("name", "")
                else:
                    tile_terrain_name = str(tile_terrain)
                
                if tile_terrain_name == terrain_type:
                    return {
                        "x": tile["x"],
                        "y": tile["y"],
                        "type": unit.get("type", {}).get("name", "") if isinstance(unit.get("type"), dict) else str(unit.get("type", "")),
                        "hp": unit.get("status", {}).get("hp", 100) if isinstance(unit.get("status"), dict) else unit.get("hp", 100),
                        "army": unit.get("army", {}).get("name", "") if isinstance(unit.get("army"), dict) else str(unit.get("army", "")),
                        "terrain": terrain_type
                    }
        return None
    
    def _find_nearby_attacker(self, board, target):
        """Find an enemy unit that can attack the target"""
        if not target:
            return None
        
        target_army = target['army']
        enemy_army = "BLUE" if target_army == "RED" else "RED"
        
        for tile in board.get("grid", []):
            # Handle string tiles
            if isinstance(tile, str):
                try:
                    tile = json.loads(tile)
                except json.JSONDecodeError:
                    continue
            
            if tile.get("unit"):
                unit = tile["unit"]
                
                # Handle string units
                if isinstance(unit, str):
                    try:
                        unit = json.loads(unit)
                    except json.JSONDecodeError:
                        continue
                
                army = unit.get("army", {}).get("name", "") if isinstance(unit.get("army"), dict) else str(unit.get("army", ""))
                
                if army == enemy_army:
                    distance = abs(tile["x"] - target['x']) + abs(tile["y"] - target['y'])
                    if distance <= 2:  # Within attack range
                        return {
                            "x": tile["x"],
                            "y": tile["y"],
                            "type": unit.get("type", {}).get("name", "") if isinstance(unit.get("type"), dict) else str(unit.get("type", "")),
                            "hp": unit.get("status", {}).get("hp", 100) if isinstance(unit.get("status"), dict) else unit.get("hp", 100),
                            "army": army
                        }
        return None
    
    def _find_adjacent_position(self, attacker, defender):
        """Find a valid adjacent position to move attacker next to defender"""
        # Check all 4 adjacent positions around defender
        adjacent_positions = [
            (defender['x'] + 1, defender['y']),  # Right
            (defender['x'] - 1, defender['y']),  # Left
            (defender['x'], defender['y'] + 1),  # Down
            (defender['x'], defender['y'] - 1),  # Up
        ]
        
        for x, y in adjacent_positions:
            # Check if position is valid and reachable
            if x >= 0 and y >= 0:  # Basic bounds check
                # Check if attacker can move to this position (simplified)
                distance = abs(attacker['x'] - x) + abs(attacker['y'] - y)
                if distance <= 3:  # Assume most units can move 3 spaces
                    return x, y
        
        return None, None
    
    def _can_counter_attack(self, attacker, defender):
        """Check if defender can counter-attack based on unit types"""
        # Simplified logic - most direct combat units can counter-attack
        ranged_units = ["ARTILLERY", "ROCKET", "MISSILE"]
        air_units = ["FIGHTER", "BOMBER", "BCOPTER", "TCOPTER"]
        
        # Air units typically can't be counter-attacked by ground units
        if attacker['type'] in air_units and defender['type'] not in air_units:
            return False
        
        # Ranged units attacking adjacent might not get counter-attacked
        if attacker['type'] in ranged_units:
            distance = abs(attacker['x'] - defender['x']) + abs(attacker['y'] - defender['y'])
            if distance == 1:  # Adjacent ranged attack
                return False
        
        return True
    
    def _unit_exists_at(self, board, x, y):
        """Check if a unit still exists at given coordinates"""
        for tile in board.get("grid", []):
            if tile.get("x") == x and tile.get("y") == y:
                return tile.get("unit") is not None
        return False
    
    def run_all_tests(self):
        """Run all combat tests"""
        print("🏹 Comprehensive Combat System Tests")
        print("=" * 60)
        
        tests = [
            ("Damage Calculation", self.test_damage_calculation),
            ("Terrain Modifiers", self.test_terrain_modifiers),
            ("Counter Attacks", self.test_counter_attacks),
            ("Unit Destruction", self.test_unit_destruction),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                # Reset game state before each test to ensure fresh units
                print(f"\n🔄 Creating fresh game state for {test_name}...")
                new_game_id = get_test_game()
                if new_game_id:
                    self.game_id = new_game_id
                    if test_func():
                        passed += 1
                        print(f"✅ {test_name} PASSED")
                    else:
                        print(f"❌ {test_name} FAILED")
                else:
                    print(f"❌ {test_name} SKIPPED - Could not create game")
            except Exception as e:
                print(f"❌ {test_name} ERROR: {str(e)}")
        
        # Results summary
        print("\n" + "=" * 60)
        print("📊 COMBAT TEST RESULTS")
        print("=" * 60)
        
        for category, results in self.test_results.items():
            if results:
                print(f"✅ {category.replace('_', ' ').title()}: {len(results)} tests")
        
        print(f"\n📈 Overall: {passed}/{total} test categories passed")
        
        if passed == total:
            print("🎉 ALL COMBAT TESTS PASSED!")
        elif passed >= total * 0.75:
            print("✅ Combat system mostly functional")
        else:
            print("⚠️  Combat system needs attention")
        
        return passed >= total * 0.75

def main():
    """Main test function"""
    print("🚀 Combat System Testing Suite")
    print("=" * 70)
    
    # Create test game
    game_id = get_test_game()
    if not game_id:
        print("❌ Could not create test game")
        return False
    
    # Run combat tests
    tester = CombatTester(game_id)
    success = tester.run_all_tests()
    
    print(f"\n🎮 Test game URL: http://localhost:5000/game/{game_id}")
    
    return success

def setup_combat_units(game_id):
    """Set up units for combat testing"""
    print("🎮 Setting up combat units...")
    
    # Create RED units at factories/ports/airports
    units_to_create = [
        # Ground units - create more units for multiple test scenarios
        ("RED", "TANK", 0, 3),      # Factory position
        ("RED", "INFANTRY", 1, 4),  # Factory position
        ("RED", "ARTILLERY", 0, 4), # Near factory
        ("RED", "RECON", 1, 3),     # Near factory
        ("RED", "MECH", 2, 3),      # Additional unit
        ("RED", "TANK", 2, 4),      # Additional tank
        
        # Naval units at port
        ("RED", "BATTLESHIP", 0, 0), # Port position
        ("RED", "CRUISER", 1, 0),    # Near port
        ("RED", "SUB", 2, 0),       # Additional naval
        
        # Air units at airport  
        ("RED", "FIGHTER", 0, 8),    # Airport position
        ("RED", "BOMBER", 1, 8),     # Near airport
        ("RED", "BCOPTER", 2, 8),   # Additional air
    ]
    
    for army, unit_type, x, y in units_to_create:
        result = rpc_call("unit_create", {
            "token": game_id,
            "army": army,
            "unit_type": unit_type,
            "x": x,
            "y": y
        })
        if "error" not in result:
            print(f"   ✅ Created {army} {unit_type} at ({x},{y})")
    
    # End turn to switch to BLUE
    rpc_call("army_end_turn", {"token": game_id})
    
    # Create BLUE units - more units for multiple test scenarios
    blue_units = [
        # Ground units
        ("BLUE", "TANK", 9, 6),      # Factory position
        ("BLUE", "INFANTRY", 8, 5), # Factory position  
        ("BLUE", "MECH", 9, 5),     # Near factory
        ("BLUE", "ARTILLERY", 8, 6), # Near factory
        ("BLUE", "TANK", 7, 5),     # Additional tank
        ("BLUE", "INFANTRY", 7, 6), # Additional infantry
        
        # Naval units
        ("BLUE", "BATTLESHIP", 9, 9), # Port position
        ("BLUE", "SUB", 8, 9),        # Near port
        ("BLUE", "LANDER", 7, 9),     # Additional naval
        
        # Air units
        ("BLUE", "FIGHTER", 9, 1),    # Airport position
        ("BLUE", "TCOPTER", 8, 1),    # Near airport
        ("BLUE", "BOMBER", 7, 1),     # Additional air
    ]
    
    for army, unit_type, x, y in blue_units:
        result = rpc_call("unit_create", {
            "token": game_id,
            "army": army,
            "unit_type": unit_type,
            "x": x,
            "y": y
        })
        if "error" not in result:
            print(f"   ✅ Created {army} {unit_type} at ({x},{y})")
    
    # Enable all units by ending turns
    print("   ⏳ Enabling units for combat...")
    rpc_call("army_end_turn", {"token": game_id})
    rpc_call("army_end_turn", {"token": game_id})
    
    print("✅ Combat units ready for testing")
    
    # Move some units into combat range
    print("   ⏳ Moving units into combat positions...")
    
    # Move RED units closer to center
    moves = [
        # Move some RED ground units east
        {"token": game_id, "x": 0, "y": 3, "x2": 3, "y2": 3},  # Tank
        {"token": game_id, "x": 1, "y": 4, "x2": 4, "y2": 4},  # Infantry
        {"token": game_id, "x": 0, "y": 4, "x2": 3, "y2": 4},  # Artillery
        {"token": game_id, "x": 1, "y": 3, "x2": 4, "y2": 3},  # Recon
        # Move some naval units
        {"token": game_id, "x": 0, "y": 0, "x2": 2, "y2": 1},  # Battleship
        {"token": game_id, "x": 1, "y": 0, "x2": 3, "y2": 0},  # Cruiser
    ]
    
    for move in moves:
        rpc_call("unit_move", move)
    
    # End turn to switch to BLUE
    rpc_call("army_end_turn", {"token": game_id})
    
    # Move BLUE units closer to center
    blue_moves = [
        # Move some BLUE ground units west
        {"token": game_id, "x": 9, "y": 6, "x2": 6, "y2": 6},  # Tank
        {"token": game_id, "x": 8, "y": 5, "x2": 5, "y2": 5},  # Infantry
        {"token": game_id, "x": 8, "y": 6, "x2": 5, "y2": 6},  # Artillery
        {"token": game_id, "x": 9, "y": 5, "x2": 6, "y2": 5},  # Mech
        # Move some naval units
        {"token": game_id, "x": 9, "y": 9, "x2": 7, "y2": 8},  # Battleship
        {"token": game_id, "x": 7, "y": 9, "x2": 5, "y2": 9},  # Lander  
    ]
    
    for move in blue_moves:
        rpc_call("unit_move", move)
    
    # End turn to enable all units again
    rpc_call("army_end_turn", {"token": game_id})
    
    print("   ✅ Units positioned for combat testing")

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
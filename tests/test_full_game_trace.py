#!/usr/bin/env python3
"""
Full Game Trace Test - Tests a complete game from start to finish
Simulates realistic gameplay and verifies all systems work together
"""

import requests
import json
import time
import sys
import os
from typing import Dict, Any, List, Tuple, Optional

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class FullGameTracer:
    """Traces through a complete game, testing all major mechanics"""
    
    def __init__(self, base_url="http://localhost:5000/api", verbose=True):
        self.base_url = base_url
        self.token = f"trace-{int(time.time())}"
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.trace_log = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.trace_log.append(log_entry)
        if self.verbose:
            # Color coding for different levels
            if level == "ERROR":
                print(f"\033[91m{log_entry}\033[0m")
            elif level == "SUCCESS":
                print(f"\033[92m{log_entry}\033[0m")
            elif level == "ACTION":
                print(f"\033[96m{log_entry}\033[0m")
            else:
                print(log_entry)
    
    def rpc(self, method: str, params: Dict = None) -> Dict:
        """Make RPC call with error handling"""
        if params is None:
            params = {}
        if 'token' not in params:
            params['token'] = self.token
            
        try:
            response = requests.post(self.base_url, json={
                'jsonrpc': '2.0',
                'method': method,
                'params': params,
                'id': 1
            })
            result = response.json()
            
            if 'error' in result:
                self.log(f"RPC Error in {method}: {result['error']}", "ERROR")
                return {'error': result['error']}
                
            return result.get('result', {})
        except Exception as e:
            self.log(f"Network error in {method}: {e}", "ERROR")
            return {'error': str(e)}
    
    def test(self, name: str, condition: bool, details: str = "") -> bool:
        """Record test result"""
        if condition:
            self.passed += 1
            self.log(f"✅ {name}", "SUCCESS")
        else:
            self.failed += 1
            self.log(f"❌ {name}: {details}", "ERROR")
        return condition
    
    def get_board_state(self) -> Dict:
        """Get current board state"""
        return self.rpc('game_board')
    
    def find_unit(self, player_id: int, unit_type: str = None) -> Optional[Tuple[int, int]]:
        """Find a unit on the board"""
        board = self.get_board_state()
        for tile in board.get('grid', []):
            if tile.get('unit'):
                unit = tile['unit']
                if unit['player_id'] == player_id:
                    if unit_type is None or unit['type'] == unit_type:
                        return (tile['x'], tile['y'])
        return None
    
    def find_property(self, property_type: str, owned_by: Optional[int] = None) -> Optional[Tuple[int, int]]:
        """Find a property on the board"""
        board = self.get_board_state()
        for tile in board.get('grid', []):
            if tile.get('type') == property_type:
                if owned_by is None or tile.get('player_id') == owned_by:
                    return (tile['x'], tile['y'])
        return None
    
    def trace_game_creation(self):
        """Test 1: Game Creation and Initial State"""
        self.log("=== PHASE 1: Game Creation ===", "ACTION")
        
        # Create game with test settings
        result = self.rpc('game_create_test')
        self.test("Game created successfully", result.get('success', False))
        
        # Check initial board state
        board = self.get_board_state()
        self.test("Board has correct dimensions", 
                 board.get('width', 0) > 0 and board.get('height', 0) > 0,
                 f"Width: {board.get('width')}, Height: {board.get('height')}")
        
        self.test("Game is active", board.get('game_active', False))
        self.test("Starting player is 0", board.get('current_player') == 0)
        self.test("Day counter starts at 1", board.get('day') == 1)
        
        # Check player funds
        funds = board.get('player_funds', [])
        self.test("Players have starting funds", 
                 len(funds) >= 2 and all(f > 0 for f in funds),
                 f"Funds: {funds}")
        
        return board
    
    def trace_unit_production(self):
        """Test 2: Unit Production"""
        self.log("=== PHASE 2: Unit Production ===", "ACTION")
        
        # Find a factory
        factory_pos = self.find_property('FACTORY', owned_by=0)
        if not factory_pos:
            self.log("No factory found for player 0, creating units directly", "INFO")
            # Create units directly for testing
            result = self.rpc('unit_create', {
                'player_id': 0,
                'unit_type': 'TANK',
                'x': 2, 'y': 2
            })
            self.test("Tank created", 'error' not in result)
            
            result = self.rpc('unit_create', {
                'player_id': 0,
                'unit_type': 'INFANTRY',
                'x': 3, 'y': 2
            })
            self.test("Infantry created", 'error' not in result)
        else:
            # Use factory to produce
            self.log(f"Found factory at {factory_pos}", "INFO")
            result = self.rpc('get_production_options', {
                'x': factory_pos[0],
                'y': factory_pos[1]
            })
            
            available_units = result.get('units', [])
            self.test("Production menu has units", len(available_units) > 0,
                     f"Available: {[u['type'] for u in available_units]}")
            
            if available_units:
                # Produce a tank
                unit_to_build = next((u for u in available_units if u['type'] == 'TANK'), available_units[0])
                result = self.rpc('unit_create', {
                    'player_id': 0,
                    'unit_type': unit_to_build['type'],
                    'x': factory_pos[0],
                    'y': factory_pos[1]
                })
                self.test(f"{unit_to_build['type']} produced", 'error' not in result)
    
    def trace_unit_movement(self):
        """Test 3: Unit Movement and Selection"""
        self.log("=== PHASE 3: Unit Movement ===", "ACTION")
        
        # End turn to enable movement
        self.rpc('army_end_turn')
        self.rpc('army_end_turn')  # Back to player 0
        
        # Find a unit to move
        unit_pos = self.find_unit(0)
        if not unit_pos:
            self.log("No unit found to test movement", "ERROR")
            return
        
        self.log(f"Testing movement with unit at {unit_pos}", "INFO")
        
        # Select unit
        result = self.rpc('unit_select', {'x': unit_pos[0], 'y': unit_pos[1]})
        self.test("Unit selected", 'error' not in result)
        
        # Get movement range
        result = self.rpc('movement_range', {
            'unit_x': unit_pos[0],
            'unit_y': unit_pos[1]
        })
        moves = result.get('moves', [])
        self.test("Movement range calculated", len(moves) > 0,
                 f"Available moves: {len(moves)}")
        
        if moves:
            # Move to first available position
            move_to = moves[0]
            result = self.rpc('movement_execute', {
                'from_x': unit_pos[0],
                'from_y': unit_pos[1],
                'to_x': move_to['x'],
                'to_y': move_to['y']
            })
            self.test("Unit moved successfully", result.get('success', False),
                     f"From {unit_pos} to ({move_to['x']}, {move_to['y']})")
            
            # Wait with unit
            result = self.rpc('unit_wait', {
                'x': move_to['x'],
                'y': move_to['y']
            })
            self.test("Unit waited after move", 'error' not in result)
    
    def trace_combat(self):
        """Test 4: Combat Mechanics"""
        self.log("=== PHASE 4: Combat ===", "ACTION")
        
        # Create opposing units for combat
        self.rpc('unit_create', {
            'player_id': 0,
            'unit_type': 'TANK',
            'x': 5, 'y': 5
        })
        
        self.rpc('army_end_turn')
        
        self.rpc('unit_create', {
            'player_id': 1,
            'unit_type': 'INFANTRY',
            'x': 6, 'y': 5
        })
        
        self.rpc('army_end_turn')
        
        # Select attacker
        result = self.rpc('unit_select', {'x': 5, 'y': 5})
        self.test("Attacker selected", 'error' not in result)
        
        # Check combat targets
        result = self.rpc('combat_targets', {
            'unit_x': 5,
            'unit_y': 5
        })
        targets = result.get('targets', [])
        self.test("Combat targets found", len(targets) > 0,
                 f"Targets: {targets}")
        
        # Get combat preview
        result = self.rpc('combat_preview', {
            'attacker_x': 5,
            'attacker_y': 5,
            'target_x': 6,
            'target_y': 5
        })
        self.test("Combat preview calculated", 
                 'attacker_damage' in result and 'defender_damage' in result,
                 f"Damage: {result.get('attacker_damage')} vs {result.get('defender_damage')}")
        
        # Execute attack
        result = self.rpc('unit_attack', {
            'attacker_x': 5,
            'attacker_y': 5,
            'target_x': 6,
            'target_y': 5
        })
        self.test("Attack executed", result.get('success', False))
        
        # Check damage was applied
        board = self.get_board_state()
        for tile in board.get('grid', []):
            if tile['x'] == 6 and tile['y'] == 5 and tile.get('unit'):
                hp = tile['unit'].get('hp', 100)
                self.test("Defender took damage", hp < 100,
                         f"Defender HP: {hp}")
                break
    
    def trace_capture(self):
        """Test 5: Property Capture"""
        self.log("=== PHASE 5: Property Capture ===", "ACTION")
        
        # Create infantry for capturing
        self.rpc('unit_create', {
            'player_id': 0,
            'unit_type': 'INFANTRY',
            'x': 7, 'y': 7
        })
        
        # Find a neutral property
        neutral_prop = self.find_property('CITY', owned_by=None)
        if not neutral_prop:
            self.log("No neutral property found for capture test", "INFO")
            return
        
        self.log(f"Found neutral property at {neutral_prop}", "INFO")
        
        # Move infantry to property (may take multiple turns)
        self.rpc('army_end_turn')
        self.rpc('army_end_turn')
        
        # Try to move infantry closer
        result = self.rpc('movement_execute', {
            'from_x': 7,
            'from_y': 7,
            'to_x': neutral_prop[0],
            'to_y': neutral_prop[1]
        })
        
        if result.get('success'):
            # Start capture
            result = self.rpc('unit_capture', {
                'x': neutral_prop[0],
                'y': neutral_prop[1]
            })
            self.test("Capture started", 'error' not in result)
            
            # Continue capture next turn
            self.rpc('army_end_turn')
            self.rpc('army_end_turn')
            
            result = self.rpc('unit_capture', {
                'x': neutral_prop[0],
                'y': neutral_prop[1]
            })
            self.test("Capture continued", 'error' not in result)
            
            # Check if captured
            board = self.get_board_state()
            for tile in board.get('grid', []):
                if tile['x'] == neutral_prop[0] and tile['y'] == neutral_prop[1]:
                    self.test("Property captured", tile.get('player_id') == 0,
                             f"Owner: {tile.get('player_id')}")
                    break
    
    def trace_transport(self):
        """Test 6: Transport Mechanics"""
        self.log("=== PHASE 6: Transport Mechanics ===", "ACTION")
        
        # Create APC and infantry
        self.rpc('unit_create', {
            'player_id': 0,
            'unit_type': 'APC',
            'x': 8, 'y': 8
        })
        
        self.rpc('unit_create', {
            'player_id': 0,
            'unit_type': 'INFANTRY',
            'x': 8, 'y': 9
        })
        
        self.rpc('army_end_turn')
        self.rpc('army_end_turn')
        
        # Load infantry into APC
        result = self.rpc('transport_load', {
            'transport_x': 8,
            'transport_y': 8,
            'cargo_x': 8,
            'cargo_y': 9
        })
        self.test("Infantry loaded into APC", result.get('success', False))
        
        # Move APC
        result = self.rpc('movement_execute', {
            'from_x': 8,
            'from_y': 8,
            'to_x': 9,
            'to_y': 8
        })
        self.test("APC moved with cargo", result.get('success', False))
        
        # Unload infantry
        result = self.rpc('transport_unload', {
            'transport_x': 9,
            'transport_y': 8,
            'cargo_index': 0,
            'unload_x': 9,
            'unload_y': 9
        })
        self.test("Infantry unloaded", result.get('success', False))
    
    def trace_victory_conditions(self):
        """Test 7: Victory Conditions"""
        self.log("=== PHASE 7: Victory Conditions ===", "ACTION")
        
        # Check if game can detect victory
        # This would normally involve capturing HQ or eliminating all units
        board = self.get_board_state()
        
        # Find HQ
        hq_pos = self.find_property('HQ', owned_by=1)
        if hq_pos:
            self.log(f"Enemy HQ found at {hq_pos}", "INFO")
            # In a real game, we'd move infantry there and capture it
            
        # Check game is still active
        self.test("Game still active", board.get('game_active', False))
        
        # Victory is checked automatically on the server
        # Just verify the game_active flag
        if not board.get('game_active'):
            self.log("Game has ended", "INFO")
            winner = board.get('winner')
            if winner is not None:
                self.log(f"Winner detected: Player {winner}", "SUCCESS")
    
    def trace_turn_management(self):
        """Test 8: Turn Management"""
        self.log("=== PHASE 8: Turn Management ===", "ACTION")
        
        board = self.get_board_state()
        initial_player = board.get('current_player')
        initial_day = board.get('day')
        
        # End turn
        result = self.rpc('army_end_turn')
        self.test("Turn ended", 'error' not in result)
        
        # Check turn changed
        board = self.get_board_state()
        new_player = board.get('current_player')
        self.test("Player changed after turn", new_player != initial_player,
                 f"Was {initial_player}, now {new_player}")
        
        # End turn again
        self.rpc('army_end_turn')
        board = self.get_board_state()
        
        # Check day increment
        self.test("Day incremented after full round", board.get('day') > initial_day,
                 f"Was day {initial_day}, now day {board.get('day')}")
    
    def run_full_trace(self):
        """Run complete game trace"""
        print("=" * 60)
        print("🎮 FULL GAME TRACE TEST")
        print("=" * 60)
        print(f"Token: {self.token}")
        print(f"Game URL: http://localhost:5000/game/{self.token}")
        print("=" * 60)
        
        try:
            # Run all test phases
            self.trace_game_creation()
            self.trace_unit_production()
            self.trace_unit_movement()
            self.trace_combat()
            self.trace_capture()
            self.trace_transport()
            self.trace_turn_management()
            self.trace_victory_conditions()
            
        except Exception as e:
            self.log(f"Critical error during trace: {e}", "ERROR")
            import traceback
            traceback.print_exc()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TRACE SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        success_rate = (self.passed / (self.passed + self.failed) * 100) if (self.passed + self.failed) > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.failed > 0:
            print("\n⚠️ Failed Tests:")
            for entry in self.trace_log:
                if "ERROR" in entry and "❌" in entry:
                    print(f"  {entry}")
        
        print("\n💡 To view the game in browser, visit:")
        print(f"   http://localhost:5000/game/{self.token}")
        
        # Save trace log
        log_file = f"/tmp/game_trace_{self.token}.log"
        with open(log_file, 'w') as f:
            f.write('\n'.join(self.trace_log))
        print(f"\n📝 Full trace log saved to: {log_file}")
        
        return self.failed == 0


def main():
    """Run full game trace test"""
    import argparse
    parser = argparse.ArgumentParser(description='Trace through a complete game')
    parser.add_argument('--quiet', '-q', action='store_true', help='Reduce output verbosity')
    parser.add_argument('--url', default='http://localhost:5000/api', help='API URL')
    args = parser.parse_args()
    
    tracer = FullGameTracer(base_url=args.url, verbose=not args.quiet)
    success = tracer.run_full_trace()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
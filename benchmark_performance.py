#!/usr/bin/env python3
"""
Performance Benchmark Suite for Advance Wars RPC
Measures key performance metrics to establish baseline
"""

import time
import requests
import json
import statistics
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

class PerformanceBenchmark:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.results = {}
        
    def measure_time(self, func):
        """Decorator to measure function execution time"""
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            return result, (end - start) * 1000  # Convert to ms
        return wrapper
    
    def rpc_call(self, method, params=None):
        """Make an RPC call and return response + timing"""
        if params is None:
            params = {}
            
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        
        start = time.perf_counter()
        response = requests.post(f"{self.base_url}/api", json=payload)
        end = time.perf_counter()
        
        return response.json(), (end - start) * 1000
    
    def benchmark_game_creation(self, iterations=10):
        """Benchmark game creation performance"""
        print(f"\n📊 Benchmarking Game Creation ({iterations} iterations)...")
        times = []
        
        for i in range(iterations):
            _, duration = self.rpc_call("game_create_v2", {
                "player_configs": [
                    {"army": "RED", "co": "andy"},
                    {"army": "BLUE", "co": "max"}
                ]
            })
            times.append(duration)
            print(f"  Iteration {i+1}: {duration:.2f}ms")
        
        self.results['game_creation'] = {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'min': min(times),
            'max': max(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0
        }
    
    def benchmark_board_retrieval(self, token, iterations=20):
        """Benchmark board state retrieval"""
        print(f"\n📊 Benchmarking Board Retrieval ({iterations} iterations)...")
        times = []
        
        for i in range(iterations):
            _, duration = self.rpc_call("get_board", {"token": token})
            times.append(duration)
            if i % 5 == 0:
                print(f"  Progress: {i+1}/{iterations}")
        
        self.results['board_retrieval'] = {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'min': min(times),
            'max': max(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0
        }
    
    def benchmark_unit_operations(self, token, iterations=10):
        """Benchmark unit creation and movement"""
        print(f"\n📊 Benchmarking Unit Operations ({iterations} iterations)...")
        
        # Unit creation times
        creation_times = []
        for i in range(iterations):
            _, duration = self.rpc_call("unit_create", {
                "token": token,
                "unit_type": "INFANTRY",
                "x": 0,
                "y": i % 10  # Vary position
            })
            creation_times.append(duration)
        
        # Unit movement times
        movement_times = []
        for i in range(min(5, iterations)):
            # Create a unit first
            self.rpc_call("unit_create", {
                "token": token,
                "unit_type": "TANK",
                "x": 1,
                "y": i
            })
            
            # End turn to allow movement
            self.rpc_call("unit_end_turn", {"token": token})
            self.rpc_call("unit_end_turn", {"token": token})
            
            # Measure movement
            _, duration = self.rpc_call("unit_move", {
                "token": token,
                "from_x": 1,
                "from_y": i,
                "to_x": 2,
                "to_y": i
            })
            movement_times.append(duration)
        
        self.results['unit_creation'] = {
            'mean': statistics.mean(creation_times),
            'median': statistics.median(creation_times),
            'min': min(creation_times),
            'max': max(creation_times),
            'stdev': statistics.stdev(creation_times) if len(creation_times) > 1 else 0
        }
        
        if movement_times:
            self.results['unit_movement'] = {
                'mean': statistics.mean(movement_times),
                'median': statistics.median(movement_times),
                'min': min(movement_times),
                'max': max(movement_times),
                'stdev': statistics.stdev(movement_times) if len(movement_times) > 1 else 0
            }
    
    def benchmark_combat_calculations(self, token, iterations=10):
        """Benchmark combat preview calculations"""
        print(f"\n📊 Benchmarking Combat Calculations ({iterations} iterations)...")
        
        # Setup units for combat
        self.rpc_call("unit_create", {"token": token, "unit_type": "TANK", "x": 3, "y": 3})
        self.rpc_call("unit_end_turn", {"token": token})
        self.rpc_call("unit_create", {"token": token, "unit_type": "TANK", "x": 3, "y": 4})
        
        times = []
        for i in range(iterations):
            _, duration = self.rpc_call("combat_preview", {
                "token": token,
                "attacker_x": 3,
                "attacker_y": 3,
                "defender_x": 3,
                "defender_y": 4
            })
            times.append(duration)
        
        self.results['combat_calculations'] = {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'min': min(times),
            'max': max(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0
        }
    
    def benchmark_large_game(self):
        """Benchmark performance with many units"""
        print(f"\n📊 Benchmarking Large Game Performance...")
        
        # Create game with many units
        result, _ = self.rpc_call("game_create_test", {})
        token = result['result']['token']
        
        # Create 20 units
        print("  Creating 20 units...")
        for i in range(20):
            self.rpc_call("unit_create", {
                "token": token,
                "unit_type": "INFANTRY" if i % 2 == 0 else "TANK",
                "x": i % 12,
                "y": i % 10
            })
        
        # Measure board retrieval with many units
        times = []
        for i in range(10):
            _, duration = self.rpc_call("get_board", {"token": token})
            times.append(duration)
        
        self.results['large_game_board'] = {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'min': min(times),
            'max': max(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0
        }
    
    def print_results(self):
        """Print benchmark results in a formatted table"""
        print("\n" + "="*70)
        print("📊 PERFORMANCE BENCHMARK RESULTS")
        print("="*70)
        print(f"{'Operation':<25} {'Mean':>10} {'Median':>10} {'Min':>10} {'Max':>10} {'StdDev':>10}")
        print("-"*70)
        
        for operation, stats in self.results.items():
            print(f"{operation:<25} "
                  f"{stats['mean']:>9.2f}ms "
                  f"{stats['median']:>9.2f}ms "
                  f"{stats['min']:>9.2f}ms "
                  f"{stats['max']:>9.2f}ms "
                  f"{stats['stdev']:>9.2f}ms")
        
        print("\n📈 Performance Grades:")
        for operation, stats in self.results.items():
            mean = stats['mean']
            if mean < 50:
                grade = "🟢 Excellent"
            elif mean < 100:
                grade = "🟡 Good"
            elif mean < 200:
                grade = "🟠 Fair"
            else:
                grade = "🔴 Needs Optimization"
            
            print(f"  {operation}: {grade} ({mean:.1f}ms avg)")
    
    def save_results(self):
        """Save results to JSON file with timestamp"""
        import datetime
        
        filename = f"benchmark_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'results': self.results,
            'summary': {
                'total_operations': len(self.results),
                'average_response_time': statistics.mean([r['mean'] for r in self.results.values()]),
                'operations_under_100ms': sum(1 for r in self.results.values() if r['mean'] < 100)
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")
    
    def run_all_benchmarks(self):
        """Run all benchmark tests"""
        print("🚀 Starting Performance Benchmark Suite")
        print("⏱️  This will take approximately 2-3 minutes...")
        
        # Check server is running
        try:
            requests.get(self.base_url)
        except:
            print("❌ Error: Server not running at http://localhost:5000")
            return False
        
        # Create a test game
        result, _ = self.rpc_call("game_create_v2", {
            "player_configs": [
                {"army": "RED", "co": "andy"},
                {"army": "BLUE", "co": "max"}
            ]
        })
        
        if 'error' in result:
            print(f"❌ Error creating game: {result['error']}")
            return False
            
        token = result['result']['token']
        
        # Run benchmarks
        self.benchmark_game_creation()
        self.benchmark_board_retrieval(token)
        self.benchmark_unit_operations(token)
        self.benchmark_combat_calculations(token)
        self.benchmark_large_game()
        
        # Print and save results
        self.print_results()
        self.save_results()
        
        return True

if __name__ == "__main__":
    benchmark = PerformanceBenchmark()
    success = benchmark.run_all_benchmarks()
    sys.exit(0 if success else 1)
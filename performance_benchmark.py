#!/usr/bin/env python3
"""
Performance Benchmark for Advance Wars RPC Game Engine

Measures performance of key game operations:
- Game creation and initialization
- Unit creation and movement
- Combat calculations
- Pathfinding performance
- Board rendering data generation
- Transport operations
- Economic calculations
"""

import time
import requests
import json
import statistics
from typing import List, Dict, Tuple
import random

class PerformanceBenchmark:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.token = f"perf-bench-{int(time.time())}"
        self.results = {}
        
    def rpc(self, method: str, params: dict = None):
        """Make RPC call and measure time"""
        headers = {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1
        }
        
        start_time = time.perf_counter()
        response = requests.post(f"{self.base_url}/api", headers=headers, data=json.dumps(payload))
        end_time = time.perf_counter()
        
        elapsed_ms = (end_time - start_time) * 1000
        
        if response.status_code != 200:
            raise Exception(f"RPC call failed: {response.status_code}")
            
        result = response.json()
        if "error" in result:
            raise Exception(f"RPC error: {result['error']}")
            
        return result.get("result"), elapsed_ms
    
    def measure_operation(self, name: str, operation, iterations: int = 10) -> Dict:
        """Measure an operation multiple times and return statistics"""
        times = []
        
        for _ in range(iterations):
            elapsed = operation()
            times.append(elapsed)
            
        return {
            "name": name,
            "iterations": iterations,
            "mean_ms": statistics.mean(times),
            "median_ms": statistics.median(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0
        }
    
    def benchmark_game_creation(self) -> Dict:
        """Benchmark game creation"""
        def create_game():
            _, elapsed = self.rpc("game_create_test", {"token": f"{self.token}-{time.time()}"})
            return elapsed
            
        return self.measure_operation("Game Creation", create_game)
    
    def benchmark_unit_creation(self) -> Dict:
        """Benchmark unit creation"""
        # Create a game first
        self.rpc("game_create_test", {"token": self.token})
        
        def create_unit():
            x, y = random.randint(0, 11), random.randint(0, 9)
            unit_types = ["INFANTRY", "TANK", "RECON", "ARTILLERY", "ANTIAIR"]
            unit_type = random.choice(unit_types)
            _, elapsed = self.rpc("unit_create", {
                "token": self.token,
                "army": "RED",
                "unit_type": unit_type,
                "x": x,
                "y": y
            })
            return elapsed
            
        return self.measure_operation("Unit Creation", create_unit, iterations=20)
    
    def benchmark_movement_calculation(self) -> Dict:
        """Benchmark movement calculation"""
        # Create new game for this test
        test_token = f"{self.token}-movement"
        self.rpc("game_create_test", {"token": test_token})
        self.rpc("unit_create", {"token": test_token, "army": "RED", "unit_type": "TANK", "x": 5, "y": 5})
        
        def calculate_moves():
            _, elapsed = self.rpc("unit_valid_moves", {"token": test_token, "x": 5, "y": 5})
            return elapsed
            
        return self.measure_operation("Movement Calculation", calculate_moves)
    
    def benchmark_combat_preview(self) -> Dict:
        """Benchmark combat preview calculations"""
        # Create game and units
        test_token = f"{self.token}-combat"
        self.rpc("game_create_test", {"token": test_token})
        self.rpc("unit_create", {"token": test_token, "army": "RED", "unit_type": "TANK", "x": 5, "y": 5})
        self.rpc("unit_create", {"token": test_token, "army": "BLUE", "unit_type": "INFANTRY", "x": 6, "y": 5})
        
        def preview_combat():
            _, elapsed = self.rpc("combat_preview", {
                "token": test_token,
                "attacker_x": 5,
                "attacker_y": 5,
                "defender_x": 6,
                "defender_y": 5
            })
            return elapsed
            
        return self.measure_operation("Combat Preview", preview_combat)
    
    def benchmark_board_generation(self) -> Dict:
        """Benchmark board data generation"""
        # Create game with many units
        test_token = f"{self.token}-board"
        self.rpc("game_create_test", {"token": test_token})
        
        # Add 20 random units
        for i in range(20):
            x, y = random.randint(0, 11), random.randint(0, 9)
            army = "RED" if i % 2 == 0 else "BLUE"
            unit_type = random.choice(["INFANTRY", "TANK", "RECON", "ARTILLERY", "ANTIAIR"])
            try:
                self.rpc("unit_create", {
                    "token": test_token,
                    "army": army,
                    "unit_type": unit_type,
                    "x": x,
                    "y": y
                })
            except:
                pass  # Ignore if position occupied
        
        def get_board():
            _, elapsed = self.rpc("game_board", {"token": test_token})
            return elapsed
            
        return self.measure_operation("Board Generation", get_board)
    
    def benchmark_pathfinding_complex(self) -> Dict:
        """Benchmark pathfinding with obstacles"""
        # Create game with terrain obstacles
        test_token = f"{self.token}-pathfind"
        self.rpc("game_create_test", {"token": test_token})
        
        # Create units as obstacles
        for x in range(3, 8):
            for y in range(3, 7):
                if (x + y) % 2 == 0:
                    try:
                        self.rpc("unit_create", {
                            "token": test_token,
                            "army": "BLUE",
                            "unit_type": "INFANTRY",
                            "x": x,
                            "y": y
                        })
                    except:
                        pass
        
        # Create unit to test pathfinding
        self.rpc("unit_create", {"token": test_token, "army": "RED", "unit_type": "TANK", "x": 0, "y": 0})
        
        def complex_pathfind():
            _, elapsed = self.rpc("unit_valid_moves", {"token": test_token, "x": 0, "y": 0})
            return elapsed
            
        return self.measure_operation("Complex Pathfinding", complex_pathfind)
    
    def benchmark_transport_operations(self) -> Dict:
        """Benchmark transport loading/unloading"""
        # Create game with transport
        test_token = f"{self.token}-transport"
        self.rpc("game_create_test", {"token": test_token})
        self.rpc("unit_create", {"token": test_token, "army": "RED", "unit_type": "APC", "x": 5, "y": 5})
        self.rpc("unit_create", {"token": test_token, "army": "RED", "unit_type": "INFANTRY", "x": 6, "y": 5})
        
        def transport_ops():
            # Load
            _, elapsed1 = self.rpc("load_unit", {
                "token": test_token,
                "transport_x": 5,
                "transport_y": 5,
                "cargo_x": 6,
                "cargo_y": 5
            })
            
            # Get unload positions
            _, elapsed2 = self.rpc("get_valid_unload_positions", {
                "token": test_token,
                "x": 5,
                "y": 5
            })
            
            return elapsed1 + elapsed2
            
        return self.measure_operation("Transport Operations", transport_ops, iterations=5)
    
    def benchmark_economic_calculations(self) -> Dict:
        """Benchmark economic system calculations"""
        # Create game with properties
        test_token = f"{self.token}-economy"
        self.rpc("game_create_test", {"token": test_token})
        
        def economic_calcs():
            # Get production options
            _, elapsed1 = self.rpc("get_production_options", {"token": test_token, "x": 0, "y": 9})
            
            # Get army economy
            _, elapsed2 = self.rpc("get_army_economy", {"token": test_token})
            
            # Get unit costs
            _, elapsed3 = self.rpc("get_unit_costs", {"token": test_token})
            
            return elapsed1 + elapsed2 + elapsed3
            
        return self.measure_operation("Economic Calculations", economic_calcs)
    
    def benchmark_rendering_data(self) -> Dict:
        """Benchmark rendering data generation for different scenarios"""
        # Create game with complex scenario
        test_token = f"{self.token}-render"
        self.rpc("game_create_test", {"token": test_token})
        
        # Add units spread across the map
        positions = [(0,0), (11,9), (5,5), (3,7), (8,2), (2,8), (10,1), (4,4), (7,6), (1,3)]
        for i, (x, y) in enumerate(positions):
            army = "RED" if i % 2 == 0 else "BLUE"
            unit_type = ["INFANTRY", "TANK", "RECON", "ARTILLERY", "ANTIAIR"][i % 5]
            try:
                self.rpc("unit_create", {
                    "token": test_token,
                    "army": army,
                    "unit_type": unit_type,
                    "x": x,
                    "y": y
                })
            except:
                pass
        
        def render_data():
            # Get full board data (includes all tiles and units)
            board_data, elapsed1 = self.rpc("game_board", {"token": test_token})
            
            # Simulate rendering tile lookups
            tile_lookups = 0
            for _ in range(5):  # Simulate 5 tile info requests
                x, y = random.randint(0, 11), random.randint(0, 9)
                _, elapsed = self.rpc("tile", {"token": test_token, "x": x, "y": y})
                tile_lookups += elapsed
            
            return elapsed1 + (tile_lookups / 5)  # Average tile lookup time
            
        return self.measure_operation("Rendering Data Generation", render_data)
    
    def run_all_benchmarks(self):
        """Run all benchmarks and display results"""
        print("🚀 Advance Wars RPC Performance Benchmark")
        print("=" * 60)
        print("📋 Testing environment:")
        print(f"   • Server: {self.base_url}")
        print(f"   • Token: {self.token}")
        print("=" * 60)
        
        benchmarks = [
            ("🎮 Game Creation", self.benchmark_game_creation),
            ("🪖 Unit Creation", self.benchmark_unit_creation),
            ("🚶 Movement Calculation", self.benchmark_movement_calculation),
            ("⚔️  Combat Preview", self.benchmark_combat_preview),
            ("🗺️  Board Generation", self.benchmark_board_generation),
            ("🧭 Complex Pathfinding", self.benchmark_pathfinding_complex),
            ("🚢 Transport Operations", self.benchmark_transport_operations),
            ("💰 Economic Calculations", self.benchmark_economic_calculations),
            ("🎨 Rendering Data", self.benchmark_rendering_data),
        ]
        
        all_results = []
        
        for name, benchmark_func in benchmarks:
            print(f"\n{name}...")
            try:
                result = benchmark_func()
                all_results.append(result)
                
                print(f"   • Mean: {result['mean_ms']:.2f}ms")
                print(f"   • Median: {result['median_ms']:.2f}ms")
                print(f"   • Min/Max: {result['min_ms']:.2f}ms / {result['max_ms']:.2f}ms")
                print(f"   • Std Dev: {result['stdev_ms']:.2f}ms")
                print(f"   • Iterations: {result['iterations']}")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE SUMMARY")
        print("=" * 60)
        
        if not all_results:
            print("❌ No successful benchmark results")
            return
            
        # Sort by mean time
        all_results.sort(key=lambda x: x['mean_ms'])
        
        print("\n🏆 Fastest Operations:")
        for result in all_results[:3]:
            print(f"   • {result['name']}: {result['mean_ms']:.2f}ms avg")
        
        print("\n⚠️  Slowest Operations:")
        for result in all_results[-3:]:
            print(f"   • {result['name']}: {result['mean_ms']:.2f}ms avg")
        
        # Performance grades
        print("\n📈 Performance Grades:")
        for result in all_results:
            grade = self.get_performance_grade(result['mean_ms'])
            print(f"   • {result['name']}: {grade}")
        
        # Overall statistics
        total_mean = sum(r['mean_ms'] for r in all_results) / len(all_results)
        print(f"\n📊 Overall Average Response Time: {total_mean:.2f}ms")
        
        # Recommendations
        print("\n💡 Performance Insights:")
        self.provide_insights(all_results)
        
    def get_performance_grade(self, mean_ms: float) -> str:
        """Grade performance based on response time"""
        if mean_ms < 10:
            return "⚡ Excellent (<10ms)"
        elif mean_ms < 25:
            return "✅ Good (10-25ms)"
        elif mean_ms < 50:
            return "🔶 Acceptable (25-50ms)"
        elif mean_ms < 100:
            return "⚠️  Needs Optimization (50-100ms)"
        else:
            return "❌ Poor (>100ms)"
    
    def provide_insights(self, results: List[Dict]):
        """Provide performance insights based on results"""
        insights = []
        
        # Check for slow operations
        slow_ops = [r for r in results if r['mean_ms'] > 50]
        if slow_ops:
            insights.append(f"• {len(slow_ops)} operations exceed 50ms threshold")
        
        # Check for high variance
        high_variance = [r for r in results if r['stdev_ms'] > r['mean_ms'] * 0.5]
        if high_variance:
            insights.append(f"• {len(high_variance)} operations show high variance")
        
        # Database operations
        db_heavy = ["Game Creation", "Unit Creation", "Board Generation"]
        db_results = [r for r in results if r['name'] in db_heavy]
        if db_results:
            avg_db = sum(r['mean_ms'] for r in db_results) / len(db_results)
            insights.append(f"• Database operations average: {avg_db:.2f}ms")
        
        # Calculation heavy
        calc_heavy = ["Movement Calculation", "Combat Preview", "Complex Pathfinding"]
        calc_results = [r for r in results if r['name'] in calc_heavy]
        if calc_results:
            avg_calc = sum(r['mean_ms'] for r in calc_results) / len(calc_results)
            insights.append(f"• Calculation operations average: {avg_calc:.2f}ms")
        
        if not insights:
            insights.append("• All operations performing within acceptable limits")
        
        for insight in insights:
            print(insight)

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get("http://localhost:5000/")
        if response.status_code not in [200, 302, 404]:  # Accept redirects and 404s as signs server is up
            print("❌ Server not responding correctly.")
            exit(1)
    except requests.ConnectionError:
        print("❌ Cannot connect to server at http://localhost:5000")
        print("Please start the server with: python3 app.py")
        exit(1)
    
    # Run benchmarks
    benchmark = PerformanceBenchmark()
    benchmark.run_all_benchmarks()
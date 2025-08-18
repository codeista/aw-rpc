#!/usr/bin/env python3
"""
Performance baseline measurement for AW-RPC
Measures key API response times
"""

import time
import requests
import json
import statistics
from typing import List, Dict


class PerformanceBaseline:
    """Measure performance baselines for key operations"""
    
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
        self.results = {}
        
    def make_rpc_call(self, method: str, params: Dict) -> tuple:
        """Make RPC call and measure time"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        
        start_time = time.time()
        try:
            response = requests.post(self.base_url, json=payload, timeout=10)
            elapsed = (time.time() - start_time) * 1000  # Convert to ms
            return elapsed, response.json()
        except Exception as e:
            return None, {"error": str(e)}
    
    def measure_operation(self, name: str, method: str, params: Dict, iterations: int = 10) -> Dict:
        """Measure an operation multiple times"""
        times = []
        errors = 0
        
        for _ in range(iterations):
            elapsed, result = self.make_rpc_call(method, params)
            if elapsed is not None:
                times.append(elapsed)
            else:
                errors += 1
        
        if times:
            return {
                "name": name,
                "method": method,
                "iterations": iterations,
                "errors": errors,
                "min_ms": min(times),
                "max_ms": max(times),
                "avg_ms": statistics.mean(times),
                "median_ms": statistics.median(times),
                "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0
            }
        else:
            return {"name": name, "error": "All requests failed"}
    
    def run_baseline_tests(self):
        """Run all baseline performance tests"""
        print("🚀 Running Performance Baseline Tests...")
        print("=" * 60)
        
        # Create a test game
        token = f"perf-baseline-{int(time.time())}"
        
        # Test 1: Game Creation
        result = self.measure_operation(
            "Game Creation",
            "game_create_test",
            {"token": token},
            iterations=5
        )
        self.results["game_creation"] = result
        self.print_result(result)
        
        # Test 2: Game Board Retrieval
        result = self.measure_operation(
            "Game Board Retrieval",
            "game_board",
            {"token": token},
            iterations=20
        )
        self.results["game_board"] = result
        self.print_result(result)
        
        # Test 3: Unit Creation
        result = self.measure_operation(
            "Unit Creation",
            "unit_create",
            {"token": token, "army": "RED", "unit_type": "INFANTRY", "x": 0, "y": 0},
            iterations=10
        )
        self.results["unit_create"] = result
        self.print_result(result)
        
        # Test 4: Movement Calculation
        # First end turn to enable movement
        self.make_rpc_call("army_end_turn", {"token": token})
        self.make_rpc_call("army_end_turn", {"token": token})
        
        result = self.measure_operation(
            "Movement Range Calculation",
            "movement_range",
            {"token": token, "unit_x": 0, "unit_y": 0},
            iterations=10
        )
        self.results["movement_range"] = result
        self.print_result(result)
        
        # Test 5: Turn End
        result = self.measure_operation(
            "End Turn",
            "army_end_turn",
            {"token": token},
            iterations=10
        )
        self.results["end_turn"] = result
        self.print_result(result)
        
        # Test 6: Tile Info
        result = self.measure_operation(
            "Tile Information",
            "tile",
            {"token": token, "x": 5, "y": 5},
            iterations=20
        )
        self.results["tile_info"] = result
        self.print_result(result)
        
        # Clean up
        self.make_rpc_call("game_delete", {"token": token})
        
        print("\n" + "=" * 60)
        self.print_summary()
    
    def print_result(self, result: Dict):
        """Print a single result"""
        print(f"\n📊 {result['name']}:")
        if "error" in result:
            print(f"   ❌ Error: {result['error']}")
        else:
            print(f"   Iterations: {result['iterations']} (Errors: {result['errors']})")
            print(f"   Min: {result['min_ms']:.2f}ms")
            print(f"   Max: {result['max_ms']:.2f}ms")
            print(f"   Avg: {result['avg_ms']:.2f}ms")
            print(f"   Median: {result['median_ms']:.2f}ms")
            print(f"   StdDev: {result['stdev_ms']:.2f}ms")
    
    def print_summary(self):
        """Print performance summary"""
        print("📈 PERFORMANCE SUMMARY")
        print("-" * 60)
        print(f"{'Operation':<30} {'Avg (ms)':<12} {'Status'}")
        print("-" * 60)
        
        for name, result in self.results.items():
            if "error" not in result:
                avg = result['avg_ms']
                status = "✅ Good" if avg < 50 else "⚠️  Slow" if avg < 100 else "❌ Too Slow"
                print(f"{result['name']:<30} {avg:>8.2f}ms   {status}")
        
        print("\n🎯 Performance Targets:")
        print("   ✅ Good: < 50ms")
        print("   ⚠️  Slow: 50-100ms")
        print("   ❌ Too Slow: > 100ms")


def main():
    """Run performance baseline tests"""
    # Check if server is running
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding properly")
            return
    except:
        print("❌ Server not running at http://localhost:5000")
        print("   Please start the server with: python app.py")
        return
    
    baseline = PerformanceBaseline()
    baseline.run_baseline_tests()
    
    # Save results
    with open("performance_baseline.json", "w") as f:
        json.dump(baseline.results, f, indent=2)
    print("\n✅ Results saved to performance_baseline.json")


if __name__ == "__main__":
    main()
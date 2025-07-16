#!/usr/bin/env python3
"""
Performance Testing Suite for Advance Wars RPC
Tests response times after modularization
"""

import time
import requests
import statistics
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

# Test configuration
BASE_URL = "http://localhost:5000"
NUM_ITERATIONS = 100
CONCURRENT_REQUESTS = 10

class PerformanceTest:
    def __init__(self):
        self.session = requests.Session()
        self.game_token = None
        self.results = {}
        
    def rpc(self, method: str, params: dict = None):
        """Make RPC call and measure time"""
        payload = {
            "method": method,
            "params": params or {},
            "id": 1,
            "jsonrpc": "2.0"
        }
        
        start = time.perf_counter()
        response = self.session.post(f"{BASE_URL}/api", json=payload)
        end = time.perf_counter()
        
        return end - start, response.json()
    
    def test_game_creation(self, iterations: int = 10):
        """Test game creation performance"""
        print(f"\n🎮 Testing game creation ({iterations} iterations)...")
        times = []
        
        for i in range(iterations):
            token = f"perf_test_{i}_{int(time.time())}"
            duration, result = self.rpc("game_create_test", {"token": token})
            times.append(duration)
            
            if i == 0:  # Keep first game for other tests
                self.game_token = token
                
        self._report_stats("Game Creation", times)
        return times
    
    def test_board_retrieval(self, iterations: int = NUM_ITERATIONS):
        """Test board state retrieval performance"""
        print(f"\n🗺️  Testing board retrieval ({iterations} iterations)...")
        times = []
        
        for _ in range(iterations):
            duration, result = self.rpc("get_game_board", {"token": self.game_token})
            times.append(duration)
            
        self._report_stats("Board Retrieval", times)
        return times
    
    def test_unit_operations(self, iterations: int = 50):
        """Test unit creation and movement performance"""
        print(f"\n🪖 Testing unit operations ({iterations} iterations)...")
        
        # Unit creation times
        creation_times = []
        for i in range(iterations):
            x = (i % 10)
            y = 3 + (i // 10)
            duration, result = self.rpc("unit_create", {
                "token": self.game_token,
                "unit_type": "INFANTRY",
                "x": x,
                "y": y
            })
            creation_times.append(duration)
            
        self._report_stats("Unit Creation", creation_times)
        
        # End turn to enable movement
        self.rpc("end_turn", {"token": self.game_token})
        
        # Movement validation times
        movement_times = []
        for i in range(min(iterations, 20)):
            duration, result = self.rpc("get_valid_moves", {
                "token": self.game_token,
                "x": i % 10,
                "y": 3
            })
            movement_times.append(duration)
            
        self._report_stats("Movement Validation", movement_times)
        
        return creation_times, movement_times
    
    def test_combat_calculations(self, iterations: int = 50):
        """Test combat preview calculations"""
        print(f"\n⚔️  Testing combat calculations ({iterations} iterations)...")
        
        # Create some units for combat testing
        self.rpc("unit_create", {"token": self.game_token, "unit_type": "TANK", "x": 0, "y": 0})
        self.rpc("end_turn", {"token": self.game_token})
        self.rpc("unit_create", {"token": self.game_token, "unit_type": "TANK", "x": 1, "y": 0})
        
        times = []
        for _ in range(iterations):
            duration, result = self.rpc("get_combat_preview", {
                "token": self.game_token,
                "x": 0,
                "y": 0,
                "x2": 1,
                "y2": 0
            })
            times.append(duration)
            
        self._report_stats("Combat Calculations", times)
        return times
    
    def test_concurrent_requests(self, num_threads: int = CONCURRENT_REQUESTS):
        """Test concurrent request handling"""
        print(f"\n🔄 Testing concurrent requests ({num_threads} threads)...")
        
        def make_request(i):
            start = time.perf_counter()
            self.rpc("get_game_board", {"token": self.game_token})
            return time.perf_counter() - start
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_threads * 10)]
            times = [future.result() for future in as_completed(futures)]
            
        self._report_stats("Concurrent Requests", times)
        return times
    
    def test_frontend_loading(self):
        """Test frontend asset loading times"""
        print(f"\n🎨 Testing frontend loading...")
        
        endpoints = [
            ("/", "Main page"),
            ("/test_game", "Test game page"),
            ("/static/js/render.js", "Main render script"),
            ("/static/sprites/terrain_sprites.png", "Terrain sprites"),
            ("/static/sprites/unit_sprites.png", "Unit sprites"),
        ]
        
        results = []
        for endpoint, name in endpoints:
            start = time.perf_counter()
            response = self.session.get(f"{BASE_URL}{endpoint}")
            duration = time.perf_counter() - start
            size = len(response.content) / 1024  # KB
            
            print(f"  {name}: {duration*1000:.1f}ms, {size:.1f}KB")
            results.append((name, duration, size))
            
        return results
    
    def test_api_endpoints(self):
        """Test various API endpoint response times"""
        print(f"\n🔌 Testing API endpoints...")
        
        # Test various RPC methods
        methods = [
            ("get_unit_costs", {}),
            ("get_damage_chart", {}),
            ("get_army_economy", {"token": self.game_token}),
            ("get_production_options", {"token": self.game_token, "x": 0, "y": 3}),
            ("check_tile_info", {"token": self.game_token, "x": 5, "y": 5}),
        ]
        
        for method, params in methods:
            times = []
            for _ in range(20):
                duration, result = self.rpc(method, params)
                times.append(duration)
            
            avg_time = statistics.mean(times) * 1000
            print(f"  {method}: {avg_time:.1f}ms avg")
    
    def _report_stats(self, name: str, times: List[float]):
        """Report statistics for a test"""
        times_ms = [t * 1000 for t in times]  # Convert to milliseconds
        
        print(f"\n  {name} Results:")
        print(f"    Mean: {statistics.mean(times_ms):.2f}ms")
        print(f"    Median: {statistics.median(times_ms):.2f}ms")
        print(f"    Min: {min(times_ms):.2f}ms")
        print(f"    Max: {max(times_ms):.2f}ms")
        print(f"    Std Dev: {statistics.stdev(times_ms):.2f}ms" if len(times_ms) > 1 else "")
        
        # Check for outliers
        sorted_times = sorted(times_ms)
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        print(f"    95th percentile: {p95:.2f}ms")
        
        # Store results
        self.results[name] = {
            "mean": statistics.mean(times_ms),
            "median": statistics.median(times_ms),
            "min": min(times_ms),
            "max": max(times_ms),
            "std_dev": statistics.stdev(times_ms) if len(times_ms) > 1 else 0,
            "p95": p95
        }
    
    def run_all_tests(self):
        """Run all performance tests"""
        print("🚀 Starting Performance Test Suite")
        print("=" * 60)
        
        # Check server
        try:
            response = requests.get(BASE_URL)
            print("✅ Server is running")
        except:
            print("❌ Server not running! Start with: source flask-env/bin/activate && python3 app.py")
            return False
        
        # Run tests
        self.test_game_creation(10)
        self.test_board_retrieval(100)
        self.test_unit_operations(50)
        self.test_combat_calculations(50)
        self.test_concurrent_requests(10)
        self.test_api_endpoints()
        self.test_frontend_loading()
        
        # Summary
        self._print_summary()
        return True
    
    def _print_summary(self):
        """Print performance summary"""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE TEST SUMMARY")
        print("=" * 60)
        
        # Performance targets
        targets = {
            "Game Creation": 50,      # 50ms target
            "Board Retrieval": 20,    # 20ms target
            "Unit Creation": 10,      # 10ms target
            "Movement Validation": 15, # 15ms target
            "Combat Calculations": 10, # 10ms target
            "Concurrent Requests": 30  # 30ms target
        }
        
        print("\nResponse Time Performance:")
        print("-" * 60)
        print(f"{'Operation':<25} {'Mean':>8} {'P95':>8} {'Target':>8} {'Status':>8}")
        print("-" * 60)
        
        all_passed = True
        for name, stats in self.results.items():
            target = targets.get(name, 50)
            mean = stats['mean']
            p95 = stats['p95']
            status = "✅ PASS" if mean <= target else "⚠️  SLOW"
            if mean > target:
                all_passed = False
                
            print(f"{name:<25} {mean:>7.1f}ms {p95:>7.1f}ms {target:>7}ms {status:>8}")
        
        print("\n" + "-" * 60)
        if all_passed:
            print("🎉 All performance targets met!")
        else:
            print("⚠️  Some operations exceed target times")
            
        # Performance grade
        avg_response = statistics.mean([s['mean'] for s in self.results.values()])
        print(f"\nOverall average response time: {avg_response:.1f}ms")
        
        if avg_response < 15:
            grade = "A+ (Excellent)"
        elif avg_response < 25:
            grade = "A (Very Good)"
        elif avg_response < 35:
            grade = "B (Good)"
        elif avg_response < 50:
            grade = "C (Acceptable)"
        else:
            grade = "D (Needs Improvement)"
            
        print(f"Performance Grade: {grade}")
            
        # Save results
        with open('performance_results.json', 'w') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'results': self.results,
                'average_response_ms': avg_response,
                'grade': grade
            }, f, indent=2)
            
        print(f"\n📄 Detailed results saved to performance_results.json")


if __name__ == "__main__":
    tester = PerformanceTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
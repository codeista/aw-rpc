#!/usr/bin/env python3
"""
Performance Benchmark Test
Measures performance of key operations before and after fixes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import requests
import json
import random
import string
import time
from statistics import mean, stdev

def generate_token():
    """Generate unique token"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def rpc_call(method: str, params: dict = None) -> dict:
    """Make RPC call to the server"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    }
    
    try:
        response = requests.post("http://localhost:5000/api", json=payload)
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
        
        result = response.json()
        if "error" in result:
            return {"error": result["error"]}
        
        result_data = result.get("result", result)
        if isinstance(result_data, dict) and result_data.get("error") == True:
            return {"error": result_data.get("message", "Unknown error")}
        
        return result_data
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def measure_operation(name, operation, iterations=10):
    """Measure operation performance"""
    times = []
    errors = 0
    
    for i in range(iterations):
        start = time.time()
        result = operation()
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        if isinstance(result, dict) and "error" in result:
            errors += 1
        else:
            times.append(elapsed)
    
    if times:
        avg = mean(times)
        std = stdev(times) if len(times) > 1 else 0
        return {
            "name": name,
            "avg_ms": round(avg, 2),
            "std_ms": round(std, 2),
            "min_ms": round(min(times), 2),
            "max_ms": round(max(times), 2),
            "errors": errors,
            "iterations": iterations
        }
    else:
        return {
            "name": name,
            "avg_ms": 0,
            "std_ms": 0,
            "min_ms": 0,
            "max_ms": 0,
            "errors": errors,
            "iterations": iterations
        }

def benchmark_game_creation():
    """Benchmark game creation"""
    def create_game():
        token = generate_token()
        return rpc_call("game_create_test", {"token": token})
    
    return measure_operation("Game Creation", create_game)

def benchmark_unit_creation():
    """Benchmark unit creation"""
    token = generate_token()
    rpc_call("game_create_test", {"token": token})
    
    def create_unit():
        return rpc_call("unit_create", {
            "token": token,
            "player_id": 0,
            "unit_type": "INFANTRY",
            "x": random.randint(0, 9),
            "y": random.randint(0, 11)
        })
    
    return measure_operation("Unit Creation", create_unit)

def benchmark_production_check():
    """Benchmark production facility checks"""
    token = generate_token()
    rpc_call("game_create_test", {"token": token})
    
    def check_production():
        return rpc_call("get_production_info", {
            "token": token,
            "x": 0,
            "y": 4  # Factory position
        })
    
    return measure_operation("Production Check", check_production)

def benchmark_combat_preview():
    """Benchmark combat preview"""
    token = generate_token()
    rpc_call("game_create_test", {"token": token})
    
    # Create units for combat
    rpc_call("unit_create", {
        "token": token,
        "player_id": 0,
        "unit_type": "TANK",
        "x": 4, "y": 4
    })
    
    rpc_call("unit_create", {
        "token": token,
        "player_id": 1,
        "unit_type": "TANK",
        "x": 5, "y": 4
    })
    
    # End turns
    rpc_call("army_end_turn", {"token": token})
    rpc_call("army_end_turn", {"token": token})
    
    def preview_combat():
        return rpc_call("combat_preview", {
            "token": token,
            "attacker_x": 4, "attacker_y": 4,
            "defender_x": 5, "defender_y": 4
        })
    
    return measure_operation("Combat Preview", preview_combat)

def benchmark_board_retrieval():
    """Benchmark game board retrieval"""
    token = generate_token()
    rpc_call("game_create_test", {"token": token})
    
    # Add some units for realistic board
    for i in range(5):
        rpc_call("unit_create", {
            "token": token,
            "player_id": 0 if i % 2 == 0 else "BLUE",
            "unit_type": ["INFANTRY", "TANK", "RECON", "ARTILLERY", "TCOPTER"][i],
            "x": i * 2,
            "y": i
        })
    
    def get_board():
        return rpc_call("game_board", {"token": token})
    
    return measure_operation("Board Retrieval", get_board)

def benchmark_unit_movement():
    """Benchmark unit movement"""
    token = generate_token()
    rpc_call("game_create_test", {"token": token})
    
    # Create a unit
    rpc_call("unit_create", {
        "token": token,
        "player_id": 0,
        "unit_type": "INFANTRY",
        "x": 0, "y": 0
    })
    
    # End turns
    rpc_call("army_end_turn", {"token": token})
    rpc_call("army_end_turn", {"token": token})
    
    positions = [(1, 0), (1, 1), (2, 1), (2, 2), (3, 2)]
    pos_index = 0
    
    def move_unit():
        nonlocal pos_index
        if pos_index >= len(positions):
            pos_index = 0
        
        result = rpc_call("unit_move", {
            "token": token,
            "x": positions[pos_index - 1][0] if pos_index > 0 else 0,
            "y": positions[pos_index - 1][1] if pos_index > 0 else 0,
            "x2": positions[pos_index][0],
            "y2": positions[pos_index][1]
        })
        
        pos_index += 1
        
        # End turns for next move
        rpc_call("army_end_turn", {"token": token})
        rpc_call("army_end_turn", {"token": token})
        
        return result
    
    return measure_operation("Unit Movement", move_unit, iterations=5)

def run_benchmarks():
    """Run all benchmarks"""
    print("🚀 Advance Wars RPC Performance Benchmark")
    print("=" * 60)
    print("📊 Running performance tests...")
    print()
    
    # Check server
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code != 200:
            print("❌ Server not accessible")
            return
    except:
        print("❌ Server not running. Start with: python3 app.py")
        return
    
    benchmarks = [
        benchmark_game_creation,
        benchmark_unit_creation,
        benchmark_production_check,
        benchmark_combat_preview,
        benchmark_board_retrieval,
        benchmark_unit_movement
    ]
    
    results = []
    for benchmark in benchmarks:
        print(f"⏱️  Running {benchmark.__name__.replace('benchmark_', '').replace('_', ' ').title()}...")
        result = benchmark()
        results.append(result)
    
    # Display results
    print("\n" + "=" * 60)
    print("📊 BENCHMARK RESULTS")
    print("=" * 60)
    print(f"{'Operation':<25} {'Avg (ms)':<10} {'Std Dev':<10} {'Min':<8} {'Max':<8} {'Errors':<8}")
    print("-" * 75)
    
    total_avg = 0
    total_operations = 0
    
    for result in results:
        print(f"{result['name']:<25} {result['avg_ms']:<10} {result['std_ms']:<10} "
              f"{result['min_ms']:<8} {result['max_ms']:<8} {result['errors']:<8}")
        total_avg += result['avg_ms']
        total_operations += 1
    
    print("-" * 75)
    print(f"{'Average Response Time:':<25} {total_avg/total_operations:.2f} ms")
    
    # Performance summary
    print("\n📈 Performance Summary:")
    fast_ops = [r for r in results if r['avg_ms'] < 50]
    medium_ops = [r for r in results if 50 <= r['avg_ms'] < 100]
    slow_ops = [r for r in results if r['avg_ms'] >= 100]
    
    print(f"   🚀 Fast (<50ms): {len(fast_ops)} operations")
    print(f"   ⚡ Medium (50-100ms): {len(medium_ops)} operations")
    print(f"   🐌 Slow (>100ms): {len(slow_ops)} operations")
    
    if any(r['errors'] > 0 for r in results):
        print("\n⚠️  Some operations had errors:")
        for r in results:
            if r['errors'] > 0:
                print(f"   - {r['name']}: {r['errors']} errors")
    else:
        print("\n✅ All operations completed without errors")
    
    # Save results for comparison
    with open('temp/benchmark_results.json', 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": results,
            "summary": {
                "avg_response_time": round(total_avg/total_operations, 2),
                "fast_operations": len(fast_ops),
                "medium_operations": len(medium_ops),
                "slow_operations": len(slow_ops),
                "total_errors": sum(r['errors'] for r in results)
            }
        }, f, indent=2)
    
    print("\n💾 Results saved to temp/benchmark_results.json")

if __name__ == "__main__":
    run_benchmarks()
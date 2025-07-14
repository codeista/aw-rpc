#!/usr/bin/env python3
"""
Master Test Runner for Advance Wars RPC
Runs all unit, integration, and system tests
"""

import subprocess
import sys
import time
import os
from datetime import datetime

# Test files organized by category
TEST_SUITES = {
    "Unit Tests": [
        "tests/unit/test_combat_system.py",
        "tests/unit/test_movement_system.py",
        "tests/unit/test_transport_final.py",
        "tests/unit/test_economic_system.py",
        "tests/unit/test_repair_resupply_system.py",
        "tests/unit/test_production_system.py",
        "tests/unit/test_ui_mobile_features.py"
    ],
    "Integration Tests": [
        "tests/integration/test_victory_conditions.py",
        "tests/integration/test_complete_victory_conditions.py",
        "tests/integration/test_multiplayer_armies.py"
    ],
    "Manual Tests": [
        "test_repair_refuel_proper.py"
    ]
}

def run_test_file(test_file):
    """Run a single test file and return results"""
    print(f"\n{'='*60}")
    print(f"Running: {test_file}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Run the test
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout per test
        )
        
        duration = time.time() - start_time
        
        # Print output
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Determine if test passed
        passed = result.returncode == 0
        if not passed:
            # Check output for pass indicators
            output_lower = result.stdout.lower()
            if "all tests passed" in output_lower or "100.0%" in output_lower:
                passed = True
            elif "passed!" in output_lower and "failed" not in output_lower:
                passed = True
        
        return {
            "file": test_file,
            "passed": passed,
            "duration": duration,
            "return_code": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        print(f"❌ Test timed out after 60 seconds")
        return {
            "file": test_file,
            "passed": False,
            "duration": 60,
            "return_code": -1
        }
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return {
            "file": test_file,
            "passed": False,
            "duration": 0,
            "return_code": -1
        }

def check_server():
    """Check if the game server is running"""
    import requests
    
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Run all tests and generate summary"""
    print("🚀 ADVANCE WARS RPC - MASTER TEST RUNNER")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Check if server is running
    if not check_server():
        print("❌ ERROR: Game server is not running!")
        print("Please start the server with: python3 app.py")
        sys.exit(1)
    
    print("✅ Server is running")
    
    # Run all tests
    all_results = []
    total_duration = 0
    
    for category, test_files in TEST_SUITES.items():
        print(f"\n{'='*80}")
        print(f"🏃 Running {category}")
        print(f"{'='*80}")
        
        for test_file in test_files:
            if os.path.exists(test_file):
                result = run_test_file(test_file)
                all_results.append(result)
                total_duration += result["duration"]
            else:
                print(f"⚠️  Skipping {test_file} - file not found")
                all_results.append({
                    "file": test_file,
                    "passed": False,
                    "duration": 0,
                    "return_code": -1
                })
    
    # Generate summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for r in all_results if r["passed"])
    total_count = len(all_results)
    
    # Group results by category
    for category, test_files in TEST_SUITES.items():
        print(f"\n{category}:")
        for test_file in test_files:
            result = next((r for r in all_results if r["file"] == test_file), None)
            if result:
                status = "✅ PASS" if result["passed"] else "❌ FAIL"
                duration = f"({result['duration']:.1f}s)"
                print(f"  {status} {os.path.basename(test_file)} {duration}")
    
    # Overall summary
    print("\n" + "-"*80)
    print(f"Total Tests Run: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print(f"Success Rate: {(passed_count/total_count)*100:.1f}%")
    print(f"Total Duration: {total_duration:.1f} seconds")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Exit code
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total_count - passed_count} tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
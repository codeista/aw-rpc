#!/usr/bin/env python3
"""
Comprehensive test runner for AW-RPC
"""

import subprocess
import sys
import os

def run_test(test_name, test_file):
    """Run a single test and report results"""
    print(f"\n{'='*60}")
    print(f"Running {test_name}...")
    print('='*60)
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, 
                              text=True,
                              timeout=30)
        
        if result.returncode == 0:
            print(f"✅ {test_name} PASSED")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {test_name} FAILED")
            if result.stdout:
                print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ {test_name} TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ {test_name} ERROR: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 AW-RPC Test Suite")
    print("===================")
    
    tests = [
        ("Click Handler Tests", "test_click_handling.py"),
        ("Sprite Extraction Tests", "test_sprite_extraction.py"),
    ]
    
    # Add more test files if they exist
    optional_tests = [
        ("Game Mechanics Tests", "test_game_mechanics.py"),
        ("Transport System Tests", "test_transport_system.py"),
        ("RPC API Tests", "test_api.py"),
    ]
    
    for test_name, test_file in optional_tests:
        if os.path.exists(test_file):
            tests.append((test_name, test_file))
    
    results = []
    
    for test_name, test_file in tests:
        if os.path.exists(test_file):
            success = run_test(test_name, test_file)
            results.append((test_name, success))
        else:
            print(f"\n⚠️  Skipping {test_name} - {test_file} not found")
            results.append((test_name, None))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)
    total = len(results)
    
    for test_name, result in results:
        if result is True:
            print(f"✅ {test_name}")
        elif result is False:
            print(f"❌ {test_name}")
        else:
            print(f"⚠️  {test_name} (skipped)")
    
    print(f"\nTotal: {total} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    
    if failed == 0 and passed > 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {failed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
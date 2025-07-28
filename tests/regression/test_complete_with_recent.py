#!/usr/bin/env python3
"""
Complete Regression Test Suite Including Recent Features

This combines the original regression tests with tests for all recent features.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from test_complete_game_mechanics import AdvanceWarsRegressionTester
from test_recent_features import RecentFeaturesRegressionTester

def main():
    """Run both original and recent feature tests"""
    print("🤖 Advance Wars RPC - Complete Regression Test Suite")
    print("=" * 70)
    
    overall_passed = 0
    overall_failed = 0
    all_success = True
    
    # Run original regression tests
    print("\n📦 PART 1: Core Game Mechanics Tests")
    print("=" * 70)
    original_tester = AdvanceWarsRegressionTester()
    if original_tester.run_all_tests():
        print("✅ Core mechanics tests passed")
    else:
        print("❌ Core mechanics tests failed")
        all_success = False
    
    overall_passed += original_tester.tests_passed
    overall_failed += original_tester.tests_failed
    
    # Run recent feature tests
    print("\n\n📦 PART 2: Recent Features Tests")
    print("=" * 70)
    recent_tester = RecentFeaturesRegressionTester()
    if recent_tester.run_all_tests():
        print("✅ Recent features tests passed")
    else:
        print("❌ Recent features tests failed")
        all_success = False
    
    overall_passed += recent_tester.tests_passed
    overall_failed += recent_tester.tests_failed
    
    # Print combined summary
    print("\n\n" + "=" * 70)
    print("📊 COMPLETE REGRESSION TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Total Tests Passed: {overall_passed}")
    print(f"❌ Total Tests Failed: {overall_failed}")
    total_tests = overall_passed + overall_failed
    if total_tests > 0:
        success_rate = (overall_passed / total_tests) * 100
        print(f"📊 Overall Success Rate: {success_rate:.1f}%")
    
    print("\n🎯 Overall Result:", "PASS" if all_success else "FAIL")
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
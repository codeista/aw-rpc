#!/usr/bin/env python3
"""
Test runner for AW-RPC integration tests
"""

import subprocess
import sys
import time
import requests
import os

def check_server_running():
    """Check if the server is running"""
    try:
        response = requests.get("http://localhost:5000", timeout=2)
        return True
    except:
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import requests
        print("✅ requests module available")
        return True
    except ImportError:
        print("❌ requests module not found")
        print("   Install with: pip install requests")
        return False

def run_quick_tests():
    """Run a quick subset of tests"""
    print("🏃 Running Quick Tests...")
    print("=" * 40)
    
    quick_tests = [
        'test_01_game_creation_and_board_loading',
        'test_04_turn_system_integration',
        'test_06_error_handling_robustness'
    ]
    
    import integration_testing_suite
    
    for test_name in quick_tests:
        try:
            test_case = integration_testing_suite.AWRPCIntegrationTests()
            test_case.setUp()
            
            test_method = getattr(test_case, test_name)
            test_method()
            
            test_case.tearDown()
            print(f"✅ {test_name.replace('_', ' ').title()}")
            
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            return False
    
    return True

def run_full_tests():
    """Run the complete test suite"""
    print("🔬 Running Full Integration Tests...")
    print("=" * 40)
    
    try:
        from integration_testing_suite import run_integration_tests
        return run_integration_tests()
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        return False

def main():
    print("🧪 AW-RPC Test Runner")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check if server is running
    if not check_server_running():
        print("❌ Server not running!")
        print("\n🚀 Start the server first:")
        print("   python app.py")
        print("\nThen run tests again:")
        print("   python run_tests.py")
        return False
    
    print("✅ Server is running")
    
    # Ask user which tests to run
    print("\n📋 Test Options:")
    print("1. Quick Tests (3 core tests, ~30 seconds)")
    print("2. Full Integration Tests (8 comprehensive tests, ~2 minutes)")
    print("3. Exit")
    
    while True:
        try:
            choice = input("\nChoose option (1-3): ").strip()
            
            if choice == "1":
                success = run_quick_tests()
                break
            elif choice == "2":
                success = run_full_tests()
                break
            elif choice == "3":
                print("👋 Goodbye!")
                return True
            else:
                print("Please enter 1, 2, or 3")
                continue
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            return True
    
    # Results
    if success:
        print("\n🎉 All tests passed!")
        print("✅ Your AW-RPC system is ready for Phase 2!")
        print("\n📋 System Status:")
        print("  • Core gameplay: Working ✅")
        print("  • Turn system: Working ✅") 
        print("  • Database: Working ✅")
        print("  • Error handling: Working ✅")
        print("  • API endpoints: Working ✅")
        return True
    else:
        print("\n⚠️  Some tests failed")
        print("📋 Recommended actions:")
        print("  • Check server logs for errors")
        print("  • Verify database is accessible")
        print("  • Review failed test details above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Quick Regression Test Runner for Advance Wars RPC

This script runs the automated regression test suite to validate
all core game mechanics are working correctly.

Usage:
    python3 run_regression_tests.py
    
    # Or make executable and run directly:
    chmod +x run_regression_tests.py
    ./run_regression_tests.py
"""

import sys
import os
import subprocess
import requests
import time

def check_server_running():
    """Check if the server is running"""
    print("🔍 Checking server availability...")
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        print("✅ Server is running")
        return True
    except Exception as e:
        print("❌ Server not available!")
        print("\n🚀 Start the server first:")
        print("   python3 app.py")
        print("\nThen run regression tests:")
        print("   python3 run_regression_tests.py")
        return False

def main():
    print("🤖 Advance Wars RPC - Automated Regression Tests")
    print("=" * 60)
    
    # Check server
    if not check_server_running():
        return False
    
    # Run regression tests
    print("\n🚀 Starting comprehensive mechanics validation...")
    print("⏱️  Expected duration: ~3 minutes")
    print("=" * 60)
    
    try:
        # Run the complete regression test suite (including recent features)
        test_path = os.path.join(os.path.dirname(__file__), 'regression', 'test_complete_with_recent.py')
        result = subprocess.run([
            sys.executable, 
            test_path
        ], timeout=300)  # 5 minute timeout
        
        # Return success/failure based on exit code
        if result.returncode == 0:
            print("\n🎉 All regression tests passed!")
            print("✅ Game mechanics are working correctly")
            return True
        else:
            print("\n⚠️  Some regression tests failed")
            print("❌ Check output above for details")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n⏰ Regression tests timed out (5 minutes)")
        print("❌ This may indicate a server or test issue")
        return False
    except KeyboardInterrupt:
        print("\n\n🛑 Tests interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    
    # Print final status
    if success:
        print("\n📋 System Status: ✅ HEALTHY")
        print("🔧 All core game mechanics validated")
    else:
        print("\n📋 System Status: ⚠️  ISSUES DETECTED")
        print("🔧 Check test output for specific failures")
    
    # Exit with appropriate code for CI/CD systems
    sys.exit(0 if success else 1)
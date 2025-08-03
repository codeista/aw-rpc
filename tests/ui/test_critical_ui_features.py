"""
Critical UI Feature Tests

This test suite covers the critical UI features that were missing from our tests,
which allowed bugs to slip through.
"""

import subprocess
import sys
import time
from datetime import datetime


def run_ui_tests():
    """Run all critical UI tests"""
    print("🧪 Running Critical UI Feature Tests")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_modules = [
        ("Production Modal", "test_production_modal.py"),
        ("Terrain Rendering", "test_terrain_rendering.py"),
        ("Basic Selenium", "test_base_selenium.py"),
        ("Movement System", "test_movement_system.py"),
        ("Highlighting", "test_highlighting_system.py"),
    ]
    
    results = []
    total_passed = 0
    total_failed = 0
    
    for test_name, test_file in test_modules:
        print(f"\n📋 Running {test_name} tests...")
        print("-" * 50)
        
        try:
            # Run pytest for this module
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd="tests/ui"
            )
            
            # Parse output
            output = result.stdout + result.stderr
            
            # Look for test results
            if "passed" in output:
                # Extract pass/fail counts
                import re
                match = re.search(r'(\d+) passed', output)
                passed = int(match.group(1)) if match else 0
                
                match = re.search(r'(\d+) failed', output)
                failed = int(match.group(1)) if match else 0
                
                total_passed += passed
                total_failed += failed
                
                if failed == 0:
                    print(f"✅ {test_name}: All {passed} tests passed")
                    results.append((test_name, "PASSED", f"{passed} tests"))
                else:
                    print(f"❌ {test_name}: {failed} failed, {passed} passed")
                    results.append((test_name, "FAILED", f"{failed} failed, {passed} passed"))
                    
                    # Show failures
                    if "FAILED" in output:
                        print("\nFailures:")
                        for line in output.split('\n'):
                            if "FAILED" in line and "::" in line:
                                print(f"  - {line.strip()}")
            else:
                print(f"❌ {test_name}: Error running tests")
                results.append((test_name, "ERROR", "Failed to run"))
                total_failed += 1
                
        except Exception as e:
            print(f"❌ {test_name}: Exception - {e}")
            results.append((test_name, "ERROR", str(e)))
            total_failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    for name, status, details in results:
        emoji = "✅" if status == "PASSED" else "❌"
        print(f"{emoji} {name}: {details}")
    
    print(f"\nTotal: {total_passed + total_failed} tests")
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    
    if total_failed == 0:
        print("\n🎉 All UI tests passed!")
    else:
        print(f"\n⚠️  {total_failed} tests failed")
    
    return total_failed == 0


if __name__ == "__main__":
    # Ensure server is running
    try:
        import requests
        response = requests.get("http://localhost:5000", timeout=2)
    except:
        print("❌ Server not running! Start it with: python3 app.py")
        sys.exit(1)
    
    # Run tests
    success = run_ui_tests()
    sys.exit(0 if success else 1)
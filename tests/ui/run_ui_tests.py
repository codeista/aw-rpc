#!/usr/bin/env python3
"""
UI Test Runner for Advance Wars RPC

This script runs the Selenium-based UI tests with proper setup and reporting.
"""

import os
import sys
import subprocess
import time
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ensure_server_running():
    """Ensure the game server is running"""
    import requests
    
    try:
        response = requests.get("http://localhost:5000/api/browse", timeout=2)
        if response.status_code == 200:
            print("✅ Server is already running")
            return True
    except:
        pass
    
    print("❌ Server not running. Please start it with:")
    print("   source flask-env/bin/activate && python3 app.py")
    return False


def install_dependencies():
    """Install required dependencies for UI testing"""
    print("📦 Checking dependencies...")
    
    required_packages = [
        'selenium',
        'pytest',
        'pytest-html',
        'pytest-xdist',
        'pillow',
        'opencv-python',
        'numpy'
    ]
    
    try:
        import selenium
        import cv2
        import PIL
        print("✅ All dependencies installed")
    except ImportError:
        print("📦 Installing missing dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install'] + required_packages)


def run_tests(test_suite=None, verbose=False, parallel=False):
    """Run the UI tests"""
    print("\n🧪 Starting UI Tests")
    print("=" * 60)
    
    # Base pytest command
    cmd = [sys.executable, '-m', 'pytest', '-v']
    
    # Add test directory or specific test
    test_path = 'tests/ui/'
    if test_suite:
        test_map = {
            'highlighting': 'test_highlighting_system.py',
            'movement': 'test_movement_system.py',
            'attack': 'test_attack_system.py',
            'complex': 'test_complex_scenarios.py',
            'basic': 'test_base_selenium.py'
        }
        
        if test_suite in test_map:
            test_path += test_map[test_suite]
        else:
            test_path += test_suite
    
    cmd.append(test_path)
    
    # Add options
    if verbose:
        cmd.append('-vv')
    
    if parallel:
        cmd.extend(['-n', 'auto'])  # Use all available CPUs
    
    # Add HTML report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_name = f'ui_test_report_{timestamp}.html'
    cmd.extend(['--html', f'tests/ui/reports/{report_name}', '--self-contained-html'])
    
    # Create reports directory
    os.makedirs('tests/ui/reports', exist_ok=True)
    os.makedirs('tests/ui/screenshots', exist_ok=True)
    
    # Run tests
    print(f"Running command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd)
    
    print(f"\n📊 Test report saved to: tests/ui/reports/{report_name}")
    
    return result.returncode


def run_specific_test(test_name):
    """Run a specific test by name"""
    cmd = [
        sys.executable, '-m', 'pytest', '-v', '-k', test_name,
        'tests/ui/', '--tb=short'
    ]
    
    return subprocess.run(cmd).returncode


def list_tests():
    """List all available UI tests"""
    print("\n📋 Available UI Tests:")
    print("=" * 60)
    
    cmd = [sys.executable, '-m', 'pytest', '--collect-only', 'tests/ui/', '-q']
    subprocess.run(cmd)


def main():
    parser = argparse.ArgumentParser(description='Run Advance Wars RPC UI Tests')
    parser.add_argument('--suite', choices=['highlighting', 'movement', 'attack', 'complex', 'basic'],
                        help='Run specific test suite')
    parser.add_argument('--test', help='Run specific test by name (e.g., test_movement_highlights_appear)')
    parser.add_argument('--list', action='store_true', help='List all available tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--parallel', '-p', action='store_true', help='Run tests in parallel')
    parser.add_argument('--no-server-check', action='store_true', help='Skip server check')
    
    args = parser.parse_args()
    
    print("🎮 Advance Wars RPC - UI Test Runner")
    print("=" * 60)
    
    # Check dependencies
    install_dependencies()
    
    # Check server
    if not args.no_server_check:
        if not ensure_server_running():
            return 1
    
    # Handle different modes
    if args.list:
        list_tests()
        return 0
    
    if args.test:
        print(f"\n🎯 Running specific test: {args.test}")
        return run_specific_test(args.test)
    
    # Run test suite
    return run_tests(args.suite, args.verbose, args.parallel)


if __name__ == '__main__':
    sys.exit(main())
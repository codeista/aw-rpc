#!/usr/bin/env python3
"""
UI Component Test Runner

Runs the new UI component tests for movement highlighting, unit rendering, and game interactions.
"""

import subprocess
import sys
import os
import argparse
from datetime import datetime


def run_component_tests(component=None, verbose=False):
    """Run UI component tests"""
    print("\n🧪 Running UI Component Tests")
    print("=" * 60)
    
    # Base command
    cmd = [sys.executable, '-m', 'pytest', '-v']
    
    # Component test mapping
    test_files = {
        'movement': 'test_movement_highlighting.py',
        'rendering': 'test_unit_rendering.py', 
        'interactions': 'test_game_interactions.py',
        'all': ''  # Run all tests
    }
    
    # Add specific test file or run all
    if component and component in test_files:
        if test_files[component]:  # Specific file
            cmd.append(f'tests/ui/{test_files[component]}')
        else:  # All tests
            cmd.append('tests/ui/')
    else:
        cmd.append('tests/ui/')
    
    # Add verbosity
    if verbose:
        cmd.append('-vv')
        cmd.append('--tb=short')
    
    # Add markers to show test progress
    cmd.extend(['-r', 'fEsxXpP'])
    
    # Add HTML report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = 'tests/ui/reports'
    os.makedirs(report_dir, exist_ok=True)
    
    report_name = f'component_test_report_{timestamp}.html'
    cmd.extend(['--html', f'{report_dir}/{report_name}', '--self-contained-html'])
    
    # Run tests
    print(f"Running: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)
    
    print(f"\n📊 Report saved to: {report_dir}/{report_name}")
    
    return result.returncode


def list_component_tests():
    """List available component tests"""
    print("\n📋 Available UI Component Test Suites:")
    print("=" * 60)
    print("  - movement    : Movement highlighting system tests")
    print("  - rendering   : Unit rendering and sprite tests")
    print("  - interactions: Game interaction handler tests")
    print("  - all         : Run all component tests")
    print()


def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import selenium
        import pytest
        print("✅ Dependencies verified")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install selenium pytest pytest-html")
        return False


def main():
    parser = argparse.ArgumentParser(description='Run UI Component Tests')
    parser.add_argument('component', nargs='?', default='all',
                        choices=['movement', 'rendering', 'interactions', 'all'],
                        help='Component to test (default: all)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List available test suites')
    
    args = parser.parse_args()
    
    print("🎮 Advance Wars RPC - UI Component Test Runner")
    
    if args.list:
        list_component_tests()
        return 0
    
    if not check_dependencies():
        return 1
    
    # Check if server is running
    import requests
    try:
        requests.get("http://localhost:5000/api/browse", timeout=2)
        print("✅ Server is running")
    except:
        print("⚠️  Server not detected at localhost:5000")
        print("   Start with: source flask-env/bin/activate && python3 app.py")
        return 1
    
    return run_component_tests(args.component, args.verbose)


if __name__ == '__main__':
    sys.exit(main())
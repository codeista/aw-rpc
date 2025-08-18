#!/usr/bin/env python3
"""
Run the newly created UI tests for production modal and terrain rendering
"""

import subprocess
import sys

def run_new_tests():
    """Run the new UI tests"""
    print("🧪 Running New UI Tests")
    print("=" * 60)
    
    # Run production modal tests
    print("\n📋 Testing Production Modal...")
    result1 = subprocess.run(
        [sys.executable, "-m", "pytest", "test_production_modal.py", "-v"],
        cwd="tests/ui"
    )
    
    # Run terrain rendering tests
    print("\n📋 Testing Terrain Rendering...")
    result2 = subprocess.run(
        [sys.executable, "-m", "pytest", "test_terrain_rendering.py", "-v"],
        cwd="tests/ui"
    )
    
    print("\n" + "=" * 60)
    print("✅ Tests completed!")
    
    return 0 if (result1.returncode == 0 and result2.returncode == 0) else 1

if __name__ == "__main__":
    sys.exit(run_new_tests())
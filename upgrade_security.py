#!/usr/bin/env python3
"""
Safe upgrade script for security patches
"""
import subprocess
import sys

def run_command(cmd):
    """Run a command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def main():
    print("🔒 Security Patch Upgrade Script")
    print("=" * 50)
    
    # Check if in virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("❌ Please activate the virtual environment first:")
        print("   source flask-env/bin/activate")
        return 1
    
    # Safe upgrade versions based on security advisories
    upgrades = [
        ("Flask", "2.3.3"),           # Fixes PYSEC-2023-62
        ("Flask-CORS", "4.0.2"),      # Fixes multiple vulnerabilities
        ("Werkzeug", "2.3.8"),        # Fixes PYSEC-2023-221 and others
        ("Jinja2", "3.1.6"),          # Fixes template vulnerabilities
        ("setuptools", "65.5.1"),     # Fixes PYSEC-2022-43012
    ]
    
    print("\n📋 Planned upgrades:")
    for package, version in upgrades:
        print(f"   {package} -> {version}")
    
    response = input("\nProceed with upgrades? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return 0
    
    # Perform upgrades
    print("\n🔧 Upgrading packages...")
    for package, version in upgrades:
        print(f"\n📦 Upgrading {package} to {version}...")
        cmd = f"pip install --upgrade {package}=={version}"
        code, stdout, stderr = run_command(cmd)
        
        if code == 0:
            print(f"   ✅ {package} upgraded successfully")
        else:
            print(f"   ❌ Failed to upgrade {package}")
            print(f"   Error: {stderr}")
            print("\n⚠️  Stopping upgrade process. Please check the error.")
            return 1
    
    # Test imports
    print("\n🧪 Testing imports...")
    test_imports = [
        "import flask",
        "import flask_cors",
        "import werkzeug",
        "import jinja2",
        "from flask import Flask",
        "from flask_cors import CORS",
    ]
    
    for test_import in test_imports:
        try:
            exec(test_import)
            print(f"   ✅ {test_import}")
        except ImportError as e:
            print(f"   ❌ {test_import} failed: {e}")
            return 1
    
    print("\n✅ All upgrades completed successfully!")
    print("\n📝 Next steps:")
    print("1. Run your test suite: python3 run_tests.py")
    print("2. Start the server: python3 app.py")
    print("3. Test the game functionality")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
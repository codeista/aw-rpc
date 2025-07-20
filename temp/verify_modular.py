#!/usr/bin/env python3
"""
Verification script for modular AW-RPC structure
Run this in your virtual environment to verify the modular refactor worked correctly
"""

import sys
import importlib

def test_imports():
    """Test that all modular components can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Test core imports
        import app_core
        print("  ✅ app_core")
        
        # Test route imports
        from routes.game_routes import game_bp
        print("  ✅ game_routes.game_bp")
        
        from routes.admin_routes import admin_bp
        print("  ✅ admin_routes.admin_bp")
        
        from routes.test_routes import test_bp
        print("  ✅ test_routes.test_bp")
        
        # Test RPC imports
        import routes.rpc_methods
        print("  ✅ rpc_methods")
        
        import routes.transport_rpc
        print("  ✅ transport_rpc")
        
        import routes.combat_rpc
        print("  ✅ combat_rpc")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False

def test_app_creation():
    """Test that the modular app can be created"""
    print("\n🏗️  Testing app creation...")
    
    try:
        import app_modular
        print("  ✅ app_modular imports successfully")
        
        # Check that app is created
        from app_core import app
        print("  ✅ Flask app instance exists")
        
        # Check blueprints are registered
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        expected_blueprints = ['game', 'admin', 'test']
        
        for bp_name in expected_blueprints:
            if bp_name in blueprint_names:
                print(f"  ✅ {bp_name} blueprint registered")
            else:
                print(f"  ❌ {bp_name} blueprint missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ App creation failed: {e}")
        return False

def test_rpc_methods():
    """Test that RPC methods are registered"""
    print("\n🔌 Testing RPC methods...")
    
    try:
        from app_core import jsonrpc
        
        # Check if jsonrpc has methods registered
        if hasattr(jsonrpc, 'jsonrpc_site'):
            site = jsonrpc.jsonrpc_site
            if hasattr(site, 'view_funcs'):
                methods = list(site.view_funcs.keys())
                print(f"  ✅ {len(methods)} RPC methods registered")
                
                # Check for key methods
                key_methods = ['game_board', 'unit_move', 'army_end_turn', 'unit_create']
                for method in key_methods:
                    if method in methods:
                        print(f"    ✅ {method}")
                    else:
                        print(f"    ❌ {method} missing")
                        
                return True
            else:
                print("  ❌ No view_funcs found")
                return False
        else:
            print("  ❌ No jsonrpc_site found")
            return False
            
    except Exception as e:
        print(f"  ❌ RPC method test failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🚀 AW-RPC Modular Verification")
    print("=" * 40)
    
    tests = [
        ("Import Tests", test_imports),
        ("App Creation Tests", test_app_creation), 
        ("RPC Method Tests", test_rpc_methods)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
            print(f"\n✅ {test_name} PASSED")
        else:
            print(f"\n❌ {test_name} FAILED")
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Modular refactor successful.")
        print("\n📋 Next steps:")
        print("  1. Test the server: python3 app_modular.py")
        print("  2. Check endpoints: http://localhost:5000/")
        print("  3. Run game tests: python3 tests/run_tests.py")
        return 0
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
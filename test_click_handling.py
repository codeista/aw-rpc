#!/usr/bin/env python3
"""
Test click handling functionality
"""

import time
import json

def test_click_handling():
    """Test that click handling is working correctly"""
    
    print("=== CLICK HANDLER TEST SUITE ===\n")
    
    # Test 1: Check if click handler files exist
    print("1. Checking click handler files...")
    import os
    
    files_to_check = [
        'static/js/click-handler.js',
        'static/js/test-click-handler.js',
        'templates/render.html'
    ]
    
    all_exist = True
    for file in files_to_check:
        exists = os.path.exists(file)
        status = "✓" if exists else "✗"
        print(f"   {status} {file}")
        if not exists:
            all_exist = False
    
    if not all_exist:
        print("\n❌ Some files are missing!")
        return False
    
    # Test 2: Check if click handler is included in HTML
    print("\n2. Checking HTML includes...")
    with open('templates/render.html', 'r') as f:
        html_content = f.read()
    
    includes = [
        ('click-handler.js', '<script src="/static/js/click-handler.js"></script>' in html_content),
        ('test-click-handler.js', '<script src="/static/js/test-click-handler.js"></script>' in html_content),
        ('Test button', 'onclick="runClickTests()' in html_content)
    ]
    
    all_included = True
    for name, included in includes:
        status = "✓" if included else "✗"
        print(f"   {status} {name}")
        if not included:
            all_included = False
    
    if not all_included:
        print("\n❌ Some includes are missing!")
        return False
    
    # Test 3: Check click handler implementation
    print("\n3. Checking click handler implementation...")
    with open('static/js/click-handler.js', 'r') as f:
        js_content = f.read()
    
    features = [
        ('Priority system', 'clickHandlers = {' in js_content),
        ('Process click function', 'function processClick' in js_content),
        ('Production handler', 'production-buildings' in js_content),
        ('Unit selection handler', 'unit-selection' in js_content),
        ('Movement handler', 'movement-execution' in js_content),
        ('Attack handler', 'attack-execution' in js_content),
        ('Alt-click handler', 'alt-click-transport' in js_content),
        ('Initialization', 'initializeClickHandler' in js_content)
    ]
    
    all_features = True
    for name, present in features:
        status = "✓" if present else "✗"
        print(f"   {status} {name}")
        if not present:
            all_features = False
    
    if not all_features:
        print("\n❌ Some features are missing!")
        return False
    
    # Test 4: Check render_legacy.js compatibility
    print("\n4. Checking render_legacy.js compatibility...")
    with open('static/js/render_legacy.js', 'r') as f:
        render_content = f.read()
    
    compatibility = [
        ('Defers to centralized handler', 'if (!window.clickHandler)' in render_content),
        ('Re-initialization', 'window.clickHandler.initialize' in render_content),
        ('advanceWarsCanvasClick defined', 'function advanceWarsCanvasClick' in render_content or 'window.canvasClick = advanceWarsCanvasClick' in render_content)
    ]
    
    all_compatible = True
    for name, compatible in compatibility:
        status = "✓" if compatible else "✗"
        print(f"   {status} {name}")
        if not compatible:
            all_compatible = False
    
    if not all_compatible:
        print("\n❌ Compatibility issues found!")
        return False
    
    # Test 5: Test suite implementation
    print("\n5. Checking test suite...")
    with open('static/js/test-click-handler.js', 'r') as f:
        test_content = f.read()
    
    test_features = [
        ('Test class', 'class ClickHandlerTests' in test_content),
        ('Initialization test', 'testClickHandlerInitialization' in test_content),
        ('Empty tile test', 'testEmptyTileClick' in test_content),
        ('Unit selection test', 'testUnitSelection' in test_content),
        ('Movement test', 'testMovementClick' in test_content),
        ('Production test', 'testProductionBuildingClick' in test_content),
        ('Attack test', 'testAttackClick' in test_content),
        ('Priority test', 'testClickPriorities' in test_content)
    ]
    
    all_tests = True
    for name, present in test_features:
        status = "✓" if present else "✗"
        print(f"   {status} {name}")
        if not present:
            all_tests = False
    
    if not all_tests:
        print("\n❌ Some tests are missing!")
        return False
    
    print("\n✅ All click handler tests passed!")
    print("\nTo run the interactive tests:")
    print("1. Start the game server")
    print("2. Open the game in a browser")
    print("3. Click the '🧪 Test Clicks' button")
    print("4. Check the browser console for results")
    print("\nOr open test_runner.html for a dedicated test interface")
    
    return True

if __name__ == "__main__":
    success = test_click_handling()
    exit(0 if success else 1)
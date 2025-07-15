"""
Unified Test API - Consolidates all test running endpoints into one flexible API
"""

from flask import Blueprint, request, jsonify
import subprocess
import os
import json
import time
import threading
from typing import Dict, List, Optional
import logging

app_logger = logging.getLogger('aw-rpc')

unified_test_api_bp = Blueprint('unified_test_api', __name__)

# Test execution state
test_execution_state = {
    'running': False,
    'current_test': None,
    'results': [],
    'start_time': None,
    'end_time': None
}

# Test categories and their associated test files
TEST_CATEGORIES = {
    'unit': {
        'name': 'Unit Tests',
        'tests': [
            'test_combat_system.py',
            'test_economic_system.py', 
            'test_movement_system.py',
            'test_production_system.py',
            'test_transport_features.py',
            'test_blackboat_repair_complete.py',
            'test_complete_repair_refuel.py',
            'test_ui_mobile_features.py',
            'test_victory_conditions.py'
        ]
    },
    'integration': {
        'name': 'Integration Tests',
        'tests': [
            'test_complete_victory_conditions.py',
            'test_game_improvements.py',
            'test_green_yellow_victory.py',
            'test_map_predeployed.py',
            'test_multiplayer_armies.py',
            'test_victory_fix_verification.py',
            'app_integration_test_map.py'
        ]
    },
    'system': {
        'name': 'System Tests',
        'tests': [
            'integration_testing_suite.py',
            'test_new_victory_maps.py',
            'test_server.py',
            'test_unittest.py',
            'updated_test_phase1.py'
        ]
    },
    'quick': {
        'name': 'Quick Smoke Tests',
        'tests': [
            'test_combat_system.py',
            'test_movement_system.py',
            'test_victory_conditions.py'
        ]
    }
}


@unified_test_api_bp.route('/api/tests', methods=['GET', 'POST'])
def unified_test_endpoint():
    """
    Unified test execution endpoint.
    
    GET /api/tests - Get test status and available tests
    POST /api/tests - Execute tests
    
    POST body parameters:
    - action: 'run', 'stop', 'status'
    - category: Test category to run (optional)
    - tests: List of specific test files to run (optional)
    - parallel: Run tests in parallel (default: false)
    
    Examples:
    POST /api/tests
    {
        "action": "run",
        "category": "unit"
    }
    
    POST /api/tests
    {
        "action": "run", 
        "tests": ["test_combat_system.py", "test_movement_system.py"]
    }
    """
    
    if request.method == 'GET':
        return get_test_info()
    
    data = request.get_json() or {}
    action = data.get('action', 'status')
    
    if action == 'status':
        return get_test_status()
    elif action == 'run':
        return run_tests(data)
    elif action == 'stop':
        return stop_tests()
    else:
        return jsonify({'error': f'Unknown action: {action}'}), 400


def get_test_info():
    """Get information about available tests."""
    return jsonify({
        'categories': TEST_CATEGORIES,
        'total_tests': sum(len(cat['tests']) for cat in TEST_CATEGORIES.values()),
        'status': test_execution_state,
        'usage': {
            'run_all': {'action': 'run'},
            'run_category': {'action': 'run', 'category': 'unit'},
            'run_specific': {'action': 'run', 'tests': ['test_combat_system.py']},
            'get_status': {'action': 'status'},
            'stop': {'action': 'stop'}
        }
    })


def get_test_status():
    """Get current test execution status."""
    if test_execution_state['running']:
        duration = time.time() - test_execution_state['start_time'] if test_execution_state['start_time'] else 0
        return jsonify({
            'running': True,
            'current_test': test_execution_state['current_test'],
            'duration': duration,
            'results': test_execution_state['results']
        })
    else:
        return jsonify({
            'running': False,
            'results': test_execution_state['results'],
            'start_time': test_execution_state['start_time'],
            'end_time': test_execution_state['end_time']
        })


def run_tests(data: dict):
    """Run specified tests."""
    if test_execution_state['running']:
        return jsonify({'error': 'Tests already running'}), 409
    
    # Determine which tests to run
    category = data.get('category')
    specific_tests = data.get('tests', [])
    parallel = data.get('parallel', False)
    
    tests_to_run = []
    
    if specific_tests:
        # Run specific tests
        tests_to_run = specific_tests
    elif category:
        # Run category tests
        if category not in TEST_CATEGORIES:
            return jsonify({'error': f'Unknown category: {category}'}), 400
        tests_to_run = TEST_CATEGORIES[category]['tests']
    else:
        # Run all tests
        for cat in TEST_CATEGORIES.values():
            tests_to_run.extend(cat['tests'])
    
    # Remove duplicates while preserving order
    tests_to_run = list(dict.fromkeys(tests_to_run))
    
    # Start test execution in background
    thread = threading.Thread(target=execute_tests, args=(tests_to_run, parallel))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'message': 'Tests started',
        'tests': tests_to_run,
        'parallel': parallel
    })


def stop_tests():
    """Stop running tests (placeholder - actual implementation would need process management)."""
    if not test_execution_state['running']:
        return jsonify({'message': 'No tests running'})
    
    # In a real implementation, we'd track subprocess PIDs and terminate them
    return jsonify({'message': 'Stop requested (not fully implemented)'}), 501


def execute_tests(tests: List[str], parallel: bool = False):
    """Execute the specified tests."""
    test_execution_state['running'] = True
    test_execution_state['results'] = []
    test_execution_state['start_time'] = time.time()
    test_execution_state['end_time'] = None
    
    try:
        if parallel:
            # Run tests in parallel (simplified - real implementation would use process pool)
            app_logger.warning("Parallel test execution not fully implemented")
        
        # Run tests sequentially
        for test_file in tests:
            test_execution_state['current_test'] = test_file
            result = run_single_test(test_file)
            test_execution_state['results'].append(result)
            
    finally:
        test_execution_state['running'] = False
        test_execution_state['current_test'] = None
        test_execution_state['end_time'] = time.time()


def run_single_test(test_file: str) -> dict:
    """Run a single test file and return results."""
    start_time = time.time()
    
    # Find the test file in the appropriate directory
    test_paths = [
        f'tests/unit/{test_file}',
        f'tests/integration/{test_file}',
        f'tests/system/{test_file}',
        f'tests/{test_file}',  # Fallback
        test_file  # Absolute path
    ]
    
    test_path = None
    for path in test_paths:
        if os.path.exists(path):
            test_path = path
            break
    
    if not test_path:
        return {
            'test': test_file,
            'status': 'error',
            'message': 'Test file not found',
            'duration': 0
        }
    
    try:
        # Run the test
        result = subprocess.run(
            ['python', test_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        duration = time.time() - start_time
        
        # Parse results
        passed = result.returncode == 0
        output = result.stdout + result.stderr
        
        # Try to extract test counts from output
        test_count = 0
        passed_count = 0
        failed_count = 0
        
        if 'tests passed' in output:
            # Parse pytest-style output
            import re
            match = re.search(r'(\d+) passed', output)
            if match:
                passed_count = int(match.group(1))
                test_count = passed_count
            match = re.search(r'(\d+) failed', output)
            if match:
                failed_count = int(match.group(1))
                test_count += failed_count
        
        return {
            'test': test_file,
            'status': 'passed' if passed else 'failed',
            'duration': duration,
            'test_count': test_count,
            'passed_count': passed_count,
            'failed_count': failed_count,
            'output': output[-1000:] if len(output) > 1000 else output  # Last 1000 chars
        }
        
    except subprocess.TimeoutExpired:
        return {
            'test': test_file,
            'status': 'timeout',
            'message': 'Test timed out after 5 minutes',
            'duration': 300
        }
    except Exception as e:
        return {
            'test': test_file,
            'status': 'error',
            'message': str(e),
            'duration': time.time() - start_time
        }


@unified_test_api_bp.route('/api/tests/categories')
def list_test_categories():
    """List available test categories."""
    return jsonify(TEST_CATEGORIES)


@unified_test_api_bp.route('/api/tests/history')
def get_test_history():
    """Get test execution history (placeholder)."""
    # In a real implementation, this would retrieve from a database
    return jsonify({
        'message': 'Test history not implemented',
        'last_run': test_execution_state.get('end_time'),
        'last_results': test_execution_state.get('results', [])
    })


# WebSocket connection test (special case)
@unified_test_api_bp.route('/api/tests/websocket')
def test_websocket():
    """Test WebSocket connectivity."""
    import socket
    
    try:
        # Try to connect to the Socket.IO endpoint
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', 5000))
        sock.close()
        
        if result == 0:
            return jsonify({
                'status': 'connected',
                'message': 'WebSocket server is reachable'
            })
        else:
            return jsonify({
                'status': 'unreachable',
                'message': 'Cannot connect to WebSocket server'
            }), 503
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# Custom game creation test (special case)
@unified_test_api_bp.route('/api/tests/create-game', methods=['POST'])
def test_create_game():
    """Test custom game creation."""
    from app_core import games
    from manager import GameManager
    from map_system import map_repository
    
    data = request.get_json() or {}
    
    # Get parameters
    map_name = data.get('map', 'test')
    players = data.get('players', 2)
    
    # Validate map
    game_map = map_repository.get_map(map_name)
    if not game_map:
        return jsonify({'error': f'Map not found: {map_name}'}), 400
    
    # Create test game
    token = f"api_test_{int(time.time())}"
    
    try:
        game = GameManager(token)
        game.setup(game_map)
        games[token] = game
        
        return jsonify({
            'success': True,
            'token': token,
            'map': map_name,
            'players': len(game_map.turn_order),
            'url': f'/render/{token}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
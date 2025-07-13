"""
Admin Routes Module
Handles all administrative routes including debug, testing, and logs
"""

from flask import Blueprint, redirect, jsonify
import secrets
import os
from app_core import app_logger, jsonrpc, ENHANCED_LOGGING
from map_system import map_repository

# Create blueprint for admin routes
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/logs')
def view_logs():
    """Enhanced log viewer"""
    try:
        logs = []
        
        # Try to read from enhanced logs first
        if os.path.exists('logs/game_events.log'):
            with open('logs/game_events.log', 'r') as f:
                lines = f.readlines()
            logs.extend([('GAME', line.strip()) for line in lines[-25:]])
        
        # Fallback to original logs
        if os.path.exists('game_events.log'):
            with open('game_events.log', 'r') as f:
                lines = f.readlines()
            logs.extend([('EVENT', line.strip()) for line in lines[-25:]])
        
        if not logs:
            return '<h2>No logs found</h2><p>Logs will appear here once the application starts generating events.</p>'
        
        # Format logs nicely
        formatted_logs = []
        for log_type, line in logs[-50:]:  # Show last 50 entries
            formatted_logs.append(f'<div class="{log_type.lower()}">[{log_type}] {line}</div>')
        
        return f'''
        <html>
        <head>
            <title>AW-RPC Logs</title>
            <style>
                body {{ font-family: monospace; margin: 20px; }}
                .game {{ color: blue; }}
                .event {{ color: green; }}
                .error {{ color: red; }}
                div {{ margin: 2px 0; }}
            </style>
        </head>
        <body>
            <h2>AW-RPC Recent Logs</h2>
            <div>{''.join(formatted_logs)}</div>
            <br><a href="/">Back to Game</a>
        </body>
        </html>
        '''
    except Exception as e:
        app_logger.error(f"Error viewing logs: {e}")
        return f'<h2>Error reading logs</h2><p>{str(e)}</p>'

@admin_bp.route('/debug/methods')
def debug_methods():
    """Enhanced debug endpoint"""
    try:
        methods_info = {
            'enhanced_logging': ENHANCED_LOGGING,
            'map_system': 'map_repository' in globals(),
            'total_methods': 0,
            'registered_methods': []
        }
        
        # Add map system details if available
        if 'map_repository' in globals():
            try:
                methods_info['map_system_details'] = {
                    'available_maps': map_repository.list_maps(),
                    'map_count': len(map_repository.list_maps()),
                    'test_map_available': map_repository.get_map('test') is not None
                }
            except Exception as e:
                methods_info['map_system_error'] = str(e)
        
        if hasattr(jsonrpc, 'jsonrpc_site'):
            site = jsonrpc.jsonrpc_site
            if hasattr(site, 'view_funcs'):
                methods = list(site.view_funcs.keys())
                methods_info['registered_methods'] = methods
                methods_info['total_methods'] = len(methods)
        
        return jsonify(methods_info)
    except Exception as e:
        return jsonify({'error': str(e)})

@admin_bp.route('/debug')
def debug_info():
    """Debug endpoint to see current game status"""
    # Import here to avoid circular imports
    from app import games
    
    active_games = []
    for token, game in games.items():
        board = game.board
        active_games.append({
            'token': token,
            'size': f"{board.width}x{board.height}",
            'current_turn': board.current_turn.name,
            'red_units': board.total_red_troops,
            'blue_units': board.total_blue_troops,
            'red_funds': board.red_funds,
            'blue_funds': board.blue_funds,
            'days': board.days
        })
    
    return jsonify({
        'active_games': active_games,
        'total_games': len(games)
    })

# Test game creation routes
@admin_bp.route('/test')
def create_terrain_test_game():
    """Create terrain-focused test game with predeployed units"""
    token = secrets.token_urlsafe(6)
    try:
        # Import here to avoid circular imports
        from app import get_predeployed_test_game, games
        
        game_manager = get_predeployed_test_game(token)
        games[token] = game_manager
        app_logger.info(f"Created terrain test game: {token}")
        return redirect(f'/game/{token}')
    except Exception as e:
        app_logger.error(f"Failed to create terrain test game: {e}")
        return f"Error creating test game: {e}", 500

@admin_bp.route('/test_comprehensive')  
def create_comprehensive_test():
    """Create comprehensive test game with all unit types"""
    token = secrets.token_urlsafe(6)
    try:
        # Import here to avoid circular imports
        from app import get_comprehensive_test_game, games
        
        game_manager = get_comprehensive_test_game(token)
        games[token] = game_manager
        app_logger.info(f"Created comprehensive test game: {token}")
        return redirect(f'/game/{token}')
    except Exception as e:
        app_logger.error(f"Failed to create comprehensive test game: {e}")
        return f"Error creating comprehensive test game: {e}", 500

@admin_bp.route('/test_interface')
def test_interface():
    """Complete testing interface with all testing tools"""
    from flask import render_template
    app_logger.info("Test interface accessed")
    return render_template('test_interface.html')

# Additional test routes will be moved here as well...
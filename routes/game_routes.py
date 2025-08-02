"""
Game Routes Module
Handles all game-related HTTP routes including creation, maps, and game pages
"""

from flask import Blueprint, render_template, request, jsonify
import secrets
from app_core import app_logger
from core.map_system import map_repository

# Create blueprint for game routes
game_bp = Blueprint('game', __name__)

@game_bp.route('/')
def index():
    """Landing page"""
    app_logger.info("Landing page accessed")
    return render_template('index.html')

@game_bp.route('/api/maps', methods=['GET'])
def get_available_maps():
    """API endpoint to get available maps"""
    try:
        maps = map_repository.list_maps()
        map_data = []
        
        for map_id in maps:
            map_obj = map_repository.get_map(map_id)
            if map_obj:
                # Handle turn_order safely
                armies = []
                if hasattr(map_obj, 'turn_order') and map_obj.turn_order:
                    armies = [army.name for army in map_obj.turn_order]
                elif hasattr(map_obj, 'armies') and map_obj.armies:
                    armies = [army.name for army in map_obj.armies]
                
                map_data.append({
                    'id': map_id,
                    'name': map_obj.name,
                    'width': map_obj.width,
                    'height': map_obj.height,
                    'armies': armies,
                    'turn_order': armies  # Add turn_order field for backward compatibility
                })
        
        return jsonify({'success': True, 'maps': map_data})
    except Exception as e:
        app_logger.error(f"Error getting maps: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@game_bp.route('/api/create_game', methods=['POST'])
def create_game_api():
    """API endpoint for creating a new game with setup parameters"""
    try:
        data = request.get_json()
        
        # Generate game token
        token = secrets.token_urlsafe(4)
        
        # Validate required fields
        required_fields = ['map', 'playerCount', 'turnLimit', 'players']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'})
        
        # Validate player setup
        players = data['players']
        if len(players) != data['playerCount']:
            return jsonify({'success': False, 'error': 'Player count mismatch'})
        
        # Check for duplicate colors
        colors = [p['color'] for p in players if p['color']]
        if len(colors) != len(set(colors)):
            return jsonify({'success': False, 'error': 'Duplicate army colors selected'})
        
        # Check all players have CO and color
        for i, player in enumerate(players):
            if not player.get('co'):
                return jsonify({'success': False, 'error': f'Player {i+1} must select a CO'})
            if not player.get('color'):
                return jsonify({'success': False, 'error': f'Player {i+1} must select an army color'})
        
        # Store game setup data
        game_setup = {
            'token': token,
            'map_id': data['map'],
            'player_count': data['playerCount'],
            'turn_limit': data['turnLimit'],
            'game_mode': data.get('gameMode', 'standard'),
            'players': players
        }
        
        # Import here to avoid circular imports
        from app import game_create_with_setup
        
        # Create the game with the selected map
        game_create_with_setup(token, game_setup)
        
        app_logger.info(f"Game created with setup: {token}, map: {data['map']}, players: {data['playerCount']}")
        
        return jsonify({'success': True, 'token': token})
        
    except Exception as e:
        app_logger.error(f"Error creating game: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@game_bp.route('/game/<token>')
def game(token: str):
    """Main game page"""
    app_logger.info(f"Game page accessed: {token}")
    return render_template('render.html', token=token)

@game_bp.route('/templates/<path:filename>')
def serve_template_files(filename):
    """Serve files from templates directory for sprite corrections"""
    from flask import send_from_directory
    return send_from_directory('templates', filename)
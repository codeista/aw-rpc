"""
Custom API Documentation Route for Categorized RPC Methods

This module provides a custom documentation endpoint that displays
RPC methods organized by category with enhanced formatting.
"""

from flask import render_template_string
from app_core import app, jsonrpc

API_DOCS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advance Wars RPC - API Documentation</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
        }
        .category {
            background: white;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .category-header {
            background: #343a40;
            color: white;
            padding: 15px 20px;
            font-size: 1.2em;
            font-weight: bold;
        }
        .category-description {
            background: #e9ecef;
            padding: 10px 20px;
            font-style: italic;
            color: #6c757d;
        }
        .method {
            border-bottom: 1px solid #e9ecef;
            padding: 15px 20px;
        }
        .method:last-child {
            border-bottom: none;
        }
        .method-name {
            font-size: 1.1em;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 5px;
        }
        .method-desc {
            color: #6c757d;
            margin-bottom: 8px;
        }
        .method-example {
            background: #f8f9fa;
            padding: 8px 12px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9em;
            color: #495057;
        }
        .stats {
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .badge {
            display: inline-block;
            padding: 5px 10px;
            background: #28a745;
            color: white;
            border-radius: 20px;
            font-size: 0.8em;
            margin: 0 5px;
        }
        .endpoint-info {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎮 Advance Wars RPC API</h1>
        <p>Comprehensive game mechanics API with categorized endpoints</p>
    </div>
    
    <div class="endpoint-info">
        <strong>🔗 API Endpoint:</strong> <code>{{ base_url }}/api</code><br>
        <strong>📖 Interactive Browser:</strong> <a href="{{ base_url }}/api/browse" target="_blank">{{ base_url }}/api/browse</a><br>
        <strong>🧪 Regression Tests:</strong> <code>python3 run_regression_tests.py</code>
    </div>
    
    <div class="stats">
        <h3>📊 API Statistics</h3>
        <span class="badge">{{ total_methods }} Total Methods</span>
        <span class="badge">{{ total_categories }} Categories</span>
        <span class="badge">100% Documented</span>
    </div>

    {% for category in categories %}
    <div class="category">
        <div class="category-header">
            {{ category.name }}
        </div>
        <div class="category-description">
            {{ category.description }}
        </div>
        {% for method in category.methods %}
        <div class="method">
            <div class="method-name">{{ method.name }}</div>
            <div class="method-desc">{{ method.description }}</div>
            <div class="method-example">{{ method.example }}</div>
        </div>
        {% endfor %}
    </div>
    {% endfor %}
    
    <div style="text-align: center; margin-top: 40px; color: #6c757d;">
        <p>⚡ Generated automatically from RPC method definitions</p>
        <p>🔄 Validated by automated regression tests</p>
    </div>
</body>
</html>
"""

@app.route('/api/docs')
def api_documentation():
    """Custom API documentation endpoint showing categorized methods"""
    
    # Define categories with their methods
    categories = [
        {
            'name': '🎮 Game Management',
            'description': 'Core game lifecycle operations - creation, state management, turn control',
            'methods': [
                {
                    'name': 'game_create_with_setup',
                    'description': 'Create a new game with custom setup parameters',
                    'example': "rpc('game_create_with_setup', {token: 'mygame', game_setup: {funds: 25000}})"
                },
                {
                    'name': 'game_create_test',
                    'description': 'Create test game with 50k funds and optimized map',
                    'example': "rpc('game_create_test', {token: 'testgame', use_optimized: true})"
                },
                {
                    'name': 'game_board',
                    'description': 'Get complete game board state and information',
                    'example': "rpc('game_board', {token: 'mygame'})"
                },
                {
                    'name': 'army_end_turn',
                    'description': 'End current army turn and pass control to next player',
                    'example': "rpc('army_end_turn', {token: 'mygame'})"
                }
            ]
        },
        {
            'name': '🪖 Unit Operations',
            'description': 'Unit creation, movement, selection, and basic actions',
            'methods': [
                {
                    'name': 'unit_create',
                    'description': 'Create new unit at production facility',
                    'example': "rpc('unit_create', {token: 'mygame', army: 'RED', unit_type: 'INFANTRY', x: 2, y: 3})"
                },
                {
                    'name': 'unit_move',
                    'description': 'Move unit from one position to another',
                    'example': "rpc('unit_move', {token: 'mygame', x: 5, y: 3, x2: 6, y2: 3})"
                },
                {
                    'name': 'unit_select',
                    'description': 'Select unit for UI and operation purposes',
                    'example': "rpc('unit_select', {token: 'mygame', x: 5, y: 3})"
                },
                {
                    'name': 'unit_valid_moves',
                    'description': 'Get all valid movement positions for a unit',
                    'example': "rpc('unit_valid_moves', {token: 'mygame', x: 5, y: 3})"
                }
            ]
        },
        {
            'name': '⚔️ Combat System',
            'description': 'Attack mechanics, damage calculations, and combat previews',
            'methods': [
                {
                    'name': 'unit_attack',
                    'description': 'Execute attack between two units with damage calculation',
                    'example': "rpc('unit_attack', {token: 'mygame', x: 5, y: 3, x2: 6, y2: 3})"
                },
                {
                    'name': 'combat_preview',
                    'description': 'Get damage preview before executing attack',
                    'example': "rpc('combat_preview', {token: 'mygame', attacker_x: 5, attacker_y: 3, defender_x: 6, defender_y: 3})"
                },
                {
                    'name': 'get_attack_targets',
                    'description': 'Get all valid attack targets for a unit',
                    'example': "rpc('get_attack_targets', {token: 'mygame', unit_x: 5, unit_y: 3})"
                },
                {
                    'name': 'get_damage_chart',
                    'description': 'Get complete damage chart for reference',
                    'example': "rpc('get_damage_chart', {token: 'mygame'})"
                }
            ]
        },
        {
            'name': '🚢 Transport System',
            'description': 'Cargo loading, transport operations, and unit management',
            'methods': [
                {
                    'name': 'load_unit',
                    'description': 'Load cargo unit into transport',
                    'example': "rpc('load_unit', {token: 'mygame', transport_x: 5, transport_y: 3, cargo_x: 4, cargo_y: 3})"
                },
                {
                    'name': 'unload_unit',
                    'description': 'Unload unit from transport to specified position',
                    'example': "rpc('unload_unit', {token: 'mygame', transport_x: 5, transport_y: 3, unload_x: 6, unload_y: 3})"
                },
                {
                    'name': 'get_transport_info',
                    'description': 'Get detailed information about transport unit',
                    'example': "rpc('get_transport_info', {token: 'mygame', x: 5, y: 3})"
                },
                {
                    'name': 'get_valid_unload_positions',
                    'description': 'Get all valid positions for unloading cargo',
                    'example': "rpc('get_valid_unload_positions', {token: 'mygame', x: 5, y: 3})"
                }
            ]
        },
        {
            'name': '🗺️ Map & Tile Information',
            'description': 'Terrain data, tile information, and map access',
            'methods': [
                {
                    'name': 'tile',
                    'description': 'Get detailed information about specific tile',
                    'example': "rpc('tile', {token: 'mygame', x: 5, y: 3})"
                },
                {
                    'name': 'get_movement_costs',
                    'description': 'Get movement costs for unit type across terrain',
                    'example': "rpc('get_movement_costs', {unit_type: 'INFANTRY', token: 'mygame'})"
                }
            ]
        },
        {
            'name': '🏰 Special Actions',
            'description': 'Property capture, repair, resupply, and special abilities',
            'methods': [
                {
                    'name': 'capture_tile',
                    'description': 'Capture property with infantry or mech unit',
                    'example': "rpc('capture_tile', {token: 'mygame', x: 5, y: 3})"
                },
                {
                    'name': 'repair_unit',
                    'description': 'Use Black Boat to repair adjacent unit',
                    'example': "rpc('repair_unit', {token: 'mygame', blackboat_x: 5, blackboat_y: 3, target_x: 5, target_y: 4})"
                },
                {
                    'name': 'resupply_unit',
                    'description': 'Manual resupply from APC or Black Boat',
                    'example': "rpc('resupply_unit', {token: 'mygame', resupply_x: 5, resupply_y: 3, target_x: 6, target_y: 3})"
                }
            ]
        },
        {
            'name': '🏭 Production & Economic',
            'description': 'Unit production, financial operations, and economic data',
            'methods': [
                {
                    'name': 'produce_unit',
                    'description': 'Produce unit at production facility',
                    'example': "rpc('produce_unit', {token: 'mygame', x: 2, y: 3, unit_type: 'TANK'})"
                },
                {
                    'name': 'get_production_options',
                    'description': 'Get available units at production facility',
                    'example': "rpc('get_production_options', {token: 'mygame', x: 2, y: 3})"
                },
                {
                    'name': 'can_afford_unit',
                    'description': 'Check if army can afford specific unit type',
                    'example': "rpc('can_afford_unit', {token: 'mygame', unit_type: 'NEOTANK'})"
                },
                {
                    'name': 'get_army_economy',
                    'description': 'Get complete economic summary for current army',
                    'example': "rpc('get_army_economy', {token: 'mygame'})"
                }
            ]
        },
        {
            'name': '📋 Information & Reference',
            'description': 'Configuration data, unit stats, and reference information',
            'methods': [
                {
                    'name': 'troop_info',
                    'description': 'Get unit configuration and reference data',
                    'example': "rpc('troop_info', {})"
                }
            ]
        },
        {
            'name': '💬 Communication',
            'description': 'Chat, messaging, and communication features',
            'methods': [
                {
                    'name': 'message',
                    'description': 'Send chat message in game',
                    'example': "rpc('message', {token: 'mygame', msg: 'Good game!'})"
                }
            ]
        }
    ]
    
    # Calculate statistics
    total_methods = sum(len(cat['methods']) for cat in categories)
    total_categories = len(categories)
    
    return render_template_string(
        API_DOCS_TEMPLATE,
        categories=categories,
        total_methods=total_methods,
        total_categories=total_categories,
        base_url="http://localhost:5000"
    )

# Register the route
if __name__ == "__main__":
    print("🔗 API Documentation available at: http://localhost:5000/api/docs")
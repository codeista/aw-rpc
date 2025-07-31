"""
Clean API v2 implementation - 8 core methods for the entire game.
Player-based system with server-side validation and state management.
"""

import uuid
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import asdict
import logging

from flask import Flask
from flask_jsonrpc import JSONRPC

from models_v2 import (
    GameStateV2, Player, Unit, Building, Tile, Terrain,
    SpriteColor, TerrainType, BuildingType, UnitType,
    GameAction
)

# Import existing game logic we'll reuse
from manager_v2 import GameManager
from gameboard import GameBoard
from map_system import Map, MapType, MapTile


logger = logging.getLogger(__name__)

# Global game storage (would be Redis/database in production)
games: Dict[str, GameStateV2] = {}

# Global manager storage for game logic
game_managers: Dict[str, GameManager] = {}


class GameAPIv2:
    """Clean API implementation with 8 core methods"""
    
    def __init__(self, app: Flask, jsonrpc: JSONRPC):
        self.app = app
        self.jsonrpc = jsonrpc
        self._register_methods()
        
    def _register_methods(self):
        """Register all API methods with Flask-JSONRPC"""
        self.jsonrpc.method('v2.create_game')(self.create_game)
        self.jsonrpc.method('v2.game_state')(self.game_state)
        self.jsonrpc.method('v2.select_tile')(self.select_tile)
        self.jsonrpc.method('v2.move_unit')(self.move_unit)
        self.jsonrpc.method('v2.attack')(self.attack)
        self.jsonrpc.method('v2.unit_action')(self.unit_action)
        self.jsonrpc.method('v2.create_unit')(self.create_unit)
        self.jsonrpc.method('v2.end_turn')(self.end_turn)
        self.jsonrpc.method('v2.get_production_options')(self.get_production_options)
        
    # ========== API METHODS ==========
    
    def create_game(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new game with player configuration.
        
        Args:
            config: {
                players: [{ name: str, color: str }],
                map: str (map name),
                settings: { starting_funds: int, fog_of_war: bool }
            }
        """
        game_id = str(uuid.uuid4())[:8]
        
        # Create players with assigned colors
        players = {}
        turn_order = []
        for i, player_data in enumerate(config['players']):
            player_id = f'player{i+1}'
            players[player_id] = Player(
                id=player_id,
                name=player_data['name'],
                color=SpriteColor(player_data['color']),
                funds=config.get('settings', {}).get('starting_funds', 5000)
            )
            turn_order.append(player_id)
            
        # Create game state
        game_state = GameStateV2(
            game_id=game_id,
            players=players,
            current_player_id=turn_order[0],
            turn_order=turn_order
        )
        
        # Create legacy game manager for game logic
        # TODO: Eventually replace with clean implementation
        map_name = config.get('map', 'test_map')
        board = self._create_board(map_name, players)
        manager = GameManager(None, board)  # Config not needed
        
        # Store both
        games[game_id] = game_state
        game_managers[game_id] = manager
        
        return {
            'game_id': game_id,
            'players': [
                {
                    'id': p.id,
                    'name': p.name,
                    'color': p.color.value,  # Convert enum to string
                    'funds': p.funds,
                    'team': p.team
                }
                for p in players.values()
            ],
            'map': {
                'name': map_name,
                'width': board.width,
                'height': board.height
            },
            'settings': config.get('settings', {})
        }
        
    def game_state(self, game_id: str) -> Dict[str, Any]:
        """Get complete game state"""
        game = games.get(game_id)
        manager = game_managers.get(game_id)
        
        if not game or not manager:
            raise ValueError(f"Game {game_id} not found")
            
        # Build tile array from manager's board
        tiles = []
        for y in range(manager.board.height):
            for x in range(manager.board.width):
                tile_data = self._build_tile_data(manager, x, y, game)
                tiles.append(tile_data)
                
        # Build player data
        player_data = {}
        for pid, player in game.players.items():
            # Count units and properties from manager
            unit_count = sum(1 for t in manager.board.grid 
                           if t.unit and t.unit.army.name == player.color.value.upper())
            property_count = sum(1 for t in manager.board.grid 
                               if t.mapTile and t.mapTile.army and 
                               t.mapTile.army.name == player.color.value.upper())
            
            player_data[pid] = {
                'name': player.name,
                'color': player.color.value,
                'funds': self._get_player_funds(manager, player.color.value),
                'unit_count': unit_count,
                'property_count': property_count
            }
            
        return {
            'current_player': game.current_player_id,
            'day': manager.board.days,
            'phase': game.phase,
            'players': player_data,
            'board': {
                'width': manager.board.width,
                'height': manager.board.height,
                'tiles': tiles
            },
            'active_unit': list(game.active_unit_pos) if game.active_unit_pos else None,
            'selected': list(game.selected_pos) if game.selected_pos else None
        }
        
    def select_tile(self, game_id: str, x: int, y: int) -> Dict[str, Any]:
        """Select a tile and get all valid actions"""
        game = games.get(game_id)
        manager = game_managers.get(game_id)
        
        if not game or not manager:
            raise ValueError(f"Game {game_id} not found")
            
        # Auto-commit active unit if selecting different tile
        committed_unit = None
        if game.active_unit_pos and game.active_unit_pos != (x, y):
            # End the active unit's turn
            ax, ay = game.active_unit_pos
            tile = manager.tile_at(ax, ay)
            if tile and tile.unit:
                tile.unit.has_moved = True
                tile.unit.done = True
                committed_unit = {'x': ax, 'y': ay}
            game.active_unit_pos = None
            
        # Update selection
        game.selected_pos = (x, y)
        
        # Get tile info
        tile = manager.tile_at(x, y)
        if not tile:
            raise ValueError(f"Invalid position ({x}, {y})")
            
        # Build response
        response = {
            'committed_unit': committed_unit,
            'selection': {
                'position': {'x': x, 'y': y},
                'terrain': self._get_terrain_info(tile),
                'building': self._get_building_info(tile) if tile.mapTile else None,
                'unit': None,
                'available_actions': [],
                'valid_moves': [],
                'valid_attacks': [],
                'valid_loads': []
            }
        }
        
        # If there's a unit, calculate valid actions
        if tile.unit and not tile.unit.done:
            current_player_color = game.players[game.current_player_id].color.value.upper()
            if tile.unit.army.name == current_player_color:
                unit_info = self._get_unit_info(tile.unit)
                response['selection']['unit'] = unit_info
                
                # Calculate available actions
                actions = []
                if not tile.unit.has_moved:
                    actions.append('move')
                    actions.append('delete')
                    
                    # Get valid moves
                    valid_moves = manager.get_valid_moves(x, y)
                    response['selection']['valid_moves'] = [
                        {
                            'x': vx,
                            'y': vy,
                            'terrain': manager.tile_at(vx, vy).mapTile.type.name.lower(),
                            'fuel_cost': 1  # TODO: Calculate actual cost
                        }
                        for vx, vy in valid_moves
                    ]
                    
                # Check for attacks
                if self._can_attack_from(manager, x, y):
                    actions.append('attack')
                    response['selection']['valid_attacks'] = self._get_attack_targets(manager, x, y, game)
                    
                # Check for transport loading
                if self._can_load_from(manager, x, y):
                    actions.append('load')
                    response['selection']['valid_loads'] = self._get_load_targets(manager, x, y, game)
                    
                actions.append('wait')
                response['selection']['available_actions'] = actions
                
        return response
        
    def move_unit(self, game_id: str, from_x: int, from_y: int, 
                  to_x: int, to_y: int) -> Dict[str, Any]:
        """Move a unit and return new valid actions"""
        game = games.get(game_id)
        manager = game_managers.get(game_id)
        
        if not game or not manager:
            raise ValueError(f"Game {game_id} not found")
            
        # Execute move
        result = manager.unit_move(from_x, from_y, to_x, to_y)
        
        # Check if auto-loaded into transport
        auto_loaded = False
        to_tile = manager.tile_at(to_x, to_y)
        if to_tile and not to_tile.unit:
            # Unit disappeared = was loaded
            auto_loaded = True
            game.active_unit_pos = None
        else:
            # Set as active unit
            game.active_unit_pos = (to_x, to_y)
            
        # Build response with new valid actions
        response = {
            'success': True,
            'movement': {
                'from': {'x': from_x, 'y': from_y},
                'to': {'x': to_x, 'y': to_y},
                'fuel_used': 1,  # TODO: Calculate actual
                'auto_loaded': auto_loaded
            }
        }
        
        # If not auto-loaded, get actions from new position
        if not auto_loaded and to_tile and to_tile.unit:
            actions = []
            
            # Check attacks from new position
            if self._can_attack_from(manager, to_x, to_y):
                actions.append('attack')
                
            # Check capture
            if to_tile.mapTile and to_tile.mapTile.army != to_tile.unit.army:
                if to_tile.mapTile.type in [MapType.CITY, MapType.FACTORY, 
                                           MapType.AIRPORT, MapType.PORT, 
                                           MapType.BASE_TOWER_0, MapType.BASE_TOWER_1,
                                           MapType.BASE_TOWER_2, MapType.BASE_TOWER_3,
                                           MapType.BASE_TOWER_4]:
                    actions.append('capture')
                    
            # Check loading
            if self._can_load_from(manager, to_x, to_y):
                actions.append('load')
                
            actions.append('wait')
            
            response['active_unit'] = {
                'position': {'x': to_x, 'y': to_y},
                'fuel_remaining': to_tile.unit.fuel,
                'available_actions': actions,
                'valid_attacks': self._get_attack_targets(manager, to_x, to_y, game) if 'attack' in actions else [],
                'valid_loads': self._get_load_targets(manager, to_x, to_y, game) if 'load' in actions else []
            }
            
        return response
        
    def attack(self, game_id: str, target_x: int, target_y: int) -> Dict[str, Any]:
        """Execute attack from active unit"""
        game = games.get(game_id)
        manager = game_managers.get(game_id)
        
        if not game or not manager:
            raise ValueError(f"Game {game_id} not found")
            
        if not game.active_unit_pos:
            raise ValueError("No active unit to attack with")
            
        ax, ay = game.active_unit_pos
        
        # Execute attack
        combat_result = manager.unit_attack_enhanced(ax, ay, target_x, target_y)
        
        # Clear active unit (attack ends turn)
        game.active_unit_pos = None
        
        # Build response
        attacker_tile = manager.tile_at(ax, ay)
        defender_tile = manager.tile_at(target_x, target_y)
        
        return {
            'success': True,
            'combat': {
                'attacker': {
                    'position': {'x': ax, 'y': ay},
                    'type': attacker_tile.unit.type.name.lower() if attacker_tile.unit else None,
                    'damage_dealt': combat_result.get('damage_dealt', 0),
                    'hp_before': combat_result.get('attacker_hp_before', 100),
                    'hp_after': attacker_tile.unit.hp if attacker_tile.unit else 0,
                    'ammo_remaining': attacker_tile.unit.ammo if attacker_tile.unit else 0
                },
                'defender': {
                    'position': {'x': target_x, 'y': target_y},
                    'type': combat_result.get('defender_type', '').lower(),
                    'damage_taken': combat_result.get('damage_dealt', 0),
                    'hp_before': combat_result.get('defender_hp_before', 100),
                    'hp_after': defender_tile.unit.hp if defender_tile.unit else 0,
                    'counter_damage': combat_result.get('counter_damage', 0),
                    'destroyed': defender_tile.unit is None
                }
            },
            'turn_ended': True
        }
        
    def unit_action(self, game_id: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute various unit actions"""
        game = games.get(game_id)
        manager = game_managers.get(game_id)
        
        if not game or not manager:
            raise ValueError(f"Game {game_id} not found")
            
        result = {'success': True, 'action': action}
        
        if action == 'wait':
            # End unit's turn
            if game.active_unit_pos:
                x, y = game.active_unit_pos
                tile = manager.tile_at(x, y)
                if tile and tile.unit:
                    tile.unit.done = True
                game.active_unit_pos = None
            result['turn_ended'] = True
            
        elif action == 'delete':
            # Delete selected unit
            if game.selected_pos:
                x, y = game.selected_pos
                manager.unit_delete(x, y)
                result['deleted'] = True
                
        elif action == 'capture':
            # Capture building
            if game.active_unit_pos:
                x, y = game.active_unit_pos
                tile = manager.tile_at(x, y)
                if tile and tile.unit and tile.mapTile:
                    # Reduce capture HP
                    capture_power = min(tile.unit.hp // 10, tile.capture_hp)
                    tile.capture_hp -= capture_power
                    
                    if tile.capture_hp <= 0:
                        # Captured!
                        tile.mapTile.army = tile.unit.army
                        tile.capture_hp = 20
                        result['capture_complete'] = True
                    else:
                        result['capture_progress'] = capture_power
                        result['capture_remaining'] = tile.capture_hp
                        
                    tile.unit.done = True
                    game.active_unit_pos = None
                    
        elif action == 'load':
            # Load into transport
            transport_x = params['transport_x']
            transport_y = params['transport_y']
            
            if game.active_unit_pos:
                ux, uy = game.active_unit_pos
                manager.load_unit(ux, uy, transport_x, transport_y)
                game.active_unit_pos = None
                result['loaded'] = True
                
        # TODO: Implement unload, repair, resupply, join
        
        return result
        
    def create_unit(self, game_id: str, facility_x: int, facility_y: int, 
                    unit_type: str) -> Dict[str, Any]:
        """Create a new unit at production facility"""
        game = games.get(game_id)
        manager = game_managers.get(game_id)
        
        if not game or not manager:
            raise ValueError(f"Game {game_id} not found")
            
        # Get current player's color for legacy system
        player = game.players[game.current_player_id]
        army_name = player.color.value.upper()
        
        # Create unit
        unit_id = str(uuid.uuid4())[:8]
        manager.unit_create(facility_x, facility_y, unit_type.upper(), army_name)
        
        # Get created unit
        tile = manager.tile_at(facility_x, facility_y)
        unit = tile.unit if tile else None
        
        if not unit:
            raise ValueError("Failed to create unit")
            
        # Deduct cost
        # TODO: Get actual unit cost
        unit_cost = 7000 if unit_type == 'tank' else 1000
        
        return {
            'success': True,
            'unit_created': {
                'id': unit_id,
                'type': unit_type,
                'position': {'x': facility_x, 'y': facility_y},
                'owner': game.current_player_id,
                'cost': unit_cost,
                'stats': {
                    'hp': 100,
                    'fuel': unit.fuel,
                    'ammo': unit.ammo,
                    'movement': unit.move
                }
            },
            'player_funds_remaining': self._get_player_funds(manager, army_name) - unit_cost,
            'can_act_this_turn': False
        }
        
    def end_turn(self, game_id: str) -> Dict[str, Any]:
        """End current player's turn"""
        game = games.get(game_id)
        manager = game_managers.get(game_id)
        
        if not game or not manager:
            raise ValueError(f"Game {game_id} not found")
            
        # Commit any active unit
        if game.active_unit_pos:
            x, y = game.active_unit_pos
            tile = manager.tile_at(x, y)
            if tile and tile.unit:
                tile.unit.done = True
            game.active_unit_pos = None
            
        # End turn in manager
        old_player = game.current_player_id
        manager.end_turn()
        
        # Update current player
        current_idx = game.turn_order.index(game.current_player_id)
        next_idx = (current_idx + 1) % len(game.turn_order)
        game.current_player_id = game.turn_order[next_idx]
        
        # Check for game end
        winner = manager.check_win_condition()
        if winner:
            game.phase = 'game_over'
            # Find player with matching color
            for pid, player in game.players.items():
                if player.color.value.upper() == winner.name:
                    game.winner_id = pid
                    break
                    
        return {
            'success': True,
            'turn_summary': {
                'player_ended': old_player,
                'units_moved': 0,  # TODO: Track this
                'units_created': 0,  # TODO: Track this
                'income_gained': 0  # TODO: Calculate
            },
            'new_turn': {
                'player': game.current_player_id,
                'day': manager.board.days,
                'funds': self._get_player_funds(manager, 
                         game.players[game.current_player_id].color.value.upper())
            },
            'game_over': game.phase == 'game_over',
            'winner': game.winner_id
        }
        
    def get_production_options(self, game_id: str, x: int, y: int) -> Dict[str, Any]:
        """Get available units for production at facility"""
        game = games.get(game_id)
        manager = game_managers.get(game_id)
        
        if not game or not manager:
            raise ValueError(f"Game {game_id} not found")
            
        tile = manager.tile_at(x, y)
        if not tile or not tile.mapTile:
            raise ValueError(f"No facility at ({x}, {y})")
            
        # Get facility type and available units
        facility_type = tile.mapTile.type.name.lower()
        player_funds = self._get_player_funds(manager, 
                       game.players[game.current_player_id].color.value.upper())
        
        # Define unit costs (TODO: Move to config)
        unit_costs = {
            'infantry': 1000,
            'mech': 3000,
            'recon': 4000,
            'tank': 7000,
            'md_tank': 16000,
            'neotank': 22000,
            'megatank': 28000,
            'apc': 5000,
            'artillery': 6000,
            'rocket': 15000,
            'aa': 8000,
            'missile': 12000
        }
        
        # Get units for this facility type
        if facility_type == 'factory':
            available_types = ['infantry', 'mech', 'recon', 'tank', 'md_tank', 
                             'neotank', 'megatank', 'apc', 'artillery', 
                             'rocket', 'aa', 'missile']
        elif facility_type == 'airport':
            available_types = ['fighter', 'bomber', 'bcopter', 'tcopter', 'stealth']
        elif facility_type == 'port':
            available_types = ['battleship', 'cruiser', 'lander', 'sub', 'carrier', 'black_boat']
        else:
            available_types = []
            
        # Build options
        options = []
        for unit_type in available_types:
            cost = unit_costs.get(unit_type, 10000)  # Default cost
            options.append({
                'type': unit_type,
                'cost': cost,
                'can_afford': player_funds >= cost
            })
            
        return {
            'facility': {
                'type': facility_type,
                'position': {'x': x, 'y': y}
            },
            'owner_funds': player_funds,
            'available_units': options
        }
        
    # ========== HELPER METHODS ==========
    
    def _create_board(self, map_name: str, players: Dict[str, Player]) -> GameBoard:
        """Create game board with player colors"""
        # Create a simple test map
        # TODO: Load actual maps
        tiles = []
        width = 12
        height = 10
        
        # Add terrain tiles
        for y in range(height):
            for x in range(width):
                tiles.append(MapTile(MapType.PLAIN))
                
        # Create turn order from players
        turn_order = []
        player_list = list(players.values())
        for player in player_list:
            turn_order.append(self._color_to_army(player.color))
                
        # Create map
        test_map = Map(
            name=map_name,
            width=width,
            height=height,
            tiles=tiles,
            turn_order=turn_order
        )
        
        # Add player HQs
        if len(players) >= 2:
            # Player 1 HQ at (1,1)
            test_map.tiles[1 * width + 1] = MapTile(MapType.BASE_TOWER_0, 
                                                    self._color_to_army(player_list[0].color))
            # Player 2 HQ at (10,8)
            test_map.tiles[8 * width + 10] = MapTile(MapType.BASE_TOWER_0,
                                                     self._color_to_army(player_list[1].color))
                             
        return GameBoard.create(test_map)
        
    def _color_to_army(self, color: SpriteColor):
        """Convert SpriteColor to legacy Army enum"""
        # Temporary hack to work with legacy system
        from map_system import Army
        color_map = {
            SpriteColor.RED: Army.RED,
            SpriteColor.BLUE: Army.BLUE,
            SpriteColor.GREEN: Army.GREEN,
            SpriteColor.YELLOW: Army.YELLOW,
            SpriteColor.GREY: Army.GREY
        }
        return color_map.get(color, Army.RED)
        
    def _build_tile_data(self, manager: GameManager, x: int, y: int, 
                        game: GameStateV2) -> Dict[str, Any]:
        """Build tile data for API response"""
        tile = manager.tile_at(x, y)
        if not tile:
            return None
            
        data = {
            'x': x,
            'y': y,
            'terrain': self._get_terrain_info(tile),
            'building': None,
            'unit': None
        }
        
        if tile.mapTile:
            building_info = self._get_building_info(tile)
            if building_info:
                data['building'] = building_info
                # Map army to player ID for buildings
                if tile.mapTile.army:
                    for pid, player in game.players.items():
                        if player.color.value.upper() == tile.mapTile.army.name:
                            data['building']['owner'] = pid
                            break
            
        if tile.unit:
            data['unit'] = self._get_unit_info(tile.unit)
            # Map army color to player ID
            for pid, player in game.players.items():
                if player.color.value.upper() == tile.unit.army.name:
                    data['unit']['owner'] = pid
                    break
                    
        return data
        
    def _get_terrain_info(self, tile) -> Dict[str, Any]:
        """Get terrain information from tile"""
        if not tile.mapTile:
            return {'type': 'plain', 'defense': 0}
            
        # Map legacy terrain types
        terrain_map = {
            'PLAIN': 'plain',
            'ROAD': 'road', 
            'WOOD': 'wood',
            'MOUNTAIN': 'mountain',
            'RIVER': 'river',
            'SEA': 'sea',
            'BEACH': 'beach',
            'REEF': 'reef'
        }
        
        terrain_type = terrain_map.get(tile.mapTile.type.name, 'plain')
        
        # Get defense value
        defense_values = {
            'plain': 1,
            'road': 0,
            'wood': 2,
            'mountain': 4,
            'city': 3,
            'factory': 3,
            'airport': 3,
            'port': 3,
            'hq': 4
        }
        
        return {
            'type': terrain_type,
            'defense': defense_values.get(terrain_type, 0)
        }
        
    def _get_building_info(self, tile) -> Optional[Dict[str, Any]]:
        """Get building information from tile"""
        if not tile.mapTile:
            return None
            
        building_types = ['CITY', 'FACTORY', 'AIRPORT', 'PORT', 'COM_TOWER', 'LAB',
                         'BASE_TOWER_0', 'BASE_TOWER_1', 'BASE_TOWER_2', 'BASE_TOWER_3', 'BASE_TOWER_4']
        if tile.mapTile.type.name not in building_types:
            return None
            
        # Map BASE_TOWER_X to HQ
        building_type = tile.mapTile.type.name.lower()
        if building_type.startswith('base_tower_'):
            building_type = 'hq'
            
        return {
            'type': building_type,
            'owner': None,  # Will be set by caller
            'capture_hp': tile.capture_hp
        }
        
    def _get_unit_info(self, unit) -> Dict[str, Any]:
        """Get unit information"""
        return {
            'type': unit.type.name.lower(),
            'owner': None,  # Will be set by caller
            'hp': unit.hp,
            'fuel': unit.fuel,
            'ammo': unit.ammo,
            'has_moved': unit.has_moved,
            'has_acted': unit.done
        }
        
    def _get_player_funds(self, manager: GameManager, army_name: str) -> int:
        """Get funds for player by army color"""
        # Map army names to fund attributes
        fund_map = {
            'RED': manager.board.red_funds,
            'BLUE': manager.board.blue_funds,
            'GREEN': 5000,  # TODO: Add to board
            'YELLOW': 5000,  # TODO: Add to board
            'GREY': 5000  # TODO: Add to board
        }
        return fund_map.get(army_name, 0)
        
    def _can_attack_from(self, manager: GameManager, x: int, y: int) -> bool:
        """Check if unit at position can attack anything"""
        tile = manager.tile_at(x, y)
        if not tile or not tile.unit:
            return False
            
        # Check surrounding tiles for enemies
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                tx, ty = x + dx, y + dy
                target = manager.tile_at(tx, ty)
                if target and target.unit and target.unit.army != tile.unit.army:
                    return True
        return False
        
    def _get_attack_targets(self, manager: GameManager, x: int, y: int, 
                           game: GameStateV2) -> List[Dict[str, Any]]:
        """Get all valid attack targets from position"""
        tile = manager.tile_at(x, y)
        if not tile or not tile.unit:
            return []
            
        targets = []
        # Check weapon range (simplified - just adjacent for now)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                tx, ty = x + dx, y + dy
                target = manager.tile_at(tx, ty)
                if target and target.unit and target.unit.army != tile.unit.army:
                    # Find owner player ID
                    owner_id = None
                    for pid, player in game.players.items():
                        if player.color.value.upper() == target.unit.army.name:
                            owner_id = pid
                            break
                            
                    targets.append({
                        'x': tx,
                        'y': ty,
                        'unit': {
                            'type': target.unit.type.name.lower(),
                            'owner': owner_id,
                            'hp': target.unit.hp
                        },
                        'damage_preview': 55  # TODO: Calculate actual damage
                    })
        return targets
        
    def _can_load_from(self, manager: GameManager, x: int, y: int) -> bool:
        """Check if unit can load into any adjacent transport"""
        tile = manager.tile_at(x, y)
        if not tile or not tile.unit:
            return False
            
        # Check if unit is loadable type
        if tile.unit.type.name not in ['INFANTRY', 'MECH']:
            return False
            
        # Check adjacent tiles for transports
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                tx, ty = x + dx, y + dy
                transport = manager.tile_at(tx, ty)
                if (transport and transport.unit and 
                    transport.unit.army == tile.unit.army and
                    transport.unit.type.name in ['APC', 'TCOPTER', 'LANDER', 'BLACK_BOAT']):
                    # TODO: Check if transport has space
                    return True
        return False
        
    def _get_load_targets(self, manager: GameManager, x: int, y: int,
                         game: GameStateV2) -> List[Dict[str, Any]]:
        """Get all valid transports to load into"""
        tile = manager.tile_at(x, y)
        if not tile or not tile.unit:
            return []
            
        targets = []
        # Check adjacent tiles
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                tx, ty = x + dx, y + dy
                transport = manager.tile_at(tx, ty)
                if (transport and transport.unit and 
                    transport.unit.army == tile.unit.army and
                    transport.unit.type.name in ['APC', 'TCOPTER', 'LANDER', 'BLACK_BOAT']):
                    
                    # Find owner player ID
                    owner_id = None
                    for pid, player in game.players.items():
                        if player.color.value.upper() == transport.unit.army.name:
                            owner_id = pid
                            break
                            
                    targets.append({
                        'x': tx,
                        'y': ty,
                        'transport': {
                            'type': transport.unit.type.name.lower(),
                            'owner': owner_id,
                            'cargo_space': 1  # TODO: Calculate actual space
                        }
                    })
        return targets
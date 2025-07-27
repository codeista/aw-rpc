"""
Manager V2 - Color-agnostic game manager
"""
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import math

from map_system import Army, MapType
from gameboard import GameTile
from unit import UnitType, Unit
from game_board_v2 import GameBoardV2
from player_system import PlayerManager
from transport_system import CompleteTransportSystem
from production_system import ProductionSystem
from manager import GameManager
from config import Config
import configparser

class GameManagerV2(GameManager):
    """Game manager that uses the new player system"""
    
    def __init__(self, config, board: GameBoardV2, player_manager: PlayerManager):
        """Initialize with player-aware board"""
        # Store V2 board
        self.board_v2 = board
        self.player_manager = player_manager
        
        # Initialize board with player manager
        board.initialize_from_player_manager(player_manager)
        
        # Call parent constructor with the board
        super().__init__(config, board)
        
    def setup_initial_economy(self) -> None:
        """Setup initial funds for all players based on starting properties"""
        # Load config
        config = configparser.ConfigParser()
        config.read('config.ini')
        income = int(config['FUNDS']['income'])
        production_system = ProductionSystem(self)
        
        # Count production buildings for each player
        for player_id in range(self.player_manager.get_player_count()):
            initial_income = 0
            
            # Count properties owned by this player
            for y in range(self.board.height):
                for x in range(self.board.width):
                    tile = self.board.grid[y * self.board.width + x]
                    if tile.mapTile and tile.mapTile.type in {MapType.CITY, MapType.FACTORY, MapType.AIRPORT, MapType.PORT}:
                        # Check ownership by player ID
                        tile_player = self._get_tile_player(tile)
                        if tile_player == player_id:
                            initial_income += income
                            
            # Set starting funds
            starting_funds = max(10000, initial_income * 3)
            self.board_v2.player_funds[player_id] = starting_funds
            
            # Update army funds for backward compatibility
            army = self.board_v2.get_army_for_player(player_id)
            if army:
                self.board_v2.army_funds[army] = starting_funds
                
    def _update_property_ownership(self, tile: GameTile, new_army: Army) -> None:
        """Update property ownership and adjust player statistics."""
        old_army = tile.mapTile.army
        
        # Call parent method to handle COM_TOWER modifiers and other logic
        super()._update_property_ownership(tile, new_army)
        
        # Convert armies to player IDs for v2-specific updates
        old_player = self.board_v2.get_player_for_army(old_army) if old_army else None
        new_player = self.board_v2.get_player_for_army(new_army) if new_army else None
        
        # Update player property counts
        if old_player is not None:
            self.board_v2.update_player_properties(old_player, -1)
            
        if new_player is not None:
            self.board_v2.update_player_properties(new_player, 1)
            
    def _update_army_funds(self, army: Army, amount: int) -> None:
        """Update funds for an army/player."""
        player_id = self.board_v2.get_player_for_army(army)
        if player_id is not None:
            self.board_v2.update_player_funds(player_id, amount)
        else:
            # Fallback for armies not mapped to players
            if hasattr(self.board, 'army_funds') and army in self.board.army_funds:
                self.board.army_funds[army] += amount
                
    def _get_army_funds(self, army: Army) -> int:
        """Get current funds for an army/player."""
        player_id = self.board_v2.get_player_for_army(army)
        if player_id is not None:
            return self.board_v2.player_funds.get(player_id, 0)
        else:
            # Fallback for armies not mapped to players
            if hasattr(self.board, 'army_funds') and army in self.board.army_funds:
                return self.board.army_funds.get(army, 0)
            return 0
            
    def unit_create(self, army: str, unit_type: str, x: int, y: int) -> Unit:
        """Create a new unit at the specified coordinates."""
        # Call parent implementation (which already updates troop counts via setters)
        unit = super().unit_create(army, unit_type, x, y)
        
        # No need to update player troops here - the parent already updated total_red_troops/total_blue_troops
        # which triggers our setters and updates player_troops
        
        return unit
        
    def _update_army_statistics(self) -> None:
        """Update all player statistics in a single pass."""
        # Reset all player counters
        for player_id in range(self.player_manager.get_player_count()):
            self.board_v2.player_troops[player_id] = 0
            self.board_v2.player_properties[player_id] = 0
            
        # Also reset army counters for backward compatibility
        for army in self.board.turn_order:
            self.board.army_troops[army] = 0
            self.board.army_properties[army] = 0
            
        # Count units and properties in single pass
        for y in range(self.board.height):
            for x in range(self.board.width):
                tile = self.board.grid[y * self.board.width + x]
                
                # Count units
                if tile.unit:
                    player_id = self._get_unit_player(tile.unit)
                    if player_id is not None:
                        self.board_v2.player_troops[player_id] += 1
                        
                    # Also update army troops for compatibility
                    if tile.unit.army in self.board.army_troops:
                        self.board.army_troops[tile.unit.army] += 1
                        
                # Count properties
                if tile.mapTile and tile.mapTile.type in {MapType.CITY, MapType.FACTORY, MapType.AIRPORT, MapType.PORT}:
                    player_id = self._get_tile_player(tile)
                    if player_id is not None:
                        self.board_v2.player_properties[player_id] += 1
                        
                    # Also update army properties for compatibility
                    if tile.mapTile.army and tile.mapTile.army in self.board.army_properties:
                        self.board.army_properties[tile.mapTile.army] += 1
                        
    def _get_unit_player(self, unit: Unit) -> Optional[int]:
        """Get player ID for a unit"""
        return self.board_v2.get_player_for_army(unit.army)
        
    def _get_tile_player(self, tile: GameTile) -> Optional[int]:
        """Get player ID for a tile"""
        if tile.mapTile and tile.mapTile.army:
            return self.board_v2.get_player_for_army(tile.mapTile.army)
        return None
        
    def _advance_to_next_army(self) -> None:
        """Advance to the next player's turn."""
        # Use player-based turn order
        self.board_v2.current_player = self.board_v2.get_next_player()
        
        # Update current_turn for backward compatibility
        new_army = self.board_v2.get_army_for_player(self.board_v2.current_player)
        if new_army:
            self.board.current_turn = new_army
            
        # Check if we've completed a round
        if self.board_v2.current_player == 0:
            self.board.days += 1
            
    def get_current_player_info(self) -> Dict:
        """Get information about the current player"""
        player_id = self.board_v2.current_player
        player = self.player_manager.get_player(player_id)
        
        if player:
            return {
                'id': player.id,
                'name': player.name,
                'color': player.color,
                'sprite_color': player.sprite_color.value,
                'funds': self.board_v2.player_funds.get(player_id, 0),
                'properties': self.board_v2.player_properties.get(player_id, 0),
                'troops': self.board_v2.player_troops.get(player_id, 0)
            }
        return {}
        
    def to_dict(self) -> Dict:
        """Convert game state to dictionary with player information"""
        # Get board state
        state = self.board.to_dict()
        
        # Add player information
        player_data = self.player_manager.to_dict()
        state['players'] = player_data['players']
        state['sprite_mapping'] = player_data['sprite_mapping']
        state['player_funds'] = self.board_v2.player_funds
        state['player_properties'] = self.board_v2.player_properties
        state['player_troops'] = self.board_v2.player_troops
        state['current_player'] = self.board_v2.current_player
        
        return state
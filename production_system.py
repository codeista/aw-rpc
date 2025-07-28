# production_system.py - Complete Unit Production System

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import configparser

# Import your existing types
try:
    from unit import UnitType, Unit, UnitConfig
    from map_system import Army, MapType
    from gameboard import GameTile
except ImportError:
    # Fallback for type hints
    pass

# Load unit costs from config
config = configparser.ConfigParser()
config.read('config.ini')

@dataclass
class ProductionResult:
    """Result of a unit production attempt"""
    success: bool
    unit: Optional['Unit'] = None
    cost: int = 0
    remaining_funds: int = 0
    error_message: str = ""

class ProductionSystem:
    """Complete unit production and economic system"""
    
    # Unit costs (from config.ini)
    UNIT_COSTS = {
        UnitType.INFANTRY: 1000,
        UnitType.MECH: 3000,
        UnitType.RECON: 4000,
        UnitType.TANK: 7000,
        UnitType.MEDIUMTANK: 16000,
        UnitType.NEOTANK: 22000,
        UnitType.MEGATANK: 28000,
        UnitType.APC: 5000,
        UnitType.ARTILLERY: 6000,
        UnitType.ROCKET: 15000,
        UnitType.ANTIAIR: 8000,
        UnitType.MISSILE: 12000,
        UnitType.FIGHTER: 20000,
        UnitType.BOMBER: 22000,
        UnitType.STEALTH: 24000,
        UnitType.BCOPTER: 9000,
        UnitType.TCOPTER: 5000,
        UnitType.BATTLESHIP: 28000,
        UnitType.CRUISER: 18000,
        UnitType.LANDER: 12000,
        UnitType.SUB: 20000,
        UnitType.CARRIER: 30000,
        UnitType.BLACKBOAT: 7500,
        UnitType.PIPERUNNER: 20000,
        UnitType.BLACKBOMB: 25000
    }
    
    # Production facilities and what they can build
    PRODUCTION_FACILITIES = {
        MapType.FACTORY: [
            UnitType.INFANTRY, UnitType.MECH, UnitType.RECON, UnitType.TANK,
            UnitType.MEDIUMTANK, UnitType.NEOTANK, UnitType.MEGATANK,
            UnitType.APC, UnitType.ARTILLERY, UnitType.ROCKET, UnitType.ANTIAIR,
            UnitType.MISSILE
        ],
        MapType.AIRPORT: [
            UnitType.FIGHTER, UnitType.BOMBER, UnitType.STEALTH,
            UnitType.BCOPTER, UnitType.TCOPTER, UnitType.BLACKBOMB
        ],
        MapType.PORT: [
            UnitType.BATTLESHIP, UnitType.CRUISER, UnitType.LANDER,
            UnitType.SUB, UnitType.CARRIER, UnitType.BLACKBOAT
        ]
    }
    
    # Income per property type per turn (Advance Wars standard)
    PROPERTY_INCOME = {
        MapType.CITY: 1000,          # Cities provide 1000 funds
        MapType.BASE_TOWER_1: 1000,  # HQ provides 1000 funds
        MapType.BASE_TOWER_2: 1000,  # Additional HQ types
        MapType.BASE_TOWER_3: 1000,
        MapType.BASE_TOWER_4: 1000,
        MapType.FACTORY: 1000,       # Production facilities provide 1000 funds
        MapType.AIRPORT: 1000,
        MapType.PORT: 1000,
        MapType.COM_TOWER: 1000,     # Communication towers provide 1000 funds
        MapType.LAB: 1000,           # Labs provide 1000 funds
    }
    
    def __init__(self, game_manager):
        self.manager = game_manager
        # Load unit costs from config if available
        self._load_costs_from_config()
    
    def _load_costs_from_config(self):
        """Load unit costs from config.ini if available"""
        try:
            for unit_type in UnitType:
                unit_name = unit_type.name
                if unit_name in config:
                    cost = config.getint(unit_name, 'cost', fallback=self.UNIT_COSTS.get(unit_type, 1000))
                    self.UNIT_COSTS[unit_type] = cost
        except Exception:
            pass  # Use default costs if config loading fails
    
    def can_produce_unit(self, facility_x: int, facility_y: int, 
                        unit_type: UnitType, army: Army) -> Tuple[bool, str]:
        """Check if a unit can be produced at this facility"""
        
        # Get facility tile
        facility_tile = self.manager.tile_at(facility_x, facility_y)
        if not facility_tile:
            return False, "Invalid facility coordinates"
        
        # Check if tile is a production facility
        facility_type = facility_tile.mapTile.type
        if facility_type not in self.PRODUCTION_FACILITIES:
            return False, f"{facility_type.name} is not a production facility"
        
        # Check if facility belongs to the army
        if facility_tile.mapTile.army != army:
            return False, f"Facility belongs to {facility_tile.mapTile.army.name if facility_tile.mapTile.army else 'neutral'}"
        
        # Check if facility is occupied
        if facility_tile.unit:
            return False, "Facility is occupied by another unit"
        
        # Check if this facility type can produce this unit type
        if unit_type not in self.PRODUCTION_FACILITIES[facility_type]:
            return False, f"{facility_type.name} cannot produce {unit_type.name}"
        
        # Check if army has enough funds
        current_funds = self.manager._get_army_funds(army)
        unit_cost = self.UNIT_COSTS.get(unit_type, 1000)
        if current_funds < unit_cost:
            return False, f"Insufficient funds: need {unit_cost}, have {current_funds}"
        
        return True, "Can produce unit"
    
    def produce_unit(self, facility_x: int, facility_y: int, 
                    unit_type: UnitType, army: Army) -> ProductionResult:
        """Produce a unit at the specified facility"""
        
        # Validate production
        can_produce, error_msg = self.can_produce_unit(facility_x, facility_y, unit_type, army)
        if not can_produce:
            return ProductionResult(
                success=False,
                error_message=error_msg,
                remaining_funds=self.manager._get_army_funds(army)
            )
        
        # Get unit cost
        unit_cost = self.UNIT_COSTS.get(unit_type, 1000)
        current_funds = self.manager._get_army_funds(army)
        
        # Create the unit
        try:
            # unit_create expects strings, not enums
            unit = self.manager.unit_create(army.name, unit_type.name, facility_x, facility_y)
            
            # Deduct cost from army funds
            self.manager._update_army_funds(army, -unit_cost)
            new_funds = current_funds - unit_cost
            
            return ProductionResult(
                success=True,
                unit=unit,
                cost=unit_cost,
                remaining_funds=new_funds
            )
            
        except Exception as e:
            return ProductionResult(
                success=False,
                error_message=f"Failed to create unit: {str(e)}",
                remaining_funds=current_funds
            )
    
    def get_producible_units(self, facility_x: int, facility_y: int, 
                           army: Army) -> Dict:
        """Get list of units that can be produced at this facility"""
        
        facility_tile = self.manager.tile_at(facility_x, facility_y)
        if not facility_tile:
            return {"error": "Invalid facility coordinates"}
        
        facility_type = facility_tile.mapTile.type
        if facility_type not in self.PRODUCTION_FACILITIES:
            return {"error": f"{facility_type.name} is not a production facility"}
        
        if facility_tile.mapTile.army != army:
            return {"error": "Facility not owned by army"}
        
        current_funds = self.manager._get_army_funds(army)
        available_units = []
        
        for unit_type in self.PRODUCTION_FACILITIES[facility_type]:
            cost = self.UNIT_COSTS.get(unit_type, 1000)
            can_afford = current_funds >= cost
            
            available_units.append({
                "type": unit_type.name,  # Changed from "unit_type" to "type" to match test expectations
                "cost": cost,
                "can_afford": can_afford
            })
        
        return {
            "facility_type": facility_type.name,
            "current_funds": current_funds,
            "units": available_units,  # Changed from "available_units" to "units" to match test expectations
            "is_occupied": facility_tile.unit is not None  # Include occupation status
        }
    
    def calculate_daily_income(self, army: Army) -> int:
        """Calculate total daily income for an army"""
        total_income = 0
        
        for tile in self.manager.board.grid:
            if tile.mapTile.army == army:
                income = self.PROPERTY_INCOME.get(tile.mapTile.type, 0)
                total_income += income
        
        return total_income
    
    def get_economic_summary(self, army: Army) -> Dict:
        """Get complete economic summary for an army"""
        current_funds = self.manager._get_army_funds(army)
        daily_income = self.calculate_daily_income(army)
        
        # Count properties by type
        properties = {}
        for tile in self.manager.board.grid:
            if tile.mapTile.army == army:
                prop_type = tile.mapTile.type.name
                properties[prop_type] = properties.get(prop_type, 0) + 1
        
        # Count units by type
        units = {}
        total_unit_value = 0
        for tile in self.manager.board.grid:
            if tile.unit and tile.unit.army == army:
                unit_type = tile.unit.type.name
                units[unit_type] = units.get(unit_type, 0) + 1
                total_unit_value += self.UNIT_COSTS.get(tile.unit.type, 1000)
        
        return {
            "army": army.name,
            "current_funds": current_funds,
            "daily_income": daily_income,
            "properties": properties,
            "units": units,
            "total_unit_value": total_unit_value,
            "net_worth": current_funds + total_unit_value
        }
    
    def get_all_production_facilities(self, army: Army) -> List[Dict]:
        """Get all production facilities owned by an army"""
        facilities = []
        
        for tile in self.manager.board.grid:
            if (tile.mapTile.army == army and 
                tile.mapTile.type in self.PRODUCTION_FACILITIES):
                
                facilities.append({
                    "position": {"x": tile.x, "y": tile.y},
                    "type": tile.mapTile.type.name,
                    "occupied": tile.unit is not None,
                    "occupant": tile.unit.type.name if tile.unit else None
                })
        
        return facilities
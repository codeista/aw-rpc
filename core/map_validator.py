"""
Map Validator - Ensures maps are balanced and well-designed
"""
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from map_parser_v2 import MapParserV2
from map_system import MapType
import math


@dataclass
class ValidationResult:
    """Results from map validation"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    stats: Dict
    
    def __str__(self):
        output = []
        if self.valid:
            output.append("✅ Map is valid!")
        else:
            output.append("❌ Map has errors!")
            
        if self.errors:
            output.append("\nErrors:")
            for error in self.errors:
                output.append(f"  ❌ {error}")
                
        if self.warnings:
            output.append("\nWarnings:")
            for warning in self.warnings:
                output.append(f"  ⚠️  {warning}")
                
        output.append("\nMap Statistics:")
        for key, value in self.stats.items():
            output.append(f"  {key}: {value}")
            
        return "\n".join(output)


class MapValidator:
    """Validates Advance Wars maps for balance and playability"""
    
    # Property types that generate income
    INCOME_PROPERTIES = {
        MapType.CITY, MapType.FACTORY, MapType.AIRPORT, 
        MapType.PORT, MapType.COM_TOWER
    }
    
    # Production facilities
    PRODUCTION_FACILITIES = {
        MapType.FACTORY, MapType.AIRPORT, MapType.PORT
    }
    
    # HQ tile types
    HQ_TYPES = {
        MapType.BASE_TOWER_0, MapType.BASE_TOWER_1,
        MapType.BASE_TOWER_2, MapType.BASE_TOWER_3,
        MapType.BASE_TOWER_4
    }
    
    def __init__(self):
        self.parser = MapParserV2()
        
    def validate_file(self, filepath: str) -> ValidationResult:
        """Validate a map file"""
        try:
            player_manager, tiles = self.parser.parse_file(filepath)
            return self.validate_map(tiles, self.parser.width, self.parser.height, 
                                    player_manager.get_player_count())
        except Exception as e:
            return ValidationResult(
                valid=False,
                errors=[f"Failed to parse map: {str(e)}"],
                warnings=[],
                stats={}
            )
            
    def validate_map(self, tiles: List[List[Tuple]], width: int, height: int, 
                    num_players: int) -> ValidationResult:
        """Validate a parsed map"""
        errors = []
        warnings = []
        stats = {
            "width": width,
            "height": height,
            "players": num_players,
            "total_tiles": width * height
        }
        
        # Track player resources
        player_properties = {i: 0 for i in range(num_players)}
        player_income = {i: 0 for i in range(num_players)}
        player_production = {i: {"FACTORY": 0, "AIRPORT": 0, "PORT": 0} for i in range(num_players)}
        player_hqs = {i: [] for i in range(num_players)}
        
        # Track neutral properties
        neutral_properties = 0
        com_towers = []
        
        # Analyze map
        for y in range(height):
            for x in range(width):
                tile_type, owner = tiles[y][x]
                
                # Check for HQ
                if tile_type in self.HQ_TYPES:
                    if owner is None:
                        errors.append(f"HQ at ({x},{y}) has no owner!")
                    else:
                        player_hqs[owner].append((x, y))
                        
                # Count properties
                if tile_type in self.INCOME_PROPERTIES:
                    if owner is not None:
                        player_properties[owner] += 1
                        player_income[owner] += 1000
                    else:
                        neutral_properties += 1
                        
                # Count production facilities
                if tile_type in self.PRODUCTION_FACILITIES:
                    if owner is not None:
                        facility_type = tile_type.name
                        player_production[owner][facility_type] += 1
                        
                # Track COM towers
                if tile_type == MapType.COM_TOWER:
                    com_towers.append((x, y))
                    
        # Validate each player has at least one HQ
        for player in range(num_players):
            if not player_hqs[player]:
                errors.append(f"Player {player} has no HQ!")
                
        # Validate income balance
        incomes = list(player_income.values())
        if incomes:
            min_income = min(incomes)
            max_income = max(incomes)
            income_diff = max_income - min_income
            
            stats["min_income"] = min_income
            stats["max_income"] = max_income
            stats["income_variance"] = income_diff
            
            if income_diff > 3000:
                errors.append(f"Income imbalance too high: {income_diff} (max allowed: 3000)")
            elif income_diff > 2000:
                warnings.append(f"Income imbalance is high: {income_diff}")
                
        # Validate production facilities
        for player in range(num_players):
            if player_production[player]["FACTORY"] == 0:
                errors.append(f"Player {player} has no factories!")
                
            # For larger maps, check for air/sea production
            if width * height > 225:  # 15x15 or larger
                if player_production[player]["AIRPORT"] == 0:
                    warnings.append(f"Player {player} has no airports (recommended for large maps)")
                    
        # Check HQ safety (minimum distance between HQs)
        if len(player_hqs) >= 2:
            min_hq_distance = float('inf')
            for p1, hqs1 in player_hqs.items():
                for p2, hqs2 in player_hqs.items():
                    if p1 < p2:
                        for hq1 in hqs1:
                            for hq2 in hqs2:
                                dist = self._manhattan_distance(hq1, hq2)
                                min_hq_distance = min(min_hq_distance, dist)
                                
            stats["min_hq_distance"] = min_hq_distance
            
            if min_hq_distance < 8:
                errors.append(f"HQs too close together: {min_hq_distance} tiles (minimum: 8)")
            elif min_hq_distance < 10:
                warnings.append(f"HQs are close together: {min_hq_distance} tiles")
                
        # Check COM tower placement
        if com_towers:
            stats["com_towers"] = len(com_towers)
            
            # Verify COM towers are roughly equidistant from all HQs
            for tower in com_towers:
                distances = []
                for hqs in player_hqs.values():
                    if hqs:
                        avg_dist = sum(self._manhattan_distance(tower, hq) for hq in hqs) / len(hqs)
                        distances.append(avg_dist)
                        
                if distances:
                    dist_variance = max(distances) - min(distances)
                    if dist_variance > 5:
                        warnings.append(f"COM tower at {tower} is not equidistant from all players")
                        
        # Statistics
        stats["neutral_properties"] = neutral_properties
        stats["total_properties"] = sum(player_properties.values()) + neutral_properties
        
        for player in range(num_players):
            stats[f"player_{player}_properties"] = player_properties[player]
            stats[f"player_{player}_income"] = player_income[player]
            
        # Determine if map is valid
        valid = len(errors) == 0
        
        return ValidationResult(valid, errors, warnings, stats)
        
    def _manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance between two positions"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
        
        
    def suggest_improvements(self, validation_result: ValidationResult) -> List[str]:
        """Suggest improvements based on validation results"""
        suggestions = []
        
        stats = validation_result.stats
        
        # Income balance suggestions
        if "income_variance" in stats and stats["income_variance"] > 1000:
            suggestions.append("Consider redistributing properties to balance income better")
            
        # HQ distance suggestions  
        if "min_hq_distance" in stats and stats["min_hq_distance"] < 12:
            suggestions.append("Consider spacing HQs further apart for longer games")
            
        # Property count suggestions
        total_tiles = stats.get("width", 0) * stats.get("height", 0)
        total_props = stats.get("total_properties", 0)
        
        if total_tiles > 0:
            prop_density = total_props / total_tiles
            if prop_density < 0.08:
                suggestions.append("Map has low property density - consider adding more cities")
            elif prop_density > 0.15:
                suggestions.append("Map has high property density - might lead to quick games")
                
        return suggestions


# Command line interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python map_validator.py <map_file>")
        sys.exit(1)
        
    validator = MapValidator()
    result = validator.validate_file(sys.argv[1])
    
    print(result)
    
    if not result.valid:
        suggestions = validator.suggest_improvements(result)
        if suggestions:
            print("\nSuggestions:")
            for suggestion in suggestions:
                print(f"  💡 {suggestion}")
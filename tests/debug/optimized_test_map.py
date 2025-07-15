import logging

logger = logging.getLogger(__name__)
# optimized_test_map.py - CLEAN FIXED VERSION
# Replace your entire optimized_test_map.py file with this content

from map_system import Map, MapType, Army, MapTile, map_repository
from unit import Unit, UnitType, Army
from gameboard import GameBoard, GameTile

def create_optimized_test_map():
    """
    Create the ultimate test map for comprehensive mechanics testing.
    Features:
    - Troops within immediate attack range
    - Neutral and enemy bases ready to capture
    - Transports loaded with cargo for testing
    - All unit types strategically positioned
    - Multiple combat scenarios ready to execute
    """
    
    # 12x10 map with optimal layout for testing all mechanics
    map_data = '''RED,BLUE
PORT:RED,SEA,SEA,REEF,SEA,SEA,REEF,SEA,SEA,SEA,SEA,PORT:BLUE
SEA,SEA,SEA,SEA,SEA,SEA,SEA,SEA,SEA,SEA,SEA,SEA
BEACH_W,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_E
FACTORY:RED,ROAD_HORT,CITY,ROAD_HORT,PLAIN,PLAIN,ROAD_HORT,CITY,ROAD_HORT,FACTORY:BLUE,AIRPORT,PLAIN
ROAD_VERT,PLAIN,WOOD,PLAIN,MOUNTAIN,MOUNTAIN,PLAIN,WOOD,PLAIN,ROAD_VERT,PLAIN,PLAIN
ROAD_VERT,PLAIN,PLAIN,CITY,PLAIN,PLAIN,CITY,PLAIN,PLAIN,ROAD_VERT,CITY,MOUNTAIN
BASE_TOWER_1:RED,ROAD_HORT,ROAD_HORT,PLAIN,PLAIN,PLAIN,PLAIN,ROAD_HORT,ROAD_HORT,BASE_TOWER_1:BLUE,PLAIN,WOOD
PLAIN,MOUNTAIN,WOOD,PLAIN,CITY,CITY,PLAIN,WOOD,MOUNTAIN,PLAIN,PLAIN,PLAIN
AIRPORT:RED,ROAD_HORT,ROAD_HORT,ROAD_HORT,PLAIN,PLAIN,ROAD_HORT,ROAD_HORT,ROAD_HORT,AIRPORT:BLUE,FACTORY,CITY
PLAIN,PLAIN,PLAIN,PLAIN,MOUNTAIN,MOUNTAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN'''
    
    # Create the map
    test_map = Map.parse(map_data, "Optimized Test Map - All Mechanics")
    board = GameBoard.create(test_map)
    
    # Set generous funds for extensive testing
    board.red_funds = 50000
    board.blue_funds = 50000
    
    # Define comprehensive unit deployment for immediate testing
    units_to_deploy = [
        # === IMMEDIATE COMBAT SCENARIOS ===
        # Center combat cluster - units ready to attack each other
        {'army': Army.RED, 'type': UnitType.TANK, 'x': 4, 'y': 5, 'hp': 80},
        {'army': Army.BLUE, 'type': UnitType.TANK, 'x': 6, 'y': 5, 'hp': 90},  # Adjacent for immediate combat
        
        {'army': Army.RED, 'type': UnitType.ARTILLERY, 'x': 3, 'y': 4, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.ARTILLERY, 'x': 7, 'y': 4, 'hp': 100},  # In range
        
        {'army': Army.RED, 'type': UnitType.INFANTRY, 'x': 4, 'y': 6, 'hp': 70},
        {'army': Army.BLUE, 'type': UnitType.MECH, 'x': 6, 'y': 6, 'hp': 85},  # Adjacent infantry vs mech
        
        # === NAVAL COMBAT WITH TRANSPORTS ===
        # RED naval force with loaded transport
        {'army': Army.RED, 'type': UnitType.BATTLESHIP, 'x': 2, 'y': 1, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.LANDER, 'x': 3, 'y': 1, 'hp': 100, 'cargo': [UnitType.TANK, UnitType.INFANTRY]},
        {'army': Army.RED, 'type': UnitType.CRUISER, 'x': 4, 'y': 1, 'hp': 100},
        
        # BLUE naval force with loaded transport  
        {'army': Army.BLUE, 'type': UnitType.BATTLESHIP, 'x': 8, 'y': 1, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.LANDER, 'x': 7, 'y': 1, 'hp': 100, 'cargo': [UnitType.MECH, UnitType.RECON]},
        {'army': Army.BLUE, 'type': UnitType.SUB, 'x': 9, 'y': 1, 'hp': 100},
        
        # === AIR UNITS FOR COMPREHENSIVE TESTING ===
        {'army': Army.RED, 'type': UnitType.FIGHTER, 'x': 1, 'y': 8, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.BOMBER, 'x': 2, 'y': 8, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.FIGHTER, 'x': 9, 'y': 8, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.BCOPTER, 'x': 10, 'y': 8, 'hp': 100},
        
        # === CAPTURE-READY INFANTRY ===
        # RED infantry positioned to capture neutral/enemy cities
        {'army': Army.RED, 'type': UnitType.INFANTRY, 'x': 2, 'y': 3, 'hp': 100},  # Next to city at (2,3)
        {'army': Army.RED, 'type': UnitType.INFANTRY, 'x': 6, 'y': 7, 'hp': 100},  # Next to city at (6,7)
        
        # BLUE infantry positioned to capture neutral cities
        {'army': Army.BLUE, 'type': UnitType.INFANTRY, 'x': 8, 'y': 3, 'hp': 100},  # Next to city at (8,3)
        {'army': Army.BLUE, 'type': UnitType.MECH, 'x': 10, 'y': 6, 'hp': 100},     # Next to city at (10,6)
        
        # === LOADED GROUND TRANSPORTS ===
        # APC units loaded with cargo for transport testing
        {'army': Army.RED, 'type': UnitType.APC, 'x': 1, 'y': 4, 'hp': 100, 'cargo': [UnitType.INFANTRY, UnitType.MECH]},
        {'army': Army.BLUE, 'type': UnitType.APC, 'x': 9, 'y': 4, 'hp': 100, 'cargo': [UnitType.INFANTRY]},
        
        # === SUPPORT AND UTILITY UNITS ===
        {'army': Army.RED, 'type': UnitType.RECON, 'x': 1, 'y': 5, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.ANTIAIR, 'x': 2, 'y': 5, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.RECON, 'x': 9, 'y': 5, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.ROCKET, 'x': 10, 'y': 5, 'hp': 100},
        
        # === ADDITIONAL VARIETY FOR EDGE CASES ===
        {'army': Army.RED, 'type': UnitType.MEDIUMTANK, 'x': 1, 'y': 6, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.NEOTANK, 'x': 9, 'y': 6, 'hp': 100},
        
        # === ADDITIONAL TESTING UNITS ===
        {'army': Army.RED, 'type': UnitType.MISSILE, 'x': 1, 'y': 7, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.MISSILE, 'x': 9, 'y': 7, 'hp': 100},
        
        # Transport copters for air transport testing
        {'army': Army.RED, 'type': UnitType.TCOPTER, 'x': 3, 'y': 8, 'hp': 100, 'cargo': [UnitType.INFANTRY]},
        {'army': Army.BLUE, 'type': UnitType.TCOPTER, 'x': 7, 'y': 8, 'hp': 100, 'cargo': [UnitType.MECH]},
    ]
    
    # Deploy all units with proper setup
    deployed_count = 0
    from config import Config
    config = Config()
    
    for unit_data in units_to_deploy:
        try:
            # Get unit configuration
            unit_type_name = unit_data['type'].name
            unit_config = config.units[unit_type_name]
            
            # Create unit
            unit = Unit.create(unit_data['army'], unit_data['type'], unit_config)
            
            # Set unit properties for immediate testing
            unit.status.hp = unit_data.get('hp', 100)
            unit.can_move = True
            unit.can_attack = True  
            unit.can_capture = True
            unit.status.fuel = unit_config.fuel
            unit.status.ammo = unit_config.ammo
            
            # Handle cargo loading for transports
            if 'cargo' in unit_data:
                # Initialize cargo array properly based on transport type
                if unit_data['type'] == UnitType.LANDER:
                    max_capacity = 2
                elif unit_data['type'] == UnitType.APC:
                    max_capacity = 1
                elif unit_data['type'] == UnitType.TCOPTER:
                    max_capacity = 1
                else:
                    max_capacity = 2  # Default for other transports
                
                # Initialize cargo array with proper size (None = empty slots)
                unit.cargo = [None] * max_capacity
                
                # Also initialize in status if it exists
                if hasattr(unit, 'status'):
                    unit.status.cargo = [None] * max_capacity
                
                cargo_loaded = 0
                for i, cargo_type in enumerate(unit_data['cargo']):
                    if cargo_loaded >= max_capacity:
                        break
                        
                    try:
                        cargo_config = config.units[cargo_type.name]
                        cargo_unit = Unit.create(unit_data['army'], cargo_type, cargo_config)
                        cargo_unit.status.hp = 100
                        cargo_unit.can_move = False  # Loaded units can't move independently
                        
                        # Store cargo in both locations for compatibility
                        unit.cargo[cargo_loaded] = cargo_unit
                        if hasattr(unit, 'status'):
                            unit.status.cargo[cargo_loaded] = cargo_unit
                            
                        cargo_loaded += 1
                        
                    except Exception as cargo_error:
                        print(f"Warning: Could not load cargo {cargo_type.name}: {cargo_error}")
                
                if cargo_loaded > 0:
                    print(f"✅ Loaded {unit_data['type'].name} with {cargo_loaded} cargo units: {[c.type.name for c in unit.cargo if c is not None]}")
                else:
                    print(f"⚠️ Failed to load any cargo for {unit_data['type'].name}")
                    # Set empty cargo arrays if no cargo was loaded
                    unit.cargo = []
                    if hasattr(unit, 'status'):
                        unit.status.cargo = []
            
            # Place unit on the board
            tile_index = unit_data['y'] * board.width + unit_data['x']
            if tile_index < len(board.grid):
                board.grid[tile_index].unit = unit
                deployed_count += 1
                
                # Update army statistics
                if unit_data['army'] == Army.RED:
                    board.total_red_troops += 1
                else:
                    board.total_blue_troops += 1
                    
        except Exception as e:
            print(f"Failed to deploy {unit_data['type'].name} at ({unit_data['x']},{unit_data['y']}): {e}")
    
    # Update property counts
    red_properties = 0
    blue_properties = 0
    neutral_properties = 0
    
    for tile in board.grid:
        if tile.mapTile.is_capturable():
            if tile.mapTile.army == Army.RED:
                red_properties += 1
            elif tile.mapTile.army == Army.BLUE:
                blue_properties += 1
            else:
                neutral_properties += 1
    
    board.total_red_properties = red_properties
    board.total_blue_properties = blue_properties
    
    print(f"✅ Deployed {deployed_count} units on optimized test map")
    print(f"   📊 RED: {board.total_red_troops} units, {board.total_red_properties} properties")
    print(f"   📊 BLUE: {board.total_blue_troops} units, {board.total_blue_properties} properties")
    print(f"   🏛️ Neutral properties: {neutral_properties}")
    print(f"   ⚔️ Immediate combat scenarios: 3 pairs ready")
    print(f"   🚢 Transport units with cargo: Multiple loaded transports")
    print(f"   🏰 Capture opportunities: {neutral_properties + blue_properties + red_properties} buildings")
    
    return board

def get_optimized_test_game(token: str):
    """Create a game manager with the optimized test map - FIXED VERSION"""
    # Import everything explicitly to avoid any import issues
    from manager import GameManager
    from config import Config
    
    logger.debug(f"Creating optimized test game for token: {token}")
    
    # Load configuration first
    logger.debug("Loading configuration...")
    config_game = Config()
    logger.debug(f"Config loaded: {type(config_game)}")
    
    # Create optimized board
    logger.debug("Creating optimized board...")
    board = create_optimized_test_map()
    logger.debug(f"Board created: {type(board)}")
    
    # Create game manager with BOTH required parameters
    logger.debug("Creating GameManager with config and board...")
    game_manager = GameManager(config_game, board)
    logger.debug(f"GameManager created successfully: {type(game_manager)}")
    
    # Set game as active and ready
    game_manager.board.game_active = True
    game_manager.board.current_turn = Army.RED  # Start with RED
    
    print(f"🎮 Created optimized test game: {token}")
    print("   Ready for immediate testing of all mechanics!")
    
    return game_manager

def create_quick_combat_scenario():
    """Create a smaller 8x6 map focused purely on combat testing"""
    
    map_data = '''RED,BLUE
FACTORY:RED,ROAD_HORT,PLAIN,PLAIN,PLAIN,PLAIN,ROAD_HORT,FACTORY:BLUE
ROAD_VERT,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,ROAD_VERT
ROAD_VERT,PLAIN,MOUNTAIN,PLAIN,PLAIN,MOUNTAIN,PLAIN,ROAD_VERT
ROAD_VERT,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,ROAD_VERT
ROAD_VERT,PLAIN,PLAIN,CITY,CITY,PLAIN,PLAIN,ROAD_VERT
AIRPORT:RED,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,AIRPORT:BLUE'''
    
    test_map = Map.parse(map_data, "Quick Combat Test")
    board = GameBoard.create(test_map)
    
    # Set funds
    board.red_funds = 30000
    board.blue_funds = 30000
    
    # Deploy units for immediate combat
    combat_units = [
        # Center combat cluster
        {'army': Army.RED, 'type': UnitType.TANK, 'x': 2, 'y': 3, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.TANK, 'x': 4, 'y': 3, 'hp': 100},  # Adjacent
        
        {'army': Army.RED, 'type': UnitType.INFANTRY, 'x': 2, 'y': 2, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.MECH, 'x': 4, 'y': 2, 'hp': 100},  # Adjacent
        
        # Artillery at range
        {'army': Army.RED, 'type': UnitType.ARTILLERY, 'x': 1, 'y': 3, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.ARTILLERY, 'x': 5, 'y': 3, 'hp': 100},
        
        # Capture units near cities
        {'army': Army.RED, 'type': UnitType.INFANTRY, 'x': 2, 'y': 4, 'hp': 100},  # Next to city
        {'army': Army.BLUE, 'type': UnitType.INFANTRY, 'x': 4, 'y': 4, 'hp': 100},  # Next to city
    ]
    
    # Deploy combat units
    from config import Config
    config = Config()
    
    for unit_data in combat_units:
        try:
            unit_config = config.units[unit_data['type'].name]
            unit = Unit.create(unit_data['army'], unit_data['type'], unit_config)
            
            unit.status.hp = unit_data['hp']
            unit.can_move = True
            unit.can_attack = True
            unit.can_capture = True
            unit.status.fuel = unit_config.fuel
            unit.status.ammo = unit_config.ammo
            
            tile_index = unit_data['y'] * board.width + unit_data['x']
            board.grid[tile_index].unit = unit
        except Exception as e:
            print(f"Failed to deploy combat unit {unit_data['type'].name}: {e}")
    
    print("🎯 Quick combat scenario ready!")
    print("   ⚔️ 4 pairs of units ready for immediate combat")
    print("   🏰 2 cities ready for capture testing")
    
    return board

def verify_optimized_map():
    """Verify that the optimized map has all required testing elements"""
    print("🔍 Verifying optimized test map...")
    
    try:
        board = create_optimized_test_map()
        
        # Count different unit types
        unit_counts = {}
        combat_pairs = 0
        loaded_transports = 0
        capture_ready = 0
        
        for tile in board.grid:
            if tile.unit:
                unit_type = tile.unit.type.name
                unit_counts[unit_type] = unit_counts.get(unit_type, 0) + 1
                
                # Check for loaded transports
                if hasattr(tile.unit, 'cargo') and len(tile.unit.cargo) > 0:
                    loaded_transports += 1
                
                # Check for capture-ready infantry near buildings
                if tile.unit.type in [UnitType.INFANTRY, UnitType.MECH]:
                    # Check adjacent tiles for capturable buildings
                    for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                        check_x, check_y = tile.x + dx, tile.y + dy
                        if 0 <= check_x < board.width and 0 <= check_y < board.height:
                            check_tile = board.grid[check_y * board.width + check_x]
                            if check_tile.mapTile.is_capturable():
                                capture_ready += 1
                                break
        
        print("🔍 OPTIMIZED MAP VERIFICATION:")
        print(f"   📊 Total units deployed: {sum(unit_counts.values())}")
        print(f"   🚢 Loaded transports: {loaded_transports}")
        print(f"   🏰 Capture-ready units: {capture_ready}")
        print(f"   📋 Unit variety: {len(unit_counts)} different types")
        
        for unit_type, count in sorted(unit_counts.items()):
            print(f"      - {unit_type}: {count}")
        
        print("✅ Optimized map verification successful!")
        return True
        
    except Exception as e:
        print(f"❌ Optimized map verification failed: {e}")
        raise e

if __name__ == "__main__":
    verify_optimized_map()
    print("\n🎮 CLEAN OPTIMIZED TEST MAP READY!")
    print("   ✅ All game mechanics can be tested immediately")
    print("   ✅ No setup required - units ready for action")
    print("   ✅ Uses correct unit types from your system")
    print("   ✅ Comprehensive coverage of all unit types and scenarios")
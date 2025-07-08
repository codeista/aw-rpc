# test_map_predeployed.py - Test Map with Predeployed Units

from map_system import Map, MapType, Army, MapTile
from unit import Unit, UnitType, Army
from gameboard import GameBoard, GameTile

def create_test_map_with_units():
    """
    Create a 7x7 test map with predeployed units for comprehensive testing.
    This map includes:
    - RED and BLUE starting positions
    - Mixed unit types for both armies
    - Strategic positions for testing movement, combat, and capture
    - Balanced funds for both players
    """
    
    # Define the map layout (7x7)
    map_data = '''RED,BLUE
FACTORY:RED,ROAD_HORT,PLAIN,CITY,PLAIN,ROAD_HORT,FACTORY:BLUE
ROAD_VERT,PLAIN,WOOD,MOUNTAIN,WOOD,PLAIN,ROAD_VERT
PLAIN,PLAIN,PLAIN,RIVER_VERT,PLAIN,PLAIN,PLAIN
CITY,WOOD,PLAIN,BASE_TOWER_1,PLAIN,WOOD,CITY
PLAIN,PLAIN,PLAIN,RIVER_VERT,PLAIN,PLAIN,PLAIN
ROAD_VERT,PLAIN,WOOD,MOUNTAIN,WOOD,PLAIN,ROAD_VERT
AIRPORT:RED,ROAD_HORT,PLAIN,PORT,PLAIN,ROAD_HORT,AIRPORT:BLUE'''
    
    # Create the map
    test_map = Map.parse(map_data, "Test Map with Predeployed Units")
    
    # Create the board
    board = GameBoard.create(test_map)
    
    # Fix fund balance - both players start with equal funds
    board.red_funds = 15000
    board.blue_funds = 15000
    
    # Define predeployed units with strategic positioning for transport testing
    units_to_deploy = [
        # RED army units (left side) - all can_move=True for testing
        {'army': Army.RED, 'type': UnitType.INFANTRY, 'x': 0, 'y': 1, 'hp': 100, 'can_move': True},
        {'army': Army.RED, 'type': UnitType.APC, 'x': 1, 'y': 1, 'hp': 100, 'can_move': True},  # APC next to infantry
        {'army': Army.RED, 'type': UnitType.MECH, 'x': 0, 'y': 3, 'hp': 100, 'can_move': True},
        {'army': Army.RED, 'type': UnitType.RECON, 'x': 1, 'y': 4, 'hp': 100, 'can_move': True},
        {'army': Army.RED, 'type': UnitType.ARTILLERY, 'x': 0, 'y': 5, 'hp': 100, 'can_move': True},
        {'army': Army.RED, 'type': UnitType.TANK, 'x': 2, 'y': 1, 'hp': 100, 'can_move': True},
        
        # BLUE army units (right side) - all can_move=True for testing
        {'army': Army.BLUE, 'type': UnitType.INFANTRY, 'x': 6, 'y': 1, 'hp': 100, 'can_move': True},
        {'army': Army.BLUE, 'type': UnitType.APC, 'x': 5, 'y': 1, 'hp': 100, 'can_move': True},  # APC next to infantry
        {'army': Army.BLUE, 'type': UnitType.MECH, 'x': 6, 'y': 3, 'hp': 100, 'can_move': True},
        {'army': Army.BLUE, 'type': UnitType.RECON, 'x': 5, 'y': 4, 'hp': 100, 'can_move': True},
        {'army': Army.BLUE, 'type': UnitType.ARTILLERY, 'x': 6, 'y': 5, 'hp': 100, 'can_move': True},
        {'army': Army.BLUE, 'type': UnitType.TANK, 'x': 4, 'y': 1, 'hp': 100, 'can_move': True},
        
        # Central units for immediate combat testing - positioned for action
        {'army': Army.RED, 'type': UnitType.INFANTRY, 'x': 2, 'y': 2, 'hp': 80, 'can_move': True},
        {'army': Army.BLUE, 'type': UnitType.INFANTRY, 'x': 4, 'y': 2, 'hp': 90, 'can_move': True},
        
        # Units near capturable properties - ready to capture
        {'army': Army.RED, 'type': UnitType.INFANTRY, 'x': 2, 'y': 3, 'hp': 100, 'can_move': True},
        {'army': Army.BLUE, 'type': UnitType.INFANTRY, 'x': 4, 'y': 3, 'hp': 100, 'can_move': True},
    ]
    
    # Deploy all units with proper action flags
    for unit_data in units_to_deploy:
        # Get the proper unit config from your Config system
        from config import Config
        config_game = Config()
        unit_config = config_game.units[unit_data['type'].name]
        
        # Create the unit with proper config
        unit = Unit.create(
            army=unit_data['army'],
            unit_type=unit_data['type'],
            unit_config=unit_config
        )
        
        # Set unit properties for testing
        unit.status.hp = unit_data['hp']
        unit.can_move = unit_data.get('can_move', True)
        unit.can_attack = True
        unit.can_capture = True
        
        # Place unit on the board with proper action flags
        tile_index = unit_data['y'] * board.width + unit_data['x']
        if tile_index < len(board.grid):
            board.grid[tile_index].unit = unit
            
            # Update army statistics
            if unit_data['army'] == Army.RED:
                board.total_red_troops += 1
            else:
                board.total_blue_troops += 1
    
    # ENSURE ALL UNITS ARE READY TO MOVE AND ACT
    for tile in board.grid:
        if tile.unit:
            tile.unit.can_move = True
            tile.unit.can_attack = True  
            tile.unit.can_capture = True
            # Ensure full fuel for movement
            tile.unit.status.fuel = 99
    
    # Update property counts (for income calculation)
    board.total_red_properties = 3  # Factory, Airport, and one City
    board.total_blue_properties = 3  # Factory, Airport, and one City
    
    return board

def create_comprehensive_test_map():
    """
    Create a larger test map with more scenarios for advanced testing
    """
    
    # Define a 10x10 map with varied terrain and strategic positions
    map_data = '''RED,BLUE
FACTORY:RED,ROAD_HORT,PLAIN,WOOD,CITY,MOUNTAIN,WOOD,PLAIN,ROAD_HORT,FACTORY:BLUE
ROAD_VERT,PLAIN,WOOD,PLAIN,PLAIN,PLAIN,PLAIN,WOOD,PLAIN,ROAD_VERT
PLAIN,PLAIN,MOUNTAIN,PLAIN,RIVER_VERT,RIVER_VERT,PLAIN,MOUNTAIN,PLAIN,PLAIN
CITY,WOOD,PLAIN,AIRPORT:RED,RIVER_VERT,RIVER_VERT,AIRPORT:BLUE,PLAIN,WOOD,CITY
PLAIN,PLAIN,PLAIN,PLAIN,HBridge,HBridge,PLAIN,PLAIN,PLAIN,PLAIN
PLAIN,PLAIN,PLAIN,PLAIN,HBridge,HBridge,PLAIN,PLAIN,PLAIN,PLAIN
CITY,WOOD,PLAIN,PORT:RED,SEA,SEA,PORT:BLUE,PLAIN,WOOD,CITY
PLAIN,PLAIN,MOUNTAIN,PLAIN,SEA,SEA,PLAIN,MOUNTAIN,PLAIN,PLAIN
ROAD_VERT,PLAIN,WOOD,PLAIN,BEACH_N,BEACH_N,PLAIN,WOOD,PLAIN,ROAD_VERT
BASE_TOWER_1:RED,ROAD_HORT,PLAIN,WOOD,CITY,MOUNTAIN,WOOD,PLAIN,ROAD_HORT,BASE_TOWER_1:BLUE'''
    
    comprehensive_map = Map.parse(map_data, "Comprehensive Test Map")
    board = GameBoard.create(comprehensive_map)
    
    # Balanced starting funds
    board.red_funds = 25000
    board.blue_funds = 25000
    
    # Comprehensive unit deployment
    comprehensive_units = [
        # RED ground forces
        {'army': Army.RED, 'type': UnitType.INFANTRY, 'x': 0, 'y': 1, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.MECH, 'x': 1, 'y': 1, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.TANK, 'x': 2, 'y': 1, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.RECON, 'x': 0, 'y': 2, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.ARTILLERY, 'x': 1, 'y': 2, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.ANTIAIR, 'x': 2, 'y': 2, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.APC, 'x': 1, 'y': 3, 'hp': 100},
        
        # RED air force
        {'army': Army.RED, 'type': UnitType.FIGHTER, 'x': 3, 'y': 3, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.BCOPTER, 'x': 2, 'y': 4, 'hp': 100},
        
        # RED naval force
        {'army': Army.RED, 'type': UnitType.LANDER, 'x': 3, 'y': 6, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.CRUISER, 'x': 4, 'y': 7, 'hp': 100},
        
        # BLUE ground forces
        {'army': Army.BLUE, 'type': UnitType.INFANTRY, 'x': 9, 'y': 1, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.MECH, 'x': 8, 'y': 1, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.TANK, 'x': 7, 'y': 1, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.RECON, 'x': 9, 'y': 2, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.ARTILLERY, 'x': 8, 'y': 2, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.ANTIAIR, 'x': 7, 'y': 2, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.APC, 'x': 8, 'y': 3, 'hp': 100},
        
        # BLUE air force
        {'army': Army.BLUE, 'type': UnitType.FIGHTER, 'x': 6, 'y': 3, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.BCOPTER, 'x': 7, 'y': 4, 'hp': 100},
        
        # BLUE naval force
        {'army': Army.BLUE, 'type': UnitType.LANDER, 'x': 6, 'y': 6, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.CRUISER, 'x': 5, 'y': 7, 'hp': 100},
        
        # Central contested units
        {'army': Army.RED, 'type': UnitType.INFANTRY, 'x': 4, 'y': 4, 'hp': 60},
        {'army': Army.BLUE, 'type': UnitType.INFANTRY, 'x': 5, 'y': 4, 'hp': 70},
        {'army': Army.RED, 'type': UnitType.TANK, 'x': 3, 'y': 5, 'hp': 80},
        {'army': Army.BLUE, 'type': UnitType.TANK, 'x': 6, 'y': 5, 'hp': 90},
    ]
    
    # Deploy comprehensive units
    for unit_data in comprehensive_units:
        # Get the proper unit config from your Config system
        from config import Config
        config_game = Config()
        unit_config = config_game.units[unit_data['type'].name]
        
        # Create the unit with proper config
        unit = Unit.create(
            army=unit_data['army'],
            unit_type=unit_data['type'],
            unit_config=unit_config
        )
        unit.status.hp = unit_data['hp']
        
        tile_index = unit_data['y'] * board.width + unit_data['x']
        if tile_index < len(board.grid):
            board.grid[tile_index].unit = unit
            
            if unit_data['army'] == Army.RED:
                board.total_red_troops += 1
            else:
                board.total_blue_troops += 1
    
    board.total_red_properties = 4  # Multiple properties for income
    board.total_blue_properties = 4
    
    return board

# Integration with your existing app.py
def get_predeployed_test_game(token: str = None):
    """
    Function to integrate with your existing game creation system.
    Call this instead of the normal game creation to get a test game with units.
    """
    from manager import GameManager
    from config import Config
    
    # Load configuration - fix: use same pattern as app.py
    config_game = Config()
    
    # Create board with predeployed units
    board = create_test_map_with_units()
    
    # Create game manager
    mngr = GameManager(config_game, board)
    
    return mngr

def get_comprehensive_test_game(token: str = None):
    """
    Get a comprehensive test game with many unit types and scenarios
    """
    from manager import GameManager
    from config import Config
    
    # Load configuration - fix: use same pattern as app.py
    config_game = Config()
    board = create_comprehensive_test_map()
    mngr = GameManager(config_game, board)
    
    return mngr

# Add this to your app.py to enable test maps
def add_test_map_endpoint():
    """
    Add this function to your app.py to create test games easily.
    
    Usage:
    1. Add this to your imports in app.py:
       from test_map_predeployed import get_predeployed_test_game, get_comprehensive_test_game
    
    2. Add these routes to your app.py:
    
    @app.route('/test_predeployed')
    def create_test_game():
        token = secrets.token_urlsafe(6)
        game_manager = get_predeployed_test_game(token)
        games[token] = game_manager
        return redirect(f'/{token}')
    
    @app.route('/test_comprehensive')
    def create_comprehensive_test():
        token = secrets.token_urlsafe(6)
        game_manager = get_comprehensive_test_game(token)
        games[token] = game_manager
        return redirect(f'/{token}')
    """
    pass

# Test script to verify the maps work
if __name__ == "__main__":
    print("🧪 Testing predeployed unit maps...")
    
    # Test basic map
    board = create_test_map_with_units()
    print(f"✅ Basic test map created:")
    print(f"   - Board size: {board.width}x{board.height}")
    print(f"   - RED units: {board.total_red_troops}")
    print(f"   - BLUE units: {board.total_blue_troops}")
    print(f"   - RED funds: {board.red_funds}")
    print(f"   - BLUE funds: {board.blue_funds}")
    
    # Test comprehensive map
    comp_board = create_comprehensive_test_map()
    print(f"✅ Comprehensive test map created:")
    print(f"   - Board size: {comp_board.width}x{comp_board.height}")
    print(f"   - RED units: {comp_board.total_red_troops}")
    print(f"   - BLUE units: {comp_board.total_blue_troops}")
    print(f"   - RED funds: {comp_board.red_funds}")
    print(f"   - BLUE funds: {comp_board.blue_funds}")
    
    # Verify units are properly placed
    units_found = 0
    for tile in board.grid:
        if tile.unit:
            units_found += 1
            print(f"   - {tile.unit.army.name} {tile.unit.type.name} at ({tile.x}, {tile.y}) HP: {tile.unit.status.hp}")
    
    print(f"✅ Found {units_found} units on basic map")
    print("🎮 Maps ready for testing movement, combat, and capture mechanics!")
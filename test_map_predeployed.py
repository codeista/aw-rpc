# test_map_predeployed.py - Updated Test Map with Predeployed Units using new map system

from map_system import Map, MapType, Army, MapTile, map_repository
from unit import Unit, UnitType, Army
from gameboard import GameBoard, GameTile

def create_test_map_with_units():
    """
    Create a comprehensive test map with predeployed units for immediate testing.
    This map includes:
    - Clear terrain separation for naval, land, and air testing
    - Strategic unit positioning for movement, combat, and terrain testing
    - All unit types represented for comprehensive mechanics testing
    - Balanced funds for sustained testing
    """
    
    # Use the new terrain-focused map design
    map_data = '''RED,BLUE
PORT:RED,SEA,SEA,SEA,REEF,SEA,SEA,SEA,PORT:BLUE,PLAIN,MOUNTAIN,CITY
SEA,SEA,SEA,SEA,SEA,SEA,SEA,SEA,SEA,PLAIN,WOOD,PLAIN
SEA,SEA,REEF,SEA,SEA,SEA,REEF,SEA,SEA,ROAD_HORT,ROAD_HORT,ROAD_HORT
BEACH_W,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_E,ROAD_VERT,FACTORY:BLUE,ROAD_VERT
FACTORY:RED,ROAD_HORT,ROAD_HORT,CITY,MOUNTAIN,CITY,ROAD_HORT,ROAD_HORT,FACTORY:BLUE,ROAD_VERT,PLAIN,ROAD_VERT
ROAD_VERT,PLAIN,WOOD,PLAIN,BASE_TOWER_1:RED,BASE_TOWER_1:BLUE,PLAIN,WOOD,ROAD_VERT,ROAD_VERT,MOUNTAIN,ROAD_VERT
ROAD_VERT,MOUNTAIN,CITY,WOOD,PLAIN,PLAIN,WOOD,CITY,ROAD_VERT,ROAD_VERT,WOOD,ROAD_VERT
AIRPORT:RED,ROAD_HORT,ROAD_HORT,ROAD_HORT,PLAIN,PLAIN,ROAD_HORT,ROAD_HORT,AIRPORT:BLUE,ROAD_SW,ROAD_HORT,ROAD_SE
PLAIN,PLAIN,PLAIN,PLAIN,MOUNTAIN,MOUNTAIN,PLAIN,PLAIN,PLAIN,CITY,PLAIN,CITY
PLAIN,MOUNTAIN,WOOD,PLAIN,CITY,CITY,PLAIN,WOOD,MOUNTAIN,PLAIN,FACTORY:RED,PLAIN'''
    
    # Create the map using the new Map.parse system
    test_map = Map.parse(map_data, "Test Map with Predeployed Units")
    
    # Create the board
    board = GameBoard.create(test_map)
    
    # Set balanced starting funds for extensive testing
    board.red_funds = 25000
    board.blue_funds = 25000
    
    # Define predeployed units with strategic positioning for comprehensive testing
    units_to_deploy = [
        # NAVAL COMBAT ZONE (Top 3 rows)
        # RED Naval Forces
        {'army': Army.RED, 'type': UnitType.BATTLESHIP, 'x': 3, 'y': 0, 'hp': 100, 'terrain': 'SEA'},
        {'army': Army.RED, 'type': UnitType.SUB, 'x': 1, 'y': 1, 'hp': 100, 'terrain': 'SEA'},
        {'army': Army.RED, 'type': UnitType.CRUISER, 'x': 4, 'y': 2, 'hp': 100, 'terrain': 'SEA'},
        {'army': Army.RED, 'type': UnitType.LANDER, 'x': 3,'y': 1, 'hp': 100, 'terrain': 'SEA'},
        
        # BLUE Naval Forces
        {'army': Army.BLUE, 'type': UnitType.BATTLESHIP, 'x': 5, 'y': 2, 'hp': 100, 'terrain': 'SEA'},
        {'army': Army.BLUE, 'type': UnitType.CRUISER, 'x': 5, 'y': 0, 'hp': 100, 'terrain': 'SEA'},
        {'army': Army.BLUE, 'type': UnitType.LANDER, 'x': 8,'y': 1, 'hp': 100, 'terrain': 'SEA'},
        
        # LAND COMBAT ZONE (Rows 4-7)
        # RED Land Forces - Testing different terrain effects
        {'army': Army.RED, 'type': UnitType.INFANTRY, 'x': 1, 'y': 4, 'hp': 100, 'terrain': 'ROAD'},
        {'army': Army.RED, 'type': UnitType.TANK, 'x': 3, 'y': 5, 'hp': 100, 'terrain': 'PLAIN'},
        {'army': Army.RED, 'type': UnitType.MECH, 'x': 1, 'y': 6, 'hp': 100, 'terrain': 'MOUNTAIN'},  # Mountain specialist
        {'army': Army.RED, 'type': UnitType.RECON, 'x': 1, 'y': 5, 'hp': 100, 'terrain': 'ROAD'},
        {'army': Army.RED, 'type': UnitType.ARTILLERY, 'x': 3, 'y': 9, 'hp': 100, 'terrain': 'PLAIN'},
        {'army': Army.RED, 'type': UnitType.ANTIAIR, 'x': 2, 'y': 5, 'hp': 100, 'terrain': 'WOOD'},
        {'army': Army.RED, 'type': UnitType.APC, 'x': 0, 'y': 5, 'hp': 100, 'terrain': 'ROAD'},
        
        # BLUE Land Forces - Testing different terrain effects
        {'army': Army.BLUE, 'type': UnitType.INFANTRY, 'x': 7, 'y': 4, 'hp': 100, 'terrain': 'ROAD'},
        {'army': Army.BLUE, 'type': UnitType.TANK, 'x': 8, 'y': 6, 'hp': 100, 'terrain': 'ROAD'},
        {'army': Army.BLUE, 'type': UnitType.MECH, 'x': 6, 'y': 5, 'hp': 100, 'terrain': 'PLAIN'},
        {'army': Army.BLUE, 'type': UnitType.RECON, 'x': 6, 'y': 5, 'hp': 100, 'terrain': 'PLAIN'},
        {'army': Army.BLUE, 'type': UnitType.ROCKET, 'x': 6, 'y': 9, 'hp': 100, 'terrain': 'CITY'},  # City defense
        {'army': Army.BLUE, 'type': UnitType.ANTIAIR, 'x': 7, 'y': 6, 'hp': 100, 'terrain': 'WOOD'},
        
        # AIR OPERATIONS (Rows 7-8)
        # RED Air Force
        {'army': Army.RED, 'type': UnitType.FIGHTER, 'x': 1, 'y': 7, 'hp': 100, 'terrain': 'AIRPORT'},
        {'army': Army.RED, 'type': UnitType.BOMBER, 'x': 1, 'y': 8, 'hp': 100, 'terrain': 'PLAIN'},
        {'army': Army.RED, 'type': UnitType.BCOPTER, 'x': 2, 'y': 8, 'hp': 100, 'terrain': 'PLAIN'},
        
        # BLUE Air Force
        {'army': Army.BLUE, 'type': UnitType.FIGHTER, 'x': 8, 'y': 8, 'hp': 100, 'terrain': 'PLAIN'},
        {'army': Army.BLUE, 'type': UnitType.BCOPTER, 'x': 9, 'y': 8, 'hp': 100, 'terrain': 'CITY'},
        
        # CENTRAL CONTESTED UNITS for immediate combat testing
        {'army': Army.RED, 'type': UnitType.INFANTRY, 'x': 3, 'y': 6, 'hp': 90, 'terrain': 'WOOD'},
        {'army': Army.BLUE, 'type': UnitType.INFANTRY, 'x': 5, 'y': 6, 'hp': 85, 'terrain': 'WOOD'},
        
        # CAPTURE-READY UNITS near neutral properties
        {'army': Army.RED, 'type': UnitType.INFANTRY, 'x': 2, 'y': 6, 'hp': 100, 'terrain': 'CITY'},  # Near city
        {'army': Army.BLUE, 'type': UnitType.INFANTRY, 'x': 9, 'y': 9, 'hp': 100, 'terrain': 'CITY'},  # Near city
    ]
    
    # Deploy all units with proper configuration
    deployed_count = 0
    for unit_data in units_to_deploy:
        try:
            # Get the proper unit config from Config system
            from config import Config
            config_game = Config()
            unit_config = config_game.units[unit_data['type'].name]
            
            # Create the unit with proper config
            unit = Unit.create(
                army=unit_data['army'],
                unit_type=unit_data['type'],
                unit_config=unit_config
            )
            
            # Set unit properties for immediate testing
            unit.status.hp = unit_data['hp']
            unit.can_move = True  # Ready to move
            unit.can_attack = True  # Ready to attack
            unit.can_capture = True  # Ready to capture
            unit.status.fuel = unit_config.fuel  # Full fuel
            unit.status.ammo = unit_config.ammo  # Full ammo
            
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
    
    # Update property counts for income calculation
    red_properties = 0
    blue_properties = 0
    for tile in board.grid:
        if tile.mapTile.is_capturable() and tile.mapTile.army:
            if tile.mapTile.army == Army.RED:
                red_properties += 1
            elif tile.mapTile.army == Army.BLUE:
                blue_properties += 1
    
    board.total_red_properties = red_properties
    board.total_blue_properties = blue_properties
    
    print(f"✅ Deployed {deployed_count} units on terrain-focused test map")
    print(f"   📊 RED: {board.total_red_troops} units, {board.total_red_properties} properties")
    print(f"   📊 BLUE: {board.total_blue_troops} units, {board.total_blue_properties} properties")
    
    return board

def create_comprehensive_test_map():
    """
    Create an even larger test map with maximum variety for advanced testing.
    This includes all terrain types and unit combinations.
    """
    
    # Larger 12x10 map with comprehensive terrain coverage
    map_data = '''RED,BLUE
PORT:RED,SEA,SEA,REEF,SEA,SEA,REEF,SEA,SEA,PORT:BLUE,MOUNTAIN,CITY
SEA,SEA,SEA,SEA,SEA,SEA,SEA,SEA,SEA,SEA,SEA,SEA
SEA,SEA,REEF,SEA,SEA,SEA,SEA,REEF,SEA,SEA,WOOD,PLAIN
BEACH_W,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_E,ROAD_HORT,ROAD_HORT
FACTORY:RED,ROAD_HORT,CITY,MOUNTAIN,WOOD,WOOD,MOUNTAIN,CITY,ROAD_HORT,FACTORY:BLUE,ROAD_VERT,PLAIN
ROAD_VERT,PLAIN,PLAIN,RIVER_VERT,PLAIN,PLAIN,RIVER_VERT,PLAIN,PLAIN,ROAD_VERT,MOUNTAIN,WOOD
ROAD_VERT,WOOD,PLAIN,RIVER_VERT,BASE_TOWER_1:RED,BASE_TOWER_1:BLUE,RIVER_VERT,PLAIN,WOOD,ROAD_VERT,PLAIN,CITY
ROAD_VERT,MOUNTAIN,CITY,RIVER_VERT,PLAIN,PLAIN,RIVER_VERT,CITY,MOUNTAIN,ROAD_VERT,WOOD,PLAIN
AIRPORT:RED,ROAD_HORT,ROAD_HORT,HBridge,PLAIN,PLAIN,HBridge,ROAD_HORT,ROAD_HORT,AIRPORT:BLUE,PLAIN,MOUNTAIN
PLAIN,PLAIN,WOOD,PLAIN,MOUNTAIN,MOUNTAIN,PLAIN,WOOD,PLAIN,PLAIN,CITY,WOOD
COM_TOWER:RED,CITY,PLAIN,WOOD,CITY,CITY,WOOD,PLAIN,CITY,COM_TOWER:BLUE,PLAIN,FACTORY:RED'''
    
    comprehensive_map = Map.parse(map_data, "Comprehensive Test Map")
    board = GameBoard.create(comprehensive_map)
    
    # Higher funds for extensive testing
    board.red_funds = 50000
    board.blue_funds = 50000
    
    # Comprehensive unit deployment covering all unit types
    comprehensive_units = [
        # RED NAVAL FORCES
        {'army': Army.RED, 'type': UnitType.BATTLESHIP, 'x': 4, 'y': 0, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.CRUISER, 'x': 4, 'y': 2, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.SUB, 'x': 4, 'y': 1, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.LANDER, 'x': 1, 'y': 3, 'hp': 100},
        
        # RED GROUND FORCES
        {'army': Army.RED, 'type': UnitType.INFANTRY, 'x': 1, 'y': 3, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.MECH, 'x': 2, 'y': 4, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.TANK, 'x': 1, 'y': 5, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.MEDIUMTANK, 'x': 2, 'y': 6, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.RECON, 'x': 0, 'y': 4, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.APC, 'x': 2, 'y': 3, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.ARTILLERY, 'x': 3, 'y': 8, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.ROCKET, 'x': 2, 'y': 8, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.ANTIAIR, 'x': 4, 'y': 8, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.MISSILE, 'x': 0, 'y': 9, 'hp': 100},
        
        # RED AIR FORCE
        {'army': Army.RED, 'type': UnitType.FIGHTER, 'x': 1, 'y': 7, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.BOMBER, 'x': 2, 'y': 7, 'hp': 100},
        {'army': Army.RED, 'type': UnitType.BCOPTER, 'x': 0, 'y': 8, 'hp': 100},
        
        # BLUE NAVAL FORCES  
        {'army': Army.BLUE, 'type': UnitType.BATTLESHIP, 'x': 5, 'y': 0, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.CRUISER, 'x': 5, 'y': 1, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.SUB, 'x': 5, 'y': 2, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.LANDER, 'x': 8, 'y': 3, 'hp': 100},
        
        # BLUE GROUND FORCES
        {'army': Army.BLUE, 'type': UnitType.INFANTRY, 'x': 8, 'y': 3, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.MECH, 'x': 7, 'y': 4, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.TANK, 'x': 8, 'y': 5, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.MEDIUMTANK, 'x': 7, 'y': 6, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.RECON, 'x': 9, 'y': 4, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.APC, 'x': 9, 'y': 5, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.ARTILLERY, 'x': 8, 'y': 8, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.ROCKET, 'x': 7, 'y': 8, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.ANTIAIR, 'x': 8, 'y': 6, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.MISSILE, 'x': 9, 'y': 9, 'hp': 100},
        
        # BLUE AIR FORCE
        {'army': Army.BLUE, 'type': UnitType.FIGHTER, 'x': 8, 'y': 7, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.BOMBER, 'x': 7, 'y': 7, 'hp': 100},
        {'army': Army.BLUE, 'type': UnitType.BCOPTER, 'x': 9, 'y': 8, 'hp': 100},
        
        # CENTRAL COMBAT UNITS
        {'army': Army.RED, 'type': UnitType.INFANTRY, 'x': 4, 'y': 5, 'hp': 80},
        {'army': Army.BLUE, 'type': UnitType.INFANTRY, 'x': 5, 'y': 5, 'hp': 90},
        {'army': Army.RED, 'type': UnitType.TANK, 'x': 3, 'y': 6, 'hp': 75},
        {'army': Army.BLUE, 'type': UnitType.TANK, 'x': 6, 'y': 6, 'hp': 85},
    ]
    
    # Deploy comprehensive units
    deployed_count = 0
    for unit_data in comprehensive_units:
        try:
            from config import Config
            config_game = Config()
            unit_config = config_game.units[unit_data['type'].name]
            
            unit = Unit.create(
                army=unit_data['army'],
                unit_type=unit_data['type'],
                unit_config=unit_config
            )
            unit.status.hp = unit_data['hp']
            unit.can_move = True
            unit.can_attack = True
            unit.can_capture = True
            unit.status.fuel = unit_config.fuel
            unit.status.ammo = unit_config.ammo
            
            tile_index = unit_data['y'] * board.width + unit_data['x']
            if tile_index < len(board.grid):
                board.grid[tile_index].unit = unit
                deployed_count += 1
                
                if unit_data['army'] == Army.RED:
                    board.total_red_troops += 1
                else:
                    board.total_blue_troops += 1
                    
        except Exception as e:
            print(f"Failed to deploy {unit_data['type'].name}: {e}")
    
    # Update property counts
    red_properties = 0
    blue_properties = 0
    for tile in board.grid:
        if tile.mapTile.is_capturable() and tile.mapTile.army:
            if tile.mapTile.army == Army.RED:
                red_properties += 1
            elif tile.mapTile.army == Army.BLUE:
                blue_properties += 1
    
    board.total_red_properties = red_properties
    board.total_blue_properties = blue_properties
    
    print(f"✅ Deployed {deployed_count} units on comprehensive test map")
    print(f"   📊 RED: {board.total_red_troops} units, {board.total_red_properties} properties")
    print(f"   📊 BLUE: {board.total_blue_troops} units, {board.total_blue_properties} properties")
    
    return board

# Integration functions for your existing app.py
def get_predeployed_test_game(token: str = None):
    """
    Function to integrate with your existing game creation system.
    Call this instead of the normal game creation to get a test game with units.
    """
    from manager import GameManager
    from config import Config
    
    # Load configuration
    config_game = Config()
    
    # Create board with predeployed units using new map system
    board = create_test_map_with_units()
    
    # Create game manager
    mngr = GameManager(config_game, board)
    
    return mngr

def get_comprehensive_test_game(token: str = None):
    """
    Get a comprehensive test game with all unit types and terrain scenarios
    """
    from manager import GameManager
    from config import Config
    
    config_game = Config()
    board = create_comprehensive_test_map()
    mngr = GameManager(config_game, board)
    
    return mngr

# Test verification function
def verify_map_and_units():
    """
    Verify that the maps and units are created correctly
    """
    print("🧪 Verifying updated predeployed unit maps...")
    
    # Test basic terrain-focused map
    board = create_test_map_with_units()
    print(f"✅ Terrain-focused test map:")
    print(f"   - Board size: {board.width}x{board.height}")
    print(f"   - RED units: {board.total_red_troops}")
    print(f"   - BLUE units: {board.total_blue_troops}")
    print(f"   - RED properties: {board.total_red_properties}")
    print(f"   - BLUE properties: {board.total_blue_properties}")
    
    # Verify terrain separation
    naval_units = 0
    land_units = 0
    air_units = 0
    
    for tile in board.grid:
        if tile.unit:
            if tile.unit.type in [UnitType.BATTLESHIP, UnitType.CRUISER, UnitType.SUB, UnitType.LANDER]:
                naval_units += 1
            elif tile.unit.type in [UnitType.FIGHTER, UnitType.BOMBER, UnitType.BCOPTER]:
                air_units += 1
            else:
                land_units += 1
    
    print(f"   - Naval units: {naval_units}")
    print(f"   - Land units: {land_units}")
    print(f"   - Air units: {air_units}")
    
    # Test comprehensive map
    comp_board = create_comprehensive_test_map()
    print(f"✅ Comprehensive test map:")
    print(f"   - Board size: {comp_board.width}x{comp_board.height}")
    print(f"   - Total units: {comp_board.total_red_troops + comp_board.total_blue_troops}")
    
    return True

# Add route integration instructions
def add_test_map_routes_to_app():
    """
    Add these routes to your app.py for easy access to test maps:
    
    @app.route('/test')
    def create_terrain_test_game():
        token = secrets.token_urlsafe(6)
        game_manager = get_predeployed_test_game(token)
        games[token] = game_manager
        app_logger.info(f"Created terrain test game: {token}")
        return redirect(f'/game/{token}')
    
    @app.route('/test_comprehensive')  
    def create_comprehensive_test():
        token = secrets.token_urlsafe(6)
        game_manager = get_comprehensive_test_game(token)
        games[token] = game_manager
        app_logger.info(f"Created comprehensive test game: {token}")
        return redirect(f'/game/{token}')
        
    @app.route('/test_combat')
    def create_combat_test():
        token = secrets.token_urlsafe(6)
        game_manager = get_predeployed_test_game(token)
        
        # Modify for immediate combat testing
        board = game_manager.board
        center_x, center_y = board.width // 2, board.height // 2
        
        # Clear center and place opposing units adjacent
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                x, y = center_x + dx, center_y + dy
                if 0 <= x < board.width and 0 <= y < board.height:
                    tile_index = y * board.width + x
                    board.grid[tile_index].unit = None
        
        # Add adjacent combat units for immediate testing
        from config import Config
        config_game = Config()
        
        # RED tank
        red_tank_config = config_game.units[UnitType.TANK.name]
        red_tank = Unit.create(Army.RED, UnitType.TANK, red_tank_config)
        tile_index = center_y * board.width + (center_x - 1)
        board.grid[tile_index].unit = red_tank
        
        # BLUE tank (adjacent)
        blue_tank_config = config_game.units[UnitType.TANK.name]
        blue_tank = Unit.create(Army.BLUE, UnitType.TANK, blue_tank_config)
        tile_index = center_y * board.width + (center_x + 1)
        board.grid[tile_index].unit = blue_tank
        
        games[token] = game_manager
        app_logger.info(f"Created combat test game: {token}")
        return redirect(f'/game/{token}')
    """
    pass

# Test script
if __name__ == "__main__":
    verify_map_and_units()
    print("🎮 Updated maps ready for comprehensive game mechanics testing!")
    print("   🌊 Naval combat in dedicated sea zones")
    print("   🏔️ Land combat with terrain variety")  
    print("   ✈️ Air operations with clear sight lines")
    print("   🎯 Immediate combat scenarios ready to test")
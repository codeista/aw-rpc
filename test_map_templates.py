"""
Test map templates with predeployed units support
Each map is tailored for specific test scenarios with comprehensive unit coverage
"""

# Combat Test Map - ALL 25 unit types represented
COMBAT_TEST_MAP = {
    'name': 'Combat Test Arena - All Units',
    'map_data': '''RED,BLUE
FACTORY:RED,CITY,PLAIN,PLAIN,MOUNTAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,MOUNTAIN,PLAIN,PLAIN,CITY,FACTORY:BLUE
PORT:RED,SEA,SEA,BEACH_W,PLAIN,WOOD,ROAD_HORT,ROAD_HORT,ROAD_HORT,WOOD,PLAIN,BEACH_E,SEA,SEA,PORT:BLUE
SEA,SEA,SEA,BEACH_W,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,BEACH_E,SEA,SEA,SEA
AIRPORT:RED,PLAIN,PLAIN,PLAIN,CITY,MOUNTAIN,PLAIN,PLAIN,PLAIN,MOUNTAIN,CITY,PLAIN,PLAIN,PLAIN,AIRPORT:BLUE
PLAIN,ROAD_VERT,PLAIN,WOOD,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,WOOD,PLAIN,ROAD_VERT,PLAIN
PLAIN,ROAD_VERT,PLAIN,PLAIN,PLAIN,ROAD_HORT,CITY,COM_TOWER,CITY,ROAD_HORT,PLAIN,PLAIN,PLAIN,ROAD_VERT,PLAIN
FACTORY:RED,ROAD_VERT,WOOD,PLAIN,MOUNTAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,MOUNTAIN,PLAIN,WOOD,ROAD_VERT,FACTORY:BLUE
CITY:RED,ROAD_VERT,PLAIN,PLAIN,PLAIN,WOOD,PLAIN,PLAIN,PLAIN,WOOD,PLAIN,PLAIN,PLAIN,ROAD_VERT,CITY:BLUE
PLAIN,ROAD_SW,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,MISSILE_SILO,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_SE,PLAIN
PLAIN,PLAIN,MOUNTAIN,PLAIN,CITY,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,CITY,PLAIN,MOUNTAIN,PLAIN,PLAIN
PIPE_END_N,PIPE_VERT,PIPE_END_S,PLAIN,PLAIN,WOOD,PLAIN,PLAIN,PLAIN,WOOD,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN
BASE_TOWER_1:RED,CITY,PLAIN,PLAIN,CITY,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,CITY,PLAIN,PLAIN,CITY,BASE_TOWER_1:BLUE''',
    'predeployed_units': [
        # RED Ground Units (13 types) - Center-left for combat testing
        {'army': 'RED', 'type': 'INFANTRY', 'x': 5, 'y': 4},      # Close to center
        {'army': 'RED', 'type': 'MECH', 'x': 5, 'y': 5},          # Close to center
        {'army': 'RED', 'type': 'RECON', 'x': 4, 'y': 4},
        {'army': 'RED', 'type': 'TANK', 'x': 5, 'y': 6},          # Close to center
        {'army': 'RED', 'type': 'MEDIUMTANK', 'x': 4, 'y': 6},
        {'army': 'RED', 'type': 'NEOTANK', 'x': 3, 'y': 6},
        {'army': 'RED', 'type': 'MEGATANK', 'x': 0, 'y': 7},
        {'army': 'RED', 'type': 'APC', 'x': 1, 'y': 5},
        {'army': 'RED', 'type': 'ARTILLERY', 'x': 4, 'y': 5},     # In range of center
        {'army': 'RED', 'type': 'ROCKET', 'x': 2, 'y': 7},
        {'army': 'RED', 'type': 'MISSILE', 'x': 3, 'y': 7},
        {'army': 'RED', 'type': 'ANTIAIR', 'x': 3, 'y': 5},
        {'army': 'RED', 'type': 'PIPERUNNER', 'x': 1, 'y': 10},  # On pipe
        
        # RED Naval Units (6 types) - Water area
        {'army': 'RED', 'type': 'BATTLESHIP', 'x': 2, 'y': 1},
        {'army': 'RED', 'type': 'CRUISER', 'x': 3, 'y': 2},
        {'army': 'RED', 'type': 'SUB', 'x': 1, 'y': 1},
        {'army': 'RED', 'type': 'LANDER', 'x': 2, 'y': 2},
        {'army': 'RED', 'type': 'CARRIER', 'x': 1, 'y': 2},
        {'army': 'RED', 'type': 'BLACKBOAT', 'x': 3, 'y': 1},
        
        # RED Air Units (6 types) - Airport area
        {'army': 'RED', 'type': 'FIGHTER', 'x': 0, 'y': 3},
        {'army': 'RED', 'type': 'BOMBER', 'x': 1, 'y': 3},
        {'army': 'RED', 'type': 'BCOPTER', 'x': 2, 'y': 3},
        {'army': 'RED', 'type': 'TCOPTER', 'x': 3, 'y': 3},
        {'army': 'RED', 'type': 'STEALTH', 'x': 4, 'y': 3},
        {'army': 'RED', 'type': 'BLACKBOMB', 'x': 4, 'y': 4},
        
        # BLUE Ground Units (13 types) - Center-right for combat testing
        {'army': 'BLUE', 'type': 'INFANTRY', 'x': 9, 'y': 4},     # Close to center
        {'army': 'BLUE', 'type': 'MECH', 'x': 9, 'y': 5},         # Close to center
        {'army': 'BLUE', 'type': 'RECON', 'x': 10, 'y': 4},
        {'army': 'BLUE', 'type': 'TANK', 'x': 9, 'y': 6},         # Close to center
        {'army': 'BLUE', 'type': 'MEDIUMTANK', 'x': 10, 'y': 6},
        {'army': 'BLUE', 'type': 'NEOTANK', 'x': 11, 'y': 6},
        {'army': 'BLUE', 'type': 'MEGATANK', 'x': 14, 'y': 7},
        {'army': 'BLUE', 'type': 'APC', 'x': 13, 'y': 5},
        {'army': 'BLUE', 'type': 'ARTILLERY', 'x': 10, 'y': 5},   # In range of center
        {'army': 'BLUE', 'type': 'ROCKET', 'x': 12, 'y': 7},
        {'army': 'BLUE', 'type': 'MISSILE', 'x': 11, 'y': 7},
        {'army': 'BLUE', 'type': 'ANTIAIR', 'x': 11, 'y': 5},
        {'army': 'BLUE', 'type': 'PIPERUNNER', 'x': 13, 'y': 10}, # No pipe here, for error testing
        
        # BLUE Naval Units (6 types) - Water area
        {'army': 'BLUE', 'type': 'BATTLESHIP', 'x': 12, 'y': 1},
        {'army': 'BLUE', 'type': 'CRUISER', 'x': 11, 'y': 2},
        {'army': 'BLUE', 'type': 'SUB', 'x': 13, 'y': 1},
        {'army': 'BLUE', 'type': 'LANDER', 'x': 12, 'y': 2},
        {'army': 'BLUE', 'type': 'CARRIER', 'x': 13, 'y': 2},
        {'army': 'BLUE', 'type': 'BLACKBOAT', 'x': 11, 'y': 1},
        
        # BLUE Air Units (6 types) - Airport area
        {'army': 'BLUE', 'type': 'FIGHTER', 'x': 14, 'y': 3},
        {'army': 'BLUE', 'type': 'BOMBER', 'x': 13, 'y': 3},
        {'army': 'BLUE', 'type': 'BCOPTER', 'x': 12, 'y': 3},
        {'army': 'BLUE', 'type': 'TCOPTER', 'x': 11, 'y': 3},
        {'army': 'BLUE', 'type': 'STEALTH', 'x': 10, 'y': 3},
        {'army': 'BLUE', 'type': 'BLACKBOMB', 'x': 10, 'y': 4},
        
        # Additional units in combat range for immediate testing
        {'army': 'RED', 'type': 'INFANTRY', 'x': 6, 'y': 5, 'hp': 80},   # Adjacent combat
        {'army': 'BLUE', 'type': 'INFANTRY', 'x': 7, 'y': 5, 'hp': 80},  # Adjacent combat
        {'army': 'RED', 'type': 'TANK', 'x': 6, 'y': 6},                 # Close combat
        {'army': 'BLUE', 'type': 'TANK', 'x': 8, 'y': 6},                # Close combat
    ]
}

# Transport Test Map - Nested transport scenarios
TRANSPORT_TEST_MAP = {
    'name': 'Transport Test Zone - Nested Loading',
    'map_data': '''RED,BLUE
PORT:RED,SEA,SEA,SEA,BEACH_W,BEACH_N,BEACH_N,BEACH_E,SEA,SEA,SEA,SEA,PORT:BLUE
SEA,SEA,REEF,SEA,SEA,BEACH_W,BEACH_E,SEA,SEA,REEF,SEA,SEA,SEA
SEA,REEF,SEA,SEA,SEA,BEACH_W,BEACH_E,SEA,SEA,SEA,REEF,SEA,SEA
BEACH_W,BEACH_SW,SEA,SEA,SEA,BEACH_W,BEACH_E,SEA,SEA,SEA,SEA,BEACH_SE,BEACH_E
FACTORY:RED,ROAD_HORT,BEACH_N,BEACH_N,BEACH_N,BEACH_SW,BEACH_SE,BEACH_N,BEACH_N,BEACH_N,BEACH_N,ROAD_HORT,FACTORY:BLUE
PLAIN,ROAD_VERT,PLAIN,PLAIN,PLAIN,ROAD_VERT,ROAD_VERT,PLAIN,PLAIN,PLAIN,PLAIN,ROAD_VERT,PLAIN
CITY,ROAD_VERT,WOOD,MOUNTAIN,PLAIN,ROAD_VERT,ROAD_VERT,PLAIN,MOUNTAIN,WOOD,PLAIN,ROAD_VERT,CITY
AIRPORT:RED,ROAD_SW,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_SE,ROAD_SW,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_SE,AIRPORT:BLUE
PLAIN,PLAIN,CITY,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,CITY,PLAIN,PLAIN,PLAIN
BASE_TOWER_1:RED,CITY:RED,PLAIN,PLAIN,CITY,PLAIN,PLAIN,CITY,PLAIN,PLAIN,CITY:BLUE,CITY:BLUE,BASE_TOWER_1:BLUE''',
    'predeployed_units': [
        # RED Nested Transport Scenario - Loaded APC to board Lander
        {'army': 'RED', 'type': 'APC', 'x': 3, 'y': 4, 'loaded_units': ['INFANTRY', 'MECH']},
        {'army': 'RED', 'type': 'LANDER', 'x': 2, 'y': 3},  # Ready to load the APC
        {'army': 'RED', 'type': 'INFANTRY', 'x': 2, 'y': 5},  # Extra infantry
        {'army': 'RED', 'type': 'MECH', 'x': 3, 'y': 5},      # Extra mech
        
        # RED Nested Transport Scenario - Loaded TCOPTER to board Cruiser
        {'army': 'RED', 'type': 'TCOPTER', 'x': 0, 'y': 7, 'loaded_units': ['INFANTRY']},
        {'army': 'RED', 'type': 'CRUISER', 'x': 3, 'y': 1},   # Ready to load the TCOPTER
        
        # Additional RED transport units for testing
        {'army': 'RED', 'type': 'BLACKBOAT', 'x': 1, 'y': 2}, # Can repair and carry infantry
        {'army': 'RED', 'type': 'CARRIER', 'x': 2, 'y': 1},   # Can carry air units
        
        # BLUE Nested Transport Scenario - Loaded APC to board Lander
        {'army': 'BLUE', 'type': 'APC', 'x': 9, 'y': 4, 'loaded_units': ['INFANTRY']},
        {'army': 'BLUE', 'type': 'LANDER', 'x': 10, 'y': 3},  # Ready to load the APC
        
        # BLUE Nested Transport Scenario - Loaded TCOPTER to board Cruiser
        {'army': 'BLUE', 'type': 'TCOPTER', 'x': 12, 'y': 7, 'loaded_units': ['MECH']},
        {'army': 'BLUE', 'type': 'CRUISER', 'x': 9, 'y': 1},  # Ready to load the TCOPTER
        
        # Additional BLUE units for transport testing
        {'army': 'BLUE', 'type': 'INFANTRY', 'x': 10, 'y': 5},
        {'army': 'BLUE', 'type': 'MECH', 'x': 11, 'y': 5},
        {'army': 'BLUE', 'type': 'FIGHTER', 'x': 11, 'y': 7}, # For carrier testing
        {'army': 'BLUE', 'type': 'BOMBER', 'x': 10, 'y': 7},  # For carrier testing
        {'army': 'BLUE', 'type': 'BCOPTER', 'x': 9, 'y': 7},  # Can board cruiser/carrier
        
        # Ground vehicles for lander testing
        {'army': 'RED', 'type': 'TANK', 'x': 1, 'y': 5},
        {'army': 'RED', 'type': 'RECON', 'x': 1, 'y': 6},
        {'army': 'BLUE', 'type': 'ARTILLERY', 'x': 11, 'y': 6},
        {'army': 'BLUE', 'type': 'ANTIAIR', 'x': 10, 'y': 6},
    ]
}

# Victory Test Map - HQ capture and property control scenarios
VICTORY_TEST_MAP = {
    'name': 'Victory Conditions Arena',
    'map_data': '''RED,BLUE
BASE_TOWER_1:RED,CITY:RED,CITY:RED,PLAIN,ROAD_HORT,ROAD_HORT,PLAIN,CITY:BLUE,CITY:BLUE,BASE_TOWER_1:BLUE
FACTORY:RED,PLAIN,PLAIN,PLAIN,ROAD_VERT,ROAD_VERT,PLAIN,PLAIN,PLAIN,FACTORY:BLUE
CITY:RED,WOOD,PLAIN,PLAIN,ROAD_VERT,ROAD_VERT,PLAIN,PLAIN,WOOD,CITY:BLUE
PLAIN,PLAIN,MOUNTAIN,PLAIN,ROAD_VERT,ROAD_VERT,PLAIN,MOUNTAIN,PLAIN,PLAIN
PLAIN,PLAIN,PLAIN,CITY,ROAD_VERT,ROAD_VERT,CITY,PLAIN,PLAIN,PLAIN
AIRPORT:RED,PLAIN,PLAIN,PLAIN,ROAD_VERT,ROAD_VERT,PLAIN,PLAIN,PLAIN,AIRPORT:BLUE
CITY:RED,CITY:RED,PLAIN,PLAIN,ROAD_SW,ROAD_SE,PLAIN,PLAIN,CITY:BLUE,CITY:BLUE
PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN''',
    'predeployed_units': [
        # RED units positioned for quick HQ capture test
        {'army': 'RED', 'type': 'INFANTRY', 'x': 4, 'y': 0, 'hp': 100},  # 1 turn from BLUE HQ
        {'army': 'RED', 'type': 'MECH', 'x': 3, 'y': 1, 'hp': 100},     # Backup capture unit
        {'army': 'RED', 'type': 'INFANTRY', 'x': 2, 'y': 0, 'hp': 50},  # Damaged unit for capture HP test
        
        # BLUE units positioned for defense and counter-capture
        {'army': 'BLUE', 'type': 'INFANTRY', 'x': 5, 'y': 0, 'hp': 100}, # 1 turn from RED HQ
        {'army': 'BLUE', 'type': 'MECH', 'x': 6, 'y': 1, 'hp': 100},    # Backup capture unit
        {'army': 'BLUE', 'type': 'TANK', 'x': 7, 'y': 0, 'hp': 100},    # HQ defender
        
        # Units for property control victory testing
        {'army': 'RED', 'type': 'INFANTRY', 'x': 0, 'y': 2},  # Near RED city
        {'army': 'RED', 'type': 'INFANTRY', 'x': 0, 'y': 6},  # Near RED city
        {'army': 'RED', 'type': 'INFANTRY', 'x': 3, 'y': 4},  # Near neutral city
        
        {'army': 'BLUE', 'type': 'INFANTRY', 'x': 9, 'y': 2}, # Near BLUE city
        {'army': 'BLUE', 'type': 'INFANTRY', 'x': 9, 'y': 6}, # Near BLUE city
        {'army': 'BLUE', 'type': 'INFANTRY', 'x': 6, 'y': 4}, # Near neutral city
        
        # Units for elimination victory testing
        {'army': 'RED', 'type': 'TANK', 'x': 1, 'y': 3, 'hp': 10},      # Low HP for easy elimination
        {'army': 'RED', 'type': 'RECON', 'x': 2, 'y': 3, 'hp': 20},     # Low HP
        {'army': 'BLUE', 'type': 'TANK', 'x': 8, 'y': 3, 'hp': 10},     # Low HP
        {'army': 'BLUE', 'type': 'RECON', 'x': 7, 'y': 3, 'hp': 20},    # Low HP
    ]
}

# Movement Test Map - Testing all movement types and terrain
MOVEMENT_TEST_MAP = {
    'name': 'Movement Test Terrain',
    'map_data': '''RED,BLUE
PLAIN,PLAIN,PLAIN,WOOD,WOOD,MOUNTAIN,MOUNTAIN,CITY,CITY,PLAIN,PLAIN,PLAIN
ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT,ROAD_HORT
PLAIN,RIVER_VERT,PLAIN,RIVER_VERT,PLAIN,RIVER_VERT,PLAIN,RIVER_VERT,PLAIN,RIVER_VERT,PLAIN,PLAIN
SEA,SEA,SEA,REEF,SEA,SEA,SEA,SEA,REEF,SEA,SEA,SEA
BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,HBridge,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N,BEACH_N
PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,ROAD_VERT,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN
PIPE_END_W,PIPE_HORT,PIPE_HORT,PIPE_HORT,PIPE_HORT,PIPE_HORT,PIPE_HORT,PIPE_HORT,PIPE_HORT,PIPE_HORT,PIPE_HORT,PIPE_END_E
FACTORY:RED,AIRPORT:RED,PORT:RED,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PLAIN,PORT:BLUE,AIRPORT:BLUE,FACTORY:BLUE''',
    'predeployed_units': [
        # Test different movement types on various terrains
        {'army': 'RED', 'type': 'INFANTRY', 'x': 0, 'y': 0},     # BOOTS movement
        {'army': 'RED', 'type': 'TANK', 'x': 1, 'y': 0},         # TREADS movement
        {'army': 'RED', 'type': 'RECON', 'x': 2, 'y': 0},        # TYRES movement
        {'army': 'RED', 'type': 'BATTLESHIP', 'x': 0, 'y': 3},   # SEA movement
        {'army': 'RED', 'type': 'FIGHTER', 'x': 1, 'y': 7},      # AIR movement
        {'army': 'RED', 'type': 'LANDER', 'x': 1, 'y': 3},       # LANDER movement
        {'army': 'RED', 'type': 'MECH', 'x': 3, 'y': 0},         # FOOT movement
        {'army': 'RED', 'type': 'PIPERUNNER', 'x': 0, 'y': 6},   # PIPE movement
        
        # Units to test movement restrictions
        {'army': 'BLUE', 'type': 'INFANTRY', 'x': 11, 'y': 0},   # Test mountain/wood
        {'army': 'BLUE', 'type': 'TANK', 'x': 10, 'y': 0},      # Test river blocking
        {'army': 'BLUE', 'type': 'ARTILLERY', 'x': 9, 'y': 0},   # Test indirect movement
        {'army': 'BLUE', 'type': 'SUB', 'x': 11, 'y': 3},       # Test reef/sea
        {'army': 'BLUE', 'type': 'BCOPTER', 'x': 10, 'y': 7},   # Test air over all
    ]
}

def get_test_map(map_name):
    """Get a test map by name"""
    maps = {
        'combat': COMBAT_TEST_MAP,
        'transport': TRANSPORT_TEST_MAP,
        'victory': VICTORY_TEST_MAP,
        'movement': MOVEMENT_TEST_MAP
    }
    return maps.get(map_name)

def create_predeployed_units(game_manager, unit_definitions):
    """Create predeployed units on the game board
    
    Args:
        game_manager: The GameManager instance
        unit_definitions: List of unit definition dicts with army, type, x, y, etc.
    """
    from unit import Unit, UnitType, Army
    
    deployed_count = 0
    for unit_def in unit_definitions:
        try:
            # Parse army and unit type
            army = Army[unit_def['army'].upper()]
            unit_type = UnitType[unit_def['type'].upper()]
            
            # Get unit config
            unit_config = game_manager.config.units.get(unit_def['type'])
            if not unit_config:
                print(f"Warning: No config for unit type {unit_def['type']}")
                continue
            
            # Create the unit
            unit = Unit.create(army, unit_type, unit_config)
            
            # Set custom properties
            if 'hp' in unit_def:
                unit.status.hp = unit_def['hp']
            if 'fuel' in unit_def:
                unit.status.fuel = unit_def['fuel']
            else:
                unit.status.fuel = unit_config.fuel
            if 'ammo' in unit_def:
                unit.status.ammo = unit_def['ammo']
            else:
                unit.status.ammo = unit_config.ammo if hasattr(unit_config, 'ammo') else None
            
            # Handle loaded units for transports
            if 'loaded_units' in unit_def and unit.capacity() > 0:
                loaded_units = []
                for loaded_type in unit_def['loaded_units']:
                    loaded_unit_type = UnitType[loaded_type.upper()]
                    loaded_config = game_manager.config.units.get(loaded_type)
                    if loaded_config:
                        loaded_unit = Unit.create(army, loaded_unit_type, loaded_config)
                        loaded_unit.status.fuel = loaded_config.fuel
                        loaded_units.append(loaded_unit)
                
                # Set the transport's cargo
                unit.cargo1 = loaded_units[0] if len(loaded_units) > 0 else None
                unit.cargo2 = loaded_units[1] if len(loaded_units) > 1 else None
            
            # Place unit on board
            x, y = unit_def['x'], unit_def['y']
            
            # Check if position is valid
            if x >= 0 and y >= 0 and x < game_manager.board.width and y < game_manager.board.height:
                tile_index = y * game_manager.board.width + x
                tile = game_manager.board.grid[tile_index]
                
                if not tile.unit:  # Only place if tile is empty
                    tile.unit = unit
                    deployed_count += 1
                    
                    # Mark unit as ready for testing
                    unit.can_move = True
                    unit.can_attack = True
                    unit.can_capture = unit.type in {UnitType.INFANTRY, UnitType.MECH}
                    
                    # Update army unit count
                    if army == Army.RED:
                        game_manager.board.total_red_troops += 1
                    else:
                        game_manager.board.total_blue_troops += 1
                else:
                    print(f"Warning: Position ({x},{y}) already occupied, skipping {unit_def['type']}")
            else:
                print(f"Warning: Invalid position ({x},{y}) for {unit_def['type']}")
                
        except Exception as e:
            print(f"Error deploying {unit_def}: {e}")
    
    print(f"✅ Deployed {deployed_count}/{len(unit_definitions)} units")
    return deployed_count
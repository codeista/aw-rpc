"""
Test map templates with predeployed units support
Each map is tailored for specific test scenarios with comprehensive unit coverage
"""

# Combat Test Map - ALL 25 unit types represented
COMBAT_TEST_MAP = {
    'name': 'Combat Test Arena - All Units',
    'map_data': '''2
15,12
FACTORY:0 CITY PLAIN PLAIN MOUNTAIN PLAIN PLAIN PLAIN PLAIN PLAIN MOUNTAIN PLAIN PLAIN CITY FACTORY:1
PORT:0 SEA SEA BEACH_W PLAIN WOOD ROAD_HORT ROAD_HORT ROAD_HORT WOOD PLAIN BEACH_E SEA SEA PORT:1
SEA SEA SEA BEACH_W PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN BEACH_E SEA SEA SEA
AIRPORT:0 PLAIN PLAIN PLAIN CITY MOUNTAIN PLAIN PLAIN PLAIN MOUNTAIN CITY PLAIN PLAIN PLAIN AIRPORT:1
PLAIN ROAD_VERT PLAIN WOOD PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN WOOD PLAIN ROAD_VERT PLAIN
PLAIN ROAD_VERT PLAIN PLAIN PLAIN ROAD_HORT CITY COM_TOWER CITY ROAD_HORT PLAIN PLAIN PLAIN ROAD_VERT PLAIN
FACTORY:0 ROAD_VERT WOOD PLAIN MOUNTAIN PLAIN PLAIN PLAIN PLAIN PLAIN MOUNTAIN PLAIN WOOD ROAD_VERT FACTORY:1
CITY:0 ROAD_VERT PLAIN PLAIN PLAIN WOOD PLAIN PLAIN PLAIN WOOD PLAIN PLAIN PLAIN ROAD_VERT CITY:1
PLAIN ROAD_SW ROAD_HORT ROAD_HORT ROAD_HORT ROAD_HORT ROAD_HORT MISSILE_SILO ROAD_HORT ROAD_HORT ROAD_HORT ROAD_HORT ROAD_HORT ROAD_SE PLAIN
PLAIN PLAIN MOUNTAIN PLAIN CITY PLAIN PLAIN PLAIN PLAIN PLAIN CITY PLAIN MOUNTAIN PLAIN PLAIN
PIPE_N PIPE_VERT PIPE_S PLAIN PLAIN WOOD PLAIN PLAIN PLAIN WOOD PLAIN PLAIN PLAIN PLAIN PLAIN
BASE_TOWER_1:0 CITY PLAIN PLAIN CITY PLAIN PLAIN PLAIN PLAIN PLAIN CITY PLAIN PLAIN CITY BASE_TOWER_1:1''',
    'predeployed_units': [
        # Player 0 Ground Units (13 types) - Center-left for combat testing
        {'player': 0, 'type': 'INFANTRY', 'x': 5, 'y': 4},      # Close to center
        {'player': 0, 'type': 'MECH', 'x': 5, 'y': 5},          # Close to center
        {'player': 0, 'type': 'RECON', 'x': 4, 'y': 4},
        {'player': 0, 'type': 'TANK', 'x': 5, 'y': 6},          # Close to center
        {'player': 0, 'type': 'MEDIUMTANK', 'x': 4, 'y': 6},
        {'player': 0, 'type': 'NEOTANK', 'x': 3, 'y': 6},
        {'player': 0, 'type': 'MEGATANK', 'x': 0, 'y': 7},
        {'player': 0, 'type': 'APC', 'x': 1, 'y': 5},
        {'player': 0, 'type': 'ARTILLERY', 'x': 4, 'y': 5},     # In range of center
        {'player': 0, 'type': 'ROCKET', 'x': 2, 'y': 7},
        {'player': 0, 'type': 'MISSILE', 'x': 3, 'y': 7},
        {'player': 0, 'type': 'ANTIAIR', 'x': 3, 'y': 5},
        {'player': 0, 'type': 'PIPERUNNER', 'x': 1, 'y': 10},  # On pipe
        
        # Player 0 Naval Units (6 types) - Water area
        {'player': 0, 'type': 'BATTLESHIP', 'x': 2, 'y': 1},
        {'player': 0, 'type': 'CRUISER', 'x': 3, 'y': 2},
        {'player': 0, 'type': 'SUB', 'x': 1, 'y': 1},
        {'player': 0, 'type': 'LANDER', 'x': 2, 'y': 2},
        {'player': 0, 'type': 'CARRIER', 'x': 1, 'y': 2},
        {'player': 0, 'type': 'BLACKBOAT', 'x': 3, 'y': 1},
        
        # Player 0 Air Units (6 types) - Airport area
        {'player': 0, 'type': 'FIGHTER', 'x': 0, 'y': 3},
        {'player': 0, 'type': 'BOMBER', 'x': 1, 'y': 3},
        {'player': 0, 'type': 'BCOPTER', 'x': 2, 'y': 3},
        {'player': 0, 'type': 'TCOPTER', 'x': 3, 'y': 3},
        {'player': 0, 'type': 'STEALTH', 'x': 4, 'y': 3},
        {'player': 0, 'type': 'BLACKBOMB', 'x': 4, 'y': 4},
        
        # Player 1 Ground Units (13 types) - Center-right for combat testing
        {'player': 1, 'type': 'INFANTRY', 'x': 9, 'y': 4},     # Close to center
        {'player': 1, 'type': 'MECH', 'x': 9, 'y': 5},         # Close to center
        {'player': 1, 'type': 'RECON', 'x': 10, 'y': 4},
        {'player': 1, 'type': 'TANK', 'x': 9, 'y': 6},         # Close to center
        {'player': 1, 'type': 'MEDIUMTANK', 'x': 10, 'y': 6},
        {'player': 1, 'type': 'NEOTANK', 'x': 11, 'y': 6},
        {'player': 1, 'type': 'MEGATANK', 'x': 14, 'y': 7},
        {'player': 1, 'type': 'APC', 'x': 13, 'y': 5},
        {'player': 1, 'type': 'ARTILLERY', 'x': 10, 'y': 5},   # In range of center
        {'player': 1, 'type': 'ROCKET', 'x': 12, 'y': 7},
        {'player': 1, 'type': 'MISSILE', 'x': 11, 'y': 7},
        {'player': 1, 'type': 'ANTIAIR', 'x': 11, 'y': 5},
        {'player': 1, 'type': 'PIPERUNNER', 'x': 13, 'y': 10}, # No pipe here, for error testing
        
        # Player 1 Naval Units (6 types) - Water area
        {'player': 1, 'type': 'BATTLESHIP', 'x': 12, 'y': 1},
        {'player': 1, 'type': 'CRUISER', 'x': 11, 'y': 2},
        {'player': 1, 'type': 'SUB', 'x': 13, 'y': 1},
        {'player': 1, 'type': 'LANDER', 'x': 12, 'y': 2},
        {'player': 1, 'type': 'CARRIER', 'x': 13, 'y': 2},
        {'player': 1, 'type': 'BLACKBOAT', 'x': 11, 'y': 1},
        
        # Player 1 Air Units (6 types) - Airport area
        {'player': 1, 'type': 'FIGHTER', 'x': 14, 'y': 3},
        {'player': 1, 'type': 'BOMBER', 'x': 13, 'y': 3},
        {'player': 1, 'type': 'BCOPTER', 'x': 12, 'y': 3},
        {'player': 1, 'type': 'TCOPTER', 'x': 11, 'y': 3},
        {'player': 1, 'type': 'STEALTH', 'x': 10, 'y': 3},
        {'player': 1, 'type': 'BLACKBOMB', 'x': 10, 'y': 4},
        
        # Additional units in combat range for immediate testing
        {'player': 0, 'type': 'INFANTRY', 'x': 6, 'y': 5, 'hp': 80},   # Adjacent combat
        {'player': 1, 'type': 'INFANTRY', 'x': 7, 'y': 5, 'hp': 80},  # Adjacent combat
        {'player': 0, 'type': 'TANK', 'x': 6, 'y': 6},                 # Close combat
        {'player': 1, 'type': 'TANK', 'x': 8, 'y': 6},                # Close combat
    ]
}

# Transport Test Map - Nested transport scenarios
TRANSPORT_TEST_MAP = {
    'name': 'Transport Test Zone - Nested Loading',
    'map_data': '''2
13,10
PORT:0 SEA SEA SEA BEACH_W BEACH_N BEACH_N BEACH_E SEA SEA SEA SEA PORT:1
SEA SEA REEF SEA SEA BEACH_W BEACH_E SEA SEA REEF SEA SEA SEA
SEA REEF SEA SEA SEA BEACH_W BEACH_E SEA SEA SEA REEF SEA SEA
BEACH_W BEACH_SW SEA SEA SEA BEACH_W BEACH_E SEA SEA SEA SEA BEACH_SE BEACH_E
FACTORY:0 ROAD_HORT BEACH_N BEACH_N BEACH_N BEACH_SW BEACH_SE BEACH_N BEACH_N BEACH_N BEACH_N ROAD_HORT FACTORY:1
PLAIN ROAD_VERT PLAIN PLAIN PLAIN ROAD_VERT ROAD_VERT PLAIN PLAIN PLAIN PLAIN ROAD_VERT PLAIN
CITY ROAD_VERT WOOD MOUNTAIN PLAIN ROAD_VERT ROAD_VERT PLAIN MOUNTAIN WOOD PLAIN ROAD_VERT CITY
AIRPORT:0 ROAD_SW ROAD_HORT ROAD_HORT ROAD_HORT ROAD_SE ROAD_SW ROAD_HORT ROAD_HORT ROAD_HORT ROAD_HORT ROAD_SE AIRPORT:1
PLAIN PLAIN CITY PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN CITY PLAIN PLAIN PLAIN
BASE_TOWER_1:0 CITY:0 PLAIN PLAIN CITY PLAIN PLAIN CITY PLAIN PLAIN CITY:1 CITY:1 BASE_TOWER_1:1''',
    'predeployed_units': [
        # Player 0 Nested Transport Scenario - Loaded APC to board Lander
        {'player': 0, 'type': 'APC', 'x': 3, 'y': 4, 'loaded_units': ['INFANTRY', 'MECH']},
        {'player': 0, 'type': 'LANDER', 'x': 2, 'y': 3},  # Ready to load the APC
        {'player': 0, 'type': 'INFANTRY', 'x': 2, 'y': 5},  # Extra infantry
        {'player': 0, 'type': 'MECH', 'x': 3, 'y': 5},      # Extra mech
        
        # Player 0 Nested Transport Scenario - Loaded TCOPTER to board Cruiser
        {'player': 0, 'type': 'TCOPTER', 'x': 0, 'y': 7, 'loaded_units': ['INFANTRY']},
        {'player': 0, 'type': 'CRUISER', 'x': 3, 'y': 1},   # Ready to load the TCOPTER
        
        # Additional Player 0 transport units for testing
        {'player': 0, 'type': 'BLACKBOAT', 'x': 1, 'y': 2}, # Can repair and carry infantry
        {'player': 0, 'type': 'CARRIER', 'x': 2, 'y': 1},   # Can carry air units
        
        # Player 1 Nested Transport Scenario - Loaded APC to board Lander
        {'player': 1, 'type': 'APC', 'x': 9, 'y': 4, 'loaded_units': ['INFANTRY']},
        {'player': 1, 'type': 'LANDER', 'x': 10, 'y': 3},  # Ready to load the APC
        
        # Player 1 Nested Transport Scenario - Loaded TCOPTER to board Cruiser
        {'player': 1, 'type': 'TCOPTER', 'x': 12, 'y': 7, 'loaded_units': ['MECH']},
        {'player': 1, 'type': 'CRUISER', 'x': 9, 'y': 1},  # Ready to load the TCOPTER
        
        # Additional Player 1 units for transport testing
        {'player': 1, 'type': 'INFANTRY', 'x': 10, 'y': 5},
        {'player': 1, 'type': 'MECH', 'x': 11, 'y': 5},
        {'player': 1, 'type': 'FIGHTER', 'x': 11, 'y': 7}, # For carrier testing
        {'player': 1, 'type': 'BOMBER', 'x': 10, 'y': 7},  # For carrier testing
        {'player': 1, 'type': 'BCOPTER', 'x': 9, 'y': 7},  # Can board cruiser/carrier
        
        # Ground vehicles for lander testing
        {'player': 0, 'type': 'TANK', 'x': 1, 'y': 5},
        {'player': 0, 'type': 'RECON', 'x': 1, 'y': 6},
        {'player': 1, 'type': 'ARTILLERY', 'x': 11, 'y': 6},
        {'player': 1, 'type': 'ANTIAIR', 'x': 10, 'y': 6},
    ]
}

# Victory Test Map - HQ capture and property control scenarios
VICTORY_TEST_MAP = {
    'name': 'Victory Conditions Arena',
    'map_data': '''2
10,8
BASE_TOWER_1:0 CITY:0 CITY:0 PLAIN ROAD_HORT ROAD_HORT PLAIN CITY:1 CITY:1 BASE_TOWER_1:1
FACTORY:0 PLAIN PLAIN PLAIN ROAD_VERT ROAD_VERT PLAIN PLAIN PLAIN FACTORY:1
CITY:0 WOOD PLAIN PLAIN ROAD_VERT ROAD_VERT PLAIN PLAIN WOOD CITY:1
PLAIN PLAIN MOUNTAIN PLAIN ROAD_VERT ROAD_VERT PLAIN MOUNTAIN PLAIN PLAIN
PLAIN PLAIN PLAIN CITY ROAD_VERT ROAD_VERT CITY PLAIN PLAIN PLAIN
AIRPORT:0 PLAIN PLAIN PLAIN ROAD_VERT ROAD_VERT PLAIN PLAIN PLAIN AIRPORT:1
CITY:0 CITY:0 PLAIN PLAIN ROAD_SW ROAD_SE PLAIN PLAIN CITY:1 CITY:1
PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN''',
    'predeployed_units': [
        # Player 0 units positioned for quick HQ capture test
        {'player': 0, 'type': 'INFANTRY', 'x': 4, 'y': 0, 'hp': 100},  # 1 turn from Player 1 HQ
        {'player': 0, 'type': 'MECH', 'x': 3, 'y': 1, 'hp': 100},     # Backup capture unit
        {'player': 0, 'type': 'INFANTRY', 'x': 2, 'y': 0, 'hp': 50},  # Damaged unit for capture HP test
        
        # Player 1 units positioned for defense and counter-capture
        {'player': 1, 'type': 'INFANTRY', 'x': 5, 'y': 0, 'hp': 100}, # 1 turn from Player 0 HQ
        {'player': 1, 'type': 'MECH', 'x': 6, 'y': 1, 'hp': 100},    # Backup capture unit
        {'player': 1, 'type': 'TANK', 'x': 7, 'y': 0, 'hp': 100},    # HQ defender
        
        # Units for property control victory testing
        {'player': 0, 'type': 'INFANTRY', 'x': 0, 'y': 2},  # Near Player 0 city
        {'player': 0, 'type': 'INFANTRY', 'x': 0, 'y': 6},  # Near Player 0 city
        {'player': 0, 'type': 'INFANTRY', 'x': 3, 'y': 4},  # Near neutral city
        
        {'player': 1, 'type': 'INFANTRY', 'x': 9, 'y': 2}, # Near Player 1 city
        {'player': 1, 'type': 'INFANTRY', 'x': 9, 'y': 6}, # Near Player 1 city
        {'player': 1, 'type': 'INFANTRY', 'x': 6, 'y': 4}, # Near neutral city
        
        # Units for elimination victory testing
        {'player': 0, 'type': 'TANK', 'x': 1, 'y': 3, 'hp': 10},      # Low HP for easy elimination
        {'player': 0, 'type': 'RECON', 'x': 2, 'y': 3, 'hp': 20},     # Low HP
        {'player': 1, 'type': 'TANK', 'x': 8, 'y': 3, 'hp': 10},     # Low HP
        {'player': 1, 'type': 'RECON', 'x': 7, 'y': 3, 'hp': 20},    # Low HP
    ]
}

# Movement Test Map - Testing all movement types and terrain
MOVEMENT_TEST_MAP = {
    'name': 'Movement Test Terrain',
    'map_data': '''2
12,8
PLAIN PLAIN PLAIN WOOD WOOD MOUNTAIN MOUNTAIN CITY CITY PLAIN PLAIN PLAIN
ROAD_HORT ROAD_HORT ROAD_HORT ROAD_HORT ROAD_HORT ROAD_HORT ROAD_HORT ROAD_HORT ROAD_HORT ROAD_HORT ROAD_HORT ROAD_HORT
PLAIN RIVER_VERT PLAIN RIVER_VERT PLAIN RIVER_VERT PLAIN RIVER_VERT PLAIN RIVER_VERT PLAIN PLAIN
SEA SEA SEA REEF SEA SEA SEA SEA REEF SEA SEA SEA
BEACH_N BEACH_N BEACH_N BEACH_N BEACH_N HBridge BEACH_N BEACH_N BEACH_N BEACH_N BEACH_N BEACH_N
PLAIN PLAIN PLAIN PLAIN PLAIN ROAD_VERT PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN
PIPE_END_W PIPE_HORT PIPE_HORT PIPE_HORT PIPE_HORT PIPE_HORT PIPE_HORT PIPE_HORT PIPE_HORT PIPE_HORT PIPE_HORT PIPE_END_E
FACTORY:0 AIRPORT:0 PORT:0 PLAIN PLAIN PLAIN PLAIN PLAIN PLAIN PORT:1 AIRPORT:1 FACTORY:1''',
    'predeployed_units': [
        # Test different movement types on various terrains
        {'player': 0, 'type': 'INFANTRY', 'x': 0, 'y': 0},     # BOOTS movement
        {'player': 0, 'type': 'TANK', 'x': 1, 'y': 0},         # TREADS movement
        {'player': 0, 'type': 'RECON', 'x': 2, 'y': 0},        # TYRES movement
        {'player': 0, 'type': 'BATTLESHIP', 'x': 0, 'y': 3},   # SEA movement
        {'player': 0, 'type': 'FIGHTER', 'x': 1, 'y': 7},      # AIR movement
        {'player': 0, 'type': 'LANDER', 'x': 1, 'y': 3},       # LANDER movement
        {'player': 0, 'type': 'MECH', 'x': 3, 'y': 0},         # FOOT movement
        {'player': 0, 'type': 'PIPERUNNER', 'x': 0, 'y': 6},   # PIPE movement
        
        # Units to test movement restrictions
        {'player': 1, 'type': 'INFANTRY', 'x': 11, 'y': 0},   # Test mountain/wood
        {'player': 1, 'type': 'TANK', 'x': 10, 'y': 0},      # Test river blocking
        {'player': 1, 'type': 'ARTILLERY', 'x': 9, 'y': 0},   # Test indirect movement
        {'player': 1, 'type': 'SUB', 'x': 11, 'y': 3},       # Test reef/sea
        {'player': 1, 'type': 'BCOPTER', 'x': 10, 'y': 7},   # Test air over all
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
        unit_definitions: List of unit definition dicts with player, type, x, y, etc.
    """
    from unit import Unit, UnitType
    
    deployed_count = 0
    for unit_def in unit_definitions:
        try:
            # Get player slot and map to army
            player_slot = unit_def['player']
            army = game_manager.board.get_army_for_player(player_slot)
            if not army:
                print(f"Warning: No army assigned to player slot {player_slot}")
                continue
                
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
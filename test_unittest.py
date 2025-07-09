'''[This is a suite of tests using unittest ]'''

import unittest
import app
import random
from app_core import app as _app, db


print('Running unit tests....')

# vars
letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
game = ''.join(random.choice(letters) for i in range(10))


''' Test class with mutiple tests;
    unit create and unit move rpc call'''


class Test_RPC_unit_create(unittest.TestCase):

    def setUp(self):
        with _app.app_context():
            # create tables
            db.create_all()
            # create game
            app.game_create_rpc(game)
            print(f"Created game: {game}")
            '''setup for unit_create'''

    def test_unit_create(self):
        with _app.app_context():
            print('Testing unit creation')
            self.assertEqual(app.unit_create_rpc(game, 'RED', 'INFANTRY', 4, 5),
                            app.tile_rpc(game, 4, 5))

    def test_unit_move(self):
        with _app.app_context():
            print('Testing unit move')
            app.unit_create_rpc(game, 'RED', 'INFANTRY', 4, 5)
            app.army_end_turn_rpc(game)
            app.army_end_turn_rpc(game)
            self.assertEqual(app.unit_move_rpc(game, 4, 5, 4, 6), app.tile_rpc(game, 4, 6))

    def tearDown(self):
        with _app.app_context():
            app.game_delete_rpc(game)

class Test_RPC_unit_movement(unittest.TestCase):
    
    def setUp(self):
        with _app.app_context():
            db.create_all()
            app.game_create_rpc(game)
            # Create a unit for movement testing
            app.unit_create_rpc(game, 'RED', 'INFANTRY', 4, 5)
            app.army_end_turn_rpc(game)
            app.army_end_turn_rpc(game)
    
    def test_basic_movement(self):
        """Test basic unit movement to adjacent tiles"""
        with _app.app_context():
            print('Testing basic unit movement')
            result = app.unit_move_rpc(game, 4, 5, 4, 6)
            self.assertEqual(result['unit']['army'], 'RED')
            self.assertEqual(result['x'], 4)
            self.assertEqual(result['y'], 6)
    
    def test_movement_fuel_consumption(self):
        """Test that movement consumes fuel"""
        with _app.app_context():
            print('Testing fuel consumption during movement')
            original_tile = app.tile_rpc(game, 4, 5)
            original_fuel = original_tile['unit']['status']['fuel']
            
            app.unit_move_rpc(game, 4, 5, 4, 6)
            moved_tile = app.tile_rpc(game, 4, 6)
            new_fuel = moved_tile['unit']['status']['fuel']
            
            self.assertLess(new_fuel, original_fuel)
    
    def test_invalid_movement(self):
        """Test that invalid movements are rejected"""
        with _app.app_context():
            print('Testing invalid movement rejection')
            with self.assertRaises(Exception):
                # Try to move too far
                app.unit_move_rpc(game, 4, 5, 10, 10)
    
    def tearDown(self):
        with _app.app_context():
            app.game_delete_rpc(game)

class Test_RPC_transport_system(unittest.TestCase):
    
    def setUp(self):
        with _app.app_context():
            db.create_all()
            app.game_create_rpc(game)
            # Create APC and Infantry for transport testing
            app.unit_create_rpc(game, 'RED', 'APC', 5, 5)
            app.unit_create_rpc(game, 'RED', 'INFANTRY', 5, 6)
            app.army_end_turn_rpc(game)
            app.army_end_turn_rpc(game)
    
    def test_unit_loading(self):
        """Test loading infantry into APC"""
        with _app.app_context():
            print('Testing unit loading into transport')
            result = app.unit_load_rpc(game, 5, 6, 5, 5)  # Load infantry into APC
            
            # Check APC has cargo
            apc_tile = app.tile_rpc(game, 5, 5)
            self.assertIsNotNone(apc_tile['unit']['status']['cargo'])
            self.assertGreater(len(apc_tile['unit']['status']['cargo']), 0)
            
            # Check infantry position is cleared
            infantry_tile = app.tile_rpc(game, 5, 6)
            self.assertIsNone(infantry_tile['unit'])
    
    def test_unit_unloading(self):
        """Test unloading infantry from APC"""
        with _app.app_context():
            print('Testing unit unloading from transport')
            # First load the unit
            app.unit_load_rpc(game, 5, 6, 5, 5)
            
            # Then unload it
            result = app.unit_unload_rpc(game, 5, 5, 6, 5, 0)  # Unload to adjacent tile
            
            # Check unit is placed correctly
            unload_tile = app.tile_rpc(game, 6, 5)
            self.assertIsNotNone(unload_tile['unit'])
            self.assertEqual(unload_tile['unit']['type'], 'INFANTRY')
    
    def test_transport_movement_with_cargo(self):
        """Test that transport can move while carrying units"""
        with _app.app_context():
            print('Testing transport movement with cargo')
            # Load infantry into APC
            app.unit_load_rpc(game, 5, 6, 5, 5)
            
            # Move APC with cargo
            result = app.unit_move_rpc(game, 5, 5, 6, 5)
            moved_tile = app.tile_rpc(game, 6, 5)
            
            # Verify APC moved and still has cargo
            self.assertEqual(moved_tile['unit']['type'], 'APC')
            self.assertIsNotNone(moved_tile['unit']['status']['cargo'])
    
    def tearDown(self):
        with _app.app_context():
            app.game_delete_rpc(game)            

class Test_RPC_capture_property(unittest.TestCase):
    
    def setUp(self):
        with _app.app_context():
            db.create_all()
            app.game_create_rpc(game)
            # Find a neutral city and place infantry nearby
            board = app.game_board_rpc(game)
            
            # Find neutral city
            self.city_pos = None
            for tile in board['grid']:
                if (tile['mapTile']['type'] == 'CITY' and 
                    tile['mapTile']['army'] != 'RED' and 
                    tile['unit'] is None):
                    self.city_pos = (tile['x'], tile['y'])
                    break
            
            if self.city_pos:
                x, y = self.city_pos
                app.unit_create_rpc(game, 'RED', 'INFANTRY', x, y)
                app.army_end_turn_rpc(game)
                app.army_end_turn_rpc(game)
    
    def test_capture_progress(self):
        """Test that capture progress reduces city HP"""
        with _app.app_context():
            print('Testing capture progress')
            if self.city_pos:
                x, y = self.city_pos
                original_tile = app.tile_rpc(game, x, y)
                original_hp = original_tile['capture_hp']
                
                # Start capture
                result = app.capture_tile_rpc(game, x, y)
                new_tile = app.tile_rpc(game, x, y)
                new_hp = new_tile['capture_hp']
                
                self.assertLess(new_hp, original_hp)
    
    def test_complete_capture(self):
        """Test complete capture changes ownership"""
        with _app.app_context():
            print('Testing complete capture')
            if self.city_pos:
                x, y = self.city_pos
                
                # Capture multiple times to complete capture
                for i in range(3):  # Usually takes 2-3 captures for full HP infantry
                    try:
                        app.capture_tile_rpc(game, x, y)
                        app.army_end_turn_rpc(game)
                        app.army_end_turn_rpc(game)
                    except:
                        break  # Capture completed
                
                final_tile = app.tile_rpc(game, x, y)
                self.assertEqual(final_tile['mapTile']['army'], 'RED')
    
    def tearDown(self):
        with _app.app_context():
            app.game_delete_rpc(game)

if __name__ == '__main__':
    unittest.main()

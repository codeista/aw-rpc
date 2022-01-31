'''[This is a unittest ]'''

import unittest
import app
import random


print('Running unit tests....')

# vars
letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
game = ''.join(random.choice(letters) for i in range(10))


''' Test class with mutiple tests;
    unit create and unit move rpc call'''


class Test_RPC_unit_create(unittest.TestCase):

    def setUp(self):
        app.game_create_rpc(game)
        app.unit_create(game, 'RED', 'INFANTRY', 1, 1)
        global unit_id
        unit_id = app.unit_create(game, 'RED', 'INFANTRY', 4, 12)['unit']['id']
        app.army_end_turn(game)
        app.army_end_turn(game)

    def test_unit_create(self):
        print('Testing unit creation')
        self.assertEqual(app.unit_create(game, 'RED', 'INFANTRY', 9, 12), app.tile(game, 9, 12))

    def test_unit_move(self):
        print('Testing unit move')
        self.assertEqual(app.unit_move(game, 1, 1, 0, 0), app.tile(game, 0, 0))

    def test_unit_move2(self):
        print('Testing unit move2')
        self.assertEqual(app.unit_move2(game, unit_id, 4, 10)['unit']['id'], app.tile(game, 4, 10)['unit']['id'])

    def tearDown(self):
        app.game_delete_rpc(game)


''' Test capture rpc call. '''


class Test_RPC_capture_property(unittest.TestCase):

    def setUp(self):
        app.game_create_rpc(game)
        global tile_hp
        tile_hp = app.tile(game, 1, 1)['capture_hp']
        app.unit_create(game, 'RED', 'INFANTRY', 1, 1)
        app.army_end_turn(game)
        app.army_end_turn(game)
        global troop_hp
        troop_hp = int(app.tile(game, 1, 1)['unit']['status']['hp'] /10)

    def test_capture_property(self):
        print('Testing capture property')
        self.assertEqual(app.capture_tile(game, 1, 1)['capture_hp'], (tile_hp - troop_hp))

    def tearDown(self):
        app.game_delete_rpc(game)


''' Test end turn rpc call'''


class Test_RPC_end_turn(unittest.TestCase):

    def setUp(self):
        app.game_create_rpc(game)
        global current_turn
        current_turn = app.check_turn(game)
        app.army_end_turn(game)

    def test_army_end_turn(self):
        print('Testing ending turn')
        self.assertNotEqual(current_turn,app.check_turn(game))

    def tearDown(self):
        app.game_delete_rpc(game)

if __name__ == '__main__':
    unittest.main()

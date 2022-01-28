'''[This is a unittest ]'''

import unittest
import app
import random

# vars

letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
game = ''.join(random.choice(letters) for i in range(10))



class Test_RPC_unit_create(unittest.TestCase):

    def setUp(self):
        app.game_create_rpc(game)

    def test_unit_create(self):
        self.assertEqual(app.unit_create(game, 'RED', 'INFANTRY', 9, 12), app.tile(game, 9, 12))

    def test_unit_move(self):
        app.unit_create(game, 'RED', 'INFANTRY', 1, 1)
        app.army_end_turn(game)
        app.army_end_turn(game)
        self.assertEqual(app.unit_move(game, 1, 1, 0, 0), app.tile(game, 0, 0))

    def tearDown(self):
        app.game_delete_rpc(game)


class Test_RPC_capture_property(unittest.TestCase):

    def setUp(self):
        app.game_create_rpc(game)

    def test_capture_property(self):
        tile_hp = app.tile(game, 1, 1)['capture_hp']
        app.unit_create(game, 'RED', 'INFANTRY', 1, 1)
        app.army_end_turn(game)
        app.army_end_turn(game)
        troop_hp = int(app.tile(game, 1, 1)['unit']['status']['hp'] /10)
        self.assertEqual(app.capture_tile(game, 1, 1)['capture_hp'], (tile_hp - troop_hp))

    def tearDown(self):
        app.game_delete_rpc(game)


class Test_RPC_end_turn(unittest.TestCase):

    def setUp(self):
        app.game_create_rpc(game)

    def test_army_end_turn(self):
        current_turn = app.check_turn(game)
        app.army_end_turn(game)
        self.assertNotEqual(current_turn,app.check_turn(game))

    def tearDown(self):
        app.game_delete_rpc(game)

if __name__ == '__main__':
    unittest.main()

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
            self.assertEqual(app.unit_create_rpc(game, 'RED', 'INFANTRY', 3, 1),
                            app.tile_rpc(game, 3, 1))

    def test_unit_move(self):
        with _app.app_context():
            print('Testing unit move')
            app.unit_create_rpc(game, 'RED', 'INFANTRY', 3, 1)
            app.army_end_turn_rpc(game)
            app.army_end_turn_rpc(game)
            self.assertEqual(app.unit_move_rpc(game, 3, 1, 3, 2), app.tile_rpc(game, 3, 2))
    #
    # def test_unit_move2(self):
    #     print('Testing unit move2')
    #     self.assertEqual(app.unit_move2(game, unit_id, 4, 10)['unit']['id'],
    #                      app.tile(game, 4, 10)['unit']['id'])

    def tearDown(self):
        with _app.app_context():
            app.game_delete_rpc(game)


''' Test capture rpc call. '''


# class Test_RPC_capture_property(unittest.TestCase):
#
#     def setUp(self):
#         app.game_create_rpc(game)
#         '''setup for capture property'''
#         global tile_hp
#         tile_hp = app.tile(game, 1, 1)['capture_hp']
#         app.unit_create(game, 'RED', 'INFANTRY', 1, 1)
#         app.army_end_turn(game)
#         app.army_end_turn(game)
#         global troop_hp
#         troop_hp = int(app.tile(game, 1, 1)['unit']['status']['hp'] / 10)
#
#     def test_capture_property(self):
#         print('Testing capture property')
#         self.assertEqual(app.capture_tile(game, 1, 1)['capture_hp'],
#                                          (tile_hp - troop_hp))
#
#     def tearDown(self):
#         app.game_delete_rpc(game)


''' Test end turn rpc call'''


# class Test_RPC_end_turn(unittest.TestCase):
#
#     def setUp(self):
#         app.game_create_rpc(game)
#         '''Setup for end turn'''
#         global current_turn
#         current_turn = app.check_turn(game)
#         app.army_end_turn(game)
#
#     def test_army_end_turn(self):
#         print('Testing ending turn')
#         self.assertNotEqual(current_turn, app.check_turn(game))
#
#     def tearDown(self):
#         app.game_delete_rpc(game)


if __name__ == '__main__':
    unittest.main()

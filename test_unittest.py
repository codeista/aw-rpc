'''[This is a suite of tests using unittest ]'''

import unittest
import app
import random


print('Running unit tests....')

# vars
letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
token = ''.join(random.choice(letters) for i in range(10))
colour = 'RED'
type = 'INFANTRY'
# base one
x = 9
y = 12
#base two
x1 = 18
y1 = 10



''' Test class with mutiple tests;
    unit create and unit move rpc call'''


class Test_RPC_unit_create(unittest.TestCase):

    def setUp(self):
        app.game_create_rpc(token)
        p1 = int(app.player_create_rpc('RED', 'MAX'))
        p2 = int(app.player_create_rpc('BLUE', 'ANDY'))
        app.join_game(token, 1, p1)
        app.join_game(token, 2, p2)
        app.start_game(token)
        '''setup for unit_create'''
        global unit_id
        unit_id = app.unit_create_rpc(token, colour, type, x, y)['id']
        app.unit_create_rpc(token, colour, type, x1, y1)
        # '''setup for unit move and unit move2'''
        # global unit_id
        # unit_id = app.unit_create(token, 'RED', 'INFANTRY', 4, 12)['unit']['id']
        # '''end turn twice so created units can take turn again'''

    # def test_unit_create(self):
    #     print(f'Testing unit creation on {token} x:{x1} y:{y1} {colour} {type}')
    #     self.assertEqual(app.unit_create_rpc(token, colour, type, x1, y1),
    #                      app.tile(token, x1, y1)['unit'])
    #     app.army_end_turn(token)

    def test_unit_move(self):
        print(f'Testing unit move on {token} x:{x1} y:{y1} {colour} {type}')
        if app.army_end_turn(token) != colour:
            app.army_end_turn(token)
        self.assertEqual(app.unit_move(token, x1, y1, 19, 10), app.tile(token, 19, 10))
        app.army_end_turn(token)

    def test_unit_move2(self):
        print(f'Testing unit move2 game {token} id {unit_id}')
        if app.army_end_turn(token) != colour:
            app.army_end_turn(token)
        self.assertEqual(app.unit_move2(token, unit_id, 9, 13)['unit']['id'],
                         app.tile(token, 9, 13)['unit']['id'])
        app.army_end_turn(token)
    #
    def tearDown(self):
        app.game_delete_rpc(token)


''' Test capture rpc call. '''


# class Test_RPC_capture_property(unittest.TestCase):
#
#     def setUp(self):
#         app.game_create_rpc(game)
#         app.player_create('RED', 'MAX')
#         app.player_create('BLUE', 'ANDY')
#         app.ame_join(game, 1, 3)
#         app.ame_join(game, 2, 4)
#         '''setup for capture property'''
#         global tile_hp
#         tile_hp = app.tile(game, 1, 1)['capture_hp']
#         app.unit_create(game, 'RED', 'INFANTRY', 9, 12)
#         app.army_end_turn(game)
#         app.army_end_turn(game)
#         global troop_hp
#         troop_hp = int(app.tile(game, 9, 12)['unit']['status']['hp'] / 10)
#
#     def test_capture_property(self):
#         print('Testing capture property')
#         self.assertEqual(app.capture_tile(game, 9, 12)['capture_hp'],
#                                          (tile_hp - troop_hp))
#
#     def tearDown(self):
#         app.game_delete_rpc(game)
#
#
# ''' Test end turn rpc call'''
#
#
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

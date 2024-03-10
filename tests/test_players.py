import unittest

import numpy as np

import player_brutal


class TestPlayers(unittest.TestCase):

    def test_tictactoe(self):
        brutal_worker = player_brutal.BrutalWorker(n_players=2, state_value_file='data/singularity.pkl')
        brutal_worker.start()

        states = np.asarray([[1, 0, 2], [2, 1, 0], [0, 1, 2]], dtype=int)
        response = brutal_worker.get_move(states, 0, 3)
        self.assertEqual(response, ((0, 1), 0))

        states = np.asarray([[1, 0, 2], [2, 1, 0], [0, 1, 0]], dtype=int)
        response = brutal_worker.get_move(states, 1, 3)
        self.assertEqual(response, ((2, 2), 1))

        states = np.asarray([[0, 0, 0], [0, 1, 0], [0, 0, 0]], dtype=int)
        response = brutal_worker.get_move(states, 1, 3)
        self.assertEqual(response, ((0, 0), 1))

        states = np.zeros((3, 3), dtype=int)
        response = brutal_worker.get_move(states, 0, 3)
        self.assertEqual(response, ((1, 1), 0))

        brutal_worker.stop()
        brutal_worker.join()

    def test_tictactoe_reloaded(self):
        brutal_worker = player_brutal.BrutalWorker(n_players=2, state_value_file='data/singularity.pkl')
        brutal_worker.start()

        states = np.zeros((3, 3), dtype=int)
        response = brutal_worker.get_move(states, 0, 3)
        self.assertEqual(response[0], (1, 1))
        self.assertAlmostEqual(response[1], 1./2)
        self.assertEqual(response[2], 0)

        brutal_worker.stop()
        brutal_worker.join()


if __name__ == '__main__':
    unittest.main()

# Generate the precomputed game tree
import argparse
import numpy as np

import player_brutal


def generate(board_size=7, n_players=2, win_count=5):
    brutal_worker = player_brutal.BrutalWorker(
        n_players=n_players,
        state_value_file='data/{:02d}_{:02d}_{:02d}.pkl'.format(board_size, win_count, n_players))
    brutal_worker.start()

    states = np.zeros((board_size, board_size), dtype=int)
    response = brutal_worker.get_move(states, 0, win_count)
    print(response)
    brutal_worker.stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate pre-computed data')
    parser.add_argument('--size', '-s', metavar='N', type=int, default=20,
                        help='Size of the board. Default: 20')
    parser.add_argument('--players', '-p', metavar='P', type=int, default=2,
                        help='Number of players. Default: 2')
    parser.add_argument('--win_count', '-w', metavar='C', type=int, default=5,
                        help='Number of consecutive pieces to be considered winning. Default: 5')
    prog_args = parser.parse_args()

    if prog_args.players < 2 or prog_args.players > 20:
        raise ValueError('Needs between 2 and 20 players. Given: {}'.format(prog_args.players))
    if prog_args.win_count < 2:
        raise ValueError('win_count must be at least 2.')
    if prog_args.size < prog_args.win_count:
        raise ValueError('Board size ({}) must be at least win_count ({})'.format(prog_args.size, prog_args.win_count))

    generate(board_size=prog_args.size, n_players=prog_args.players, win_count=prog_args.win_count)

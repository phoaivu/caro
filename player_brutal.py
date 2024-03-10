import os
import threading
import multiprocessing
import queue
import pickle
import numpy as np

import caro


def _state_code(state, n_players):
    if n_players < 1 or n_players >= 100:
        raise ValueError('Too few or too many')
    return '{}'.format(''.join(map('{:02d}'.format, state.flatten())))


def _player_state_code(coded_state, player_id):
    return '{:02d}:{}'.format(player_id, coded_state)


def _all_players_state_codes(state, n_players):
    """
    Returns all the coded states for all players, in a dict
    """
    coded_state = _state_code(state, n_players)
    return dict((_id, _player_state_code(coded_state, _id)) for _id in range(n_players))


class BrutalThread(threading.Thread):
    state_value_lock = threading.Lock()
    last_saved_count = 0

    def __init__(self, state_values, state_queue, n_players, current_player, win_count,
                 thread_count, state_value_file, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state_values = state_values
        self.state_queue = state_queue
        self._n_players = n_players
        self._current_player = current_player
        self._win_count = win_count
        self._thread_count = thread_count
        self._state_value_file = state_value_file

    def _show_stopper(self):
        for i in range(self._thread_count):
            self.state_queue.put(None)

    def _write_state_value(self, coded_state, state_val):
        try:
            BrutalThread.state_value_lock.acquire()
            self.state_values[coded_state] = state_val
        finally:
            BrutalThread.state_value_lock.release()

    def run(self):
        while True:
            state_queue_item = self.state_queue.get()
            if state_queue_item is None:
                break

            (state, coded_state, player_id, depth) = state_queue_item
            current_player_coded_state = _player_state_code(coded_state, self._current_player)

            try:
                BrutalThread.state_value_lock.acquire()
                computed = current_player_coded_state in self.state_values
            finally:
                self.state_value_lock.release()

            if computed:
                if depth == 0:
                    self._show_stopper()
                continue

            viable_moves = caro.viable_moves(state)
            n_computed_moves = 0
            moves_players = []
            for move in viable_moves:
                moved_state = state.copy()
                moved_state[move] = player_id + 1
                coded_moved_states = _all_players_state_codes(moved_state, self._n_players)
                moves_players.append(coded_moved_states)

                try:
                    BrutalThread.state_value_lock.acquire()
                    moved_value = self.state_values.get(coded_moved_states[self._current_player], None)
                finally:
                    BrutalThread.state_value_lock.release()

                if moved_value is not None:
                    n_computed_moves += 1
                else:
                    winner_data = caro.check_termination(moved_state, move, self._win_count)

                    if winner_data is not None:
                        n_computed_moves += 1

                        try:
                            BrutalThread.state_value_lock.acquire()
                            for _id in range(self._n_players):
                                other_state_val = 0. if winner_data.winner_id < 0 else (
                                    (self._n_players - 1.) if _id + 1 == winner_data.winner_id else -1.)
                                self.state_values[coded_moved_states[_id]] = other_state_val
                        finally:
                            BrutalThread.state_value_lock.release()
                        # print('Terminal State {} value: {}'.format(coded_moved_state, state_val))
                    else:
                        self.state_queue.put((moved_state, _state_code(moved_state, self._n_players),
                                              (player_id + 1) % self._n_players, depth + 1))

            if n_computed_moves == len(viable_moves):
                try:
                    self.state_value_lock.acquire()
                    self.state_values[_player_state_code(coded_state, player_id)] = max(
                        self.state_values[moves_players[m][player_id]] for m in range(len(viable_moves)))
                    for _id in set(range(self._n_players)) - {player_id}:
                        self.state_values[_player_state_code(coded_state, _id)] = np.mean(
                            list(self.state_values[moves_players[m][_id]] for m in range(len(viable_moves))))
                finally:
                    self.state_value_lock.release()
                if depth == 0:
                    self._show_stopper()
                if depth < 5:
                    print('Non-terminal state {} depth = {} computed'.format(coded_state, depth))
            else:
                self.state_queue.put((state, coded_state, player_id, depth))

            try:
                self.state_value_lock.acquire()
                n_entries = len(self.state_values)
                if BrutalThread.last_saved_count != n_entries > 0 == (n_entries % 1000):
                    print('Saving {}, {} entries'.format(self._state_value_file, n_entries))
                    with open(self._state_value_file, 'wb') as f:
                        pickle.dump(self.state_values, f)
                    BrutalThread.last_saved_count = n_entries
            finally:
                self.state_value_lock.release()


class BrutalWorker(multiprocessing.Process):

    def __init__(self, n_players=2, state_value_file=''):
        super().__init__()
        self._request_queue = multiprocessing.Queue()
        self._response_queue = multiprocessing.Queue()
        self._n_players = n_players
        self._n_threads = os.cpu_count() * 2
        self._state_value_file = state_value_file

    def get_move(self, states, player_id=0, win_count=3, timeout=None):
        """
        :return: a tuple ((x, y), score, player_id).
        """
        self._request_queue.put((states, player_id, win_count))
        try:
            return self._response_queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None

    def put_move(self, states, player_id=0, win_count=3):
        """
        Put a request on the request queue.
        :param states:
        :param player_id:
        :param win_count:
        """
        self._request_queue.put((states, player_id, win_count))

    def poll(self, timeout=0.05):
        try:
            return self._response_queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None

    def stop(self):
        self._request_queue.put(None)

    def run(self):
        state_values = dict()
        if os.path.exists(self._state_value_file):
            with open(self._state_value_file, 'rb') as f:
                state_values = pickle.load(f)
            print('Loaded {}, {} entries'.format(self._state_value_file, len(state_values)))

        state_queue = queue.Queue()

        # print('In {}'.format(self.__class__.__name__))
        request = self._request_queue.get()

        while request is not None:
            (states, _id, win_count) = request
            # print('Received: {} {}\n{}'.format(_id, win_count, states))
            state_queue.put((states, _state_code(states, self._n_players), _id, 0))
            threads = [BrutalThread(state_values, state_queue, self._n_players, _id, win_count, self._n_threads,
                                    self._state_value_file)
                       for _ in range(self._n_threads)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            # print('Threads done')

            min_value = np.inf
            best_move = None
            for move in caro.viable_moves(states):
                moved_state = states.copy()
                moved_state[move] = _id + 1
                coded_moved_state = _state_code(moved_state, self._n_players)
                avg_other_scores = np.mean(
                    list(state_values[_player_state_code(coded_moved_state, other)]
                         for other in set(range(self._n_players)) - {_id}))
                if min_value > avg_other_scores:
                    min_value = avg_other_scores
                    best_move = move
                # move_value = state_values[_player_state_code(coded_moved_state, _id)]
                # if move_value > max_value:
                #     max_value = move_value
                #     best_move = move
                print('Move {}, score {}'.format(move, avg_other_scores))
            if best_move is None:
                raise RuntimeError('')
            self._response_queue.put((best_move, min_value, _id))
            print('Player #{} move: {}. Total state_values size: {}'.format(_id, best_move, len(state_values)))

            if self._state_value_file != '':
                print('Updating state value file {}'.format(self._state_value_file))
                with open(self._state_value_file, 'wb') as f:
                    pickle.dump(state_values, f)

            request = self._request_queue.get()


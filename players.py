import player_brutal


class Player(object):

    def __init__(self, name='player'):
        self.name = name

    def move(self, states, _id, win_count):
        raise NotImplementedError()

    def is_human(self):
        return False

    def description(self):
        raise NotImplementedError()


class HumanPlayer(Player):
    def __init__(self, name='human'):
        super().__init__(name)

    def move(self, states, _id, win_count):
        pass

    def is_human(self):
        return True

    def description(self):
        return '{} [Manual]'.format(self.name)


_brutal_worker = None


class BrutalPlayer(Player):
    """Brute-force"""

    def __init__(self, name='brutal', auto_player_index=0, board_size=3, win_count=3, n_players=2):
        super().__init__(name)
        self._auto_player_index = auto_player_index
        global _brutal_worker
        if _brutal_worker is None:
            _brutal_worker = player_brutal.BrutalWorker(
                n_players, state_value_file='data/{:02d}_{:02d}_{:02d}.pkl'.format(board_size, win_count, n_players))
            _brutal_worker.start()

    def move(self, states, _id, win_count):
        _brutal_worker.put_move(states, _id, win_count)

    def poll(self, timeout=0.05):
        move = _brutal_worker.poll(timeout)
        return None if move is None else move[0]

    def description(self):
        return '{} [{}]'.format(self.name, self._auto_player_index)


def stop_brutal_worker():
    global _brutal_worker
    _brutal_worker.stop()
    _brutal_worker.join()
    _brutal_worker = None

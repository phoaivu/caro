import numpy as np
import caro


class Game(object):
    """Keeping states, players and turn."""

    def __init__(self, size=3, win_count=3, _players=None):
        self.size = size
        self.win_count = win_count
        self._players = _players
        self._state = np.zeros((size, size), dtype=int)
        self._current_player_idx = 0

    @property
    def state(self):
        return self._state

    @property
    def current_player_index(self):
        return self._current_player_idx

    @property
    def current_player(self):
        return self._players[self._current_player_idx]

    def is_valid(self, move=(0, 0)):
        x, y = move
        return self._state[x, y] == 0

    def move(self, move=(0, 0)):
        """
        Record the move and check for termination. Returns WinnerData if terminated, otherwise None
        """
        if not self.is_valid(move):
            raise ValueError('Invalid move: {}'.format(move))
        self._state[move] = self._current_player_idx + 1
        return caro.check_termination(self._state, move, self.win_count)

    def next(self):
        self._current_player_idx = (self._current_player_idx + 1) % len(self._players)

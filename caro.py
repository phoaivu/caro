import itertools

import numpy as np


class WinnerData(object):
    def __init__(self, x, y, x_end, y_end, count, winner_id):
        self.x = x
        self.y = y
        self.x_end = x_end
        self.y_end = y_end
        self.count = count
        self.winner_id = winner_id

    def cells(self):
        def _range(_start, _end):
            sign = np.sign(_end - _start)
            return self.count * [_start] if _start == _end else range(_start, _end + sign, sign)
        return zip(_range(self.x, self.x_end), _range(self.y, self.y_end))

    def __str__(self):
        return '{}({}, {}, {}, {}, {}, {})'.format(
            self.__class__.__name__, self.x, self.y, self.x_end, self.y_end, self.count, self.winner_id)


def viable_moves(state):
    return list(filter(lambda p: state[p[0], p[1]] == 0,
                       itertools.product(range(state.shape[0]), range(state.shape[1]))))


def check_termination(states, latest_move, win_count):
    x, y = latest_move
    val = states[x, y]

    # increments = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    increments = list(filter(lambda _: _ != (0, 0), itertools.product([-1, 0, 1], [-1, 0, 1])))

    def _inbounds(_x, _y):
        return 0 <= _x < states.shape[0] and 0 <= _y < states.shape[1]

    def _trace(inc):
        # functools.reduce()
        count = 0
        xx = x + inc[0]
        yy = y + inc[1]
        while _inbounds(xx, yy) and states[xx, yy] == val:
            count += 1
            xx += inc[0]
            yy += inc[1]
        return count, _inbounds(xx, yy) and states[xx, yy] != 0

    traces = list(map(_trace, increments))
    assert len(traces) == 8
    # Plus 1 for the move at (x, y)
    whole_traces = map(lambda idx: (idx, traces[idx][0], traces[7 - idx][0],
                                    traces[idx][0] + traces[7 - idx][0] + 1,
                                    traces[idx][1] and traces[7 - idx][1]),
                       range(4))

    def _finished_filter(_idx, _start_count, _end_count, _count, _bounded):
        return _count >= win_count and not _bounded

    finished = next(filter(lambda _elm: _finished_filter(*_elm), whole_traces), None)
    winner_data = None
    if finished is not None:
        _idx, _start_count, _end_count, _count, _ = finished
        winner_data = WinnerData(x=x + _start_count * increments[_idx][0],
                                 y=y + _start_count * increments[_idx][1],
                                 x_end=x + _end_count * increments[7 - _idx][0],
                                 y_end=y + _end_count * increments[7 - _idx][1],
                                 count=_count, winner_id=val)
    elif len(viable_moves(states)) == 0:
        winner_data = WinnerData(x=0, y=0, x_end=0, y_end=0, count=0, winner_id=-1)
    return winner_data

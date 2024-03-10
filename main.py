import argparse

import gui
import game
import players


class Controller(object):
    def __init__(self, size=3, win_count=3, player_names=None):
        _players = []
        auto_count = 1
        for i, name in enumerate(player_names):
            if name.lower() == 'auto':
                p = players.BrutalPlayer(name=name, auto_player_index=auto_count,
                                         board_size=size, win_count=win_count, n_players=len(player_names))
                auto_count += 1
            else:
                p = players.HumanPlayer(name=name)
            _players.append(p)
        self._game = game.Game(size=size, win_count=win_count, _players=_players)
        self.view = gui.GameView(size=size, player_names=[p.name for p in _players],
                                 player_desc=[p.description() for p in _players],
                                 click_handler=lambda x, y: self._on_move(x, y))
        self._human_move = None
        self._requested_auto = False
        self._is_terminated = False

    def _on_move(self, x, y):
        if self._human_move is not None:
            return
        if self._game.is_valid((x, y)):
            self._human_move = (x, y)
        else:
            self.view.print_not_there()

    def _next(self, move):
        self.view.draw_move(self._game.current_player_index, x=move[0], y=move[1])
        winner_data = self._game.move(move)
        if winner_data is not None:
            self._is_terminated = True
            self.view.print_winner_message(winner_data)
            if winner_data.winner_id >= 0:
                self.view.draw_win_line(winner_data)
        else:
            self._game.next()
            self.view.print_turn_message(self._game.current_player_index)

    def play(self):
        while True:
            if not self._is_terminated:
                current_player = self._game.current_player
                if current_player.is_human():
                    if self._human_move is not None:
                        self._next(self._human_move)
                        self._human_move = None
                else:
                    if not self._requested_auto:
                        current_player.move(self._game.state, self._game.current_player_index,
                                            win_count=self._game.win_count)
                        self._requested_auto = True
                    else:
                        move = current_player.poll()
                        if move is not None:
                            self._next(move)
                            self._requested_auto = False
            try:
                self.view.flush()
            except Exception:
                break

        players.stop_brutal_worker()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Play a game')
    parser.add_argument('players', metavar='name', type=str, nargs='+',
                        help='names of the players. Must have at least two players. '
                             'Use `auto` for an exceptionally smart auto-player')
    parser.add_argument('--size', '-s', metavar='N', type=int, default=20,
                        help='size of the board. Default: 20')
    parser.add_argument('--win_count', '-w', metavar='C', type=int, default=5,
                        help='Number of consecutive pieces to be considered winning. Default: 5')
    prog_args = parser.parse_args()

    if len(prog_args.players) < 2:
        raise ValueError('Needs at least 2 players')
    if prog_args.win_count < 2:
        raise ValueError('win_count must be at least 2.')
    if prog_args.size < prog_args.win_count:
        raise ValueError('Board size ({}) must be at least win_count ({})'.format(prog_args.size, prog_args.win_count))

    controller = Controller(size=prog_args.size, win_count=prog_args.win_count, player_names=prog_args.players)
    controller.view.show()
    controller.play()

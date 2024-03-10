import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import colormaps


HIGHLIGHT_COLOR = 'gray'
LINE_COLOR = 'black'
BACKGROUND_ALPHA = 0.4


class GameView(object):

    def __init__(self, size=3, player_names=None, player_desc=None, click_handler=None):
        if len(player_names) > 20:
            raise ValueError('Too many players')

        self._cell_size = 10
        self._size = size
        self._player_names = player_names
        self._player_desc = player_desc
        self._click_handler = click_handler
        self._colors = (colormaps['tab20'].colors[0:-1:2] + colormaps['tab20'].colors[1:-1:2])
        self._fig = None
        self._ax = None
        self._status = None
        self._pos_patch = None

    def _on_mouse_clicked(self, event_data):
        if event_data.inaxes == self._ax:
            self._click_handler(int(event_data.xdata // self._cell_size),
                                int(event_data.ydata // self._cell_size))

    def _on_mouse_move(self, event_data):
        self._pos_patch.set_visible(False)
        if event_data.inaxes == self._ax:
            x, y = int(event_data.xdata // self._cell_size), int(event_data.ydata // self._cell_size)
            self._pos_patch.set_xy((x * self._cell_size, y * self._cell_size))
            self._pos_patch.set_visible(True)

    def setup(self):
        plt.ion()
        self._fig = plt.figure()
        self._ax = self._fig.add_subplot()
        self._ax.set_xlim(0, self._cell_size * self._size)
        self._ax.set_ylim(0, self._cell_size * self._size)
        self._ax.set_aspect(1., adjustable=None)
        self._ax.xaxis.set_visible(False)
        self._ax.yaxis.set_visible(False)

        for i in range(1, self._size):
            self._ax.axvline(x=self._cell_size * i, ymin=0, ymax=1., color=LINE_COLOR, alpha=BACKGROUND_ALPHA)
            self._ax.axhline(y=self._cell_size * i, xmin=0, xmax=1., color=LINE_COLOR, alpha=BACKGROUND_ALPHA)

        self._pos_patch = patches.Rectangle((-self._cell_size, -self._cell_size),
                                            width=self._cell_size, height=self._cell_size,
                                            fc=HIGHLIGHT_COLOR, alpha=BACKGROUND_ALPHA, zorder=1)
        self._pos_patch.set_visible(False)
        self._ax.add_patch(self._pos_patch)

        player_patches = list(map(lambda item: patches.Patch(color=item[0], label=item[1]),
                                  zip(self._colors, self._player_desc)))
        self._ax.legend(handles=player_patches, bbox_to_anchor=(1.02, 1), loc='upper left')

        self._status = self._ax.text(0., -0.04, '', transform=self._ax.transAxes, fontsize=10, fontname='sans serif')
        self.print_turn_message(player_idx=0)

        self._fig.canvas.mpl_connect('button_release_event', lambda e: self._on_mouse_clicked(e))
        self._fig.canvas.mpl_connect('motion_notify_event', lambda e: self._on_mouse_move(e))

    def print_message(self, msg=''):
        self._status.set_text(msg)

    def print_not_there(self):
        self.print_message('Uh oh, not there!')

    def print_turn_message(self, player_idx=0):
        self.print_message('Your move, {}!'.format(self._player_names[player_idx]))

    def print_winner_message(self, winner_data):
        if winner_data.winner_id < 0:
            self.print_message('Draw. Good game.')
        else:
            self.print_message('{} won.'.format(self._player_names[winner_data.winner_id - 1]))

    def draw_move(self, player_idx=0, x=0, y=0):
        half = self._cell_size / 2.
        self._ax.add_patch(patches.Circle((x * self._cell_size + half, y * self._cell_size + half),
                                          half * 0.7,
                                          fc=self._colors[player_idx],
                                          zorder=2))

    def draw_win_line(self, winner_data):
        for (x, y) in winner_data.cells():
            self._ax.add_patch(patches.Rectangle((x*self._cell_size, y*self._cell_size),
                                                 self._cell_size, self._cell_size,
                                                 fc='gray', alpha=BACKGROUND_ALPHA, zorder=1))

    def flush(self):
        self._fig.canvas.flush_events()

    def show(self):
        self.setup()
        plt.show()

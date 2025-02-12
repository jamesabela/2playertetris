import random
from dataclasses import dataclass, replace
import tkinter


shapes = {
    # See README.md for format.
    'O': ['56a9', '6a95', 'a956', '956a'],
    'I': ['4567', '26ae', 'ba98', 'd951'],
    'J': ['0456', '2159', 'a654', '8951'],
    'L': ['2654', 'a951', '8456', '0159'],
    'T': ['1456', '6159', '9654', '4951'],
    'Z': ['0156', '2659', 'a954', '8451'],
    'S': ['1254', 'a651', '8956', '0459'],
}


@dataclass(frozen=True)
class Piece:
    shape: str
    rot: int = 0
    x: int = 0
    y: int = 0


def get_piece_blocks(piece):
    for char in shapes[piece.shape][piece.rot % 4]:
        y, x = divmod(int(char, 16), 4)
        yield piece.x + x, piece.y - y


def move_piece(piece, *, rot=0, dx=0, dy=0):
    rot = (piece.rot + rot) % 4
    x = piece.x + dx
    y = piece.y + dy
    return replace(piece, rot=rot, x=x, y=y)


def get_wall_kicks(piece, *, rot=0):
    return [
        move_piece(piece, rot=rot, dx=dx, dy=dy)
        for dx, dy in [(0, 0), (-1, 0), (1, 0), (0, -1)]
    ]


def piece_fits(field, piece):
    width = len(field[0])
    height = len(field)

    for x, y in get_piece_blocks(piece):
        if not 0 <= x < width:
            return False
        elif not 0 <= y < height:
            return False
        elif field[y][x]:
            return False
    else:
        return True


def random_shape_bag():
    bag = list(shapes)

    # Start with an easy piece.
    yield random.choice('IJLT')

    while True:
        random.shuffle(bag)
        yield from bag


def make_rows(width, height):
    return [[''] * width for _ in range(height)]


class Tetris:
    def __init__(self, width=10, height=16):
        self.width = width
        self.height = height
        self.game_over = False
        self.score = 0
        self._random_shapes = random_shape_bag()

        self.field = make_rows(width, height)
        self.piece = self._get_next_piece()

    def _get_next_piece(self):
        shape = next(self._random_shapes)
        centered = self.width // 2 - 2
        top = self.height - 1
        return Piece(shape, x=centered, y=top)

    def _place_new_piece(self):
        self.piece = self._get_next_piece()
        if not piece_fits(self.field, self.piece):
            self.game_over = True

    def _freeze_piece(self):
        for x, y in get_piece_blocks(self.piece):
            self.field[y][x] = self.piece.shape

    def _remove_full_rows(self):
        self.field = [row for row in self.field if not all(row)]
        num_rows_cleared = self.height - len(self.field)
        self.score += num_rows_cleared
        self.field += make_rows(self.width, num_rows_cleared)

    def _move(self, *, rot=0, dx=0, dy=0):
        if rot:
            candidate_pieces = get_wall_kicks(self.piece, rot=rot)
        else:
            candidate_pieces = [move_piece(self.piece, dx=dx, dy=dy)]

        for piece in candidate_pieces:
            if piece_fits(self.field, piece):
                self.piece = piece
                return

        tried_to_move_down = dy == -1
        if tried_to_move_down:
            self._freeze_piece()
            self._remove_full_rows()
            self._place_new_piece()

    def move(self, movement):
        if not self.game_over:
            args = {
                'left': {'dx': -1},
                'right': {'dx': 1},
                'down': {'dy': -1},
                'rotleft': {'rot': -1},
                'rotright': {'rot': 1},
            }[movement]
            self._move(**args)


# Colors from Flatris.
colors = {
    'I': '#3cc7d6',  # Cyan.
    'O': '#fbb414',  # Yellow.
    'T': '#b04497',  # Magenta.
    'J': '#3993d0',  # Blue.
    'L': '#ed652f',  # Orange.
    'S': '#95c43d',  # Green.
    'Z': '#e84138',  # Red.
    '':  '#ecf0f1',  # (Background color.)
}


class BlockDisplay(tkinter.Canvas):
    def __init__(self, parent, width, height, block_size=40):
        tkinter.Canvas.__init__(self, parent,
                                width=width * block_size,
                                height=height * block_size)
        self.block_size = block_size
        self.width = width
        self.height = height
        self.color_mode = True
        self.blocks = {
            (x, y): self._create_block(x, y)
            for x in range(width)
            for y in range(height)
        }

    def _create_block(self, x, y):
        flipped_y = self.height - y - 1
        y = flipped_y
        size = self.block_size
        return self.create_rectangle(
            x * size,
            y * size,
            (x + 1) * size,
            (y + 1) * size,
            fill='',
            outline='',
        )

    def __setitem__(self, pos, char):
        if self.color_mode:
            fill = colors[char.upper()]
        else:
            if char == '':
                fill = colors['']
            elif char.isupper():
                fill = 'gray50'
            else:
                fill = 'black'

        block = self.blocks[pos]
        self.itemconfigure(block, fill=fill)

    def clear(self):
        self.itemconfigure('all', fill='')

    def pause(self):
        self.itemconfigure('all', stipple='gray50')

    def resume(self):
        self.itemconfigure('all', stipple='')


class TetrisTk:
    def __init__(self):

        self.tk = tk = tkinter.Tk()
        self.tk.title('Tetris - Two Player')

        # Player 1 setup
        self.tetris1 = Tetris()
        self.display1 = BlockDisplay(tk, self.tetris1.width, self.tetris1.height)
        self.display1.pack(side=tkinter.LEFT, fill=tkinter.X)

        # Player 2 setup
        self.tetris2 = Tetris()
        self.display2 = BlockDisplay(tk, self.tetris2.width, self.tetris2.height)
        self.display2.pack(side=tkinter.RIGHT, fill=tkinter.X)

        # Player 1 score
        self.score_view1 = tkinter.Label(self.tk, text='Player 1 Score: 0')
        self.score_view1.pack(side=tkinter.LEFT, fill=tkinter.X)
        self.score_view1['font'] = 'Helvetica 20'

        # Player 2 score
        self.score_view2 = tkinter.Label(self.tk, text='Player 2 Score: 0')
        self.score_view2.pack(side=tkinter.RIGHT, fill=tkinter.X)
        self.score_view2['font'] = 'Helvetica 20'

        # Bind keys for both players
        tk.bind('<KeyPress>', self.keypress)

        self.paused = True
        self.fall_id = None
        self.redraw()
        self.resume()

        tk.mainloop()

    def fall(self):
        self.tetris1.move('down')
        self.tetris2.move('down')
        self.redraw()
        if self.tetris1.game_over or self.tetris2.game_over:
            self.pause()
        else:
            self.schedule_fall()

    def schedule_fall(self):
        # In case we're already called once.
        self.cancel_fall()
        self.fall_id = self.tk.after(500, self.fall)

    def cancel_fall(self):
        if self.fall_id is not None:
            self.tk.after_cancel(self.fall_id)
            self.fall_id = None

    def _draw_field(self, tetris, display):
        for y, row in enumerate(tetris.field):
            for x, char in enumerate(row):
                display[x, y] = char

    def _draw_piece(self, tetris, display):
        piece = tetris.piece
        char = piece.shape.lower()
        for x, y in get_piece_blocks(piece):
            display[x, y] = char

    def redraw(self):
        # Player 1
        self._draw_field(self.tetris1, self.display1)
        if not self.tetris1.game_over:
            self._draw_piece(self.tetris1, self.display1)
        self.score_view1['text'] = f'Player 1 Score: {self.tetris1.score}'

        # Player 2
        self._draw_field(self.tetris2, self.display2)
        if not self.tetris2.game_over:
            self._draw_piece(self.tetris2, self.display2)
        self.score_view2['text'] = f'Player 2 Score: {self.tetris2.score}'

    def pause(self):
        if not self.paused:
            self.display1.pause()
            self.display2.pause()
            self.cancel_fall()
            self.paused = True

    def resume(self):
        if self.paused:
            self.display1.resume()
            self.display2.resume()
            self.schedule_fall()
            self.paused = False

    def new_game(self):
        self.tetris1 = Tetris()
        self.tetris2 = Tetris()
        self.display1.resume()
        self.display2.resume()
        self.resume()

    def toggle_pause(self):
        if self.tetris1.game_over or self.tetris2.game_over:
            self.new_game()
        elif self.paused:
            self.resume()
        else:
            self.pause()

    def keypress(self, event):
        commands1 = {
            'w': lambda: self.tetris1.move('rotleft'),
            'a': lambda: self.tetris1.move('left'),
            'd': lambda: self.tetris1.move('right'),
            's': lambda: self.tetris1.move('down'),
        }
        commands2 = {
            'Up': lambda: self.tetris2.move('rotleft'),
            'Left': lambda: self.tetris2.move('left'),
            'Right': lambda: self.tetris2.move('right'),
            'Down': lambda: self.tetris2.move('down'),
        }



        if not self.paused:
            if event.keysym in commands1:
                commands1[event.keysym]()
                self.redraw()
            elif event.keysym in commands2:
                commands2[event.keysym]()
                self.redraw()


if __name__ == '__main__':
    TetrisTk()

"""Curses front end: difficulty menu and the interactive board."""

from __future__ import annotations

import curses
import random
import time

from .board import (
    CELLS,
    DIFFICULTIES,
    SIZE,
    Difficulty,
    candidates,
    conflicts,
    generate,
)

MIN_HEIGHT = 22
MIN_WIDTH = 40

BORDER_TOP = "┌───────┬───────┬───────┐"
BORDER_MID = "├───────┼───────┼───────┤"
BORDER_BOTTOM = "└───────┴───────┴───────┘"
BORDER_ROW = "│       │       │       │"

GRID_Y = 3
GRID_X = 3
GRID_W = len(BORDER_TOP)

CLR_FRAME = 1
CLR_GIVEN = 2
CLR_ENTRY = 3
CLR_BAD = 4
CLR_CURSOR = 5
CLR_PEER = 6
CLR_TITLE = 7
CLR_WIN = 8


def _init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(CLR_FRAME, curses.COLOR_BLUE, -1)
    curses.init_pair(CLR_GIVEN, curses.COLOR_WHITE, -1)
    curses.init_pair(CLR_ENTRY, curses.COLOR_CYAN, -1)
    curses.init_pair(CLR_BAD, curses.COLOR_RED, -1)
    curses.init_pair(CLR_CURSOR, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(CLR_PEER, curses.COLOR_YELLOW, -1)
    curses.init_pair(CLR_TITLE, curses.COLOR_MAGENTA, -1)
    curses.init_pair(CLR_WIN, curses.COLOR_GREEN, -1)


def _put(win: curses.window, y: int, x: int, text: str, attr: int = 0) -> None:
    try:
        win.addstr(y, x, text, attr)
    except curses.error:
        pass


def _cell_y(row: int) -> int:
    return GRID_Y + 1 + row + row // 3


def _cell_x(col: int) -> int:
    return GRID_X + 2 + 8 * (col // 3) + 2 * (col % 3)


def _mmss(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 60:02d}:{total % 60:02d}"


class Game:
    def __init__(self, difficulty: Difficulty, rng: random.Random) -> None:
        self.difficulty = difficulty
        self.puzzle, self.solution = generate(difficulty, rng)
        self.grid = self.puzzle[:]
        self.notes: list[set[int]] = [set() for _ in range(CELLS)]
        self.cursor = self.puzzle.index(0) if 0 in self.puzzle else 0
        self.undo: list[tuple[int, int, set[int]]] = []
        self.hints = 0
        self.notes_mode = False
        self.mark_mistakes = False
        self.started = time.monotonic()
        self.finished: float | None = None
        self.message = ""

    @property
    def elapsed(self) -> float:
        return (self.finished or time.monotonic()) - self.started

    @property
    def solved(self) -> bool:
        return self.grid == self.solution

    def _record(self, index: int) -> None:
        self.undo.append((index, self.grid[index], set(self.notes[index])))

    def move(self, drow: int, dcol: int) -> None:
        row, col = divmod(self.cursor, SIZE)
        self.cursor = ((row + drow) % SIZE) * SIZE + (col + dcol) % SIZE

    def place(self, digit: int) -> None:
        index = self.cursor
        if self.puzzle[index]:
            self.message = "That digit is a given."
            return
        self._record(index)
        if self.notes_mode:
            self.notes[index] ^= {digit}
            return
        self.grid[index] = 0 if self.grid[index] == digit else digit
        self.notes[index].clear()
        self._check_finished()

    def clear(self) -> None:
        index = self.cursor
        if self.puzzle[index]:
            return
        self._record(index)
        self.grid[index] = 0
        self.notes[index].clear()

    def hint(self) -> None:
        index = self.cursor
        if self.grid[index] == self.solution[index]:
            self.message = "Already correct."
            return
        self._record(index)
        self.grid[index] = self.solution[index]
        self.notes[index].clear()
        self.hints += 1
        self._check_finished()

    def undo_last(self) -> None:
        if not self.undo:
            self.message = "Nothing to undo."
            return
        index, value, notes = self.undo.pop()
        self.grid[index] = value
        self.notes[index] = notes
        self.cursor = index

    def _check_finished(self) -> None:
        if self.solved and self.finished is None:
            self.finished = time.monotonic()


def _draw_frame(win: curses.window) -> None:
    frame = curses.color_pair(CLR_FRAME)
    lines = [BORDER_TOP] + ([BORDER_ROW] * 3 + [BORDER_MID]) * 2 + [BORDER_ROW] * 3
    lines.append(BORDER_BOTTOM)
    for offset, line in enumerate(lines):
        _put(win, GRID_Y + offset, GRID_X, line, frame)


def _draw_game(win: curses.window, game: Game) -> None:
    win.erase()
    _put(win, 0, GRID_X, "TTY SUDOKU", curses.color_pair(CLR_TITLE) | curses.A_BOLD)
    status = f"{_mmss(game.elapsed)}  hints {game.hints}"
    _put(win, 0, GRID_X + GRID_W - len(status), status, curses.A_DIM)
    mode = "notes" if game.notes_mode else "entry"
    if game.mark_mistakes:
        mode += " · check"
    _put(win, 1, GRID_X, f"{game.difficulty.name.lower()} · {mode}", curses.A_DIM)

    _draw_frame(win)

    bad = conflicts(game.grid)
    cursor_row, cursor_col = divmod(game.cursor, SIZE)
    for index in range(CELLS):
        row, col = divmod(index, SIZE)
        value = game.grid[index]
        if value:
            char = str(value)
            if index in bad or (game.mark_mistakes and value != game.solution[index]):
                attr = curses.color_pair(CLR_BAD) | curses.A_BOLD
            elif game.puzzle[index]:
                attr = curses.color_pair(CLR_GIVEN) | curses.A_BOLD
            else:
                attr = curses.color_pair(CLR_ENTRY)
        else:
            char = "·" if game.notes[index] else " "
            attr = curses.A_DIM
        if index == game.cursor:
            attr = curses.color_pair(CLR_CURSOR) | curses.A_BOLD
        elif row == cursor_row or col == cursor_col:
            attr |= curses.A_UNDERLINE
        _put(win, _cell_y(row), _cell_x(col), char, attr)

    panel_y = GRID_Y + 14
    notes = game.notes[game.cursor]
    possible = candidates(game.grid, game.cursor) if not game.grid[game.cursor] else []
    _put(
        win,
        panel_y,
        GRID_X,
        f"cell {chr(ord('A') + cursor_row)}{cursor_col + 1}"
        f"  notes {''.join(str(d) for d in sorted(notes)) or '-'}"
        f"  fits {''.join(str(d) for d in possible) or '-'}",
    )

    if game.solved:
        won = f"Solved in {_mmss(game.elapsed)} with {game.hints} hint(s)!"
        _put(win, panel_y + 1, GRID_X, won, curses.color_pair(CLR_WIN) | curses.A_BOLD)
        _put(win, panel_y + 2, GRID_X, "n new puzzle · d difficulty · q quit", curses.A_DIM)
    else:
        _put(win, panel_y + 1, GRID_X, game.message, curses.color_pair(CLR_PEER))
        _put(win, panel_y + 2, GRID_X, "hjkl/arrows move · 1-9 place · 0 erase · p notes", curses.A_DIM)
        _put(win, panel_y + 3, GRID_X, "u undo · ? hint · m check · n new · d difficulty · q quit", curses.A_DIM)
    win.noutrefresh()
    curses.doupdate()


def _menu(win: curses.window) -> Difficulty | None:
    selected = 0
    while True:
        win.erase()
        _put(win, 1, GRID_X, "TTY SUDOKU", curses.color_pair(CLR_TITLE) | curses.A_BOLD)
        _put(win, 2, GRID_X, "Choose a difficulty", curses.A_DIM)
        for offset, difficulty in enumerate(DIFFICULTIES):
            label = f" {offset + 1}. {difficulty.name:<7}{difficulty.clues} clues "
            attr = (
                curses.color_pair(CLR_CURSOR) | curses.A_BOLD
                if offset == selected
                else 0
            )
            _put(win, 4 + offset, GRID_X, label, attr)
        _put(win, 8, GRID_X, "enter start · q quit", curses.A_DIM)
        win.noutrefresh()
        curses.doupdate()

        key = win.getch()
        if key in (ord("q"), 27):
            return None
        if key in (curses.KEY_UP, ord("k")):
            selected = (selected - 1) % len(DIFFICULTIES)
        elif key in (curses.KEY_DOWN, ord("j")):
            selected = (selected + 1) % len(DIFFICULTIES)
        elif ord("1") <= key <= ord("0") + len(DIFFICULTIES):
            return DIFFICULTIES[key - ord("1")]
        elif key in (curses.KEY_ENTER, 10, 13, ord(" ")):
            return DIFFICULTIES[selected]


def _loading(win: curses.window, difficulty: Difficulty) -> None:
    win.erase()
    _put(win, 4, GRID_X, f"Building a {difficulty.name.lower()} puzzle…")
    win.refresh()


def _play(win: curses.window, game: Game) -> str:
    """Run one puzzle; returns 'new', 'menu' or 'quit'."""
    while True:
        _draw_game(win, game)
        key = win.getch()
        if key == -1:
            continue
        game.message = ""

        if key in (ord("q"), 27):
            return "quit"
        if key == ord("d"):
            return "menu"
        if key == ord("n"):
            return "new"
        if key in (curses.KEY_LEFT, ord("h")):
            game.move(0, -1)
        elif key in (curses.KEY_RIGHT, ord("l")):
            game.move(0, 1)
        elif key in (curses.KEY_UP, ord("k")):
            game.move(-1, 0)
        elif key in (curses.KEY_DOWN, ord("j")):
            game.move(1, 0)
        elif ord("1") <= key <= ord("9"):
            game.place(key - ord("0"))
        elif key in (ord("0"), ord(" "), ord("x"), curses.KEY_BACKSPACE, 127, 8, curses.KEY_DC):
            game.clear()
        elif key == ord("p"):
            game.notes_mode = not game.notes_mode
        elif key == ord("u"):
            game.undo_last()
        elif key == ord("?"):
            game.hint()
        elif key == ord("m"):
            game.mark_mistakes = not game.mark_mistakes
        elif key == curses.KEY_RESIZE:
            win.clear()


def run(stdscr: curses.window, seed: int | None, difficulty: Difficulty | None) -> None:
    curses.curs_set(0)
    _init_colors()
    stdscr.keypad(True)
    curses.halfdelay(5)
    rng = random.Random(seed)

    height, width = stdscr.getmaxyx()
    if height < MIN_HEIGHT or width < MIN_WIDTH:
        raise SystemExit(
            f"Terminal too small: need at least {MIN_WIDTH}x{MIN_HEIGHT}, "
            f"got {width}x{height}."
        )

    while True:
        if difficulty is None:
            curses.nocbreak()
            curses.cbreak()
            difficulty = _menu(stdscr)
            curses.halfdelay(5)
            if difficulty is None:
                return
        _loading(stdscr, difficulty)
        action = _play(stdscr, Game(difficulty, rng))
        if action == "quit":
            return
        if action == "menu":
            difficulty = None

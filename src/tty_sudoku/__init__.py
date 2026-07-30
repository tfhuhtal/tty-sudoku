"""A sudoku game for the terminal."""

from __future__ import annotations

import argparse
import curses

from .board import DIFFICULTIES
from .ui import run

__all__ = ["main"]


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="tty-sudoku", description=__doc__)
    parser.add_argument(
        "-d",
        "--difficulty",
        choices=[d.name.lower() for d in DIFFICULTIES],
        help="skip the menu and start straight away",
    )
    parser.add_argument("-s", "--seed", type=int, help="seed for reproducible puzzles")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    chosen = next((d for d in DIFFICULTIES if d.name.lower() == args.difficulty), None)
    try:
        curses.wrapper(run, args.seed, chosen)
    except KeyboardInterrupt:
        pass

"""Puzzle generation and solving for a 9x9 sudoku on a flat 81-cell list."""

from __future__ import annotations

import random
from dataclasses import dataclass

SIZE = 9
CELLS = SIZE * SIZE
DIGITS = tuple(range(1, SIZE + 1))


def _peers() -> tuple[tuple[int, ...], ...]:
    peers: list[tuple[int, ...]] = []
    for i in range(CELLS):
        row, col = divmod(i, SIZE)
        box_row, box_col = row - row % 3, col - col % 3
        group = {row * SIZE + c for c in range(SIZE)}
        group |= {r * SIZE + col for r in range(SIZE)}
        group |= {
            (box_row + r) * SIZE + box_col + c for r in range(3) for c in range(3)
        }
        group.discard(i)
        peers.append(tuple(sorted(group)))
    return tuple(peers)


PEERS = _peers()


@dataclass(frozen=True)
class Difficulty:
    name: str
    clues: int


DIFFICULTIES: tuple[Difficulty, ...] = (
    Difficulty("Easy", 45),
    Difficulty("Medium", 33),
    Difficulty("Hard", 25),
)


def candidates(grid: list[int], index: int) -> list[int]:
    taken = {grid[p] for p in PEERS[index]}
    return [d for d in DIGITS if d not in taken]


def _first_empty(grid: list[int]) -> int:
    try:
        return grid.index(0)
    except ValueError:
        return -1


def count_solutions(grid: list[int], limit: int = 2) -> int:
    """Number of solutions, giving up once `limit` is reached."""
    work = grid[:]

    def search() -> int:
        index = _first_empty(work)
        if index < 0:
            return 1
        found = 0
        for digit in candidates(work, index):
            work[index] = digit
            found += search()
            work[index] = 0
            if found >= limit:
                break
        return found

    return search()


def solve(grid: list[int]) -> list[int] | None:
    work = grid[:]

    def search() -> bool:
        index = _first_empty(work)
        if index < 0:
            return True
        for digit in candidates(work, index):
            work[index] = digit
            if search():
                return True
            work[index] = 0
        return False

    return work if search() else None


def _full_grid(rng: random.Random) -> list[int]:
    grid = [0] * CELLS

    def search() -> bool:
        index = _first_empty(grid)
        if index < 0:
            return True
        options = candidates(grid, index)
        rng.shuffle(options)
        for digit in options:
            grid[index] = digit
            if search():
                return True
            grid[index] = 0
        return False

    search()
    return grid


def generate(difficulty: Difficulty, rng: random.Random) -> tuple[list[int], list[int]]:
    """Return (puzzle, solution); the puzzle always has exactly one solution."""
    solution = _full_grid(rng)
    puzzle = solution[:]

    # Removal is done in mirrored pairs so the puzzle looks like a printed one.
    pairs = list({tuple(sorted((i, CELLS - 1 - i))) for i in range(CELLS)})
    rng.shuffle(pairs)

    clues = CELLS
    for pair in pairs:
        if clues <= difficulty.clues:
            break
        removed = [(i, puzzle[i]) for i in pair if puzzle[i]]
        for index, _ in removed:
            puzzle[index] = 0
        if count_solutions(puzzle) == 1:
            clues -= len(removed)
        else:
            for index, value in removed:
                puzzle[index] = value

    return puzzle, solution


def conflicts(grid: list[int]) -> set[int]:
    """Indices whose digit is repeated within a row, column or box."""
    bad: set[int] = set()
    for index, value in enumerate(grid):
        if value and any(grid[p] == value for p in PEERS[index]):
            bad.add(index)
    return bad

# tty-sudoku

A sudoku game that runs in the terminal. Pure Python + `curses`, no dependencies.

```
   TTY SUDOKU              02:41
   hard · entry

   +-------+-------+-------+
   |     4 |   7   | 3   6 |
   |     3 | 1     |   4 8 |
   | 8 5   |     3 | 1     |
   +-------+-------+-------+
   |     6 |   9   |       |
   | 3     | 6   8 |     2 |
   |       |   4   | 8     |
   +-------+-------+-------+
   |     7 | 9     |   8   |
   | 9 3   |     6 | 4     |
   | 5     |   8   | 2     |
   +-------+-------+-------+

   cell D4  notes -
```

## Run

```sh
uv run tty-sudoku              # pick difficulty from the menu
uv run tty-sudoku -d hard      # skip the menu
uv run tty-sudoku -s 42        # reproducible puzzles
uv run tty-sudoku --style unicode   # box-drawing borders
```

The border is ASCII by default because some terminal fonts are missing the
box-drawing glyphs; `--style unicode` switches to `┌─┬─┐` if yours has them.

Needs a terminal of at least 40x22.

## Difficulties

| Mode   | Clues |
| ------ | ----- |
| Easy   | 45    |
| Medium | 33    |
| Hard   | 25    |

Puzzles are generated fresh each round and always have exactly one solution.

## Keys

| Key                   | Action                                               |
| --------------------- | ---------------------------------------------------- |
| arrows / `hjkl`       | move the cursor (wraps at the edges)                 |
| `1`–`9`               | place a digit, or toggle a pencil mark in notes mode |
| `0` / space / `x` / ⌫ | erase the cell                                       |
| `p`                   | toggle notes mode                                    |
| `u`                   | undo                                                 |
| `m`                   | check mode: mark wrong digits, not just conflicts    |
| `n`                   | new puzzle, same difficulty                          |
| `d`                   | back to the difficulty menu                          |
| `q`                   | quit                                                 |

Given digits are bold white, your entries cyan, and digits that clash within a
row, column or box turn red. The cursor's row, column and box are shaded so the
cell you are working on is easy to place; on terminals with fewer than 16 colours
the shading falls back to underlining. The panel under the grid shows the pencil
marks for the current cell; cells holding pencil marks are drawn as a dim `*`.

# ID: 20221341 / w1956364
# Name: Kavindu Mihiranga

"""
Grid data structure for the sliding-ice puzzle (Task 2).

Builds on top of a plain 2-D list (the language's array type) as required
by the coursework. The key operation is `slide`: from any square, moving
in a cardinal direction carries the player across frictionless ice until
they hit a rock or the surrounding wall.

Coordinates are (row, col), zero-based internally. The coursework's
output format uses 1-based (column, row), which is handled by the solver
when it formats steps.
"""

from core.map_parser import ROCK

# The four cardinal directions as (d_row, d_col) and human-readable names.
DIRECTIONS = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1),
}


class Grid:
    """A parsed sliding-puzzle map with slide and neighbour queries."""

    def __init__(self, parsed):
        """`parsed` is the dict returned by core.map_parser.parse_*."""
        self.grid = parsed["grid"]
        self.width = parsed["width"]
        self.height = parsed["height"]
        self.start = parsed["start"]
        self.finish = parsed["finish"]

    def in_bounds(self, row, col):
        return 0 <= row < self.height and 0 <= col < self.width

    def is_rock(self, row, col):
        """True if the cell is a rock. Out-of-bounds counts as a wall."""
        if not self.in_bounds(row, col):
            return True
        return self.grid[row][col] == ROCK

    def slide(self, row, col, direction):
        """
        Slide from (row, col) in `direction` until blocked.

        The player keeps moving across ice until the next cell is a rock
        or wall. If the finish square is crossed mid-slide, the player
        stops there (the puzzle is solved on contact, as in the
        coursework example). Returns the final (row, col).

        A slide that cannot move at all returns the original square.
        """
        d_row, d_col = DIRECTIONS[direction]
        cur_row, cur_col = row, col
        while True:
            nxt_row, nxt_col = cur_row + d_row, cur_col + d_col
            # Blocked by a rock or the outer wall: stop here.
            if self.is_rock(nxt_row, nxt_col):
                return cur_row, cur_col
            cur_row, cur_col = nxt_row, nxt_col
            # The puzzle ends the instant the finish is reached.
            if (cur_row, cur_col) == self.finish:
                return cur_row, cur_col

    def neighbours(self, row, col):
        """
        All squares reachable in one move from (row, col).

        Yields (next_row, next_col, direction_name). Slides that don't
        change position (immediately blocked) are skipped, since they
        are not real moves.
        """
        for name in DIRECTIONS:
            dest = self.slide(row, col, name)
            if dest != (row, col):
                yield dest[0], dest[1], name

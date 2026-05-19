# ID: 20221341 / w1956364
# Name: Kavindu Mihiranga

"""
A* shortest-path solver for the sliding-ice puzzle (Task 4).

The search graph: nodes are squares the player can come to rest on
(start, finish, and every stop-position reachable by sliding). Each
edge is one slide and has a uniform cost of 1, because the puzzle asks
for the fewest *moves*, not the fewest tiles travelled.

Algorithm: A* with an admissible heuristic.

Heuristic:
    A single slide can cover at most max(width, height) - 1 tiles.
    So the number of moves still needed is at least
        ceil(manhattan_distance / max_slide_length).
    This never overestimates the true remaining move count, so A*
    is guaranteed to return a shortest path (optimal).

Output: a list of Step records describing each move, formatted to match
the coursework's expected output (1-based column,row coordinates).
"""

import heapq
from math import ceil

from core.grid import DIRECTIONS


class Step:
    """One line of the solution: a move from one square to another."""

    def __init__(self, index, action, row, col, direction=None):
        self.index = index          # 1-based step number
        self.action = action        # "Start", "Move", or "Done"
        self.row = row              # zero-based destination row
        self.col = col              # zero-based destination column
        self.direction = direction  # "up"/"down"/"left"/"right" or None

    def as_text(self):
        """Render the step in the coursework's output format."""
        # Coursework numbers squares left-to-right, top-to-bottom and
        # prints coordinates as (column, row), both 1-based.
        coord = f"({self.col + 1},{self.row + 1})"
        if self.action == "Start":
            return f"{self.index}. Start at {coord}"
        if self.action == "Done":
            return f"{self.index}. Done!"
        return f"{self.index}. Move {self.direction} to {coord}"


class SolveResult:
    """Outcome of a solve: the path, the step list, and search statistics."""

    def __init__(self, found, path, steps, nodes_expanded):
        self.found = found                    # bool: was the finish reached
        self.path = path                      # list of (row, col) positions
        self.steps = steps                    # list of Step objects
        self.nodes_expanded = nodes_expanded  # search-effort metric

    def steps_text(self):
        """The full solution as a list of formatted lines."""
        return [s.as_text() for s in self.steps]


def _heuristic(pos, finish, max_slide):
    """Admissible estimate of moves remaining from `pos` to `finish`."""
    manhattan = abs(pos[0] - finish[0]) + abs(pos[1] - finish[1])
    if manhattan == 0:
        return 0
    return ceil(manhattan / max_slide)


def solve(grid):
    """
    Find a shortest path from start to finish on `grid` using A*.

    Returns a SolveResult. If the finish is unreachable, `found` is False.
    """
    start = grid.start
    finish = grid.finish
    # Longest possible single slide on this map (used by the heuristic).
    max_slide = max(grid.width, grid.height) - 1
    max_slide = max(max_slide, 1)

    # Priority queue ordered by f = g + h. The counter breaks ties so
    # entries with equal f never have to compare positions.
    counter = 0
    open_heap = [(_heuristic(start, finish, max_slide), 0, counter, start)]

    # best_g[pos] = cheapest known move-count from start to pos.
    best_g = {start: 0}
    # came_from[pos] = (previous_pos, direction) for path reconstruction.
    came_from = {}
    nodes_expanded = 0

    while open_heap:
        _, g, _, current = heapq.heappop(open_heap)

        # A stale queue entry (a better route to `current` was found
        # after this one was pushed): skip it.
        if g > best_g.get(current, float("inf")):
            continue

        if current == finish:
            return _build_result(came_from, start, finish, nodes_expanded)

        nodes_expanded += 1

        for next_row, next_col, direction in grid.neighbours(*current):
            neighbour = (next_row, next_col)
            tentative_g = g + 1  # every slide costs one move
            if tentative_g < best_g.get(neighbour, float("inf")):
                best_g[neighbour] = tentative_g
                came_from[neighbour] = (current, direction)
                f = tentative_g + _heuristic(neighbour, finish, max_slide)
                counter += 1
                heapq.heappush(open_heap, (f, tentative_g, counter, neighbour))

    # Open set exhausted without reaching the finish.
    return SolveResult(False, [], [], nodes_expanded)


def _build_result(came_from, start, finish, nodes_expanded):
    """Reconstruct the path from `came_from` and format it into Steps."""
    # Walk backwards from finish to start.
    path = [finish]
    directions = []
    node = finish
    while node != start:
        prev, direction = came_from[node]
        directions.append(direction)
        path.append(prev)
        node = prev
    path.reverse()
    directions.reverse()

    # Build the step list. Step 1 is the start; then one Move per slide;
    # then a final Done.
    steps = [Step(1, "Start", start[0], start[1])]
    for i, direction in enumerate(directions):
        dest = path[i + 1]
        steps.append(
            Step(i + 2, "Move", dest[0], dest[1], direction.lower())
        )
    steps.append(Step(len(steps) + 1, "Done", finish[0], finish[1]))

    return SolveResult(True, path, steps, nodes_expanded)


# Direction vectors are imported so other modules (renderer/animation)
# can reuse the same definition without re-declaring it.
__all__ = ["solve", "Step", "SolveResult", "DIRECTIONS"]

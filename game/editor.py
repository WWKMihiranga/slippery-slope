# ID: 20221341 / w1956364
# Name: Kavindu Mihiranga

"""
In-game map editor.

Lets the player build or modify a map by clicking tiles, then save it
as a .txt file in the coursework format. The editor works on a plain
grid (list of list of chars) and validates before handing back a
playable Grid.
"""

from core.map_parser import (
    EMPTY, ROCK, START, FINISH, parse_lines, grid_to_text, MapParseError,
)
from core.grid import Grid

# The tools the editor cycles through. Clicking a tile applies the
# current tool. "erase" sets a tile back to empty ice.
TOOLS = ["rock", "start", "finish", "erase"]


class MapEditor:
    """Editable grid with click-to-edit and save-to-file support."""

    def __init__(self, width=12, height=12):
        self.set_blank(width, height)
        self.tool_index = 0
        self.message = ""

    @property
    def tool(self):
        return TOOLS[self.tool_index]

    def cycle_tool(self):
        self.tool_index = (self.tool_index + 1) % len(TOOLS)

    def set_blank(self, width, height):
        """Reset to an all-ice grid with a default S and F."""
        self.width = width
        self.height = height
        self.grid = [[EMPTY] * width for _ in range(height)]
        # Place start and finish in opposite corners by default.
        self.grid[0][0] = START
        self.grid[height - 1][width - 1] = FINISH
        self.message = "Blank map created."

    def load_from_grid(self, src_grid):
        """Copy an existing Grid into the editor for modification."""
        self.width = src_grid.width
        self.height = src_grid.height
        self.grid = [row[:] for row in src_grid.grid]
        self.message = "Map loaded into editor."

    def apply(self, row, col):
        """Apply the current tool to cell (row, col)."""
        if not (0 <= row < self.height and 0 <= col < self.width):
            return
        current = self.grid[row][col]

        if self.tool == "erase":
            self.grid[row][col] = EMPTY
            return

        if self.tool == "rock":
            # Toggle: clicking a rock removes it. Don't overwrite S/F.
            if current in (START, FINISH):
                return
            self.grid[row][col] = EMPTY if current == ROCK else ROCK
            return

        if self.tool == "start":
            self._clear_unique(START)
            self.grid[row][col] = START
            return

        if self.tool == "finish":
            self._clear_unique(FINISH)
            self.grid[row][col] = FINISH

    def _clear_unique(self, marker):
        """Remove any existing instance of a unique marker (S or F)."""
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] == marker:
                    self.grid[r][c] = EMPTY

    def to_grid(self):
        """
        Validate the current map and return a playable Grid.

        Raises MapParseError if the map is invalid (missing S/F, etc.).
        """
        parsed = parse_lines(grid_to_text(self.grid).split("\n"))
        return Grid(parsed)

    def save(self, path):
        """Validate then write the map to `path`. Returns True on success."""
        try:
            self.to_grid()  # validation only
        except MapParseError as exc:
            self.message = f"Cannot save: {exc}"
            return False
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(grid_to_text(self.grid) + "\n")
        except OSError as exc:
            self.message = f"Save failed: {exc}"
            return False
        self.message = f"Saved to {path}"
        return True

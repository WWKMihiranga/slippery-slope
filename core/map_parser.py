# ID: 20221341 / w1956364
# Name: Kavindu Mihiranga

"""
Map parser for sliding-ice puzzles.

Reads a map file in the coursework format and produces a validated 2-D grid.
File format: each line is a row; characters are
    '.'  empty ice square
    '0'  rock / obstacle
    'S'  start square (exactly one)
    'F'  finish square (exactly one)

Implements Task 3 of the coursework: determine width, height, and the
locations of the start, finish and rocks, for any file in this format.
"""

# Legal tile characters.
EMPTY, ROCK, START, FINISH = ".", "0", "S", "F"
LEGAL_CHARS = {EMPTY, ROCK, START, FINISH}


class MapParseError(Exception):
    """Raised when an input map file is malformed."""


def parse_lines(lines):
    """
    Parse an iterable of text lines into a grid (list of list of chars).

    Returns a dict: {"grid", "width", "height", "start", "finish"}.
    'start' and 'finish' are (row, col) tuples.

    Raises MapParseError for any structural problem so the caller can
    show a clean message instead of crashing.
    """
    # Strip newline characters but keep the rest; drop trailing blank lines.
    rows = [line.rstrip("\r\n") for line in lines]
    while rows and rows[-1].strip() == "":
        rows.pop()

    if not rows:
        raise MapParseError("Map file is empty.")

    width = len(rows[0])
    if width == 0:
        raise MapParseError("First row of the map is empty.")

    grid = []
    start = None
    finish = None

    for r, row in enumerate(rows):
        if len(row) != width:
            raise MapParseError(
                f"Row {r + 1} has width {len(row)}, expected {width}. "
                "All rows must be the same length."
            )
        cells = []
        for c, ch in enumerate(row):
            if ch not in LEGAL_CHARS:
                raise MapParseError(
                    f"Illegal character {ch!r} at row {r + 1}, column {c + 1}. "
                    f"Allowed: {sorted(LEGAL_CHARS)}."
                )
            if ch == START:
                if start is not None:
                    raise MapParseError("Map has more than one start (S).")
                start = (r, c)
            elif ch == FINISH:
                if finish is not None:
                    raise MapParseError("Map has more than one finish (F).")
                finish = (r, c)
            cells.append(ch)
        grid.append(cells)

    if start is None:
        raise MapParseError("Map has no start square (S).")
    if finish is None:
        raise MapParseError("Map has no finish square (F).")

    return {
        "grid": grid,
        "width": width,
        "height": len(grid),
        "start": start,
        "finish": finish,
    }


def parse_file(path):
    """Read and parse a map file from disk. Raises MapParseError on failure."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return parse_lines(handle.readlines())
    except FileNotFoundError:
        raise MapParseError(f"Map file not found: {path}")
    except OSError as exc:
        raise MapParseError(f"Could not read map file: {exc}")


def grid_to_text(grid):
    """Serialise a grid back into the .txt map format (used by the editor)."""
    return "\n".join("".join(row) for row in grid)

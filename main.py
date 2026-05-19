# ID: 20221341 / w1956364
# Name: Kavindu Mihiranga

"""
Sliding Puzzle Pathfinder - entry point.

A game built on the 5SENG003W Algorithms coursework: solving sliding-ice
puzzles with the A* shortest-path algorithm. Run this file to start.

    python main.py

Controls are on-screen: Start solves and animates the shortest path;
Load Map opens a .txt map; the Editor lets you build your own maps.
"""

from game.app import Game


def main():
    Game().run()


if __name__ == "__main__":
    main()

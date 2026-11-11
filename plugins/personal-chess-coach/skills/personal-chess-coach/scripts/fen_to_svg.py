#!/usr/bin/env python3
"""
usage: fen_to_svg.py [-h] [-s SIZE] [--flip] -f FEN (-o OUT | -d DIR)

Convert FEN board description to Scaled Vector Graphics.

options:
  -h, --help            show this help message and exit
  -s SIZE, --size SIZE  The size of the svg
  --flip                Show the board from Black's side
  -f FEN, --fen FEN     The input FEN
  -o OUT, --out OUT     The file to write the SVG to
  -d DIR, --dir DIR     Write the SVG into DIR, named after the position
                        (<hash>.svg, or <hash>-black.svg with --flip),
                        and print the file name

With -d, the name is a hash of the first four FEN fields (pieces, side to
move, castling rights, en passant), so the same position always gets the
same file, whatever the move counters, and different positions never clash.

Exit codes: 0 ok, 2 bad arguments, 3 python-chess not installed.
"""

import argparse
import hashlib
import os
import sys

try:
    import chess
    import chess.svg
except ImportError:
    # Exit code 3 tells the skill to install the package and retry
    # (see rendering/show-board.md). Not 2: argparse uses 2 for bad arguments.
    print("python-chess is not installed: run `pip install chess`", file=sys.stderr)
    sys.exit(3)

FEN_EXAMPLE = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert FEN board description to Scaled Vector Graphics."
    )
    parser.add_argument("-s", "--size", type=int, default=480, help="The size of the svg")
    parser.add_argument("--flip", action="store_true", help="Show the board from Black's side")
    parser.add_argument("-f", "--fen", type=str, required=True, help="The input FEN")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("-o", "--out", type=str, help="The file to write the SVG to")
    target.add_argument(
        "-d", "--dir", type=str,
        help="Write the SVG into DIR, named after the position, and print the file name",
    )
    return parser.parse_args()


def position_file_name(fen, flip=False):
    """File name for a position: hash of the first four FEN fields."""
    key = " ".join(fen.split()[:4])
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]
    return f"{digest}-black.svg" if flip else f"{digest}.svg"


def fen_to_svg(fen, size=480, flip=False):
    board = chess.Board(fen)
    orientation = chess.BLACK if flip else chess.WHITE
    return chess.svg.board(board=board, size=size, orientation=orientation)


def main() -> None:
    args = parse_args()
    svg = fen_to_svg(args.fen, args.size, args.flip)

    if args.dir:
        os.makedirs(args.dir, exist_ok=True)
        name = position_file_name(args.fen, args.flip)
        path = os.path.join(args.dir, name)
    else:
        name = None
        path = args.out

    with open(path, "w") as f:
        f.write(svg)

    if name:
        print(name)


if __name__ == "__main__":
    main()

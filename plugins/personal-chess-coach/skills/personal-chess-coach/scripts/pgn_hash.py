#!/usr/bin/env python3
"""
usage: pgn_hash.py [-h] (-f FILE | -p PGN) [--legacy | --both]
       pgn_hash.py --update-records DIR [--dry-run]

A stable SHA-256 hash of a chess game, used by F37 (game records) and F08
(analyzed_games in the profile) to recognise a game they have seen before.

The hash is over the game itself, not over how its PGN is written: the starting
position (the first four FEN fields: the standard start unless [FEN] says
otherwise) and the main-line moves in canonical SAN, as read by python-chess.
So headers, comments, variations, NAGs, move numbers ("1.e4" or "1. e4", a
repeated "1... e5"), castling with zeros, "e8Q" for "e8=Q", missing "+"/"#"
and the result marker make no difference, and the same moves from another
starting position give another hash. games.py identifies games the same way.

options:
  -f FILE, --file FILE  a .pgn file (the first game in it)
  -p PGN, --pgn PGN     PGN text
  --legacy              the hash of skill versions before 0.4.4: over the
                        movetext as written. Only to find records and profile
                        entries made with those versions
  --both                print the hash, then the legacy hash, one per line
  --update-records DIR  one-off: give the game records in DIR (Game_Analysis/)
                        the hash, where they still hold their legacy hash.
                        Only the `hash:` line changes. Lists records that turn
                        out to be the same game; never merges them
  --dry-run             with --update-records: report, change nothing

Exit codes: 0 ok, 1 unreadable PGN or file, 3 python-chess not installed.
"""
import argparse
import hashlib
import io
import os
import re
import sys

try:
    import chess
    import chess.pgn
except ImportError:
    print("python-chess is not installed: run `pip install chess`", file=sys.stderr)
    sys.exit(3)


class Unreadable(Exception):
    pass


def try_game_hash(pgn: str) -> str:
    """SHA-256 of '<first four FEN fields> <SAN moves>' of the first game.
    Raises Unreadable with the reason when there is no readable game."""
    game = chess.pgn.read_game(io.StringIO(pgn))
    if game is None:
        raise Unreadable("no game found in the PGN")
    if game.errors:
        raise Unreadable(f"cannot read the PGN: {game.errors[0]}")
    board = game.board()
    start = " ".join(board.fen().split()[:4])
    sans = []
    for move in game.mainline_moves():
        sans.append(board.san(move))
        board.push(move)
    if not sans:
        raise Unreadable("the PGN has no moves")
    return hashlib.sha256(f"{start} {' '.join(sans)}".encode("utf-8")).hexdigest()


def game_hash(pgn: str) -> str:
    try:
        return try_game_hash(pgn)
    except Unreadable as e:
        fail(str(e))


# ---------------------------------------------------------------- legacy
# Unchanged from before 0.4.4, quirks included (a "*" result is not stripped),
# so it gives exactly the hash stored in older records and profiles.
def normalize_movetext(pgn: str) -> str:
    text = pgn
    text = re.sub(r'\[[^\]]*\]', '', text)
    text = re.sub(r'\{[^}]*\}', '', text)
    for _ in range(5):
        text = re.sub(r'\([^()]*\)', '', text)
    text = re.sub(r'\$\d+', '', text)
    text = re.sub(r'[!?]+', '', text)
    text = re.sub(r'\b(1-0|0-1|1/2-1/2|\*)\s*$', '', text.strip())
    text = ' '.join(text.split())
    return text.strip()


def legacy_hash(pgn: str) -> str:
    return hashlib.sha256(normalize_movetext(pgn).encode('utf-8')).hexdigest()


# ---------------------------------------------------------------- records
HASH_LINE = re.compile(r'^hash:[ \t]*"?([0-9a-fA-F]*)"?[ \t]*$', re.M)


def update_records(folder: str, dry_run: bool) -> None:
    if not os.path.isdir(folder):
        fail(f"no folder {folder}")
    counts = {"updated": 0, "up to date": 0, "left unchanged": 0}
    by_hash: dict[str, list[str]] = {}
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not name.endswith(".md") or not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        record = name[:-3]
        end = text.find("\n---", 4) if text.startswith("---\n") else -1
        line = HASH_LINE.search(text, 0, end) if end > 0 else None
        block = re.search(r"```pgn\s*\n(.*?)```", text, re.S)
        if line is None or block is None:
            continue  # not a game record
        try:
            new = try_game_hash(block.group(1))
        except Unreadable as e:
            counts["left unchanged"] += 1
            print(f"left unchanged: {record} ({e})")
            continue
        by_hash.setdefault(new, []).append(record)
        stored = line.group(1).lower()
        if stored == new:
            counts["up to date"] += 1
        elif stored == legacy_hash(block.group(1)):
            counts["updated"] += 1
            print(f"{'would update' if dry_run else 'updated'}: {record}")
            if not dry_run:
                updated = text[: line.start()] + f"hash: {new}" + text[line.end():]
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(updated)
        else:
            counts["left unchanged"] += 1
            print(f"left unchanged: {record} (its hash matches neither the game nor its legacy hash)")
    summary = ", ".join(f"{k} {v}" for k, v in counts.items())
    print(("dry run: " if dry_run else "") + summary)
    for records in by_hash.values():
        if len(records) > 1:
            print("same game: " + ", ".join(records))


# ---------------------------------------------------------------- main
def fail(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(1)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="A stable SHA-256 hash of a chess game.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('-f', '--file', help='a .pgn file (the first game in it)')
    source.add_argument('-p', '--pgn', help='PGN text')
    source.add_argument('--update-records', metavar='DIR',
                        help='one-off: give the game records in DIR the hash where they hold the legacy hash')
    parser.add_argument('--dry-run', action='store_true', help='with --update-records: change nothing')
    kind = parser.add_mutually_exclusive_group()
    kind.add_argument('--legacy', action='store_true', help='the hash of skill versions before 0.4.4')
    kind.add_argument('--both', action='store_true', help='the hash, then the legacy hash')
    return parser.parse_args(argv)


def main(argv: list[str]) -> None:
    args = parse_args(argv)
    if args.update_records:
        update_records(args.update_records, args.dry_run)
        return
    if args.file:
        try:
            with open(args.file, encoding='utf-8', errors='replace') as fh:
                pgn = fh.read()
        except OSError as e:
            fail(f"cannot read {args.file}: {e.strerror}")
    else:
        pgn = args.pgn

    if args.legacy:
        print(legacy_hash(pgn))
    elif args.both:
        print(game_hash(pgn))
        print(legacy_hash(pgn))
    else:
        print(game_hash(pgn))


if __name__ == '__main__':
    main(sys.argv[1:])

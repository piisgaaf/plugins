#!/usr/bin/env python3
"""games.py — the player's games: what there is, what was analysed, what was searched.

Used by F14 (r04-train-my-weaknesses/f14-find-missed-tactics.md). Reads the PGN
files in the games folder (any depth, several games per file) and the game
records in Game_Analysis/ (F37), and lists every game once, with the side the
player had, whether it has a game record ("analysed") and whether F14 already
searched it for puzzles ("searched", logged in <Puzzles>/searched.json).

A game is identified by its moves (read with python-chess) and its starting
position, not by how the PGN is written: the same game exported by two programs
("1.e4" or "1. e4", other headers, comments) is the same game. Its id is the
first 10 hex digits of that key.

The script never reads the Player Profile and never changes a PGN file or a game
record: the skill passes the player's names with --player.

usage:
  games.py [--games DIR] [--records DIR] [--book DIR] [--player NAME ...] list
           [--unsearched] [--analysed | --not-analysed] [--since YYYY-MM-DD] [--json]
  games.py [same options] pgn <id>
  games.py [same options] searched <id> --found N

Exit codes: 0 ok, 1 bad input, 3 python-chess not installed.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import io
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field

try:
    import chess
    import chess.pgn
except ImportError:
    print("python-chess is not installed: run `pip install chess`", file=sys.stderr)
    sys.exit(3)

LOG_NAME = "searched.json"
ID_LENGTH = 10


@dataclass
class Game:
    id: str
    key: str
    date: str
    white: str
    black: str
    result: str
    plies: int
    side: str | None = None
    file: str | None = None
    index: int | None = None
    record: str | None = None
    searched: str | None = None
    puzzles: int | None = None
    pgn: str = field(default="", repr=False)

    @property
    def label(self) -> str:
        where = f" ({self.file} #{self.index})" if self.file else ""
        return f"{self.white} – {self.black}, {self.date or 'no date'}{where}"


# ---------------------------------------------------------------- reading games
def read_pgn_games(text: str) -> list[chess.pgn.Game]:
    """All games in a PGN text. [Variant] lines are dropped: Scid exports misuse
    them for the opening name, and python-chess would read a chess variant."""
    text = "".join(line for line in text.splitlines(keepends=True) if not line.startswith("[Variant "))
    stream, games = io.StringIO(text), []
    while (game := chess.pgn.read_game(stream)) is not None:
        games.append(game)
    return games


def move_key(game: chess.pgn.Game) -> tuple[str, int] | None:
    """The game's identity: its starting position and main-line moves in SAN.
    None for a game without moves."""
    board = game.board()
    start = " ".join(board.fen().split()[:4])
    sans = []
    for move in game.mainline_moves():
        sans.append(board.san(move))
        board.push(move)
    if not sans:
        return None
    return hashlib.sha1(f"{start} {' '.join(sans)}".encode("utf-8")).hexdigest(), len(sans)


def pgn_date(value: str) -> str:
    """'2026.11.15' -> '2026-11-15'; unknown or partial dates -> ''."""
    m = re.fullmatch(r"(\d{4})[.\-/](\d{2})[.\-/](\d{2})", value or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def name_tokens(name: str) -> frozenset[str]:
    return frozenset(re.findall(r"\w+", name.casefold()))


def player_side(white: str, black: str, players: list[str]) -> str | None:
    """'white' or 'black' when exactly one header matches one of the player's
    names, ignoring case and word order ("Rijken, Pieter" is "Pieter Rijken")."""
    wanted = [name_tokens(p) for p in players if name_tokens(p)]

    def matches(header: str) -> bool:
        return bool(name_tokens(header)) and name_tokens(header) in wanted

    w, b = matches(white), matches(black)
    return "white" if w and not b else "black" if b and not w else None


def game_from(pgn_game: chess.pgn.Game, players: list[str]) -> Game | None:
    keyed = move_key(pgn_game)
    if keyed is None:
        return None
    key, plies = keyed
    h = pgn_game.headers
    white, black = h.get("White", "?"), h.get("Black", "?")
    exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
    return Game(id=key[:ID_LENGTH], key=key, date=pgn_date(h.get("Date", "")), white=white, black=black,
                result=h.get("Result", "*"), plies=plies, side=player_side(white, black, players),
                pgn=pgn_game.accept(exporter))


def read_text(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def folder_games(folder: str, players: list[str]) -> list[Game]:
    games = []
    for root, dirs, files in os.walk(folder):
        dirs.sort()
        for name in sorted(files):
            if not name.lower().endswith(".pgn"):
                continue
            path = os.path.join(root, name)
            for i, pgn_game in enumerate(read_pgn_games(read_text(path)), 1):
                game = game_from(pgn_game, players)
                if game:
                    game.file, game.index = os.path.relpath(path, folder), i
                    games.append(game)
    return games


# ---------------------------------------------------------------- game records
def front_matter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    data = {}
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*\"?([^\"]*)\"?\s*$", line)
        if m:
            data[m.group(1)] = m.group(2).strip()
    return data


def record_games(folder: str, players: list[str]) -> list[Game]:
    games = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not name.endswith(".md") or not os.path.isfile(path):
            continue
        text = read_text(path)
        block = re.search(r"```pgn\s*\n(.*?)```", text, re.S)
        if not block:
            continue
        pgn_games = read_pgn_games(block.group(1))
        game = game_from(pgn_games[0], players) if pgn_games else None
        if game is None:
            continue
        meta = front_matter(text)
        game.record = name[:-3]
        if meta.get("player_color") in ("white", "black"):
            game.side = meta["player_color"]
        game.date = meta.get("date", "") or game.date
        games.append(game)
    return games


# ---------------------------------------------------------------- the search log
def load_log(book: str | None) -> dict[str, dict]:
    if not book:
        return {}
    try:
        with open(os.path.join(book, LOG_NAME), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_log(book: str, log: dict[str, dict]) -> None:
    os.makedirs(book, exist_ok=True)
    with open(os.path.join(book, LOG_NAME), "w", encoding="utf-8") as f:
        json.dump(log, f, indent=1, ensure_ascii=False, sort_keys=True)


# ---------------------------------------------------------------- all games
def all_games(args: argparse.Namespace) -> list[Game]:
    """Folder games and records, each game once: a record adds its name (and its
    side, when the names do not tell) to the same game from the folder."""
    by_key: dict[str, Game] = {}
    for game in folder_games(args.games, args.player) if args.games else []:
        by_key.setdefault(game.key, game)
    for game in record_games(args.records, args.player) if args.records else []:
        if game.key in by_key:
            known = by_key[game.key]
            known.record = known.record or game.record
            known.side = known.side or game.side
        else:
            by_key[game.key] = game
    log = load_log(args.book)
    for game in by_key.values():
        if game.key in log:
            game.searched, game.puzzles = log[game.key].get("date"), log[game.key].get("puzzles")
    return sorted(by_key.values(), key=lambda g: (g.date or "", g.file or "", g.index or 0), reverse=True)


def find(games: list[Game], game_id: str) -> Game:
    hits = [g for g in games if g.key.startswith(game_id)]
    if len(hits) != 1:
        fail(f"no game with id {game_id}" if not hits else f"id {game_id} is not unique")
    return hits[0]


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------- commands
def cmd_list(args: argparse.Namespace) -> None:
    games = all_games(args)
    total = len(games)
    analysed = sum(1 for g in games if g.record)
    searched = sum(1 for g in games if g.searched)
    unknown = sum(1 for g in games if g.side is None)
    if args.unsearched:
        games = [g for g in games if not g.searched]
    if args.analysed:
        games = [g for g in games if g.record]
    if args.not_analysed:
        games = [g for g in games if not g.record]
    if args.since:
        games = [g for g in games if g.date and g.date >= args.since]

    if args.json:
        for g in games:
            row = {k: v for k, v in asdict(g).items() if k not in ("key", "pgn")}
            row["label"] = g.label
            print(json.dumps(row, ensure_ascii=False))
        return

    print(f"{total} games: {analysed} analysed (game record), {searched} searched for puzzles, "
          f"{total - searched} not searched yet." + (f" Your side is unknown in {unknown}." if unknown else ""))
    if not games:
        print("No games match.")
        return
    print()
    print("| # | Id | Date | Game | Result | You | Analysed | Puzzles searched |")
    print("|---|---|---|---|---|---|---|---|")
    for i, g in enumerate(games, 1):
        record = f"[[{g.record}]]" if g.record else "—"
        done = f"{g.searched} ({g.puzzles})" if g.searched else "—"
        side = g.side.capitalize() if g.side else "?"
        print(f"| {i} | {g.id} | {g.date or '—'} | {g.white} – {g.black} | {g.result} | {side} | {record} | {done} |")


def cmd_pgn(args: argparse.Namespace) -> None:
    print(find(all_games(args), args.id).pgn)


def cmd_searched(args: argparse.Namespace) -> None:
    if not args.book:
        fail("searched needs --book (the Puzzles folder)")
    if args.found < 0:
        fail("--found must be 0 or more")
    game = find(all_games(args), args.id)
    log = load_log(args.book)
    log[game.key] = {"date": datetime.date.today().isoformat(), "puzzles": args.found, "game": game.label}
    save_log(args.book, log)
    print(f"searched: {game.label}, {args.found} puzzle(s)")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="The player's games: analysed and searched for puzzles.")
    p.add_argument("--games", help="the games folder: PGN files, any depth")
    p.add_argument("--records", help="the Game_Analysis folder with game records")
    p.add_argument("--book", help="the Puzzles folder, where searched.json is kept")
    p.add_argument("--player", action="append", default=[],
                   help="a name the player appears under in White/Black (repeat for each name, alias, username)")
    sub = p.add_subparsers(dest="command", required=True)

    ls = sub.add_parser("list", help="list the games, newest first")
    ls.add_argument("--unsearched", action="store_true", help="only games not searched for puzzles")
    which = ls.add_mutually_exclusive_group()
    which.add_argument("--analysed", action="store_true", help="only games with a game record")
    which.add_argument("--not-analysed", action="store_true", help="only games without a game record")
    ls.add_argument("--since", help="only games on or after this date (YYYY-MM-DD)")
    ls.add_argument("--json", action="store_true", help="one JSON object per game instead of a table")
    ls.set_defaults(run=cmd_list)

    pg = sub.add_parser("pgn", help="print one game's PGN")
    pg.add_argument("id")
    pg.set_defaults(run=cmd_pgn)

    se = sub.add_parser("searched", help="log a game as searched for puzzles")
    se.add_argument("id")
    se.add_argument("--found", type=int, required=True, help="the number of puzzles found")
    se.set_defaults(run=cmd_searched)
    return p


def main(argv: list[str]) -> None:
    args = parser().parse_args(argv)
    for name in ("games", "records"):
        path = getattr(args, name)
        if path and not os.path.isdir(path):
            fail(f"--{name}: no folder {path}")
    if not args.games and not args.records:
        fail("give --games, --records or both")
    since = getattr(args, "since", None)
    if since and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", since):
        fail("--since takes a date as YYYY-MM-DD")
    args.run(args)


if __name__ == "__main__":
    main(sys.argv[1:])

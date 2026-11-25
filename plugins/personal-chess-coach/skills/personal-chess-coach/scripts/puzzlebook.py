#!/usr/bin/env python3
"""puzzlebook.py — the puzzle book (F14–F16): one Markdown note per puzzle.

Used by F14, F15 and F16 (r04-train-my-weaknesses/). Every write to a puzzle note
goes through this script; the skill never edits one by hand. Which games were
searched for puzzles is kept by games.py, not here. Notes are built from templates/puzzle.md; after that only their front matter is
rewritten (and, by `update`, the solution and PGN the script wrote), so text the user
adds under "My notes" is kept.

  puzzlebook.py --dir <Puzzles> add --fen FEN --solver white|black --source S
                --solution "SAN ..." --theme T [--record NAME | --game LABEL] [--date YYYY-MM-DD]
                [--move "24.Rxf7"] [--line "SAN ..."] [--motif M] [--idea TEXT]
                --pgn -                   (the puzzle PGN on stdin)
  puzzlebook.py --dir <Puzzles> next [--fresh] [--source S] [--motif M] [--theme T]
                [--status S] [--since YYYY-MM-DD] [--exclude NOTE ...]
  puzzlebook.py --dir <Puzzles> record <note> solved|solved_with_hint|failed
  puzzlebook.py --dir <Puzzles> update <note> --solution "SAN ..." [--theme T] --pgn -
                                            a corrected solution (PGN on stdin); keeps the
                                            history, sources and the user's notes
  puzzlebook.py --dir <Puzzles> remove <note> [--force]
                                            the note and its board; --force for a note that
                                            was tried or has the user's own notes
  puzzlebook.py --dir <Puzzles> stats [--since YYYY-MM-DD]
  puzzlebook.py --dir <Puzzles> export <out.pgn> [--status S] [--source S] [--motif M]
  puzzlebook.py check --fen FEN --solution "SAN ..." --step N "<answer>"
                                            check an answer (no folder needed)

`update` and `remove` are only run after the user's yes.

The note for a position is "Puzzle <hash>.md", where <hash> is the board's file
name from fen_to_svg.py -d (first four FEN fields), so the same position is always
the same note. `add` on an existing note only adds the new source.

Exit codes: 0 ok, 1 bad input, 3 python-chess not installed.
"""
import datetime
import hashlib
import json
import os
import re
import sys

try:
    import chess
except ImportError:
    print("python-chess is not installed: run `pip install chess`", file=sys.stderr)
    sys.exit(3)

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "puzzle.md")
SOURCES = ("own_mistake", "opponent_missed", "variation")
THEMES = ("mate", "material", "defence")
RESULTS = ("solved", "solved_with_hint", "failed")
STATUSES = ("new",) + RESULTS
# Front matter keys in the order they are written; unknown keys follow.
KEYS = ("fen", "solver", "source", "sources", "move", "line", "motif", "theme", "solution",
        "solver_moves", "status", "attempts", "last_tried", "history", "added", "tags")
LISTS = ("sources", "history", "tags")
# Order of "next": new first, then failed, then solved with a hint, then solved.
STATUS_RANK = {"new": 0, "failed": 1, "solved_with_hint": 2, "solved": 3}


def today():
    return datetime.date.today().isoformat()


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def position_hash(fen):
    """Same as fen_to_svg.py position_file_name, without the extension."""
    key = " ".join(fen.split()[:4])
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]


# ---------------------------------------------------------------- front matter
def split_note(text):
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end < 0:
        return None, text
    return text[4:end], text[end + 4:]


def unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
        return v.replace('\\"', '"') if v else v
    return v


def parse_front(front):
    """A small YAML subset: `key: value`, `key: [a, b]` and block lists (`  - a`).
    Obsidian rewrites inline lists as block lists when a property is edited."""
    data, key = {}, None
    for line in front.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^\s+-\s*(.*)$", line)
        if m and key is not None:
            if not isinstance(data.get(key), list):
                data[key] = []
            data[key].append(unquote(m.group(1)))
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [unquote(x) for x in re.findall(r'"[^"]*"|\'[^\']*\'|[^,]+', inner) if x.strip()] if inner else []
        else:
            data[key] = unquote(value)
    return data


def quote(v):
    s = str(v)
    if s == "" or re.search(r'[:#\[\]{},"\'&*!|>%@`]', s) or s != s.strip():
        return '"' + s.replace('"', '\\"') + '"'
    return s


def dump_front(data):
    out = []
    for key in list(KEYS) + [k for k in data if k not in KEYS]:
        if key not in data:
            continue
        v = data[key]
        if key in LISTS or isinstance(v, list):
            items = v if isinstance(v, list) else ([v] if v else [])
            out.append(f"{key}:" if items else f"{key}: []")
            out += [f"  - {quote(x)}" for x in items]
        else:
            out.append(f"{key}: {quote(v)}")
    return "\n".join(out)


def read_note(path):
    text = open(path, encoding="utf-8").read()
    front, body = split_note(text)
    if front is None:
        fail(f"{path}: no front matter")
    return parse_front(front), body


def write_note(path, data, body):
    open(path, "w", encoding="utf-8").write("---\n" + dump_front(data) + "\n---" + body)


def notes(folder):
    if not os.path.isdir(folder):
        return []
    out = []
    for name in sorted(os.listdir(folder)):
        if name.startswith("Puzzle ") and name.endswith(".md"):
            path = os.path.join(folder, name)
            data, _ = read_note(path)
            out.append((path, data))
    return out


# ---------------------------------------------------------------- chess helpers
def board_for(fen):
    try:
        return chess.Board(fen)
    except ValueError as e:
        fail(f"bad FEN {fen!r}: {e}")


def movetext(fen, sans):
    """Numbered movetext from fen; checks every move is legal."""
    b, out = board_for(fen), []
    for i, s in enumerate(sans):
        try:
            move = b.parse_san(s)
        except ValueError:
            fail(f"move {i + 1} ({s}) is not legal in this line from {fen}")
        san = b.san(move)
        if b.turn == chess.WHITE:
            out.append(f"{b.fullmove_number}.{san}")
        else:
            out.append(f"{b.fullmove_number}...{san}" if not out else san)
        b.push(move)
    return " ".join(out)


def task_text(solver, theme):
    side = "White" if solver == "white" else "Black"
    return {"mate": f"{side} to move and mate.", "material": f"{side} to move and win.",
            "defence": f"{side} to move: find the only move."}[theme]


def read_pgn(args, fen, flag):
    """The puzzle PGN from stdin (--pgn -): it must start from fen's position."""
    pgn = sys.stdin.read() if opt(args, "--pgn") == "-" else ""
    m = re.search(r'\[FEN "([^"]+)"\]', pgn)
    if not m or " ".join(m.group(1).split()[:4]) != " ".join(fen.split()[:4]):
        fail(f"the PGN on stdin must have a [FEN] tag with the same position as {flag}")
    return pgn


def solution_movetext(fen, solution):
    sans = solution.split()
    text = movetext(fen, sans)
    if len(sans) % 2 == 0:
        fail("a solution ends with a solver move: it has an odd number of moves")
    return sans, text


# ---------------------------------------------------------------- notes by name
def note_file(folder, name):
    path = name if os.path.isabs(name) else os.path.join(folder, os.path.basename(name))
    if not os.path.exists(path):
        fail(f"no note {path}")
    return path


def split_own_notes(body):
    """The body before "## My notes" (written by this script) and the user's part."""
    i = body.find("\n## My notes")
    return (body, "") if i < 0 else (body[:i], body[i:])


def own_notes(body):
    """The text the user wrote under "## My notes", without the heading."""
    return split_own_notes(body)[1].replace("\n## My notes", "", 1).strip()


def board_of(body):
    m = re.search(r"!\[\[([^\]|]+\.svg)", body)
    return m.group(1) if m else None


# ---------------------------------------------------------------- add
def opt(args, name, default=None):
    if name in args:
        i = args.index(name)
        if i + 1 >= len(args):
            fail(f"{name} needs a value")
        return args[i + 1]
    return default


def opts_many(args, name):
    if name not in args:
        return []
    i, out = args.index(name) + 1, []
    while i < len(args) and not args[i].startswith("--"):
        out.append(args[i]); i += 1
    return out


def context_line(source, record, game, date, move, line_text):
    if record:
        where = f"[[{record}]]"
    elif game:
        where = f"your game {game}"
    else:
        where = f"your game of {date}" if date else "one of your games"
    if source == "own_mistake":
        return f"From {where}: you played {move} here." if move else f"From {where}."
    if source == "opponent_missed":
        return (f"From {where}: your opponent played {move} here and missed this." if move
                else f"From {where}: a chance your opponent missed.")
    return (f"From {where}: a position that could have arisen after {line_text}, instead of {move}."
            if move else f"From {where}: a position from the engine's line.")


def cmd_add(folder, args):
    fen, solver, source = opt(args, "--fen"), opt(args, "--solver"), opt(args, "--source")
    solution, theme = opt(args, "--solution"), opt(args, "--theme")
    if not all([fen, solver, source, solution, theme]):
        fail("add needs --fen, --solver, --source, --solution and --theme")
    if solver not in ("white", "black") or source not in SOURCES or theme not in THEMES:
        fail(f"--solver white|black, --source {'|'.join(SOURCES)}, --theme {'|'.join(THEMES)}")
    board = board_for(fen)
    if (board.turn == chess.WHITE) != (solver == "white"):
        fail(f"the solver ({solver}) is not the side to move in the FEN")
    sans, solution_text = solution_movetext(fen, solution)
    pgn = read_pgn(args, fen, "--fen")

    record, date, move = opt(args, "--record", ""), opt(args, "--date", ""), opt(args, "--move", "")
    game = opt(args, "--game", "")
    if record and game:
        fail("give --record or --game, not both")
    line = opt(args, "--line", "")
    h = position_hash(fen)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"Puzzle {h}.md")
    # A game record is linked; a game from the games folder is named by its label.
    link = f"[[{record}]]" if record else game

    if os.path.exists(path):
        data, body = read_note(path)
        srcs = data.get("sources") or []
        srcs = srcs if isinstance(srcs, list) else [srcs]
        if link and link not in srcs:
            data["sources"] = srcs + [link]
            write_note(path, data, body)
            print(f"exists, source added: {os.path.basename(path)}")
        else:
            print(f"exists: {os.path.basename(path)}")
        return

    # A variation's line starts where `move` was played: number it from that move.
    line_text = ""
    if line and move:
        num = re.match(r"(\d+)(\.\.\.|…|\.)", move)
        if num:
            n, black = int(num.group(1)), num.group(2) != "."
            parts, b_turn = [], black
            for i, s in enumerate(line.split()):
                if not b_turn:
                    parts.append(f"{n}.{s}")
                else:
                    parts.append(f"{n}...{s}" if i == 0 else s)
                    n += 1
                b_turn = not b_turn
            line_text = " ".join(parts)
        else:
            line_text = line
    task = task_text(solver, theme)
    board_name = f"{h}-black.svg" if solver == "black" else f"{h}.svg"
    values = {
        "fen": fen, "solver": solver, "source": source, "move": move, "line": line_text,
        "motif": opt(args, "--motif", ""), "theme": theme, "solution": solution_text,
        "solver_moves": str((len(sans) + 1) // 2), "added": today(), "hash": h, "board": board_name,
        "task": task, "context": context_line(source, record, game, date, move, line_text),
        "idea": opt(args, "--idea", "") or "(The idea is added after you solve it.)",
        "pgn": pgn.strip(),
    }
    template = open(TEMPLATE, encoding="utf-8").read()
    text = re.sub(r"\{\{(\w+)\}\}", lambda mm: values.get(mm.group(1), mm.group(0)), template)
    front, body = split_note(text)
    data = parse_front(front)
    data["sources"] = [link] if link else []
    data["history"], data["tags"] = [], ["puzzle"]
    data["status"], data["attempts"], data["last_tried"] = "new", "0", ""
    write_note(path, data, body)
    print(f"added: {os.path.basename(path)} (board {board_name})")


# ---------------------------------------------------------------- next / record / stats
def matches(data, args):
    for flag in ("--source", "--motif", "--theme", "--status"):
        want = opt(args, flag)
        if want and data.get(flag[2:]) != want:
            return False
    if "--fresh" in args and data.get("source") == "own_mistake":
        return False
    since = opt(args, "--since")
    if since and (data.get("added") or "") < since:
        return False
    return True


def cmd_next(folder, args):
    exclude = {os.path.basename(x) for x in opts_many(args, "--exclude")}
    pool = [(p, d) for p, d in notes(folder) if matches(d, args) and os.path.basename(p) not in exclude]
    if not pool:
        print(json.dumps({"note": None, "left": 0}))
        return
    t = today()
    # Puzzles tried today come last, so a session does not repeat itself.
    pool.sort(key=lambda pd: (pd[1].get("last_tried") == t, STATUS_RANK.get(pd[1].get("status"), 9),
                              pd[1].get("last_tried") or "", pd[1].get("added") or ""))
    path, data = pool[0]
    out = {k: data.get(k) for k in ("fen", "solver", "source", "sources", "move", "line", "motif",
                                    "theme", "solution", "solver_moves", "status", "attempts")}
    for k in ("solver_moves", "attempts"):
        out[k] = int(out[k] or 0)
    out["note"], out["left"] = os.path.basename(path), len(pool)
    print(json.dumps(out, ensure_ascii=False))


def cmd_record(folder, args):
    if len(args) != 2 or args[1] not in RESULTS:
        fail(f"record <note> {'|'.join(RESULTS)}")
    path = note_file(folder, args[0])
    data, body = read_note(path)
    data["status"] = args[1]
    data["attempts"] = str(int(data.get("attempts") or 0) + 1)
    data["last_tried"] = today()
    hist = data.get("history") or []
    data["history"] = (hist if isinstance(hist, list) else [hist]) + [f"{today()}: {args[1]}"]
    write_note(path, data, body)
    print(f"{os.path.basename(path)}: {args[1]}, attempts {data['attempts']}")


# ---------------------------------------------------------------- update / remove
def cmd_update(folder, args):
    if not args or args[0].startswith("--"):
        fail('update <note> --solution "SAN ..." [--theme T] --pgn -')
    path, rest = note_file(folder, args[0]), args[1:]
    data, body = read_note(path)
    solution = opt(rest, "--solution")
    if not solution:
        fail("update needs --solution")
    theme = opt(rest, "--theme", data.get("theme"))
    if theme not in THEMES:
        fail(f"--theme {'|'.join(THEMES)}")
    fen, solver = data.get("fen") or "", data.get("solver")
    sans, solution_text = solution_movetext(fen, solution)
    pgn = read_pgn(rest, fen, "the note's fen")

    # Only the part this script wrote changes; the user's notes stay as they are.
    head, mine = split_own_notes(body)
    head, found = re.subn(r"(> \[!success\]- Solution\n> )[^\n]*",
                          lambda m: m.group(1) + solution_text, head, count=1)
    if not found:
        fail(f"{os.path.basename(path)}: no Solution callout")
    head, found = re.subn(r"```pgn\n.*?\n```", lambda m: "```pgn\n" + pgn.strip() + "\n```",
                          head, count=1, flags=re.S)
    if not found:
        fail(f"{os.path.basename(path)}: no PGN block")
    old_task, new_task = task_text(solver, data.get("theme")), task_text(solver, theme)
    head = head.replace(f"**{old_task}**", f"**{new_task}**", 1)

    data["solution"], data["theme"] = solution_text, theme
    data["solver_moves"] = str((len(sans) + 1) // 2)
    write_note(path, data, head + mine)
    print(f"updated: {os.path.basename(path)}: {solution_text}")


def cmd_remove(folder, args):
    if not args or args[0].startswith("--"):
        fail("remove <note> [--force]")
    path = note_file(folder, args[0])
    name = os.path.basename(path)
    data, body = read_note(path)
    if "--force" not in args[1:]:
        why = []
        if int(data.get("attempts") or 0) > 0:
            why.append(f"it was tried {data['attempts']} time(s)")
        if own_notes(body):
            why.append("it has your own notes")
        if why:
            fail(f"{name} not removed: {' and '.join(why)}; use --force to remove it anyway")
    board = board_of(body)
    os.remove(path)
    board_path = os.path.join(os.path.dirname(path), "boards", board) if board else None
    if board_path and os.path.exists(board_path):
        os.remove(board_path)
        print(f"removed: {name} (board {board})")
    else:
        print(f"removed: {name} (no board {board or 'linked'})")


def cmd_stats(folder, args):
    since = opt(args, "--since", today())
    all_notes = notes(folder)
    by_status = {s: 0 for s in STATUSES}
    for _, d in all_notes:
        by_status[d.get("status", "new")] = by_status.get(d.get("status", "new"), 0) + 1
    tried = {}
    for _, d in all_notes:
        hist = d.get("history") or []
        for h in (hist if isinstance(hist, list) else [hist]):
            day, _, result = h.partition(": ")
            if day >= since:
                tried[result] = tried.get(result, 0) + 1
    print(json.dumps({"puzzles": len(all_notes), "by_status": by_status,
                      "since": since, "tried": tried}, ensure_ascii=False))


# ---------------------------------------------------------------- export
def cmd_export(folder, args):
    if not args or args[0].startswith("--"):
        fail("export <out.pgn> [--status S] [--source S] [--motif M]")
    out_path, games = args[0], []
    for path, data in notes(folder):
        if not matches(data, args[1:]):
            continue
        body = split_note(open(path, encoding="utf-8").read())[1]
        m = re.search(r"```pgn\s*\n(.*?)```", body, re.S)
        if not m:
            continue
        name = os.path.basename(path)[:-3]
        theme = data.get("theme", "")
        # Lichess names a study chapter after the Event tag.
        games.append(re.sub(r'\[Event "[^"]*"\]', f'[Event "{name} ({theme})"]', m.group(1).strip(), count=1))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(games) + ("\n" if games else ""))
    print(f"exported {len(games)} puzzles to {out_path}")


# ---------------------------------------------------------------- check an answer
def cmd_check(args):
    """Check the solver's answer at step N (1-based) of a puzzle. Any mate is correct."""
    fen, solution, step = opt(args, "--fen"), opt(args, "--solution"), opt(args, "--step")
    rest = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] not in ("--fen", "--solution", "--step"))]
    if not (fen and solution and step and step.isdigit() and len(rest) == 1):
        fail('check --fen FEN --solution "SAN ..." --step N "<answer>"')
    sans, n = solution.split(), int(step)
    total = (len(sans) + 1) // 2
    if not 1 <= n <= total:
        fail(f"step {n}: this puzzle has {total} solver move(s)")
    board = board_for(fen)
    for s in sans[: 2 * (n - 1)]:
        board.push_san(s)
    current = board.fen()
    expected = board.parse_san(sans[2 * (n - 1)])
    answer = rest[0].strip()
    move = None
    try:
        move = board.parse_san(answer)
    except ValueError:
        try:
            m = chess.Move.from_uci(answer.lower())
            move = m if m in board.legal_moves else None
        except ValueError:
            move = None
    if move is None:
        print(json.dumps({"legal": False, "answer": answer, "fen": current, "step": n, "steps": total}))
        return
    san = board.san(move)
    expected_san = board.san(expected)
    board.push(move)
    mate = board.is_checkmate()
    correct = move == expected or mate
    out = {"legal": True, "correct": correct, "san": san, "expected": expected_san, "mate": mate,
           "step": n, "steps": total, "fen": current, "solved": correct and (mate or n == total)}
    if correct and not out["solved"]:
        reply = sans[2 * n - 1]
        out["reply"] = board.san(board.parse_san(reply))
        board.push_san(reply)
        out["next_fen"] = board.fen()
    print(json.dumps(out, ensure_ascii=False))


def main(argv):
    folder = None
    if argv[:1] == ["--dir"] and len(argv) >= 2:
        folder, argv = argv[1], argv[2:]
    cmd, *rest = argv or ["help"]
    if cmd == "check":
        return cmd_check(rest)
    commands = {"add": cmd_add, "next": cmd_next, "record": cmd_record, "update": cmd_update,
                "remove": cmd_remove, "stats": cmd_stats, "export": cmd_export}
    if folder is None or cmd not in commands:
        sys.exit(__doc__)
    commands[cmd](folder, rest)


if __name__ == "__main__":
    main(sys.argv[1:])

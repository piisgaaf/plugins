#!/usr/bin/env python3
"""repfreq.py — split a PGN repertoire into major / minor / rare by practical frequency.

Used by F39 (r03-prepare-and-understand-openings/f39-prioritise-repertoire.md).

Frequencies come ONLY from the chess engine tool get_opening_continuations; this
script never goes online. Work files (tree.json, results.json, chapters.json) live
in the work directory: --work DIR (first argument), default the current directory.
Keep it in a temporary directory, never in the user's working folder.

  repfreq.py [--work DIR] tree <w|b> <file.pgn> [...]       build the merged tree
  repfreq.py [--work DIR] frontier                          positions still to look up
  repfreq.py [--work DIR] add "<moves>" "san:pct ..." [...] store looked-up replies
  repfreq.py [--work DIR] report <outdir> [--band TEXT]     write the 3 markdown files

Used by F29 (r03-prepare-and-understand-openings/f29-learn-my-repertoire.md), after the
frontier loop above:

  repfreq.py [--work DIR] lines                             lines to evaluate (lines.json)
  repfreq.py [--work DIR] evals <n> "san:cp:best:score ..." [gap]   store evaluate_game's result
  repfreq.py [--work DIR] games <record.md> [...]           match game records (games.json)
  repfreq.py [--work DIR] review <outdir> [--band TEXT]     write repertoire_<side>_review.md

report writes <outdir>/repertoire_<white|black>_{major,minor,rare}.md. Text below
the line "<!-- coach notes -->" in an existing file is kept on a rerun; the same holds for review.

Exit codes: 0 ok, 1 bad input (illegal SAN, missing tree), 3 python-chess not installed.
"""
import io
import json
import os
import re
import sys

try:
    import chess
    import chess.pgn
except ImportError:
    # Exit code 3 tells the skill to install the package and retry, as for fen_to_svg.py.
    print("python-chess is not installed: run `pip install chess`", file=sys.stderr)
    sys.exit(3)

MAJOR, MINOR = 5.0, 1.0          # percent of the side's games
SPLIT_MIN_PLIES = 40             # side variations worth a split: at least this many plies
SPLIT_MIN_SHARE = 0.5            # ... and at least this share of the chapter
NOTES_MARKER = "<!-- coach notes -->"
DEFAULT_BAND = "1800–2000, rapid and classical"
DUBIOUS_CP, CHECK_CP = 100, 50  # F29: own moves losing this much (centipawns)
END_WORSE = -0.5                # F29: line ends with the player this much worse (pawns)
END_GAP = 1.0                   # F29: line ends where the best move is this far ahead of the next
MISTAKE_WINDOW = 16             # F29: plies after leaving the repertoire that count as "soon after"
TOP_ITEMS = 15                  # F29: rows in "Prepare next"


def load(name, default=None):
    try:
        return json.load(open(name))
    except FileNotFoundError:
        if default is None:
            sys.exit(f"{name} not found in {os.getcwd()}: run `tree` first")
        return default


def coach_notes(path):
    """Text below the coach-notes marker in an existing report, or ''."""
    try:
        text = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        return ""
    _, marker, notes = text.partition(NOTES_MARKER)
    return notes if marker else ""


def cls(x):
    return "major" if x >= MAJOR else "minor" if x >= MINOR else "rare"


def read_games(path):
    # [Variant] means "type of chess" in PGN; repertoire files misuse it for the opening line
    text = "".join(l for l in open(path, encoding="utf-8") if not l.startswith("[Variant "))
    fh, i = io.StringIO(text), 0
    while (g := chess.pgn.read_game(fh)) is not None:
        i += 1
        if g.errors:
            print(f"parse errors in {g.headers.get('Event')}: {g.errors}", file=sys.stderr)
        yield f"{os.path.basename(path)}#{i}: {g.headers.get('Event', '?')}", g


# ---------------------------------------------------------------- tree
def cmd_tree(side, paths):
    tree = {}

    def walk(node, board, source, ply):
        key = board.epd()
        e = tree.setdefault(key, {"ply": ply, "turn": "w" if board.turn else "b", "moves": {}, "sources": []})
        e["ply"] = min(e["ply"], ply)
        if source not in e["sources"]:
            e["sources"].append(source)
        for child in node.variations:
            san = board.san(child.move)
            board.push(child.move)
            e["moves"][san] = board.epd()
            walk(child, board, source, ply + 1)
            board.pop()

    files = []
    for p in paths:
        for source, g in read_games(p):
            walk(g, g.board(), source, 0)
        files.append(p)
    json.dump({"side": side, "files": files, "tree": tree}, open("tree.json", "w"))
    opp = [k for k, v in tree.items() if v["turn"] != side and v["moves"]]
    own_multi = [k for k, v in tree.items() if v["turn"] == side and len(v["moves"]) > 1]
    print(f"positions {len(tree)}, opponent-to-move with an answer {len(opp)}, own alternatives {len(own_multi)}")


# ---------------------------------------------------------------- reach
def compute_reach():
    t = load("tree.json")
    side, tree = t["side"], t["tree"]
    results = load("results.json", {})
    root = chess.Board().epd()
    reach, path, queue = {root: 100.0}, {root: []}, [root]
    while queue:
        key = queue.pop(0)
        node = tree.get(key)
        if not node:
            continue
        freq = dict(map(tuple, results.get(key, [])))
        for san, child in node["moves"].items():
            if node["turn"] == side:
                x = reach[key]
            elif key in results:
                x = reach[key] * freq.get(san, 0.0) / 100
            else:
                continue                      # not looked up yet
            if x > reach.get(child, -1):      # highest reach over all paths
                reach[child], path[child] = x, path[key] + [san]
                queue.append(child)
    return side, tree, results, reach, path


def cmd_frontier():
    side, tree, results, reach, path = compute_reach()
    todo = [k for k, v in tree.items() if v["turn"] != side and v["moves"]
            and k not in results and reach.get(k, 0) >= MINOR]
    todo.sort(key=lambda k: -reach[k])
    print(f"looked up {len(results)}, to look up {len(todo)}")
    for k in todo:
        print(f'{reach[k]:6.2f}%  "{" ".join(path[k])}"')


def cmd_add(args):
    results = load("results.json", {})
    if not args or len(args) % 2:
        sys.exit('add takes pairs: "<moves>" "san:pct ..."')
    for moves, conts in zip(args[0::2], args[1::2]):
        b = chess.Board()
        try:
            for s in moves.split():
                b.push_san(s)
            data = []
            for item in conts.split():
                san, pct = item.rsplit(":", 1)
                data.append([b.san(b.parse_san(san)), float(pct)])   # canonical SAN
        except ValueError as e:
            sys.exit(f'bad move in "{moves}" / "{conts}": {e}')
        results[b.epd()] = data
    json.dump(results, open("results.json", "w"), indent=1)
    print(f"stored {len(args) // 2}, total {len(results)}")


# ---------------------------------------------------------------- report
def movetext(sans):
    b, out = chess.Board(), []
    for s in sans:
        if b.turn:
            out.append(f"{b.fullmove_number}.{s}")
        else:
            out.append(s if out else f"{b.fullmove_number}...{s}")
        b.push_san(s)
    return " ".join(out)


def size(node):
    return 1 + sum(size(c) for c in node.variations)


def find_holes(tree, results, reach, path):
    """Frequent replies (reach >= MINOR) without an answer that do not transpose straight back."""
    holes = []
    for key, opts in results.items():
        for san, pct in opts:
            x = reach.get(key, 0) * pct / 100
            if x < MINOR or san in tree[key]["moves"]:
                continue
            b = chess.Board()
            for m in path[key]:
                b.push_san(m)
            b.push_san(san)
            if b.epd() in tree and tree[b.epd()]["moves"]:
                continue
            holes.append((x, path[key] + [san]))
    holes.sort(reverse=True)
    return holes


def find_chapters(files, side, tree, reach, path):
    """Each chapter's class (by its own line) and its side variations off the main line."""
    opp_turn = chess.BLACK if side == "w" else chess.WHITE
    chapters = []
    for f in files:
        for source, g in read_games(f):
            keys = [k for k, v in tree.items() if source in v["sources"]]
            own = [k for k, v in tree.items() if v["sources"] == [source]]
            entry = min(own or keys, key=lambda k: tree[k]["ply"])
            x = reach.get(entry)
            sides, main = [], g
            while main.variations:
                board = main.board()
                if board.turn == opp_turn:
                    nb = board.copy(); nb.push(main.variations[0].move)
                    main_x = reach.get(nb.epd(), 0.0)
                    for var in main.variations[1:]:
                        vb = board.copy(); vb.push(var.move)
                        sides.append({"move": f"{board.fullmove_number}{'.' if board.turn else '…'}{board.san(var.move)}",
                                      "reach": reach.get(vb.epd(), 0.0), "main": main_x, "plies": size(var)})
                main = main.variations[0]
            plies = size(g) - 1
            side_plies = sum(s["plies"] for s in sides)
            lower = [s for s in sides if cls(s["reach"]) != cls(x if x is not None else 0)]
            lower_plies = sum(s["plies"] for s in lower)
            split = lower_plies >= SPLIT_MIN_PLIES and lower_plies >= SPLIT_MIN_SHARE * plies
            better = [s for s in sides if s["reach"] > s["main"] and s["reach"] >= MINOR]
            chapters.append({"event": g.headers.get("Event", "?"), "file": os.path.basename(f), "source": source,
                             "entry": path.get(entry), "reach": x, "class": cls(x) if x is not None else "rare",
                             "plies": plies, "main": len(list(g.mainline_moves())), "side_plies": side_plies,
                             "sides": sides, "split": split, "better": better})
    return chapters


def cmd_report(outdir, band):
    side, tree, results, reach, path = compute_reach()
    files = load("tree.json")["files"]
    label = "White" if side == "w" else "Black"
    holes = find_holes(tree, results, reach, path)
    chapters = find_chapters(files, side, tree, reach, path)

    def note(c):
        n = []
        if c["split"]:
            n.append("**Split proposed** (see below)")
        for s in c["better"]:
            n.append(f"Side variation {s['move']} ({s['reach']:.1f}%) is more common than the main line ({s['main']:.1f}%)")
        return "; ".join(n)

    def chapter_table(cl):
        rows = sorted([c for c in chapters if c["class"] == cl], key=lambda c: -(c["reach"] or -1))
        s = "| Event name | File | Own line starts at | Reached in | Plies | Note |\n|---|---|---|---|---|---|\n"
        for c in rows:
            line = movetext(c["entry"]) if c["entry"] is not None else "beyond the looked-up lines"
            xs = f"{c['reach']:.1f}%" if c["reach"] is not None else "< 1%"
            s += f"| `{c['event']}` | {c['file']} | {line} | {xs} | {c['plies']} | {note(c)} |\n"
        return s if rows else "None.\n"

    def hole_table(lo, hi):
        rows = [h for h in holes if lo <= h[0] < hi]
        if not rows:
            return "None.\n"
        return "| Reply without an answer | Reached in |\n|---|---|\n" + "".join(
            f"| {movetext(p)} | {x:.1f}% |\n" for x, p in rows)

    def split_table(cl):
        rows = [c for c in chapters if c["class"] == cl and c["split"]]
        if not rows:
            return "No chapter needs splitting.\n"
        s = "| Chapter (see table above) | Plies | Main line | Side variations by class | Largest side variations |\n|---|---|---|---|---|\n"
        for c in rows:
            by = {"major": 0, "minor": 0, "rare": 0}
            for v in c["sides"]:
                by[cls(v["reach"])] += v["plies"]
            top = sorted(c["sides"], key=lambda v: -v["plies"])[:4]
            s += (f"| {movetext(c['entry']) if c['entry'] else '?'} | {c['plies']} | {c['main']} | "
                  + ", ".join(f"{k} {v}" for k, v in by.items() if v)
                  + " | " + "; ".join(f"{v['move']} {v['plies']} plies, " + (f"{v['reach']:.1f}%" if v['reach'] >= 0.05 else "< 1%") for v in top) + " |\n")
        return s

    header = f"""---
tags: [repertoire, frequency]
side: {label}
sources: [{", ".join(os.path.basename(f) for f in files)}]
---

# {label} repertoire — {{title}}

How often each line comes up in your {label} games: the share of games in which you reach the
position (*reached in*), from Lichess games ({{band}}), looked up through the chess engine.
Thresholds: **major** ≥ {MAJOR:g}%, **minor** {MINOR:g}–{MAJOR:g}%, **rare** < {MINOR:g}%.

Each chapter (`[Event]`) is listed in exactly one of the three files. Its class is set by how often
you reach the start of its **own line**: the first position that only this chapter covers.
*Plies* counts half-moves, variations included.

"""
    os.makedirs(outdir, exist_ok=True)
    base = f"{outdir}/repertoire_{label.lower()}"
    for cl, lo, hi in (("major", MAJOR, 101), ("minor", MINOR, MAJOR), ("rare", 0, MINOR)):
        md = header.format(title=cl, band=band)
        md += f"## {cl.capitalize()} chapters\n\n" + chapter_table(cl)
        if cl != "rare":
            md += f"\n## {cl.capitalize()} holes (reply reached in {'≥ 5%' if cl == 'major' else '1–5%'}, no answer in the files)\n\n" + hole_table(lo, hi)
            md += f"\n## Split proposals\n\n" + split_table(cl)
        notes = coach_notes(f"{base}_{cl}.md")
        md += f"\n{NOTES_MARKER}" + (notes or "\n")
        open(f"{base}_{cl}.md", "w", encoding="utf-8").write(md)

    # every Event exactly once over the three files
    texts = [open(f"{base}_{cl}.md").read() for cl in ("major", "minor", "rare")]
    bad = [c["event"] for c in chapters if sum(t.count(f"`{c['event']}`") for t in texts) != 1]
    dupe_names = len({c["event"] for c in chapters}) != len(chapters)
    print(f"chapters {len(chapters)}: " + ", ".join(f"{k} {sum(c['class'] == k for c in chapters)}" for k in ("major", "minor", "rare")))
    print("events not exactly once:", bad or "none", "| duplicate event names:", dupe_names)
    json.dump(chapters, open("chapters.json", "w"), indent=1, default=str)


# ---------------------------------------------------------------- F29: soundness
def cmd_lines():
    """The fewest lines that cover every own move in a position reached in >= MINOR."""
    side, tree, results, reach, path = compute_reach()
    todo = [k for k, v in tree.items() if v["turn"] != side and v["moves"]
            and k not in results and reach.get(k, 0) >= MINOR]
    if todo:
        sys.exit(f"{len(todo)} positions still to look up: finish the frontier loop first")
    edges = [(k, san) for k, v in tree.items() if v["turn"] == side and reach.get(k, 0) >= MINOR
             for san in v["moves"]]
    edges.sort(key=lambda e: -len(path[e[0]]))          # deepest first: long lines cover their trunk
    covered, lines = set(), []
    for key, san in edges:
        if (key, san) in covered:
            continue
        line, node, seen = path[key] + [san], tree[key]["moves"][san], {key}
        while node in tree and tree[node]["moves"] and node not in seen:
            seen.add(node)
            v = tree[node]
            if v["turn"] == side:
                nxt = next((m for m in v["moves"] if (node, m) not in covered), next(iter(v["moves"])))
            else:
                best = max(v["moves"], key=lambda m: reach.get(v["moves"][m], 0))
                if reach.get(v["moves"][best], 0) < MINOR:
                    break
                nxt = best
            line.append(nxt)
            node = v["moves"][nxt]
        b = chess.Board()
        for m in line:
            if (b.turn == chess.WHITE) == (side == "w"):
                covered.add((b.epd(), m))
            b.push_san(m)
        lines.append(line)
    json.dump(lines, open("lines.json", "w"), indent=1)
    print(f"own moves to check {len(edges)}, lines {len(lines)}, plies {sum(map(len, lines))}")
    for i, line in enumerate(lines, 1):
        print(f'{i:3d}  "{movetext(line)}"')


def cmd_evals(args):
    """Store evaluate_game's result for one line: san:cp_loss:best_move:score per ply."""
    if len(args) not in (2, 3):
        sys.exit('evals takes <n> "<san:cp_loss:best:score ...>" [<gap>]')
    lines = load("lines.json")
    try:
        n = int(args[0])
        line = lines[n - 1]
        if n < 1:
            raise IndexError
    except (ValueError, IndexError):
        sys.exit(f"no line {args[0]}: lines run from 1 to {len(lines)}")
    tokens = args[1].split()
    if len(tokens) != len(line):
        sys.exit(f"line {n} has {len(line)} plies, got {len(tokens)}: pass every ply, from move 1")
    b, plies = chess.Board(), []
    for want, tok in zip(line, tokens):
        try:
            san, cp, best, score = tok.rsplit(":", 3)
            if b.san(b.parse_san(san)) != want:
                raise ValueError(f"expected {want}, got {san}")
            best = b.san(b.parse_san(best)) if best not in ("", "-") else None
            plies.append({"san": want, "cp_loss": int(cp) if cp not in ("", "-") else None, "best": best,
                          "score": float(score) if score not in ("", "-") else None})
        except ValueError as e:
            sys.exit(f"line {n}, ply {len(plies) + 1} ({tok}): {e}")
        b.push_san(want)
    evals = load("evals.json", {})
    evals[str(n)] = {"plies": plies, "gap": float(args[2]) if len(args) == 3 else None}
    json.dump(evals, open("evals.json", "w"), indent=1)
    print(f"stored line {n}, evaluated {len(evals)} of {len(lines)}")


# ---------------------------------------------------------------- F29: game records
MISTAKE_RE = re.compile(r"^###\s*(\d+)\s*(\.\.\.|…|\.)\s*(\S+)")


def parse_record(path):
    text = open(path, encoding="utf-8").read()
    front = text.split("---", 2)[1] if text.startswith("---") else ""
    field = lambda k: (re.search(rf"^{k}:\s*\"?([^\"\n]*)\"?\s*$", front, re.M) or [None, ""])[1].strip()
    pgn = re.search(r"```pgn\s*\n(.*?)```", text, re.S)
    mistakes, in_section = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            in_section = line.strip() == "## Mistakes"
        elif in_section and (m := MISTAKE_RE.match(line)):
            mistakes.append({"ply": (int(m[1]) - 1) * 2 + (2 if m[2] != "." else 1),
                             "move": f"{m[1]}{m[2]}{m[3]}"})
    return {"name": os.path.splitext(os.path.basename(path))[0], "date": field("date"),
            "color": field("player_color"), "result": field("result"),
            "pgn": pgn[1] if pgn else None, "mistakes": mistakes}


def cmd_games(paths):
    """Match game records (F37) against the tree: where each game left the repertoire."""
    t = load("tree.json")
    side, tree = t["side"], t["tree"]
    color = "white" if side == "w" else "black"
    games, skipped = [], {"other side": 0, "side unknown": 0, "no PGN": 0, "other start": 0}
    for p in paths:
        r = parse_record(p)
        if r["color"] not in ("white", "black"):
            skipped["side unknown"] += 1; continue
        if r["color"] != color:
            skipped["other side"] += 1; continue
        g = chess.pgn.read_game(io.StringIO(r["pgn"] or ""))
        if g is None or not r["pgn"]:
            skipped["no PGN"] += 1; continue
        b = g.board()
        if b.epd() not in tree:
            skipped["other start"] += 1; continue
        sans, edges, left = [], [], None
        for ply, move in enumerate(g.mainline_moves(), 1):
            key, san = b.epd(), b.san(move)
            node = tree[key]
            if node["turn"] == side:
                edges.append([key, san])
            b.push(move)
            if b.epd() in tree:                       # in the repertoire, transpositions included
                sans.append(san); continue
            kind = "end" if not node["moves"] else "you" if node["turn"] == side else "opponent"
            left = {"ply": ply, "path": sans, "san": san, "epd": key, "kind": kind,
                    "expected": list(node["moves"]), "sources": node["sources"]}
            edges = edges[:-1] if kind == "you" else edges
            break
        res = {"1-0": 1.0, "0-1": 0.0, "1/2-1/2": 0.5}.get(r["result"])
        score = None if res is None else res if side == "w" else 1 - res
        after = left["ply"] if left else 10 ** 6
        soon = [m for m in r["mistakes"] if after < m["ply"] <= after + MISTAKE_WINDOW]
        games.append({"name": r["name"], "date": r["date"], "result": r["result"], "score": score,
                      "left": left, "edges": edges, "soon": soon})
    json.dump(games, open("games.json", "w"), indent=1)
    print(f"games with this side {len(games)}; skipped " + ", ".join(f"{k} {v}" for k, v in skipped.items()))


# ---------------------------------------------------------------- F29: review
def cmd_review(outdir, band):
    side, tree, results, reach, path = compute_reach()
    files = load("tree.json")["files"]
    label = "White" if side == "w" else "Black"
    sign = 1 if side == "w" else -1
    holes = find_holes(tree, results, reach, path)
    chapters = find_chapters(files, side, tree, reach, path)
    event = {c["source"]: c["event"] for c in chapters}
    lines = load("lines.json", [])
    evals = load("evals.json", {})
    games = load("games.json", [])
    pct = lambda x: f"{x:.1f}%" if x >= 0.05 else "< 1%"

    # soundness: own moves (one entry per position + move) and line ends
    moves, ends = {}, []
    for i, line in enumerate(lines, 1):
        ev = evals.get(str(i))
        if not ev:
            continue
        b = chess.Board()
        for j, (san, e) in enumerate(zip(line, ev["plies"])):
            key = b.epd()
            if (b.turn == chess.WHITE) == (side == "w") and e["cp_loss"] is not None and reach.get(key, 0) >= MINOR:
                if e["cp_loss"] >= CHECK_CP and (key, san) not in moves:
                    note = ""
                    if e["best"]:
                        nb = b.copy(); nb.push_san(e["best"])
                        if nb.epd() in tree:
                            note = "transposes into " + " / ".join(sorted({event.get(s, s) for s in tree[nb.epd()]["sources"]}))
                    moves[(key, san)] = {"path": line[:j], "san": san, "reach": reach[key], "cp": e["cp_loss"],
                                         "best": e["best"], "note": note}
            b.push_san(san)
        last = ev["plies"][-1]["score"]
        why = []
        if last is not None and sign * last <= END_WORSE:
            why.append(f"you are worse at the end ({sign * last:+.1f})")
        if ev["gap"] is not None and ev["gap"] >= END_GAP:
            why.append(f"only one move holds ({ev['gap']:.1f} pawns ahead of the next)")
        if why:
            ends.append({"line": line, "reach": reach.get(b.epd(), 0.0), "score": last, "why": why})
    missing = [i for i in range(1, len(lines) + 1) if str(i) not in evals]

    # priorities: base (reach of the position, at least 1% when games show it) x weight x (1 + games)
    items = []
    for m in moves.values():
        b = chess.Board()
        for x in m["path"]:
            b.push_san(x)
        n = sum(1 for g in games if [b.epd(), m["san"]] in g["edges"])
        w = 2 if m["cp"] >= DUBIOUS_CP else 1
        items.append((m["reach"] * w * (1 + n), "Dubious move" if w == 2 else "Move to check",
                      m["path"] + [m["san"]], m["reach"], n, f"loses {m['cp']} cp; engine prefers {m['best']}"))
    seen_holes = set()
    for x, p in holes:
        b = chess.Board()
        for y in p[:-1]:
            b.push_san(y)
        n = sum(1 for g in games if g["left"] and g["left"]["kind"] == "opponent"
                and g["left"]["epd"] == b.epd() and g["left"]["san"] == p[-1])
        seen_holes.add((b.epd(), p[-1]))
        items.append((x * (1 + n), "Hole", p, x, n, "common reply without an answer"))
    met, forgot = {}, {}
    for g in games:
        l = g["left"]
        if l and l["kind"] == "opponent" and (l["epd"], l["san"]) not in seen_holes:
            met.setdefault((l["epd"], l["san"]), []).append(l)
        if l and l["kind"] == "you":
            forgot.setdefault(l["epd"], []).append(l)
    for (key, san), ls in met.items():
        r = max(reach.get(key, 0), MINOR)
        items.append((r * (1 + len(ls)), "Unprepared reply", ls[0]["path"] + [san], reach.get(key, 0), len(ls),
                      "met in your games, no answer in the files"))
    for key, ls in forgot.items():
        r = max(reach.get(key, 0), MINOR)
        played = ", ".join(sorted({l["san"] for l in ls}))
        items.append((r * (1 + len(ls)), "Forgotten move", ls[0]["path"], reach.get(key, 0), len(ls),
                      f"you played {played}; the repertoire has {', '.join(ls[0]['expected'])}"))
    for e in ends:
        items.append((e["reach"], "Line to extend", e["line"], e["reach"], 0, "; ".join(e["why"])))
    items.sort(key=lambda it: -it[0])

    def chapter_of(sources):
        names = sorted({event.get(s, s) for s in sources})
        return f"`{names[0]}`" if len(names) == 1 else "several chapters (shared trunk)"

    md = f"""---
tags: [repertoire, review]
side: {label}
sources: [{", ".join(os.path.basename(f) for f in files)}]
---

# {label} repertoire — review

What to work on first in your {label} repertoire. It combines how often a line comes up (Lichess
games, {band}), the engine's view of your own moves in the major and minor lines (reached in
≥ {MINOR:g}%), and where your own games (game records) left the repertoire.

"""
    md += "## Prepare next\n\n"
    if items:
        md += "| # | What | Line | Reached in | Your games | Why |\n|---|---|---|---|---|---|\n"
        for i, (_, kind, p, x, n, why) in enumerate(items[:TOP_ITEMS], 1):
            md += f"| {i} | {kind} | {movetext(p) or 'start'} | {pct(x)} | {n or ''} | {why} |\n"
    else:
        md += "Nothing found.\n"
    md += (f"\n## Moves to check (engine)\n\nYour moves in lines reached in ≥ {MINOR:g}% that lose ≥ {CHECK_CP} centipawns"
           f" (dubious: ≥ {DUBIOUS_CP}).\n\n")
    if missing:
        md += f"Not evaluated yet: line{'s' if len(missing) > 1 else ''} {', '.join(map(str, missing))}.\n\n"
    if moves:
        md += "| Line | Reached in | Your move | Loss (cp) | Engine prefers | Note |\n|---|---|---|---|---|---|\n"
        for m in sorted(moves.values(), key=lambda m: -m["reach"]):
            md += (f"| {movetext(m['path'] + [m['san']])} | {pct(m['reach'])} | {m['san']} | {m['cp']} "
                   f"| {m['best']} | {m['note']} |\n")
    else:
        md += "None.\n" if lines else "Not checked.\n"
    md += "\n## Lines to extend\n\nLines that end where you are worse or where only one move holds.\n\n"
    if ends:
        md += "| Line | Reached in | Why |\n|---|---|---|\n"
        for e in sorted(ends, key=lambda e: -e["reach"]):
            md += f"| {movetext(e['line'])} | {pct(e['reach'])} | {'; '.join(e['why'])} |\n"
    else:
        md += "None.\n" if lines else "Not checked.\n"
    md += f"\n## Your games\n\nGame records where you played {label}.\n\n"
    if games:
        by = {}
        for g in games:
            ch = chapter_of(g["left"]["sources"]) if g["left"] else "never left the repertoire"
            by.setdefault(ch, []).append(g)
        md += ("| Chapter | Games | Score | Left by you | Left by opponent | End of preparation | Mistakes soon after |\n"
               "|---|---|---|---|---|---|---|\n")
        for ch, gs in sorted(by.items(), key=lambda kv: -len(kv[1])):
            scored = [g["score"] for g in gs if g["score"] is not None]
            kinds = lambda k: sum(1 for g in gs if g["left"] and g["left"]["kind"] == k)
            md += (f"| {ch} | {len(gs)} | {sum(scored):g}/{len(scored)} | {kinds('you')} | {kinds('opponent')} "
                   f"| {kinds('end')} | {sum(len(g['soon']) for g in gs)} |\n")
        how = {"you": "you left it", "opponent": "opponent left it", "end": "end of preparation"}
        md += f"\n| Game | Result | Left the repertoire at | How | Mistakes within {MISTAKE_WINDOW // 2} moves |\n|---|---|---|---|---|\n"
        for g in sorted(games, key=lambda g: g["date"], reverse=True):
            l = g["left"]
            at = movetext(l["path"] + [l["san"]]) if l else "—"
            hw = how[l["kind"]] + (f" (repertoire: {', '.join(l['expected'])})" if l and l["kind"] == "you" else "") if l else "stayed in"
            md += f"| [[{g['name']}]] | {g['result']} | {at} | {hw} | {', '.join(m['move'] for m in g['soon'])} |\n"
    else:
        md += "No game records with this side.\n"
    os.makedirs(outdir, exist_ok=True)
    out = f"{outdir}/repertoire_{label.lower()}_review.md"
    notes = coach_notes(out)
    md += f"\n{NOTES_MARKER}" + (notes or "\n")
    open(out, "w", encoding="utf-8").write(md)
    print(f"items {len(items)}, moves to check {len(moves)}, lines to extend {len(ends)}, games {len(games)}"
          + (f", lines not evaluated {len(missing)}" if missing else ""))


def main(argv):
    work = None
    if argv[:1] == ["--work"] and len(argv) >= 2:
        work, argv = argv[1], argv[2:]
    cmd, *rest = argv or ["help"]
    if cmd == "tree" and len(rest) >= 2 and rest[0] in ("w", "b"):
        paths = [os.path.abspath(p) for p in rest[1:]]       # before changing directory
        run = lambda: cmd_tree(rest[0], paths)
    elif cmd == "frontier" and not rest:
        run = cmd_frontier
    elif cmd == "add":
        run = lambda: cmd_add(rest)
    elif cmd == "report" and len(rest) in (1, 3) and rest[1:2] in ([], ["--band"]):
        outdir = os.path.abspath(rest[0])
        band = rest[2] if len(rest) == 3 else DEFAULT_BAND
        run = lambda: cmd_report(outdir, band)
    elif cmd == "lines" and not rest:
        run = cmd_lines
    elif cmd == "evals":
        run = lambda: cmd_evals(rest)
    elif cmd == "games" and rest:
        paths = [os.path.abspath(p) for p in rest]
        run = lambda: cmd_games(paths)
    elif cmd == "review" and len(rest) in (1, 3) and rest[1:2] in ([], ["--band"]):
        outdir = os.path.abspath(rest[0])
        band = rest[2] if len(rest) == 3 else DEFAULT_BAND
        run = lambda: cmd_review(outdir, band)
    else:
        sys.exit(__doc__)
    if work:
        os.makedirs(work, exist_ok=True)
        os.chdir(work)
    run()


if __name__ == "__main__":
    main(sys.argv[1:])

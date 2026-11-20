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

report writes <outdir>/repertoire_<white|black>_{major,minor,rare}.md. Text below
the line "<!-- coach notes -->" in an existing file is kept on a rerun.

Exit codes: 0 ok, 1 bad input (illegal SAN, missing tree), 3 python-chess not installed.
"""
import io
import json
import os
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


def cmd_report(outdir, band):
    side, tree, results, reach, path = compute_reach()
    files = load("tree.json")["files"]
    label = "White" if side == "w" else "Black"
    opp_turn = chess.BLACK if side == "w" else chess.WHITE

    # holes: frequent replies without an answer that do not transpose straight back
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

    # chapters: class by own line; side variations off the main line
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
            chapters.append({"event": g.headers.get("Event", "?"), "file": os.path.basename(f),
                             "entry": path.get(entry), "reach": x, "class": cls(x) if x is not None else "rare",
                             "plies": plies, "main": len(list(g.mainline_moves())), "side_plies": side_plies,
                             "sides": sides, "split": split, "better": better})

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
    else:
        sys.exit(__doc__)
    if work:
        os.makedirs(work, exist_ok=True)
        os.chdir(work)
    run()


if __name__ == "__main__":
    main(sys.argv[1:])

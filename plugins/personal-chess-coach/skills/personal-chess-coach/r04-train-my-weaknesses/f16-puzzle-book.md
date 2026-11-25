# 1.  F16 — Build My Personal Puzzle Book

## 1.1.  User question

> "Add these to my puzzle book."
> "Give me a puzzle." / "Start a puzzle session."
> "Give me a fresh puzzle." (one I have not played)
> "Give me a mate puzzle." / "Retry my failed puzzles." / "One from last month."
> "How am I doing with my puzzles?"
> "Export my puzzles as PGN." / "Export my failed puzzles for Lichess."
> (or: "yes" to F14's "Add them to your puzzle book?")

## 1.2.  Capability unlocked

The puzzles from the player's games are kept as a growing collection of notes in `Puzzles/`, one per position, with an overview table. The user can solve them with the coach ("Give me a puzzle"), which saves each result, or on their own in Obsidian (the solution is in a collapsed callout), or on a board after exporting them as PGN, e.g. as a Lichess study.

## 1.3.  Validation

A correct implementation demonstrates:

- Every note is written by `puzzlebook.py add` from [templates/puzzle.md](../templates/puzzle.md), with its board in `Puzzles/boards/`, and only after the user's yes
- The same position from two games is one note listing both games
- "Give me a puzzle" takes the note `puzzlebook.py next` picks: new first, then failed, then solved with a hint, then solved; not one tried earlier in the same session
- Each result is saved with `puzzlebook.py record`; a status the user set by hand in Obsidian is respected
- Text the user wrote in a note is never changed
- The PGN export contains only the puzzles asked for, starting from each puzzle position

---

## 1.4.  Where the puzzle book lives

All paths are relative to the **working folder** ([SKILL.md §1.7.1](../SKILL.md#171--working-folder-decide-once-per-conversation)).

```
Puzzles/
  Puzzles.base            ← overview table: To do, By source, By motif, Failed (created once)
  boards/
    925e3d95.svg          ← puzzle board, from White's side
    70a81aaf-black.svg    ← puzzle board, from Black's side
  Puzzle 925e3d95.md      ← one note per puzzle position
  puzzles.pgn             ← only after an export
```

A note is named after the position (`Puzzle <hash>.md`, the same hash as its board). Its front matter holds the FEN, the solver, the source and the games it comes from (links to game records, or a label such as *de Vries – Pieter, 2026-11-08 (2026.pgn #2)* for a game from the games folder), the motif, the theme, the solution and the results (`status`: `new`, `solved`, `solved_with_hint` or `failed`; `attempts`, `last_tried`, `history`). The body has the board, the task and where it comes from, the solution in a collapsed callout, the puzzle as PGN, and "My notes" for the user.

## 1.5.  Tools used

| Tool | When |
|---|---|
| [scripts/puzzlebook.py](../scripts/puzzlebook.py) | Every read and write of a puzzle note: `add`, `next`, `record`, `stats`, `export`. Run it with `python3 -I` and its absolute path (`<skill-folder>` is the folder that contains `SKILL.md`). Exit code 3 means python-chess is missing: run `pip install chess` and retry |
| Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)) | Saving each new puzzle's board in `Puzzles/boards/` (show-board.md §1.5), from the solver's side; and showing a puzzle when solving (F15) |
| F15's tools | Solving: `puzzlebook.py check` and `evaluate_move` |

Never edit a puzzle note's front matter yourself: `puzzlebook.py` keeps it in the form the overview table reads.

---

## 1.6.  Workflow

### 1.6.1.  Adding puzzles

After the user's yes (F14), for each puzzle from `find_puzzles`:

0. **Folder (first time):** create `Puzzles/` with a command (`mkdir -p "<working folder>/Puzzles"`) and, if `Puzzles/Puzzles.base` does not exist, copy [templates/Puzzles.base](../templates/Puzzles.base) there unchanged.
1. **Note:** pass the puzzle's own PGN (`pgn` from `find_puzzles`) on stdin:
   ```bash
   printf '%s\n' "<pgn>" | python3 -I <skill-folder>/scripts/puzzlebook.py --dir "<working folder>/Puzzles" add \
     --fen "<fen>" --solver <solver> --source <source> --theme <theme_hint> \
     --solution "<the solution's SAN moves, space-separated>" \
     --record "<game record name, without .md>" | --game "<label from games.py>" --date <game date> \
     --move "<move_number and played_move, e.g. 24.Rxf7 or 17...Qd7>" \
     [--line "<line, SAN, space-separated>"] [--motif <motif from F14>]
   ```
   `--line` only for `variation` puzzles. `--record` when the game has a game record; otherwise `--game` with the game's `label` from `games.py` (F14's batch), or neither for a game pasted in the chat. `--date` is the game's date. The script checks that the solution is legal from the FEN and that the PGN starts from the same position, and stops otherwise: never "fix" a value by hand, take it again from the tool result.
2. **Board:** the script prints `added: Puzzle <hash>.md (board <name>)`. Save the board with `fen_to_svg.py -d "<working folder>/Puzzles/boards"` (`--flip` when the solver is Black, show-board.md §1.5). The name it prints must be the board name `add` printed; if it differs, say so and stop.
3. When the script prints `exists` (the same position from another game), there is nothing to do: it added the game as a source.

Then one line: *"Added 3 puzzles to `Puzzles/` (1 was already there, from another game)."*

### 1.6.2.  A puzzle session

On "Give me a puzzle", "Start a puzzle session" or a request with a filter:

```bash
python3 -I <skill-folder>/scripts/puzzlebook.py --dir "<working folder>/Puzzles" next [filters] [--exclude "<notes shown in this session>"]
```

| Request | Filter |
|---|---|
| "a fresh puzzle" (one I have not played) | `--fresh` (only `opponent_missed` and `variation`) |
| "a mate puzzle" / "a defence puzzle" | `--theme mate` / `--theme defence` |
| "a knight fork puzzle" | `--motif knight_fork` (the labels of [mistake-taxonomy.md §1.3](../codebook/mistake-taxonomy.md#13--motif-vocabulary)) |
| "retry my failed puzzles" | `--status failed` |
| "one from last month" | `--since <date>` |
| "only my own mistakes" | `--source own_mistake` |

The script prints the note's data as JSON (`note`, `fen`, `solver`, `source`, `sources`, `move`, `line`, `theme`, `solution`, `left`), or `"note": null` when no puzzle matches: then say so and suggest a wider choice or F14. Solve it with [F15](f15-reliable-puzzles.md) Steps 2–4: the FEN, solver, theme and solution come from this JSON. For the "where it comes from" line, use `move`, `line` and the first of `sources`.

After each puzzle, ask *"Next one?"* and pass every note shown in this session to `--exclude`.

### 1.6.3.  Recording a result

After F15 Step 4, for a puzzle from the book:

```bash
python3 -I <skill-folder>/scripts/puzzlebook.py --dir "<working folder>/Puzzles" record "<note>" solved|solved_with_hint|failed
```

`failed` when any answer was wrong or the user asked for the solution; `solved_with_hint` after a hint; `solved` otherwise.

If the idea is still the placeholder in the note's solution callout ("The idea is added after you solve it."), replace that one line with F15's two-sentence idea. That line is the only body text you may change.

### 1.6.4.  End of a session

When the user stops, or `next` prints `"left": 1` for the last one:

```bash
python3 -I <skill-folder>/scripts/puzzlebook.py --dir "<working folder>/Puzzles" stats
```

One line from it: *"5 tried today: 3 solved, 1 with a hint, 1 failed. The failed one comes back next time."*

"How am I doing with my puzzles?" is the same `stats`, with `--since` for a longer period: the totals by status and what was tried since then.

### 1.6.5.  Export as PGN

```bash
python3 -I <skill-folder>/scripts/puzzlebook.py --dir "<working folder>/Puzzles" export "<working folder>/Puzzles/puzzles.pgn" [--status failed] [--source …] [--motif …]
```

Each puzzle is a game that starts from the puzzle position (`[SetUp "1"]`/`[FEN]`), with the task as a comment and the solution as the main line, named `Puzzle <hash> (<theme>)`. Tell the user they can import the file into a Lichess study (one chapter per puzzle; choose "Interactive lesson" so that they play the moves themselves), or open it in Scid or ChessBase. A Lichess study holds at most 64 chapters: for more, export with a filter.

---

## 1.7.  Without a working folder

F16 does not run: the puzzle book lives in the folder. Say so in one line ([SKILL.md §1.7.3](../SKILL.md#173--without-a-working-folder)). Puzzles found in this conversation (F14) can still be solved (F15).

---

## 1.8.  Quality checklist

- [ ] Notes were only written by `puzzlebook.py add`, after the user's yes, with their board in `Puzzles/boards/`
- [ ] `Puzzles.base` was copied once, unchanged
- [ ] A session used `next` with `--exclude` for the notes already shown, and every result went through `record`
- [ ] No front matter was edited by hand; in the body only the idea placeholder was replaced
- [ ] The export contained the puzzles asked for, and the user was told how to use it

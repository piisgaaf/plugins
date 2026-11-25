# 1.  F14 — Find My Missed Tactical Opportunities

## 1.1.  User question

> "Find the puzzles in this game."
> "Turn my mistakes into puzzles."
> "Which tactics did I miss in this game?"
> "Find puzzles in my games." / "Find puzzles in my game records."
> "Which of my games have I analysed?" / "Which games have not been searched for puzzles yet?"
> (or: "yes" to the coach's offer "Find the puzzles in this game?" after F07 or F08)

## 1.2.  Capability unlocked

The tactics the player missed in their own games become puzzles: positions with exactly one good move at every step, checked by the engine. There are three kinds, so not every puzzle is a position the player has already seen:

| Source | Position | Solved as |
|---|---|---|
| `own_mistake` | Before one of the player's own moves that lost a pawn or more, or missed a mate | The player |
| `opponent_missed` | Before an opponent's move that missed a win | The opponent (the board is shown from their side) |
| `variation` | 2, 4 or 6 plies into the engine's best line from any critical move | Whoever had the critical move: a position that never came up on the board |

## 1.3.  Validation

A correct implementation demonstrates:

- Puzzles come only from `find_puzzles`; the skill never decides by itself that a position is a puzzle
- `player_color` is the side the player really had; when it is not known, the skill asks once
- The result names how many positions were checked and how many puzzles passed, by source, without giving away a solution
- Puzzles can be solved straight away (F15), also without a working folder
- With a working folder, puzzles are added to the puzzle book (F16) only after the user's yes
- The game list shows every game once (from the games folder and the game records, whatever the notation), with the player's side, whether it was analysed (a game record) and whether it was searched for puzzles
- A batch runs only on the games the user chose, skips games with an unknown side unless the user gives it, and logs each finished game as searched; PGN files and game records are never changed

---

## 1.4.  Tools used

| Tool | When |
|---|---|
| `find_puzzles` | Per game: `pgn` = the game's PGN, `player_color`, default sources and depth. It evaluates the game itself and takes about 1–3 minutes per game, over several calls (Step 2) |
| [scripts/games.py](../scripts/games.py) | Batch only: `list` (the player's games, analysed and searched), `pgn` (one game's PGN) and `searched` (log a game as searched). Run it with `python3 -I` and its absolute path (`<skill-folder>` is the folder that contains `SKILL.md`). Exit code 3 means python-chess is missing: run `pip install chess` and retry |

No board images in this step: the puzzles are shown when they are solved (F15).

---

## 1.5.  Workflow

### 1.5.1.  Step 1 — The game and the player's side

- **One game:** the game analysed in this conversation, or a PGN the user gives. For a multi-game PGN, follow [SKILL.md §1.4](../SKILL.md#14--multi-game-pgn-handling) first.
- **Side:** from the `player` section of the profile when it is known without asking ([SKILL.md §1.7.2](../SKILL.md#172--when-to-resolve-the-profile)), from the game record's `player_color`, or from what the user said. Otherwise ask once: *"Which side did you play?"*

### 1.5.2.  Step 2 — Find the puzzles

Say it will take a minute or two, then call `find_puzzles`. Each call stops after about a minute:

- **`complete` is false:** the search is not done yet. Call `find_puzzles` again with exactly the same arguments (same `pgn`, `player_color`, `sources` and `depth`): it carries on where it stopped. Repeat until `complete` is true. Between calls, say in one short line how far it is (*"Game evaluated, 6 of 25 positions checked…"*), from `plies_evaluated`/`ply_count` and `candidates_checked`/`candidates_total`; never show puzzles from an incomplete reply.
- **`complete` is true:** use this reply only. It holds everything found, also from the earlier calls.

In the complete result:

- `puzzles` holds only puzzles that passed. Each has `source`, `solver`, `ply`, `move_number`, `played_move`, `line` (for `variation`), `fen`, `solution`, `theme_hint` and `pgn`.
- `candidates_checked` and `rejected` say how many positions were looked at and why the others were not good puzzles.

### 1.5.3.  Step 3 — Report, without spoilers

> *"I checked 14 positions from this game: 3 make good puzzles. One from your own move 24, one your opponent missed on move 17, and one from a line that could have happened after move 31. Solve them now?"*

Never show a solution, the theme or the motif here. With no puzzles, say so in one line: most mistakes are not tactics with one clear answer, and that is normal.

Then, in this order:

1. **"Solve them now?"** → [F15](f15-reliable-puzzles.md), one puzzle at a time, in game order.
2. With a working folder: **"Add them to your puzzle book?"** → [F16](f16-puzzle-book.md) §1.6.1. Ask it together with question 1 when both apply, e.g. *"Solve them now, and add them to your puzzle book?"*; do only what the user says yes to.

**Motif:** when F08 classified the mistake at a puzzle's `ply` in this conversation, or the game record's "Mistakes" section has it, pass that motif label to F16 for `own_mistake` puzzles. Otherwise leave it empty: naming it is F17's job.

### 1.5.4.  Batch: your games

Only with a working folder, when the user asks for puzzles from their games, or which of their games were analysed or searched.

**List the games.** The player's names come from the `player` section of the profile (`name`, every `aliases` entry and every `usernames` value), when the profile file is known without asking ([SKILL.md §1.7.2](../SKILL.md#172--when-to-resolve-the-profile)); the games folder is `player.games_folder`, relative to the working folder.

```bash
python3 -I <skill-folder>/scripts/games.py --games "<working folder>/<games_folder>" \
  --records "<working folder>/Game_Analysis" --book "<working folder>/Puzzles" \
  --player "<name>" --player "<alias>" --player "<username>" list
```

Leave out `--games` when there is no games folder, and `--records` when there is no `Game_Analysis/`. The script lists every game once, from the PGN files (any depth, several games per file) and the game records, newest first: the same game written by two programs counts once. It starts with the counts (games, analysed, searched, side unknown), then a table: date, players, result, the player's side (`?` when no name matches, or both do), the game record ("analysed") and when it was searched for puzzles, with how many were found.

Show the counts and the table. With more than 20 games, show the counts and the latest 20, and say the user can narrow the list: `--unsearched` (not searched yet), `--analysed` / `--not-analysed` (with or without a game record), `--since YYYY-MM-DD`. Without player names, every side is `?`: ask which names they play under, or offer to add them to the profile (F08 Step 1).

**Choose.** The user picks games: by number from the table ("2, 5 and 7"), or by filter ("all not searched since October"). Games with side `?` are skipped unless the user says which side they had. Say how many games that is and how long it takes (about 2 minutes each), and wait for the user's yes.

**Run.** Get the ids with the same command and `--json` (one JSON object per game: `id`, `date`, `white`, `black`, `side`, `file`, `record`, `label`, `searched`, …). For each chosen game, newest first:

1. Its PGN: `python3 -I <skill-folder>/scripts/games.py <same options> pgn <id>`. Run Steps 2 and 3 above with it and the game's `side`. Do not ask "Solve them now?" per game.
2. Add the puzzles to the puzzle book (F16 §1.6.1): with `--record "<record>"` when the game has a record, otherwise `--game "<label>"`. The user's yes to the batch counts as yes to adding.
3. Log it: `python3 -I <skill-folder>/scripts/games.py <same options> searched <id> --found <number of puzzles>`, also when no puzzle was found. This writes `Puzzles/searched.json`; the PGN files and game records are never changed.

Tell the user briefly how far it is between games (*"4 of 9 games done, 7 puzzles so far"*). At the end, give one line per source and offer *"Start a puzzle session?"* → F16.

---

## 1.6.  Without a working folder

Steps 1–3 work as usual; only the puzzle book offer and the batch (the game list) are left out ([SKILL.md §1.7.3](../SKILL.md#173--without-a-working-folder)).

---

## 1.7.  Quality checklist

- [ ] `find_puzzles` was called with the side the player really had
- [ ] `find_puzzles` was called again with the same arguments until `complete` was true
- [ ] The report gave the counts by source and no solution, theme or motif
- [ ] Puzzles were only added to the book after the user's yes
- [ ] In a batch: the game list was shown first, only the chosen games were searched, skipped games were mentioned, and each finished game was logged with `games.py searched`

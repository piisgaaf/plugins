# 1.  F29 — Learn My Opening Repertoire

## 1.1.  User question

> "Is my White repertoire any good?"
> "Check my repertoire with the engine."
> "Where do my games leave my repertoire?"
> "What should I change in my repertoire?"
> "What should I work on next in my openings?"
> "Update my repertoire review."

## 1.2.  Capability unlocked

The user learns what to fix in their repertoire, and in what order. F29 builds on F39's frequencies and adds two things:

- **Soundness:** Stockfish checks the player's own moves in every line they meet in ≥ 1% of their games (the major and minor lines). Moves that lose ground and lines that stop where the player is worse or where only one move holds are flagged.
- **Results:** the player's own game records (F37) are matched against the repertoire. For each game the review shows where it left the repertoire and who left it: the player (a forgotten move), the opponent (an unprepared reply) or the end of the preparation. It also shows the score per chapter and the mistakes made soon after leaving the repertoire.

Together with F39's holes, these become one ranked **"Prepare next"** list in `Repertoire/repertoire_<side>_review.md`, with the coach's advice below it. Each piece of advice names the F36 opening card to create or update.

## 1.3.  Validation

A correct implementation demonstrates:

- Frequencies come from F39's lookup loop (`get_opening_continuations`), finished before the engine check starts
- The engine checks every own move in a position reached in ≥ 1% of games, and nothing below that, through `evaluate_game` on the lines `repfreq.py lines` prints (`from_ply: 1`), never through FENs typed by hand
- A flagged move shows its loss in centipawns and the engine's move; a move that transposes into another chapter says so
- Game results come only from game records in `Game_Analysis/` where the player's side is known and matches; never from the Player Profile or the games folder
- Each game shows where it left the repertoire and who left it; mistakes from the record within 8 moves after that are counted
- "Prepare next" is ranked by the rule in §1.6, step 4, and every coach note names an F36 card (existing or to create)
- A rerun replaces the tables but keeps everything below `<!-- coach notes -->`
- Work files stay in a temporary directory; only the review is written to the working folder, after the user's yes
- The PGN files and the game records are never changed

---

## 1.4.  Where the files live

All paths are relative to the **working folder** ([SKILL.md §1.7.1](../SKILL.md#171--working-folder-decide-once-per-conversation)).

```
Repertoire/
  repertoire_white_major.md      ← F39
  repertoire_white_minor.md      ← F39
  repertoire_white_rare.md       ← F39
  repertoire_white_review.md     ← F29
Game_Analysis/
  2026-11-15 Pieter - Jansen.md  ← F37 game records, read only
Openings/
  White/…                        ← F36 cards, named in the coach notes
```

The repertoire PGN files are found as in [F39 §1.4](f39-prioritise-repertoire.md#14--where-the-files-live). The game records are all `*.md` files in `Game_Analysis/` (not in `boards/`). There may be none: the review then has no "Your games" part, which is fine.

The script's work files (`tree.json`, `results.json`, `lines.json`, `evals.json`, `games.json`) go in a temporary directory, as in F39. If F39 ran earlier in this conversation for the same side and band, reuse its work directory: the lookups are then already done.

## 1.5.  Tools used

| Tool | When |
|---|---|
| [scripts/repfreq.py](../scripts/repfreq.py) | Always. F39's `tree`, `frontier` and `add` first, then `lines` (lines to evaluate), `evals` (store each result), `games` (match the records) and `review` (write the file). Run it with `python3 -I` and its absolute path, as in F39 |
| `get_opening_continuations` | F39's lookup loop, unless it already ran in this conversation (§1.4) |
| `evaluate_game` | Once per line from `lines`: `pgn` = the line exactly as printed, `from_ply: 1`, default depth. Several calls in one turn are fine |
| `analyze_position` | Once per line, on the last ply's `fen_after` from `evaluate_game` (a tool FEN, [SKILL.md §1.2.7](../SKILL.md#127--fen-integrity)), `multipv: 2`: the gap between the two top moves |
| `compare_moves` | Only while writing coach notes, to explain why the engine's move is better than a flagged move |

No board images in the review. The Player Profile is not used ([SKILL.md §1.7.2](../SKILL.md#172--when-to-resolve-the-profile)): only its `player` section, for the files and the band, as in F39.

---

## 1.6.  Method

These rules are built into the script; know them to explain the result.

1. **Lines.** `lines` takes every own move in a position reached in ≥ 1% of games (major and minor). It builds the fewest lines that cover them all, deepest first, and follows the opponent's most common reply. Lines run from move 1, so `evaluate_game` replays them itself.
2. **Soundness.**
   - **Moves to check:** own moves with `cp_loss` ≥ 50.
   - **Dubious moves:** own moves with `cp_loss` ≥ 100.
   - When the engine's move leads to a position in the repertoire, the note names the chapter it transposes into.
   - **Lines to extend:** lines whose last position is ≤ −0.5 from the player's side, or where the best move is ≥ 1.0 pawn ahead of the second (only one move holds).
3. **Games.** Each record with a known side that matches is replayed through the tree. Transpositions count as staying in the repertoire. The first move that leaves it is:
   - **left by you:** the repertoire had another move here;
   - **left by the opponent:** a reply with no answer in the files;
   - **end of preparation:** the line had ended.

   Mistakes from the record's `## Mistakes` section within 16 plies (8 moves) after that point count as *soon after*. The score is from the player's side.
4. **Prepare next.** Every item gets a priority, the highest first (top 15):

   priority = *reach* × *weight* × (1 + *games*)

   - *Reach* is the share of games that reach the position, at least 1% for items that come from the player's games.
   - *Weight* is 2 for a dubious move and 1 for everything else.
   - *Games* counts the records in which the item came up.

   The items are dubious moves and moves to check, F39's holes, unprepared replies and forgotten moves from the games, and lines to extend.

---

## 1.7.  Workflow

### 1.7.1.  Step 1 — Side, files, band and frequencies

Do [F39](f39-prioritise-repertoire.md) Steps 1–3: the side, the files, the band, the tree and the lookup loop until `frontier` prints `to look up 0`. Skip what F39 already did in this conversation for the same side and band.

### 1.7.2.  Step 2 — Engine check

```bash
python3 -I <skill-folder>/scripts/repfreq.py --work "$W" lines
```

The script prints the number of own moves to check and the lines, numbered. Tell the user how many lines there are; each takes up to a minute. Then, for each line `n`:

1. Call `evaluate_game` with the line as printed and `from_ply: 1`.
2. Call `analyze_position` on the last ply's `fen_after` with `multipv: 2`. The gap is the first move's `score` minus the second's, made positive (in pawns). If either has `mate_in`, use 10.
3. Store both. Pass one token per ply, every ply from move 1, as `san:cp_loss:best_move:score` (copied from the plies; write `-` for a null value), then the gap:
   ```bash
   python3 -I <skill-folder>/scripts/repfreq.py --work "$W" evals 3 "d4:0:d4:0.21 Nf6:4:Nf6:0.25 c4:0:c4:0.22 …" 0.4
   ```
   `evals` checks every move against the line and stops on a mismatch: fix the token and retry.

Between rounds, tell the user briefly how far it is (*"7 of 12 lines checked"*). If a call fails, retry once; if it keeps failing, carry on: the review lists the lines that were not evaluated.

### 1.7.3.  Step 3 — Game records

```bash
python3 -I <skill-folder>/scripts/repfreq.py --work "$W" games "<working folder>"/Game_Analysis/*.md
```

The script prints how many games it used and how many it skipped (other side, side unknown, no PGN, other start). If many records have an unknown side, say in one line that setting `player_color` in those records would let them count. Never edit the records yourself. Without any records, skip this step.

### 1.7.4.  Step 4 — Write the review

Before writing, say in one line what will happen (*"I'll write `Repertoire/repertoire_white_review.md`; your coach notes in it are kept."*) and wait for the user's yes, unless they asked for the update. Then:

```bash
mkdir -p "<working folder>/Repertoire"
python3 -I <skill-folder>/scripts/repfreq.py --work "$W" review "<working folder>/Repertoire" --band "1800–2000, rapid and classical"
```

After writing, check that the file is really there and changed, as in F39.

### 1.7.5.  Step 5 — Coach notes

The script writes only tables. Below `<!-- coach notes -->` goes the coach's advice. Go through the first items of "Prepare next" (about five) and write for each:

- **What to do:**
  - **Dubious move:** replace it, or keep it on purpose with the reason (a practical choice, a trap).
  - **Hole or unprepared reply:** suggest an answer that fits the existing repertoire.
  - **Forgotten move:** say what the repertoire move was and why it matters there.
  - **Line to extend:** say how far to extend the line and what to look for.

  Use chess knowledge, and `compare_moves` when a flagged move needs explaining.
- **Which F36 card:** look in `Openings/<Side>/` for the card whose line holds the position. Name it as a link (`[[White/Queen's Gambit Declined (D35)]]`) to update, or name the opening for a new card to create (*"new card: Queen's Gambit Declined, 4.Bg5 Be7"*). Do not create or change cards here; offer it at the end of Step 6.
- **From the games:** where the "Your games" table shows a pattern (a chapter with a poor score, mistakes right after the opponent left the repertoire), say what it means in one or two sentences.

A move to check that loses only 50–99 centipawns is often a matter of taste in the opening: say so rather than urging a change.

On a rerun, the existing notes are kept. Read them, then **add** what changed (a move that was fixed, a new hole, new games) under a dated heading (`### Update YYYY-MM-DD`). Never rewrite or remove the user's own text there.

### 1.7.6.  Step 6 — Summary

In the chat, give a short summary, not the tables:

> *White, 1800–2000 rapid+classical: 12 lines checked, 2 dubious moves (2.g4 against the Dutch, 4.Qc2 is fine but loses a little), 1 line to extend. 9 games: you left the repertoire twice yourself (4.Bf4 instead of 4.Bg5 in the QGD). Prepare first: 4.Bg5 in the QGD, an answer to 2…g6, the Dutch. Saved to `Repertoire/repertoire_white_review.md`.*

End with the offer to update the notebook cards named in the coach notes ([F36](f36-opening-notebook.md)): *"Update these opening cards now?"*

---

## 1.8.  Without a working folder

F29 does not run: it reads the repertoire PGNs and the game records from the folder and writes its review there. Say so in one line ([SKILL.md §1.7.3](../SKILL.md#173--without-a-working-folder)). For a single opening line pasted in the chat, offer F01 or F04 instead.

---

## 1.9.  Quality checklist

- [ ] The lookup loop was finished before `lines` ran
- [ ] Every line from `lines` went through `evaluate_game` (`from_ply: 1`) and `analyze_position` (`multipv: 2`), or the review says which lines were not evaluated
- [ ] No FEN was typed by hand: lines are SAN move lists, and `analyze_position` got `fen_after` from `evaluate_game`
- [ ] Game results came only from records with a known, matching side; records were not changed
- [ ] Work files stayed in a temporary directory; only `Repertoire/repertoire_<side>_review.md` was written, after the user's yes
- [ ] Coach notes cover the top items of "Prepare next", each naming an F36 card; existing notes were kept unchanged
- [ ] The PGN files were not changed
- [ ] The chat shows a short summary and offers to update the named opening cards

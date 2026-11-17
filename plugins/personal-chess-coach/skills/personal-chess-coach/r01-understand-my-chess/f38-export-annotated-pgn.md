# 1.  F38 — Export My Analysis as an Annotated PGN

## 1.1.  User question
> "Can I have this as a PGN?"
> "Export the annotated game so I can import it into Lichess."
> "Give me a PGN file with your comments for Scid."

Or: the user answers yes to F07's offer "Want this as an annotated PGN you can import into a chess GUI or database?"

## 1.2.  Capability unlocked
The user gets a PGN file of a game the coach has annotated, with the coaching comments, evaluations, move symbols (`!`, `?`, `??`, ...) and better lines as variations. They can import it into Lichess, Scid, Chess.com or any engine GUI, and see every comment, symbol and variation at the right move.

F38 does **no new analysis**. It exports the annotations of an [F07](f07-annotate-game.md) analysis of the same game, made earlier in this conversation. The `export_annotated_pgn` tool writes the PGN: it replays the game and every variation, so all moves in the file are legal and correctly numbered. Never write the PGN by hand.

## 1.3.  Validation
A correct implementation demonstrates:
- The exported PGN imports into Lichess and Scid without errors
- Comments, symbols and variations show at the moves F07 annotated
- The main line is the game exactly as played
- The comments and symbols are the ones from the F07 analysis, not new ones

---

## 1.4.  MCP tools used

| Tool | When |
|---|---|
| `export_annotated_pgn` | Once, with the game and all F07 annotations |
| `get_variation` | Only when F07 named a better move without its continuation and a 2–3 move line makes the variation clearer (optional) |

No engine analysis: the evaluations come from the engine results F07 already has (`evaluate_game` or `evaluate_move`).

---

## 1.5.  Workflow

### 1.5.1.  Step 1 — Check that F07 has annotated this game
F38 needs an F07 analysis of this game earlier in the conversation: the annotated move list with its symbols and comments, and the engine results it was built on (`evaluate_game` or `evaluate_move` per ply).

If there is none (e.g. the user pastes a game and asks straight away for an annotated PGN), say so in one line and run [F07](f07-annotate-game.md) first: *"I'll annotate the game first, then export it as a PGN."* Then continue here at Step 2. Do not export a PGN without annotations.

If F05 or F06 analysed the game but F07 did not, also run F07 first: those features annotate only a few moves.

### 1.5.2.  Step 2 — Build the annotations
Make one entry per move that F07 gave a symbol or a comment. Use the 1-based ply index in the game's `plies` list from `load_pgn` or `evaluate_game` (ply 1 is the first move in the PGN: White's first move from the standard start).

| Field | Take it from |
|---|---|
| `ply` | The index of the move in `plies` |
| `symbol` | F07's symbol for the move (`!!`, `!`, `!?`, `?!`, `?`, `??`); leave it out for a move with only a comment |
| `comment` | F07's comment, as shown in the chat |
| `score` | The engine's `score` for that ply (`evaluate_game` or `evaluate_move`), unchanged: pawns, White's perspective, never flip the sign. Leave it out when the ply was not evaluated |
| `mate_in` | Only if F07 found a forced mate after the move (White's perspective) |
| `variation` | For `?` and `??` moves (and `?!` where F07 named the better move): the better move, starting with the side that played this ply. Use the ply's `best_move`, followed by the continuation F07 showed, if any. A `get_variation` call on the ply's `fen_before` gives a continuation: pass its `moves` as is |
| `variation_comment` | Optional, a few words on the line (e.g. "wins the exchange") |

Also pass F07's **In brief** summary as `game_comment`.

Pass the same PGN text that F07 analysed as `pgn`. The tool keeps its header tags and drops comments or variations that were already in it.

Do not add moves, comments or symbols that are not in the F07 analysis. Raw centipawn numbers belong only in `score`, never in a comment.

### 1.5.3.  Step 3 — Call `export_annotated_pgn`
Call it once with `pgn`, `annotations` and `game_comment`.

If it refuses a variation (an illegal move, or a line starting with the wrong side), correct that variation: check that it starts from the position **before** the move played (`fen_before`) and with the side that played it, and verify it with `apply_move` move by move. If it still fails, leave that variation out. Never drop a comment or symbol to make the call pass.

### 1.5.4.  Step 4 — Hand over the PGN
- **With a file tool** (`present_files` / `SendUserFile`): write the `pgn` field to `/mnt/user-data/outputs/<White>-<Black>-<date>.pgn` (leave out what is unknown, e.g. `annotated-game.pgn`) and present that file.
- **Without one:** show the `pgn` field in a code block (` ```pgn `), so it can be copied.

Do not save the PGN in the working folder: F38 hands the file to the user, nothing more.

Then add one or two lines on importing it:
- **Lichess:** *Study* → *Add chapter* → *PGN* tab → paste or upload the file. The evaluations show as an evaluation bar and graph.
- **Scid:** *File* → *Open* the `.pgn`, or *Edit* → *Paste PGN* into a game.
- **Chess.com:** *Analysis* → *Load PGN*.

Show only the line for the program the user named; list all three if they named none.

### 1.5.5.  Step 5 — Offer next steps
- "Want me to go deeper on move [N]?" → triggers F02

---

## 1.6.  Export checklist

- [ ] The game was annotated by F07 in this conversation (or F07 ran first)
- [ ] Every F07 symbol and comment is in `annotations`, at the right ply, and nothing was added
- [ ] `score` values are the engine's, unchanged in sign and unit
- [ ] Every variation starts from the position before the move played, with the side that played it
- [ ] The PGN comes from `export_annotated_pgn`, not written by hand
- [ ] The file is handed over as a `.pgn` file or a code block, not saved in the working folder

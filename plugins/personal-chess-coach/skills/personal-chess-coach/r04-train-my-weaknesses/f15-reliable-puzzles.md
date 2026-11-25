# 1.  F15 — Give Me Reliable Puzzles

## 1.1.  User question

> "Is this position a good puzzle?"
> "Make a puzzle of this position."
> "Let me solve it." / "Show me the first puzzle."
> (or: "yes" to F14's "Solve them now?", or a puzzle picked by F16)

## 1.2.  Capability unlocked

Every puzzle has one objectively best move at each step, checked by the engine at two depths, so the user is never marked wrong for a move that was just as good. The coach shows the puzzle, checks each answer, plays the opponent's replies, explains a wrong move and gives hints on request. Any mate is accepted as correct, as on Lichess.

## 1.3.  Validation

A correct implementation demonstrates:

- A position counts as a puzzle only if `build_puzzle` or `find_puzzles` says `valid`; otherwise the coach explains the `reason` in words
- The board is shown from the solver's side, with whose move it is and the task, but no motif and no solution
- Answers are checked with `puzzlebook.py check`, never by reading the solution and comparing by eye; SAN, UCI and moves in words are accepted
- A wrong move gets a one-line reason, the attempt counts as failed, and the user chooses: try again or see the solution
- Hints are given only on request: first the piece, then the motif
- After the last step: a two-line explanation of the idea

---

## 1.4.  Tools used

| Tool | When |
|---|---|
| `build_puzzle` | When the user gives a position (a FEN, or one from the analysis) and asks whether it is a puzzle, or to make one of it. Takes 5–30 seconds |
| [scripts/puzzlebook.py](../scripts/puzzlebook.py) `check` | For every answer: `--fen` = the puzzle's starting FEN, `--solution` = the solution's SAN moves (space-separated), `--step` = which solver move (1, 2, …) and the user's answer. Works without a folder. Run it with `python3 -I` and its absolute path |
| `evaluate_move` | For a wrong move: on the position `check` printed (`fen`), to say what it costs and what it allows |
| Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)) | The puzzle position, and the position after each reply (`next_fen` from `check`), from the solver's side (`--flip` when the solver is Black) |

The puzzle's FEN and solution come from `find_puzzles`, `build_puzzle` or the puzzle note (F16): never from your own analysis ([SKILL.md §1.2.7](../SKILL.md#127--fen-integrity)).

---

## 1.5.  Workflow

### 1.5.1.  Step 1 — Is it a puzzle? (only for a position the user gives)

Call `build_puzzle` with the FEN. If `valid` is false, say why in one sentence and do not show it as a puzzle:

| `reason` | Say |
|---|---|
| `unbalanced` | One side is already a piece or more up, so the answer is too obvious (or it is the middle of an exchange) |
| `two_good_moves` | Two moves are about equally good, so there is no single answer |
| `winning_anyway` | Several moves win: the position is already won |
| `no_clear_win` | No move wins or saves the position clearly |
| `only_one_legal_move` | There is only one legal move |
| `game_over` | The game is already over in this position |
| `not_confirmed` | A deeper search did not confirm the answer |
| `mate_not_reached` | There is a mate, but it is too long or can be reached in more than one way |

### 1.5.2.  Step 2 — Show the puzzle

Show the board as an **SVG image** from the solver's side (`--flip` when the solver is Black). Below it, in one or two lines:

- **The task**, from `theme_hint`: *"White to move and win."*, *"Black to move and mate."* or *"White to move: find the only move."*
- **Where it comes from**, without giving anything away: *"From your game of 15 November, move 24."* For `opponent_missed`: *"Your opponent missed this on move 17: you play their side."* For `variation`: *"A position that could have arisen after 24.Nf6+ gxf6."*

Then wait for the answer.

### 1.5.3.  Step 3 — Check each answer

Turn an answer in words ("knight to f6") into SAN; if it is unclear which piece is meant, ask. Then:

```bash
python3 -I <skill-folder>/scripts/puzzlebook.py check --fen "<puzzle FEN>" --solution "<SAN moves>" --step <n> "<answer>"
```

| Result | What to do |
|---|---|
| `legal: false` | Say the move is not possible here and ask again. This is not a failed attempt |
| `correct: true`, `solved: false` | *"Correct."* Play the opponent's `reply`, show the board of `next_fen` as an **SVG image**, and ask for the next move (`step` + 1) |
| `correct: true`, `solved: true` | Solved: go to Step 4 |
| `correct: false` | The attempt has failed (it stays failed even if the user then finds it). Call `evaluate_move` on `fen` with the user's move and say in one line what it allows (*"After Qd7, Black plays Rc1+ and mates."*). Then ask: *"Try again, or see the solution?"* |

**Hints**, only when the user asks: the first names the piece to move (from the expected move), the second the motif (a fork, a pin, a back-rank mate…, from your own reading of the solution). A puzzle solved after a hint counts as `solved_with_hint`.

### 1.5.4.  Step 4 — The idea

After the last step, or after showing the solution: the whole solution in numbered SAN, then the idea in at most two sentences, naming the motif (*"A queen sacrifice that deflects the rook from the back rank: Rxd8 is mate."*). Link the source game when there is a record.

Then: for a puzzle from F16, record the result there (F16 §1.6.3). From F14, go on with the next puzzle: *"Next one?"*

---

## 1.6.  Without a working folder

Everything here works without a folder: `check` needs none. Results are not saved.

---

## 1.7.  Quality checklist

- [ ] Only `valid` puzzles were shown; a rejected position got its reason in words
- [ ] The board was an SVG image from the solver's side; the task line gave no motif and no solution
- [ ] Every answer went through `puzzlebook.py check`
- [ ] A wrong move got a reason and the choice "try again or see the solution"
- [ ] Hints only on request, piece first, motif second
- [ ] The idea was explained in at most two sentences after the last step

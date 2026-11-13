# 1.  F01 — Analyze a Chess Position

## 1.1.  User question

> "What happened in this position?"

## 1.2.  Capability unlocked

The user can submit any chess position (FEN string, board diagram, or position description) and receive:

- The objectively best continuation according to the engine
- A human-readable board diagram
- Opening identification (if applicable)
- A coaching summary of the key features of the position

## 1.3.  Validation

A correct implementation demonstrates:

- Evaluation and best move match a reference engine on several known FEN positions
- Output describes plans and ideas, not just move sequences

---

## 1.4.  MCP tools used

|Tool|When|
|---|---|
|`validate_fen`|Always — before any analysis|
| Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)); `fen_to_board` only as text fallback or to check a position yourself |Always — show the board before explaining it|
|`analyze_position`|Always — get top moves and evaluation|
|`get_variation`|When the user wants to see the main continuation, or asks for one side's plan (see §1.6)|
|`identify_opening`|When the position arises from an opening (move number ≤ 15 or recognizable pawn structure)|

---

## 1.5.  Workflow

### 1.5.1.  Step 1 — Accept input

Accept any of:

- A raw FEN string (e.g. `rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1`)
- A position described in natural language or as a move sequence ("after 1.e4 e5 2.Nf3")
- A board diagram pasted as text
- A board picture (image)

How to obtain the FEN (never construct one by hand — see [SKILL.md §1.2.7](../SKILL.md#127--fen-integrity)):

- **Move sequence:** replay the moves with `apply_move` from the starting position and use the returned FEN.
- **Position described only in words, without moves:** ask the user for the moves or a FEN.
- **Board diagram or board picture:** follow [input/board-image.md](../input/board-image.md) completely before Step 2.

### 1.5.2.  Step 2 — Validate

Call `validate_fen`. If invalid, report the error clearly and ask the user to correct it. Do not proceed with an invalid FEN.

### 1.5.3.  Step 3 — Render the board

Show the board as an **SVG image**, as described in [show-board.md](../rendering/show-board.md). This grounds the conversation — the user should see what position is being discussed before reading any analysis.

### 1.5.4.  Step 4 — Analyze

Call `analyze_position` at depth ≥ 20 (or the server default). Capture:

- `side_to_move` — every candidate move is for this side. If the user asked about the *other* side's plan, also follow §1.6
- Top 3 candidate moves with evaluations (White-perspective scores — see the perspective rules in SKILL.md §1.2.5)
- The best move
- The centipawn score (for internal use — do not lead with this in the explanation)

### 1.5.5.  Step 5 — Identify opening and compose plans (conditional)

If the position is from the opening or early middlegame (roughly move ≤ 15), call `identify_opening`.

If an opening is identified, **do not call a tool for the plans**. Compose the opening context section directly from your knowledge of the opening:

- What structural and strategic goals each side is pursuing
- What pawn breaks, piece manoeuvres, or imbalances define the position
- What the identified variation (not just the family) specifically implies for both sides

This knowledge is sufficient for all mainstream openings at the target player level (1800–2000). A tool call will be introduced in a later release when plans become player-specific.

### 1.5.6.  Step 6 — Compose the coaching explanation

Write a structured coaching response:

```
## Position: [short positional label, e.g. "Closed Ruy Lopez after 9...Bb7"]

[Board diagram from Step 3]

### Key features of this position
[2–4 bullets describing material balance, pawn structure, king safety, piece activity, open files, weak squares — whatever is relevant]

### Best continuation
[Best move in SAN notation], [1–2 sentences explaining the concrete idea behind it]

### The plan
[2–3 sentences on the strategic plan this move supports — what piece coordination, pawn breaks, or structural goals follow from it]

### Opening context (if applicable)
[Opening name and 1–2 sentences on what both sides are trying to achieve in this specific variation]
```

Do **not** include:

- Raw centipawn scores in the explanation
- PV lines longer than 2–3 moves unless the user requests them
- Phrases like "the engine says" or "according to Stockfish"

### 1.5.7.  Step 7 — Offer next steps

End with a short offer:

- "Want me to explain why the alternatives are weaker?" → triggers F02 (Compare Candidate Moves)
- "Shall I show the main continuation a few moves further?"
- "Would you like to know the typical plans for both sides from here?"

Then, if a working folder is available ([SKILL.md §1.7.1](../SKILL.md#171--working-folder-decide-once-per-conversation)), offer to save the position to the notebook: see [F36 §1.6](f36-opening-notebook.md#16--when-to-offer-saving).

---

## 1.6.  Plan for the side not to move

Use this when the user asks for one side's plan ("what is White's plan?") and the FEN has the **other** side to move. The engine only ever answers for the side to move, so the plan has to be read carefully.

### 1.6.1.  Step 1 — Name the side to move

Open the answer by saying whose move it is ("It is Black to move here, so first a word on Black's best move"). Do not skip this: it is what keeps the two sides' moves apart.

### 1.6.2.  Step 2 — The plan in reply to best play

Call `get_variation` on the FEN **without** `for_side`, at depth 6–8. Then:

- The first ply is the side to move's best move — describe it in one sentence, as the move the asked side must react to.
- The asked side's moves are the plies whose `side` is that side (in the numbered `line`, `18. Bd3 … 19. e4 …` for White). Extract the plan from **those moves only**: which pieces are rerouted, which pawn breaks are prepared, which squares or files are targeted.
- Never describe the side to move's moves as part of the asked side's plan.

When the user says to use only the engine's variation, this step is the whole analysis: build the plan from the asked side's plies, and do not add ideas that do not appear in them.

### 1.6.3.  Step 3 — Intentions if the side to move passed (optional)

If the asked side's ideas are still unclear, call `get_variation` with `for_side` set to the asked side. The result has `hypothetical: true`: it shows what the asked side would do with a free move. Present it as intentions ("White would like to play e4 and Bc4"), never as a line that will happen. Skip this step when the side to move is in check (the tool refuses it), or when the user asked to use only the engine's main line.

### 1.6.4.  Step 4 — Compose

Use the "The plan" heading from §1.5.6, written for the asked side. Keep the evaluation White-perspective: a positive score means White is better, even though Black is to move.

If a working folder is available ([SKILL.md §1.7.1](../SKILL.md#171--working-folder-decide-once-per-conversation)), end with "Save to your notebook?" ([F36 §1.6](f36-opening-notebook.md#16--when-to-offer-saving)), also when the position is past the opening book.
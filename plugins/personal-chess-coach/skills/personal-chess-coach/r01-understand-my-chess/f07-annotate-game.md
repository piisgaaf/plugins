# 1.  F07 — Annotate My Game Like a Coach

## 1.1.  User question
> "Annotate this game like a coach."
> "Give me commentary on every move."
> "Can I get this game with coaching notes I could paste into my database?"

## 1.2.  Capability unlocked
The user can submit a full game (PGN movetext, or a pasted move list) and receive readable coaching annotations move by move — the way a coach marks up a scoresheet — instead of an engine dump. Unlike [F05](f05-analyze-my-games.md) (opening + critical moments + one narrative summary) and [F06](f06-critical-moments.md) (only the 2–5 turning points), F07 comments on the game's full move list: routine moves are passed over briefly or grouped, but nothing is skipped silently. The result is available both as a readable annotated move list in the conversation and, on request, as a standard PGN file with the same comments embedded inline (`{...}`) so it can be imported into any chess GUI or database.

## 1.3.  Validation
A correct implementation demonstrates:
- An experienced player can read the annotations and understand the game without reading engine variations
- Every move has either a short comment or is explicitly treated as routine/book — nothing is fabricated for narrative effect, and nothing is silently dropped
- The exported PGN (when requested) is valid PGN that a standard chess GUI can import, with comments attached to the correct moves
- No raw centipawn scores appear anywhere in the chat output

---

## 1.4.  MCP tools used

| Tool | When |
|---|---|
| `load_pgn` | Always, first — parse the PGN and replay the whole game in one call |
| `identify_opening` | Once, on the position after the opening phase (roughly move ≤ 15) |
| `evaluate_move` | Once per ply from roughly move 8 onward — get `score_loss` and `is_best_move` for the move actually played |
| Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)); `fen_to_board` only as text fallback or to check a position yourself | On the position before each critical moment only (not every move — see [Step 5](#155--step-5--render-the-chat-view)) |
| `get_variation` | Optional, for a critical moment where the better idea benefits from showing 2–3 moves of the alternative line |

Same tool set as [F05](f05-analyze-my-games.md#14--mcp-tools-used) and [F06](f06-critical-moments.md#14--mcp-tools-used) — F07 differs in scope (every move gets a tier/comment, not just the critical few) and in offering a second, exportable rendering (annotated PGN), not in engine interaction.

---

## 1.5.  Workflow

### 1.5.1.  Step 1 — Accept the game and load it
Same as [F05 Step 1](f05-analyze-my-games.md#151--step-1--accept-the-game-and-load-it): call `load_pgn` with the raw text as given. Capture `tags`, `starting_fen`, `plies`, `final_fen`.

If `load_pgn` errors, report which move failed and why, and stop — do not annotate a partial or unreliable ply list.

### 1.5.2.  Step 2 — Identify the opening
Same as [F05 Step 2](f05-analyze-my-games.md#152--step-2--identify-the-opening). Capture the opening name and ECO code, or state plainly that it wasn't found — never invent one.

### 1.5.3.  Step 3 — Evaluate every move played
Same as [F05 Step 3](f05-analyze-my-games.md#153--step-3--evaluate-every-move-played): call `evaluate_move` for each ply from roughly move 8 onward, capturing `score_loss`, `best_move`, and `is_best_move`. Same depth/cost trade-off for long games (60+ plies): reduce depth (still ≥ 14) rather than skipping plies.

### 1.5.4.  Step 4 — Classify and annotate every move
For each evaluated ply, map its `score_loss` to a tier using the [centipawn loss → coaching tier table](../codebook/coaching-tone.md#11--centipawn-loss--coaching-tier), then to a classic annotation symbol:

| Tier | Symbol | When to write a comment |
|---|---|---|
| Blunder (≥300) | `??` | Always — name the concrete cost and, briefly, what should have been played |
| Mistake (100–299) | `?` | Always — name the concrete cost |
| Inaccuracy (30–99) | `?!` | Usually — a short note on what was slightly better, unless very minor and the game has many of these (then group, see below) |
| Best/equal (<30), but instructive | `!` or `!?` | Only where the move is the point of a plan, a only move, a strong practical try, or a well-found resource — not every accurate move needs praise |
| Best/equal (<30), routine | *(none)* | No symbol, no comment — book theory, forced recaptures, quiet consolidating moves. Do not manufacture praise to fill space. |

For symboled moves, classify the move type using the [move-type taxonomy](../codebook/coaching-tone.md#12--move-type-taxonomy) (tactical / positional / prophylactic / strategic) to decide how to phrase the comment: name the motif for tactical moments, the structural idea for positional ones, the threat prevented for prophylactic ones, the plan for strategic ones. Use the same reasoning approach as F02 — the engine's `best_move` is already known from `evaluate_move`; trace its idea from chess knowledge, optionally confirmed with `get_variation` for a critical moment worth a deeper look.

Comments must stay short: one sentence for `!`/`!?`/`?!`, one to two sentences for `?`/`??`. This is annotation, not a full explanation — if the user wants more, that's F02.

### 1.5.5.  Step 5 — Render the chat view
Present the game as an annotated move list, grouped by move number, White and Black side by side. Only show a board as an **SVG image** ([show-board.md](../rendering/show-board.md), on `fen_before`) at Blunder/Mistake-tier moments — routine and lightly-annotated moves stay text-only so the list reads at a glance.

```
## Annotated game: [White] vs [Black] (if headers present, otherwise omit)

[Opening name] ([ECO code]) — [1 sentence on the opening's idea]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 ...
[continue plainly through book/routine moves with no comment]

18. Nd5?! [one-sentence note on what was slightly better]
18... Qd8

24. Rxf7?? [board diagram — position before the move]
[1–2 sentences: what was missed, the concrete cost, named motif or structural idea]
24... Rxf7

[continue to the end of the game]

### In brief
[2–3 sentences: the overall character of the game and its result — shorter than F05's full summary, since the annotations above already carry the narrative]
```

Do **not** include:
- Raw centipawn scores anywhere
- A board diagram for every move — only at Blunder/Mistake tier
- Long PV lines beyond 2–3 moves
- Phrases like "the engine found" or "Stockfish evaluates this as"
- Manufactured comments on routine moves

### 1.5.6.  Step 6 — Offer the exportable annotated PGN
After the chat view, offer: "Want this as an annotated PGN you can import into a chess GUI or database?"

If accepted (or if the user asked for this format up front), produce standard PGN text with the same comments embedded inline as PGN comments, attached immediately after the move they refer to:

```
[Event "..."]
[White "..."]
[Black "..."]
[Result "..."]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 ... 18. Nd5 {Slightly better was ... because ...} Qd8
... 24. Rxf7?? {This drops ... to a ... } Rxf7 ...
```

Rules for the PGN export:
- Preserve original headers from `load_pgn`'s `tags` if present; omit tags that weren't supplied rather than inventing them
- Attach each comment directly after the move it annotates, in `{...}` braces, using the same tier symbol suffixed to the SAN (`Nd5?!`, `Rxf7??`) per standard PGN annotation convention
- Only annotate moves that received a symbol in Step 4 — routine moves appear in the movetext with no comment, exactly as played
- Do not alter any move, result, or ordering from what `load_pgn` replayed
- Present the PGN in a code block so it can be copied directly, or save it as a `.pgn` file and share it via `present_files` if the user wants a file rather than inline text

### 1.5.7.  Step 7 — Offer next steps
End with a targeted offer:
- "Want me to go deeper on move [N] and walk through why [best move] works?" → triggers F02
- "Shall I compare what was played against the engine's top alternatives there?" → triggers F03
- "Want just the critical moments, without the full move list?" → triggers F06

---

## 1.6.  Annotation quality checklist

Before delivering the annotated game, verify:

- [ ] Every move with `score_loss` ≥ 30 (Inaccuracy or worse) has a symbol and a comment, or an explicit, justified grouping (e.g. "moves 9–14 were routine consolidation")
- [ ] No comment is manufactured for a routine/book move just to fill space
- [ ] Board diagrams appear only at Blunder/Mistake tier, not on every move
- [ ] Every `?`/`??`/`?!`/`!`/`!?` symbol matches the tier table in the codebook
- [ ] No raw centipawn scores appear anywhere in the chat output
- [ ] If a PGN export is produced, it is valid movetext with comments correctly attached to their moves, and headers are only included when actually present in the source
- [ ] If the PGN failed to replay partway through, this is reported clearly rather than annotating an incomplete game

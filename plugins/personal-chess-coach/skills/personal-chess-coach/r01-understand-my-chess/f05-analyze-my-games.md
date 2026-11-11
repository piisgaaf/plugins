# 1.  F05 — Analyze My Games

## 1.1.  User question
> "Can you analyze this game?"
> "Here's a PGN — what happened?"
> "What went wrong in this game?"

## 1.2.  Capability unlocked
The user can submit a full game (PGN movetext, or a pasted move list) and receive a complete game analysis: the opening that was played, the critical moments where the evaluation swung, and a coaching summary of the game as a whole — rather than a move-by-move engine dump.

## 1.3.  Validation
A correct implementation demonstrates:
- Several different PGNs produce correct opening identification
- Critical moments correspond to real evaluation swings (mistakes/blunders), not arbitrary moves
- The game summary reads as a coaching narrative a player can act on, not a list of engine scores

---

## 1.4.  MCP tools used

| Tool | When |
|---|---|
| `load_pgn` | Always, first — parse the PGN and replay the whole game in one call |
| Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)); `fen_to_board` only as text fallback or to check a position yourself | On the starting position, and on each critical-moment position, to ground the narrative |
| `identify_opening` | Once, on the position after the opening phase (roughly move ≤ 15), to get the opening name and ECO code |
| `evaluate_move` | Once per ply — get `score_loss` for the move actually played, relative to the engine's best move in that position |

`load_pgn` does the PGN-specific work (header parsing, movetext cleanup, replaying every move against a live board) in a single call, returning header tags, the starting FEN, and every ply with its SAN move and the FEN before/after it was played. Everything downstream of that — opening identification, per-move evaluation, critical-moment detection, and the coaching write-up — reuses the same single-position tools as F01–F04, just applied per ply.

---

## 1.5.  Workflow

### 1.5.1.  Step 1 — Accept the game and load it

**Multi-game PGN check:** If the PGN contains more than one game, apply the multi-game handling protocol in [SKILL.md §1.4](../SKILL.md#14--multi-game-pgn-handling) before proceeding. Only continue here once the user has identified a single game to analyze.

Accept any of:
- A PGN with full headers and movetext (e.g. `[Event "..."] ... 1.e4 e5 2.Nf3 ...`)
- Bare movetext without headers (e.g. `1. e4 e5 2. Nf3 Nc6 ...`)
- A pasted move list in natural language ("1.e4 e5 2.Nf3 Nc6 3.Bb5 a6 ...")

Call `load_pgn` with the raw text as given. It handles header parsing, movetext cleanup (move numbers, result markers, comments, NAG annotations), and — if the PGN declares a custom starting position via `[FEN]`/`[SetUp]` — starting from that position instead of the standard one. From the response, capture:
- `tags` — header metadata (`Event`, `White`, `Black`, `Date`, `Result`), optional and used for context only
- `starting_fen` — the position the game started from
- `plies` — the ordered list of moves, each with `number`, `side`, `san`, `fen_before`, `fen_after`
- `final_fen` — the position after the last move

If `load_pgn` returns an error (no moves found, or a specific move that failed to replay), report it plainly — which move, and why — and ask the user to check that part of the PGN. Do not attempt to salvage a partial analysis from a game that failed to load; the ply list would be incomplete and any "critical moments" found in it would be unreliable.

### 1.5.2.  Step 2 — Identify the opening

Once the ply list reaches roughly move 15 (or the end of the game if shorter), call `identify_opening` on the `fen_after` of the ply at that point. Capture the opening name and ECO code.

If not found, state that plainly and describe the opening in general terms from chess knowledge — do not invent a name (same rule as F04).

### 1.5.3.  Step 3 — Evaluate every move played

For each ply returned by `load_pgn`, call `evaluate_move` using that ply's `fen_before` and its `san`. Capture `score_loss` and `is_best_move` for each ply.

This is the most expensive step — for long games, evaluating every single ply at full depth may be unnecessary. Prioritize:
- Always evaluate moves from roughly move 8 onward (skip pure book theory already covered by Step 2, unless the user asks for the opening moves too)
- If the game is very long (60+ plies) and depth/time is a constraint, evaluate at a slightly reduced depth (still ≥ 14) rather than skipping plies — every move must be checked for critical moments; only precision may be traded off

### 1.5.4.  Step 4 — Find the critical moments

Use [F06 — Show Me the Critical Moments](f06-critical-moments.md) to detect and select the critical moments from the `score_loss` values gathered in Step 3: F06's [detection rule](f06-critical-moments.md#153--step-3--detect-the-critical-moments) (Mistake/Blunder tier, or an evaluation sign flip) and selection guidance (2–5 most instructive, prioritizing largest `score_loss` and hand-changing moments) are the single source of truth — do not restate or fork the thresholds here.

If there are none (a clean, accurate game), say so explicitly — this is itself useful coaching signal, not a gap to paper over.

For each selected critical moment, show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)) for the position **before** the critical move (that ply's `fen_before`), so the reader can see exactly what was missed.

### 1.5.5.  Step 5 — Classify each critical moment

For each critical moment, classify it using the [move-type taxonomy](../codebook/coaching-tone.md#12--move-type-taxonomy) (tactical / positional / prophylactic / strategic) — this determines how it should be explained (name the motif for tactical misses; name the structural cost for positional ones).

Use the same reasoning approach as F02 (Explain the Best Move) to understand what the better move achieved: the engine's best move at that position is already known from `evaluate_move`'s `best_move` field — trace its idea from chess knowledge, optionally confirmed with `get_variation` if a deeper look is warranted.

### 1.5.6.  Step 6 — Compose the game analysis

```
## Game analysis: [White] vs [Black] (if headers present, otherwise omit this line)

### Opening
[Opening name] ([ECO code]) — [1–2 sentences on what both sides were aiming for, from chess knowledge]

### Critical moments

#### Move [N]: [side]'s [SAN move]
[Board diagram — position before the move]

[2–3 sentences: what the position called for, what was played instead, and the concrete cost — named motif if tactical, structural/strategic cost if positional. Reference the tone tier language from the codebook, never raw centipawn numbers.]

[Repeat for each selected critical moment]

### Game summary
[3–5 sentences telling the story of the game: how the opening went, where it was decided, and the overall character of the game (e.g. "a well-played positional game undone by one tactical oversight on move 24"). This should read as something a coach would say after watching the game, not a score report.]
```

Do **not** include:
- Raw centipawn scores anywhere in the output
- A move-by-move commentary of every single ply — only the critical moments and the summary
- Long PV lines beyond what's needed to illustrate a critical moment (2–3 moves)
- Phrases like "the engine found" or "Stockfish evaluates this as"

### 1.5.7.  Step 7 — Offer next steps

End with a targeted offer:
- "Want me to go deeper on move [N] and explain exactly why [best move] works?" → triggers F02
- "Shall I compare what was played against the engine's top alternatives at that point?" → triggers F03
- "Want to look at the opening in more detail?" → triggers F04

---

## 1.6.  Analysis quality checklist

Before delivering the analysis, verify:

- [ ] The opening name and ECO code are correct, or their absence is stated plainly (never guessed)
- [ ] Every selected critical moment has a real `score_loss` supporting it — nothing is invented for narrative effect
- [ ] Each critical moment names a concrete idea (motif for tactical, structural concept for positional) — not just "this was a mistake"
- [ ] The game summary tells a coherent story, not a list of disconnected facts
- [ ] No raw centipawn scores appear anywhere in the output text
- [ ] A game with no real mistakes is reported as such, not padded with manufactured "critical moments"
- [ ] If the PGN failed to replay partway through, this is reported clearly rather than silently truncating the analysis

# 1.  F06 — Show Me the Critical Moments

## 1.1.  User question
> "Where did this game turn?"
> "Show me the critical moments."
> "What were the key turning points?"

## 1.2.  Capability unlocked
The user can submit a full game (PGN movetext, or a pasted move list) and immediately see where the game changed — the moments where the evaluation swung decisively — without waiting for a full move-by-move narrative. This is the fast, focused counterpart to [F05](f05-analyze-my-games.md#15--workflow): F05 wraps this same detection in an opening summary and a coaching narrative; F06 surfaces just the turning points, quickly, and can be used standalone or as a building block by F05.

## 1.3.  Validation
A correct implementation demonstrates:
- Significant evaluation swings (mistakes/blunders) in annotated games are identified correctly
- A clean game with no real swings is reported as such, not padded with manufactured moments
- The output is scannable at a glance — a reader sees where the game turned without reading a full narrative

---

## 1.4.  MCP tools used

| Tool | When |
|---|---|
| `load_pgn` | Always, first — parse the PGN and replay the whole game in one call |
| `evaluate_move` | Once per ply (from move ~8 onward) — get `score_loss` for the move actually played |
| Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)); `fen_to_board` only as text fallback or to check a position yourself | On the position before each identified critical moment |

This feature reuses the same tools as [F05](f05-analyze-my-games.md#14--mcp-tools-used) — the difference is entirely in scope and presentation, not in engine interaction. No opening identification (`identify_opening`) is needed here; F06 does not narrate the opening.

---

## 1.5.  Workflow

### 1.5.1.  Step 1 — Accept the game and load it

Same as [F05 Step 1](f05-analyze-my-games.md#151--step-1--accept-the-game-and-load-it): call `load_pgn` with the raw text as given (full PGN, bare movetext, or a pasted move list). Capture `starting_fen`, `plies`, and `final_fen`.

If `load_pgn` errors, report which move failed and why, and stop — do not attempt partial detection on an incomplete ply list.

### 1.5.2.  Step 2 — Evaluate every move played

For each ply from roughly move 8 onward, call `evaluate_move` using that ply's `fen_before` and its `san`. Capture `score_loss` and `is_best_move`.

Same cost trade-off as [F05 Step 3](f05-analyze-my-games.md#153--step-3--evaluate-every-move-played): for long games (60+ plies), reduce depth (still ≥ 14) rather than skipping plies — every move must be checked, only precision may be traded off.

### 1.5.3.  Step 3 — Detect the critical moments

This is the canonical definition of a **critical moment**, shared with F05. A ply is a critical moment if either:
- It is classified as a Mistake or Blunder by the [centipawn loss → coaching tier table](../codebook/coaching-tone.md#11--centipawn-loss--coaching-tier) (`score_loss` ≥ 100), or
- The evaluation crosses from one side being better to the other being better (a sign flip in `score_cp` across the move), even if the single-move `score_loss` falls just under the Mistake threshold

Select the 2–5 most instructive moments for the output:
- If there are more than 5, prioritize the largest `score_loss` values and any moment where the game's result changed hands
- If there are none, say so explicitly — a clean, accurate game is a valid and useful result, not a gap to fill with manufactured moments

### 1.5.4.  Step 4 — Sketch the evaluation shape

Before listing individual moments, describe the overall shape of the game in one line, using tier language rather than numbers — e.g. "an even game until move 24, then a decisive swing to Black" or "roughly balanced throughout, with one brief inaccuracy that was corrected." This gives the reader the big picture before the detail.

Never plot or state raw centipawn values or a numeric sequence; describe the trend qualitatively (steady, swinging, one-sided, see-sawing).

### 1.5.5.  Step 5 — Render each critical moment

For each selected critical moment, show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)) for the position **before** the move (`fen_before`). Name what tier it falls into and, in one sentence, what was missed — enough to orient the reader, not a full explanation (that is F02's job if the user wants to go deeper).

### 1.5.6.  Step 6 — Compose the output

```
## Critical moments: [White] vs [Black] (if headers present, otherwise omit)

[One-line evaluation shape summary — Step 4]

### Move [N]: [side]'s [SAN move] — [tier]
[Board diagram — position before the move]
[One sentence: what the position called for instead, and the concrete cost]

[Repeat for each selected critical moment, in move order]
```

If there are no critical moments:

```
## Critical moments: [White] vs [Black]

No critical moments — the evaluation stayed steady throughout, with no move losing more than a minor amount of accuracy. This was a clean, well-played game.
```

Do **not** include:
- Raw centipawn scores or a numeric evaluation graph
- Opening identification or commentary (that's F05/F04)
- A full coaching narrative or game summary (that's F05)
- Long PV lines

### 1.5.7.  Step 7 — Offer next steps

End with a targeted offer:
- "Want me to explain exactly why [move] was the losing moment?" → triggers F02
- "Shall I compare what was played against the best alternative at that point?" → triggers F03
- "Want the full game analysis with opening and summary?" → triggers F05

---

## 1.6.  Output quality checklist

Before delivering the critical-moments view, verify:

- [ ] Every listed moment has a real `score_loss` or sign-flip supporting it — nothing invented
- [ ] The evaluation-shape summary is qualitative, never a raw number or numeric list
- [ ] A clean game with no real swings is reported as such
- [ ] No raw centipawn scores appear anywhere in the output
- [ ] The output is scannable — no full narrative, no opening commentary
- [ ] If the PGN failed to replay partway through, this is reported clearly rather than silently truncating

# 1.  F03 — Compare Candidate Moves

## 1.1.  User question
> "Why is Nd5 better than Nf5?"
> "Compare these candidate moves."
> "Which of these two moves is stronger, and why?"

## 1.2.  Capability unlocked
The user can submit two or more candidate moves for a position and receive a side-by-side comparison ranking them, with the strategic and tactical reasoning behind the ranking — not just a centipawn table.

## 1.3.  Validation
A correct implementation demonstrates:
- Comparisons on master-game candidate moves are demonstrated
- Both strategic and tactical differences are explained, not only the evaluation gap
- The ranking and the reasoning behind it match reference engine output

---

## 1.4.  MCP tools used

| Tool | When |
|---|---|
| `validate_fen` | Always — before any analysis |
| Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)); `fen_to_board` only as text fallback or to check a position yourself | Always — show the board before comparing |
| `analyze_position` | When the user doesn't name specific candidates — use `multipv` to surface the top N moves as candidates |
| `evaluate_move` | For each named candidate — evaluate every move in the set at equal depth |
| `get_variation` | To trace the short follow-up plan for each candidate (2–3 moves deep) |
| `apply_move` | To reach the position after each candidate, for follow-up analysis |

There is no dedicated "compare" tool — this feature composes `evaluate_move` (once per candidate, at the same depth) and `get_variation` (once per candidate) into a single comparison.

---

## 1.5.  Workflow

### 1.5.1.  Step 1 — Establish the position and the candidates

Determine:
- The FEN of the position (from context, or ask if missing)
- The set of candidate moves to compare

If the user names specific moves (e.g. "compare Nd5 and Nf5"), use exactly those. If the user asks to compare candidates without naming them (e.g. "compare the top moves here"), call `analyze_position` with `multipv` set to the desired count (2–3) and use the resulting top moves as the candidate set.

### 1.5.2.  Step 2 — Validate

Call `validate_fen`. Do not proceed with an invalid FEN.

### 1.5.3.  Step 3 — Render the board

Show the board as an **SVG image** for the position being compared from — see [show-board.md](../rendering/show-board.md).

### 1.5.4.  Step 4 — Evaluate every candidate at equal depth

Call `evaluate_move` for each candidate, using the **same depth** for all of them so the comparison is fair. Record for each candidate:
- `score_cp`
- `cp_loss` computed relative to the best move in the set

Rank candidates by `cp_loss` and look up the tone tier for each gap in the [coaching tone codebook](../codebook/coaching-tone.md#11--centipawn-loss--coaching-tier) — the same tiers used by F02.

### 1.5.5.  Step 5 — Trace each candidate's plan

For each candidate, call `apply_move` to reach the resulting position. Immediately call `fen_to_board` on the resulting FEN and check the piece positions yourself (this check is for you: do not show these boards to the user) before reasoning about threats, diagonals, or piece coordination. Never reason from piece names alone — always confirm from the `fen_to_board` output.

Then call `get_variation` (depth 4–6) to understand the concrete threat, structural change, and follow-up plan each move leads to. For each key reply suggested by `get_variation`, call `apply_move` to reach the position after that reply, and verify the resulting position with `fen_to_board` before building any explanation around it. Check specifically: is the suggested reply actually safe (does it hang material)? Does the follow-up plan hold up on the actual board?

Do not paste variations into the output — use them to inform the write-up.

### 1.5.6.  Step 6 — Classify each candidate's character

For each candidate, classify what kind of move it is using the [move-type taxonomy](../codebook/coaching-tone.md#12--move-type-taxonomy) (tactical / positional / prophylactic / strategic).

Comparing candidates often means comparing *across* these categories (e.g. "the tactical shot vs. the safe positional choice") — name the trade-off explicitly when the candidates differ in kind.

### 1.5.7.  Step 7 — Compose the comparison

```
## Comparing candidate moves

[Board diagram — the position being compared from]

### Ranking
1. [Best move] — [one-line verdict]
2. [Next move] — [one-line verdict]
3. [...]

### [Move A]
[2–3 sentences: the idea, the plan, and what kind of move this is (tactical/positional/prophylactic/strategic)]

### [Move B]
[2–3 sentences, same structure]

### Why [Move A] is better than [Move B]
[1–3 sentences on the concrete difference: what does the weaker move fail to achieve, allow, or address, that the stronger move does?]

### In short
[One memorable sentence a student could retain: "Nd5 beats Nf5 because it plants a knight on a square Black cannot contest, while Nf5 walks into ...g6 losing the piece."]
```

If more than two candidates are compared, extend the ranking list and give each its own short section, but keep the "why" comparison focused on the most instructive pair (typically best vs. second-best, or best vs. the user's original guess).

### 1.5.8.  Step 8 — Offer to go deeper

End with a targeted offer:
- "Want the full plan behind [top move] a few moves further?" → triggers F02
- "Shall I add another candidate to the comparison?"
- "Want me to explain why [a specific alternative] is objectively losing?"

---

## 1.6.  Comparison quality checklist

Before delivering the comparison, verify:

- [ ] Every candidate was evaluated at the **same depth**
- [ ] The ranking matches the engine evaluations (best `cp_loss`/best score first)
- [ ] Each candidate's explanation names a concrete **idea**, not just its evaluation
- [ ] The "why better" section names a concrete difference, not just "the engine prefers it"
- [ ] If candidates differ in kind (tactical vs. positional), the trade-off is named explicitly
- [ ] No raw centipawn scores appear in the explanation text
- [ ] No PV lines longer than 3 moves appear verbatim
- [ ] The "In short" summary is memorable and precise
- [ ] Every key claim has been verified against `fen_to_board` output — no piece placement or diagonal control stated from memory
- [ ] White's best replies (from engine variations) were applied with `apply_move` and checked before being used in the explanation
- [ ] No move was described as "safe" or "active" without verifying it doesn't immediately hang material

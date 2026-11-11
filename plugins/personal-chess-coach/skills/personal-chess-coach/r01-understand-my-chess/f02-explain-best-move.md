# 1.  F02 — Explain the Best Move

## 1.1.  User question
> "Why did the engine recommend this move?"
> "Why is Nd5 better than Nf5?"

## 1.2.  Capability unlocked
The user can ask *why* a specific move is recommended and receive an explanation in terms of chess ideas — plans, motifs, piece coordination, structural effects — rather than engine output.

## 1.3.  Validation
A correct implementation demonstrates:
- Explanations describe plans, ideas, and motifs rather than repeating engine lines
- Both positional and tactical positions are handled
- An experienced player finds the explanation informative without needing an engine

---

## 1.4.  MCP tools used

| Tool | When |
|---|---|
| `validate_fen` | Always — before any analysis |
| Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)); `fen_to_board` only as text fallback or to check a position yourself | Always — show the board before explaining |
| `get_best_move` | When the user asks what the best move is without specifying one |
| `evaluate_move` | Always — evaluate the recommended move AND any stated alternatives |
| `get_variation` | To trace the follow-up plan 2–3 moves deep when relevant |
| `apply_move` | To reach the position after the recommended move, for follow-up analysis |
| `analyze_position` | On the resulting position after the best move, to show what was achieved |

---

## 1.5.  Workflow

### 1.5.1.  Step 1 — Establish the position and the move

Determine:
- The FEN of the position to explain (from context, or ask if missing)
- The move to explain (the engine's best, or a specific move the user is asking about)

If a FEN is not available but a game score is, reconstruct the FEN using `apply_move` from the starting position.

If the user asks "what is the best move?" without specifying one, call `get_best_move` first, then explain it.

### 1.5.2.  Step 2 — Validate

Call `validate_fen`. Do not proceed with an invalid FEN.

### 1.5.3.  Step 3 — Render the board

Show the board as an **SVG image** for the **current position** (before the move) — see [show-board.md](../rendering/show-board.md). This is the position being explained.

### 1.5.4.  Step 4 — Evaluate the move and alternatives

Call `evaluate_move` for:
1. The recommended move
2. Any alternative the user mentioned or that appears in the top candidates

This gives the centipawn difference — useful for gauging whether the distinction is critical (+200 cp) or subtle (+15 cp). Compute `cp_loss` from the returned `score_cp` values and look up the tone tier in the [coaching tone codebook](../codebook/coaching-tone.md#11--centipawn-loss--coaching-tier).

### 1.5.5.  Step 5 — Trace the plan (optional but recommended)

Call `get_variation` on the position after the recommended move (use `apply_move` to get the resulting FEN) to depth 4–6. In that position the **opponent** is to move, so the line's first ply is the opponent's reply; use the `side` of each entry in `plies` (or the numbered `line`) to tell the two sides' moves apart. Read the variation to understand:
- The concrete threat created
- The structural or positional benefit
- The follow-up plan

You will use this to inform the explanation — do **not** paste the variation into the output.

### 1.5.6.  Step 6 — Classify the explanation type

Before writing, decide what kind of explanation this is using the [move-type taxonomy](../codebook/coaching-tone.md#12--move-type-taxonomy) (tactical / positional / prophylactic / strategic). A move can have more than one aspect — address the most important one first.

### 1.5.7.  Step 7 — Compose the explanation

```
## Why [Move] is the best move

[Board diagram — the position before the move]

### The idea
[1–2 sentences on the direct idea behind the move: what threat does it create, what square does it control, what piece does it activate?]

### The plan
[2–3 sentences on what follows from this move: what the player is trying to achieve over the next several moves, and what structural or piece activity is gained]

### Why [alternative move] is weaker (if applicable)
[1–2 sentences on the concrete drawback: what does the alternative fail to achieve, or what does it allow the opponent to do?]

### In short
[One sentence summary a student could remember: "Nd5 is best because it establishes an outpost on a square the opponent cannot easily contest, while simultaneously threatening Nxf6."]
```

### 1.5.8.  Step 8 — Offer to go deeper

End with a targeted offer based on what was left unexplained:
- "Want me to show the main line a few moves further?"
- "Shall I explain why [specific alternative] loses material?"
- "Would you like to compare all the top candidate moves side by side?" → triggers F03

---

## 1.6.  Explanation quality checklist

Before delivering the explanation, verify:

- [ ] The explanation names a concrete **idea** (not just "it's better")
- [ ] The explanation names a concrete **plan** (not just the next move)
- [ ] If tactical: the motif is named and the sequence is traced
- [ ] If positional: a structural or piece-activity concept is named
- [ ] No raw centipawn scores appear in the explanation text
- [ ] No PV lines longer than 3 moves appear verbatim
- [ ] The "In short" summary is memorable and precise

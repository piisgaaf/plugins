# 1.  F35 — See My Opponent's Threats

## 1.1.  User question

> "What is my opponent threatening?"
> "What happens if I do nothing here?"
> "What am I missing in this position?"

## 1.2.  Capability unlocked

The user can submit any position and learn what the side **not** to move is threatening — the resource the opponent would gain if the side to move played a useless waiting move. This is the mirror image of F01/F02 (which answer "what should I play"): F35 answers "what does my opponent get to do if I don't deal with it".

## 1.3.  Validation

A correct implementation demonstrates:

- The threat identified matches a reference engine's null-move-probe best reply on several known tactical positions (e.g. an unmet mating threat, a hanging piece, a fork)
- The explanation names the concrete idea (what is captured, what square is invaded, what is forked) rather than just repeating the move
- Quiet, insignificant "threats" (e.g. a routine developing move) are not presented with the same urgency as a genuine tactical or material threat

---

## 1.4.  MCP tools used

| Tool | When |
|---|---|
| `validate_fen` | Always — before any analysis |
| Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)); `fen_to_board` only as text fallback or to check a position yourself | Always — show the board before explaining the threat |
| `get_threats` | Always — returns the engine's null-move-probe candidate(s), each with an `eval_swing_cp` |
| `apply_move` | To reach the position after the threatening move, so the follow-up can be verified on the board |
| `get_variation` | To trace the concrete follow-up 2–3 moves deep once the threatening move is applied |

`get_threats` is a dedicated tool because there is no other way to compose this from existing tools: `analyze_position` and `get_best_move` only ever answer for the side to move, never for the side that just moved. Internally, `get_threats` works by flipping the side-to-move flag in the FEN (a "null move" — an illegal free extra turn for the opponent) and asking the engine what it would do with that free turn. Whatever it finds is exactly the threat.

`get_threats` returns raw facts only (`move`, `score`, `mate_in`, `eval_swing_cp`, `pv`) — it does not decide what counts as "serious". Use `min_eval_swing` to filter, and use the tone/severity judgment described below to phrase the result.

---

## 1.5.  Workflow

### 1.5.1.  Step 1 — Establish the position

Determine the FEN of the position for which the user wants to know the opponent's threats. `get_threats` computes threats **for the side NOT to move in the given FEN** — i.e. if it is Black's move, the tool reports what White is threatening.

### 1.5.2.  Step 2 — Validate

Call `validate_fen`. Do not proceed with an invalid FEN.

### 1.5.3.  Step 3 — Render the board

Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)), and call `fen_to_board` to read the piece placement yourself (do not show that text board as well, unless it is the fallback). Ground the explanation in the actual piece placement before reasoning about threats — never reason about diagonals, forks, or open files from memory alone.

### 1.5.4.  Step 4 — Get the threats

Call `get_threats` with the FEN. Use `multipv: 2-3` to see the top candidate threats, not just one. Start with `min_eval_swing: 0` (no filtering) so you can see the full picture, then apply judgment in Step 5.

### 1.5.5.  Step 5 — Judge severity

For each candidate threat, use `eval_swing_cp` to judge how serious it is, following the same tiers as the [coaching tone codebook](../codebook/coaching-tone.md#11--centipawn-loss--coaching-tier) (the swing is on the same centipawn scale as `cp_loss`):

- **≥ 300 cp or forces mate (`mate_in` present):** a genuine, urgent threat — lead with this.
- **100–299 cp:** a real threat worth addressing, but not immediately losing.
- **30–99 cp:** a minor edge, worth mentioning but not alarming.
- **< 30 cp:** not meaningfully a "threat" — if this is the only candidate returned, tell the user the position has no pressing threat rather than manufacturing one from a quiet move.

Do not surface the raw `eval_swing_cp` number to the user — use it only to calibrate tone, the same rule F02/F03 already follow for `cp_loss`.

### 1.5.6.  Step 6 — Verify the threat on the board

Call `apply_move` with the threatening move to reach the resulting position, and call `fen_to_board` on the result to check it yourself. Confirm the concrete claim (material actually wins, mate actually lands, the fork actually forks two pieces) on that board before describing it — never assert a tactical claim from the move name alone.

If the top candidate carries a meaningful `pv` (note: `pv` starts with the *reply* to the threatening move, not the threat itself), call `get_variation` from the post-threat position (depth 4; its first ply is the defending side's move) to understand what follows and whether the "threat" holds up against best defense, or is refuted by a simple reply.

### 1.5.7.  Step 7 — Compose the explanation

```
## What your opponent is threatening

[Board diagram from Step 3]

### The threat
[Threatening move in SAN], [1-2 sentences on the concrete idea: what is won, what square is invaded, what piece is forked or trapped]

### Why it works
[1-2 sentences on the tactical or positional justification — what makes the move possible right now]

### What happens if you ignore it
[1 sentence, grounded in the verified follow-up from Step 6]

### In short
[One memorable sentence: "If you don't defend f7, Qxf7 wins because your king has no escape square."]
```

If Step 5 concluded there is no meaningful threat, replace the above with a short reassurance: name the best candidate the probe found, but state plainly that it does not amount to a real threat, and why (e.g. "White's null-move probe only turns up a quiet developing move — there's nothing urgent to defend against here").

### 1.5.8.  Step 8 — Offer next steps

End with a targeted offer:

- "Want me to suggest how to meet this threat?" → triggers F02 (Explain the Best Move) on the defended position
- "Should I check if there's a second threat lurking?" → re-run with a higher `multipv`
- "Want the full follow-up line if the threat isn't met?" → triggers a deeper `get_variation` call

---

## 1.6.  Threat quality checklist

Before delivering the explanation, verify:

- [ ] `get_threats` was called on the correct FEN (threats are for the side NOT to move)
- [ ] The threatening move and its consequence were verified with `apply_move` + `fen_to_board`, not asserted from memory
- [ ] Severity language matches the `eval_swing_cp` tier — a quiet move is not called a "threat"
- [ ] No raw centipawn or eval-swing numbers appear in the explanation text
- [ ] If no meaningful threat exists, the response says so plainly instead of manufacturing urgency
- [ ] The "In short" summary names a concrete consequence, not just "the engine found this move"

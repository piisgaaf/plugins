# 1.  F09 — Explain Why I Made the Mistake

## 1.1.  User question
> "Why did I make that mistake?"
> "What went wrong at move N?"
> "Was it a calculation failure or did I just not see the move?"
> "Explain the root cause of my blunder on move N."

## 1.2.  Capability unlocked
For each significant mistake identified by F08, the user receives a root-cause diagnosis — not just what the correct move was, but *why* they chose the wrong one (calculation error, candidate not seen, planning error, assumption bias, etc.) — plus a concrete coaching note on what thinking habit would have caught it. Over multiple games, the Player Profile accumulates a root-cause breakdown that reveals the player's most persistent thinking errors.

## 1.3.  Validation
A correct implementation demonstrates:
- Each mistake receives exactly one root cause from the [taxonomy](../codebook/mistake-root-causes.md)
- The diagnostic reasoning is shown explicitly, not just the conclusion
- The explanation names the specific move and what the player likely thought, then contrasts it with what correct thinking would have produced
- The Player Profile is updated additively: `root_cause_profile` counts, shares, and severities are recomputed; examples capped at 3 per root cause
- Running F09 on 2–3 mistakes from different games produces different root-cause diagnoses (not every mistake is `calculation_error`)

---

## 1.4.  MCP tools used

| Tool | When |
|---|---|
| Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)); `fen_to_board` only as text fallback or to check a position yourself | To display the mistake position before explaining it |
| `get_variation` | To confirm the correct continuation and ground the diagnostic in concrete moves |
| `evaluate_move` | Optional — to re-confirm `score_loss` if the mistake came from a prior session (not in context) |

---

## 1.5.  Relationship to F08

F09 always operates on a mistake already identified by F08. The input to F09 is:
- The mistake move (SAN, move number, color)
- The `fen_before` of the mistake position
- The mistake's F08 category and motif (already classified)
- The `score_loss` value

F09 can run:
1. **Immediately after F08** — the user asks "why did I make that mistake?" during the same session. All data is in context.
2. **In a later session** (only with a working folder, [SKILL.md §1.7.3](../SKILL.md#173--without-a-working-folder)) — the user references a previously analyzed game. Read the Player Profile to locate the game in `analyzed_games`, then re-run `load_pgn` and `evaluate_move` for the specific position if needed.

F09 never re-classifies the category or motif — that is F08's job. F09 only adds the root-cause layer.

---

## 1.6.  Player Profile

### 1.6.1.  Schema extension

F09 writes to the `root_cause_profile` section introduced in the [F08 profile skeleton](f08-classify-my-mistakes.md#153--profile-skeleton-first-run-only):

```yaml
root_cause_profile:
  calculation_error:
    count: 0
    share: 0.00
    severity: low
    examples: []
  candidate_generation:
    count: 0
    share: 0.00
    severity: low
    examples: []
  visualization_failure:
    count: 0
    share: 0.00
    severity: low
    examples: []
  planning_error:
    count: 0
    share: 0.00
    severity: low
    examples: []
  tactical_oversight:
    count: 0
    share: 0.00
    severity: low
    examples: []
  assumption_bias:
    count: 0
    share: 0.00
    severity: low
    examples: []
  time_pressure:
    count: 0
    share: 0.00
    severity: low
    examples: []
```

### 1.6.2.  Example shape

```yaml
root_cause_profile:
  calculation_error:
    examples:
      - game: "SGS-2026-R3-white"
        move: "24.Rxd5"
        category: tactical
        motif: "overloaded_defender"
        root_cause: "calculation_error"
        note: "Saw the rook sacrifice but stopped calculation after 24...Qxd5 25.Qxd5 — missed 25...Rb1+ drawing the queen away"
```

Each example must include: `game` (human-readable ID), `move`, `category`, `motif`, `root_cause`, and `note`. The `note` should describe what the player likely calculated and where the thinking broke down. Maximum 3 examples per root cause — drop the oldest when a fourth arrives.

### 1.6.3.  Write rule

After diagnosing a mistake:
- Increment the relevant root-cause `count`
- Recompute all `share` values = `count / total_mistakes` (where `total_mistakes` is taken from `mistake_summary`)
- Recompute `severity` using the [severity table](../codebook/mistake-root-causes.md#13--severity)
- Append an example (max 3 per root cause)

**Read before writing.** Always read the current profile at session start. F09 is additive only — nothing is deleted.

---

## 1.7.  Workflow

### 1.7.1.  Step 1 — Identify the target mistake

If F08 has already run in this session, the classified mistakes are in context. Confirm with the user which mistake(s) to diagnose, or proceed with the one(s) they referenced.

Without a working folder, F09 only diagnoses mistakes classified earlier in this conversation; if there are none, offer to classify a game first (F08).

If this is a standalone F09 request (new session), ask which game and move number the user wants to investigate. Re-read the Player Profile to locate the game; if needed, re-run `load_pgn` and `evaluate_move` for that position.

### 1.7.2.  Step 2 — Show the position

Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)) for `fen_before` of the target mistake, and name the move played and the move number.

### 1.7.3.  Step 3 — Confirm the correct continuation

Call `get_variation` from `fen_before` at a moderate depth (depth 18–20). This gives the principal variation from the correct move and grounds the diagnosis in what the engine considers best play.

### 1.7.4.  Step 4 — Apply the diagnostic procedure

Apply the [diagnostic procedure](../codebook/mistake-root-causes.md#12--diagnostic-procedure) in order:

1. Was the correct move likely generated as a candidate?
2. Did the player check for opponent replies before moving?
3. Was the calculation correct but stopped too early / was visualization the issue?
4. Was the wrong strategic goal chosen?
5. Was something assumed without verification?
6. Is time-pressure evidence present in the PGN?

State the diagnostic reasoning explicitly in the coaching output — not just the conclusion. For example: *"The correct move 19...e5 is a quiet piece-attack rather than a capture, which suggests it was unlikely to appear as a candidate — pointing to candidate_generation rather than a calculation error."*

### 1.7.5.  Step 5 — Deliver the root-cause explanation

Structure the output as follows:

```
### Why you made this mistake (move [N][color])

**Position:** [brief one-sentence description]
**You played:** [move] | **Better was:** [correct move]

**Root cause: [Root Cause Label]**

[2–4 sentences explaining what the player most likely thought, where the thinking
went wrong, and what the correct thought process would have looked like. Be specific
to the position — not generic. Name pieces, squares, and threats.]

**What to practise:** [1–2 sentences from the coaching implications table, adapted to this position.]
```

Do not expose raw centipawn scores or engine lines without context. Reference the specific move and position.

### 1.7.6.  Step 6 — Update the Player Profile

Apply the write rule from section 1.6.3. Write the updated profile back to the profile file (full overwrite — read first, merge in memory, then write). Skip this step without a working folder.

### 1.7.7.  Step 7 — Offer next steps

After each root-cause explanation, offer:
- "Want me to explain another mistake from this game?" → repeat from Step 1 for the next mistake
- "Shall I show your root-cause breakdown across all analyzed games?" → summarise `root_cause_profile` from the profile
- "Want a training recommendation based on your most frequent root cause?" → use [coaching implications](../codebook/mistake-root-causes.md#14--coaching-implications)

---

## 1.8.  Quality checklist

Before delivering output, verify (without a working folder, skip the items about the Player Profile):

- [ ] The board was shown (per show-board.md) before the explanation
- [ ] `get_variation` was called to confirm the correct continuation
- [ ] The diagnostic procedure was applied in order — not guessed at
- [ ] The root cause is from the [taxonomy vocabulary](../codebook/mistake-root-causes.md#15--root-cause-motif-vocabulary)
- [ ] The explanation names specific moves and squares — not generic patterns only
- [ ] The Player Profile was read before writing — no prior root-cause data was discarded
- [ ] `share` and `severity` were recomputed after incrementing `count`
- [ ] No raw centipawn scores appear in the coaching output
- [ ] The example added to the profile includes all required fields: `game`, `move`, `category`, `motif`, `root_cause`, `note`

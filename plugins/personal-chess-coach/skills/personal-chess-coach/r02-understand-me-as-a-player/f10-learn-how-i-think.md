# 1.  F10 — Learn How I Think

## 1.1.  User question
> "How do I think during a game?"
> "What are my thinking habits?"
> "Do I calculate too shallowly?"
> "What does my decision-making look like?"
> "Ask me about my thinking on that move."

## 1.2.  Capability unlocked
After each game analysis the coach asks targeted reflective questions about critical moments — not to re-run the engine, but to hear the player describe what they were thinking. The answers are used to build a persistent **Thinking Profile** that accumulates across sessions. Later coaching sessions consume the profile to give personalised feedback: *"You tend to stop calculating one move too early — watch for that here."*

## 1.3.  Validation
A correct implementation demonstrates:
- After a game analysis (F05/F06/F07/F08/F09), the coach asks at least 2 reflective questions anchored to concrete moments in the game
- Questions probe different dimensions: candidate generation, calculation depth, forcing moves, decision biases
- Player answers are interpreted and mapped to one or more `thinking_patterns` fields
- The Thinking Profile accumulates additively across multiple sessions — no prior observations are lost
- A second session on a different game produces questions and observations that may confirm, refine, or extend existing patterns — not merely duplicate them
- Existing patterns from the profile are referenced in coaching output: *"This confirms your tendency to avoid sacrifices"*

---

## 1.4.  MCP tools used

F10 does not require engine calls of its own. All positions referenced in reflective questions come from the ply list already in context (from F05/F06/F07/F08/F09).

| Tool | When |
|---|---|
| Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)); `fen_to_board` only as text fallback or to check a position yourself | To display a position before asking a reflective question about it |

---

## 1.5.  Relationship to earlier features

F10 always runs after at least one of F05, F06, F07, F08, or F09 has completed in the same session. The critical moments and classified mistakes from those features are the anchors for reflective questions.

F10 can also run in a standalone session if the user explicitly asks about their thinking habits. In that case, load the Thinking Profile from the Player Profile and provide a summary of observed patterns, then offer to ask questions about a specific game.

Without a working folder ([SKILL.md §1.7.3](../SKILL.md#173--without-a-working-folder)), the standalone summary is not available. After a game analysis in this conversation, ask the questions and interpret the answers as usual, but skip Steps 1 and 6 and do not refer to patterns from earlier sessions.

F10 does not re-classify mistakes (F08's job) or diagnose root causes mechanically (F09's job). It elicits the player's own account of their thought process, then interprets that account to update the profile.

---

## 1.6.  Player Profile

### 1.6.1.  Schema extension

F10 adds a `thinking_profile` section to the Player Profile:

```yaml
thinking_profile:

  calculation_depth:
    tendency: null          # e.g. "Stops one move too early", "Adequate", "Deep but slow"
    confidence: low         # low / medium / high — increases with more observations
    observations: 0
    notes: []               # up to 3 most recent supporting observations

  candidate_generation:
    quality: null           # e.g. "Good", "Misses quiet moves", "Overlooks opponent resources"
    confidence: low
    observations: 0
    notes: []

  forcing_moves:
    often_missed: null      # true / false / null (unknown)
    confidence: low
    observations: 0
    notes: []

  decision_biases:
    observed: []            # list of bias labels (see §1.6.2)
    confidence: low
    observations: 0
    notes: []
```

### 1.6.2.  Bias labels

When adding to `decision_biases.observed`, use one of these standardised labels (or a free-form label if none fits):

| Label | Meaning |
|---|---|
| `avoids_sacrifices` | Consistently declines sacrifice opportunities even when they are objectively correct |
| `assumes_recaptures` | Assumes the opponent will recapture as expected; misses Zwischenzug |
| `prefers_forcing_play` | Chooses forcing/tactical lines over quieter winning continuations |
| `avoids_simplification` | Resists exchanges even when simplifying improves the position |
| `trusts_intuition_over_calculation` | Plays the "feeling" move without verifying it concretely |
| `underestimates_opponent_resources` | Assumes opponent is passive; misses defensive resources |

### 1.6.3.  Example shape

```yaml
thinking_profile:
  calculation_depth:
    tendency: "Stops one move too early"
    confidence: medium
    observations: 4
    notes:
      - game: "SGS-2026-R7-white"
        move: "20.Nxd8"
        note: "Saw the queen capture but stopped before checking 20...Nd3-e1 recapturing the queen"
      - game: "EML-2025-R6-black"
        move: "20...Be6"
        note: "Calculated Bh6+ check but stopped one move short of seeing the fork on d6"
  decision_biases:
    observed:
      - avoids_sacrifices
      - assumes_recaptures
    confidence: medium
    observations: 3
    notes:
      - game: "SGS-2026-Mark-white"
        move: "18.Nxf7+"
        note: "Chose forcing sacrifice over clinical Nxc6; preference for dynamic play over material"
```

Each note must include: `game` (human-readable ID), `move`, and `note`. Maximum 3 notes per field — drop the oldest when a fourth arrives.

### 1.6.4.  Write rule

After interpreting the player's reflective answers:
- Update the relevant `thinking_profile` field(s)
- Increment the `observations` counter for each updated field
- Raise `confidence` one level (`low` → `medium` → `high`) when `observations` reaches 3 and 6 respectively
- Append a note (max 3 per field)
- For `decision_biases.observed`, append any new bias labels not already present; do not duplicate
- For `tendency` and `quality` fields: if the new observation is consistent with the existing value, leave it; if it contradicts, update to reflect the nuance (e.g. "Usually stops early; adequate in tactical positions")

**Read before writing.** Always read the current profile at session start. F10 is additive only — nothing is deleted.

---

## 1.7.  Workflow

### 1.7.1.  Step 1 — Read the Player Profile

Skip this step without a working folder (§1.5). Otherwise read the current profile (following the rule in [SKILL.md §1.7](../SKILL.md#17--player-profile)). Hold the existing `thinking_profile` in context — it informs how questions are framed and whether a new observation confirms or contradicts a prior pattern.

If `thinking_profile` is absent (first F10 run), add the skeleton from §1.6.1.

### 1.7.2.  Step 2 — Select anchor positions

From the current session's analysis (F05/F08/F09 output), select 2–4 positions to use as reflective anchors. Prioritise:
1. **Mistakes with root cause `candidate_generation`** — these are the best windows into what the player was searching
2. **Mistakes with root cause `planning_error`** — reveal strategic thinking habits
3. **Moments where the player found the best move** — understanding correct thinking is as valuable as diagnosing errors
4. **Positions that probe an existing `thinking_profile` pattern** — if the profile already shows `avoids_sacrifices`, pick a position where a sacrifice was or wasn't found

Aim for variety across the selected anchors: do not ask multiple questions that probe the same dimension.

### 1.7.3.  Step 3 — Ask reflective questions

For each anchor position:
1. Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md))
2. State the move played and the move number
3. Ask one focused reflective question about the player's thinking at that moment

**Question templates by dimension:**

| Dimension | Example question |
|---|---|
| Candidate generation | "What moves were you considering here before you chose [move]?" |
| Calculation depth | "How far ahead did you calculate before playing [move]? What did you see?" |
| Forcing moves | "Did you look for checks or captures first, or did [move] feel like the natural choice?" |
| Decision bias | "You had [alternative] available — what made you choose [move] instead?" |
| Correct thinking | "You found [best move] here — what was your reasoning? What did you calculate?" |

Ask one question at a time. Wait for the player's answer before asking the next question or moving to interpretation.

### 1.7.4.  Step 4 — Interpret the answers

Map the player's answers to `thinking_profile` fields using these heuristics:

| Player says... | Maps to |
|---|---|
| "I only looked one move ahead" / "I didn't check their reply" | `calculation_depth.tendency` = stops too early |
| "I never considered [correct move]" / "I didn't see that at all" | `candidate_generation.quality` = misses [type of move] |
| "I didn't look for checks first" | `forcing_moves.often_missed` = true |
| "I felt like I should attack / exchange / simplify" without calculation | `decision_biases` += appropriate label |
| "I calculated 4–5 moves deep and saw the threat" | `calculation_depth.tendency` = adequate / deep |
| "I considered [correct move] but rejected it because..." | `candidate_generation.quality` = generates good candidates; examine why it was rejected for `planning_error` or `assumption_bias` |

State the interpretation explicitly in your coaching output before updating the profile. For example: *"You mentioned you never considered Bh6+ — that points to a candidate-generation gap for quiet checking moves, which matches what we've seen before."*

### 1.7.5.  Step 5 — Deliver the thinking summary

After all questions and answers, summarise what was learned:

```
### How you think (updated after [game ID])

**Calculation depth:** [current tendency + confidence]
**Candidate generation:** [current quality + confidence]
**Forcing moves:** [often missed / rarely missed / unknown]
**Decision biases:** [list of observed labels, or "none identified yet"]

[2–3 sentences connecting what was revealed in this session to the existing profile.
Note confirmations ("This is the third time we've seen you stop one move too early")
and new findings ("This is the first indication that you prefer forcing play over quiet wins").]
```

Reference the existing `thinking_profile` where relevant — make it clear the coach is building on prior sessions, not starting from scratch.

### 1.7.6.  Step 6 — Update the Player Profile

Skip this step without a working folder (§1.5).

Apply the write rule from §1.6.4. Write the updated profile back to the profile file (full overwrite — read first, merge in memory, then write). Update the `# Last updated` comment at the top of the file.

### 1.7.7.  Step 7 — Offer next steps

After delivering the thinking summary, offer:
- "Want me to ask about another position from this game?" → repeat from Step 3 for the next anchor
- "Shall I show your full Thinking Profile across all sessions?" → summarise `thinking_profile` from the profile
- "Want a training recommendation based on your thinking patterns?" → use coaching implications from §1.8

---

## 1.8.  Coaching implications

| Pattern | Coaching recommendation |
|---|---|
| `calculation_depth` stops too early | Extend every calculation line by one forcing move before deciding; practice "what can my opponent do next?" as a final check |
| `candidate_generation` misses quiet moves | Before deciding, apply the "what is the best move for my opponent?" question; study prophylaxis and quiet positional moves |
| `forcing_moves` often missed | Start candidate search with checks and captures before considering other moves; use the LPDO (Loose Pieces Drop Off) scan |
| `avoids_sacrifices` | Study sacrifice patterns; practice calculating forcing lines after piece sacrifices; trust concrete variations over material count |
| `assumes_recaptures` | Before every capture sequence, ask: "does my opponent have to recapture?" — study Zwischenzug |
| `prefers_forcing_play` | Practice recognising when the position calls for restraint; study quiet winning techniques in won positions |
| `trusts_intuition_over_calculation` | Discipline: require at least one concrete variation before playing any move that feels "obvious" |

---

## 1.9.  Quality checklist

Before delivering output, verify (without a working folder, skip the items about the Player Profile):

- [ ] Player Profile was read before any questions were asked
- [ ] The board was shown (per show-board.md) for each anchor position before the question about it
- [ ] Questions were asked one at a time, not as a list
- [ ] Anchor positions were selected for variety across dimensions
- [ ] Each answer was interpreted and mapped to a specific `thinking_profile` field
- [ ] The interpretation was stated explicitly in the coaching output before writing the profile
- [ ] New observations were checked against existing profile patterns (confirm / refine / extend)
- [ ] `confidence` was raised where `observations` thresholds were met
- [ ] `notes` were capped at 3 per field — oldest dropped when a fourth arrived
- [ ] Profile was written additively — no prior observations were discarded
- [ ] The thinking summary references prior sessions where a pattern is confirmed

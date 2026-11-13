# 1.  F11 — Learn My Playing Style

## 1.1.  User question
> "What kind of player am I?"
> "What is my playing style?"
> "What openings do I usually play?"
> "Am I a tactical or positional player?"
> "What are my strengths as a chess player?"
> "Show me my playing style profile."

## 1.2.  Capability unlocked
The coach derives a persistent model of the player's chess identity from accumulated game data: a style archetype (Positional, Tactical, Universal), a list of preferred openings per color, and observed strengths. The model is built entirely from evidence already in the Player Profile — no new engine calls are needed. It accumulates across sessions: every newly analyzed game potentially refines the archetype, adds to the opening frequency count, or confirms a strength.

## 1.3.  Validation
A correct implementation demonstrates:
- Style archetype is derived from the ratio of positional vs tactical mistake categories and from `root_cause_profile` and `thinking_profile` patterns — not asserted arbitrarily
- Preferred openings are derived from frequency across `analyzed_games` — openings appearing in ≥ 3 games as a given color are listed as preferred
- Strengths are inferred from low-error phases (e.g., `opening.count = 0` → opening preparation is a strength) and from games won or drawn from difficult positions
- The profile is updated additively — no prior data is overwritten
- A second F11 run after new games are analyzed refines or confirms the style; it does not reset it
- The coaching output reads as a portrait of the player, not a statistics report

---

## 1.4.  MCP tools used

F11 derives everything from the Player Profile already in memory. No engine calls are required.

| Tool | When |
|---|---|
| `identify_opening` | Optional — only if an opening name is missing from an `analyzed_games` entry |

F11 does **not** call `evaluate_game`, `evaluate_move`, or any position analysis tool. All data comes from the `analyzed_games` registry, `mistake_categories`, `root_cause_profile`, and `thinking_profile` sections of the Player Profile.

---

## 1.4.1.  Blitz game handling

Blitz games (identified by `time_control: blitz` in their `analyzed_games` entry) are **included** when counting games played and computing win/draw rates for trend analysis, but their openings are sourced and labelled separately from classical-game openings.

- In the `preferred_openings` derivation (§1.6.3), bucket and count blitz openings independently. Label them with a note, e.g. `"Sicilian Defense: Dragon Variation (blitz, 4 games)"`.
- When classical data for a color/opening bucket is thin (< 3 games), F11 **may** supplement with blitz opening data to fill in the picture — but must explicitly label this as blitz-sourced and note the lower confidence.
- Archetype inference (§1.6.2) and strength inference (§1.6.4) use only classical games' mistake data, as blitz games are not mistake-classified.

---

## 1.5.  Minimum data requirement

F11 requires at least **5 analyzed games** (entries in `analyzed_games`) before assigning an archetype with any confidence. Below that threshold:

- Derive `preferred_openings` from whatever games exist (frequency still applies; ≥ 2 games suffices at low confidence)
- Set `archetype` to `null` and `confidence` to `low`
- Tell the user: *"I need a few more games before I can draw reliable conclusions about your style. Here is what I can see so far."*

---

## 1.6.  Player Profile

### 1.6.1.  Schema extension

F11 adds a `playing_style` section and a `strengths` list to the Player Profile. If these sections are absent (first F11 run), add the skeleton below.

```yaml
playing_style:
  archetype: null           # Positional | Tactical | Universal | null (insufficient data)
  confidence: low           # low / medium / high
  observations: 0           # number of games that contributed to the archetype inference
  notes: []                 # up to 3 most recent observations supporting the archetype

strengths: []               # free-form list, e.g. ["Opening preparation", "Endgame technique"]

preferred_openings:
  white: []                 # opening names appearing in ≥ 3 games as White
  black_vs_e4: []           # opening names appearing in ≥ 3 games as Black vs 1.e4
  black_vs_d4: []           # opening names appearing in ≥ 3 games as Black vs 1.d4
  black_vs_other: []        # opening names appearing in ≥ 3 games as Black vs other first moves
```

### 1.6.2.  Archetype inference rules

Derive the archetype from the existing profile data using these rules, applied in order:

| Condition | Archetype |
|---|---|
| `positional.share ≥ 0.55` | Positional |
| `tactical.share ≥ 0.55` | Tactical |
| `planning_error.share ≥ 0.20` and `tactical_oversight.share < 0.10` | Positional (struggles with long-term plans — characteristic of positional players who overreach) |
| `tactical_oversight.share ≥ 0.15` and `planning_error.share < 0.10` | Tactical (oversight pattern — characteristic of tactical players who skip positional evaluation) |
| `thinking_profile.decision_biases` includes `avoids_sacrifices` | Positional (bias toward material retention) |
| `thinking_profile.decision_biases` includes `prefers_forcing_play` | Tactical (bias toward forcing sequences) |
| None of the above produce a clear signal | Universal |

If multiple rules fire, the one with the strongest supporting evidence takes precedence. State which rule produced the archetype in the coaching output.

### 1.6.3.  Preferred openings derivation

For each entry in `analyzed_games`:
1. Extract `opening` (the opening name string), `color`, and the first move of the opponent (infer from the opening name when possible: names containing "Sicilian", "French", "Caro-Kann", "King's Indian", "Nimzo" etc. identify Black responses to 1.e4 or 1.d4).
2. Bucket each opening by `color` and opponent first move.
3. Count frequency per opening name (normalize: strip ECO codes and sub-variation suffixes for grouping — e.g. "Sicilian Defense: Dragon Variation, Yugoslav Attack (B76)" and "Sicilian Defense: Dragon Variation, Yugoslav Attack, Modern Line (B76)" both count as "Sicilian Defense: Dragon Variation").
4. List openings with frequency ≥ 3 in the relevant bucket as preferred. If no opening reaches 3, list the top 2 most frequent (with a note that frequency is low).

### 1.6.4.  Strengths inference rules

Infer strengths from these signals:

| Signal | Strength label |
|---|---|
| `opening.count = 0` across ≥ 8 analyzed games | `Opening preparation` |
| `endgame.count = 0` across ≥ 8 analyzed games | `Endgame technique` |
| `tactical.share ≤ 0.15` across ≥ 8 analyzed games | `Tactical vigilance` |
| `positional.share ≤ 0.20` across ≥ 8 analyzed games | `Positional understanding` |
| Win rate ≥ 60% across ≥ 8 analyzed games (compute from `result` field) | `Converting advantages` |
| Draw rate ≥ 40% across ≥ 8 analyzed games and win rate ≥ 30% | `Resilience and fighting spirit` |
| `thinking_profile.calculation_depth.tendency` indicates adequate/deep and `confidence` ≥ medium | `Calculation` |

Only assert a strength when the evidence threshold is met. Do not invent strengths from insufficient data — omit that category or note "insufficient data".

### 1.6.5.  Write rule

After deriving the style profile:
- Set `playing_style.archetype` to the derived value (or `null` if insufficient data)
- Increment `playing_style.observations` by the number of games that contributed to this derivation
- Raise `confidence` one level (`low` → `medium` → `high`) when `observations` reaches 5 and 10 respectively
- Append a note (max 3 per field — drop oldest when a fourth arrives) summarizing the key evidence for the archetype
- Overwrite `preferred_openings` buckets with the freshly derived lists (these are always recomputed from the full `analyzed_games` registry, not accumulated additively)
- Overwrite `strengths` with the freshly derived list (also always recomputed)

**Read before writing.** Always read the current profile at session start. F11 is the only feature that overwrites (rather than appends to) `preferred_openings` and `strengths` — this is intentional, as these fields are always derived from the full game registry.

---

## 1.7.  Workflow

### 1.7.1.  Step 1 — Read the Player Profile

Without a working folder ([SKILL.md §1.7.3](../SKILL.md#173--without-a-working-folder)), do not run this feature: say in one line that it needs a saved player profile (Cowork with a project folder), and offer to analyze or classify a game instead. Otherwise read the current profile (following the rule in [SKILL.md §1.7](../SKILL.md#17--player-profile)). If `playing_style`, `strengths`, or `preferred_openings` sections are absent, add the skeletons from §1.6.1.

Check `mistake_summary.games_analyzed`. If fewer than 5, note this to the user (see §1.5) and proceed with reduced confidence.

### 1.7.2.  Step 2 — Derive preferred openings

Apply the derivation rules from §1.6.3 to the full `analyzed_games` list. Build the four buckets (white, black_vs_e4, black_vs_d4, black_vs_other).

### 1.7.3.  Step 3 — Derive the style archetype

Apply the archetype inference rules from §1.6.2 in order. Identify which rule(s) fired and what evidence supports them. Record the primary rule and evidence for the coaching note.

### 1.7.4.  Step 4 — Derive strengths

Apply the strength inference rules from §1.6.4. Compute win rate and draw rate from `analyzed_games` result fields (`1-0`, `0-1`, `1/2-1/2`), filtered to games where the player's `color` matches the winning side.

### 1.7.5.  Step 5 — Deliver the style portrait

Present the findings as a coaching portrait, not a data dump:

```
## Your Playing Style

**Archetype: [Positional / Tactical / Universal]** (confidence: [low/medium/high], based on [N] games)

[2–3 sentences describing what this archetype means for this player specifically.
Ground it in the evidence: name the mistake ratio, the planning pattern, or the
thinking bias that produced this conclusion. Not generic archetype descriptions.]

**Preferred Openings**

| Color | Opening(s) |
|---|---|
| White | [list] |
| Black vs 1.e4 | [list or "varies / insufficient data"] |
| Black vs 1.d4 | [list or "varies / insufficient data"] |

**Strengths**

[Bulleted list of inferred strengths, each with a one-sentence rationale.
If no strengths can be inferred yet, say so and explain what evidence is still needed.]

**What this means for your training**

[2–3 sentences connecting the style portrait to a concrete study priority.
E.g. a positional player with planning errors should study pawn structures and long-term plans;
a tactical player with candidate generation gaps should practice systematic move search.]
```

Do not expose raw counts or shares in the coaching output. Refer to patterns, not percentages.

### 1.7.6.  Step 6 — Update the Player Profile

Apply the write rule from §1.6.5. Write the updated profile back to the profile file (full overwrite — read first, merge in memory, then write). Update the `# Last updated` comment at the top of the file.

### 1.7.7.  Step 7 — Offer next steps

After delivering the style portrait, offer:
- "Want me to show how your style has evolved across tournaments?" → compare `analyzed_games` entries by event or date range
- "Shall I recommend openings that suit your style?" → triggers F04 for style-matched opening suggestions
- "Want a training plan based on your style and weaknesses?" → cross-reference `recurring_weaknesses` with the style archetype for a study recommendation

---

## 1.8.  Coaching implications

| Style | Training priority |
|---|---|
| Positional | Study pawn structures, long-term planning, prophylaxis, and endgame technique; use master games rather than tactics puzzles as primary material |
| Tactical | Develop positional evaluation skills; study quiet moves, piece improvement, and strategic plans in addition to tactics; practice candidate generation discipline |
| Universal | Identify which of the two disciplines (positional or tactical) produces more mistakes and prioritize that; no single dominant training focus |

---

## 1.9.  Quality checklist

Before delivering output, verify:

- [ ] Player Profile was read before any derivation — existing `playing_style` data was held in context
- [ ] `analyzed_games` count was checked; minimum data threshold was applied
- [ ] Preferred openings were derived from the full `analyzed_games` registry, not from memory or assumption
- [ ] Blitz openings were bucketed separately and labelled as blitz-sourced; used to supplement classical data only when classical data is thin (< 3 games per bucket)
- [ ] Archetype and strength inference used only classical games' mistake data — blitz games excluded from mistake-based signals
- [ ] Archetype rules were applied in order; the rule that fired and its evidence are stated
- [ ] Strengths were inferred from evidence thresholds — none invented from insufficient data
- [ ] Win rate and draw rate were computed from `result` and `color` fields, not asserted from memory
- [ ] The coaching output names specific patterns (mistake ratios, thinking biases, opening names) — not generic descriptions
- [ ] `preferred_openings` and `strengths` were recomputed from the full registry (not accumulated)
- [ ] `playing_style.observations` was incremented and `confidence` raised if thresholds were met
- [ ] Profile was written; `# Last updated` comment was updated
- [ ] No raw counts or centipawn values appear in the coaching output

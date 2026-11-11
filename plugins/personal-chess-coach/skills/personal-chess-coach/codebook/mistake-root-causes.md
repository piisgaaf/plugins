# 1.  Mistake Root-Cause Taxonomy

Shared reference for diagnosing *why* a mistake was made. Used by F09 and any later feature that builds on root-cause analysis.

A root cause is assigned to each classified mistake (i.e. any move with `score_loss` ≥ 100). Root causes are orthogonal to categories: a tactical mistake can stem from a candidate-generation failure or a calculation error; a positional mistake can stem from a planning error or an assumption bias.

---

## 1.1.  Root causes

| Root cause | When to assign | Typical indicators |
|---|---|---|
| **calculation_error** | The player considered the correct move or a move in the right direction, but miscounted variations, missed a forcing reply, or stopped the calculation one move too early | The correct move was "almost" played; the player's move is objectively reasonable until the missed reply; requires only 2–4 more moves of calculation to refute |
| **candidate_generation** | The correct move was never considered — it was outside the player's search tree entirely | The correct move is surprising, quiet, or involves an unexpected piece; the played move is the most natural-looking alternative |
| **visualization_failure** | The player could generate the candidate and knew the general idea, but couldn't hold the resulting position accurately in mind | Mistakes in long forced lines; confusion about piece positions after multiple exchanges; errors involving pieces that move off and back to a square |
| **planning_error** | The calculation was locally correct but served the wrong strategic goal | The move is reasonable in isolation but inconsistent with the requirements of the position (e.g., attacking when defence was required, simplifying when activity was needed) |
| **tactical_oversight** | The player moved without checking for opponent threats first — a basic procedural failure | The opponent's reply is a simple threat (check, capture, fork) that would have been caught by a one-move blunder check |
| **assumption_bias** | The player assumed a recapture was forced, a piece was safe, or a square was inaccessible — without verifying | Phrases like "of course", "obviously", or "automatically" describe the thought process; the refutation involves the opponent ignoring the expected recapture |
| **time_pressure** | The mistake is consistent with a hasty decision under clock pressure | Only applicable when clock data (e.g. `%clk` annotations) is present in the PGN; do not assign without clock evidence |

---

## 1.2.  Diagnostic procedure

Apply these questions in order to arrive at the most likely root cause. Stop at the first question that resolves the case.

1. **Was the correct move generated as a candidate?**
   - No → `candidate_generation`
   - Yes → continue

2. **Did the player check for the opponent's reply before moving?**
   - No (opponent's reply is a simple one-move threat) → `tactical_oversight`
   - Yes → continue

3. **Was the correct move's idea understood (plan/goal), but the forcing sequence miscounted?**
   - Yes → `calculation_error` or `visualization_failure` (use `visualization_failure` if the error involves tracking piece positions across many exchanges; use `calculation_error` if the player stopped the tree too early)

4. **Was the forcing sequence correctly calculated, but the wrong strategic goal was chosen?**
   - Yes → `planning_error`

5. **Did the player assume something without verifying (recapture, safety, square control)?**
   - Yes → `assumption_bias`

6. **Is clock data present and does the move time suggest extreme time pressure?**
   - Yes → `time_pressure` (may be combined with another cause as secondary context)

When a mistake fits more than one root cause, assign the most proximate cause — the one that, if corrected, would most directly have prevented this specific error.

---

## 1.3.  Severity

Root-cause severity uses the same share-based thresholds as the mistake category taxonomy:

| Share of total mistakes | Severity |
|---|---|
| > 0.40 | High |
| 0.20–0.40 | Medium |
| < 0.20 | Low |

Severity is **computed on write**, recomputed each time F09 updates the profile.

---

## 1.4.  Coaching implications

Each root cause maps to a different training intervention:

| Root cause | Coaching recommendation |
|---|---|
| `calculation_error` | Tactics training with forced lines; practice extending calculation one move further before deciding |
| `candidate_generation` | Positional pattern recognition; study quiet moves and prophylaxis; use the "what is my opponent's best reply?" question before every candidate |
| `visualization_failure` | Blindfold training; practice calculating longer forcing sequences without moving pieces; slow down on exchange sequences |
| `planning_error` | Study annotated master games for strategic decision-making; identify the position's key feature before calculating any move |
| `tactical_oversight` | Blunder-check discipline: always ask "can my opponent capture something or give check?" before playing a move |
| `assumption_bias` | Anti-pattern: pause before any "obvious" move and verify the opponent's options; study Zwischenzug and unexpected refusals to recapture |
| `time_pressure` | Time management training; practice making decisions faster in earlier phases to preserve clock time for critical moments |

---

## 1.5.  Root-cause motif vocabulary

When recording an example in the Player Profile, use one of these labels as the `root_cause` field:

`calculation_error`, `candidate_generation`, `visualization_failure`, `planning_error`, `tactical_oversight`, `assumption_bias`, `time_pressure`

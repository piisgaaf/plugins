# 1.  F08 — Classify My Mistakes

## 1.1.  User question
> "What kind of mistakes do I make?"
> "What went wrong in this game?"
> "Can you classify my mistakes?"
> "Do I have a pattern of errors?"

## 1.2.  Capability unlocked
The user submits a game and receives a classification of their mistakes by category (tactical, positional, opening, endgame), a summary of any emerging patterns, and a persistent update to their Player Profile. Over multiple games, the profile accumulates evidence that later features (F09–F13) can reason about.

## 1.3.  Validation
A correct implementation demonstrates:
- Mistakes are consistently assigned to the correct category using the taxonomy
- The Player Profile is correctly read before analysis and correctly updated after
- Running F08 on multiple games accumulates data additively — no prior data is lost
- Submitting the same game twice is detected and rejected before any analysis runs
- The output reads as coaching insight into the player's patterns, not an engine score report

---

## 1.4.  MCP tools used

F08 reuses the same tools as F05 when the evaluation pipeline must be run:

| Tool | When |
|---|---|
| `load_pgn` | Only if F05 has not already run in this session |
| `evaluate_move` | Only if F05 has not already run in this session |
| Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)); `fen_to_board` only as text fallback or to check a position yourself | For each mistake position shown to the user |
| `get_variation` | Optional — to confirm the better move's idea for a critical mistake |

**If F05 was already run in this session**, skip directly to Step 3 — the `score_loss` data per ply is already in context.

---

## 1.5.  Player Profile

### 1.5.1.  Location

The Player Profile is stored as `<name>.yaml` in the root of the working folder (the folder the user has mounted, e.g. the Cowork project folder). This is a plain YAML file the user can open, copy, and back up directly from their computer.

Which profile to use is resolved following the rule in [SKILL.md §1.7](../SKILL.md#17--player-profile): use the filename from the project instructions if specified, otherwise ask the user.

### 1.5.2.  Read rule

At the start of every F08 run, read the profile file. If it does not exist, create it with the skeleton from section 1.5.3. Never start with an empty profile — always read first to avoid overwriting prior data.

### 1.5.3.  Profile skeleton (first run only)

```yaml
# Personal Chess Coach — Player Profile
# Created: <ISO date of first F08 run>
# Last updated: <ISO date>

player:
  name: ""                  # fill in from game headers or ask the user

mistake_summary:
  games_analyzed: 0
  total_mistakes: 0
  total_inaccuracies: 0

mistake_categories:
  tactical:
    count: 0
    share: 0.00
    severity: low
    examples: []
  positional:
    count: 0
    share: 0.00
    severity: low
    examples: []
  opening:
    count: 0
    share: 0.00
    severity: low
    examples: []
  endgame:
    count: 0
    share: 0.00
    severity: low
    examples: []

recurring_weaknesses: []

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

# Analyzed games registry — used for deduplication and example traceability
analyzed_games: []

# Monthly mistake statistics — used by F13 for improvement trends
# Key format: "YYYY-MM" (derived from game date, not analysis date)
monthly_stats: {}
```

Each entry in `analyzed_games` has this shape:

```yaml
analyzed_games:
  - id: "LC-2026-Justcheckn1-white"
    hash: "..."
    date: "2026-05-09"
    event: "Live Chess"
    opponent: "Justcheckn1"
    color: white
    result: "1/2-1/2"
    opening: "Queen's Gambit Accepted (D20)"
    time_control: blitz         # blitz | rapid | classical; omit for classical
    use_for: [improvement_trends, opening_repertoire]   # omit for classical (all features apply)
```

Classical games omit both `time_control` and `use_for` (absence = all features apply).

**ID generation rule:** `<Event abbreviation>-<Year>-<Round if present, else opponent slug>-<color>`. Keep it short and human-readable. Examples: `SGS-2026-R3-white`, `OKH-2024-R7-black`, `SGS-2026-Chris-white`.

### 1.5.4.  monthly_stats schema

F08 maintains a `monthly_stats` map in the profile, keyed by `"YYYY-MM"`. Each bucket accumulates mistake counts for all games played in that calendar month. This data is consumed by F13 to compute improvement trends.

```yaml
monthly_stats:
  "2026-05":
    games: 4
    mistakes:
      tactical: 6
      positional: 3
      opening: 1
      endgame: 0
      total: 10
    shares:
      tactical: 0.60
      positional: 0.30
      opening: 0.10
      endgame: 0.00
  "2026-06":
    games: 7
    mistakes:
      tactical: 8
      positional: 5
      opening: 2
      endgame: 1
      total: 16
    shares:
      tactical: 0.50
      positional: 0.31
      opening: 0.13
      endgame: 0.06
```

**Blitz-only month:** when all games in a bucket are blitz, set `mistakes` and `shares` to `~` and add a `time_control` field:

```yaml
monthly_stats:
  "2026-05":
    games: 3
    time_control: blitz         # present when all games in bucket are blitz
    mistakes: ~                 # not classified for blitz
    shares: ~
```

**Mixed month (blitz + classical):** track only classical games' mistake counts; note how many blitz games were excluded:

```yaml
monthly_stats:
  "2026-06":
    games: 5                    # total games played
    classical_games: 3          # games used for mistake stats
    blitz_games: 2              # registered but not classified
    mistakes:
      tactical: 4
      positional: 2
      opening: 1
      endgame: 0
      total: 7
    shares:
      tactical: 0.57
      positional: 0.29
      opening: 0.14
      endgame: 0.00
```

**Month key derivation:** use the `[Date]` tag from the PGN headers (`YYYY.MM.DD` → `YYYY-MM`). If the PGN has no `[Date]` tag or the date is `????`, use today's date (the date F08 runs) as a fallback.

If `monthly_stats` is absent from the profile (older profiles), add it as an empty map and populate the current game's bucket.

### 1.5.5.  Write rule

After classification (Step 5), update the profile:
- Append a new entry to `analyzed_games` (hash + human-readable ID + metadata)
- Increment `games_analyzed`, `total_mistakes`, `total_inaccuracies`
- Increment each category's `count`
- Recompute each category's `share` = `count / total_mistakes` (0.00 if total_mistakes is 0)
- Recompute each category's `severity` using the [severity table](../codebook/mistake-taxonomy.md#12--severity)
- Append up to one new example per category from this game (most instructive mistake per category, by highest `score_loss`). Each example must include a `game` field referencing the human-readable ID of the game it came from. Keep a maximum of 3 examples per category — drop the oldest when a fourth arrives.
- Recompute `recurring_weaknesses`: list all categories with `severity` = high or medium, ordered by `share` descending.
- Update `monthly_stats`: derive the month key from the game date (see §1.5.4). Increment `games` by 1. For blitz games, increment `blitz_games` and leave `mistakes`/`shares` as `~`. For classical/rapid games, increment `classical_games` (if the bucket is mixed), increment each category's mistake count, increment `total`, and recompute `shares` (`category_count / total`, 0.00 if total is 0). Set `time_control: blitz` only when every game in the bucket is blitz.

Write the updated profile back to the profile file. This is a full overwrite — read the current content first (Step 1), merge in memory, then write.

**Example shape:**
```yaml
examples:
  - game: "OKH-2024-R7-black"
    move: "19...Rxf4+"
    motif: "overloaded_defender"
    note: "Rook sacrifice released tension; 19...e5 attacking Ne4 directly was correct"
```

Note: the `root_cause` field is added to examples by F09, not F08. F08 examples omit it; F09 enriches them in `root_cause_profile`.

---

## 1.6.  Workflow

### 1.6.1.  Step 1 — Resolve and read the Player Profile

Resolve which profile to use following the rule in [SKILL.md §1.7](../SKILL.md#17--player-profile): use the filename specified in the project instructions, or ask the user if not specified (listing any `*.yaml` files already in the project root as options).

Read the resolved profile file. Hold the current values in context throughout the session — they are needed for the additive update in Step 6.

If the file does not exist yet (new player), create it with the skeleton from section 1.5.3 and proceed.

If the `player.name` field is empty and it cannot be inferred from PGN headers, ask the user for their name before proceeding.

### 1.6.2.  Step 2 — Deduplicate

Compute the PGN hash by running:

```bash
python3 <project_root>/chess_engine/priv/personal-chess-coach/scripts/pgn_hash.py -p "<raw PGN text>"
```

Or, if the PGN was saved to a file:

```bash
python3 <project_root>/chess_engine/priv/personal-chess-coach/scripts/pgn_hash.py -f <path_to_pgn>
```

Compare the resulting hash against every `hash` field in `analyzed_games`.

**If a match is found:** stop immediately. Tell the user which game was already analyzed (show the matching entry's `id`, `date`, `opponent`, and `result`), and do not proceed further. Example message:

> This game was already analyzed (SGS-2026-R3-white, 2026-07-08 vs Mark de G, ½–½). No changes were made to your profile. If you want to re-analyze it, remove the entry from `analyzed_games` in your profile first.

**If no match is found:** continue to the time-control check.

**Time-control check:** Read the `[TimeControl]` tag from the PGN. Parse the base time in seconds (format is typically `600+0` or `300+3` — use the base number before `+`). Classify:
- ≤ 600 s → **blitz**
- 601–2999 s → **rapid**
- ≥ 3000 s → **classical**
- Tag absent or unparseable → treat as classical

**If the game is blitz:** stop and inform the user:

> This is a blitz game (10 min or less). Blitz games are registered for deduplication, opening repertoire, and improvement trends, but are not used for mistake classification.

Append an entry to `analyzed_games` with `time_control: blitz` and `use_for: [improvement_trends, opening_repertoire]` (see §1.5.3 for the full shape), then stop. Do **not** proceed to engine evaluation or mistake classification.

**If the game is rapid or classical:** continue to Step 3.

### 1.6.3.  Step 3 — Run the evaluation pipeline (if not already done)

**If F05 has already run in this session**, the ply list and per-ply `score_loss` values are already in context. Skip to Step 4.

**Otherwise**, run the F05 evaluation pipeline:
1. Call `load_pgn` with the raw game text. Capture `tags`, `starting_fen`, `plies`, `final_fen`.
2. For each ply from roughly move 8 onward, call `evaluate_move` using that ply's `fen_before` and `san`. Capture `score_loss`, `best_move`, and `is_best_move`.
3. Deliver the F05 game analysis output to the user (opening, critical moments, game summary) — see [F05](../r01-understand-my-chess/f05-analyze-my-games.md) for the full output format.

The F05 output is always delivered before the F08 classification — the user sees the game narrative first, then the mistake pattern summary.

### 1.6.4.  Step 4 — Identify mistakes and inaccuracies

From the per-ply `score_loss` values:
- **Mistakes and blunders**: `score_loss` ≥ 100 — these are classified by category
- **Inaccuracies**: `score_loss` 30–99 — counted in total but not classified by category

### 1.6.5.  Step 5 — Classify each mistake

For each mistake (`score_loss` ≥ 100), assign a category using the [mistake taxonomy](../codebook/mistake-taxonomy.md). For each classified mistake, also assign a motif label from the [motif vocabulary](../codebook/mistake-taxonomy.md#13--motif-vocabulary).

Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)) for the `fen_before` of each mistake position shown to the user, and use `fen_to_board` to ground the classification in the concrete position. Optionally call `get_variation` if the better move's idea is not immediately clear from chess knowledge.

Apply the [classification rules](../codebook/mistake-taxonomy.md#111--classification-rules): one primary category per mistake, phase takes priority.

### 1.6.6.  Step 6 — Update the Player Profile

Apply the write rule from section 1.5.4. Write the updated profile file.

### 1.6.7.  Step 7 — Deliver the mistake classification

After the F05 game analysis, append a coaching section:

```
## Mistake classification

**Games analyzed so far: [N]**

| Category | This game | Total | Share | Severity |
|---|---|---|---|---|
| Tactical | [N] | [N] | [X%] | [High/Medium/Low] |
| Positional | [N] | [N] | [X%] | [High/Medium/Low] |
| Opening | [N] | [N] | [X%] | [High/Medium/Low] |
| Endgame | [N] | [N] | [X%] | [High/Medium/Low] |

[If recurring_weaknesses is non-empty:]
**Recurring weaknesses:** [list categories with severity High or Medium]

[2–4 sentences of coaching insight: what the pattern suggests about the player's game,
and what kind of study would address the dominant weakness. Ground this in the
specific mistakes from this game — not generic advice.]
```

Do not surface raw `score_loss` values or centipawn numbers. Reference specific moves from the game by move number and piece/square when illustrating a pattern.

### 1.6.8.  Step 8 — Offer next steps

End with a targeted offer based on the dominant weakness category:
- Tactical weakness → "Want me to explain why you missed the tactic on move [N]?" → triggers F02
- Positional weakness → "Shall I go deeper on the positional decision at move [N]?" → triggers F02
- Opening weakness → "Want to understand what the opening called for instead?" → triggers F04

---

## 1.7.  Quality checklist

Before delivering output, verify:

- [ ] Player Profile was read before analysis — no prior data was discarded
- [ ] PGN hash was computed and checked against `analyzed_games` before any engine calls
- [ ] `[TimeControl]` tag was read and game was classified as blitz / rapid / classical; blitz games were registered but not sent to the engine
- [ ] Blitz games have `time_control: blitz` and `use_for: [improvement_trends, opening_repertoire]` in their `analyzed_games` entry; classical games omit both fields
- [ ] Every classified mistake has a `score_loss` ≥ 100 supporting it — nothing invented
- [ ] Each mistake has exactly one category and one motif label
- [ ] Each example in the profile includes a `game` field with the human-readable game ID
- [ ] Phase priority was respected in classification (Opening/Endgame take precedence)
- [ ] A new entry was appended to `analyzed_games` with hash, ID, and game metadata
- [ ] Profile `share` and `severity` values were recomputed, not carried over from the previous version
- [ ] `monthly_stats` bucket was updated: game count incremented; blitz games excluded from mistake counts; mixed-month fields (`classical_games`, `blitz_games`) added where applicable
- [ ] Month key was derived from the PGN `[Date]` tag, with today's date as fallback
- [ ] No raw centipawn scores appear in the output
- [ ] The coaching insight names specific moves, not generic patterns only

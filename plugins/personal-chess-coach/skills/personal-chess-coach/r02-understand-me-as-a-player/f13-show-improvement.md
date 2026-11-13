# 1.  F13 — Show How I'm Improving

## 1.1.  User question
> "Am I improving?"
> "Are my weaknesses getting better?"
> "Show me my progress."
> "How have my mistakes changed over time?"
> "Show me the last 3 months."
> "Show me all time."

## 1.2.  Capability unlocked
The coach shows whether the player's weakness categories are improving, stable, or worsening over time, using the `monthly_stats` section of the Player Profile. The player sees a trend table per category, can choose their analysis window, and always sees a reliability note showing how many months and games the trend covers.

## 1.3.  Validation
A correct implementation demonstrates:
- Trends are derived from `monthly_stats`, not recomputed from `analyzed_games`
- The number of months and games covered is always shown
- The default window is the last 6 months; the user can override this
- Output is still delivered with 1 month of data (minimum); reliability note reflects low data
- Trend direction is derived from comparing the first and last portions of the window
- No new engine calls are made

---

## 1.4.  MCP tools used

F13 requires no engine calls. All data comes from `monthly_stats` in the Player Profile.

---

## 1.4.1.  Blitz game handling

Blitz games (identified by `time_control: blitz` in their `analyzed_games` entry) contribute to the game-count and win/draw-rate trends shown in the improvement report, but their months are excluded from mistake-share trend computation.

- When reading `monthly_stats`, include blitz-only months (`mistakes: ~`) in the games-played total so the activity picture is accurate, but **skip them** when computing mistake-share averages and trend directions.
- For mixed months, use `classical_games` as the denominator for share computation, and note how many blitz games were excluded in the month row.
- The coaching narrative should distinguish between "games played" (all time controls) and "games classified" (classical/rapid only) when both figures are relevant.

---

## 1.5.  Window selection

### 1.5.1.  Default

The default window is the **last 6 calendar months** of data present in `monthly_stats` (the 6 most recent keys when sorted chronologically). If fewer than 6 months exist, use all available months.

### 1.5.2.  User override

Accept natural-language window requests:

| User says | Interpretation |
|---|---|
| "last 3 months" | Last 3 months in `monthly_stats` |
| "last year" | Last 12 months |
| "all time" | All months in `monthly_stats` |
| "since January" | All months from `YYYY-01` onward (use current year unless user specifies) |
| A specific range, e.g. "2025-10 to 2026-03" | Those months inclusive |

If the requested window exceeds available data, use all available months and note this.

### 1.5.3.  Asking the user

When the user asks for trends without specifying a window, proceed with the 6-month default and offer at the end: *"This covers the last [N] months. Want to see a different window?"*

---

## 1.6.  Minimum data requirement

F13 always delivers output. The reliability note informs the user how much data backs the trend:

| Months in window | Behavior |
|---|---|
| 1 | Show data. Note: *"Only 1 month of data — no trend can be computed yet. Keep analyzing games."* Show the single month as a baseline. |
| 2–3 | Show trend with note: *"Based on [N] months ([M] games) — trend direction is tentative."* |
| ≥ 4 | Show trend with standard note: *"Based on [N] months ([M] games)."* |

---

## 1.7.  Trend computation

### 1.7.1.  Data preparation

Collect all `monthly_stats` entries within the selected window, sorted chronologically. For each month, read:
- `games` — total games played in that month (all time controls)
- `classical_games` — if present (mixed month); use as the game count for mistake stats
- `blitz_games` — if present (mixed month); include in total but exclude from mistake computation
- `time_control: blitz` — if present (blitz-only month): include in games total but skip for mistake-share averages
- `mistakes.tactical`, `mistakes.positional`, `mistakes.opening`, `mistakes.endgame`, `mistakes.total` — skip if `~`
- `shares.tactical`, `shares.positional`, `shares.opening`, `shares.endgame` — skip if `~`

### 1.7.2.  Trend direction

For windows of ≥ 2 months, compute the trend direction for each category by comparing the **first half** of the window against the **second half** (split evenly; for odd counts the middle month is excluded):

- Compute the average share for the first half and for the second half
- Direction:
  - **Improving** (↓) — second-half average share is more than 5 percentage points lower than first-half
  - **Worsening** (↑) — second-half average share is more than 5 percentage points higher
  - **Stable** (→) — difference is within 5 percentage points

For windows of 1 month, show `—` for trend direction.

### 1.7.3.  Rolling view

When the window contains ≥ 3 months, show a month-by-month share table (see §1.8 output format) so the player can see the shape of the trend, not just the direction.

---

## 1.8.  Workflow

### 1.8.1.  Step 1 — Read the Player Profile

Without a working folder ([SKILL.md §1.7.3](../SKILL.md#173--without-a-working-folder)), do not run this feature: say in one line that it needs a saved player profile (Cowork with a project folder), and offer to analyze or classify a game instead. Otherwise read the profile following the rule in [SKILL.md §1.7](../SKILL.md#17--player-profile). If `monthly_stats` is absent or empty, tell the user:

> *"No monthly data is available yet. Analyze at least one game with F08 first."*

And stop.

### 1.8.2.  Step 2 — Determine the window

Apply the window selection rules from §1.5. Identify the months in scope. Compute total games in the window.

### 1.8.3.  Step 3 — Compute trends

Apply the trend computation from §1.7. For each category, determine direction and collect the per-month share series.

### 1.8.4.  Step 4 — Deliver the improvement report

```
## How You're Improving

*Based on [N] months of data ([M] games), [start month] – [end month].*
[If N < 4: include appropriate reliability note from §1.6]

**Trend summary**

| Category | [N] months ago | Recent | Trend |
|---|---|---|---|
| Tactical | 58% | 42% | ↓ Improving |
| Positional | 27% | 31% | ↑ Worsening |
| Opening | 10% | 8% | → Stable |
| Endgame | 5% | 4% | → Stable |

[If window ≥ 3 months, show month-by-month table:]

**Month-by-month breakdown**

| Month | Games | Tactical | Positional | Opening | Endgame |
|---|---|---|---|---|---|
| 2026-01 | 5 | 60% | 25% | 10% | 5% |
| 2026-02 | 4 | 55% | 28% | 12% | 5% |
| 2026-03 | 6 | 48% | 30% | 14% | 8% |
| 2026-04 | 3 | 50% | 32% | 10% | 8% |
| 2026-05 | 5 | 44% | 31% | 17% | 8% |
| 2026-06 | 7 | 42% | 31% | 19% | 8% |

**What the trend means**

[2–3 sentences coaching narrative. Name the improving category and what might
be driving it. Name the worsening category and what may need attention.
Ground it in the player's profile context — e.g. "Your tactical vigilance is
clearly improving, consistent with the knight fork puzzles you've been working on.
Positional mistakes are creeping up slightly — this is common when tactical
awareness grows faster than positional evaluation skills."]
```

Do not expose raw counts. Show shares as percentages. Use month labels (`2026-01`) not dates.

### 1.8.5.  Step 5 — Offer next steps

After the report, offer:
- "Want to see your recurring weaknesses in more detail?" → triggers F12
- "Want to focus on [worsening category] — shall I show what's going wrong there?" → triggers F09 or F08 on the worsening category
- "Want to see a different time window?" → re-run with a user-specified window

---

## 1.9.  Quality checklist

Before delivering output, verify:

- [ ] Player Profile was read; `monthly_stats` contains data before proceeding
- [ ] Window was determined correctly (default 6 months or user override)
- [ ] Total months and games in the window are stated at the top
- [ ] Reliability note matches the month count (§1.6)
- [ ] Blitz-only months were included in game totals but excluded from mistake-share averages and trend direction computation
- [ ] Mixed months used `classical_games` as the mistake-stat denominator and noted blitz exclusions
- [ ] Trend direction was computed by comparing first-half vs second-half average shares
- [ ] 5 percentage point threshold was applied for Improving / Worsening / Stable
- [ ] Month-by-month table shown when window ≥ 3 months
- [ ] Coaching narrative names specific categories and is grounded in the player's profile
- [ ] No raw counts or centipawn scores appear in the output
- [ ] Next steps are offered, including option to change the window

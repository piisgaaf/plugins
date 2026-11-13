# 1.  F12 — Show My Recurring Weaknesses

## 1.1.  User question
> "What are my recurring weaknesses?"
> "What do I keep getting wrong?"
> "What's my biggest weakness?"
> "Show me my mistake patterns."
> "Which weaknesses come up most often?"

## 1.2.  Capability unlocked
The coach presents a ranked summary of the player's most persistent weakness categories, drawn entirely from the accumulated Player Profile. The player sees which categories dominate across all analyzed games, with supporting examples and severity labels. A reliability note signals how much data backs the analysis.

## 1.3.  Validation
A correct implementation demonstrates:
- Weaknesses are ranked by share (descending), not by count alone
- Severity labels are read from the profile, not recomputed from scratch
- At least one concrete example per weakness is shown (from `mistake_categories[category].examples`)
- A data quality note ("Based on N analyzed games") always appears
- A warning is shown — but the output is still delivered — when `games_analyzed < 20`
- No new engine calls are made

---

## 1.4.  MCP tools used

F12 requires no engine calls. All data comes from the Player Profile.

| Tool | When |
|---|---|
| Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)); `fen_to_board` only as text fallback or to check a position yourself | Optional — only if the user requests a board diagram for a specific example position |

---

## 1.5.  Minimum data requirement

F12 always delivers output, regardless of game count. The reliability note informs the user how much evidence backs the analysis:

| `games_analyzed` | Behavior |
|---|---|
| < 5 | Show output with a prominent warning: *"Only N games analyzed — patterns may not yet be reliable."* |
| 5–19 | Show output with a note: *"Based on N games — more games will sharpen these patterns."* |
| ≥ 20 | Show output with standard note: *"Based on N analyzed games."* |

---

## 1.6.  Workflow

### 1.6.1.  Step 1 — Read the Player Profile

Without a working folder ([SKILL.md §1.7.3](../SKILL.md#173--without-a-working-folder)), do not run this feature: say in one line that it needs a saved player profile (Cowork with a project folder), and offer to analyze or classify a game instead. Otherwise read the profile following the rule in [SKILL.md §1.7](../SKILL.md#17--player-profile). If `mistake_categories` is absent or all counts are zero, tell the user:

> *"No mistakes have been classified yet. Analyze a game with F08 first."*

And stop.

### 1.6.2.  Step 2 — Rank the weaknesses

From `mistake_categories`, collect all categories where `count > 0`. Sort by `share` descending. This is the ranked weakness list.

Also read `recurring_weaknesses` (the pre-computed list of high/medium severity categories). Use this to determine which weaknesses to flag as significant.

From `root_cause_profile`, identify the top 1–2 root causes by share. These enrich the coaching narrative.

### 1.6.3.  Step 3 — Deliver the weakness report

```
## Your Recurring Weaknesses

*Based on [N] analyzed games.*
[If N < 20: include appropriate reliability note from §1.5]

| Rank | Category | Share | Severity | Most Common Motif |
|---|---|---|---|---|
| 1 | Tactical | 58% | High | overloaded_defender |
| 2 | Positional | 27% | Medium | weak_square |
| 3 | Opening | 10% | Low | — |
| 4 | Endgame | 5% | Low | — |

**Dominant pattern**

[2–3 sentences naming the top weakness category and what it costs the player.
Reference the top root cause(s) from root_cause_profile. Ground this in the
example motifs — e.g. "Your tactical mistakes are most often overloaded defenders
and knight forks — patterns where one piece is doing too much defensive work."]

**Most instructive example**

[Show the single most instructive example from the top weakness category.
Format: Move [N], [game ID], [brief explanation of what went wrong and why.]]

[If a second weakness has severity High or Medium, show its most instructive example too.]

**What to work on**

[1–2 sentences of concrete study advice directly tied to the dominant weakness.
E.g. "Solving puzzles that feature overloaded pieces will sharpen the pattern
recognition you need here." Do not give generic advice.]
```

Do not expose raw counts or centipawn values. Refer to shares as percentages. Show motif labels only where they are populated in the examples.

### 1.6.4.  Step 4 — Offer next steps

After the report, offer:
- "Want to understand *why* you keep making these mistakes?" → triggers F09 on a specific example
- "Want to see whether these weaknesses are improving over time?" → triggers F13
- "Want a training plan targeting your biggest weakness?" → cross-reference weakness with F11 style archetype

---

## 1.7.  Quality checklist

Before delivering output, verify:

- [ ] Player Profile was read; `mistake_categories` contains data before proceeding
- [ ] Weaknesses are ranked by `share`, not raw count
- [ ] Severity labels are read from the profile — not recomputed
- [ ] A reliability note with game count is always present
- [ ] At least one concrete example is shown for the top weakness
- [ ] Root cause(s) from `root_cause_profile` are referenced in the narrative
- [ ] No raw centipawn scores or engine output appear
- [ ] Coaching advice is specific to the dominant weakness, not generic
- [ ] Next steps are offered

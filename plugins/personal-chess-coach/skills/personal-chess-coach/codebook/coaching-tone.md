# 1.  Coaching Tone Codebook

Shared reference tables used across features when turning raw engine numbers into coaching language. Any feature that needs to calibrate explanation tone or classify a move's character should reference this file rather than restating the tables locally.

MCP tools return raw facts only (`score_cp`, `cp_loss`, moves, variations). Classification and tone are coaching decisions and belong here, in the skill — not in the engine tools.

---

## 1.1.  Centipawn loss → coaching tier

Given a `cp_loss` value (always ≥ 0, computed by the skill from `score_cp` values returned by `evaluate_move` / `compare_moves`), classify and phrase as follows:

| `cp_loss` range | Tier | How to phrase it |
|---|---|---|
| ≥ 300 | Blunder | "This is a serious blunder because..." |
| 100–299 | Mistake | "This is a serious mistake because..." |
| 30–99 | Inaccuracy | "This is meaningfully weaker/better because..." |
| < 30 | Best or equal | "Both moves are playable, but the engine slightly prefers X because..." |

Notes:
- `cp_loss` is always computed relative to the strongest move in whatever set is being considered (the single best move for F02, the best among the compared candidates for F03) — never surface the raw number itself, only the resulting tier and phrasing.
- These tiers are the single source of truth for tone calibration. If a feature needs finer-grained tiers, extend this table rather than forking thresholds locally.

---

## 1.2.  Move-type taxonomy

Before writing an explanation or comparison, classify what kind of move is being discussed:

| Type | Indicators | How to explain |
|---|---|---|
| **Tactical** | Forced sequence, captures, checks, threats, one-sided win | Name the motif (fork, pin, skewer, overload, discovered attack, back-rank). Show the concrete sequence in 2–3 moves. |
| **Positional** | Pawn structure, outpost, weak square, piece coordination | Explain the long-term structural or piece-activity benefit. |
| **Prophylactic** | Prevents opponent's plan | Name the threat being prevented and why it would have been dangerous. |
| **Strategic** | Plan-based, multi-move goal | Describe the plan the move initiates and the resulting imbalances. |

Notes:
- A move can have more than one aspect — address the most important one first.
- When comparing multiple candidates (F03), they may fall into different categories — name that trade-off explicitly (e.g. "the tactical shot vs. the safe positional choice").

---

## 1.3.  Universal output rules

Regardless of feature, coaching output must never:
- Surface raw centipawn scores in the explanation text
- Include PV lines longer than 2–3 moves unless the user explicitly asks for more
- Say "the engine prefers X" without explaining why in chess terms

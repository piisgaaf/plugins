# 1.  F04 — Understand Opening Positions

## 1.1.  User question
> "What opening is this?"
> "What's the idea behind the Grünfeld?"
> "What should both sides be aiming for here?"
> "What do people usually play here?"

## 1.2.  Capability unlocked
The user can ask about an opening position — by FEN, move sequence, or name — and receive the opening's identity, the strategic plans typical for both sides, and the continuations players actually choose at their level, rather than a raw evaluation of a single position.

## 1.3.  Validation
A correct implementation demonstrates:
- Correct opening identification (name and ECO code) on well-known openings
- Typical plans described for **both** sides, not just the side to move
- Continuations reflect real practice (frequency data), not just engine preference, when that data is available
- Graceful behavior when continuation data is unavailable — the response still delivers value from chess knowledge alone

---

## 1.4.  MCP tools used

| Tool | When |
|---|---|
| `validate_fen` | Always — before any analysis |
| Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)); `fen_to_board` only as text fallback or to check a position yourself | Always — show the board before discussing it |
| `identify_opening` | Always — get the opening name and ECO code from the FEN or move sequence |
| `get_opening_continuations` | Always — get frequency-ranked continuations for the position at a relevant rating band, when the opening was identified |

`get_opening_continuations` calls an external data source (Lichess Opening Explorer) and can fail or be unavailable (auth, rate limit, network). Treat its absence as expected, not exceptional — see Step 5.

There is no tool for opening **plans**. Plans, ideas, and typical structures are composed from chess knowledge, the same way F01 handles opening context — this is sufficient for mainstream openings at the target player level (1800–2000) and keeps this feature decoupled from any single data source.

---

## 1.5.  Workflow

### 1.5.1.  Step 1 — Accept input

Accept any of:
- A raw FEN string
- A move sequence in natural language or SAN/PGN (e.g. "1.d4 Nf6 2.c4 g6")
- An opening named directly (e.g. "the Grünfeld", "the Berlin") — if no position is given, use the main-line FEN for that opening from your own knowledge

If the input is a move sequence, derive the FEN before proceeding.

### 1.5.2.  Step 2 — Validate

Call `validate_fen`. If invalid, report the error clearly and ask the user to correct it. Do not proceed with an invalid FEN.

### 1.5.3.  Step 3 — Render the board

Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)) before discussing the opening.

### 1.5.4.  Step 4 — Identify the opening

Call `identify_opening` with the FEN or move list. Capture the ECO code, name, and the move sequence it resolved against.

If not found (position too deep, or off the beaten path), say so plainly and fall back to describing the position in general terms — do not invent an opening name.

### 1.5.5.  Step 5 — Get typical continuations (conditional on Step 4 succeeding)

Call `get_opening_continuations` on the same FEN/moves, using a rating band appropriate to the player (default to a club-level band, roughly 1800–2000, unless a player profile already read in this conversation indicates otherwise; never resolve a profile just for this).

If the call succeeds, capture the top 3–5 continuations with their frequency and score tendencies (win/draw/loss), for use in Step 7. Do not surface raw frequency percentages or rating numbers as the headline of the explanation — use them to support statements like "most club players continue with..." or "this is by far the most common choice at this level."

If the call fails or returns no data (network issue, auth issue, rate limit, or position not covered), do not block or apologize at length — proceed with continuations drawn from your own opening knowledge, and simply omit frequency-specific claims. The user should not notice a degraded experience, only a slightly less data-backed one.

### 1.5.6.  Step 6 — Compose the plans (from chess knowledge, not a tool)

Using your own knowledge of the opening, determine:
- The strategic goals for **White** in this line
- The strategic goals for **Black** in this line
- The key pawn breaks, piece manoeuvres, or structural imbalances that define the variation
- What the specific variation (not just the opening family) implies, if the position is beyond the main tabiya

### 1.5.7.  Step 7 — Compose the coaching explanation

```
## [Opening name] ([ECO code])

[Board diagram from Step 3]

### What both sides are trying to do
**White:** [2–3 sentences on White's strategic plan in this line]
**Black:** [2–3 sentences on Black's strategic plan in this line]

### Typical continuations
[If continuation data available: 2–4 bullet-free sentences naming the most commonly played replies and what distinguishes them in character (sharp/quiet, main line/sideline), grounded in "commonly played" rather than raw stats.]
[If unavailable: describe the standard theoretical continuation(s) from chess knowledge, without claiming frequency data.]

### Key ideas to remember
[1–2 sentences capturing the defining imbalance or idea of this opening — the thing a player should retain even if they forget the moves]
```

Do **not** include:
- Raw frequency percentages, rating numbers, or engine centipawn scores in the explanation text
- Long PV lines or move lists beyond what's needed to illustrate a continuation
- Phrases like "the database shows" or "the API returned" — speak as a coach, not a data pipe

### 1.5.8.  Step 8 — Offer next steps

End with a targeted offer:
- "Want me to analyze a specific continuation from here?" → triggers F01
- "Shall I compare two of these typical replies?" → triggers F03
- "Want to see why one particular line is currently considered best?" → triggers F02
- "Save to your notebook?" → triggers [F36](f36-opening-notebook.md) (see its §1.6 for when to ask; only with a working folder, [SKILL.md §1.7.1](../SKILL.md#171--working-folder-decide-once-per-conversation))

---

## 1.6.  Explanation quality checklist

Before delivering the explanation, verify:

- [ ] Opening name and ECO code are correct (or absence is stated plainly, not guessed)
- [ ] Plans are given for **both** sides, not just one
- [ ] Continuations reflect actual practice when data was available, and are clearly knowledge-based (not fabricated as data-backed) when it wasn't
- [ ] No raw frequency percentages, ratings, or centipawn scores appear in the text
- [ ] The response reads the same whether or not `get_opening_continuations` succeeded — no visible degradation, no apology for a tool failure
- [ ] The "Key ideas" section is memorable and specific to this opening, not generic

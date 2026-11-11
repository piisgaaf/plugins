# 1.  Mistake Taxonomy

Shared reference for classifying chess mistakes by category. Used by F08 and any later feature that reasons about the player's error patterns.

A mistake is any move with `score_loss` ≥ 100 (Mistake or Blunder tier per the [centipawn loss → coaching tier table](coaching-tone.md#11--centipawn-loss--coaching-tier)). Inaccuracies (`score_loss` 30–99) are tracked separately and not classified by category unless a later feature requires it.

---

## 1.1.  Categories

| Category | When to assign | Typical indicators |
|---|---|---|
| **Tactical** | The better move wins material or delivers a decisive threat through a concrete forcing sequence | Missed fork, pin, skewer, discovered attack, back-rank weakness, overloaded defender, zwischenzug |
| **Positional** | The better move improves piece activity, pawn structure, or control of key squares without an immediate forcing sequence | Weak square neglect, bad piece placement, premature exchange, failure to restrict opponent's piece |
| **Opening** | The mistake occurs in the opening phase (roughly moves 1–15) and violates a known opening principle or exits a known good line into a worse structure | Loss of tempo, early queen excursion, ignoring development, weakening king-side without compensation |
| **Endgame** | The mistake occurs when queens are off the board and material is reduced, and involves endgame-specific technique | King activation failure, wrong pawn advance, opposition neglect, rook cut-off |

### 1.1.1.  Classification rules

- Assign **one primary category** per mistake. If a move is both a tactical oversight and a positional concession, assign the category of the more direct cause of the evaluation swing.
- **Opening** and **Endgame** take priority over Tactical/Positional when the phase criterion is met — phase context is the more specific signal.
- When classification is genuinely ambiguous, prefer **Tactical** over Positional, since tactical errors tend to be more concrete and actionable to study.

---

## 1.2.  Severity

Severity for a category is derived from its share of total mistakes across all analyzed games:

| Share of total mistakes | Severity |
|---|---|
| > 0.40 | High |
| 0.20–0.40 | Medium |
| < 0.20 | Low |

Severity is **computed on write**, not stored as a free-form label. Recompute it each time F08 updates the profile.

---

## 1.3.  Motif vocabulary

When recording an example in the Player Profile, use a consistent motif label from this list. Add new labels as needed, but prefer existing ones for consistency across games.

**Tactical motifs**
`knight_fork`, `pawn_fork`, `pin`, `skewer`, `discovered_attack`, `back_rank`, `overloaded_defender`, `zwischenzug`, `deflection`, `decoy`, `remove_the_guard`, `perpetual_missed`, `stalemate_missed`

**Positional motifs**
`weak_square_neglect`, `bad_piece_placement`, `premature_exchange`, `failure_to_restrict`, `pawn_structure_damage`, `open_file_neglect`, `bishop_pair_surrendered`

**Opening motifs**
`development_neglect`, `early_queen_excursion`, `tempo_loss`, `king_safety_weakened`, `theory_deviation`

**Endgame motifs**
`king_activation_failure`, `wrong_pawn_advance`, `opposition_neglect`, `rook_cutoff`, `pawn_promotion_missed`

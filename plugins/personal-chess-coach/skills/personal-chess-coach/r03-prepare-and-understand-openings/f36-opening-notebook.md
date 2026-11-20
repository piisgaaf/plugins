# 1.  F36 — Build My Opening Notebook

## 1.1.  User question

> "Add this to my opening notebook."
> "Add the Caro-Kann Advance to my notebook — I play it as Black."
> "Start the card from here."
> "Make this key position its own card."
> (or: "yes" to the coach's offer "Add this to your opening notebook?" after F01, F04, F05 or F07)

## 1.2.  Capability unlocked

The user builds a library of the openings in their repertoire as **idea cards**: concepts, not theory. A card starts from a **position**: the end of the main line or of an important variation, where the plans are set. It holds the pawn structure, the plans for both sides, where the pieces belong, the pawn breaks, the traps and the typical mistakes, with a short "In short" list on top. The only moves in it are the line to the starting position and the key positions found while analysing.

Where the opponent's choice changes the plan, the line gets its own **branch card**, linked from the card it branches from. Positions that only deepen the same plan become key positions on the existing card. Cards are kept per side, in `Openings/White/` and `Openings/Black/`, and an overview table (Obsidian Bases) shows each repertoire with its branches.

## 1.3.  Validation

A correct implementation demonstrates:

- A new opening creates a card in the folder of the user's side, starting from the end of the main line or important variation (not simply the position analysed), with every section filled, its boards in `Openings/boards/` and the overview table (if missing)
- The card has no engine lines, evaluations or side lines; the only moves are the line to the starting position and the key positions
- A deeper position with the same plans becomes a key position on that card: ideas merged, "In short" rewritten, nothing removed
- A position where the opponent's choice changes the plan becomes a branch card, linked both ways with its parent
- The offer says where the card starts and whether it is a new card, a branch or a key position; the user can change that
- The same position reached through another move order lands on the same card
- The same opening played from both sides gives one card in `White/` and one in `Black/`, each written from that side
- "Make this key position its own card" turns a key position into a branch card
- Text the user wrote under "My notes" is never changed, and nothing is written without the user's yes

---

## 1.4.  Where the notebook lives

All paths are relative to the **working folder**: the folder the user mounted (the Cowork project folder, which the user points at their Obsidian vault or a subfolder of it).

```
Openings/
  Openings.base                                             ← overview table (created once)
  boards/
    2cba17e3.svg                                            ← board from White's side
    2cba17e3-black.svg                                      ← same position from Black's side
  White/
    Ruy Lopez, Closed (C84).md                              ← card, top level
  Black/
    Sicilian Defense, Najdorf Variation (B90).md            ← card, top level
    Sicilian Defense, Najdorf Variation (B90) 6.Be3 e5.md   ← branch card
```

The side folder (`White/` or `Black/`) is the side the user plays. An opening played from both sides has a card with the same name in each folder, so links between cards always include the side folder: `[[Black/Sicilian Defense, Najdorf Variation (B90)]]`. Obsidian resolves this partial path also when the working folder is a subfolder of the vault.

Boards are named by the script after the position itself (a hash of the first four FEN fields), never after the card. Names are therefore unique across all openings, the same position always uses the same file, and cards embed them by name alone (`![[2cba17e3.svg|400]]`).

Templates are in this skill's `templates/` folder: [opening.md](../templates/opening.md) and [Openings.base](../templates/Openings.base). Always build cards from these templates; do not invent another layout.

## 1.5.  MCP tools used

| Tool | When |
|---|---|
| `identify_opening` | Always — on the move list (or FEN) of the analysed position, to find the line, and on the starting position, for the card's opening name and ECO code |
| `apply_move` | To get the FENs along a line (starting position, transpositions), when they are not known yet |
| Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)) | Always — save the board of the starting position and of each new key position in `Openings/boards/`, from the user's side (show-board.md §1.5) |

No engine analysis: the card holds ideas, not lines or evaluations. Ideas come from what the conversation found plus chess knowledge, the same way F04 composes plans ([F04 Step 6](f04-understand-opening-positions.md#156--step-6--compose-the-plans-from-chess-knowledge-not-a-tool)).

---

## 1.6.  When to offer saving

The notebook needs a working folder ([SKILL.md §1.7.1](../SKILL.md#171--working-folder-decide-once-per-conversation)). Without one, never offer saving; if the user asks to save, say in one line that the notebook needs Cowork with a project folder ([SKILL.md §1.7.3](../SKILL.md#173--without-a-working-folder)), and write nothing.

Offer it with one short question, **"Add this to your opening notebook?"**:

- **After F01 or F04** about a position that comes from an opening (in the book or just past it, at any move number): the positions worth keeping are often just past the book. Not for a middlegame or endgame position without a link to an opening.
- **After F05 or F07**, for the game's opening, from the side the user played. F07 also asks "Save a record of this game?" ([F37](../r02-understand-me-as-a-player/f37-keep-game-records.md)): ask both in **one** question, e.g. *"Save a record of this game, and add the Najdorf's ideas to your opening notebook?"*, and do only what the user says yes to.

Rules:

- Ask once per opening per conversation. If the user declines, do not ask again for that opening.
- If the user says "add this to my notebook" (or similar), or names an opening to add, save without asking.
- Never save without the user's yes.

Before writing, say in one line what will happen, so the user can change it (Step 3 decides it):

> *New card for the Najdorf, starting after 6.Be3 e5.*
> *Key position 9.Qd2 Nbd7 10.f3 on your card "Najdorf 6.Be3 e5": same plans.*
> *New branch of "Najdorf 6.Be3 e5" after 7.Nf3: White's knight goes to f3 instead of b3, which changes Black's plan.*

If the user asks for another starting position ("start the card from here", "start after 6.Be3") or for a branch instead of a key position (or the other way round), follow that. When the user asked to save straight away, put this line in the confirmation (Step 6) instead.

---

## 1.7.  Workflow

### 1.7.1.  Step 1 — Collect the facts

Gather from the conversation (call a tool only if missing):

- **The analysed position:** its `fen` and the moves from move 1, if known. When the user only named an opening, the position at the end of its main line, from chess knowledge.
- **Opening** from `identify_opening` (with the move list if known, otherwise the FEN). If nothing was found, ask once: *"Which opening is this? Give the name or the moves that led here."*
  - Moves given → call `identify_opening` with them.
  - Only a name given → use that name, with ECO `—`, and the line from chess knowledge.
  - The user doesn't know or skips → do not save; say in one line that a card needs a named opening.
- **Repertoire side:** the side the user plays in this opening. From the conversation ("I play this as Black"), or after F05/F07 the side the user played (as F37 Step 1 finds it). Otherwise ask once: *"Do you play this opening as White or as Black?"* If the user plays it with both, use the side the conversation was about; ask when that is unclear.
- **The ideas** that came up in the conversation: plans for both sides, structure, piece placement, pawn breaks, tactics, the mistake that was made in the game.
- **Today's date** (`YYYY-MM-DD`; from the conversation context, or by running `date +%F`).

### 1.7.2.  Step 2 — Read the side folder

List the cards (tag `opening-card`) in `Openings/White/` or `Openings/Black/`, for the repertoire side only. For each, note its name, `moves`, `fen`, `positions` and `parent`. Cards of the other side are never used.

### 1.7.3.  Step 3 — Decide: key position, branch or new card

Compare FENs by their **first four fields** (pieces, side to move, castling, en passant) and ignore the move counters, so a position reached by another move order is the same position. Get the FENs along the analysed line with `apply_move` when needed.

1. **The analysed position is a card's `fen` or in its `positions`** → update that card (Step 5) with the new ideas.
2. **A card's starting position lies on the analysed line** (one of the FENs along it equals a card's `fen`; take the deepest such card) → decide from chess knowledge:
   - **Same plans:** the position deepens that card's plans (a natural continuation, a move-order detail, a typical moment in the middlegame that follows) → **key position** on that card (Step 5).
   - **The plans change:** after that card's starting position, the opponent made a choice that calls for a different plan (another set-up, another pawn structure, another side of the board) → **branch card** (Step 4), with that card as `parent`. Its starting position is where the new plans are set, usually a few plies after the opponent's choice, at the end of the important variation.
   - Only a choice of the **opponent** creates a branch; the user's own deviation from their repertoire is a key position (with the idea why it is worse or fine), unless the user asks for a branch.
3. **No card's starting position lies on the line** → **new top-level card** (Step 4). Its starting position is the end of the main line or important variation that the analysed position belongs to, where the plans are set; not the analysed position itself when that is deeper. If the analysed position is deeper, it also becomes the card's first key position.

If an existing top-level card's starting position lies on the line of a **new** top-level card (the new one starts earlier), make the new card and add the existing one to its "Branches" with `parent` set, rather than duplicating its ideas.

Tell the user what was decided (§1.6), then continue.

### 1.7.4.  Step 4 — Create a card

0. **Folders:** create `Openings/` and the side folder if they do not exist, with a command (`mkdir -p "<working folder>/Openings/Black"`), not by relying on the file tool to create parent folders. (`Openings/boards/` is created by the script.)
1. **Overview table:** if `Openings/Openings.base` does not exist, copy [templates/Openings.base](../templates/Openings.base) there unchanged.
2. **Opening and name:** call `identify_opening` on the line to the starting position. The name is `<opening name> (<ECO>)`, with `: ` replaced by `, `, followed by the moves of the line **after** the moves `identify_opening` returned, numbered (`6.Be3 e5`; start with `6...e5` when the first of them is Black's). Without an ECO code, leave out ` (<ECO>)`. Example: `Sicilian Defense: Najdorf Variation`, `B90`, line `… 5...a6 6.Be3 e5` → `Sicilian Defense, Najdorf Variation (B90) 6.Be3 e5`.
   - Remove characters that Obsidian forbids or that break links: `: * " \ / < > | ? # ^ [ ]`, and also `+` and `!`. Collapse double spaces.
   - If a card with another starting position already has this name in the side folder, append the next ply of the line, until the name is free.
3. **Boards:** save the board of the starting position, and of each key position, in `Openings/boards/` ([show-board.md §1.5](../rendering/show-board.md)), from the repertoire side: `--flip` for Black. Use the file names the script prints.
4. **Card:** create `Openings/<side folder>/<name>.md` from [templates/opening.md](../templates/opening.md). Fill **every** section for this starting position, from the conversation and from chess knowledge (as [F04 Step 6](f04-understand-opening-positions.md#156--step-6--compose-the-plans-from-chess-knowledge-not-a-tool)), so the card is useful from the start. "My plan" is the repertoire side's plan. Add the key position, if any, under "Key positions" and its FEN to `positions`. Leave "Branches" empty unless Step 3 linked an existing card. Write "In short" last. Leave "My notes" empty.
5. **Branch card only:** set `parent` and the "Branch of" line. A branch card holds what is **different** from its parent; it does not repeat the parent's ideas that still hold, but may say so in one bullet ("Black's …d5 break from the parent card still applies").
6. **Parent:** add a line to the parent's "Branches" section (`- 7.Nf3 → [[Black/<name>]]: …`) and set the parent's `updated` to today. Change nothing else in the parent.

What a card never holds: engine lines, evaluations or centipawn scores, side lines, move-order theory beyond the line to its starting position, or the moves of a whole game. Keep each bullet to one idea in one or two sentences. A move in a bullet only illustrates an idea ("the ...d5 break, prepared by ...Nbd7 and ...Qc7").

### 1.7.5.  Step 5 — Update a card

1. **Ideas:** add each new idea as a bullet to the section it belongs in. An idea already in the card is not added again; one that adds a detail to an existing bullet goes in a new bullet next to it. Never rewrite or remove an existing bullet. If a new idea contradicts one in the card, add it with the condition under which it holds, and mention it in the confirmation.
2. **Key position:** if the analysed position's FEN (first four fields) is not in `positions` or `fen` yet, save its board (Step 4.3), add a block under "Key positions" and append its FEN to `positions`. If it is already there, add only new ideas (item 1).
3. **In short:** rewrite it from the card's sections, 3–5 lines. It is the only text that is rewritten, and it never says something that is not in a section.
4. **Frontmatter:** set `updated` to today. Keep everything else.
5. **Boards:** run the script again for each board in the card. It writes the same file name for the same position, so this only repairs a missing file and never changes an embed.
6. **Never touch "My notes"**, and never delete a card, a section or a bullet.

### 1.7.6.  Step 6 — Confirm

Tell the user in one line what happened, with the path, e.g.:

> Saved to `Openings/Black/Sicilian Defense, Najdorf Variation (B90) 6.Be3 e5.md` (new card, starting after 6.Be3 e5).
> Updated `Openings/Black/Sicilian Defense, Najdorf Variation (B90) 6.Be3 e5.md`: new key position 9.Qd2 Nbd7 10.f3, two ideas added.
> Saved to `Openings/Black/Sicilian Defense, Najdorf Variation (B90) 6.Be3 e5 7.Nf3.md` (new branch, linked from its parent).

---

## 1.8.  Splitting a card

When the user asks to make a key position its own card ("make this its own card", "this needs its own plan"):

1. Create a branch card (Step 4) with the current card as `parent`, starting from that key position (or from where its plans are set, if the user agrees).
2. Copy the ideas that belong to the new line into it. Ideas in the parent stay where they are: never remove a bullet.
3. In the parent, keep the key position block and add a line to it: `Own card: [[<side folder>/<name>]]`. Keep its FEN in `positions`, so the position still finds the parent first; Step 3 then follows the link: a position that is in a key position with an "Own card" link is updated in that card.
4. Add the branch to the parent's "Branches".

---

## 1.9.  Quality checklist

- [ ] The user said yes (or asked to save) before anything was written, and was told where the card starts and whether it is a new card, a branch or a key position
- [ ] Only cards in the folder of the repertoire side were searched, by FEN (first four fields) along the analysed line
- [ ] A card starts where its plans are set (end of the main line or an important variation), not at an arbitrary deeper position
- [ ] A branch exists only where the opponent's choice changes the plan; it is linked both ways and does not repeat its parent
- [ ] The card follows the template; its name contains no forbidden characters; links between cards include the side folder
- [ ] "My plan" is written for the side the user plays
- [ ] No engine lines, evaluations or side lines
- [ ] Each board is from the repertoire side (`--flip` for Black), stored in `Openings/boards/` under the name the script printed
- [ ] Existing bullets are unchanged; only "In short" was rewritten
- [ ] "My notes" is untouched

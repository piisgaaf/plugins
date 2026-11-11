# 1.  F36 — Build My Opening Notebook

## 1.1.  User question

> "Save this to my notebook."
> (or: "yes" to the coach's offer "Save to your notebook?" after a plan question in an opening position)

## 1.2.  Capability unlocked

Every opening position the user studies can be saved as a note in their Obsidian vault: one note per position, grouped under one hub note per opening variation, with the plans discussed (each with a board seen from that side) and the engine line. Returning to the same position updates its note instead of creating a duplicate. An overview table (Obsidian Bases) lists every saved position by opening, ECO code and side to move.

## 1.3.  Validation

A correct implementation demonstrates:

- A new position creates its hub note (if missing), its position note, its board SVG in `Openings/boards/`, and the overview table (if missing)
- White's plan shows the board from White's side, Black's plan from Black's side
- A position beyond the opening book (e.g. move 17) still gets the offer; when the opening can't be identified, the coach asks for it once
- The same position, revisited for the other side's plan, updates the existing note — no duplicate
- The same position reached through a different move order is recognised as the same note
- A second position in the same variation gets its own note, linked from the existing hub
- Text the user wrote under "My notes" is never changed

---

## 1.4.  Where the notebook lives

All paths are relative to the **working folder**: the folder the user mounted (the Cowork project folder, which the user points at their Obsidian vault or a subfolder of it).

```
Openings/
  Openings.base                                   ← overview table (created once)
  boards/
    2cba17e3.svg                                  ← board from White's side
    2cba17e3-black.svg                            ← same position from Black's side
  Sicilian Defense, Najdorf Variation (B90).md    ← hub note, one per variation
  Sicilian Defense, Najdorf Variation (B90)/
    6.Be3 e5 7.Nb3.md                             ← position note
```

Boards are named by the script after the position itself (a hash of the first four FEN fields), never after the note. Names are therefore unique across all openings, the same position always uses the same file, and notes embed them by name alone (`![[2cba17e3.svg|400]]`).

Templates for all three files are in this skill's `templates/` folder: [opening-position.md](../templates/opening-position.md), [opening-hub.md](../templates/opening-hub.md), [Openings.base](../templates/Openings.base). Always build notes from these templates; do not invent another layout.

## 1.5.  MCP tools used

| Tool | When |
|---|---|
| `identify_opening` | Always — the opening name and ECO code key the hub note. Pass the move list when known (finds the deepest named variation), otherwise the FEN |
| `get_variation` | When the conversation produced no engine line yet — its numbered `line` goes into the note |
| Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)) | Always — save one board per discussed side in `Openings/boards/` (show-board.md §1.5) |

---

## 1.6.  When to offer saving

After answering about a specific position (F01, including a plan question per F01 §1.6, or F04), end with one short question: **"Save to your notebook?"** Ask this whether or not the position is in the opening book, and at any move number: the positions worth saving are often just past the book.

- Ask once per position. If the user declines, do not ask again for that position in this conversation.
- If the user says "save this" (or similar) at any time, save without asking.
- Never save without the user's yes.

---

## 1.7.  Workflow

### 1.7.1.  Step 1 — Collect the facts

Gather from the conversation (call the tool only if missing):

- `fen` of the position, and `side_to_move` (from the FEN)
- The move sequence from move 1, if known (numbered SAN, e.g. `1.e4 c5 2.Nf3 d6`)
- Opening `name` and `eco` from `identify_opening` (with the move list if known, otherwise the FEN). If nothing was found, ask once: *"Which opening is this? Give the name or the moves that led here."*
  - Moves given → call `identify_opening` with them (it finds the deepest named variation), and use them as the move sequence.
  - Only a name given → use that name, with ECO `—`.
  - The user doesn't know or skips → hub `Unclassified`, ECO `—`. The note can be moved later.
- The plan(s) discussed in this conversation, per side
- The engine line (`get_variation`'s numbered `line`)
- Today's date (`YYYY-MM-DD`; from the conversation context, or by running `date +%F`)

### 1.7.2.  Step 2 — Build the names

**Hub note name:** `<opening name> (<ECO>)`, with `: ` replaced by `, `. Example: `Sicilian Defense: Najdorf Variation` + `B90` → `Sicilian Defense, Najdorf Variation (B90)`.

**Position note name:** the last three plies of the move sequence, numbered: `6.Be3 e5 7.Nb3`. If the first of those plies is Black's, start with `6...e5 7.Nb3 Nc6`. If the move sequence is unknown, use `Move <fullmove number> (<side_to_move> to move)`.

**For both names**, remove characters that Obsidian forbids or that break links: `: * " \ / < > | ? # ^ [ ]`, and also `+` and `!`. Collapse double spaces.

### 1.7.3.  Step 3 — Find an existing note

Search `Openings/` (all subfolders) for a position note whose `fen` frontmatter has the **same first four FEN fields** (pieces, side to move, castling, en passant) as this position. Ignore the last two fields (move counters): the same position reached by another move order is the same note.

- **Found** → Step 5 (update). Use that note, even if its name or hub differs from what Step 2 produced.
- **Not found** → Step 4 (create). If a different position already uses the Step 2 name in this hub, append ` (2)`, ` (3)`, … until the name is free.

### 1.7.4.  Step 4 — Create

0. **Folders:** create `Openings/` and `Openings/<hub name>/` if they do not exist, with a command (`mkdir -p "<working folder>/Openings/<hub name>"`), not by relying on the file tool to create parent folders. Quote the path: hub names contain spaces. (`Openings/boards/` is created by the script.)
1. **Overview table:** if `Openings/Openings.base` does not exist, copy [templates/Openings.base](../templates/Openings.base) there unchanged.
2. **Hub note:** if `Openings/<hub name>.md` does not exist, create it from [templates/opening-hub.md](../templates/opening-hub.md).
3. **Boards:** for each side whose plan was discussed, save its board in `Openings/boards/` ([show-board.md §1.5](../rendering/show-board.md)): White's plan without `--flip`, Black's plan with `--flip`. Use the file name the script prints.
4. **Position note:** create `Openings/<hub name>/<position name>.md` from [templates/opening-position.md](../templates/opening-position.md). Fill only the plan sections that were discussed, each starting with its own board embed (`![[<file name>|400]]`); leave the others as an empty heading. Leave "My notes" empty.
5. **Link:** add `- [[<position name>]]` to the hub's "Positions" list.

### 1.7.5.  Step 5 — Update

1. **Plans:** append the new explanation to the matching plan section as a new dated entry (`**YYYY-MM-DD** — …`). Never rewrite or remove earlier entries. If the section was still empty, first add its board embed (Step 4.3–4.4).
2. **Engine line:** append the new line as a dated entry, if it differs from the last one.
3. **Frontmatter:** add the side to `plans` if missing, and set `updated` to today. Keep everything else.
4. **Boards:** run the script again for each discussed side. It writes the same file name for the same position, so this only repairs a missing file and never changes an embed.
5. **Never touch "My notes"**, and never delete a note, a section or an entry.

### 1.7.6.  Step 6 — Confirm

Tell the user in one line what happened, with the path, e.g.:

> Saved to `Openings/Sicilian Defense, Najdorf Variation (B90)/6.Be3 e5 7.Nb3.md` (new note).
> Updated `Openings/…/6.Be3 e5 7.Nb3.md`: added Black's plan.

---

## 1.8.  Quality checklist

- [ ] The user said yes (or asked to save) before anything was written
- [ ] An existing note was searched for by FEN (first four fields) before creating one
- [ ] Notes follow the templates; names contain no forbidden characters
- [ ] Each filled plan section embeds a board from that side (`--flip` for Black), stored in `Openings/boards/` under the name the script printed
- [ ] Earlier plan and engine-line entries are unchanged; only dated entries were appended
- [ ] "My notes" is untouched
- [ ] The hub links to every position note in its folder
